#!/usr/bin/env python3
"""Read-only feature-use evidence projection for combined harness runs."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

from runners.agent_harness.trajectory import read_trajectory, validate_trajectory


SCHEMA_VERSION = "vaevas-combined-tool-evidence-v1"
_DOCS_TOOL = "vaevas_docs_search"
_WAVEFORM_TOOL = "vaevas_public_simulate"
_SUPPORTED_BACKENDS = frozenset({"native-reasoning", "evolution"})
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def collect_feature_use(run_dir: Path, *, backend: str) -> dict[str, Any]:
    """Project observed tool use without reading credentials or rerunning checks."""

    if backend not in _SUPPORTED_BACKENDS:
        raise ValueError("backend must be native-reasoning or evolution")
    root = _checked_root(run_dir)
    report = (
        _collect_native(root, backend=backend)
        if backend == "native-reasoning"
        else _collect_evolution(root, backend=backend)
    )
    report["report_sha256"] = canonical_sha256(report)
    return report


def canonical_sha256(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def _collect_native(root: Path, *, backend: str) -> dict[str, Any]:
    files: dict[str, Any] = {}
    incomplete: dict[str, list[str]] = {
        _DOCS_TOOL: [],
        _WAVEFORM_TOOL: [],
    }
    trajectory = _read_events(
        root,
        "evidence/native-episode/trajectory.jsonl",
        files=files,
        incomplete=incomplete[_WAVEFORM_TOOL],
    )
    private = _read_events(
        root,
        "evidence/native-launcher/private-events.jsonl",
        files=files,
        incomplete=incomplete[_DOCS_TOOL],
    )
    docs = _tool_counts(private, _DOCS_TOOL)
    waveform = _tool_counts(private, _WAVEFORM_TOOL)
    docs_exposed = _native_observation_exposed_requests(private, _DOCS_TOOL)
    waveform_exposed = _native_observation_exposed_requests(private, _WAVEFORM_TOOL)
    return _report(
        backend=backend,
        files=files,
        docs=_with_incomplete(docs, docs_exposed, incomplete[_DOCS_TOOL]),
        waveform=_with_incomplete(
            waveform,
            waveform_exposed,
            incomplete[_WAVEFORM_TOOL],
        ),
    )


def _collect_evolution(root: Path, *, backend: str) -> dict[str, Any]:
    files: dict[str, Any] = {}
    request = _read_json(root, "request.json", files=files)
    manifest_sha = _optional_sha256(request.get("manifest_sha256"))
    config = request.get("config") if isinstance(request, Mapping) else None
    rounds = _positive_int(
        config.get("rounds") if isinstance(config, Mapping) else None,
        "rounds",
    )
    roster = config.get("branch_roster") if isinstance(config, Mapping) else None
    if not isinstance(roster, list) or not roster:
        raise ValueError("evolution branch_roster must be a non-empty list")
    branch_ids = [_branch_id(branch) for branch in roster]
    docs_counts = Counter()
    waveform_counts = Counter()
    docs_missing: list[str] = []
    waveform_missing: list[str] = []
    prior_waveform_receipts: set[tuple[str, str]] = set()
    waveform_exposed = 0
    docs_exposed_total = 0
    branch_root = _evolution_branch_root(root)
    for round_index in range(rounds):
        round_waveform_receipts: set[tuple[str, str]] = set()
        for branch_id in branch_ids:
            prefix = f"{branch_root}/round-{round_index:04d}/{branch_id}"
            private = _read_events(
                root,
                f"{prefix}/private-events.jsonl",
                files=files,
                incomplete=docs_missing,
            )
            if f"{prefix}/private-events.jsonl" in docs_missing:
                waveform_missing.append(f"{prefix}/private-events.jsonl")
            _merge_counter(docs_counts, _tool_counts(private, _DOCS_TOOL))
            docs_exposed_total += _native_observation_exposed_requests(private, _DOCS_TOOL)
            if round_index > 0:
                waveform_exposed += _prior_candidate_exposed_requests(
                    private,
                    prior_waveform_receipts,
                )
            receipt = _read_optional_json(
                root,
                f"{prefix}/public-validation.json",
                files=files,
                incomplete=waveform_missing,
            )
            if receipt is None:
                continue
            identity = _valid_public_receipt(
                receipt,
                manifest_sha=manifest_sha,
                expected_branch_id=branch_id,
                expected_round_index=round_index,
                branch_dir=(root / prefix).resolve(),
            )
            if identity is None:
                continue
            waveform_counts["attempted"] += 1
            waveform_counts["succeeded"] += 1
            round_waveform_receipts.add(identity)
        prior_waveform_receipts.update(round_waveform_receipts)
    return _report(
        backend=backend,
        files=files,
        docs=_with_incomplete(docs_counts, docs_exposed_total, docs_missing),
        waveform=_with_incomplete(waveform_counts, waveform_exposed, waveform_missing),
    )


def _report(
    *,
    backend: str,
    files: Mapping[str, Any],
    docs: Mapping[str, Any],
    waveform: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "backend": backend,
        "source": {"files": dict(sorted(files.items()))},
        "features": {
            "offline_docs": docs,
            "public_waveform": waveform,
        },
        "claim_boundary": {
            "actual_model_consumption_claimed": False,
            "actual_improvement_claimed": False,
            "final_score_or_hidden_judge_exported": False,
            "raw_queries_snippets_waveforms_exported": False,
        },
    }


def _read_events(
    root: Path,
    relative: str,
    *,
    files: dict[str, Any],
    incomplete: list[str],
) -> list[dict[str, Any]]:
    path = _confined_file(root, relative)
    if path is None:
        incomplete.append(relative)
        return []
    files[relative] = _file_reference(path)
    events = read_trajectory(path)
    if not validate_trajectory(events):
        raise ValueError(f"{relative} event chain is corrupt")
    return events


def _read_json(root: Path, relative: str, *, files: dict[str, Any]) -> dict[str, Any]:
    path = _confined_file(root, relative)
    if path is None:
        raise ValueError(f"{relative} is missing")
    files[relative] = _file_reference(path)
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{relative} must contain a JSON object")
    return value


def _read_optional_json(
    root: Path,
    relative: str,
    *,
    files: dict[str, Any],
    incomplete: list[str],
) -> dict[str, Any] | None:
    path = _confined_file(root, relative)
    if path is None:
        incomplete.append(relative)
        return None
    files[relative] = _file_reference(path)
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{relative} must contain a JSON object")
    return value


def _checked_root(run_dir: Path) -> Path:
    raw = run_dir
    if raw.is_symlink():
        raise ValueError("run_dir must not be a symlink")
    if not raw.is_dir():
        raise ValueError("run_dir must be an existing directory")
    return raw.resolve(strict=True)


def _confined_file(root: Path, relative: str) -> Path | None:
    rel = Path(relative)
    if rel.is_absolute() or any(part in {"", ".", ".."} for part in rel.parts):
        raise ValueError("evidence path must be a safe relative path")
    raw = root / rel
    cursor = root
    for part in rel.parts:
        cursor = cursor / part
        if cursor.exists() and cursor.is_symlink():
            raise ValueError(f"{relative} must not traverse a symlink")
    if not raw.exists():
        return None
    path = raw.resolve(strict=True)
    if root != path and root not in path.parents:
        raise ValueError("evidence path escaped run_dir")
    if not path.is_file():
        raise ValueError(f"{relative} must be a regular file")
    return path


def _file_reference(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    return {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}


def _tool_counts(events: Sequence[Mapping[str, Any]], tool_name: str) -> Counter[str]:
    counts: Counter[str] = Counter()
    for event in events:
        payload = event.get("payload")
        if not isinstance(payload, Mapping):
            continue
        if event.get("event_type") == "tool_request" and payload.get("tool_name") == tool_name:
            counts["attempted"] += 1
        if event.get("event_type") == "tool_result":
            observation = payload.get("observation")
            if (
                isinstance(observation, Mapping)
                and observation.get("tool_name") == tool_name
                and observation.get("status") == "succeeded"
            ):
                counts["succeeded"] += 1
    return counts


def _with_incomplete(
    counts: Mapping[str, int],
    exposed: int,
    incomplete: Sequence[str],
) -> dict[str, Any]:
    missing = sorted(set(incomplete))
    return {
        "attempted": None if missing else int(counts.get("attempted", 0)),
        "succeeded": None if missing else int(counts.get("succeeded", 0)),
        "feedback_exposed_requests": None if missing else exposed,
        "incomplete": missing,
    }


def _native_observation_exposed_requests(
    events: Sequence[Mapping[str, Any]],
    tool_name: str,
) -> int:
    prior: set[tuple[str, str, str | None, str | None]] = set()
    exposed = 0
    for event in events:
        event_type = event.get("event_type")
        payload = event.get("payload")
        if not isinstance(payload, Mapping):
            continue
        if event_type == "provider_request":
            exposed += int(
                any(
                    identity in prior
                    for identity in _message_observation_identities(
                        payload.get("messages"),
                        tool_name,
                    )
                )
            )
            continue
        if event_type == "tool_result":
            observation = payload.get("observation")
            identity = _observation_identity(observation, tool_name)
            if identity is not None:
                prior.add(identity)
    return exposed


def _message_observation_identities(
    value: Any,
    tool_name: str,
) -> set[tuple[str, str, str | None, str | None]]:
    identities: set[tuple[str, str, str | None, str | None]] = set()
    for candidate in _walk_json_like(value):
        if not isinstance(candidate, Mapping):
            continue
        observation = (
            candidate.get("observation")
            if candidate.get("schema_version") == "vaevas-reasoning-request-v1"
            else candidate
        )
        identity = _observation_identity(observation, tool_name)
        if identity is not None:
            identities.add(identity)
    return identities


def _walk_json_like(value: Any) -> Sequence[Any]:
    found: list[Any] = []
    if isinstance(value, str):
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError:
            return found
        found.extend(_walk_json_like(decoded))
        return found
    if isinstance(value, Mapping):
        found.append(value)
        for item in value.values():
            found.extend(_walk_json_like(item))
        return found
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        for item in value:
            found.extend(_walk_json_like(item))
    return found


def _observation_identity(value: Any, tool_name: str) -> tuple[str, str, str | None, str | None] | None:
    if not isinstance(value, Mapping):
        return None
    if value.get("tool_name") != tool_name or value.get("status") != "succeeded":
        return None
    observation_id = value.get("observation_id")
    if not isinstance(observation_id, str) or not observation_id:
        return None
    payload = value.get("payload")
    receipt = payload.get("receipt") if isinstance(payload, Mapping) else None
    receipt_sha = receipt.get("receipt_sha256") if isinstance(receipt, Mapping) else None
    if receipt_sha is not None and (
        not isinstance(receipt_sha, str) or not _SHA256_RE.fullmatch(receipt_sha)
    ):
        receipt_sha = None
    candidate_sha = value.get("candidate_tree_sha256")
    if candidate_sha is not None and (
        not isinstance(candidate_sha, str) or not _SHA256_RE.fullmatch(candidate_sha)
    ):
        candidate_sha = None
    if receipt_sha is None and candidate_sha is None:
        return None
    return (tool_name, observation_id, candidate_sha, receipt_sha)


def _prior_candidate_exposed_requests(
    events: Sequence[Mapping[str, Any]],
    prior_receipts: set[tuple[str, str]],
) -> int:
    if not prior_receipts:
        return 0
    exposed = 0
    for event in events:
        if event.get("event_type") != "provider_request":
            continue
        payload = event.get("payload")
        if not isinstance(payload, Mapping):
            continue
        if _message_prior_candidates(payload.get("messages")) & prior_receipts:
            exposed += 1
    return exposed


def _message_prior_candidates(value: Any) -> set[tuple[str, str]]:
    identities: set[tuple[str, str]] = set()
    for candidate in _walk_json_like(value):
        if not isinstance(candidate, Mapping):
            continue
        prior_candidates = candidate.get("prior_candidates")
        if not isinstance(prior_candidates, Sequence) or isinstance(prior_candidates, (str, bytes, bytearray)):
            continue
        for item in prior_candidates:
            if not isinstance(item, Mapping):
                continue
            candidate_sha = item.get("candidate_tree_sha256")
            public_validation = item.get("public_validation")
            result = public_validation.get("result") if isinstance(public_validation, Mapping) else None
            event_sha = result.get("event_sha256") if isinstance(result, Mapping) else None
            if (
                isinstance(candidate_sha, str)
                and _SHA256_RE.fullmatch(candidate_sha)
                and isinstance(event_sha, str)
                and _SHA256_RE.fullmatch(event_sha)
            ):
                identities.add((candidate_sha, event_sha))
    return identities


def _valid_public_receipt(
    receipt: Mapping[str, Any],
    *,
    manifest_sha: str | None,
    expected_branch_id: str | None = None,
    expected_round_index: int | None = None,
    branch_dir: Path | None = None,
) -> tuple[str, str] | None:
    if receipt.get("schema_version") != "vaevas-native-evolution-public-validation-receipt-v1":
        raise ValueError("public validation receipt schema mismatch")
    if manifest_sha is not None and receipt.get("manifest_sha256") != manifest_sha:
        raise ValueError("public validation receipt manifest mismatch")
    if expected_branch_id is not None and receipt.get("branch_id") != expected_branch_id:
        raise ValueError("public validation receipt branch mismatch")
    if expected_round_index is not None and receipt.get("round_index") != expected_round_index:
        raise ValueError("public validation receipt round mismatch")
    result = receipt.get("result")
    if not isinstance(result, Mapping):
        raise ValueError("public validation receipt result is missing")
    event_sha = result.get("event_sha256")
    if not isinstance(event_sha, str) or not _SHA256_RE.fullmatch(event_sha):
        raise ValueError("public validation receipt event hash is invalid")
    observation = receipt.get("observation")
    if observation is None:
        return None
    if not isinstance(observation, Mapping):
        raise ValueError("public validation receipt observation is invalid")
    if observation.get("tool_name") != _WAVEFORM_TOOL:
        return None
    candidate = receipt.get("candidate_tree_sha256")
    if not isinstance(candidate, str) or not _SHA256_RE.fullmatch(candidate):
        raise ValueError("public validation receipt candidate hash is invalid")
    if branch_dir is None or expected_branch_id is None or expected_round_index is None:
        raise ValueError("public waveform receipt requires branch identity")
    return _validated_waveform_public_feedback_identity(
        receipt,
        branch_dir=branch_dir,
        manifest_sha=manifest_sha or str(receipt.get("manifest_sha256")),
        branch_id=expected_branch_id,
        round_index=expected_round_index,
    )


def _validated_waveform_public_feedback_identity(
    receipt: Mapping[str, Any],
    *,
    branch_dir: Path,
    manifest_sha: str,
    branch_id: str,
    round_index: int,
) -> tuple[str, str] | None:
    candidate = str(receipt["candidate_tree_sha256"])
    candidate_id = f"{branch_id}-round-{round_index:04d}-{candidate[:12]}"
    store = branch_dir / "candidate-store" / candidate
    import run_native_evolution as evolution

    feedback = evolution._public_feedback_for_prior_candidate(
        store=store,
        entry={"summary": {}, "source_event_sha256": receipt["result"]["event_sha256"]},
        tree_sha256=candidate,
        candidate_id=candidate_id,
        manifest_sha256=manifest_sha,
    )
    observation = feedback.get("observation")
    result = feedback.get("result")
    if not isinstance(observation, Mapping) or observation.get("tool_name") != _WAVEFORM_TOOL:
        return None
    if not isinstance(result, Mapping):
        raise ValueError("public validation receipt result is missing")
    status = str(result.get("status") or observation.get("status") or "")
    if status in {"succeeded", "completed"} and observation.get("status") == "succeeded":
        event_sha = result.get("event_sha256")
        if isinstance(event_sha, str) and _SHA256_RE.fullmatch(event_sha):
            return (candidate, event_sha)
    return None


def _evolution_branch_root(root: Path) -> str:
    if (root / "evolution/branches").is_dir():
        return "evolution/branches"
    if (root / "branches").is_dir():
        return "branches"
    return "evolution/branches"


def _merge_counter(target: Counter[str], source: Mapping[str, int]) -> None:
    for key, value in source.items():
        target[key] += int(value)


def _branch_id(value: Any) -> str:
    if not isinstance(value, Mapping):
        raise ValueError("branch_roster entries must be objects")
    branch_id = value.get("branch_id")
    if not isinstance(branch_id, str) or not branch_id:
        raise ValueError("branch_id must be a non-empty string")
    if "/" in branch_id or "\\" in branch_id or branch_id in {".", ".."}:
        raise ValueError("branch_id must be a safe path segment")
    return branch_id


def _positive_int(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{label} must be a positive integer")
    return value


def _optional_sha256(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise ValueError("manifest_sha256 must be a SHA-256 digest")
    return value
