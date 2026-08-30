"""Synthetic-only training export projection for vaEVAS harness traces."""

from __future__ import annotations

import hashlib
import json
import math
import re
from typing import Any, Mapping, Sequence


SCHEMA_VERSION = "vaevas-training-export-v1"
SPLIT_SCHEMA_VERSION = "vaevas-training-split-manifest-v1"
NORMALIZER_ID = "vaevas-training-export-normalizer-v1"
EXPORTER_CONTRACT = {
    "id": NORMALIZER_ID,
    "contract": "synthetic-fixture-only",
    "version": "1",
}

_ALLOWED_MODES = frozenset({"sft", "rl"})
_ALLOWED_SOURCE_KIND = "synthetic"
_ALLOWED_RELEASE_IDENTITY = "synthetic-training-fixtures-v1"
_ALLOWED_LICENSES = frozenset({"CC0-1.0"})
_ALLOWED_SPLITS = ("train", "dev", "heldout")
_TRAINING_SPLITS = frozenset({"train", "dev"})
_FORBIDDEN_AUTHORITY_WORDS = ("final", "hidden", "private", "trusted")
_FORBIDDEN_METADATA_MARKERS = ("final", "hidden", "private", "trusted", "unknown", "unk")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_MAX_EVENTS = 256
_MAX_CONTENT_BYTES = 16 * 1024
_MAX_ID_CHARS = 128
_MAX_SPLIT_IDS = 1024

_SOURCE_KEYS = frozenset({
    "source_kind",
    "source_id",
    "release_identity",
    "task_id",
    "episode_id",
    "provenance",
    "normalizer",
    "license",
    "provider_use",
    "project_authorization",
    "exposure_policy",
    "trajectory",
    "termination",
})
_PROVENANCE_KEYS = frozenset({"artifact", "generator", "version"})
_NORMALIZER_KEYS = frozenset({"id", "version"})
_LICENSE_KEYS = frozenset({"spdx", "redistributable"})
_PROVIDER_USE_KEYS = frozenset({"terms", "allows_training", "raw_provider_payload"})
_AUTHORIZATION_KEYS = frozenset({"project", "allows_training_export"})
_EXPOSURE_KEYS = frozenset({
    "contains_private",
    "contains_trusted",
    "contains_hidden",
    "contains_final",
    "may_enter_model_training",
})
_TERMINATION_KEYS = frozenset({"reason", "budget_exhausted"})
_LABELS_KEYS = frozenset({"sft"})
_SFT_LABEL_KEYS = frozenset({"authority", "accepted"})
_REWARD_KEYS = frozenset({"authority", "value", "definition", "generator_sha256"})
_SPLIT_MANIFEST_KEYS = frozenset({"schema_version", "splits", "excluded_releases"})


class TrainingExportError(ValueError):
    """Raised when a trace cannot be safely projected into training data."""


def build_training_export(
    source: Mapping[str, Any],
    *,
    split_manifest: Mapping[str, Any],
    mode: str,
) -> dict[str, Any]:
    """Build a deterministic synthetic training export.

    The caller owns persistence and any real dataset authorization. This module
    intentionally accepts only synthetic fixture-like sources and fails closed
    on hidden/final/trusted/private material.
    """

    if mode not in _ALLOWED_MODES:
        raise TrainingExportError(f"unsupported training export mode: {mode}")
    source_doc = _mapping(source, "source")
    split_doc = _mapping(split_manifest, "split manifest")
    _assert_finite_json(source_doc, "source")
    _assert_finite_json(split_doc, "split manifest")
    _validate_source_gate(source_doc, mode)
    split_name = _validate_split_manifest(split_doc, _string(source_doc, "task_id"))
    if split_name not in _TRAINING_SPLITS:
        raise TrainingExportError("heldout split cannot be exported for training")
    trajectory = _trajectory(source_doc)
    if mode == "sft":
        projection = {"sft": _build_sft_projection(source_doc, trajectory)}
    else:
        projection = {"rl": _build_rl_projection(source_doc, trajectory)}

    export: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "normalizer_id": NORMALIZER_ID,
        "mode": mode,
        "identity": {
            "source_id": _string(source_doc, "source_id"),
            "release_identity": _string(source_doc, "release_identity"),
            "task_id": _string(source_doc, "task_id"),
            "episode_id": _string(source_doc, "episode_id"),
        },
        "source": {
            "source_kind": _ALLOWED_SOURCE_KIND,
            "source_sha256": _canonical_sha256(source_doc),
            "exporter_contract_sha256": _canonical_sha256(EXPORTER_CONTRACT),
            "provenance_sha256": _canonical_sha256(
                _mapping(source_doc.get("provenance"), "provenance")
            ),
            "normalizer_sha256": _canonical_sha256(
                _mapping(source_doc.get("normalizer"), "source normalizer")
            ),
        },
        "split": {
            "name": split_name,
            "manifest_sha256": _canonical_sha256(split_doc),
        },
        "license": _license_summary(source_doc),
        "provider_use": _provider_use_summary(source_doc),
        "project_authorization": _project_authorization_summary(source_doc),
        "exposure_policy": _exposure_summary(source_doc),
        "termination": _termination_summary(source_doc),
        **projection,
    }
    export["export_sha256"] = _canonical_sha256(export)
    return export


def validate_training_export(
    document: Mapping[str, Any],
    *,
    source: Mapping[str, Any],
    split_manifest: Mapping[str, Any],
) -> None:
    """Rebuild and compare a training export against its declared inputs."""

    exported = _mapping(document, "training export")
    mode = _string(exported, "mode")
    rebuilt = build_training_export(source, split_manifest=split_manifest, mode=mode)
    if exported != rebuilt:
        raise TrainingExportError("training export does not match source and split")


def _validate_source_gate(source: Mapping[str, Any], mode: str) -> None:
    expected_keys = set(_SOURCE_KEYS)
    if mode == "sft":
        expected_keys.add("labels")
    else:
        expected_keys.add("reward")
    _require_keys(source, expected_keys, "source")
    if source.get("source_kind") != _ALLOWED_SOURCE_KIND:
        raise TrainingExportError("training export accepts only synthetic sources")
    _validate_metadata_id(_string(source, "source_id"), "source_id")
    _validate_metadata_id(_string(source, "episode_id"), "episode_id")
    task_id = _string(source, "task_id")
    release_identity = _string(source, "release_identity")
    if not task_id.startswith("synthetic/"):
        raise TrainingExportError("non-synthetic task ids are not exportable")
    if _mentions_r53(task_id) or _mentions_r53(release_identity):
        raise TrainingExportError("r53 benchmark tasks are excluded from training")
    if release_identity != _ALLOWED_RELEASE_IDENTITY:
        raise TrainingExportError("source release identity must be synthetic fixture v1")
    _validate_named_record(
        _mapping(source.get("provenance"), "provenance"),
        ("artifact", "generator", "version"),
        "provenance",
    )
    _validate_named_record(
        _mapping(source.get("normalizer"), "source normalizer"),
        ("id", "version"),
        "source normalizer",
    )
    _license_summary(source)
    _provider_use_summary(source)
    _project_authorization_summary(source)
    exposure = _exposure_summary(source)
    if not exposure["may_enter_model_training"]:
        raise TrainingExportError("source exposure policy does not allow training")
    _termination_summary(source)


def _validate_split_manifest(
    manifest: Mapping[str, Any],
    task_id: str,
) -> str:
    _require_keys(manifest, _SPLIT_MANIFEST_KEYS, "split manifest")
    if manifest.get("schema_version") != SPLIT_SCHEMA_VERSION:
        raise TrainingExportError("unsupported split manifest schema")
    excluded = manifest.get("excluded_releases")
    if not isinstance(excluded, Sequence) or isinstance(excluded, (str, bytes)):
        raise TrainingExportError("split manifest excluded_releases must be a list")
    if not any(isinstance(item, str) and _mentions_r53(item) for item in excluded):
        raise TrainingExportError("split manifest must explicitly exclude r53")
    splits = manifest.get("splits")
    if not isinstance(splits, Mapping):
        raise TrainingExportError("split manifest splits must be an object")
    _require_keys(splits, frozenset(_ALLOWED_SPLITS), "split buckets")
    membership: dict[str, str] = {}
    for split_name in _ALLOWED_SPLITS:
        tasks = splits.get(split_name)
        if not isinstance(tasks, Sequence) or isinstance(tasks, (str, bytes)):
            raise TrainingExportError(f"{split_name} split must be a list")
        if len(tasks) > _MAX_SPLIT_IDS:
            raise TrainingExportError("split exceeds maximum task id count")
        seen: set[str] = set()
        for item in tasks:
            if not isinstance(item, str) or not item:
                raise TrainingExportError("split task ids must be non-empty strings")
            _validate_id(item, "split task id")
            if not item.startswith("synthetic/"):
                raise TrainingExportError("split task ids must use synthetic namespace")
            if _mentions_r53(item):
                raise TrainingExportError("r53 benchmark tasks are excluded from splits")
            if item in seen:
                raise TrainingExportError("duplicate task id within split")
            seen.add(item)
            previous = membership.setdefault(item, split_name)
            if previous != split_name:
                raise TrainingExportError("task id appears in multiple splits")
    matches = [split for split in _ALLOWED_SPLITS if task_id in set(splits[split])]
    if len(matches) != 1:
        raise TrainingExportError("source task id must appear in exactly one split")
    return matches[0]


def _build_sft_projection(
    source: Mapping[str, Any],
    trajectory: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    labels = _mapping(source.get("labels"), "labels")
    _require_keys(labels, _LABELS_KEYS, "labels")
    sft = _mapping(labels.get("sft"), "sft labels")
    _require_keys(sft, _SFT_LABEL_KEYS, "sft labels")
    if sft.get("accepted") is not True:
        raise TrainingExportError("SFT export requires an accepted synthetic label")
    authority = _string(sft, "authority")
    if authority != "synthetic_fixture":
        raise TrainingExportError("SFT label authority must be synthetic_fixture")
    termination = _mapping(source.get("termination"), "termination")
    if (
        termination.get("budget_exhausted") is True
        or _string(termination, "reason") != "submitted"
    ):
        raise TrainingExportError("only submitted non-budget SFT labels are positive")
    messages = _loss_masked_messages(trajectory)
    if not any(message["role"] == "assistant" and message["loss"] for message in messages):
        raise TrainingExportError("SFT export requires at least one assistant target")
    return {
        "label_authority": authority,
        "messages": messages,
        "assistant_targets": [
            {"event_id": message["event_id"], "content": message["content"]}
            for message in messages
            if message["role"] == "assistant" and message["loss"]
        ],
        "public_context": _public_context(trajectory),
        "environment_observations": _environment_observations(trajectory),
        "budget_stop_positive_example": False,
    }


def _build_rl_projection(
    source: Mapping[str, Any],
    trajectory: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    reward = _mapping(source.get("reward"), "reward")
    _require_keys(reward, _REWARD_KEYS, "reward")
    authority = _string(reward, "authority")
    if authority != "public_validation":
        raise TrainingExportError("RL reward authority must be public_validation")
    generator_sha256 = _string(reward, "generator_sha256")
    if not _SHA256_RE.fullmatch(generator_sha256):
        raise TrainingExportError("RL reward generator_sha256 must be a SHA-256 hex")
    value = reward.get("value")
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
        raise TrainingExportError("RL reward value must be finite")
    if float(value) < -1.0 or float(value) > 1.0:
        raise TrainingExportError("RL reward value must be within [-1, 1]")
    definition = _string(reward, "definition")
    _reject_authority(definition, "RL reward definition")
    return {
        "reward": {
            "authority": authority,
            "value": float(value),
            "definition": definition,
            "generator_sha256": generator_sha256,
        },
        "public_context": _public_context(trajectory),
        "accepted_actions": [
            {
                "event_id": _string(event, "event_id"),
                "content_sha256": _content_sha256(event),
            }
            for event in trajectory
            if event.get("role") == "assistant" and event.get("visibility") == "model"
        ],
        "public_observations": _environment_observations(trajectory),
        "final_score_exported": False,
    }


def _public_context(trajectory: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            "event_id": _string(event, "event_id"),
            "role": _string(event, "role"),
            "content_sha256": _content_sha256(event),
        }
        for event in trajectory
        if event.get("visibility") == "model" and event.get("role") in {"system", "user"}
    ]


def _environment_observations(
    trajectory: Sequence[Mapping[str, Any]],
) -> list[dict[str, str]]:
    return [
        {
            "event_id": _string(event, "event_id"),
            "content_sha256": _content_sha256(event),
        }
        for event in trajectory
        if event.get("role") == "environment" and event.get("visibility") == "model"
    ]


def _trajectory(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    value = source.get("trajectory")
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise TrainingExportError("trajectory must be a list")
    events = [_mapping(event, "trajectory event") for event in value]
    if not events:
        raise TrainingExportError("trajectory must not be empty")
    if len(events) > _MAX_EVENTS:
        raise TrainingExportError("trajectory exceeds maximum event count")
    seen_event_ids: set[str] = set()
    for event in events:
        _require_keys(
            event,
            {"event_id", "role", "visibility", "content"}
            | ({"content_sha256"} if "content_sha256" in event else set()),
            "trajectory event",
        )
        visibility = _string(event, "visibility")
        role = _string(event, "role")
        if visibility != "model":
            raise TrainingExportError("training export allows only model-visible events")
        if role not in {"system", "user", "assistant", "environment"}:
            raise TrainingExportError("unsupported trajectory role")
        event_id = _string(event, "event_id")
        _validate_id(event_id, "event_id")
        if event_id in seen_event_ids:
            raise TrainingExportError("duplicate trajectory event_id")
        seen_event_ids.add(event_id)
        _content(event)
        _content_sha256(event)
    return events


def _license_summary(source: Mapping[str, Any]) -> dict[str, Any]:
    license_doc = _mapping(source.get("license"), "license")
    _require_keys(license_doc, _LICENSE_KEYS, "license")
    spdx = _string(license_doc, "spdx")
    if spdx not in _ALLOWED_LICENSES or license_doc.get("redistributable") is not True:
        raise TrainingExportError("source license is not training-exportable")
    return {"spdx": spdx, "redistributable": True}


def _provider_use_summary(source: Mapping[str, Any]) -> dict[str, Any]:
    provider_use = _mapping(source.get("provider_use"), "provider_use")
    _require_keys(provider_use, _PROVIDER_USE_KEYS, "provider_use")
    if provider_use.get("terms") != "synthetic-fixture":
        raise TrainingExportError("provider terms must be synthetic-fixture")
    if provider_use.get("allows_training") is not True:
        raise TrainingExportError("provider terms do not allow training")
    if provider_use.get("raw_provider_payload") is not False:
        raise TrainingExportError("raw provider payload is not exportable")
    return {
        "terms": _string(provider_use, "terms"),
        "allows_training": True,
        "raw_provider_payload": False,
    }


def _project_authorization_summary(source: Mapping[str, Any]) -> dict[str, Any]:
    authorization = _mapping(source.get("project_authorization"), "project_authorization")
    _require_keys(authorization, _AUTHORIZATION_KEYS, "project_authorization")
    if authorization.get("allows_training_export") is not True:
        raise TrainingExportError("project authorization does not allow training export")
    project = _string(authorization, "project")
    _validate_metadata_id(project, "project_authorization.project")
    return {
        "project": project,
        "allows_training_export": True,
    }


def _exposure_summary(source: Mapping[str, Any]) -> dict[str, bool]:
    exposure = _mapping(source.get("exposure_policy"), "exposure_policy")
    _require_keys(exposure, _EXPOSURE_KEYS, "exposure_policy")
    summary = {
        "contains_private": _false(exposure, "contains_private"),
        "contains_trusted": _false(exposure, "contains_trusted"),
        "contains_hidden": _false(exposure, "contains_hidden"),
        "contains_final": _false(exposure, "contains_final"),
        "may_enter_model_training": exposure.get("may_enter_model_training") is True,
    }
    if any(summary[key] for key in (
        "contains_private",
        "contains_trusted",
        "contains_hidden",
        "contains_final",
    )):
        raise TrainingExportError("source exposure policy contains forbidden material")
    return summary


def _termination_summary(source: Mapping[str, Any]) -> dict[str, Any]:
    termination = _mapping(source.get("termination"), "termination")
    _require_keys(termination, _TERMINATION_KEYS, "termination")
    budget_exhausted = termination.get("budget_exhausted")
    if not isinstance(budget_exhausted, bool):
        raise TrainingExportError("termination budget_exhausted must be boolean")
    reason = _string(termination, "reason")
    if reason in {"budget_exhausted", "model_call_limit", "tool_call_limit"} and not budget_exhausted:
        raise TrainingExportError("termination reason contradicts budget_exhausted")
    return {
        "reason": reason,
        "budget_exhausted": budget_exhausted,
    }


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise TrainingExportError(f"{label} must be an object")
    return dict(value)


def _validate_named_record(
    value: Mapping[str, Any],
    fields: Sequence[str],
    label: str,
) -> None:
    for field in fields:
        field_value = _string(value, field)
        if field_value.lower() in {"unknown", "none", "n/a", "unspecified"}:
            raise TrainingExportError(f"{label} must declare {field}")
        _validate_metadata_id(field_value, f"{label}.{field}")
    expected = {
        "provenance": _PROVENANCE_KEYS,
        "source normalizer": _NORMALIZER_KEYS,
    }[label]
    _require_keys(value, expected, label)


def _string(mapping: Mapping[str, Any], field: str) -> str:
    value = mapping.get(field)
    if not isinstance(value, str) or not value:
        raise TrainingExportError(f"{field} must be a non-empty string")
    return value


def _content(mapping: Mapping[str, Any]) -> str:
    value = _string(mapping, "content")
    if len(value.encode("utf-8")) > _MAX_CONTENT_BYTES:
        raise TrainingExportError("content exceeds maximum byte length")
    return value


def _false(mapping: Mapping[str, Any], field: str) -> bool:
    if mapping.get(field) is not False:
        raise TrainingExportError(f"{field} must be false")
    return False


def _content_sha256(event: Mapping[str, Any]) -> str:
    explicit = event.get("content_sha256")
    content_sha256 = hashlib.sha256(_content(event).encode("utf-8")).hexdigest()
    if explicit is not None:
        if not isinstance(explicit, str) or not _SHA256_RE.fullmatch(explicit):
            raise TrainingExportError("content_sha256 must be a SHA-256 hex")
        if explicit != content_sha256:
            raise TrainingExportError("content_sha256 does not match content")
        return explicit
    return content_sha256


def _reject_authority(value: str, label: str) -> None:
    lowered = value.lower()
    if any(word in lowered for word in _FORBIDDEN_AUTHORITY_WORDS):
        raise TrainingExportError(f"{label} is not public training authority")


def _mentions_r53(value: str) -> bool:
    lowered = value.lower()
    return (
        "benchmarkv4-r53" in lowered
        or "vabench-r53" in lowered
        or lowered == "r53"
        or lowered.startswith("v4-")
        or lowered.startswith("benchmarkv4/")
    )


def _canonical_sha256(value: Mapping[str, Any]) -> str:
    material = dict(value)
    material.pop("export_sha256", None)
    return hashlib.sha256(
        json.dumps(
            material,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def _require_keys(value: Mapping[str, Any], expected: set[str] | frozenset[str], label: str) -> None:
    keys = set(value)
    if keys != set(expected):
        missing = sorted(set(expected) - keys)
        extra = sorted(keys - set(expected))
        details = []
        if missing:
            details.append(f"missing {missing}")
        if extra:
            details.append(f"unknown {extra}")
        raise TrainingExportError(f"{label} has invalid fields: {', '.join(details)}")


def _validate_id(value: str, label: str) -> None:
    if len(value) > _MAX_ID_CHARS:
        raise TrainingExportError(f"{label} exceeds maximum length")
    if any(marker in value.lower() for marker in _FORBIDDEN_AUTHORITY_WORDS):
        raise TrainingExportError(f"{label} contains forbidden authority marker")


def _validate_metadata_id(value: str, label: str) -> None:
    """Reject unsafe metadata declarations; this is not content provenance proof."""

    _validate_id(value, label)
    lowered = value.lower()
    if any(marker in lowered for marker in _FORBIDDEN_METADATA_MARKERS):
        raise TrainingExportError(f"{label} metadata contains forbidden marker")


def _assert_finite_json(value: Any, label: str) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise TrainingExportError(f"{label} keys must be strings")
            _assert_finite_json(item, f"{label}.{key}")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _assert_finite_json(item, f"{label}[{index}]")
        return
    if isinstance(value, float) and not math.isfinite(value):
        raise TrainingExportError(f"{label} contains non-finite number")


def _loss_masked_messages(
    trajectory: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "event_id": _string(event, "event_id"),
            "role": _string(event, "role"),
            "content": _content(event),
            "loss": event.get("role") == "assistant",
        }
        for event in trajectory
    ]
