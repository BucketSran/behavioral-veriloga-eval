#!/usr/bin/env python3
"""Run one r53 task through the real three-condition evaluation plumbing.

The client is deterministic and derives an intentionally incomplete candidate only
from the public contract.  The smoke therefore tests the runner, sandbox boundary,
trajectory, immutable submission freeze, and EVAS 0.8.7 score sidecars without
claiming model quality or reproducing a paper baseline.
"""

from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import re
import shlex
import shutil
import sys
import time
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "benchmark-vabench-release-v4"
CALIBRATION = PACKAGE / "operations" / "calibration_pilot"
for import_root in (CALIBRATION, PACKAGE / "runners"):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

import build_campaign as campaign_builder  # noqa: E402
import result_protocol  # noqa: E402
import run_campaign  # noqa: E402
import score_campaign  # noqa: E402


DEFAULT_RELEASE = PACKAGE / "release" / "benchmarkv4-r53"
DEFAULT_TASK_ID = "v4-001"
DEFAULT_MODEL = "deterministic-public-contract-smoke"
DEFAULT_EVAS_IMAGE = "vabench-agent-runtime:0.8.7"
DEFAULT_NO_EVAS_IMAGE = "vabench-agent-runtime:0.8.7-no-evas"
PIPELINE_CLAIM_SCOPE = "single_task_three_arm_clean_room_pipeline"
EXPECTED_EVAS_VERSION = "0.8.7"
STRUCTURED_SCORE_STATUSES = {
    "passed",
    "compile_failure",
    "runtime_failure",
    "behavior_failure",
}
FORBIDDEN_PUBLIC_PARTS = {
    "evaluator",
    "solution",
    "mutation_bundles",
    "trusted_replay_fixtures",
    "trusted_replay_test.scs",
    "score_tb.scs",
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_immutable_json(path: Path, value: Any) -> None:
    encoded = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != encoded:
            raise ValueError(f"immutable evidence already exists with different bytes: {path}")
        return
    with path.open("xb") as handle:
        handle.write(encoded)
    path.chmod(0o444)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_identity(path: Path) -> dict[str, Any]:
    identity: dict[str, Any] = {"path": str(path), "exists": path.is_file()}
    if path.is_file():
        identity.update(
            {
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
        )
    return identity


def resolve_evas_command(command: str) -> tuple[str, dict[str, Any]]:
    argv = shlex.split(command)
    if not argv:
        raise ValueError("--evas-command must not be empty")
    resolved = shutil.which(argv[0]) if not Path(argv[0]).is_absolute() else argv[0]
    if resolved:
        argv[0] = str(Path(resolved).resolve())
    identity = result_protocol.evas_identity(argv)
    version_output = str(identity.get("version_output") or "")
    if not identity.get("available"):
        raise RuntimeError(
            "configured EVAS is unavailable: "
            f"{identity.get('error') or version_output or command}"
        )
    if re.search(r"\bevas-sim\s+0\.8\.7\b", version_output) is None:
        raise RuntimeError(
            "r53 clean-room smoke requires evas-sim 0.8.7; "
            f"observed {version_output or '<empty version output>'}"
        )
    return shlex.join(argv), identity


def release_summary(release: Path) -> dict[str, Any]:
    manifest = read_json(release / "MANIFEST.json")
    summary = {
        "path": str(release),
        "release_revision": str(manifest["release_revision"]),
        "task_count": int(manifest["task_count"]),
        "family_count": int(manifest["family_count"]),
        "evas_package": manifest["runtime_requirements"]["evas_package"],
        "evas_version": manifest["runtime_requirements"]["evas_version"],
        "manifest_sha256": sha256_file(release / "MANIFEST.json"),
        "task_index_sha256": sha256_file(release / "TASK_INDEX.json"),
    }
    if summary["release_revision"] != "r53":
        raise ValueError("clean-room closure is frozen to benchmark release r53")
    if summary["evas_version"] != EXPECTED_EVAS_VERSION:
        raise ValueError("r53 manifest is not pinned to evas-sim 0.8.7")
    return summary


def task_index_row(release: Path, task_id: str) -> dict[str, Any]:
    for row in read_json(release / "TASK_INDEX.json")["tasks"]:
        if row["task_id"] == task_id:
            return dict(row)
    raise ValueError(f"unknown r53 task id: {task_id}")


def public_contract(release: Path, task_id: str) -> dict[str, Any]:
    row = task_index_row(release, task_id)
    contract_path = release / str(row["public_contract"])
    if sha256_file(contract_path) != row["public_contract_sha256"]:
        raise ValueError(f"public contract hash mismatch for {task_id}")
    contract = read_json(contract_path)
    if contract.get("task_id") != task_id:
        raise ValueError(f"public contract task id mismatch for {task_id}")
    return contract


def three_arm_cells(release: Path, task_id: str, model: str) -> list[dict[str, Any]]:
    row = task_index_row(release, task_id)
    campaign = campaign_builder.build_campaign(
        release,
        family_ids=[str(row["family_id"])],
        model_provider="deterministic-public-contract-smoke",
        model=model,
        per_turn_max_tokens=4096,
        repetitions=1,
        three_arm_g0_g2=True,
    )
    cells = [cell for cell in campaign["cells"] if cell["task_id"] == task_id]
    run_campaign.validate_campaign_cells(cells, release)
    arms = {str(cell.get("experimental_arm")) for cell in cells}
    if arms != {"OneShot", "Agent-No-EVAS", "Agentic"} or len(cells) != 3:
        raise ValueError(f"expected exactly three matched arms, observed {sorted(arms)}")
    return cells


def verilog_number(value: Any) -> str:
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (int, float)):
        return repr(value)
    return "0"


def public_stub_artifacts(contract: dict[str, Any]) -> dict[str, str]:
    if contract.get("form") != "dut":
        raise ValueError("the deterministic closure fixture currently supports DUT tasks")
    files = (contract.get("artifact_contract") or {}).get("files") or []
    artifacts: dict[str, str] = {}
    for file_row in files:
        path = str(file_row.get("path") or "")
        modules = list(file_row.get("modules") or [])
        if not path or not modules:
            raise ValueError("public contract is missing artifact module metadata")
        lines = [
            "// Intentionally incomplete r53 clean-room smoke candidate.",
            "// Generated only from the public contract; not a reference solution.",
            '`include "constants.vams"',
            '`include "disciplines.vams"',
            "",
        ]
        for module in modules:
            ports = [str(port["name"]) for port in module.get("ports") or []]
            lines.append(f"module {module['name']}({', '.join(ports)});")
            for port in module.get("ports") or []:
                direction = str(port.get("direction") or "inout")
                lines.append(f"  {direction} {port['name']};")
            electrical = [
                str(port["name"])
                for port in module.get("ports") or []
                if port.get("discipline") == "electrical"
            ]
            if electrical:
                lines.append(f"  electrical {', '.join(electrical)};")
            for parameter in module.get("parameters") or []:
                parameter_type = (
                    "integer" if parameter.get("type") == "integer" else "real"
                )
                lines.append(
                    f"  parameter {parameter_type} {parameter['name']} = "
                    f"{verilog_number(parameter.get('default'))};"
                )
            output_ports = [
                str(port["name"])
                for port in module.get("ports") or []
                if port.get("direction") == "output"
                and port.get("discipline") == "electrical"
            ]
            lines.append("  analog begin")
            for output in output_ports:
                lines.append(f"    V({output}) <+ 0.0;")
            lines.extend(["  end", "endmodule", ""])
        artifacts[path] = "\n".join(lines)
    expected = sorted(str(value) for value in contract.get("target_artifacts") or [])
    if sorted(artifacts) != expected:
        raise ValueError("public artifact contract and target_artifacts disagree")
    return artifacts


class ScriptedClient:
    """OpenAI-compatible deterministic client used only by this integration smoke."""

    def __init__(self, model: str, responses: list[dict[str, Any]]) -> None:
        self.model = model
        self._responses = list(responses)

    def complete(self, _messages, _max_tokens, _tools, **_kwargs):
        if not self._responses:
            raise RuntimeError("deterministic smoke client exhausted its response script")
        message = self._responses.pop(0)
        return {
            "id": f"r53-smoke-{len(self._responses)}",
            "model": self.model,
            "choices": [{"finish_reason": "tool_calls", "message": message}],
            "usage": {"completion_tokens": 1},
        }


def tool_call(name: str, arguments: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "id": f"r53-smoke-call-{index}",
        "type": "function",
        "function": {"name": name, "arguments": json.dumps(arguments)},
    }


def client_for_arm(
    arm: str,
    artifacts: dict[str, str],
    model: str,
    public_evas_command: str,
) -> ScriptedClient:
    if arm == "OneShot":
        message = {
            "role": "assistant",
            "content": "",
            "tool_calls": [tool_call("submit_artifacts", {"artifacts": artifacts}, 0)],
        }
        return ScriptedClient(model, [message])

    commands = []
    for path, content in sorted(artifacts.items()):
        encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
        commands.append(
            f"mkdir -p public/submission/{shlex.quote(str(Path(path).parent))} && "
            f"printf %s {shlex.quote(encoded)} | base64 -d > "
            f"public/submission/{shlex.quote(path)}"
        )
    if arm == "Agentic":
        commands.append(f"{public_evas_command} || true")
    commands.append("vabench-submit")
    responses = [
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [tool_call("bash", {"command": command}, index)],
        }
        for index, command in enumerate(commands)
    ]
    return ScriptedClient(model, responses)


def public_clean_room_manifest(
    runtime: Path,
    result: dict[str, Any],
    arm: str,
    sandbox: str,
) -> dict[str, Any]:
    public = runtime / "public"
    files = sorted(
        path.relative_to(public).as_posix()
        for path in public.rglob("*")
        if path.is_file()
    )
    forbidden = [
        item
        for item in files
        if any(part in FORBIDDEN_PUBLIC_PARTS for part in Path(item).parts)
    ]
    scaffold = result.get("agent_scaffold")
    isolated = not forbidden
    if arm in {"Agent-No-EVAS", "Agentic"}:
        isolated = isolated and isinstance(scaffold, dict)
        isolated = isolated and scaffold.get("evaluator_mounted") is False
        isolated = isolated and scaffold.get("network") is False
        isolated = isolated and scaffold.get("sandbox_backend") == sandbox
    else:
        policy = read_json(runtime / "MODEL_ACCESS_POLICY.json")
        isolated = isolated and policy.get("transport_tools") == ["submit_artifacts"]
    return {
        "runtime": str(runtime),
        "fresh_runtime": True,
        "sandbox_backend": sandbox if arm != "OneShot" else "provider_transport",
        "candidate_visible_root": str(public),
        "visible_to_candidate": ["task/*", "submission/*", "MODEL_ACCESS_POLICY.json"],
        "hidden_evaluator_mounted": False,
        "network": False,
        "forbidden_private_paths": forbidden,
        "private_paths_absent": not forbidden,
        "isolation_contract_satisfied": isolated,
    }


def source_trajectory_identities(runtime: Path) -> list[dict[str, Any]]:
    candidates = [
        runtime / "evidence" / "conversation_checkpoint.json",
        runtime / "evidence" / "mini_swe_trajectory.json",
        runtime / "evidence" / "campaign_checkpoint.json",
    ]
    return [file_identity(path) for path in candidates if path.is_file()]


def write_trajectory_chain(
    runtime: Path,
    result: dict[str, Any],
    final_submission: dict[str, Any],
) -> dict[str, Any]:
    source_events: list[dict[str, Any]] = []
    source_events.extend(dict(event) for event in result.get("events") or [])
    source_events.extend(
        {"type": "tool", "name": "bash", **dict(command)}
        for command in result.get("commands") or []
    )
    source_events.extend(
        {"type": "evas_invocation", **dict(invocation)}
        for invocation in result.get("evas_invocations") or []
    )
    source_events.append(
        {
            "type": "submission_freeze",
            "tree_sha256": final_submission["tree_sha256"],
            "immutable": final_submission.get("immutable") is True,
        }
    )
    records: list[dict[str, Any]] = []
    previous: str | None = None
    cell_id = str(result["cell"]["cell_id"])
    for index, event in enumerate(source_events):
        record = {
            "schema_version": "v4-r53-trajectory-chain-event-v1",
            "cell_id": cell_id,
            "event_index": index,
            "prev_event_sha256": previous,
            "event": event,
        }
        record["event_sha256"] = canonical_sha256(record)
        previous = record["event_sha256"]
        records.append(record)
    path = runtime / "evidence" / "trajectory_chain.jsonl"
    encoded = "".join(canonical_json(record) + "\n" for record in records).encode()
    if path.exists() and path.read_bytes() != encoded:
        raise ValueError(f"trajectory chain already exists with different bytes: {path}")
    if not path.exists():
        path.write_bytes(encoded)
        path.chmod(0o444)
    verified = verify_trajectory_chain(path)
    return {
        "path": str(path),
        "exists": True,
        "sha256": sha256_file(path),
        "event_count": len(records),
        "chain_head_sha256": previous,
        "chain_verified": verified,
        "source_trajectories": source_trajectory_identities(runtime),
    }


def verify_trajectory_chain(path: Path) -> bool:
    previous: str | None = None
    for index, line in enumerate(path.read_text(encoding="utf-8").splitlines()):
        record = json.loads(line)
        observed = record.pop("event_sha256", None)
        if record.get("event_index") != index:
            return False
        if record.get("prev_event_sha256") != previous:
            return False
        expected = canonical_sha256(record)
        if observed != expected:
            return False
        previous = observed
    return previous is not None


def score_sidecar_payload(
    row: dict[str, Any],
    cell: dict[str, Any],
    release: dict[str, Any],
) -> dict[str, Any]:
    replay = row.get("trusted_replay") or {}
    return {
        "schema_version": "v4-r53-evas-score-sidecar-v1",
        "cell_id": cell["cell_id"],
        "task_id": cell["task_id"],
        "experimental_arm": cell["experimental_arm"],
        "release_manifest_sha256": release["manifest_sha256"],
        "judge_engine": "evas",
        "judge_runtime": "evas-sim==0.8.7",
        "score_authority": "development_only",
        "paper_result_authority": False,
        "judge_status": row.get("judge_status"),
        "outcome": row.get("outcome"),
        "failure_taxonomy": row.get("failure_taxonomy"),
        "submission_tree_sha256": replay.get("submission_tree_sha256"),
        "trusted_replay_status": replay.get("status"),
        "trusted_replay_input_signature_sha256": replay.get(
            "input_signature_sha256"
        ),
        "trusted_replay_diagnostics": list(replay.get("diagnostics") or []),
        "evas_identity": replay.get("evas_identity") or {},
    }


def write_score_sidecar(
    runtime: Path,
    row: dict[str, Any],
    cell: dict[str, Any],
    release: dict[str, Any],
) -> dict[str, Any]:
    payload = score_sidecar_payload(row, cell, release)
    digest = canonical_sha256(payload)
    path = runtime / "evidence" / "score_sidecars" / f"{digest}.json"
    write_immutable_json(path, payload)
    return {**payload, "path": str(path), "sha256": sha256_file(path)}


def configure_runner_args(args: argparse.Namespace, output: Path, identity: dict[str, Any]) -> None:
    args.output = output
    args.resume = False
    args.dry_run = False
    args.final_judge_command = None
    args.agent_scaffold = "mini-swe"
    args.mini_swe_sandbox = args.sandbox
    args.mini_swe_image = args.mini_swe_image
    args.mini_swe_no_evas_image = args.mini_swe_no_evas_image
    args.mini_swe_preflight_timeout_s = args.preflight_timeout_s
    args.mini_swe_preflight_attempts = args.preflight_attempts
    args.docker_command = args.docker_command
    args.evas_identity = identity


def run_smoke(args: argparse.Namespace) -> dict[str, Any]:
    started = time.perf_counter()
    args.release = args.release.expanduser().resolve()
    args.output_root = args.output_root.expanduser().resolve()
    if args.output_root.exists() and any(args.output_root.iterdir()):
        raise ValueError("--output-root must be absent or empty for fresh clean rooms")
    args.output_root.mkdir(parents=True, exist_ok=True)
    if args.sandbox != "docker" and not args.allow_insecure_test_sandbox:
        raise ValueError("non-Docker smoke requires --allow-insecure-test-sandbox")

    release = release_summary(args.release)
    contract = public_contract(args.release, args.task_id)
    artifacts = public_stub_artifacts(contract)
    public_evas_command = str((contract.get("evas") or {}).get("command") or "")
    if not public_evas_command:
        raise ValueError("public contract does not declare an EVAS command")
    evas_command, evas_identity = resolve_evas_command(args.evas_command)
    args.evas_command = evas_command
    cells = three_arm_cells(args.release, args.task_id, args.model)
    run_root = args.output_root / "run"
    configure_runner_args(args, run_root, evas_identity)

    rows: list[dict[str, Any]] = []
    cell_reports: list[dict[str, Any]] = []
    blockers: list[str] = []
    runtime_paths: set[str] = set()
    for cell in cells:
        arm = str(cell["experimental_arm"])
        client = client_for_arm(arm, artifacts, args.model, public_evas_command)
        result = run_campaign.run_cell(cell, args, client)
        runtime = Path(result["runtime"]).resolve()
        runtime_paths.add(str(runtime))
        result_path = runtime / "evidence" / "campaign_result.json"
        result["candidate_fixture"] = {
            "kind": "intentionally_incomplete_public_smoke_candidate",
            "source_boundary": "public_contract_only",
        }
        final_submission = result["experiment_result"]["final_submission"]
        trajectory = write_trajectory_chain(runtime, result, final_submission)
        result["trajectory_chain"] = trajectory
        write_json(result_path, result)

        clean_room = public_clean_room_manifest(runtime, result, arm, args.sandbox)
        row = score_campaign.evaluate_cell(
            result_path,
            args.judge_command,
            args.judge_timeout_s,
            args.evas_command,
            False,
            args.testbench_timeout_s,
            write_back=False,
        )
        rows.append(row)
        sidecar = write_score_sidecar(runtime, row, cell, release)
        evas_usage = result.get("evas_usage") or run_campaign.summarize_evas_invocations(
            []
        )
        cell_reports.append(
            {
                "cell_id": cell["cell_id"],
                "task_id": cell["task_id"],
                "form": cell["form"],
                "mode": cell["mode"],
                "experimental_arm": arm,
                "executable_feedback": cell["executable_feedback"],
                "status": result["status"],
                "candidate_fixture": result["candidate_fixture"],
                "clean_room_contract": clean_room,
                "trajectory": trajectory,
                "final_submission": final_submission,
                "evas_usage": evas_usage,
                "score_sidecar": sidecar,
            }
        )

        if result["status"] != "submitted":
            blockers.append(f"submission_not_terminal:{cell['cell_id']}")
        if not clean_room["isolation_contract_satisfied"]:
            blockers.append(f"clean_room_contract_failed:{cell['cell_id']}")
        if not trajectory["chain_verified"]:
            blockers.append(f"trajectory_chain_failed:{cell['cell_id']}")
        if sidecar["submission_tree_sha256"] != final_submission["tree_sha256"]:
            blockers.append(f"score_submission_hash_mismatch:{cell['cell_id']}")
        if row.get("judge_status") not in STRUCTURED_SCORE_STATUSES:
            blockers.append(f"structured_evas_score_missing:{cell['cell_id']}")
        if arm == "Agent-No-EVAS" and int(evas_usage.get("calls_executed", 0)) != 0:
            blockers.append(f"no_evas_arm_invoked_evas:{cell['cell_id']}")
        if arm == "Agentic" and int(evas_usage.get("calls_executed", 0)) < 1:
            blockers.append(f"agentic_arm_did_not_invoke_evas:{cell['cell_id']}")

    if len(runtime_paths) != 3:
        blockers.append("condition_runtimes_not_distinct")
    if args.sandbox != "docker":
        blockers.append("clean_room_requires_docker")

    score_report = score_campaign.summarize(rows, "final_trusted_replay")
    score_report["score_authority"] = "development_only_evas_0.8.7"
    score_report["paper_result_authority"] = False
    score_report_path = args.output_root / "SCORE_EVAS_0_8_7.json"
    write_immutable_json(score_report_path, score_report)
    blockers = sorted(set(blockers))
    claim_allowed = not blockers
    payload = {
        "date": now(),
        "benchmark": "benchmark-vabench-release-v4",
        "smoke": "r53_three_arm_clean_room_hidden_scoring",
        "status": "PASS" if claim_allowed else "FAIL",
        "benchmark_release": release,
        "task_id": args.task_id,
        "model": args.model,
        "comparison_profile": "executable-feedback-control-v1",
        "cells": cell_reports,
        "score_report": {
            "path": str(score_report_path),
            "sha256": sha256_file(score_report_path),
            "cell_count": score_report["cell_count"],
            "judge_statuses": score_report["judge_statuses"],
            "score_authority": score_report["score_authority"],
            "paper_result_authority": False,
        },
        "execution_policy": {
            "python_version": platform.python_version(),
            "sandbox": args.sandbox,
            "evas_command": args.evas_command,
            "evas_identity": evas_identity,
            "judge_command": args.judge_command,
            "agent_timeout_s": args.agent_timeout_s,
            "judge_timeout_s": args.judge_timeout_s,
            "persistent_worker": False,
        },
        "wall_s": round(time.perf_counter() - started, 6),
        "claim_scope": PIPELINE_CLAIM_SCOPE,
        "claim_gate": {
            "scope": PIPELINE_CLAIM_SCOPE,
            "status": "allowed" if claim_allowed else "blocked",
            "allowed": claim_allowed,
            "blocking_reasons": blockers,
            "model_score_claim_allowed": False,
            "paper_result_claim_allowed": False,
            "spectre_required": False,
            "paper_result_requires_spectre": True,
            "supports": (
                "one r53 task across matched OneShot, Agent-No-EVAS, and Agentic "
                "harness/evaluator connectivity only"
            ),
        },
    }
    if args.out:
        out_path = args.out.expanduser().resolve()
        write_json(out_path, payload)
        payload["paths"] = {"smoke_json": str(out_path)}
    return payload


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", type=Path, default=DEFAULT_RELEASE)
    parser.add_argument("--task-id", default=DEFAULT_TASK_ID)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--evas-command", default="evas")
    parser.add_argument(
        "--judge-command",
        default=f"{sys.executable} {CALIBRATION / 'trusted_replay_adapter.py'}",
    )
    parser.add_argument("--sandbox", choices=("docker", "none"), default="docker")
    parser.add_argument("--allow-insecure-test-sandbox", action="store_true")
    parser.add_argument("--docker-command", default="docker")
    parser.add_argument("--mini-swe-image", default=DEFAULT_EVAS_IMAGE)
    parser.add_argument("--mini-swe-no-evas-image", default=DEFAULT_NO_EVAS_IMAGE)
    parser.add_argument("--setup-timeout-s", type=int, default=1800)
    parser.add_argument("--agent-timeout-s", type=int, default=1800)
    parser.add_argument("--request-timeout-s", type=int, default=1800)
    parser.add_argument("--tool-timeout-s", type=int, default=180)
    parser.add_argument("--judge-timeout-s", type=int, default=180)
    parser.add_argument("--testbench-timeout-s", type=int, default=750)
    parser.add_argument("--preflight-timeout-s", type=int, default=60)
    parser.add_argument("--preflight-attempts", type=int, default=2)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        payload = run_smoke(args)
    except Exception as exc:  # noqa: BLE001 - CLI emits a structured blocker.
        payload = {
            "date": now(),
            "benchmark": "benchmark-vabench-release-v4",
            "smoke": "r53_three_arm_clean_room_hidden_scoring",
            "status": "FAIL",
            "failure": f"{type(exc).__name__}: {exc}",
            "claim_gate": {
                "scope": PIPELINE_CLAIM_SCOPE,
                "status": "blocked",
                "allowed": False,
                "blocking_reasons": ["smoke_exception"],
                "model_score_claim_allowed": False,
                "paper_result_claim_allowed": False,
                "spectre_required": False,
                "paper_result_requires_spectre": True,
            },
        }
        if getattr(args, "out", None):
            write_json(args.out.expanduser().resolve(), payload)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 1
    if args.json or not args.out:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(
            "[v4-r53-clean-room-smoke] "
            f"status={payload['status']} task={payload['task_id']}"
        )
    return 0 if payload["claim_gate"]["allowed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
