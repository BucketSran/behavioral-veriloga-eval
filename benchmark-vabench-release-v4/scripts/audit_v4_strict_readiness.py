#!/usr/bin/env python3
"""Strict v4 Gate-2/Gate-3 readiness audit.

This audit deliberately uses reports/v4_task_family_numbering/numbering_plan.json
as the only canonical family mapping. Per-task AUDIT.md files are ignored.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator


SCRIPTS_DIR = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
for import_dir in (SCRIPTS_DIR, REPO_ROOT / "runners", ROOT / "runners"):
    if str(import_dir) not in __import__("sys").path:
        __import__("sys").path.insert(0, str(import_dir))

from evidence_fingerprints import backend_fingerprints, checker_fingerprints  # noqa: E402
from generate_toolchain_lock import benchmark_component_hashes  # noqa: E402
from render_v4_harness import render_scs  # noqa: E402
from simulate_evas import CHECKS  # noqa: E402


TASKS = ROOT / "tasks"
NUMBERING_PLAN = ROOT / "reports" / "v4_task_family_numbering" / "numbering_plan.json"
TOOLCHAIN_LOCK = ROOT / "TOOLCHAIN_LOCK.json"
DEFAULT_OUTPUT = ROOT / "reports" / "strict_readiness" / "strict_readiness.json"

SCHEMAS = {
    "family": ROOT / "schemas" / "family_spec.schema.json",
    "harness": ROOT / "schemas" / "harness_spec.schema.json",
    "profile": ROOT / "schemas" / "harness_profile.schema.json",
    "mutation_catalog": ROOT / "schemas" / "mutation_catalog.schema.json",
    "derivation": ROOT / "schemas" / "derivation_manifest.schema.json",
    "certification": ROOT / "schemas" / "negative_certification.schema.json",
    "toolchain": ROOT / "schemas" / "toolchain_lock.schema.json",
    "first_n_spectre": ROOT / "schemas" / "first_n_spectre_evidence.schema.json",
}

PRIVATE_PATH_PATTERNS = (
    "solution/",
    "negative_variants/",
    "evaluator/score_tb.scs",
    "evaluator/checker_profile.json",
    "evaluator/profiles/score.json",
    "evaluator/derivation_manifest.json",
    "certification.json",
)


class AuditError(RuntimeError):
    """Raised for unrecoverable audit input errors."""


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise AuditError(f"expected JSON object: {path}")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def display_path(path: Path, root: Path | None = None) -> str:
    base = root or ROOT
    try:
        return str(path.relative_to(base))
    except ValueError:
        return str(path)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bundle_hash(root: Path, rels: Iterable[str]) -> str:
    digest = hashlib.sha256()
    for rel in sorted(rels):
        file_hash = sha256_file(root / rel)
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_hash.encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()


def issue(code: str, category: str, message: str, action: str, *, gate: str) -> dict[str, str]:
    return {"gate": gate, "code": code, "category": category, "message": message, "action": action}


def schema_errors(payload: dict[str, Any], schema_path: Path) -> list[str]:
    schema = read_json(schema_path)
    validator = Draft202012Validator(schema)
    return [
        f"{'.'.join(str(part) for part in error.path) or '<root>'}: {error.message}"
        for error in sorted(validator.iter_errors(payload), key=lambda item: list(item.path))
    ]


def add_schema_issues(
    issues: list[dict[str, str]], payload: dict[str, Any], schema_key: str, *, gate: str, label: str
) -> None:
    for error in schema_errors(payload, SCHEMAS[schema_key]):
        issues.append(
            issue(
                f"{label}_schema",
                "schema",
                f"{label} violates {SCHEMAS[schema_key].name}: {error}",
                f"Regenerate or edit {label} to satisfy the current v4 schema.",
                gate=gate,
            )
        )


def load_numbering_plan(path: Path, canonical_first: int) -> tuple[list[dict[str, Any]], str]:
    plan = read_json(path)
    if plan.get("schema_version") != "v4-task-family-numbering-plan-v1":
        raise AuditError("numbering_plan.json is not schema_version v4-task-family-numbering-plan-v1")
    rows = list(plan.get("rows") or [])
    if not 1 <= canonical_first <= len(rows):
        raise AuditError(f"--canonical-first must be within 1..{len(rows)}")
    for expected, row in enumerate(rows, start=1):
        expected_id = f"{expected:03d}"
        if row.get("canonical_index") != expected:
            raise AuditError(
                f"numbering_plan row {expected} has canonical_index={row.get('canonical_index')!r}"
            )
        if row.get("canonical_dut_id") != expected_id:
            raise AuditError(
                f"numbering_plan row {expected} has canonical_dut_id={row.get('canonical_dut_id')!r}"
            )
        slug = str(row.get("old_dut_slug") or "")
        if not re.fullmatch(r"[0-9]{3,4}-[A-Za-z0-9_.-]+", slug):
            raise AuditError(f"numbering_plan row {expected} has unsafe old_dut_slug={slug!r}")
    return rows[:canonical_first], sha256_file(path)


def normalize_signal(raw: str) -> set[str]:
    text = str(raw).strip().strip('"').strip("'")
    if text.startswith("V(") and text.endswith(")"):
        text = text[2:-1]
    text = text.replace("\\", "/").split("/")[-1]
    text = text.split(".")[-1]
    candidates = {text, text.lower()}
    bus = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_$]*)(?:\[|<)(\d+)(?::(\d+))?(?:\]|>)", text)
    if bus:
        name = bus.group(1)
        hi = int(bus.group(2))
        lo = int(bus.group(3) or bus.group(2))
        step = 1 if lo >= hi else -1
        for bit in range(hi, lo + step, step):
            candidates.update({f"{name}[{bit}]", f"{name}<{bit}>", f"{name}{bit}"})
    flattened = re.sub(r"[\[\]<>:_]", "", text)
    candidates.add(flattened)
    candidates.add(flattened.lower())
    return candidates


def covers_signal(required: str, observed: Iterable[str]) -> bool:
    required_forms = normalize_signal(required)
    observed_forms: set[str] = set()
    for item in observed:
        observed_forms.update(normalize_signal(item))
    return bool(required_forms & observed_forms)


def canonical_text(raw: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(raw or "").lower()).strip()


def declared_artifacts(family_spec: dict[str, Any]) -> list[str]:
    return [str(item.get("path")) for item in (family_spec.get("artifact_contract") or {}).get("files") or []]


def property_ids(family_spec: dict[str, Any]) -> set[str]:
    return {str(item.get("id")) for item in family_spec.get("properties") or []}


def trace_signals(family_spec: dict[str, Any]) -> list[str]:
    return [str(item) for item in (family_spec.get("trace_contract") or {}).get("required_signals") or []]


def load_optional_json(path: Path, issues: list[dict[str, str]], *, gate: str, label: str) -> dict[str, Any] | None:
    if not path.is_file():
        issues.append(
            issue(
                f"{label}_missing",
                "missing_evidence",
                f"Missing required {label}: {path.relative_to(ROOT)}",
                f"Materialize {path.relative_to(ROOT)} from the current v4 pipeline.",
                gate=gate,
            )
        )
        return None
    try:
        return read_json(path)
    except Exception as exc:
        issues.append(
            issue(
                f"{label}_unreadable",
                "schema",
                f"Cannot read {label}: {exc}",
                f"Replace {path.relative_to(ROOT)} with valid JSON.",
                gate=gate,
            )
        )
        return None


def public_entry_module_declaration(line: str, family: dict[str, Any]) -> bool:
    """Allow module interfaces and port fragments declared by the public contract."""
    match = re.fullmatch(r"module\s+([A-Za-z_][A-Za-z0-9_$]*)\s*\([^;]*\)\s*;", line)
    modules = [
        module
        for artifact in (family.get("artifact_contract") or {}).get("files") or []
        for module in artifact.get("modules") or []
    ]
    if match:
        return match.group(1) in {str(module.get("name")) for module in modules}

    identifiers = re.findall(r"[A-Za-z_][A-Za-z0-9_$]*", line)
    if len(identifiers) < 2:
        return False
    for module in modules:
        ports = [str(port.get("name")) for port in module.get("ports") or []]
        width = len(identifiers)
        if any(identifiers == ports[start : start + width] for start in range(len(ports) - width + 1)):
            return True
    return False


def find_public_leaks(
    task_dir: Path, catalog: dict[str, Any] | None, family: dict[str, Any]
) -> list[str]:
    visible_paths = [task_dir / "instruction.md", task_dir / "public_contract.json"]
    text_parts: list[str] = []
    for path in visible_paths:
        if path.is_file():
            text_parts.append(path.read_text(encoding="utf-8", errors="ignore"))
    text = "\n".join(text_parts)
    leaks: list[str] = []
    for pattern in PRIVATE_PATH_PATTERNS:
        if pattern in text:
            leaks.append(f"private_path:{pattern}")
    mutation_ids = [str(item.get("id")) for item in (catalog or {}).get("mutations") or [] if item.get("id")]
    for mutation_id in mutation_ids:
        if re.search(rf"(?<![A-Za-z0-9_]){re.escape(mutation_id)}(?![A-Za-z0-9_])", text):
            leaks.append(f"mutation_id:{mutation_id}")
    solution_root = task_dir / "solution"
    if solution_root.is_dir():
        for source in solution_root.rglob("*.va"):
            for raw_line in source.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = raw_line.strip()
                if public_entry_module_declaration(line, family):
                    continue
                if len(line) >= 48 and line in text:
                    leaks.append(f"gold_code_line:{source.relative_to(task_dir)}")
                    break
    return sorted(set(leaks))


def load_spectre_evidence(
    root: Path,
    evidence_paths: Iterable[Path] | None = None,
) -> list[tuple[Path, dict[str, Any]]]:
    candidates = (
        [Path(path) for path in evidence_paths]
        if evidence_paths is not None
        else sorted((root / "reports" / "first_n_spectre").glob("*.json"))
    )
    evidence: list[tuple[Path, dict[str, Any]]] = []
    for path in candidates:
        try:
            payload = read_json(path)
        except Exception:
            continue
        if isinstance(payload.get("rows"), list):
            evidence.append((path, payload))
    return evidence


def load_local_evas(root: Path, evidence_path: Path | None = None) -> dict[str, list[dict[str, Any]]]:
    path = evidence_path or root / "reports" / "tri_form_first120" / "local_evas_evidence.json"
    if not path.is_file():
        return {}
    try:
        payload = read_json(path)
    except Exception:
        return {}
    by_family: dict[str, list[dict[str, Any]]] = {}
    for record in payload.get("records") or []:
        if isinstance(record, dict):
            by_family.setdefault(str(record.get("family_id") or ""), []).append(record)
    return by_family


def validate_spectre_evidence(
    record: dict[str, Any],
    row: dict[str, Any],
    context: dict[str, Any],
    spectre_evidence: list[tuple[Path, dict[str, Any]]],
) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    family_id = context["family_id"]
    matches: list[tuple[Path, dict[str, Any], dict[str, Any]]] = []
    for path, payload in spectre_evidence:
        for item in payload.get("rows") or []:
            if str(item.get("canonical_id") or "") == family_id:
                matches.append((path, payload, item))
    if not matches:
        issues.append(
            issue(
                "spectre_evidence_missing",
                "missing_evidence",
                f"No current first-N Spectre evidence row found for canonical family {family_id}.",
                "Run run_v4_first_n_spectre.py on a slice containing this canonical family.",
                gate="gate2",
            )
        )
        return {"issues": issues, "selected_path": None}
    # Reports accumulate across certification campaigns.  A lexical filename
    # order is not an evidence freshness policy: legacy files commonly use
    # names such as ``zzzz_final`` and can otherwise shadow a current run.
    # Prefer the record bound to the current task inputs. The release snapshot
    # hash is provenance and does not participate in evidence validity.
    expected_hashes = {
        "family_spec_sha256": context.get("family_spec_sha256"),
        "deck_sha256": context.get("deck_sha256"),
        "harness_spec_sha256": context.get("harness_spec_sha256"),
        "score_profile_sha256": context.get("score_profile_sha256"),
        "checker_profile_sha256": context.get("checker_profile_sha256"),
        "gold_bundle_sha256": context.get("gold_bundle_sha256"),
    }

    def evidence_rank(candidate: tuple[Path, dict[str, Any], dict[str, Any]]) -> tuple[int, str, str]:
        candidate_path, candidate_payload, candidate_item = candidate
        candidate_hashes = candidate_item.get("hashes") or {}
        input_matches = sum(
            expected is not None and candidate_hashes.get(key) == expected
            for key, expected in expected_hashes.items()
        )
        return (input_matches, str(candidate_payload.get("generated_at") or ""), str(candidate_path))

    path, payload, item = max(matches, key=evidence_rank)
    if payload.get("schema_version") in {
        "v4-first-n-spectre-evidence-v1",
        "v4-first-n-spectre-evidence-v2",
    }:
        add_schema_issues(issues, payload, "first_n_spectre", gate="gate2", label="first_n_spectre_evidence")
    hashes = item.get("hashes") or {}
    for key, expected in expected_hashes.items():
        if expected and hashes.get(key) != expected:
            issues.append(
                issue(
                    f"spectre_{key}_mismatch",
                    "hash",
                    f"Spectre evidence row {family_id} has {key}={hashes.get(key)!r}, expected {expected}.",
                    "Regenerate the Spectre evidence after current artifact changes.",
                    gate="gate2",
                )
            )
    identity = item.get("spectre_identity") or {}
    mode = str(identity.get("mode") or "")
    toolchain = context.get("toolchain") or {}
    if toolchain and mode:
        expected_backend = backend_fingerprints(
            toolchain,
            spectre_mode=mode,
        )["spectre_sha256"]
        components = item.get("component_fingerprints") or {}
        observed_backend = (components.get("backend") or {}).get("spectre_sha256")
        if not observed_backend:
            observed_backend = backend_fingerprints(
                {"spectre": identity, "evas": {}},
                spectre_mode=mode,
                spectre_identity=identity,
            )["spectre_sha256"]
        if observed_backend != expected_backend:
            issues.append(
                issue(
                    "spectre_backend_component_stale",
                    "hash",
                    f"Spectre backend component for {family_id} does not match the current declared Spectre semantics.",
                    "Rerun only the affected Spectre backend evidence; retain matching EVAS evidence.",
                    gate="gate2",
                )
            )
    components = item.get("component_fingerprints") or {}
    if components:
        observed_oracle = components.get("oracle") or {}
        expected_oracle = context.get("oracle_fingerprints") or {}
        stale_oracle = [
            key
            for key, expected in expected_oracle.items()
            if observed_oracle.get(key) != expected
        ]
        if stale_oracle:
            issues.append(
                issue(
                    "spectre_checker_component_stale",
                    "hash",
                    f"Spectre checker components for {family_id} are stale: {', '.join(sorted(stale_oracle))}.",
                    "Re-run the current checker from the stored raw trace; rerun Spectre only if required trace signals are absent.",
                    gate="gate2",
                )
            )
    else:
        issues.append(
            issue(
                "spectre_checker_component_unproven",
                "missing_evidence",
                f"Legacy Spectre evidence for {family_id} has no task-specific checker component identity.",
                "Recover the raw trace and re-run the current checker to emit evidence v2; preserve the matching Spectre backend result.",
                gate="gate2",
            )
        )
    spectre = item.get("spectre") or {}
    behavior = item.get("behavior") or {}
    if item.get("status") not in {"PASS", "PASS_WITH_WARNINGS"} or spectre.get("ok") is not True:
        issues.append(
            issue(
                "spectre_behavior_failure",
                "behavioral_failure",
                f"Spectre row status is {item.get('status')!r}; spectre.ok={spectre.get('ok')!r}.",
                "Inspect Spectre errors/behavior notes and fix the DUT/harness/checker mismatch.",
                gate="gate2",
            )
        )
    if behavior.get("score") != 1.0:
        issues.append(
            issue(
                "spectre_checker_score_not_full",
                "behavioral_failure",
                f"Spectre behavior score is {behavior.get('score')!r}, expected 1.0.",
                "Fix the score checker or task artifacts until the gold row receives full credit.",
                gate="gate2",
            )
        )
    missing_signals = [
        sig for sig in context.get("trace_signals", []) if not covers_signal(sig, spectre.get("signals") or [])
    ]
    if missing_signals:
        issues.append(
            issue(
                "spectre_trace_missing_signals",
                "trace",
                f"Spectre trace omits required signals: {', '.join(missing_signals)}.",
                "Regenerate the harness/evidence so Spectre saves the full public trace contract.",
                gate="gate2",
            )
        )
    if spectre.get("untriaged_warnings"):
        issues.append(
            issue(
                "spectre_untriaged_warnings",
                "behavioral_failure",
                "Spectre evidence contains untriaged warnings.",
                "Classify benign warnings or fix the underlying model/harness issue.",
                gate="gate2",
            )
        )
    return {"issues": issues, "selected_path": str(path)}


def validate_local_evas_evidence(family_id: str, local_evas: dict[str, list[dict[str, Any]]]) -> list[dict[str, str]]:
    records = local_evas.get(family_id) or []
    issues: list[dict[str, str]] = []
    by_profile = {str(item.get("profile")): item for item in records}
    for profile in ("feedback", "score"):
        item = by_profile.get(profile)
        if not item:
            issues.append(
                issue(
                    f"evas_{profile}_evidence_missing",
                    "missing_evidence",
                    f"No local EVAS {profile} evidence found for canonical family {family_id}.",
                    "Run run_canonical_local_evas.py for the audited canonical slice.",
                    gate="gate2",
                )
            )
        elif item.get("status") != "pass" or item.get("returncode") != 0:
            issues.append(
                issue(
                    f"evas_{profile}_behavior_failure",
                    "behavioral_failure",
                    f"Local EVAS {profile} evidence status={item.get('status')!r} returncode={item.get('returncode')!r}.",
                    "Inspect local EVAS diagnostics and fix the artifact/checker mismatch.",
                    gate="gate2",
                )
            )
    return issues


def audit_gate2(
    row: dict[str, Any],
    task_dir: Path,
    context: dict[str, Any],
    spectre_evidence: list[tuple[Path, dict[str, Any]]],
    local_evas: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    family = load_optional_json(task_dir / "family_spec.json", issues, gate="gate2", label="family_spec")
    public = load_optional_json(task_dir / "public_contract.json", issues, gate="gate2", label="public_contract")
    checker = load_optional_json(
        task_dir / "evaluator" / "checker_profile.json", issues, gate="gate2", label="checker_profile"
    )
    harness = load_optional_json(
        task_dir / "evaluator" / "harness_spec.json", issues, gate="gate2", label="harness_spec"
    )
    feedback = load_optional_json(
        task_dir / "evaluator" / "profiles" / "feedback.json", issues, gate="gate2", label="feedback_profile"
    )
    score = load_optional_json(
        task_dir / "evaluator" / "profiles" / "score.json", issues, gate="gate2", label="score_profile"
    )
    catalog = load_optional_json(
        task_dir / "negative_variants" / "manifest.json", issues, gate="gate3", label="mutation_catalog"
    )
    if not (task_dir / "instruction.md").is_file():
        issues.append(
            issue(
                "instruction_missing",
                "missing_evidence",
                "instruction.md is missing.",
                "Restore the public instruction surface for this task.",
                gate="gate2",
            )
        )
    if not all([family, public, checker, harness, feedback, score]):
        return {"ready": False, "issues": issues}

    assert family and public and checker and harness and feedback and score
    add_schema_issues(issues, family, "family", gate="gate2", label="family_spec")
    add_schema_issues(issues, harness, "harness", gate="gate2", label="harness_spec")
    add_schema_issues(issues, feedback, "profile", gate="gate2", label="feedback_profile")
    add_schema_issues(issues, score, "profile", gate="gate2", label="score_profile")

    family_id = str(row["canonical_dut_id"])
    artifacts = declared_artifacts(family)
    props = property_ids(family)
    traces = trace_signals(family)
    context.update(
        {
            "family_id": family_id,
            "trace_signals": traces,
            "family_spec_sha256": sha256_file(task_dir / "family_spec.json"),
            "deck_sha256": hashlib.sha256(
                render_scs(harness, score).encode("utf-8")
            ).hexdigest(),
            "harness_spec_sha256": sha256_file(task_dir / "evaluator" / "harness_spec.json"),
            "score_profile_sha256": sha256_file(task_dir / "evaluator" / "profiles" / "score.json"),
            "checker_profile_sha256": sha256_file(task_dir / "evaluator" / "checker_profile.json"),
            "gold_bundle_sha256": bundle_hash(task_dir / "solution", artifacts),
        }
    )
    checker_task_id = str(checker.get("checker_task_id") or "")
    context["oracle_fingerprints"] = checker_fingerprints(
        checker_task_id,
        checker,
        CHECKS.get(checker_task_id),
    )
    context["oracle_fingerprints"]["oracle_runner_sha256"] = benchmark_component_hashes()[
        "oracle_runner_sha256"
    ]

    identity_checks = [
        (family.get("family_id"), family_id, "family_id"),
        ((family.get("task_ids") or {}).get("dut"), f"v4-{family_id}", "family task_ids.dut"),
        (public.get("task_slug"), row.get("old_dut_slug"), "public task_slug"),
        (public.get("title"), row.get("title"), "public title"),
        (public.get("category"), row.get("category"), "public category"),
        (public.get("level"), row.get("level"), "public level"),
        ((family.get("identity") or {}).get("title"), row.get("title"), "family title"),
        ((family.get("identity") or {}).get("category"), row.get("category"), "family category"),
        ((family.get("identity") or {}).get("level"), row.get("level"), "family level"),
        (harness.get("family_id"), family_id, "harness family_id"),
        (harness.get("task_id"), f"v4-{family_id}", "harness task_id"),
    ]
    for observed, expected, label in identity_checks:
        if expected is None:
            continue
        if "title" in label:
            mismatch = canonical_text(observed) != canonical_text(expected)
        else:
            mismatch = observed != expected
        if mismatch:
            issues.append(
                issue(
                    f"{label.replace(' ', '_').replace('.', '_')}_mismatch",
                    "identity",
                    f"{label} is {observed!r}, expected {expected!r} from numbering_plan.json.",
                    "Regenerate the task family artifacts from the canonical numbering plan.",
                    gate="gate2",
                )
            )

    if public.get("target_artifacts") != artifacts or row.get("target_artifacts", artifacts) != artifacts:
        issues.append(
            issue(
                "artifact_identity_mismatch",
                "identity",
                "public_contract/numbering_plan/family_spec target artifacts do not agree.",
                "Use family_spec artifact_contract as the artifact list and refresh public_contract/numbering_plan.",
                gate="gate2",
            )
        )
    if (harness.get("candidate") or {}).get("artifact_paths") != artifacts:
        issues.append(
            issue(
                "harness_candidate_artifact_mismatch",
                "identity",
                "harness candidate artifact_paths do not match family_spec artifact_contract.",
                "Regenerate evaluator/harness_spec.json from family_spec.json.",
                gate="gate2",
            )
        )

    if checker.get("checker_task_id") != public.get("task_id") or (checker.get("contract") or {}).get("task_id") != public.get("task_id"):
        issues.append(
            issue(
                "checker_task_registration_mismatch",
                "checker",
                "checker_profile checker_task_id/contract.task_id does not match public_contract.task_id.",
                "Register the task-specific checker under the current public task id.",
                gate="gate2",
            )
        )
    expected_prefix = f"v4_{family_id}_"
    if not str(checker.get("checker_task_id") or "").startswith(expected_prefix):
        issues.append(
            issue(
                "checker_canonical_prefix_missing",
                "checker",
                f"checker_task_id must start with {expected_prefix!r}.",
                "Rename/register the checker with a task-specific canonical v4 prefix.",
                gate="gate2",
            )
        )
    if checker.get("checker_source_public") is not False or checker.get("score_and_feedback_share_checker") is not True:
        issues.append(
            issue(
                "checker_visibility_or_sharing_invalid",
                "checker",
                "checker_profile must keep checker source private and share the checker family.",
                "Set checker_source_public=false and score_and_feedback_share_checker=true.",
                gate="gate2",
            )
        )

    harness_props = set(str(item) for item in harness.get("property_ids") or [])
    if harness_props != props:
        issues.append(
            issue(
                "harness_property_set_mismatch",
                "property",
                "harness_spec.property_ids does not equal family_spec.properties ids.",
                "Regenerate harness_spec from the current family_spec property set.",
                gate="gate2",
            )
        )
    for profile_name, profile in (("feedback", feedback), ("score", score)):
        if set(str(item) for item in profile.get("property_ids") or []) != props:
            issues.append(
                issue(
                    f"{profile_name}_profile_property_set_mismatch",
                    "property",
                    f"{profile_name}.json property_ids does not equal family_spec properties.",
                    f"Regenerate evaluator/profiles/{profile_name}.json from harness_spec.json.",
                    gate="gate2",
                )
            )
        if profile.get("harness_spec_sha256") != context["harness_spec_sha256"]:
            issues.append(
                issue(
                    f"{profile_name}_profile_harness_hash_stale",
                    "hash",
                    f"{profile_name}.json harness_spec_sha256 is stale.",
                    f"Regenerate evaluator/profiles/{profile_name}.json after harness changes.",
                    gate="gate2",
                )
            )

    for prop in family.get("properties") or []:
        missing = [
            sig
            for sig in prop.get("required_signals") or []
            if not any(covers_signal(str(sig), [trace]) for trace in traces)
        ]
        if missing:
            issues.append(
                issue(
                    f"property_{prop.get('id')}_trace_missing",
                    "trace",
                    f"Property {prop.get('id')} requires signals absent from trace_contract: {', '.join(missing)}.",
                    "Add the property-required signals to family_spec.trace_contract.required_signals.",
                    gate="gate2",
                )
            )

    save_signals = list((harness.get("deck") or {}).get("save_signals") or [])
    for profile in (feedback, score):
        save_signals.extend(((profile.get("deck_overrides") or {}).get("save_signals") or []))
    missing_save = [sig for sig in traces if sig != "time" and not covers_signal(sig, save_signals)]
    if missing_save:
        issues.append(
            issue(
                "harness_save_trace_missing",
                "trace",
                f"Harness save_signals do not cover trace signals: {', '.join(missing_save)}.",
                "Update harness_spec deck/profile save_signals; bus forms like code[3:0] are accepted.",
                gate="gate2",
            )
        )
    public_observables = [str(item) for item in public.get("public_observables") or []]
    for sig in traces:
        if sig != "time" and not covers_signal(sig, public_observables):
            issues.append(
                issue(
                    "public_observable_trace_mismatch",
                    "trace",
                    f"public_observables does not expose trace signal {sig!r}.",
                    "Refresh public_contract.public_observables from family_spec.trace_contract.",
                    gate="gate2",
                )
            )

    source_contract = harness.get("source_contract") or {}
    if source_contract.get("family_spec_sha256") != context["family_spec_sha256"]:
        issues.append(
            issue(
                "harness_family_hash_stale",
                "hash",
                "harness_spec.source_contract.family_spec_sha256 does not match family_spec.json.",
                "Regenerate harness_spec after family_spec changes.",
                gate="gate2",
            )
        )
    if source_contract.get("checker_profile_sha256") != context["checker_profile_sha256"]:
        issues.append(
            issue(
                "harness_checker_hash_stale",
                "hash",
                "harness_spec.source_contract.checker_profile_sha256 does not match checker_profile.json.",
                "Regenerate harness_spec after checker_profile changes.",
                gate="gate2",
            )
        )

    leaks = find_public_leaks(task_dir, catalog, family)
    for leak in leaks:
        issues.append(
            issue(
                "public_surface_private_leak",
                "leak",
                f"Public surface leaks private token {leak}.",
                "Remove private paths, mutation ids, or copied gold code from public files.",
                gate="gate2",
            )
        )

    if public.get("gate2_status") != "cadence_modeling_ready_candidate":
        issues.append(
            issue(
                "gate2_status_not_ready",
                "contract",
                f"public_contract.gate2_status is {public.get('gate2_status')!r}.",
                "Set gate2_status only after all Gate-2 evidence and contracts are current.",
                gate="gate2",
            )
        )
    validation = public.get("validation_status") or {}
    if validation.get("spectre_score_deck") != "PASS" or validation.get("untriaged_warning_count") != 0:
        issues.append(
            issue(
                "public_validation_status_not_pass",
                "behavioral_failure",
                "public_contract.validation_status does not record PASS Spectre score deck with zero untriaged warnings.",
                "Refresh public validation status from current Spectre evidence.",
                gate="gate2",
            )
        )

    spectre_result = validate_spectre_evidence({}, row, context, spectre_evidence)
    issues.extend(spectre_result["issues"])
    issues.extend(validate_local_evas_evidence(family_id, local_evas))

    return {"ready": not issues, "issues": issues, "spectre_evidence": spectre_result.get("selected_path")}


def audit_gate3(row: dict[str, Any], task_dir: Path, context: dict[str, Any]) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    family = load_optional_json(task_dir / "family_spec.json", issues, gate="gate3", label="family_spec")
    catalog = load_optional_json(
        task_dir / "negative_variants" / "manifest.json", issues, gate="gate3", label="mutation_catalog"
    )
    derivation = load_optional_json(
        task_dir / "evaluator" / "derivation_manifest.json", issues, gate="gate3", label="derivation_manifest"
    )
    if not all([family, catalog, derivation]):
        return {"ready": False, "issues": issues}
    assert family and catalog and derivation

    add_schema_issues(issues, catalog, "mutation_catalog", gate="gate3", label="mutation_catalog")
    add_schema_issues(issues, derivation, "derivation", gate="gate3", label="derivation_manifest")
    props = property_ids(family)
    artifacts = set(declared_artifacts(family))
    family_id = str(row["canonical_dut_id"])
    mutation_ids: set[str] = set()
    fault_classes: set[str] = set()
    violated_props: set[str] = set()
    activated_props: set[str] = set()
    certified_count = 0

    if catalog.get("family_id") != family_id or derivation.get("family_id") != family_id:
        issues.append(
            issue(
                "mutation_family_id_mismatch",
                "identity",
                "mutation catalog/derivation family_id does not match canonical numbering.",
                "Regenerate mutation artifacts for the canonical family id.",
                gate="gate3",
            )
        )
    if derivation.get("mutation_catalog_sha256") != sha256_file(task_dir / "negative_variants" / "manifest.json"):
        issues.append(
            issue(
                "derivation_catalog_hash_stale",
                "hash",
                "derivation_manifest.mutation_catalog_sha256 does not match mutation catalog.",
                "Regenerate derivation_manifest after catalog changes.",
                gate="gate3",
            )
        )

    for mutation in catalog.get("mutations") or []:
        mutation_id = str(mutation.get("id") or "")
        mutation_ids.add(mutation_id)
        fault_classes.add(str(mutation.get("fault_class") or ""))
        changed = {str(item) for item in mutation.get("changed_artifacts") or []}
        if not changed <= artifacts:
            issues.append(
                issue(
                    "mutation_unknown_changed_artifact",
                    "contract",
                    f"{mutation_id} changes undeclared artifacts: {sorted(changed - artifacts)}.",
                    "Keep changed_artifacts within family_spec.artifact_contract.files.",
                    gate="gate3",
                )
            )
        hashes = mutation.get("artifact_hashes") or {}
        for artifact in changed:
            path = task_dir / "negative_variants" / mutation_id / artifact
            if not path.is_file():
                issues.append(
                    issue(
                        "mutation_artifact_missing",
                        "missing_evidence",
                        f"{mutation_id} is missing materialized artifact {artifact}.",
                        "Materialize every changed artifact in the mutation bundle.",
                        gate="gate3",
                    )
                )
            elif hashes.get(artifact) != sha256_file(path):
                issues.append(
                    issue(
                        "mutation_artifact_hash_mismatch",
                        "hash",
                        f"{mutation_id} artifact hash mismatch for {artifact}.",
                        "Refresh mutation_catalog artifact_hashes from the materialized bundle.",
                        gate="gate3",
                    )
                )
        mutation_violated = {str(item) for item in mutation.get("violated_property_ids") or []}
        violated_props.update(mutation_violated)
        if not mutation_violated <= props:
            issues.append(
                issue(
                    "mutation_unknown_property",
                    "property",
                    f"{mutation_id} references unknown property ids: {sorted(mutation_violated - props)}.",
                    "Use only property ids declared in family_spec.json.",
                    gate="gate3",
                )
            )
        cert = mutation.get("certification") or {}
        cert_path = task_dir / str(cert.get("evidence_path") or "")
        if not cert.get("evidence_path") or not cert_path.is_file():
            issues.append(
                issue(
                    "mutation_certification_missing",
                    "missing_evidence",
                    f"{mutation_id} lacks certification evidence.",
                    "Run mutation certification and promote the evidence JSON.",
                    gate="gate3",
                )
            )
            continue
        cert_payload = read_json(cert_path)
        add_schema_issues(issues, cert_payload, "certification", gate="gate3", label=f"{mutation_id}_certification")
        cert_inputs = cert_payload.get("inputs") or {}
        cert_profile = str(cert.get("profile") or "feedback")
        profile_path = task_dir / "evaluator" / "profiles" / f"{cert_profile}.json"
        mutation_bundle_sha256 = None
        if all((task_dir / "negative_variants" / mutation_id / artifact).is_file() for artifact in changed):
            mutation_bundle_sha256 = bundle_hash(task_dir / "negative_variants" / mutation_id, changed)
        expected_input_hashes = {
            "mutation_bundle_sha256": mutation_bundle_sha256,
            "checker_profile_sha256": context.get("checker_profile_sha256"),
            "harness_spec_sha256": context.get("harness_spec_sha256"),
            "profile_sha256": sha256_file(profile_path) if profile_path.is_file() else None,
        }
        for key, expected in expected_input_hashes.items():
            if expected and cert_inputs.get(key) != expected:
                issues.append(
                    issue(
                        f"certification_{key}_stale",
                        "hash",
                        f"{mutation_id} certification {key} is stale.",
                        "Recertify mutations after checker/harness/profile changes.",
                        gate="gate3",
                    )
                )
        evaluators = cert_payload.get("evaluators") or {}
        if cert.get("status") == "pending" or cert.get("compile_status") == "pending" or cert.get("simulation_status") == "pending":
            issues.append(
                issue(
                    "mutation_certification_pending",
                    "missing_evidence",
                    f"{mutation_id} certification is still pending.",
                    "Complete EVAS/Spectre certification for this mutation.",
                    gate="gate3",
                )
            )
        elif (
            cert.get("status") != "pass"
            or cert.get("compile_status") != "pass"
            or cert.get("simulation_status") != "pass"
            or cert.get("behavior_status") != "killed_behaviorally"
            or cert_payload.get("outcome") != "killed_behaviorally"
            or evaluators.get("evas") != "compile_pass_behavior_fail"
            or evaluators.get("spectre") != "compile_pass_behavior_fail"
        ):
            issues.append(
                issue(
                    "mutation_not_behaviorally_killed",
                    "behavioral_failure",
                    f"{mutation_id} is not certified as EVAS/Spectre compile-pass behavior-fail.",
                    "Fix checker stimulus/diagnostics or replace this mutation with a semantic behavioral kill.",
                    gate="gate3",
                )
            )
        else:
            certified_count += 1
        activated = set(str(item) for item in cert.get("activated_property_ids") or [])
        activated_payload = set(str(item) for item in (cert_payload.get("diagnostics") or {}).get("violated_property_ids") or [])
        activated_props.update(activated | activated_payload)
        if mutation_violated and not (activated | activated_payload) & mutation_violated:
            issues.append(
                issue(
                    "mutation_property_not_activated",
                    "property",
                    f"{mutation_id} certification does not activate any declared violated property.",
                    "Recertify with diagnostics tied to the violated family property ids.",
                    gate="gate3",
                )
            )

    partition = derivation.get("mutation_partition") or {}
    b = set(partition.get("bugfix_seed") or [])
    p = set(partition.get("testbench_public_feedback") or [])
    h = set(partition.get("testbench_private_score") or [])
    if b & p or b & h or p & h:
        issues.append(
            issue(
                "mutation_partition_overlap",
                "contract",
                "B/P/H mutation partitions overlap.",
                "Assign each mutation id to exactly one B/P/H partition.",
                gate="gate3",
            )
        )
    if b | p | h != mutation_ids:
        issues.append(
            issue(
                "mutation_partition_not_total",
                "contract",
                "B/P/H mutation partitions do not cover exactly the catalog ids.",
                "Refresh derivation_manifest.mutation_partition from mutation_catalog.",
                gate="gate3",
            )
        )
    if len(b) != 1 or len(p) < 1 or len(h) < 3:
        issues.append(
            issue(
                "mutation_partition_count_insufficient",
                "contract",
                f"Partition counts are B={len(b)} P={len(p)} H={len(h)}, expected B=1 P>=1 H>=3.",
                "Add or repartition certified semantic mutations.",
                gate="gate3",
            )
        )
    if len(mutation_ids) < 5 or len({item for item in fault_classes if item}) < 3:
        issues.append(
            issue(
                "mutation_diversity_insufficient",
                "contract",
                f"Catalog has {len(mutation_ids)} mutations and {len({item for item in fault_classes if item})} fault classes.",
                "Provide at least five certified semantic mutations across at least three fault classes.",
                gate="gate3",
            )
        )
    if props and violated_props != props:
        issues.append(
            issue(
                "mutation_property_coverage_incomplete",
                "property",
                f"Mutation catalog covers properties {sorted(violated_props)}, expected {sorted(props)}.",
                "Add certified mutations so every family property has mutation coverage.",
                gate="gate3",
            )
        )
    if props and not props <= activated_props:
        issues.append(
            issue(
                "mutation_activation_coverage_incomplete",
                "property",
                f"Certification activates properties {sorted(activated_props)}, expected at least {sorted(props)}.",
                "Recertify or add mutations with diagnostics activating every family property.",
                gate="gate3",
            )
        )

    return {
        "ready": not issues,
        "issues": issues,
        "mutation_count": len(mutation_ids),
        "certified_mutation_count": certified_count,
        "fault_class_count": len({item for item in fault_classes if item}),
        "partition_counts": {"B": len(b), "P": len(p), "H": len(h)},
    }


def audit_release(
    *,
    root: Path | None = None,
    numbering_plan_path: Path | None = None,
    canonical_first: int = 120,
    spectre_evidence_paths: Iterable[Path] | None = None,
    local_evas_evidence_path: Path | None = None,
) -> dict[str, Any]:
    root = root or ROOT
    numbering_plan_path = numbering_plan_path or root / "reports" / "v4_task_family_numbering" / "numbering_plan.json"
    rows, numbering_hash = load_numbering_plan(numbering_plan_path, canonical_first)
    toolchain_hash = sha256_file(root / "TOOLCHAIN_LOCK.json") if (root / "TOOLCHAIN_LOCK.json").is_file() else None
    toolchain_issues: list[dict[str, str]] = []
    if (root / "TOOLCHAIN_LOCK.json").is_file():
        toolchain = read_json(root / "TOOLCHAIN_LOCK.json")
        add_schema_issues(toolchain_issues, toolchain, "toolchain", gate="gate2", label="toolchain_lock")
    else:
        toolchain_issues.append(
            issue(
                "toolchain_lock_missing",
                "missing_evidence",
                "TOOLCHAIN_LOCK.json is missing.",
                "Generate the current v4 toolchain lock before auditing readiness.",
                gate="gate2",
            )
        )
    spectre_evidence = load_spectre_evidence(root, spectre_evidence_paths)
    local_evas = load_local_evas(root, local_evas_evidence_path)

    records: list[dict[str, Any]] = []
    for row in rows:
        task_dir = root / "tasks" / str(row["old_dut_slug"])
        context: dict[str, Any] = {
            "numbering_hash": numbering_hash,
            "toolchain_hash": toolchain_hash,
            "toolchain": toolchain if (root / "TOOLCHAIN_LOCK.json").is_file() else None,
        }
        if not task_dir.is_dir():
            missing = [
                issue(
                    "task_directory_missing",
                    "missing_evidence",
                    f"Task directory is missing: tasks/{row['old_dut_slug']}",
                    "Materialize the task selected by numbering_plan.json.",
                    gate="gate2",
                )
            ]
            gate2 = {"ready": False, "issues": toolchain_issues + missing}
            gate3 = {"ready": False, "issues": missing}
        else:
            gate2 = audit_gate2(row, task_dir, context, spectre_evidence, local_evas)
            gate2["issues"] = toolchain_issues + gate2["issues"]
            gate3 = audit_gate3(row, task_dir, context)
        records.append(
            {
                "canonical_index": row["canonical_index"],
                "canonical_dut_id": row["canonical_dut_id"],
                "canonical_dut_slug": row.get("canonical_dut_slug"),
                "source_slug": row["old_dut_slug"],
                "title": row.get("title"),
                "gate2": gate2,
                "gate3": gate3,
            }
        )

    def counts(gate: str) -> dict[str, Any]:
        categories = Counter(
            item["category"]
            for record in records
            for item in (record[gate].get("issues") or [])
        )
        codes = Counter(
            item["code"]
            for record in records
            for item in (record[gate].get("issues") or [])
        )
        return {
            "ready_count": sum(bool(record[gate]["ready"]) for record in records),
            "not_ready_count": sum(not bool(record[gate]["ready"]) for record in records),
            "issue_category_counts": dict(sorted(categories.items())),
            "issue_code_counts": dict(sorted(codes.items())),
        }

    return {
        "schema_version": "v4-strict-readiness-audit-v1",
        "generated_at": now_utc(),
        "scope": {
            "canonical_first": canonical_first,
            "family_count": len(records),
            "numbering_plan": str(numbering_plan_path),
            "numbering_plan_sha256": numbering_hash,
            "toolchain_lock_sha256": toolchain_hash,
            "spectre_evidence_paths": [str(path) for path, _payload in spectre_evidence],
            "local_evas_evidence_path": str(local_evas_evidence_path)
            if local_evas_evidence_path is not None
            else str(root / "reports" / "tri_form_first120" / "local_evas_evidence.json"),
        },
        "summary": {"gate2": counts("gate2"), "gate3": counts("gate3")},
        "records": records,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canonical-first", type=int, default=120, metavar="N")
    parser.add_argument(
        "--spectre-evidence",
        type=Path,
        action="append",
        default=None,
        metavar="PATH",
        help="First-N Spectre evidence JSON to audit. May be repeated. Defaults to reports/first_n_spectre/*.json.",
    )
    parser.add_argument(
        "--local-evas-evidence",
        type=Path,
        default=None,
        metavar="PATH",
        help="Local EVAS evidence JSON to audit. Defaults to reports/tri_form_first120/local_evas_evidence.json.",
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = audit_release(
        canonical_first=args.canonical_first,
        spectre_evidence_paths=args.spectre_evidence,
        local_evas_evidence_path=args.local_evas_evidence,
    )
    write_json(args.output, payload)
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
