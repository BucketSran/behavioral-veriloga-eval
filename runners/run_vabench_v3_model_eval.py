#!/usr/bin/env python3
"""Run prompt-only model evaluation on vaBench release-v3 tasks.

This runner is v3-native: it reads benchmark-vabench-release-v3/TASKS.json and
the v3 score-denominator manifest, presents public instruction.md contracts to
the model, stages public starter support artifacts, and scores generated DUTs
with the v3 hidden EVAS checker. The default selection is the current v3
candidate denominator, not counted_in_score, because the v3 formal score policy
is intentionally not frozen yet.
"""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time
from typing import Any

from generate import extract_code_blocks
from run_vabench_release_minimax_baseline import (
    DEFAULT_BASE_URL,
    DEFAULT_MODEL,
    call_anthropic_compatible,
    call_minimax,
    is_quota_or_rate_error,
    load_api_key,
    model_slug,
    resolved_api_metadata,
)
from simulate_evas import (
    read_meta,
    read_task_artifact_supports,
    read_task_artifact_targets,
    run_case,
)
from vabench_release_prompt_wrapper import (
    RELEASE_RUNNER_WRAPPER_VERSION,
    RELEASE_SYSTEM_PROMPT,
    build_release_generation_prompt,
    clean_artifact_text,
    extract_marked_artifacts,
)


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = ROOT / "benchmark-vabench-release-v3"
TASKS_JSON = PACKAGE_ROOT / "TASKS.json"
CHECKS_YAML = PACKAGE_ROOT / "CHECKS.yaml"
DEFAULT_SCORE_ROSTER = PACKAGE_ROOT / "reports" / "score_denominator_manifest.json"
RESULTS_ROOT = ROOT / "results"

CLAIM_BOUNDARY = (
    "Legacy V3 contract only: pinned strict EVAS hidden scoring is the formal "
    "judge for this archived evaluation path. Spectre is "
    "optional parity evidence and is never required for certification or model-score "
    "claims. Exploratory candidate runs cannot support a formal model-score claim; "
    "formal claims require a frozen counted denominator, verified evaluator identity, "
    "and complete terminal evidence for every selected row."
)

FORMAL_SCORE_SCOPE = "formal_model_score"
EXPLORATORY_SCOPE = "exploratory_candidate_eval"
VALID_SCORE_FAILURES = {
    "FAIL_DUT_COMPILE",
    "FAIL_TB_COMPILE",
    "FAIL_SIM_CORRECTNESS",
}
INFRA_SCORE_FAILURES = {"FAIL_INFRA", "FAIL_UNKNOWN"}
TERMINAL_SCORE_STATUSES = {"PASS", *VALID_SCORE_FAILURES, *INFRA_SCORE_FAILURES}
EXPECTED_EVAS_IDENTITY = {
    "package_name": "evas-sim",
    "package_version": "0.8.7",
    "engine": "evas-rust",
    "rust_core_present": True,
    "rust_core_loadable": True,
    "rust_core_abi_version": 20260718,
    "rust_core_version": "0.2.4",
}
EXPECTED_PYTHON_VERSION = "3.11.13"


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_identity(path: Path) -> dict[str, Any]:
    identity: dict[str, Any] = {"path": rel(path), "exists": path.is_file()}
    if path.is_file():
        identity.update({"sha256": sha256_file(path), "size_bytes": path.stat().st_size})
    return identity


def repository_identity(root: Path) -> dict[str, Any]:
    try:
        revision = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout.strip()
        status = subprocess.run(
            ["git", "status", "--porcelain=v1", "--untracked-files=normal"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
            timeout=120,
        ).stdout.splitlines()
        return {
            "status": "available",
            "commit": revision,
            "dirty": bool(status),
        }
    except (FileNotFoundError, subprocess.SubprocessError) as exc:
        return {"status": "unavailable", "error": f"{type(exc).__name__}: {exc}"}


@contextmanager
def evaluator_execution_environment(args: argparse.Namespace):
    updates = {
        "VABENCH_EVAS_COMMAND": str(args.evas_command),
        "VAEVAS_EVAS_PERSISTENT_WORKER": "1" if args.persistent_evas_worker else "0",
    }
    previous = {name: os.environ.get(name) for name in updates}
    try:
        os.environ.update(updates)
        yield
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


def resolve_repo_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def output_root_for(model: str, tag: str) -> Path:
    stamp = tag or datetime.now().strftime("%Y%m%d-%H%M%S")
    return RESULTS_ROOT / f"vabench-v3-model-eval-{model_slug(model)}-{stamp}"


def load_tasks() -> dict[str, dict[str, Any]]:
    payload = read_json(TASKS_JSON)
    defaults = payload.get("defaults", {})
    tasks: dict[str, dict[str, Any]] = {}
    for slug, entry in payload.get("tasks", {}).items():
        if not isinstance(entry, dict):
            continue
        merged = dict(defaults) if isinstance(defaults, dict) else {}
        merged.update(entry)
        tasks[str(slug)] = merged
    return tasks


def slug_number(slug: str) -> int:
    try:
        return int(slug.split("-", 1)[0])
    except ValueError:
        return 10**9


def task_dir(slug: str) -> Path:
    return PACKAGE_ROOT / "tasks" / slug


def task_tokens_from_args(args: argparse.Namespace) -> set[str]:
    tokens = {str(item).strip() for item in args.task if str(item).strip()}
    for raw_path in args.task_file:
        path = resolve_repo_path(raw_path)
        tokens.update(
            line.strip()
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        )
    return tokens


def task_matches(row: dict[str, Any], tokens: set[str]) -> bool:
    if not tokens:
        return True
    slug = str(row.get("release_entry_id") or "")
    task_id = str(row.get("task_id") or "")
    number = f"{slug_number(slug):03d}"
    return slug in tokens or task_id in tokens or number in tokens


def base_rows_from_denominator(score_roster: Path, tasks: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    if not score_roster.exists():
        rows: list[dict[str, Any]] = []
        for slug, task in tasks.items():
            rows.append({
                "release_entry_id": slug,
                "task_id": str(task.get("id") or slug),
                "form": str(task.get("form") or "dut"),
                "level": str(task.get("level") or ""),
                "track": "unknown",
                "difficulty": str(task.get("difficulty") or ""),
                "category": str(task.get("category") or ""),
                "base_function": str(task.get("title") or ""),
                "candidate_score_denominator": False,
                "counted_in_score": False,
                "spectre_recalibration_required": False,
            })
        return rows
    payload = read_json(score_roster)
    rows = payload.get("form_rows", [])
    return [dict(row) for row in rows if isinstance(row, dict)]


def selected_rows(args: argparse.Namespace) -> list[dict[str, Any]]:
    tasks = load_tasks()
    rows = base_rows_from_denominator(resolve_repo_path(args.score_roster), tasks)
    if args.selection_surface == "candidate":
        rows = [row for row in rows if row.get("candidate_score_denominator") is True]
    elif args.selection_surface == "counted":
        rows = [row for row in rows if row.get("counted_in_score") is True]
    elif args.selection_surface != "all":
        raise ValueError(f"unsupported selection surface: {args.selection_surface}")

    task_tokens = task_tokens_from_args(args)
    rows = [row for row in rows if task_matches(row, task_tokens)]
    if args.level:
        wanted = set(args.level)
        rows = [row for row in rows if str(row.get("level")) in wanted]
    if args.track:
        wanted = set(args.track)
        rows = [row for row in rows if str(row.get("track")) in wanted]
    if args.difficulty:
        wanted = set(args.difficulty)
        rows = [row for row in rows if str(row.get("difficulty")) in wanted]
    if args.category:
        wanted = set(args.category)
        rows = [row for row in rows if str(row.get("category")) in wanted]
    if args.exclude_spectre_divergent:
        rows = [row for row in rows if row.get("spectre_recalibration_required") is not True]

    rows.sort(key=lambda row: slug_number(str(row.get("release_entry_id") or "")))
    if args.limit is not None:
        rows = rows[: args.limit]
    return [augment_row(row, tasks) for row in rows]


def augment_row(row: dict[str, Any], tasks: dict[str, dict[str, Any]]) -> dict[str, Any]:
    slug = str(row.get("release_entry_id") or "")
    task = tasks.get(slug, {})
    directory = task_dir(slug)
    targets = read_task_artifact_targets(directory)
    supports = read_task_artifact_supports(directory)
    augmented = dict(row)
    augmented.update({
        "task_dir": rel(directory),
        "instruction": rel(directory / "instruction.md"),
        "target_artifacts": targets,
        "support_artifacts": supports,
        "task_title": str(task.get("title") or row.get("base_function") or slug),
    })
    return augmented


def count_by(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key) or "unknown") for row in rows).items()))


def support_artifact_contents(directory: Path, support_names: list[str]) -> dict[str, str]:
    support: dict[str, str] = {}
    for name in support_names:
        path = directory / "starter" / name
        if path.exists() and path.is_file():
            support[name] = path.read_text(encoding="utf-8", errors="ignore")
    return support


def copy_public_support_artifacts(directory: Path, sample_dir: Path, support_names: list[str]) -> list[str]:
    copied: list[str] = []
    for name in support_names:
        src = directory / "starter" / name
        if not src.exists() or not src.is_file():
            continue
        dst = sample_dir / Path(name).name
        shutil.copyfile(src, dst)
        copied.append(str(dst.relative_to(sample_dir)))
    return copied


def fallback_code_blocks(response_text: str) -> dict[str, list[str]]:
    blocks = extract_code_blocks(response_text)
    if blocks["va"] or blocks["scs"]:
        return blocks
    stripped = response_text.strip()
    if not stripped:
        return {"va": [], "scs": []}
    if "simulator lang=spectre" in stripped.lower():
        return {"va": [], "scs": [stripped]}
    if "module " in stripped:
        return {"va": [stripped], "scs": []}
    return {"va": [], "scs": []}


def save_candidate_files(response_text: str, target_artifacts: list[str], sample_dir: Path) -> list[str]:
    saved: list[str] = []

    def write_file(filename: str, text: str) -> None:
        out = sample_dir / Path(filename).name
        out.write_text(clean_artifact_text(text) + "\n", encoding="utf-8")
        saved.append(str(out))

    marked = extract_marked_artifacts(response_text)
    for target in target_artifacts:
        if target in marked:
            write_file(target, marked[target])
    for name, text in marked.items():
        if name not in target_artifacts:
            write_file(name, text)
    if saved:
        return saved

    blocks = fallback_code_blocks(response_text)
    va_idx = 0
    scs_idx = 0
    for target in target_artifacts:
        if target.endswith((".va", ".vams")) and va_idx < len(blocks["va"]):
            write_file(target, blocks["va"][va_idx])
            va_idx += 1
        elif target.endswith(".scs") and scs_idx < len(blocks["scs"]):
            write_file(target, blocks["scs"][scs_idx])
            scs_idx += 1
    return saved


def call_model(
    *,
    api_format: str,
    api_key: str,
    base_url: str,
    model: str,
    prompt: str,
    max_tokens: int,
    temperature: float,
    timeout_s: int,
    network_mode: str,
    token_param: str,
    auth_header: str,
    extra_body: dict[str, Any] | None,
) -> tuple[str, dict[str, Any]]:
    if api_format == "anthropic":
        return call_anthropic_compatible(
            api_key=api_key,
            base_url=base_url,
            model=model,
            system_prompt=RELEASE_SYSTEM_PROMPT,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            timeout_s=timeout_s,
            network_mode=network_mode,
            extra_body=extra_body,
        )
    return call_minimax(
        api_key=api_key,
        base_url=base_url,
        model=model,
        system_prompt=RELEASE_SYSTEM_PROMPT,
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        timeout_s=timeout_s,
        network_mode=network_mode,
        token_param=token_param,
        auth_header=auth_header,
        extra_body=extra_body,
    )


def generate_one(
    *,
    row: dict[str, Any],
    api_key: str,
    args: argparse.Namespace,
    output_root: Path,
) -> dict[str, Any]:
    slug = str(row["release_entry_id"])
    directory = task_dir(slug)
    model_key = model_slug(args.model)
    sample_dir = output_root / "generated" / model_key / slug / f"sample_{args.sample_idx}"
    meta_path = sample_dir / "generation_meta.json"
    if args.resume and meta_path.exists():
        old = read_json(meta_path)
        if old.get("status") in {"generated", "no_code_extracted", "dry_run"}:
            return old

    sample_dir.mkdir(parents=True, exist_ok=True)
    targets = list(row.get("target_artifacts") or [])
    supports = list(row.get("support_artifacts") or [])
    copied_support = copy_public_support_artifacts(directory, sample_dir, supports)
    public_prompt_text = (directory / "instruction.md").read_text(encoding="utf-8")
    prompt_text = build_release_generation_prompt(
        public_prompt=public_prompt_text,
        target_artifacts=targets,
        form=str(row.get("form") or "dut"),
        support_artifacts=support_artifact_contents(directory, supports),
    )
    (sample_dir / "public_instruction.md").write_text(public_prompt_text, encoding="utf-8")
    (sample_dir / "prompt_sent.md").write_text(prompt_text, encoding="utf-8")

    resolved_token, resolved_auth = resolved_api_metadata(
        api_format=args.api_format,
        base_url=args.base_url,
        model=args.model,
        token_param=args.token_param,
        auth_header=args.auth_header,
    )
    base_meta = {
        "status": "pending",
        "benchmark": "benchmark-vabench-release-v3",
        "source": "api_prompt_only_v3_candidate_eval",
        "runner_wrapper_version": RELEASE_RUNNER_WRAPPER_VERSION,
        "model": args.model,
        "model_slug": model_key,
        "task_slug": slug,
        "task_id": row.get("task_id"),
        "form": row.get("form"),
        "level": row.get("level"),
        "difficulty": row.get("difficulty"),
        "category": row.get("category"),
        "selection_surface": args.selection_surface,
        "candidate_score_denominator": row.get("candidate_score_denominator"),
        "counted_in_score": row.get("counted_in_score"),
        "sample_idx": args.sample_idx,
        "temperature": args.temperature,
        "max_tokens": args.max_tokens,
        "token_param": resolved_token,
        "auth_header": resolved_auth,
        "target_artifacts": targets,
        "support_artifacts": supports,
        "copied_support_artifacts": copied_support,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "api_base_url": args.base_url,
        "api_format": args.api_format,
        "claim_allowed": False,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    if args.dry_run:
        meta = {**base_meta, "status": "dry_run", "saved_files": []}
        write_json(meta_path, meta)
        return meta

    extra_body = read_json(resolve_repo_path(args.extra_body_json)) if args.extra_body_json else None
    last_error = ""
    for attempt in range(1, args.api_attempts + 1):
        try:
            response_text, usage = call_model(
                api_format=args.api_format,
                api_key=api_key,
                base_url=args.base_url,
                model=args.model,
                prompt=prompt_text,
                max_tokens=args.max_tokens,
                temperature=args.temperature,
                timeout_s=args.request_timeout_s,
                network_mode=args.network_mode,
                token_param=resolved_token,
                auth_header=resolved_auth,
                extra_body=extra_body,
            )
            (sample_dir / "raw_response.txt").write_text(response_text, encoding="utf-8")
            saved = save_candidate_files(response_text, targets, sample_dir)
            meta = {
                **base_meta,
                "status": "generated" if saved else "no_code_extracted",
                "saved_files": [rel(Path(path)) for path in saved],
                "raw_response_length": len(response_text),
                "api_attempts_used": attempt,
                **usage,
            }
            write_json(meta_path, meta)
            return meta
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {str(exc)[:800]}"
            if attempt < args.api_attempts:
                delay_s = args.quota_retry_sleep_s if is_quota_or_rate_error(exc) else min(60, 5 * attempt)
                if delay_s > 0:
                    time.sleep(delay_s)
                continue

    meta = {**base_meta, "status": "api_error", "error": last_error, "saved_files": []}
    write_json(meta_path, meta)
    return meta


def run_generation(rows: list[dict[str, Any]], args: argparse.Namespace, output_root: Path) -> list[dict[str, Any]]:
    api_key = "" if args.dry_run else load_api_key(args.api_key_file, args.api_format)
    workers = max(1, min(args.gen_workers, len(rows) or 1))
    results: list[dict[str, Any]] = []
    if workers == 1:
        for index, row in enumerate(rows, start=1):
            print(f"[v3-generate] {index}/{len(rows)} {row['release_entry_id']} ...", flush=True)
            result = generate_one(row=row, api_key=api_key, args=args, output_root=output_root)
            print(f"[v3-generate] {row['release_entry_id']} {result.get('status')}", flush=True)
            results.append(result)
        return results
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(generate_one, row=row, api_key=api_key, args=args, output_root=output_root): row for row in rows}
        for future in as_completed(futures):
            row = futures[future]
            result = future.result()
            print(f"[v3-generate] {row['release_entry_id']} {result.get('status')}", flush=True)
            results.append(result)
    return results


def choose_hidden_tb(directory: Path) -> Path | None:
    direct = directory / "test_hidden" / "hidden.scs"
    if direct.exists():
        return direct
    candidates = sorted((directory / "test_hidden" / "tests").glob("*.scs"))
    return candidates[0] if len(candidates) == 1 else None


def fail_score(row: dict[str, Any], reason: str, output_root: Path, args: argparse.Namespace) -> dict[str, Any]:
    result = {
        "benchmark": "benchmark-vabench-release-v3",
        "model": model_slug(args.model),
        "task_slug": row.get("release_entry_id"),
        "task_id": row.get("task_id"),
        "form": row.get("form"),
        "level": row.get("level"),
        "difficulty": row.get("difficulty"),
        "category": row.get("category"),
        "status": "FAIL_INFRA",
        "failure_class": "infrastructure",
        "termination_reason": reason,
        "scores": {
            "dut_compile": 0.0,
            "tb_compile": 0.0,
            "sim_correct": 0.0,
            "weighted_total": 0.0,
        },
        "required_score_axes": ["dut_compile", "tb_compile", "sim_correct"],
        "sample_idx": args.sample_idx,
        "temperature": args.temperature,
        "top_p": args.top_p,
        "evas_notes": [reason],
        "claim_allowed": False,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    path = output_root / str(row.get("release_entry_id")) / "result.json"
    write_json(path, result)
    return result


def runtime_identity_matches(identity: Any) -> bool:
    return isinstance(identity, dict) and all(
        identity.get(key) == expected for key, expected in EXPECTED_EVAS_IDENTITY.items()
    )


def infrastructure_failure_reason(raw: dict[str, Any], identity: Any) -> str | None:
    notes = [str(note) for note in raw.get("notes", [])]
    infrastructure_markers = (
        "strict_spectre_lint_error=FileNotFoundError",
        "evas_command_not_found",
        "Rust backend library not found",
        "rust_core_loadable=False",
        "EVAS does not fall back",
    )
    if any(marker in note for note in notes for marker in infrastructure_markers):
        return "evaluator_runtime_unavailable"
    if not isinstance(identity, dict):
        return "per_run_evas_identity_missing"
    if not runtime_identity_matches(identity):
        return "per_run_evas_identity_mismatch"
    return None


def required_score_axes(directory: Path) -> list[str]:
    try:
        meta = read_meta(directory)
    except FileNotFoundError:
        meta = {}
    scoring = set(meta.get("scoring", ["dut_compile", "tb_compile", "sim_correct"]))
    axes: list[str] = []
    if "dut_compile" in scoring or "syntax" in scoring:
        axes.append("dut_compile")
    if "tb_compile" in scoring or {"routing", "simulation"} & scoring:
        axes.append("tb_compile")
    if "sim_correct" in scoring:
        axes.append("sim_correct")
    return axes or ["dut_compile", "tb_compile", "sim_correct"]


def score_one(row: dict[str, Any], args: argparse.Namespace, output_root: Path) -> dict[str, Any]:
    slug = str(row["release_entry_id"])
    directory = task_dir(slug)
    model_key = model_slug(args.model)
    sample_dir = args.generated_root or output_root.parent / "generated"
    sample_path = sample_dir / model_key / slug / f"sample_{args.sample_idx}"
    result_path = output_root / slug / "result.json"
    if args.resume and result_path.exists():
        return read_json(result_path)
    if not sample_path.exists():
        return fail_score(row, "missing_generated_sample", output_root, args)
    targets = list(row.get("target_artifacts") or [])
    if not targets:
        return fail_score(row, "missing_target_artifacts", output_root, args)
    missing = [name for name in targets if not (sample_path / name).exists()]
    if missing:
        return fail_score(row, f"missing_generated_target_artifacts={','.join(missing)}", output_root, args)
    tb_path = choose_hidden_tb(directory)
    if tb_path is None:
        return fail_score(row, "missing_hidden_testbench", output_root, args)
    primary = sample_path / targets[0]
    evas_output_root = output_root / slug / "evas_output"
    try:
        raw = run_case(
            directory,
            primary,
            tb_path,
            output_root=evas_output_root,
            timeout_s=args.score_timeout_s,
            task_id_override=str(row.get("task_id") or slug),
        )
    except Exception as exc:
        return fail_score(row, f"{type(exc).__name__}: {str(exc)[:500]}", output_root, args)
    status = str(raw.get("status", "FAIL_UNKNOWN"))
    identity_path = evas_output_root / "evas_identity.json"
    try:
        per_run_identity = read_json(identity_path) if identity_path.is_file() else None
    except (OSError, json.JSONDecodeError):
        per_run_identity = None
    infra_reason = infrastructure_failure_reason(raw, per_run_identity)
    if infra_reason is not None:
        status = "FAIL_INFRA"
    result = {
        "benchmark": "benchmark-vabench-release-v3",
        "model": model_key,
        "task_slug": slug,
        "task_id": row.get("task_id"),
        "form": row.get("form"),
        "level": row.get("level"),
        "difficulty": row.get("difficulty"),
        "category": row.get("category"),
        "selection_surface": args.selection_surface,
        "candidate_score_denominator": row.get("candidate_score_denominator"),
        "counted_in_score": row.get("counted_in_score"),
        "sample_idx": args.sample_idx,
        "temperature": args.temperature,
        "top_p": args.top_p,
        "status": status,
        "failure_class": (
            None
            if status == "PASS"
            else "candidate"
            if status in VALID_SCORE_FAILURES
            else "infrastructure"
        ),
        "termination_reason": infra_reason or status.lower(),
        "checker_task_id": raw.get("checker_task_id"),
        "scores": raw.get("scores", {}),
        "required_score_axes": required_score_axes(directory),
        "evas_notes": raw.get("notes", []),
        "evas_timing": raw.get("timing", {}),
        "evas_identity": per_run_identity,
        "evidence_artifacts": {
            "candidate": file_identity(primary),
            "hidden_testbench": file_identity(tb_path),
            "waveform": file_identity(evas_output_root / "tran.csv"),
            "strobe": file_identity(evas_output_root / "strobe.txt"),
            "evas_identity": file_identity(identity_path),
        },
        "claim_allowed": False,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    write_json(result_path, result)
    return result


def run_scoring(rows: list[dict[str, Any]], args: argparse.Namespace, output_root: Path) -> list[dict[str, Any]]:
    workers = max(1, min(args.score_workers, len(rows) or 1))
    results: list[dict[str, Any]] = []
    if workers == 1:
        for index, row in enumerate(rows, start=1):
            print(f"[v3-score] {index}/{len(rows)} {row['release_entry_id']} ...", flush=True)
            result = score_one(row, args, output_root)
            print(f"[v3-score] {row['release_entry_id']} {result.get('status')}", flush=True)
            results.append(result)
        return results
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(score_one, row, args, output_root): row for row in rows}
        for future in as_completed(futures):
            row = futures[future]
            result = future.result()
            print(f"[v3-score] {row['release_entry_id']} {result.get('status')}", flush=True)
            results.append(result)
    return results


def pass_count(results: list[dict[str, Any]]) -> int:
    return sum(1 for item in results if item.get("status") == "PASS")


def status_counts(items: list[dict[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(str(item.get("status") or "missing") for item in items).items()))


def score_metrics_valid(score: dict[str, Any]) -> bool:
    metrics = score.get("scores")
    required = ("dut_compile", "tb_compile", "sim_correct", "weighted_total")
    if not isinstance(metrics, dict):
        return False
    if not all(
        isinstance(metrics.get(key), (int, float))
        and not isinstance(metrics.get(key), bool)
        and 0.0 <= float(metrics[key]) <= 1.0
        for key in required
    ):
        return False
    axes = score.get("required_score_axes")
    if (
        not isinstance(axes, list)
        or not axes
        or len(set(axes)) != len(axes)
        or any(axis not in required[:3] for axis in axes)
    ):
        return False
    expected = round(sum(float(metrics[axis]) for axis in axes) / len(axes), 4)
    return abs(float(metrics["weighted_total"]) - expected) <= 0.00005


def score_status_consistent(score: dict[str, Any]) -> bool:
    status = str(score.get("status") or "")
    if status in INFRA_SCORE_FAILURES:
        return True
    if not score_metrics_valid(score):
        return False
    axes = score["required_score_axes"]
    metrics = score["scores"]
    expected = "PASS"
    for axis, failure_status in (
        ("dut_compile", "FAIL_DUT_COMPILE"),
        ("tb_compile", "FAIL_TB_COMPILE"),
        ("sim_correct", "FAIL_SIM_CORRECTNESS"),
    ):
        if axis in axes and float(metrics[axis]) < 1.0:
            expected = failure_status
            break
    return status == expected


def environment_evidence(args: argparse.Namespace) -> tuple[dict[str, Any] | None, list[str]]:
    raw_path = str(getattr(args, "environment_evidence", "") or "").strip()
    if not raw_path:
        return None, ["environment_evidence_not_provided"]
    path = resolve_repo_path(raw_path)
    if not path.is_file():
        return {"path": rel(path), "exists": False}, ["environment_evidence_missing"]
    identity = file_identity(path)
    try:
        payload = read_json(path)
    except (OSError, json.JSONDecodeError) as exc:
        identity["load_error"] = f"{type(exc).__name__}: {exc}"
        return identity, ["environment_evidence_invalid_json"]

    identity["status"] = payload.get("status")
    identity["payload"] = payload
    problems: list[str] = []
    if str(payload.get("status") or "").lower() != "pass":
        problems.append("environment_verification_not_passed")
    if payload.get("schema_version") != "vabench-evaluator-environment-verification-v1":
        problems.append("environment_evidence_schema_mismatch")
    live_evas = payload.get("live_evas", {})
    if not isinstance(live_evas, dict) or live_evas.get("status") != "pass":
        problems.append("environment_live_evas_not_verified")
    elif not runtime_identity_matches(live_evas.get("observed")):
        problems.append("environment_live_evas_identity_mismatch")
    live_python = payload.get("live_python", {})
    if not isinstance(live_python, dict) or live_python.get("status") != "pass":
        problems.append("environment_live_python_not_verified")
    elif str(live_python.get("observed_version") or "") != EXPECTED_PYTHON_VERSION:
        problems.append("environment_live_python_version_mismatch")
    return identity, problems


def score_evidence_index(scores: list[dict[str, Any]], output_root: Path) -> list[dict[str, Any]]:
    index: list[dict[str, Any]] = []
    for score in sorted(scores, key=lambda item: str(item.get("task_slug") or "")):
        slug = str(score.get("task_slug") or "")
        path = output_root / "evas_results" / slug / "result.json"
        result_identity = file_identity(path)
        artifact_status: str | None = None
        if path.is_file():
            try:
                artifact_status = str(read_json(path).get("status") or "")
            except (OSError, json.JSONDecodeError):
                artifact_status = None
        row = {
            "task_slug": slug,
            "task_id": score.get("task_id"),
            "status": score.get("status"),
            "artifact_status": artifact_status,
            "result": result_identity,
        }
        index.append(row)
    return index


def derive_claim_gate(
    *,
    rows: list[dict[str, Any]],
    scores: list[dict[str, Any]],
    args: argparse.Namespace,
    environment_provenance: dict[str, Any] | None,
    environment_problems: list[str],
    result_evidence: list[dict[str, Any]],
    input_provenance: dict[str, dict[str, Any]],
    full_counted_rows: list[dict[str, Any]],
    current_repository: dict[str, Any],
    roster_path: Path,
    executed_python_version: str,
) -> dict[str, Any]:
    scope = str(getattr(args, "claim_scope", EXPLORATORY_SCOPE))
    selected_slugs = [str(row.get("release_entry_id") or "") for row in rows]
    scored_slugs = [str(score.get("task_slug") or "") for score in scores]
    score_statuses = [str(score.get("status") or "missing") for score in scores]
    counted_slugs = [str(row.get("release_entry_id") or "") for row in full_counted_rows]
    blocking_reasons: list[str] = []

    if scope != FORMAL_SCORE_SCOPE:
        blocking_reasons.append("claim_scope_is_exploratory")
    if args.stage not in {"score", "all"} or args.dry_run:
        blocking_reasons.append("hidden_scoring_not_executed")
    if args.selection_surface != "counted":
        blocking_reasons.append("selection_surface_is_not_counted")
    if not rows:
        blocking_reasons.append("selected_denominator_is_empty")
    if any(row.get("counted_in_score") is not True for row in rows):
        blocking_reasons.append("selected_row_not_counted_in_score")
    if len(set(selected_slugs)) != len(selected_slugs):
        blocking_reasons.append("selected_denominator_contains_duplicates")
    if len(scores) != len(rows) or sorted(scored_slugs) != sorted(selected_slugs):
        blocking_reasons.append("score_evidence_incomplete")
    if len(result_evidence) != len(scores) or any(
        item.get("result", {}).get("exists") is not True for item in result_evidence
    ):
        blocking_reasons.append("score_result_artifact_missing")
    if any(item.get("artifact_status") != item.get("status") for item in result_evidence):
        blocking_reasons.append("score_result_artifact_status_mismatch")
    if any(status not in TERMINAL_SCORE_STATUSES for status in score_statuses):
        blocking_reasons.append("score_evidence_has_nonterminal_status")
    if any(status in INFRA_SCORE_FAILURES for status in score_statuses):
        blocking_reasons.append("score_evidence_has_infrastructure_failure")
    if any(not runtime_identity_matches(score.get("evas_identity")) for score in scores):
        blocking_reasons.append("score_evidence_evas_identity_mismatch")
    if any(not score_metrics_valid(score) for score in scores):
        blocking_reasons.append("score_evidence_metrics_invalid")
    if any(not score_status_consistent(score) for score in scores):
        blocking_reasons.append("score_status_metrics_inconsistent")
    repository = (
        (environment_provenance or {}).get("payload", {}).get("source", {}).get("repository", {})
    )
    if scope == FORMAL_SCORE_SCOPE:
        if roster_path.resolve() != DEFAULT_SCORE_ROSTER.resolve():
            blocking_reasons.append("formal_score_roster_is_not_canonical")
        filtered = (
            any(
                (
                    getattr(args, "task", []),
                    getattr(args, "task_file", []),
                    getattr(args, "level", []),
                    getattr(args, "track", []),
                    getattr(args, "difficulty", []),
                    getattr(args, "category", []),
                )
            )
            or bool(getattr(args, "exclude_spectre_divergent", False))
            or getattr(args, "limit", None) is not None
        )
        if filtered:
            blocking_reasons.append("formal_denominator_is_filtered")
        if not full_counted_rows:
            blocking_reasons.append("frozen_counted_denominator_is_empty")
        elif sorted(selected_slugs) != sorted(counted_slugs):
            blocking_reasons.append("formal_denominator_is_incomplete")
        if any(
            identity.get("exists") is not True or not identity.get("sha256")
            for identity in input_provenance.values()
        ):
            blocking_reasons.append("input_provenance_incomplete")
        if not isinstance(repository, dict) or repository.get("status") != "available":
            blocking_reasons.append("environment_source_identity_unavailable")
        elif repository.get("dirty") is not False:
            blocking_reasons.append("environment_source_is_dirty")
        if current_repository.get("status") != "available":
            blocking_reasons.append("current_source_identity_unavailable")
        elif current_repository.get("dirty") is not False:
            blocking_reasons.append("current_source_is_dirty")
        elif repository.get("commit") != current_repository.get("commit"):
            blocking_reasons.append("environment_source_commit_is_stale")
        live_evas = (environment_provenance or {}).get("payload", {}).get("live_evas", {})
        verified_command = live_evas.get("command") if isinstance(live_evas, dict) else None
        if verified_command != str(getattr(args, "evas_command", "evas")):
            blocking_reasons.append("executed_evas_command_not_bound_to_environment_evidence")
        if bool(getattr(args, "persistent_evas_worker", False)):
            blocking_reasons.append("persistent_evas_worker_not_allowed_for_formal_claim")
        if executed_python_version != EXPECTED_PYTHON_VERSION:
            blocking_reasons.append("executed_python_version_mismatch")
    blocking_reasons.extend(environment_problems)

    unique_reasons = list(dict.fromkeys(blocking_reasons))
    return {
        "scope": scope,
        "status": "allowed" if not unique_reasons else "blocked",
        "allowed": not unique_reasons,
        "formal_judge": "pinned_strict_evas",
        "spectre_required": False,
        "selection_surface": args.selection_surface,
        "selected_rows": len(rows),
        "frozen_counted_rows": len(full_counted_rows),
        "scored_rows": len(scores),
        "terminal_score_rows": sum(status in TERMINAL_SCORE_STATUSES for status in score_statuses),
        "valid_failure_rows": sum(status in VALID_SCORE_FAILURES for status in score_statuses),
        "infrastructure_failure_rows": sum(status in INFRA_SCORE_FAILURES for status in score_statuses),
        "environment_verified": environment_provenance is not None and not environment_problems,
        "blocking_reasons": unique_reasons,
    }


def execution_status(
    *,
    rows: list[dict[str, Any]],
    generation: list[dict[str, Any]],
    scores: list[dict[str, Any]],
    args: argparse.Namespace,
) -> str:
    if args.dry_run:
        return "completed_dry_run"
    if str(getattr(args, "claim_scope", EXPLORATORY_SCOPE)) == FORMAL_SCORE_SCOPE and not rows:
        return "blocked_empty_denominator"
    if args.stage == "generate":
        return "completed" if len(generation) == len(rows) else "incomplete"
    if len(scores) != len(rows):
        return "incomplete"
    if any(str(item.get("status") or "") in INFRA_SCORE_FAILURES for item in scores):
        return "completed_with_infrastructure_failures"
    return "completed"


def write_summary(
    *,
    rows: list[dict[str, Any]],
    generation: list[dict[str, Any]],
    scores: list[dict[str, Any]],
    output_root: Path,
    args: argparse.Namespace,
    current_repository: dict[str, Any] | None = None,
    executed_python_version: str | None = None,
) -> dict[str, Any]:
    environment_provenance, environment_problems = environment_evidence(args)
    result_evidence = score_evidence_index(scores, output_root)
    roster_path = resolve_repo_path(args.score_roster)
    input_provenance = {
        "tasks": file_identity(TASKS_JSON),
        "checks": file_identity(CHECKS_YAML),
        "score_roster": file_identity(roster_path),
    }
    full_counted_rows = [
        row
        for row in base_rows_from_denominator(roster_path, load_tasks())
        if row.get("counted_in_score") is True
    ]
    if current_repository is None:
        current_repository = (
            repository_identity(ROOT)
            if str(getattr(args, "claim_scope", EXPLORATORY_SCOPE)) == FORMAL_SCORE_SCOPE
            else {
                "status": "not_checked",
                "reason": "current source identity is required only for formal score scope",
            }
        )
    if executed_python_version is None:
        executed_python_version = platform.python_version()
    claim_gate = derive_claim_gate(
        rows=rows,
        scores=scores,
        args=args,
        environment_provenance=environment_provenance,
        environment_problems=environment_problems,
        result_evidence=result_evidence,
        input_provenance=input_provenance,
        full_counted_rows=full_counted_rows,
        current_repository=current_repository,
        roster_path=roster_path,
        executed_python_version=executed_python_version,
    )
    summary = {
        "date": datetime.now(timezone.utc).isoformat(),
        "benchmark": "benchmark-vabench-release-v3",
        "model": args.model,
        "model_slug": model_slug(args.model),
        "runner_wrapper_version": RELEASE_RUNNER_WRAPPER_VERSION,
        "stage": args.stage,
        "selection_surface": args.selection_surface,
        "dry_run": args.dry_run,
        "status": execution_status(rows=rows, generation=generation, scores=scores, args=args),
        "claim_scope": claim_gate["scope"],
        "claim_allowed": claim_gate["allowed"],
        "claim_boundary": CLAIM_BOUNDARY,
        "claim_gate": claim_gate,
        "score_roster": rel(roster_path),
        "frozen_counted_rows": len(full_counted_rows),
        "selected_rows": len(rows),
        "selected_by_level": count_by(rows, "level"),
        "selected_by_track": count_by(rows, "track"),
        "selected_by_category": count_by(rows, "category"),
        "generation_status_counts": status_counts(generation),
        "scored_rows": len(scores),
        "evas_pass_count": pass_count(scores),
        "evas_pass_rate": round(pass_count(scores) / len(scores), 4) if scores else 0.0,
        "score_status_counts": status_counts(scores),
        "execution_policy": {
            "python_version": executed_python_version,
            "evas_command": str(getattr(args, "evas_command", "evas")),
            "persistent_evas_worker": bool(getattr(args, "persistent_evas_worker", False)),
            "score_workers": int(getattr(args, "score_workers", 1)),
            "score_timeout_s": int(getattr(args, "score_timeout_s", 0)),
        },
        "spectre_parity": {
            "status": "not_run",
            "required": False,
            "reason": (
                "Legacy V3 contract only: Spectre is optional parity evidence; "
                "pinned strict EVAS is the judge for this archived evaluation path."
            ),
        },
        "provenance": {
            "inputs": input_provenance,
            "source_repository": current_repository,
            "environment": environment_provenance,
            "score_results": result_evidence,
        },
        "paths": {
            "output_root": rel(output_root),
            "generated_root": rel(output_root / "generated"),
            "evas_results_root": rel(output_root / "evas_results"),
            "summary": rel(output_root / "summary.json"),
        },
    }
    write_json(output_root / "summary.json", summary)
    return summary


def list_rows(args: argparse.Namespace) -> int:
    rows = selected_rows(args)
    payload = {
        "date": datetime.now(timezone.utc).isoformat(),
        "benchmark": "benchmark-vabench-release-v3",
        "score_roster": rel(resolve_repo_path(args.score_roster)),
        "selection_surface": args.selection_surface,
        "selected_rows": len(rows),
        "selected_by_level": count_by(rows, "level"),
        "selected_by_track": count_by(rows, "track"),
        "selected_by_category": count_by(rows, "category"),
        "claim_scope": str(getattr(args, "claim_scope", EXPLORATORY_SCOPE)),
        "claim_allowed": False,
        "claim_gate": {
            "status": "blocked",
            "allowed": False,
            "blocking_reasons": ["listing_has_no_executed_evidence"],
        },
        "claim_boundary": CLAIM_BOUNDARY,
        "rows": rows,
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"score_roster={payload['score_roster']}")
        print(f"selection_surface={payload['selection_surface']}")
        print(f"selected_rows={payload['selected_rows']}")
        print(f"by_level={payload['selected_by_level']}")
        print(f"by_track={payload['selected_by_track']}")
        print(f"by_category={payload['selected_by_category']}")
        for row in rows[: min(len(rows), 20)]:
            print(
                f"- {row['release_entry_id']} task_id={row.get('task_id')} "
                f"level={row.get('level')} category={row.get('category')} "
                f"targets={','.join(row.get('target_artifacts') or [])}"
            )
        if len(rows) > 20:
            print(f"... {len(rows) - 20} more rows")
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--list", action="store_true", help="List selected v3 rows and exit.")
    ap.add_argument("--json", action="store_true", help="Print JSON for --list or final summary.")
    ap.add_argument("--score-roster", default=str(DEFAULT_SCORE_ROSTER))
    ap.add_argument(
        "--selection-surface",
        choices=["candidate", "all", "counted"],
        default="candidate",
        help="candidate uses candidate_score_denominator=true; counted uses counted_in_score=true.",
    )
    ap.add_argument("--exclude-spectre-divergent", action="store_true")
    ap.add_argument("--stage", choices=["generate", "score", "all"], default="all")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--base-url", default=DEFAULT_BASE_URL)
    ap.add_argument("--api-format", choices=["openai", "anthropic"], default="openai")
    ap.add_argument("--api-key-file", default="")
    ap.add_argument("--output-root", default="")
    ap.add_argument("--tag", default="")
    ap.add_argument("--generated-root", type=Path, default=None)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--task", action="append", default=[], help="Task slug, numeric id such as 001, or v3 task_id.")
    ap.add_argument("--task-file", action="append", default=[])
    ap.add_argument("--level", action="append", default=[])
    ap.add_argument("--track", action="append", default=[])
    ap.add_argument("--difficulty", action="append", default=[])
    ap.add_argument("--category", action="append", default=[])
    ap.add_argument("--sample-idx", type=int, default=0)
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--top-p", type=float, default=1.0)
    ap.add_argument("--max-tokens", type=int, default=8192)
    ap.add_argument("--request-timeout-s", type=int, default=420)
    ap.add_argument("--score-timeout-s", type=int, default=180)
    ap.add_argument(
        "--evas-command",
        default="evas",
        help="Installed EVAS CLI to bind for scoring; formal claims require the same command in environment evidence.",
    )
    ap.add_argument(
        "--persistent-evas-worker",
        action="store_true",
        help="Opt in to the persistent EVAS worker for exploratory throughput; forbidden for formal claims.",
    )
    ap.add_argument("--gen-workers", type=int, default=1)
    ap.add_argument("--score-workers", type=int, default=4)
    ap.add_argument("--api-attempts", type=int, default=2)
    ap.add_argument("--quota-retry-sleep-s", type=int, default=0)
    ap.add_argument("--network-mode", choices=["auto", "direct", "env"], default="auto")
    ap.add_argument("--token-param", choices=["auto", "max_tokens", "max_completion_tokens"], default="auto")
    ap.add_argument("--auth-header", choices=["auto", "authorization", "api-key", "both"], default="auto")
    ap.add_argument("--extra-body-json", default="")
    ap.add_argument(
        "--claim-scope",
        choices=[EXPLORATORY_SCOPE, FORMAL_SCORE_SCOPE],
        default=EXPLORATORY_SCOPE,
        help="Formal scope is allowed only when the executed evidence satisfies every claim gate.",
    )
    ap.add_argument(
        "--environment-evidence",
        default="",
        help="PASS JSON emitted by scripts/verify_evaluator_environment.py.",
    )
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.list:
        return list_rows(args)

    rows = selected_rows(args)
    if not rows and args.claim_scope != FORMAL_SCORE_SCOPE:
        print("No v3 rows selected.", file=sys.stderr)
        return 1
    output_root = resolve_repo_path(args.output_root) if args.output_root else output_root_for(args.model, args.tag)
    generation: list[dict[str, Any]] = []
    scores: list[dict[str, Any]] = []
    if args.stage in {"generate", "all"}:
        generation = run_generation(rows, args, output_root)
    if args.stage in {"score", "all"} and not args.dry_run:
        with evaluator_execution_environment(args):
            scores = run_scoring(rows, args, output_root / "evas_results")
    summary = write_summary(rows=rows, generation=generation, scores=scores, output_root=output_root, args=args)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(
            f"[vabench-v3-model-eval] status={summary['status']} "
            f"rows={summary['selected_rows']} scored={summary['scored_rows']} "
            f"summary={summary['paths']['summary']}",
            flush=True,
        )
    if args.claim_scope == FORMAL_SCORE_SCOPE and not summary["claim_allowed"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
