#!/usr/bin/env python3
"""Audit a tri-form runtime export for public/evaluator isolation."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def tree_sha(path: Path) -> str:
    digest = hashlib.sha256()
    for item in sorted(path.rglob("*")):
        if item.is_file():
            digest.update(item.relative_to(path).as_posix().encode("utf-8"))
            digest.update(b"\0")
            digest.update(item.read_bytes())
            digest.update(b"\0")
    return digest.hexdigest()


def file_map(path: Path) -> dict[str, bytes]:
    return {item.relative_to(path).as_posix(): item.read_bytes() for item in sorted(path.rglob("*")) if item.is_file()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    run = args.run.expanduser().resolve()
    problems: list[str] = []
    policy = read_json(run / "MODEL_ACCESS_POLICY.json")
    attempt = read_json(run / "evidence" / "attempt_record.json")
    mode = str(policy.get("mode") or "")
    mounts = policy.get("mounts") or []
    if policy.get("evaluator_mounted") is not False or any("evaluator" in str(item) for item in mounts):
        problems.append("evaluator assets are model-mounted")
    if policy.get("network") is not False:
        problems.append("network is not disabled")
    if mode in {"G0", "G1"}:
        if mounts:
            problems.append("direct one-shot mode has filesystem mounts")
        if not (run / "direct_prompt.txt").is_file():
            problems.append("direct one-shot prompt is missing")
        if (run / "public" / "tool_manifest.json").exists():
            problems.append("direct one-shot mode exposes a tool manifest")
    else:
        if mounts != ["public/task:ro", "public/submission:rw"]:
            problems.append("agentic model mounts differ from the public contract")
        if not (run / "public" / "tool_manifest.json").is_file():
            problems.append("agentic mode lacks the feedback tool manifest")
        if not (run / "agent_prompt.txt").is_file():
            problems.append("agentic mode lacks the composed initial prompt")
    submission = run / "public" / "submission"
    if attempt.get("initial_submission_sha256") != tree_sha(submission):
        problems.append("initial submission hash does not match the prepared workspace")
    if attempt.get("form") == "bugfix" and mode not in {"G0", "G1"}:
        buggy = run / "public" / "task" / "buggy_bundle"
        if file_map(buggy) != file_map(submission):
            problems.append("bugfix writable submission is not an exact editable copy of the supplied buggy bundle")
        if attempt.get("submission_seeded_from_buggy_bundle") is not True:
            problems.append("bugfix attempt does not record its seeded editable workspace")
    if attempt.get("state") != "prepared" or attempt.get("private_score_decisions") != 0:
        problems.append("attempt lifecycle was not initialized safely")
    for path in (run / "public").rglob("*"):
        if path.is_symlink():
            problems.append(f"public bundle contains symlink: {path}")
        if path.is_file():
            text = path.read_text(encoding="utf-8", errors="ignore")
            if "negative_variants/" in text or "/evaluator/" in text:
                problems.append(f"public file leaks authoring evaluator path: {path}")
    report = {"schema_version": "v4-runtime-export-audit-v1", "status": "pass" if not problems else "fail", "problems": problems}
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
