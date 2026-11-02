#!/usr/bin/env python3
"""Build and run a benchmarkv4 model campaign with direct and agentic modes.

This is the operator-facing entry point for API experiments.  It builds a
campaign from ``release/benchmarkv4-r51`` and delegates execution to the v4
calibration runner:

* G0/G1 use direct one-shot artifact extraction.
* G2-G5 run in a pinned mini-SWE-agent scaffold with one bash tool. The public
  workspace exposes task/, submission/, and EVAS diagnostics; evaluator and
  trusted-replay assets stay outside the model shell.

The result is still an experiment runner, not the final Spectre scorer.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any


PACKAGE = Path(__file__).resolve().parents[1]
REPO = PACKAGE.parent
CALIBRATION = PACKAGE / "operations" / "calibration_pilot"
DEFAULT_RELEASE = PACKAGE / "release" / "benchmarkv4-r51"
DEFAULT_AGENT_TIMEOUT_S = 5400
DEFAULT_SETUP_TIMEOUT_S = 1800
DEFAULT_REQUEST_TIMEOUT_S = 1800
DEFAULT_TOOL_TIMEOUT_S = 1800
DEFAULT_JUDGE_TIMEOUT_S = 1800
DEFAULT_DOCKER_IMAGE = "vabench-agent-runtime:0.8.4"
DEFAULT_NOEXEC_DOCKER_IMAGE = "vabench-agent-runtime:0.8.4-noexec"
MODES = tuple(f"G{i}" for i in range(6))
EXECUTABLE_FEEDBACK_ARMS = (
    ("OneShot", "oneshot", "G0", False),
    ("Agent-NoExec", "noexec", "G2", False),
    ("Agentic", "agentic", "G2", True),
)
if str(CALIBRATION) not in sys.path:
    sys.path.insert(0, str(CALIBRATION))
from build_campaign import build_campaign  # noqa: E402
import result_protocol as RESULT_PROTOCOL  # noqa: E402


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def resolve_evas_command(command: str) -> tuple[str, dict[str, Any]]:
    argv = shlex.split(command)
    identity = RESULT_PROTOCOL.evas_identity(argv)
    if not identity.get("available") or not identity.get("resolved_executable"):
        raise SystemExit(
            "configured --evas-command is unavailable or has no version identity: "
            f"{identity.get('error') or identity.get('version_output') or command}"
        )
    argv[0] = str(Path(identity["resolved_executable"]).resolve())
    identity = RESULT_PROTOCOL.evas_identity(argv)
    if not identity.get("available"):
        raise SystemExit("resolved --evas-command failed identity verification")
    return shlex.join(argv), identity


def command_for_metadata(command: list[str]) -> list[str]:
    """Keep reproducible structure without persisting credential-adjacent paths."""
    redacted_values = {
        "--api-key-file": "<redacted-credential-file>",
        "--final-judge-command": "<redacted-operator-command>",
    }
    sanitized: list[str] = []
    redact_next: str | None = None
    for token in command:
        if redact_next is not None:
            sanitized.append(redact_next)
            redact_next = None
            continue
        sanitized.append(token)
        redact_next = redacted_values.get(token)
    return sanitized


def text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def build_executable_feedback_control(campaign: dict[str, Any]) -> dict[str, Any]:
    """Project a standard G0-G5 campaign onto the three matched study arms."""
    source_cells = {
        (cell["task_id"], cell["mode"], cell["repetition"]): cell
        for cell in campaign["cells"]
    }
    task_repetitions = sorted(
        {
            (cell["task_id"], cell["repetition"])
            for cell in campaign["cells"]
        }
    )
    cells: list[dict[str, Any]] = []
    for task_id, repetition in task_repetitions:
        for arm, slug, mode, executable_feedback in EXECUTABLE_FEEDBACK_ARMS:
            source = source_cells[(task_id, mode, repetition)]
            cell = dict(source)
            cell.update(
                {
                    "cell_id": f"{source['cell_id']}-{slug}",
                    "experimental_arm": arm,
                    "executable_feedback": executable_feedback,
                    "evas_cli_available": executable_feedback,
                    "base_mode": mode,
                }
            )
            cells.append(cell)

    projected = dict(campaign)
    projected.update(
        {
            "schema_version": "v4-executable-feedback-control-campaign-v1",
            "comparison_profile": "executable-feedback-control-v1",
            "arms": [arm for arm, _slug, _mode, _feedback in EXECUTABLE_FEEDBACK_ARMS],
            "arm_count": len(EXECUTABLE_FEEDBACK_ARMS),
            "mode_count": len({cell["mode"] for cell in cells}),
            "cell_count": len(cells),
            "cells": cells,
        }
    )
    return projected


def filter_campaign(campaign: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    modes = set(args.mode or MODES)
    forms = set(args.form or ("dut", "testbench", "bugfix"))
    task_ids = set(args.task_id or [])
    experimental_arms = set(args.experimental_arm or [])
    cells = [
        cell
        for cell in campaign["cells"]
        if cell["mode"] in modes
        and cell["form"] in forms
        and (not task_ids or cell["task_id"] in task_ids)
        and (
            not experimental_arms
            or cell.get("experimental_arm") in experimental_arms
        )
    ]
    if args.limit is not None:
        cells = cells[: args.limit]
    if not cells:
        raise SystemExit("no campaign cells match the requested filters")
    campaign = dict(campaign)
    campaign["cells"] = cells
    campaign["cell_count"] = len(cells)
    campaign["mode_count"] = len({cell["mode"] for cell in cells})
    if campaign.get("comparison_profile"):
        campaign["arm_count"] = len(
            {cell["experimental_arm"] for cell in cells}
        )
    campaign["task_count"] = len({cell["task_id"] for cell in cells})
    campaign["family_count"] = len({cell["family_id"] for cell in cells})
    campaign["status"] = "planned_filtered"
    campaign["filters"] = {
        "modes": sorted(modes),
        "forms": sorted(forms),
        "task_ids": sorted(task_ids),
        "experimental_arms": sorted(experimental_arms),
        "limit": args.limit,
    }
    return campaign


def family_ids_for_task_ids(release: Path, task_ids: list[str] | None) -> list[str] | None:
    if not task_ids:
        return None
    index = read_json(release / "TASK_INDEX.json")["tasks"]
    by_task = {str(row["task_id"]): str(row["family_id"]) for row in index}
    missing = [task_id for task_id in task_ids if task_id not in by_task]
    if missing:
        raise SystemExit(f"unknown task-id(s): {', '.join(missing)}")
    return sorted({by_task[task_id] for task_id in task_ids}, key=lambda value: int(value))


def parse_family_range(value: str) -> list[str]:
    try:
        start_text, end_text = value.split("-", 1)
        start = int(start_text)
        end = int(end_text)
    except (ValueError, TypeError) as exc:
        raise argparse.ArgumentTypeError("family range must be START-END") from exc
    if start <= 0 or end < start:
        raise argparse.ArgumentTypeError("family range must satisfy 1 <= START <= END")
    return [str(family_id) for family_id in range(start, end + 1)]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", type=Path, default=DEFAULT_RELEASE)
    parser.add_argument("--selection", type=Path)
    parser.add_argument("--sample-families", type=int)
    parser.add_argument(
        "--family-range",
        type=parse_family_range,
        help="Select an inclusive deterministic family range, for example 351-400.",
    )
    parser.add_argument(
        "--comparison-profile",
        choices=("executable-feedback-control",),
        help=(
            "Run a matched control profile. Currently supported: "
            "executable-feedback-control."
        ),
    )
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--mode", action="append", choices=MODES)
    parser.add_argument("--form", action="append", choices=("dut", "testbench", "bugfix"))
    parser.add_argument("--task-id", action="append")
    parser.add_argument(
        "--experimental-arm",
        action="append",
        choices=(
            "OneShot",
            "Agent-NoExec",
            "Agentic",
        ),
        help="Keep only the selected arm(s) after applying a comparison profile.",
    )
    parser.add_argument("--limit", type=int)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--model-provider", default="openai-compatible")
    parser.add_argument("--model", required=True)
    parser.add_argument("--base-url", default="https://api.deepseek.com/v1")
    parser.add_argument("--api-key-file")
    parser.add_argument("--api-key-env", default="DEEPSEEK_API_KEY")
    parser.add_argument(
        "--per-turn-max-tokens",
        "--max-output-tokens",
        "--max-working-tokens",
        dest="per_turn_max_tokens",
        type=int,
        default=65536,
        help="Provider per-call max_tokens cap. This is not a cumulative episode budget.",
    )
    parser.add_argument("--repetitions", type=int, default=1)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument(
        "--agent-scaffold",
        choices=("mini-swe", "native"),
        default="mini-swe",
        help="Use pinned mini-SWE-agent for G2-G5; native is a legacy sensitivity path.",
    )
    parser.add_argument(
        "--mini-swe-sandbox",
        choices=("auto", "docker", "sandbox-exec", "bubblewrap", "none"),
        default="auto",
        help="Formal runs use the upstream shared Docker environment; 'none' is test-only.",
    )
    parser.add_argument("--docker-command", default="docker")
    parser.add_argument("--mini-swe-image", default=DEFAULT_DOCKER_IMAGE)
    parser.add_argument("--mini-swe-noexec-image", default=DEFAULT_NOEXEC_DOCKER_IMAGE)
    parser.add_argument("--agent-timeout-s", type=int, default=DEFAULT_AGENT_TIMEOUT_S)
    parser.add_argument("--setup-timeout-s", type=int, default=DEFAULT_SETUP_TIMEOUT_S)
    parser.add_argument("--request-timeout-s", type=int, default=DEFAULT_REQUEST_TIMEOUT_S)
    parser.add_argument("--tool-timeout-s", type=int, default=DEFAULT_TOOL_TIMEOUT_S)
    parser.add_argument("--judge-timeout-s", type=int, default=DEFAULT_JUDGE_TIMEOUT_S)
    parser.add_argument("--final-judge-command")
    parser.add_argument(
        "--evas-command",
        help="Explicit EVAS command required for executable campaigns; omitted only for dry-run planning.",
    )
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument(
        "--api-max-inflight",
        type=int,
        help="Maximum simultaneous provider requests; defaults to --workers.",
    )
    parser.add_argument("--stream", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    selectors = (args.selection, args.sample_families, args.family_range)
    if sum(selector is not None for selector in selectors) > 1:
        raise SystemExit(
            "use only one of --selection, --sample-families, or --family-range"
        )
    if args.comparison_profile and args.mode:
        raise SystemExit("--mode cannot be combined with --comparison-profile")
    if (
        args.comparison_profile
        in {"executable-feedback-control"}
        and args.agent_scaffold != "mini-swe"
    ):
        raise SystemExit(
            f"{args.comparison_profile} requires --agent-scaffold mini-swe"
        )
    if not args.dry_run and not args.evas_command:
        raise SystemExit("--evas-command is required for executable campaigns")
    evas_identity = None
    if args.evas_command:
        args.evas_command, evas_identity = resolve_evas_command(args.evas_command)
    if args.per_turn_max_tokens <= 0:
        raise SystemExit("--per-turn-max-tokens must be positive")
    if args.repetitions <= 0:
        raise SystemExit("--repetitions must be positive")
    if args.workers <= 0:
        raise SystemExit("--workers must be positive")
    if args.api_max_inflight is not None and args.api_max_inflight <= 0:
        raise SystemExit("--api-max-inflight must be positive")
    if min(
        args.agent_timeout_s,
        args.setup_timeout_s,
        args.request_timeout_s,
        args.tool_timeout_s,
        args.judge_timeout_s,
    ) <= 0:
        raise SystemExit("all timeout values must be positive")
    if (
        args.agent_scaffold == "mini-swe"
        and args.mini_swe_sandbox == "none"
        and any(mode in {"G2", "G3", "G4", "G5"} for mode in (args.mode or MODES))
        and not args.dry_run
    ):
        raise SystemExit(
            "--mini-swe-sandbox none is test-only; use a supported secure sandbox "
            "for executable G2-G5 campaigns"
        )
    if (
        args.agent_scaffold == "mini-swe"
        and args.mini_swe_sandbox not in {"auto", "docker", "none"}
        and any(mode in {"G2", "G3", "G4", "G5"} for mode in (args.mode or MODES))
        and not args.dry_run
    ):
        raise SystemExit(
            "paper-valid mini-SWE campaigns require the upstream shared Docker "
            "environment; legacy host sandboxes are sensitivity-only"
        )
    release = args.release.expanduser().resolve()
    output_root = args.output_root.expanduser().resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    explicit_family_ids = None
    if args.family_range is not None:
        explicit_family_ids = args.family_range
    elif args.task_id and args.selection is None and args.sample_families is None:
        explicit_family_ids = family_ids_for_task_ids(release, args.task_id)
    campaign = build_campaign(
        release,
        selection_path=args.selection.expanduser().resolve() if args.selection else None,
        sample_families=args.sample_families,
        family_ids=explicit_family_ids,
        seed=args.seed,
        model_provider=args.model_provider,
        model=args.model,
        per_turn_max_tokens=args.per_turn_max_tokens,
        repetitions=args.repetitions,
    )
    if args.comparison_profile == "executable-feedback-control":
        campaign = build_executable_feedback_control(campaign)
    campaign = filter_campaign(campaign, args)
    campaign["execution_config"] = {
        "schema_version": "v4-campaign-execution-config-v1",
        "termination_policy": "wall_time",
        "agent_timeout_s": args.agent_timeout_s,
        "setup_timeout_s": args.setup_timeout_s,
        "request_timeout_s": args.request_timeout_s,
        "tool_timeout_s": args.tool_timeout_s,
        "judge_timeout_s": args.judge_timeout_s,
        "cell_workers": args.workers,
        "api_max_inflight": args.api_max_inflight or args.workers,
        "per_turn_max_tokens": args.per_turn_max_tokens,
        "token_accounting": "telemetry_only",
        "agent_scaffold": args.agent_scaffold,
        "mini_swe_sandbox": args.mini_swe_sandbox,
        "mini_swe_image": args.mini_swe_image,
        "mini_swe_noexec_image": args.mini_swe_noexec_image,
        "base_url_sha256": text_sha256(args.base_url.rstrip("/")),
        "temperature": args.temperature,
        "stream": args.stream,
        "comparison_profile": campaign.get("comparison_profile"),
        "controlled_difference": (
            "public_evas_execution_diagnostics_and_waveforms"
            if args.comparison_profile == "executable-feedback-control"
            else None
        ),
        "final_judge_configured": bool(args.final_judge_command),
        "final_judge_command_sha256": text_sha256(args.final_judge_command or ""),
        "evas_command_sha256": text_sha256(args.evas_command or ""),
        "evas_command": args.evas_command,
        "evas_identity": evas_identity,
    }
    campaign_path = output_root / "campaign.json"
    write_json(campaign_path, campaign)
    command = [
        sys.executable,
        str(CALIBRATION / "run_campaign.py"),
        "--campaign",
        str(campaign_path),
        "--release",
        str(release),
        "--output",
        str(output_root / "run"),
        "--base-url",
        args.base_url,
        "--api-key-env",
        args.api_key_env,
        "--temperature",
        str(args.temperature),
        "--agent-scaffold",
        args.agent_scaffold,
        "--mini-swe-sandbox",
        args.mini_swe_sandbox,
        "--docker-command",
        args.docker_command,
        "--mini-swe-image",
        args.mini_swe_image,
        "--mini-swe-noexec-image",
        args.mini_swe_noexec_image,
        "--agent-timeout-s",
        str(args.agent_timeout_s),
        "--setup-timeout-s",
        str(args.setup_timeout_s),
        "--request-timeout-s",
        str(args.request_timeout_s),
        "--tool-timeout-s",
        str(args.tool_timeout_s),
        "--judge-timeout-s",
        str(args.judge_timeout_s),
        "--workers",
        str(args.workers),
    ]
    if args.api_max_inflight is not None:
        command.extend(["--api-max-inflight", str(args.api_max_inflight)])
    if args.evas_command:
        command.extend(["--evas-command", args.evas_command])
    if args.api_key_file:
        command.extend(["--api-key-file", args.api_key_file])
    if args.final_judge_command:
        command.extend(["--final-judge-command", args.final_judge_command])
    if args.stream:
        command.append("--stream")
    if args.dry_run:
        command.append("--dry-run")
    if args.resume:
        command.append("--resume")
    metadata = {
        "schema_version": "v4-benchmarkv4-campaign-wrapper-v1",
        "campaign": str(campaign_path),
        "run_output": str(output_root / "run"),
        "release": str(release),
        "model": args.model,
        "base_url": args.base_url,
        "workers": args.workers,
        "api_max_inflight": args.api_max_inflight or args.workers,
        "dry_run": args.dry_run,
        "command": command_for_metadata(command),
    }
    write_json(output_root / "wrapper_summary.json", metadata)
    completed = subprocess.run(command, cwd=REPO, check=False)
    metadata["returncode"] = completed.returncode
    run_summary = output_root / "run" / "SUMMARY.json"
    if run_summary.is_file():
        metadata["run_summary"] = read_json(run_summary)
    write_json(output_root / "wrapper_summary.json", metadata)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
