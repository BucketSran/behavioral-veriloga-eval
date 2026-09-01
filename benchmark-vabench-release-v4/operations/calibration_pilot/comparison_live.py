"""Explicit named-service comparison preparation; never an automatic paid run."""

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import argparse
import json
from pathlib import Path
import re
import subprocess

from deepseek_budget import (
    BudgetedDeepSeekClient,
    CONTEXT_TOKEN_BOUND,
    MAX_OUTPUT_TOKENS,
    MODEL,
    PRICING_REVIEWED_ON,
    PRICING_SCHEDULES,
    RATES,
)
from pilot_credentials import load_pilot_key
from run_deepseek_pilot import clear_provider_environment, provider_preflight
from runners.agent_harness.batch_resume import _atomic_once, docker_image_identity, file_sha256


REVIEWED_ON = PRICING_REVIEWED_ON
PREVIOUS_REVIEWED_ON = "2026-08-31"
ENDPOINT = "https://api.deepseek.com/v1/chat/completions"


def build_provider_profile(*, currency: str, cap: str) -> dict:
    """Dated, bounded profile; the cap is proposed, not spending authority."""
    try:
        amount = Decimal(cap)
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError("invalid comparison cap") from None
    if currency not in RATES or not amount.is_finite() or not 0 < amount <= RATES[currency][2]:
        raise ValueError("comparison cap outside the supported guard range")
    return {
        "schema_version": "vaevas-deepseek-comparison-profile-v1",
        "service": "deepseek", "endpoint": ENDPOINT, "model": MODEL,
        "documented_model_version": "DeepSeek-V4-Flash-0731",
        "model_snapshot_policy": "provider_alias_not_immutable_snapshot",
        "reviewed_on": REVIEWED_ON, "valid_through_utc": REVIEWED_ON,
        "pricing_sources": ["https://api-docs.deepseek.com/quick_start/pricing/",
                            "https://api-docs.deepseek.com/zh-cn/quick_start/pricing/"],
        "currency": currency, "cap": str(amount),
        "input_peak_per_million": str(RATES[currency][0]),
        "output_peak_per_million": str(RATES[currency][1]),
        "pricing_schedule": PRICING_SCHEDULES[currency],
        "context_token_bound": CONTEXT_TOKEN_BOUND,
        "decoding": {"temperature": 0, "thinking": {"type": "disabled"},
                     "stream": True, "stream_options": {"include_usage": True},
                     "max_tokens": MAX_OUTPUT_TOKENS, "tool_choice": "auto"},
    }


def validate_provider_profile(profile: dict, *, currency: str, cap: str, for_launch=False) -> None:
    current = build_provider_profile(currency=currency, cap=cap)
    previous = dict(current)
    previous.pop("pricing_schedule")
    previous.update(reviewed_on=PREVIOUS_REVIEWED_ON, valid_through_utc=PREVIOUS_REVIEWED_ON)
    if profile != current and (for_launch or profile != previous):
        raise ValueError("frozen provider profile mismatch")
    if for_launch and datetime.now(timezone.utc).date().isoformat() != profile["valid_through_utc"]:
        raise ValueError("provider profile expired; review rates and freeze a fresh profile")


def _authorization(root, manifest):
    return {"schema_version": "vaevas-comparison-live-authorization-v1",
            "manifest_sha256": file_sha256(root / "comparison-manifest.json"),
            "approved_cap": manifest["budget"]["cap"], "currency": manifest["budget"]["currency"],
            "authority": "operator_assertion_not_authenticated_identity"}


def validate_live_authorization(root: Path, manifest: dict) -> str:
    from run_legacy_native_comparison import _source_path
    path = _source_path(root, "live-authorization.json")
    if json.loads(path.read_text()) != _authorization(root, manifest):
        raise ValueError("live authorization differs from frozen manifest/cap")
    return file_sha256(path)


def validate_provider_preflight(root: Path, manifest: dict) -> str:
    from run_legacy_native_comparison import _source_path
    path = _source_path(root, "provider-preflight.json")
    value = json.loads(path.read_text())
    hashes = value.get("response_sha256", {})
    if (set(value) != {"currency", "model_available", "response_sha256"}
            or value["currency"] != manifest["budget"]["currency"] or value["model_available"] is not True
            or set(hashes) != {"/models", "/user/balance"}
            or any(not isinstance(v, str) or not re.fullmatch(r"[0-9a-f]{64}", v) for v in hashes.values())):
        raise ValueError("invalid comparison provider preflight")
    return file_sha256(path)


class LiveComparisonClient(BudgetedDeepSeekClient):
    """Observe requests; retain the existing budget, curl, SSE and redaction."""

    def __init__(self, *, budget, cell_id, api_key, request_observer, profile):
        super().__init__(budget=budget, cell_id=cell_id, api_key=api_key, timeout_s=1800)
        self.request_observer = request_observer
        self.profile = profile

    def _complete_stream(self, payload, *, timeout_s, transport_observer=None):
        validate_provider_profile(self.profile, currency=self.budget.currency,
                                  cap=str(self.budget.cap), for_launch=True)
        expected = {"model": self.profile["model"], **self.profile["decoding"]}
        if not payload.get("tools"):
            expected.pop("tool_choice")
        if {key: value for key, value in payload.items() if key not in {"messages", "tools"}} != expected:
            raise ValueError("request decoding differs from frozen provider profile")
        self.request_observer(payload, timeout_s)
        return super()._complete_stream(payload, timeout_s=timeout_s, transport_observer=transport_observer)


def execute_live_comparison(root: Path, *, expected_manifest_sha256: str, approved_cap: str,
                            currency: str, credential_file: Path, evas_command: str) -> dict:
    """Explicit one-use launch. A receipt is an operator assertion, not identity proof."""
    from run_legacy_native_comparison import ROOT, _execute_comparison, _source_path, _validate_frozen, runner

    clear_provider_environment()
    path = _source_path(root, "comparison-manifest.json")
    manifest = json.loads(path.read_text())
    if file_sha256(path) != expected_manifest_sha256:
        raise ValueError("expected comparison manifest hash mismatch")
    if (manifest["schema_version"] != "vaevas-workflow-comparison-live-v1"
            or approved_cap != manifest["budget"]["cap"] or currency != manifest["budget"]["currency"]):
        raise ValueError("live profile or approved cap/currency mismatch")
    _validate_frozen(root, manifest)
    validate_provider_profile(manifest["provider_profile"], currency=currency, cap=approved_cap, for_launch=True)
    runner.validate_pinned_evas_identity(evas_command, manifest["evas_identity"])
    image = manifest["controls"]["image_id_for_live_run"]
    if docker_image_identity(image) != image:
        raise ValueError("frozen comparison image unavailable or changed")
    if credential_file.resolve().is_relative_to(ROOT):
        raise ValueError("comparison credentials must be repository-external")
    if any((root / name).exists() for name in ("execution.jsonl", "budget.jsonl", "comparison-execution.json")):
        raise ValueError("live comparison cannot resume")
    _atomic_once(root / "live-authorization.json", _authorization(root, manifest))
    # From this reservation onward even preflight failure cannot silently retry.
    key = load_pilot_key(credential_file, "DEEPSEEK_API_KEY")
    preflight = provider_preflight(key)
    if preflight["currency"] != currency:
        raise ValueError("account currency differs from frozen comparison")
    _atomic_once(root / "provider-preflight.json", preflight)
    return _execute_comparison(root, manifest, evas_command=evas_command,
                               client_factory=lambda **kwargs: LiveComparisonClient(
                                   **kwargs, api_key=key, profile=manifest["provider_profile"]))


def inspect_preparation(root: Path) -> dict:
    from run_legacy_native_comparison import _source_path, _validate_frozen
    path = _source_path(root, "comparison-manifest.json")
    manifest = json.loads(path.read_text())
    _validate_frozen(root, manifest, current_source=False)
    return {"manifest_sha256": file_sha256(path), "live_authorized": False,
            "provider_profile": manifest.get("provider_profile"),
            "evidence_scope": manifest["evidence_scope"], "code_commit": manifest["code_commit"],
            "schedule": [{key: row[key] for key in ("comparison_cell_id", "task_id", "backend")}
                         for row in manifest["schedule"]]}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare", help="freeze local identities only; no credentials or HTTP")
    prepare.add_argument("--currency", choices=tuple(RATES), required=True)
    prepare.add_argument("--cap", required=True)
    prepare.add_argument("--image", required=True)
    prepare.add_argument("--evas-command", required=True)
    commands.add_parser("inspect", help="read the frozen profile and its approval hash")
    commands.add_parser("report", help="validate existing results; never rejudge")
    run = commands.add_parser("run", help="explicitly approved, potentially paid, one-use launch")
    run.add_argument("--expected-manifest-sha256", required=True)
    run.add_argument("--approve-cap", required=True)
    run.add_argument("--currency", choices=tuple(RATES), required=True)
    run.add_argument("--credential-file", type=Path, required=True)
    run.add_argument("--evas-command", required=True)
    for command in commands.choices.values():
        command.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args(argv)
    from run_legacy_native_comparison import ROOT, freeze_comparison, read_comparison, runner
    try:
        if args.command == "prepare":
            clear_provider_environment()
            profile = build_provider_profile(currency=args.currency, cap=args.cap)
            identity = runner.resolve_pinned_evas_identity(args.evas_command)
            image_id = docker_image_identity(args.image)
            commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
            freeze_comparison(args.output_root, image_id=image_id, code_commit=commit,
                              evas_identity=identity, currency=args.currency, cap=args.cap, provider_profile=profile)
            result = inspect_preparation(args.output_root)
        elif args.command == "inspect":
            result = inspect_preparation(args.output_root)
        elif args.command == "report":
            result = read_comparison(args.output_root)
        else:
            result = execute_live_comparison(
                args.output_root, expected_manifest_sha256=args.expected_manifest_sha256,
                approved_cap=args.approve_cap, currency=args.currency,
                credential_file=args.credential_file, evas_command=args.evas_command,
            )
        print(json.dumps(result, sort_keys=True))
        if args.command == "run" and any(row["disposition"] != "completed" for row in result["audit_rows"]):
            return 2
        return 0
    except Exception:
        # No credential paths, exception bodies, provider responses or balances.
        print("Comparison command failed; inspect the frozen configuration/private evidence. No automatic retry.")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
