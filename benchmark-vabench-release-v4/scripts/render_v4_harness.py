#!/usr/bin/env python3
"""Render v4 harness profiles and Spectre decks from one canonical spec."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft202012Validator
except ModuleNotFoundError:  # Runtime oracle environments intentionally stay minimal.
    Draft202012Validator = None


ROOT = Path(__file__).resolve().parents[1]
SPEC_SCHEMA = ROOT / "schemas" / "harness_spec.schema.json"
PROFILE_SCHEMA = ROOT / "schemas" / "harness_profile.schema.json"
GENERATOR_VERSION = "v4-harness-renderer-v1"
MAX_SAVE_LINE_LENGTH = 1000


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_schema(payload: dict[str, Any], schema_path: Path) -> None:
    if Draft202012Validator is not None:
        Draft202012Validator(read_json(schema_path)).validate(payload)
        return
    if schema_path == SPEC_SCHEMA:
        required = {
            "schema_version",
            "family_id",
            "task_id",
            "generator",
            "candidate",
            "deck",
            "property_ids",
            "profile_defaults",
        }
        missing = sorted(required - payload.keys())
        if missing:
            raise ValueError(f"harness spec missing keys: {missing}")
        if payload["schema_version"] != "v4-harness-spec-v1":
            raise ValueError("unsupported harness spec schema_version")
        if not re.fullmatch(r"[0-9]{3}", str(payload["family_id"])):
            raise ValueError("invalid harness family_id")
        if not re.fullmatch(r"v4-[0-9]{3,4}", str(payload["task_id"])):
            raise ValueError("invalid harness task_id")
        artifacts = list((payload.get("candidate") or {}).get("artifact_paths") or [])
        if not artifacts:
            raise ValueError("harness candidate artifact_paths must not be empty")
        for artifact in artifacts:
            path = Path(str(artifact))
            if path.is_absolute() or ".." in path.parts or path.suffix != ".va":
                raise ValueError(f"unsafe harness artifact path: {artifact}")
        support = payload.get("support") or {}
        support_artifacts = list(support.get("artifact_paths") or [])
        if support and not support_artifacts:
            raise ValueError("harness support artifact_paths must not be empty")
        for artifact in support_artifacts:
            path = Path(str(artifact))
            if path.is_absolute() or ".." in path.parts or path.suffix != ".va":
                raise ValueError(f"unsafe harness support path: {artifact}")
        deck = payload.get("deck") or {}
        if not deck.get("header") or not deck.get("analyses"):
            raise ValueError("harness deck requires header and analyses")
        property_ids = list(payload.get("property_ids") or [])
        if not property_ids or any(not re.fullmatch(r"P_[A-Z0-9_]+", str(item)) for item in property_ids):
            raise ValueError("invalid harness property_ids")
        defaults = payload.get("profile_defaults") or {}
        if set(defaults) != {"feedback", "score"}:
            raise ValueError("harness profile_defaults must contain feedback and score")
        return
    if schema_path == PROFILE_SCHEMA:
        required = {
            "schema_version",
            "profile_name",
            "harness_spec_sha256",
            "generated_from",
            "property_ids",
            "parameters",
            "corners",
            "deterministic_seed",
            "simulatorOptions",
            "public_visible",
        }
        missing = sorted(required - payload.keys())
        if missing:
            raise ValueError(f"harness profile missing keys: {missing}")
        name = payload.get("profile_name")
        if payload.get("schema_version") != "v4-harness-profile-v1" or name not in {"feedback", "score"}:
            raise ValueError("invalid harness profile identity")
        if name == "feedback":
            if (payload.get("simulatorOptions") or {}).get("evas_profile") != "balanced":
                raise ValueError("feedback harness must use evas_profile=balanced")
            if payload.get("public_visible") is not True:
                raise ValueError("feedback harness must be public_visible")
        elif payload.get("public_visible") is not False:
            raise ValueError("score harness must not be public_visible")
        return
    raise ValueError(f"unsupported schema path: {schema_path}")


def format_value(value: Any) -> str:
    if isinstance(value, bool):
        return "yes" if value else "no"
    return str(value)


def render_template(text: str, values: dict[str, Any]) -> str:
    return text.format(**{key: format_value(value) for key, value in values.items()})


def render_save_lines(
    signals: list[str], max_line_length: int = MAX_SAVE_LINE_LENGTH
) -> list[str]:
    """Split wide save lists without changing their signal order or meaning."""
    if max_line_length < len("save ") + 1:
        raise ValueError("max save line length is too small")

    rendered: list[str] = []
    current = "save"
    for signal in signals:
        token = str(signal).strip()
        if not token:
            continue
        candidate = f"{current} {token}"
        if current != "save" and len(candidate) > max_line_length:
            rendered.append(current)
            current = f"save {token}"
        else:
            current = candidate
    if current != "save":
        rendered.append(current)
    return rendered


def build_profile(spec: dict[str, Any], profile_name: str, spec_hash: str) -> dict[str, Any]:
    if profile_name not in {"feedback", "score"}:
        raise ValueError(f"unknown profile: {profile_name}")
    defaults = dict((spec.get("profile_defaults") or {}).get(profile_name) or {})
    simulator_options = dict(defaults.get("simulatorOptions") or {})
    if profile_name == "feedback":
        existing = simulator_options.get("evas_profile")
        if existing not in {None, "balanced"}:
            raise ValueError("feedback simulatorOptions.evas_profile must be balanced")
        simulator_options["evas_profile"] = "balanced"
    profile = {
        "schema_version": "v4-harness-profile-v1",
        "profile_name": profile_name,
        "harness_spec_sha256": spec_hash,
        "generated_from": {"script": "render_v4_harness.py", "version": GENERATOR_VERSION},
        "property_ids": list(spec["property_ids"]),
        "parameters": dict(defaults.get("parameters") or {}),
        "corners": list(defaults.get("corners") or []),
        "deterministic_seed": int(defaults.get("deterministic_seed") or 0),
        "simulatorOptions": simulator_options,
        "deck_overrides": dict(defaults.get("deck_overrides") or {}),
        "public_visible": profile_name == "feedback",
    }
    validate_schema(profile, PROFILE_SCHEMA)
    return profile


def render_scs(spec: dict[str, Any], profile: dict[str, Any]) -> str:
    values: dict[str, Any] = {}
    values.update(profile.get("parameters") or {})
    values["candidate_source_root"] = spec["candidate"]["source_root"]
    values["support_source_root"] = (spec.get("support") or {}).get(
        "source_root", "./support"
    )
    values["deterministic_seed"] = profile["deterministic_seed"]
    values["profile_name"] = profile["profile_name"]

    lines: list[str] = []
    lines.extend(str(line) for line in spec["deck"]["header"])
    lines.append("")
    for artifact_path in spec["candidate"]["artifact_paths"]:
        values["artifact_path"] = artifact_path
        for template in spec["deck"].get("include_templates") or []:
            lines.append(render_template(str(template), values))
    for artifact_path in (spec.get("support") or {}).get("artifact_paths") or []:
        values["support_artifact_path"] = artifact_path
        for template in spec["deck"].get("support_include_templates") or []:
            lines.append(render_template(str(template), values))
    deck_overrides = profile.get("deck_overrides") or {}
    body_lines = list(spec["deck"]["body_lines"]) + list(deck_overrides.get("body_lines") or [])
    analyses = list(deck_overrides.get("analyses") or spec["deck"]["analyses"])
    save_signals = list(deck_overrides.get("save_signals") or spec["deck"]["save_signals"])

    if body_lines:
        lines.append("")
        lines.extend(render_template(str(line), values) for line in body_lines)
    if profile["simulatorOptions"]:
        options = " ".join(
            f"{key}={format_value(value)}" for key, value in sorted(profile["simulatorOptions"].items())
        )
        lines.append("")
        lines.append(f"simulatorOptions options {options}")
    if analyses:
        lines.append("")
        lines.extend(render_template(str(line), values) for line in analyses)
    if save_signals:
        lines.extend(render_save_lines(save_signals))
    return "\n".join(lines).rstrip() + "\n"


def load_spec(path: Path) -> tuple[dict[str, Any], str]:
    spec = read_json(path)
    validate_schema(spec, SPEC_SCHEMA)
    return spec, file_sha256(path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True, help="Canonical harness_spec.json.")
    parser.add_argument("--profile", choices=["feedback", "score"], required=True)
    parser.add_argument("--profile-output", type=Path)
    parser.add_argument("--deck-output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    spec, spec_hash = load_spec(args.spec)
    profile = build_profile(spec, args.profile, spec_hash)
    deck = render_scs(spec, profile)
    if args.profile_output:
        write_json(args.profile_output, profile)
    if args.deck_output:
        args.deck_output.parent.mkdir(parents=True, exist_ok=True)
        args.deck_output.write_text(deck, encoding="utf-8")
    if not args.profile_output and not args.deck_output:
        print(deck, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
