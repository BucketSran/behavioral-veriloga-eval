"""Batch-only resume around existing native cell/attempt execution."""

from copy import copy
from concurrent.futures import ThreadPoolExecutor, as_completed

import run_campaign as runner
import score_campaign as scorer
from run_native_attempts import read_native_attempt_sequence, retry_policy
from runners.agent_harness.batch_resume import BatchRun, docker_image_identity, source_identity


def run_native_batch(campaign, args, client_factory):
    cells = campaign["cells"]
    policy = retry_policy(args.native_max_attempts)
    images = {}
    if not args.dry_run and getattr(args, "mini_swe_sandbox", "none") in {"auto", "docker"}:
        for cell in cells:
            if cell["experimental_arm"] == "OneShot":
                continue
            image = (args.mini_swe_image if cell.get("executable_feedback", True)
                     else args.mini_swe_no_evas_image)
            if image not in images:
                images[image] = docker_image_identity(
                    image, docker_command=getattr(args, "docker_command", "docker"),
                    timeout_s=args.setup_timeout_s)
    manifest = {
        "campaign_file_sha256": args.campaign_file_sha256,
        "campaign": campaign, "source": source_identity(runner.REPO),
        "dry_run": args.dry_run,
        "observed_images": images,
        "runtime_options": {name: getattr(args, name, None) for name in (
            "episode_backend", "native_max_attempts", "native_model_call_limit",
            "reasoning_proposal_format", "base_url", "temperature", "stream",
            "agent_scaffold", "mini_swe_sandbox", "mini_swe_image", "mini_swe_no_evas_image",
            "setup_timeout_s", "request_timeout_s", "tool_timeout_s", "judge_timeout_s", "agent_timeout_s",
            "mini_swe_preflight_timeout_s", "mini_swe_preflight_attempts",
            "mini_swe_startup_workers", "workers", "evas_identity", "final_judge_command",
            "evas_command", "docker_command",
        )},
    }
    # Endpoint/command identities only; never credential values or key-file paths.
    from hashlib import sha256
    for name in ("base_url", "final_judge_command", "evas_command", "docker_command"):
        value = manifest["runtime_options"].pop(name)
        manifest["runtime_options"][name + "_sha256"] = sha256((value or "").encode()).hexdigest()
    rows = [{"cell_id": cell["cell_id"], "disposition": "not_started", "score": None}
            for cell in cells]
    results = {}
    with BatchRun(args.output, manifest, [cell["cell_id"] for cell in cells],
                  resume=args.resume) as batch:
        pending = []

        def read_terminal(cell):
            runtime = args.output / cell["cell_id"]
            if policy.max_attempts > 1:
                row = read_native_attempt_sequence(
                    runtime, cell, campaign_file_sha256=args.campaign_file_sha256,
                    expected_retry_policy=policy)
            else:
                row = scorer.read_native_cell(runtime, cell,
                                             campaign_file_sha256=args.campaign_file_sha256)
            return {**row, "status": row.get("status", row.get("judge_status") or row.get("outcome"))}

        def finished(index, row, disposition):
            cell_id = cells[index]["cell_id"]
            results[cell_id] = row
            rows[index] = {"cell_id": cell_id, "disposition": disposition,
                           "status": row["status"], "score": row.get("score"),
                           "attempt_count": row.get("attempt_count", 1)}

        # Scan the full roster before creating any provider. Unknown in-flight
        # evidence cannot authorize spending on another cell in this batch.
        errors = []
        for index, cell in enumerate(cells):
            runtime = args.output / cell["cell_id"]
            try:
                previous = batch.read(cell["cell_id"], runtime)
                if previous is not None:
                    finished(index, previous, "reused")
                elif runtime.exists():
                    if args.dry_run:
                        raise ValueError("interrupted dry-run export has no terminal receipt")
                    if policy.max_attempts > 1 and not (runtime / "selection.json").exists():
                        from run_native_attempts import validate_native_attempt_resume
                        validate_native_attempt_resume(
                            runtime, cell, campaign_file_sha256=args.campaign_file_sha256,
                            expected_retry_policy=policy,
                            model_call_limit=getattr(args, "native_model_call_limit", None))
                        pending.append((index, cell, True))
                    else:
                        previous = read_terminal(cell)
                        batch.record(cell["cell_id"], previous, runtime)
                        finished(index, previous, "recovered_terminal")
                else:
                    pending.append((index, cell, False))
            except Exception as exc:
                rows[index]["disposition"] = "blocked"
                errors.append(exc)
        batch.snapshot(rows)
        if errors:
            raise errors[0]

        def execute(item):
            index, cell, resume_attempts = item
            cell_args = copy(args)
            cell_args.resume = False  # Never enter legacy conversation resume.
            for name in ("mini_swe_image", "mini_swe_no_evas_image"):
                if getattr(cell_args, name, None) in images:
                    setattr(cell_args, name, images[getattr(cell_args, name)])
            if resume_attempts:
                from run_native_attempts import run_native_attempt_sequence
                run_native_attempt_sequence(
                    cell=cell, args=cell_args, client_factory=client_factory,
                    retry_policy=policy, resume=True)
            else:
                result = runner.run_cell_preserving_failure(
                    cell, cell_args, None if args.dry_run or policy.max_attempts > 1 else client_factory(),
                    client_factory=client_factory)
                if args.dry_run:
                    batch.record(cell["cell_id"], result, args.output / cell["cell_id"])
                    return index, result
            result = read_terminal(cell)
            batch.record(cell["cell_id"], result, args.output / cell["cell_id"])
            return index, result

        try:
            if args.workers == 1:
                for item in pending:
                    rows[item[0]]["disposition"] = "started"
                    batch.snapshot(rows)
                    index, row = execute(item)
                    finished(index, row, "executed")
                    batch.snapshot(rows)
            else:
                for item in pending:
                    rows[item[0]]["disposition"] = "scheduled"
                batch.snapshot(rows)
                with ThreadPoolExecutor(max_workers=args.workers) as pool:
                    futures = {pool.submit(execute, item): item[0] for item in pending}
                    for future in as_completed(futures):
                        index, row = future.result()
                        finished(index, row, "executed")
                        batch.snapshot(rows)
        finally:
            batch.snapshot(rows)
        return [results[cell["cell_id"]] for cell in cells]
