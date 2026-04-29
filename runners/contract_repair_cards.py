#!/usr/bin/env python3
"""Deterministic repair-card retrieval from behavior contract reports."""
from __future__ import annotations

import argparse
import fnmatch
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CARD_PATH = ROOT / "docs" / "CONTRACT_REPAIR_CARDS.json"
_GENERIC_RELAXED_REPAIR_FAMILIES = {
    "runtime-interface-minimal-harness",
    "compile-interface-syntax-first",
    "clock-event-generator-or-reset-release",
    "manual-contract-extraction-needed",
}


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _as_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def _matches_any(patterns: list[str], values: list[str]) -> bool:
    return any(fnmatch.fnmatchcase(value, pattern) for pattern in patterns for value in values)


def _matches_all(patterns: list[str], values: list[str]) -> bool:
    return all(any(fnmatch.fnmatchcase(value, pattern) for value in values) for pattern in patterns)


def _task_tokens(task_id: str, category: str = "") -> list[str]:
    raw = f"{task_id} {category}".strip().lower().replace("-", "_").replace(" ", "_")
    return [raw, *[part.strip() for part in raw.replace("/", "_").split("_") if part.strip()]]


def _repair_families(report: dict, *, failed_only: bool = True, hard_only: bool = True) -> list[str]:
    families: list[str] = []
    for item in report.get("contract_results", []):
        if failed_only and item.get("passed"):
            continue
        if hard_only and item.get("severity", "hard") != "hard":
            continue
        family = item.get("repair_family")
        if family and family not in families:
            families.append(str(family))
    return families


def _functional_claims(report: dict) -> list[str]:
    claims = report.get("prompt_functional_claims") or []
    if isinstance(claims, list):
        return [str(item) for item in claims if str(item)]
    return []


def _prompt_templates(report: dict) -> list[str]:
    templates = report.get("prompt_checker_templates") or []
    if isinstance(templates, list):
        return [str(item) for item in templates if str(item)]
    return []


def _functional_ir_only() -> bool:
    return os.environ.get("VAEVAS_FUNCTIONAL_IR_ONLY", "").strip().lower() in {"1", "true", "yes", "on"}


def _relaxed_selector_enabled() -> bool:
    return os.environ.get("VAEVAS_RELAXED_CARD_SELECTOR", "").strip().lower() in {"1", "true", "yes", "on"}


def _source(report: dict) -> dict:
    source = report.get("source", {})
    return source if isinstance(source, dict) else {}


def _match_card(card: dict, report: dict, *, task_id: str, category: str = "") -> tuple[bool, int, list[str]]:
    match = card.get("match", {})
    passed = _as_list(report.get("passed_contracts"))
    failed = _as_list(report.get("failed_contracts"))
    failed_hard = _as_list(report.get("failed_hard_contracts") or failed)
    failed_advisory = _as_list(report.get("failed_advisory_contracts"))
    families = _repair_families(report)
    claims = _functional_claims(report)
    prompt_templates = _prompt_templates(report)
    tokens = _task_tokens(task_id, category)

    checks = [
        ("passed_all", passed, _matches_all),
        ("passed_any", passed, _matches_any),
        ("failed_all", failed, _matches_all),
        ("failed_any", failed, _matches_any),
        ("failed_hard_all", failed_hard, _matches_all),
        ("failed_hard_any", failed_hard, _matches_any),
        ("failed_advisory_all", failed_advisory, _matches_all),
        ("failed_advisory_any", failed_advisory, _matches_any),
        ("repair_family_all", families, _matches_all),
        ("repair_family_any", families, _matches_any),
        ("functional_claim_all", claims, _matches_all),
        ("functional_claim_any", claims, _matches_any),
        ("prompt_template_all", prompt_templates, _matches_all),
        ("prompt_template_any", prompt_templates, _matches_any),
    ]
    if not _functional_ir_only():
        checks.extend(
            [
                ("task_keywords_all", tokens, _matches_all),
                ("task_keywords_any", tokens, _matches_any),
            ]
        )

    reasons: list[str] = []
    score = 0
    saw_constraint = False
    for key, values, matcher in checks:
        patterns = _as_list(match.get(key))
        if not patterns:
            continue
        saw_constraint = True
        if not matcher(patterns, values):
            return False, 0, []
        reasons.append(f"{key}={','.join(patterns)}")
        score += 10 if key.endswith("_all") else 6

    if not saw_constraint:
        return False, 0, []
    score += int(card.get("priority", 0))
    return True, score, reasons


def _extended_repair_families(report: dict) -> list[str]:
    families = _repair_families(report)
    source = _source(report)
    for key in (
        "semantic_repair_template",
        "prompt_semantic_repair_template",
        "repair_template",
        "raw_repair_template",
        "blocking_repair_template",
    ):
        value = str(source.get(key, "") or "")
        if value and value not in families:
            families.append(value)
    return families


def _extended_prompt_templates(report: dict) -> list[str]:
    templates = _prompt_templates(report)
    source = _source(report)
    source_checker_templates = _as_list(source.get("prompt_checker_templates"))
    for value in source_checker_templates:
        if value and value not in templates:
            templates.append(value)
    # `prompt_semantic_templates` is intentionally a fallback, not an
    # additive source. It can contain speculative templates that were inferred
    # but not applied to the concrete public observables.
    if not templates:
        for value in _as_list(source.get("prompt_semantic_templates")):
            if value and value not in templates:
                templates.append(value)
    return templates


def _extended_functional_claims(report: dict) -> list[str]:
    claims = _functional_claims(report)
    source = _source(report)
    for value in _as_list(source.get("prompt_functional_claims")):
        if value and value not in claims:
            claims.append(value)
    functional_ir = source.get("prompt_functional_ir", {})
    if isinstance(functional_ir, dict):
        for item in functional_ir.get("claims", []):
            if not isinstance(item, dict):
                continue
            value = str(item.get("type", "") or "")
            if value and value not in claims:
                claims.append(value)
    return claims


def _match_card_relaxed(card: dict, report: dict, *, task_id: str, category: str = "") -> tuple[bool, int, list[str]]:
    """Soft-match mechanism cards when public semantic evidence is already strong.

    The default matcher intentionally requires every declared card constraint to
    match.  That is safe, but too brittle when functional-IR extraction misses a
    claim or when compile/runtime failures prevent CSV-based contract vectors.
    Relaxed mode still requires at least one mechanism-level signal, but treats
    task keywords, prompt templates, repair families, and failed contract names
    as additive evidence instead of an all-or-nothing gate.
    """
    match = card.get("match", {})
    passed = _as_list(report.get("passed_contracts"))
    failed = _as_list(report.get("failed_contracts"))
    failed_hard = _as_list(report.get("failed_hard_contracts") or failed)
    failed_advisory = _as_list(report.get("failed_advisory_contracts"))
    families = _extended_repair_families(report)
    claims = _extended_functional_claims(report)
    prompt_templates = _extended_prompt_templates(report)
    tokens = _task_tokens(task_id, category)

    checks = [
        ("passed_all", passed, _matches_all, 5),
        ("passed_any", passed, _matches_any, 4),
        ("failed_all", failed, _matches_all, 10),
        ("failed_any", failed, _matches_any, 8),
        ("failed_hard_all", failed_hard, _matches_all, 12),
        ("failed_hard_any", failed_hard, _matches_any, 10),
        ("failed_advisory_all", failed_advisory, _matches_all, 5),
        ("failed_advisory_any", failed_advisory, _matches_any, 4),
        ("repair_family_all", families, _matches_all, 12),
        ("repair_family_any", families, _matches_any, 10),
        ("functional_claim_all", claims, _matches_all, 6),
        ("functional_claim_any", claims, _matches_any, 4),
        ("prompt_template_all", prompt_templates, _matches_all, 12),
        ("prompt_template_any", prompt_templates, _matches_any, 10),
    ]
    if not _functional_ir_only():
        checks.extend(
            [
                ("task_keywords_all", tokens, _matches_all, 14),
                ("task_keywords_any", tokens, _matches_any, 12),
            ]
        )

    reasons: list[str] = []
    score = int(card.get("priority", 0))
    matched_keys: set[str] = set()
    saw_constraint = False
    for key, values, matcher, weight in checks:
        patterns = _as_list(match.get(key))
        if not patterns:
            continue
        saw_constraint = True
        if matcher(patterns, values):
            reasons.append(f"{key}={','.join(patterns)}")
            score += weight
            matched_keys.add(key)

    if not saw_constraint:
        return False, 0, []

    prompt_patterns = _as_list(match.get("prompt_template_any")) + _as_list(match.get("prompt_template_all"))
    prompt_matched = "prompt_template_any" in matched_keys or "prompt_template_all" in matched_keys
    task_matched = "task_keywords_any" in matched_keys or "task_keywords_all" in matched_keys
    repair_patterns = _as_list(match.get("repair_family_any")) + _as_list(match.get("repair_family_all"))
    non_generic_repair_matched = any(
        family not in _GENERIC_RELAXED_REPAIR_FAMILIES and fnmatch.fnmatchcase(family, pattern)
        for pattern in repair_patterns
        for family in families
    )
    if prompt_patterns and not prompt_matched and not task_matched and not non_generic_repair_matched:
        return False, 0, []
    if non_generic_repair_matched and not report.get("contract_results"):
        reasons.append("relaxed_selector=no_csv_semantic_guard")
        return True, score, reasons

    mechanism_keys = {
        "failed_all",
        "failed_any",
        "failed_hard_all",
        "failed_hard_any",
        "repair_family_all",
        "repair_family_any",
        "functional_claim_all",
        "functional_claim_any",
        "prompt_template_all",
        "prompt_template_any",
    }
    context_keys = {
        "task_keywords_all",
        "task_keywords_any",
        "passed_all",
        "passed_any",
        "failed_advisory_all",
        "failed_advisory_any",
    }
    has_mechanism = bool(matched_keys & mechanism_keys)
    has_context = bool(matched_keys & context_keys)
    has_two_mechanisms = len(matched_keys & mechanism_keys) >= 2

    # Typical safe cases:
    # - CSV exists: failed contract + prompt/repair-family evidence.
    # - CSV missing: prompt/semantic repair-family evidence + task context.
    if has_two_mechanisms or (has_mechanism and has_context):
        reasons.append("relaxed_selector=semantic_bridge")
        return True, score, reasons
    return False, 0, []


def select_contract_repair_cards(
    report: dict,
    *,
    task_id: str | None = None,
    category: str = "",
    card_path: Path = DEFAULT_CARD_PATH,
    limit: int = 2,
) -> list[dict]:
    cards = _read_json(card_path).get("cards", [])
    task = task_id or str(report.get("task_id", ""))
    scored: list[tuple[int, str, dict]] = []
    for card in cards:
        if _relaxed_selector_enabled():
            matched, score, reasons = _match_card_relaxed(card, report, task_id=task, category=category)
        else:
            matched, score, reasons = _match_card(card, report, task_id=task, category=category)
        if not matched:
            continue
        payload = dict(card)
        payload["match_score"] = score
        payload["match_reasons"] = reasons
        scored.append((score, str(card.get("id", "")), payload))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [payload for _score, _id, payload in scored[:limit]]


def format_contract_repair_cards(cards: list[dict]) -> str:
    if not cards:
        return ""
    lines = [
        "# Contract-Guided Repair Cards",
        "",
        "These mechanism cards were selected deterministically from the behavior-contract vector. Use them only to repair failed hard contracts, while preserving passed contracts.",
    ]
    for card in cards:
        lines.extend([
            "",
            f"## Card `{card.get('id', 'unknown')}`: {card.get('title', '')}",
            f"- Source: `{card.get('source', '')}`",
        ])
        reasons = card.get("match_reasons") or []
        if reasons:
            lines.append(f"- Match: {'; '.join(reasons)}")
        lines.append("- Mechanism:")
        lines.extend(f"  - {item}" for item in card.get("text", []))
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract-report", type=Path, required=True)
    parser.add_argument("--task-id", default="")
    parser.add_argument("--category", default="")
    parser.add_argument("--cards", type=Path, default=DEFAULT_CARD_PATH)
    parser.add_argument("--limit", type=int, default=2)
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    args = parser.parse_args()

    report = _read_json(args.contract_report)
    cards = select_contract_repair_cards(
        report,
        task_id=args.task_id or report.get("task_id"),
        category=args.category,
        card_path=args.cards,
        limit=args.limit,
    )
    if args.format == "markdown":
        print(format_contract_repair_cards(cards))
    else:
        print(json.dumps({"cards": cards}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
