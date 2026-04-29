#!/usr/bin/env python3
"""Build matched-budget retry/repair prompts for model-assisted experiments.

The module is intentionally side-effect light: it reads the frozen task prompt,
the previous candidate artifacts, and optionally an EVAS result, then emits a
single prompt.  API keys are never read here.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import textwrap
from pathlib import Path

from generate import build_prompt, read_meta, extract_module_signature
from score import find_tb_file, find_va_file
from diagnosis_translation import translate_diagnosis, format_repair_section
from observation_repair_policy import build_observation_policy_section
from extract_expected_values import (
    extract_expected_values,
    format_expected_for_prompt,
    get_checker_name_for_task,
    metric_aliases_for_task,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SKILL_BUNDLE = ROOT / "docs" / "TABLE2_VERILOGA_SKILL_BUNDLE.md"
DEFAULT_CONTRACT_REPAIR_CARDS = ROOT / "docs" / "CONTRACT_REPAIR_CARDS.json"
SKILL_REFS_DIR = ROOT.parent / "veriloga-skills" / "veriloga" / "references" / "categories"
_METRIC_TOKEN_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)=([^\s,;]+)")
_NUMERIC_TOKEN_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?$", re.IGNORECASE)
_COLUMN_RANGE_RE = re.compile(r"\b([A-Za-z][A-Za-z0-9]*_?)(\d+)\.\.(\d+)\b")
_TIME_VALUE_RE = re.compile(r"^\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+))(fs|f|ps|p|ns|n|us|u|ms|m|s)?\s*$", re.IGNORECASE)
_TIME_UNITS = {
    None: 1.0,
    "s": 1.0,
    "m": 1e-3,
    "ms": 1e-3,
    "u": 1e-6,
    "us": 1e-6,
    "n": 1e-9,
    "ns": 1e-9,
    "p": 1e-12,
    "ps": 1e-12,
    "f": 1e-15,
    "fs": 1e-15,
}


def _functional_ir_only() -> bool:
    return os.environ.get("VAEVAS_FUNCTIONAL_IR_ONLY", "").strip().lower() in {"1", "true", "yes", "on"}


def _task_id_text_for_matching(task_id: str) -> str:
    """Return task-id text only when benchmark-name matching is allowed.

    I-clean/cold-start runs should select guidance from prompt-derived
    functional IR, contract vectors, and EVAS notes.  In that mode the task id
    remains available for logs and paths but not for semantic routing.
    """
    return "" if _functional_ir_only() else task_id.lower()


def _get_gold_tran_params(task_dir: Path) -> str | None:
    """Read the tran statement from the gold testbench and return it as a string."""
    try:
        gold_dir = task_dir / "gold"
        tbs = sorted(gold_dir.glob("tb*.scs"))
        if not tbs:
            return None
        text = tbs[0].read_text(encoding="utf-8")
        m = re.search(r'\btran\s+\w+\s+(.+)', text)
        return m.group(1).strip() if m else None
    except Exception:
        return None


def _extract_checker_required_columns(task_id: str) -> list[str]:
    """Extract required CSV column names from the checker's issubset call in simulate_evas.py.

    Looks up the checker function name via the CHECKS dict, then finds its issubset call.
    """
    try:
        sim_path = Path(__file__).parent / "simulate_evas.py"
        src = sim_path.read_text(encoding="utf-8")

        # Find what checker function this task_id maps to in CHECKS dict
        checks_match = re.search(
            rf'"{re.escape(task_id)}"\s*:\s*(check_\w+)', src
        )
        if not checks_match:
            return []
        checker_name = checks_match.group(1)

        # Find the function definition and extract its issubset call
        func_match = re.search(rf"def {re.escape(checker_name)}\s*\(", src)
        if not func_match:
            return []
        after_func = src[func_match.start():func_match.start() + 2000]
        issubset_match = re.search(r"not \{([^}]+)\}\.issubset\(rows\[0\]\)", after_func)
        if not issubset_match:
            return []
        return re.findall(r'"([^"]+)"', issubset_match.group(1))
    except Exception:
        return []


def _dedupe_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def _contract_csv_candidates(evas_result: dict) -> list[Path]:
    artifacts = evas_result.get("artifacts") or {}
    candidates: list[Path] = []

    for key in ("tran_csv", "csv_path"):
        value = artifacts.get(key) or evas_result.get(key)
        if value:
            candidates.append(Path(value))

    result_json = artifacts.get("result_json") or evas_result.get("result_json")
    if result_json:
        candidates.append(Path(result_json).parent / "tran.csv")

    seen: set[Path] = set()
    result: list[Path] = []
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        result.append(candidate)
    return result


def _env_truthy(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _contract_repair_cards_section(task_dir: Path, report: dict) -> str:
    if not _env_truthy("VAEVAS_ENABLE_REPAIR_CARDS"):
        return ""
    card_path = Path(os.environ.get("VAEVAS_REPAIR_CARDS_PATH", str(DEFAULT_CONTRACT_REPAIR_CARDS)))
    if not card_path.exists():
        return ""
    try:
        from contract_repair_cards import format_contract_repair_cards, select_contract_repair_cards

        meta = read_meta(task_dir)
        limit = int(os.environ.get("VAEVAS_REPAIR_CARD_LIMIT", "2"))
        cards = select_contract_repair_cards(
            report,
            task_id=meta.get("task_id", meta.get("id", task_dir.name)),
            category=meta.get("category", ""),
            card_path=card_path,
            limit=limit,
        )
        return format_contract_repair_cards(cards)
    except Exception as exc:
        return textwrap.dedent(f"""\
            # Contract-Guided Repair Cards

            Repair-card retrieval was unavailable: `{type(exc).__name__}: {exc}`.
            Continue using the behavior-contract diagnosis above.
        """).strip()


def _circuit_mechanism_rag_section(task_dir: Path, evas_result: dict) -> str:
    """Append prompt-derived circuit-mechanism RAG hints when enabled.

    This is intentionally advisory.  It does not use gold code or task-id
    routing; the query is built from the public prompt, inferred functional IR,
    and the current EVAS notes.
    """
    if not _env_truthy("VAEVAS_ENABLE_CIRCUIT_RAG"):
        return ""
    try:
        from infer_prompt_checker_specs import infer_specs
        from run_circuit_mechanism_rag_audit import build_knowledge_base, retrieve, _query_text

        resolved_task_dir = task_dir.resolve()
        prompt = (resolved_task_dir / "prompt.md").read_text(encoding="utf-8", errors="ignore")
        record = infer_specs(resolved_task_dir.name, resolved_task_dir, include_gold_save_names=False)
        templates = [
            str(item.get("template", ""))
            for item in record.get("templates", [])
            if float(item.get("confidence", 0.0)) >= float(os.environ.get("VAEVAS_RAG_TEMPLATE_THRESHOLD", "0.62"))
        ]
        claims = [
            str(item.get("type", ""))
            for item in record.get("functional_ir", {}).get("claims", [])
            if isinstance(item, dict) and item.get("type")
        ]
        prompt_l = prompt.lower()
        explicit_count_style = any(
            phrase in prompt_l
            for phrase in (
                "thermometer",
                "unary",
                "population count",
                "count of ones",
                "count high",
                "number of high",
            )
        )
        if not explicit_count_style:
            templates = [item for item in templates if "thermometer" not in item and "unary" not in item]
            claims = [item for item in claims if item != "count_high_to_analog"]
        notes = [str(item) for item in (evas_result.get("evas_notes") or evas_result.get("notes") or [])]
        report = {
            "failed_contracts": [],
            "failed_hard_contracts": [],
            "contract_results": [],
            "prompt_checker_templates": templates,
            "prompt_functional_claims": claims,
            "source": {
                "prompt_checker_templates": templates,
                "prompt_functional_claims": claims,
                "prompt_functional_ir": record.get("functional_ir", {}),
            },
        }
        query = "\n".join(
            [
                _query_text(prompt, record, report),
                "evas_status " + str(evas_result.get("status", "")),
                "evas_notes " + " ".join(notes),
            ]
        )
        nodes = build_knowledge_base(include_skills=_env_truthy("VAEVAS_RAG_INCLUDE_SKILLS"))
        node_by_id = {node.node_id: node for node in nodes}
        top_k = int(os.environ.get("VAEVAS_RAG_TOP_K", "4"))
        max_chars = int(os.environ.get("VAEVAS_RAG_NODE_MAX_CHARS", "1400"))
        raw_retrieved = retrieve(nodes, query, top_k=max(top_k * 30, 80))
        filtered = []
        for item in raw_retrieved:
            node = node_by_id.get(str(item.get("node_id")))
            if node is None:
                continue
            node_l = f"{node.node_id} {node.title} {node.text}".lower()
            node_head_l = f"{node.node_id} {node.title}".lower()
            if not explicit_count_style and ("thermometer" in node_head_l or "unary" in node_head_l) and "dwa" not in node_head_l:
                continue
            filtered.append(item)
        if _env_truthy("VAEVAS_RAG_DIVERSIFY_KINDS") or os.environ.get("VAEVAS_RAG_DIVERSIFY_KINDS", "1") == "1":
            retrieved = []
            seen_ids: set[str] = set()

            def add_first(kind: str, *, min_score: float = 0.0) -> None:
                for candidate in filtered:
                    if candidate.get("kind") != kind:
                        continue
                    if float(candidate.get("score", 0.0)) < min_score:
                        continue
                    node_id = str(candidate.get("node_id"))
                    if node_id in seen_ids:
                        continue
                    retrieved.append(candidate)
                    seen_ids.add(node_id)
                    return

            # Prefer executable skeletons and compact mechanism summaries when
            # available. Template nodes explain what failed; skeleton/card/R26
            # nodes explain how to build it.
            add_first("mechanism_skeleton", min_score=8.0)
            add_first("r26_template", min_score=10.0)
            add_first("repair_card", min_score=10.0)
            add_first("prompt_template", min_score=0.0)
            for candidate in filtered:
                if len(retrieved) >= top_k:
                    break
                node_id = str(candidate.get("node_id"))
                if node_id in seen_ids:
                    continue
                retrieved.append(candidate)
                seen_ids.add(node_id)
        else:
            retrieved = filtered[:top_k]
        if len(retrieved) > top_k:
            retrieved = retrieved[:top_k]
        if not retrieved:
            return ""

        lines = [
            "# Circuit-Mechanism RAG Hints",
            "",
            "Use these prompt-matched mechanism hints as soft guidance. Keep the original module interface and EVAS artifact contract authoritative.",
        ]
        if templates or claims:
            lines.append(f"- Inferred prompt templates: {', '.join(f'`{item}`' for item in templates) or '`none`'}")
            lines.append(f"- Inferred functional claims: {', '.join(f'`{item}`' for item in claims) or '`none`'}")
        for rank, item in enumerate(retrieved, start=1):
            node = node_by_id.get(str(item.get("node_id")))
            if node is None:
                continue
            if node.kind == "mechanism_skeleton":
                metadata = node.metadata or {}
                pieces = []
                slot_schema = metadata.get("slot_schema", {})
                if isinstance(slot_schema, dict) and slot_schema:
                    pieces.append("Slots: " + "; ".join(f"{key}={value}" for key, value in slot_schema.items()))
                impl = metadata.get("implementation_skeleton", [])
                if impl:
                    pieces.append("Implementation: " + " ".join(str(part) for part in impl))
                shape = metadata.get("veriloga_shape", [])
                if shape:
                    pieces.append("Verilog-A shape: " + " | ".join(str(part) for part in shape))
                anti = metadata.get("anti_patterns", [])
                if anti:
                    pieces.append("Avoid: " + " ".join(str(part) for part in anti))
                snippet = " ".join(pieces) if pieces else node.text
            else:
                snippet = node.text
            snippet = re.sub(r"\s+", " ", snippet).strip()
            if len(snippet) > max_chars:
                snippet = snippet[: max_chars - 3].rstrip() + "..."
            lines.extend(
                [
                    "",
                    f"{rank}. `{node.node_id}` ({node.kind}, score={item.get('score')})",
                    f"   - Title: {node.title}",
                    f"   - Guidance: {snippet}",
                ]
            )
        return "\n".join(lines)
    except Exception as exc:
        return textwrap.dedent(f"""\
            # Circuit-Mechanism RAG Hints

            RAG hint retrieval was unavailable: `{type(exc).__name__}: {exc}`.
            Continue using EVAS notes and any contract/card guidance above.
        """).strip()


def _lego_mechanism_skill_section(task_dir: Path, evas_result: dict) -> str:
    """Append typed LEGO-style mechanism skill packets when enabled.

    Unlike the older RAG hints, this section has an explicit skill schema:
    function concepts, slot binding, checker expectations, implementation
    skeleton, and Spectre constraints.  It is prompt/EVAS-note based by
    default and does not route from task id.
    """
    if not _env_truthy("VAEVAS_ENABLE_LEGO_SKILLS"):
        return ""
    try:
        from lego_skill_library import format_lego_skill_prompt, retrieve_lego_skills

        prompt = (task_dir / "prompt.md").read_text(encoding="utf-8", errors="ignore")
        meta_path = task_dir / "meta.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
        notes = [str(item) for item in (evas_result.get("evas_notes") or evas_result.get("notes") or [])]
        result = retrieve_lego_skills(
            prompt,
            meta=meta,
            notes=notes,
            top_k=int(os.environ.get("VAEVAS_LEGO_SKILL_TOP_K", "3")),
            use_meta_family=_env_truthy("VAEVAS_LEGO_USE_META_FAMILY"),
            use_meta_slots=_env_truthy("VAEVAS_LEGO_USE_META_SLOTS"),
        )
        packets = result.get("skills", [])
        if not packets:
            return ""
        lines = [
            format_lego_skill_prompt(packets),
            "",
            "Functional routing evidence:",
            "- Concepts: " + ", ".join(f"`{item}`" for item in result.get("functional_ir", {}).get("concepts", [])),
            "- Negative constraints: " + (
                ", ".join(f"`{item}`" for item in result.get("functional_ir", {}).get("negative_constraints", [])) or "`none`"
            ),
        ]
        return "\n".join(lines).strip()
    except Exception as exc:
        return textwrap.dedent(f"""\
            # LEGO-Style Mechanism Skills

            LEGO skill retrieval was unavailable: `{type(exc).__name__}: {exc}`.
            Continue using EVAS notes, behavior contracts, and generic repair guidance.
        """).strip()


def _contract_report_without_csv(task_dir: Path, contracts_path: Path) -> dict:
    """Build a semantic guard report when no waveform CSV exists yet.

    Compile/runtime failures often block the normal contract checker, but the
    generated contract spec still carries public prompt templates and semantic
    repair-family hints.  Relaxed card selection can use those hints to inject
    a mechanism-preservation card while the model fixes the blocking layer.
    """
    try:
        spec = json.loads(contracts_path.read_text(encoding="utf-8"))
    except Exception:
        spec = {}
    source = spec.get("source", {}) if isinstance(spec.get("source", {}), dict) else {}
    functional_ir = source.get("prompt_functional_ir", {}) if isinstance(source.get("prompt_functional_ir", {}), dict) else {}
    functional_claims = source.get("prompt_functional_claims", [])
    if not functional_claims:
        functional_claims = [
            str(item.get("type", ""))
            for item in functional_ir.get("claims", [])
            if isinstance(item, dict) and item.get("type")
        ]
    return {
        "task_id": spec.get("task_id", task_dir.name),
        "contract_path": str(contracts_path),
        "csv_path": "",
        "source": source,
        "prompt_functional_ir": functional_ir,
        "prompt_functional_claims": functional_claims,
        "prompt_checker_templates": source.get("prompt_checker_templates", []),
        "prompt_checker_signal_sources": source.get("prompt_checker_signal_sources", {}),
        "status": "NO_CSV",
        "advisory_status": "PASS",
        "passed_contracts": [],
        "failed_contracts": [],
        "passed_hard_contracts": [],
        "passed_advisory_contracts": [],
        "failed_hard_contracts": [],
        "failed_advisory_contracts": [],
        "contract_results": [],
        "diagnostic_summary": [],
    }


def _contract_source_for_task(task_dir: Path) -> dict:
    """Read prompt-derived contract source metadata for mechanism routing.

    This helper is intentionally task-id independent when
    `VAEVAS_FUNCTIONAL_IR_ONLY=1`: it reads the task's generated contracts,
    whose source fields are produced from the public prompt/functional IR.
    """
    contract_paths: list[Path] = []
    external_root = os.environ.get("VAEVAS_CONTRACT_ROOT")
    if external_root:
        contract_paths.append(Path(external_root) / task_dir.name / "contracts.json")
    contract_paths.append(task_dir / "contracts.json")
    for path in contract_paths:
        if not path.exists():
            continue
        try:
            spec = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        source = spec.get("source", {})
        if isinstance(source, dict):
            return source
    return {}


def _contract_mechanism_tokens(task_dir: Path, notes: list[str]) -> set[str]:
    source = _contract_source_for_task(task_dir)
    tokens: set[str] = set()
    for key in (
        "semantic_family",
        "prompt_semantic_family",
        "semantic_repair_template",
        "prompt_semantic_repair_template",
        "repair_template",
        "raw_repair_template",
        "blocking_repair_template",
    ):
        value = source.get(key)
        if value:
            tokens.add(str(value))
    for key in ("prompt_checker_templates", "prompt_semantic_templates", "prompt_functional_claims"):
        values = source.get(key, [])
        if isinstance(values, list):
            tokens.update(str(item) for item in values if str(item))
    functional_ir = source.get("prompt_functional_ir", {})
    if isinstance(functional_ir, dict):
        for claim in functional_ir.get("claims", []):
            if isinstance(claim, dict) and claim.get("type"):
                tokens.add(str(claim["type"]))
    lowered_notes = "\n".join(str(note) for note in notes).lower()
    for marker in (
        "dynamic_analog_vector_index",
        "conditional_transition",
        "duplicate_vsource_branch",
        "evas_timeout",
        "ptr_",
        "cell_en_",
        "late_edge_ratio",
        "lag_window_updn",
        "up_first",
        "dn_second",
        "vdac",
        "frame_rises",
    ):
        if marker in lowered_notes:
            tokens.add(marker)
    return tokens


def _behavior_contract_diagnosis_section(task_dir: Path, evas_result: dict) -> str:
    """Summarize optional task-local behavior contracts for repair prompts.

    Contracts are hidden benchmark checks. The prompt gets pass/fail names and
    abstract repair hints, not raw thresholds or gold implementation details.
    """
    contract_paths: list[Path] = []
    external_root = os.environ.get("VAEVAS_CONTRACT_ROOT")
    if external_root:
        contract_paths.append(Path(external_root) / task_dir.name / "contracts.json")
    contract_paths.append(task_dir / "contracts.json")
    contracts_path = next((path for path in contract_paths if path.exists()), None)
    if contracts_path is None:
        return ""

    csv_path = next((path for path in _contract_csv_candidates(evas_result) if path.exists()), None)
    if csv_path is None:
        report = _contract_report_without_csv(task_dir, contracts_path)
        source = report.get("source", {})
        semantic_family = source.get("semantic_family") or source.get("prompt_semantic_family") or ""
        semantic_repair = source.get("semantic_repair_template") or source.get("prompt_semantic_repair_template") or ""
        prompt_templates = report.get("prompt_checker_templates", [])
        lines = textwrap.dedent("""\
            # Behavior Contract Diagnosis

            Task-local behavior contracts are available, but no transient CSV from the failed run was found.
            Continue using EVAS notes and preserve any already-fixed observability behavior.
        """).strip().splitlines()
        if semantic_family or semantic_repair or prompt_templates:
            lines.extend(
                [
                    "",
                    "Public semantic guard while CSV is unavailable:",
                    f"- Semantic family: `{semantic_family or 'unknown'}`",
                    f"- Semantic repair family: `{semantic_repair or 'unknown'}`",
                ]
            )
            if prompt_templates:
                lines.append(f"- Prompt templates: {', '.join(f'`{item}`' for item in prompt_templates)}")
            lines.append(
                "- First repair the blocking compile/runtime layer, but preserve this mechanism shape for the next EVAS round."
            )
        card_section = _contract_repair_cards_section(task_dir, report)
        if card_section:
            lines.extend(["", card_section])
        return "\n".join(lines)

    try:
        from contract_check import run_contracts

        report = run_contracts(contracts_path, csv_path)
    except Exception as exc:
        return textwrap.dedent(f"""\
            # Behavior Contract Diagnosis

            Task-local behavior contract diagnosis was unavailable: `{type(exc).__name__}: {exc}`.
            Continue using EVAS notes and preserve any already-fixed observability behavior.
        """).strip()

    passed = report.get("passed_contracts") or []
    failed = report.get("failed_contracts") or []
    failed_hard = report.get("failed_hard_contracts")
    failed_advisory = report.get("failed_advisory_contracts")
    if failed_hard is None:
        failed_hard = failed
    if failed_advisory is None:
        failed_advisory = []
    summaries = report.get("diagnostic_summary") or []
    failed_families = _dedupe_preserve_order(
        [
            str(item.get("repair_family"))
            for item in report.get("contract_results", [])
            if not item.get("passed") and item.get("severity", "hard") == "hard" and item.get("repair_family")
        ]
    )

    lines = [
        "# Behavior Contract Diagnosis",
        "",
        "Use these task-local contract outcomes as repair guidance. Preserve passed contracts, fix hard failures first, and treat advisory failures as secondary hints.",
        "",
        f"- Contract status: `{report.get('status', 'UNKNOWN')}`",
    ]
    if passed:
        lines.append(f"- Passed contracts: {', '.join(f'`{name}`' for name in passed)}")
    if failed_hard:
        lines.append(f"- Failed hard contracts: {', '.join(f'`{name}`' for name in failed_hard)}")
    if failed_advisory:
        lines.append(f"- Advisory hints still failing: {', '.join(f'`{name}`' for name in failed_advisory)}")
    if failed and not failed_hard and not failed_advisory:
        lines.append(f"- Failed contracts: {', '.join(f'`{name}`' for name in failed)}")
    if failed_families:
        lines.append(f"- Repair families to prioritize: {', '.join(f'`{name}`' for name in failed_families)}")
    if summaries:
        lines.append("")
        lines.append("Diagnostic hints:")
        for summary in summaries:
            lines.append(f"- {summary}")

    card_section = _contract_repair_cards_section(task_dir, report)
    if card_section:
        lines.extend(["", card_section])

    return "\n".join(lines)


def _expand_column_ranges(text: str) -> list[str]:
    """Expand compact checker notes such as `ptr_0..15` or `dout_3..0`."""
    columns: list[str] = []
    for prefix, start_s, end_s in _COLUMN_RANGE_RE.findall(text):
        start = int(start_s)
        end = int(end_s)
        step = 1 if end >= start else -1
        columns.extend(f"{prefix}{idx}" for idx in range(start, end + step, step))
    return columns


def _observable_columns_from_notes(task_id: str, notes: list[str]) -> list[str]:
    """Infer checker-visible CSV columns from EVAS observable failure notes.

    The checker is the source of truth, but many notes are written as compact
    human strings (`missing vin/clk/dout2/...`, `ptr_0..15`).  This function
    turns those strings into explicit scalar names for the repair skeleton.
    """
    task_lower = _task_id_text_for_matching(task_id)
    joined = "\n".join(str(note) for note in notes)
    lowered = joined.lower()
    columns: list[str] = []

    columns.extend(_expand_column_ranges(joined))

    for note in notes:
        note_text = str(note)
        lowered_note = note_text.lower()
        if not (
            lowered_note.startswith("missing ")
            or "missing " in lowered_note
            or "expected " in lowered_note
            or "need " in lowered_note
        ):
            continue
        # Keep only the payload-like part of the diagnostic and split slash lists.
        payload = note_text
        if "missing " in payload:
            payload = payload.split("missing ", 1)[1]
        payload = re.sub(r"\([^)]*\)", " ", payload)
        payload = payload.replace(" or ", "/").replace(" and ", "/").replace(",", "/")
        payload = payload.replace("..", "_RANGE_")
        for token in re.split(r"[/\s]+", payload):
            token = token.replace("_RANGE_", "..").strip("`.;:")
            if not token:
                continue
            if ".." in token:
                columns.extend(_expand_column_ranges(token))
                continue
            if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", token):
                if token not in {
                    "missing", "required", "columns", "need", "expected", "rows",
                    "or", "and", "columns", "column", "all", "these", "names",
                }:
                    columns.append(token)

    if "missing dout_code or dout_3..0" in lowered:
        columns.extend(["vin", "vout", "rst_n", "dout_3", "dout_2", "dout_1", "dout_0"])
    if "missing dout_0..7" in lowered:
        columns.extend(["vin", "vin_sh", "vout", "rst_n"])
        columns.extend(f"dout_{idx}" for idx in range(8))
    if "missing time/clk_i/rst_ni/ptr_0/cell_en_0" in lowered:
        columns.extend(["time", "clk_i", "rst_ni"])
        columns.extend(f"ptr_{idx}" for idx in range(16))
        columns.extend(f"cell_en_{idx}" for idx in range(16))
    if "missing time/clk_i/rst_ni/ptr_0/cell_en_0/code_0" in lowered:
        columns.extend(["time", "clk_i", "rst_ni"])
        columns.extend(f"ptr_{idx}" for idx in range(16))
        columns.extend(f"cell_en_{idx}" for idx in range(16))
        columns.extend(f"code_{idx}" for idx in range(4))
    if "missing required columns" in lowered and "ptr_code/cell_en_code" in lowered:
        columns.extend(["clk_i", "rst_ni", "ptr_code", "cell_en_code"])
        columns.extend(f"ptr_{idx}" for idx in range(16))
        columns.extend(f"cell_en_{idx}" for idx in range(16))

    checker_cols = _extract_checker_required_columns(task_id)
    if checker_cols:
        columns.extend(checker_cols)

    # Family-specific checker contracts that are not always statically visible
    # because the checker builds `required` sets programmatically.
    if "flash_adc_3b" in task_lower:
        columns.extend(["vin", "clk", "dout2", "dout1", "dout0"])
    elif "sample_hold" in task_lower:
        columns.extend(["time", "vin", "clk", "vout"])
    elif "serializer" in task_lower:
        columns.extend(["time", "load", "clk", "sout"])

    columns = _dedupe_preserve_order(columns)
    # When the checker accepts either a synthetic integer code or explicit bit
    # columns, prefer bit columns in the alias skeleton.  Synthetic code
    # columns are easy to ask for but hard to create portably in raw Spectre CSV.
    if "dout_code" in columns and any(col.startswith("dout_") for col in columns):
        columns = [col for col in columns if col != "dout_code"]
    if {"ptr_code", "cell_en_code"}.issubset(columns) and any(col.startswith("ptr_") for col in columns):
        columns = [col for col in columns if col not in {"ptr_code", "cell_en_code"}]
    return columns


def _numeric_suffix_groups(columns: list[str]) -> dict[str, list[int]]:
    groups: dict[str, list[int]] = {}
    for col in columns:
        match = re.match(r"^(.+_)(\d+)$", col)
        if not match:
            continue
        groups.setdefault(match.group(1), []).append(int(match.group(2)))
    return {prefix: sorted(set(indices)) for prefix, indices in groups.items()}


def _observable_scalar_alias_template(task_id: str, notes: list[str]) -> list[str]:
    """Reusable repair skeleton for checker-visible scalar waveform columns."""
    columns = _observable_columns_from_notes(task_id, notes)
    lowered = "\n".join(str(note) for note in notes).lower()
    should_emit = columns and (
        "missing " in lowered
        or "missing_" in lowered
        or "not enough" in lowered
        or "too_few" in lowered
        or "insufficient_post_reset_samples" in lowered
        or "observability" in lowered
    )
    if not should_emit:
        return []

    save_columns = [col for col in columns if col != "time"]
    grouped = _numeric_suffix_groups(columns)
    grouped_lines: list[str] = []
    for prefix, indices in sorted(grouped.items()):
        if not indices:
            continue
        grouped_lines.append(f"- `{prefix}{indices[0]}..{prefix}{indices[-1]}` as separate top-level scalar nodes.")

    lines = [
        "",
        "# Reusable Repair Skeleton: Observable Scalar CSV Alias",
        "",
        "This is a generic observable-contract repair. It does not change the intended circuit behavior; it makes the checker-required signals visible to EVAS as stable CSV columns.",
        "",
        "## Required checker-visible CSV columns",
        "",
        "- `" + " ".join(columns) + "`",
        "",
        "## Skeleton",
        "",
        "1. Create or preserve top-level Spectre nodes with exactly the required scalar names.",
        "2. Connect DUT ports directly to those scalar nodes. Prefer positional instance wiring; do not use SystemVerilog-style brace bundles such as `{dout_3 dout_2 ...}` in Spectre.",
        "3. For every bus-like observable, expose each bit as its own scalar node, not as `bus[0]`, `XDUT:bus[0]`, or a hierarchical/internal name.",
        "4. Save the scalar names directly with one canonical save list. Do not use instance-qualified save syntax such as `XDUT:out`.",
        "5. Do not use save aliases such as `save code_i[0] as code_0`; EVAS will not treat that as a stable `code_0` CSV column. The top-level node itself must be named `code_0`.",
        "6. If a checker accepts either an integer code column or bit columns, prefer bit columns because they are simulator-stable across EVAS and Spectre.",
        "7. Keep reset release, transient stop, and clock/stimulus coverage sufficient to produce post-reset samples; `tran stop` must be after reset deassertion plus several clock periods.",
        "8. Do not repair behavior until the CSV columns are correct.",
    ]
    if save_columns:
        lines.extend([
            "",
            "Canonical save statement:",
            f"- `save {' '.join(save_columns)}`",
        ])
    if grouped_lines:
        lines.extend(["", "Detected scalar bus groups:"])
        lines.extend(grouped_lines)
    if any(col.startswith(("ptr_", "cell_en_", "code_")) for col in columns):
        lines.extend([
            "",
            "DWA-style observable wiring pattern:",
            "- Use scalar testbench nodes `ptr_0 ... ptr_15`, `cell_en_0 ... cell_en_15`, and when required `code_0 ... code_3`.",
            "- Drive code stimulus sources on scalar nodes directly, e.g. `Vcode0 (code_0 0) ...`, not on `code_i[0]` followed by `save ... as code_0`.",
            "- Connect scalar nodes positionally into the DUT ports, e.g. `(... code_0 code_1 code_2 code_3 cell_en_0 ... ptr_0 ...) module_name`.",
            "- Instantiate the DUT so each output bit connects to the matching scalar node name.",
            "- Then save those scalar nodes directly. The checker reconstructs integer codes from these columns.",
        ])
    if any(col.startswith("dout_") for col in columns) or {"dout2", "dout1", "dout0"} & set(columns):
        lines.extend([
            "",
            "ADC/SAR/serializer-style observable wiring pattern:",
            "- Connect every output bit to a top-level scalar node with the checker's exact name and bit order.",
            "- Do not save `dout[0]` or generated vector headers; save `dout_0`, `dout_1`, etc. exactly when those are required.",
            "- Verify that reset deasserts before the conversion/output window so the saved columns contain non-reset behavior.",
        ])
    lines.extend([
        "",
        "Stop condition for this layer:",
        "- The next EVAS result should no longer contain `missing ...` or `tran.csv missing`. If it still fails, it should expose a behavior metric such as `unique_codes`, `too_few_edges`, `sample_mismatch`, or `bad_ptr_rows`.",
    ])
    return lines


def _spectre_time_seconds(raw: str | None) -> float | None:
    if raw is None:
        return None
    match = _TIME_VALUE_RE.match(raw.strip())
    if not match:
        return None
    unit = match.group(2).lower() if match.group(2) else None
    return float(match.group(1)) * _TIME_UNITS.get(unit, 1.0)


def _format_seconds(value: float | None) -> str:
    if value is None:
        return "<unknown>"
    for unit, scale in (("ms", 1e-3), ("us", 1e-6), ("ns", 1e-9), ("ps", 1e-12)):
        scaled = value / scale
        if abs(scaled) >= 1.0:
            return f"{scaled:.4g}{unit}"
    return f"{value:.4g}s"


def _assignment_time(line: str, name: str) -> float | None:
    match = re.search(rf"\b{re.escape(name)}\s*=\s*([^\s\]]+)", line, flags=re.IGNORECASE)
    return _spectre_time_seconds(match.group(1)) if match else None


def _assignment_token(line: str, name: str) -> str | None:
    match = re.search(rf"\b{re.escape(name)}\s*=\s*([^\s\]]+)", line, flags=re.IGNORECASE)
    return match.group(1).strip() if match else None


def _wave_value_is_high(raw: str) -> bool | None:
    token = raw.strip().lower()
    if token in {"vdd", "vhigh", "vh", "val1"}:
        return True
    if token in {"0", "0.0", "vss", "gnd"}:
        return False
    try:
        return float(token) > 0.45
    except ValueError:
        return None


def _pwl_first_low_to_high_time(line: str) -> float | None:
    match = re.search(r"wave\s*=\s*\[([^\]]+)\]", line, flags=re.IGNORECASE)
    if not match:
        return None
    tokens = match.group(1).replace(",", " ").split()
    pairs = list(zip(tokens[0::2], tokens[1::2]))
    prev_high: bool | None = None
    for time_raw, value_raw in pairs:
        high = _wave_value_is_high(value_raw)
        if high is None:
            continue
        if prev_high is False and high is True:
            return _spectre_time_seconds(time_raw)
        prev_high = high
    return None


def _clock_reset_timing_facts(sample_dir: Path | None) -> dict:
    if sample_dir is None:
        return {}
    tb_path = find_tb_file(sample_dir)
    if not tb_path:
        return {}
    lines = tb_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    facts: dict[str, object] = {
        "tb": tb_path.name,
        "tran_lines": [],
        "clock_lines": [],
        "reset_lines": [],
    }
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("//"):
            continue
        lowered = line.lower()
        if re.search(r"\btran\b", lowered):
            facts.setdefault("tran_lines", []).append(line)
            facts.setdefault("tran_stop_s", _assignment_time(line, "stop"))
        if "vsource" in lowered and "pulse" in lowered and "clk" in lowered:
            facts.setdefault("clock_lines", []).append(line)
            if facts.get("clock_period_s") is None:
                facts["clock_period_s"] = _assignment_time(line, "period")
            if facts.get("clock_delay_s") is None:
                facts["clock_delay_s"] = _assignment_time(line, "delay") or 0.0
        if "vsource" in lowered and ("rst" in lowered or "reset" in lowered):
            facts.setdefault("reset_lines", []).append(line)
            release = _assignment_time(line, "delay")
            if release is None and "pwl" in lowered:
                release = _pwl_first_low_to_high_time(line)
            if facts.get("reset_release_s") is None:
                facts["reset_release_s"] = release

    stop_s = facts.get("tran_stop_s")
    period_s = facts.get("clock_period_s")
    clk_delay_s = facts.get("clock_delay_s") or 0.0
    reset_s = facts.get("reset_release_s") or 0.0
    if isinstance(stop_s, float) and isinstance(period_s, float) and period_s > 0:
        first_valid_s = max(float(clk_delay_s), float(reset_s)) + 1e-15
        facts["estimated_post_reset_edges"] = max(0, int((stop_s - first_valid_s) // period_s) + 1)
    return facts


def _reset_source_release_issue(sample_dir: Path | None) -> dict | None:
    """Detect reset sources that deassert only temporarily then reassert.

    A common LLM TB bug is using `type=pulse val0=0 val1=VDD width=50n`
    for an active-low reset.  In Spectre pulse semantics this is high only for
    `width`, then returns low, so the DUT is reset during the checker window.
    """
    if sample_dir is None:
        return None
    tb_path = find_tb_file(sample_dir)
    if not tb_path:
        return None

    lines = tb_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    tran_stop_s: float | None = None
    reset_candidates: list[dict] = []
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("//"):
            continue
        lowered = line.lower()
        if re.search(r"\btran\b", lowered):
            tran_stop_s = _assignment_time(line, "stop") or tran_stop_s
        if "vsource" not in lowered or "pulse" not in lowered:
            continue
        if not ("rst" in lowered or "reset" in lowered):
            continue

        val0 = _assignment_token(line, "val0")
        val1 = _assignment_token(line, "val1")
        width_s = _assignment_time(line, "width")
        delay_s = _assignment_time(line, "delay") or 0.0
        if val0 is None or val1 is None or width_s is None:
            continue

        active_low = any(token in lowered for token in ("rstb", "rst_n", "rst_ni", "reset_n", "resetb"))
        val0_high = _wave_value_is_high(val0)
        val1_high = _wave_value_is_high(val1)
        if val0_high is None or val1_high is None:
            continue

        reasserts_after_width = False
        if active_low and not val0_high and val1_high:
            reasserts_after_width = True
        if not active_low and val0_high and not val1_high:
            reasserts_after_width = True
        if not reasserts_after_width:
            continue

        reassert_s = delay_s + width_s
        reset_candidates.append({
            "line": line,
            "active_low": active_low,
            "delay_s": delay_s,
            "width_s": width_s,
            "reassert_s": reassert_s,
            "tran_stop_s": tran_stop_s,
        })

    if not reset_candidates:
        return None
    # Prefer a source that reasserts before the transient ends.
    for candidate in reset_candidates:
        stop = candidate.get("tran_stop_s")
        if isinstance(stop, float) and candidate["reassert_s"] < stop:
            return candidate
    return reset_candidates[0]


def _reset_hold_contract_template(task_id: str, notes: list[str], sample_dir: Path | None) -> list[str]:
    issue = _reset_source_release_issue(sample_dir)
    joined = "\n".join(str(note) for note in notes).lower()
    task_lower = _task_id_text_for_matching(task_id)
    if issue is None and not (
        "not_enough_clk_edges" in joined
        or "not_enough_post_reset" in joined
        or "no post-reset samples" in joined
        or ("gray" in task_lower and "bad_transitions" in joined)
    ):
        return []

    lines = [
        "",
        "# Reusable Repair Skeleton: Reset Release Must Persist",
        "",
        "This is a generic testbench/bring-up repair. Many behavior failures are caused by a reset source that deasserts briefly and then reasserts during the checker window.",
        "",
        "## Required reset contract",
        "",
        "- Identify whether reset is active-low (`rstb`, `rst_n`, `rst_ni`) or active-high (`rst`, `reset`).",
        "- Reset may assert at the beginning, but after release it must remain deasserted through the entire checking window.",
        "- Do not model reset release with a finite-width pulse that returns to the active reset level before `tran stop`.",
        "- Prefer a PWL source that explicitly holds the deasserted level until the final transient stop time.",
        "- Repair this TB timing layer before changing DUT behavior when EVAS shows too few post-reset samples/edges or a state machine stuck in reset.",
    ]
    if issue:
        polarity = "active-low" if issue["active_low"] else "active-high"
        lines.extend([
            "",
            "## Detected candidate reset source",
            "",
            f"- Reset polarity inferred from signal name: `{polarity}`.",
            f"- Existing source: `{issue['line']}`",
            f"- Parsed reset reassertion time: `{_format_seconds(issue['reassert_s'])}`.",
            f"- Parsed tran stop: `{_format_seconds(issue.get('tran_stop_s'))}`.",
            "",
            "Why this matters:",
            "- In Spectre pulse semantics, the source returns from `val1` back to `val0` after `width`.",
            "- For active-low reset, `val0=0 val1=VDD width=...` means reset is deasserted only during `width`, then asserted low again.",
            "- For active-high reset, `val0=VDD val1=0 width=...` has the analogous problem.",
        ])
    lines.extend([
        "",
        "Safe edit patterns:",
        "- Active-low reset release: use a PWL such as `wave=[0 0 20n 0 20.1n 1.8 <stop> 1.8]`.",
        "- Active-high reset release: use a PWL such as `wave=[0 1.8 20n 1.8 20.1n 0 <stop> 0]`.",
        "- If using a pulse anyway, ensure the deasserted level lasts beyond `tran stop`; otherwise use PWL.",
        "- Keep clock and enable active after reset release so the checker observes valid post-reset behavior.",
        "",
        "Stop condition for this layer:",
        "- The next EVAS result should no longer show reset-window symptoms such as `not_enough_post_reset_edges`, `not_enough_clk_edges`, `no post-reset samples`, or state outputs stuck at reset values.",
    ])
    return lines


def _clocked_output_settle_template(task_id: str, notes: list[str], sample_dir: Path | None) -> list[str]:
    joined = "\n".join(str(note) for note in notes).lower()
    task_lower = _task_id_text_for_matching(task_id)
    markers = (
        "gray_property_violated",
        "bad_transitions",
        "q_mismatch",
        "qb_mismatch",
        "bit_mismatch",
        "sample_mismatch",
    )
    if not any(marker in joined for marker in markers):
        return []
    if not any(token in task_lower for token in ("gray", "counter", "dff", "serializer", "adc", "dac", "sar")):
        return []

    facts = _clock_reset_timing_facts(sample_dir)
    tedge_lines: list[str] = []
    if sample_dir is not None:
        for va_path in sorted(sample_dir.glob("*.va"))[:4]:
            text = va_path.read_text(encoding="utf-8", errors="ignore")
            for match in re.finditer(r"parameter\s+real\s+(?:t(?:edge|rise|fall|d)|tr|tf)\s*=\s*([^;]+);", text):
                tedge_lines.append(f"{va_path.name}: `{match.group(0).strip()}`")
                if len(tedge_lines) >= 4:
                    break
            if len(tedge_lines) >= 4:
                break

    lines = [
        "",
        "# Reusable Repair Skeleton: Clocked Digital Output Settling",
        "",
        "This is a generic clocked-output repair. If the DUT state sequence is logically correct but EVAS still reports bit/transition mismatches, the checker may be sampling before `transition()` outputs have crossed its logic threshold.",
        "",
        "## Settling rule",
        "",
        "- Keep discrete state in held integer/real target variables.",
        "- Update those target variables once per valid clock edge.",
        "- Drive electrical outputs continuously from the targets with `transition()`.",
        "- Ensure the transition rise/fall is fast enough for the checker sampling offset and `tran maxstep`.",
        "- For smoke tests with sub-ns sampling after a clock edge, use a small edge time such as `10p` when a `tedge`/`tr`/`tf` parameter is available.",
        "- Alternatively keep the checker threshold reasonable by using digital stimulus high levels near `2*vth` when the public task permits it.",
        "- If the module exposes `tedge`, `tr`, or `tf`, the safest minimal repair is a testbench instance override such as `XDUT (...) module_name tedge=10p`; this preserves the module's public default while making the smoke waveform settle before sampling.",
        "",
        "Required edit pattern:",
        "- Do not rewrite a correct counter/serializer/ADC algorithm just because EVAS reports sampled bit mismatches.",
        "- First reduce output `transition()` edge time or override the exposed transition parameter in the testbench instance.",
        "- If the same mismatch metric stayed unchanged across the previous round, make the transition-parameter override mandatory in the next answer; do not return another cosmetic DUT rewrite.",
        "- Preserve reset release, clock period, save names, module names, and bit order while changing only the settle-time parameter.",
    ]
    if facts.get("tran_lines") or facts.get("clock_lines") or tedge_lines:
        lines.extend(["", "## Current candidate timing facts", ""])
        if facts.get("tran_lines"):
            lines.append("- Tran: `" + " | ".join(facts["tran_lines"]) + "`")
        if facts.get("clock_lines"):
            lines.append("- Clock source: `" + " | ".join(facts["clock_lines"][:2]) + "`")
        if tedge_lines:
            lines.append("- Output transition parameters:")
            lines.extend(f"  - {line}" for line in tedge_lines)
            lines.extend([
                "",
                "Concrete next edit if no other metric moved:",
                "- Keep the Verilog-A default parameter if the task lists one, but instantiate the DUT with a faster smoke-test edge, e.g. `... gray_counter_4b tedge=10p` or the equivalent for the current module.",
            ])
    lines.extend([
        "",
        "Stop condition for this layer:",
        "- The next EVAS result should preserve compile/passable waveform columns and reduce sampled mismatch metrics such as `bad_transitions`, `q_mismatch`, `bit_mismatch`, or `sample_mismatch`.",
    ])
    return lines


def _post_reset_sample_budget_template(task_id: str, notes: list[str], sample_dir: Path | None) -> list[str]:
    joined = "\n".join(str(note) for note in notes)
    lowered = joined.lower()
    if not any(
        marker in lowered
        for marker in (
            "insufficient_post_reset_samples",
            "no post-reset samples",
            "no_clock_edges",
            "too_few_edges",
            "too_few_clock_edges",
            "not_enough_edges",
        )
    ):
        return []

    facts = _clock_reset_timing_facts(sample_dir)
    lines = [
        "",
        "# Reusable Repair Skeleton: Post-Reset Sample Budget",
        "",
        "This is a generic observable/stimulus-window repair. Do not change DUT behavior until the checker can observe enough post-reset clocked samples.",
        "",
        "## Budget rule",
        "",
        "- Compute the available post-reset window: `tran_stop - reset_deassert_time`.",
        "- Estimate valid sampled edges: `floor((tran_stop - max(reset_deassert_time, clock_start_time)) / clock_period)`.",
        "- For smoke tests, target at least 6 post-reset rising edges unless the checker note requires more.",
        "- Remember that several checkers sample at `rising_edge_time + 1ns`, so the last useful edge must occur before `tran_stop - 1ns`.",
        "- If the strict benchmark `tran stop` is fixed, do not extend the stop time as the first repair. Instead release reset earlier, start the clock earlier, or shorten the clock period while preserving the task's intended stimulus.",
        "",
        "## Required edit pattern",
        "",
        "1. Keep the canonical `tran` line required by the task unless EVAS says the tran itself is invalid.",
        "2. Move reset deassertion near the beginning of the transient window.",
        "3. Choose a clock period that produces enough rising edges before `tran stop`.",
        "4. Align PWL stimulus changes before the clock edges that the checker samples.",
        "5. Preserve scalar save names and module/interface wiring while fixing timing.",
    ]
    if facts:
        lines.extend(["", "## Current candidate timing facts", ""])
        if facts.get("tran_lines"):
            lines.append("- Tran: `" + " | ".join(facts["tran_lines"]) + "`")
        if facts.get("clock_lines"):
            lines.append("- Clock source: `" + " | ".join(facts["clock_lines"][:2]) + "`")
        if facts.get("reset_lines"):
            lines.append("- Reset source: `" + " | ".join(facts["reset_lines"][:2]) + "`")
        lines.extend([
            f"- Parsed `tran_stop`: `{_format_seconds(facts.get('tran_stop_s'))}`",
            f"- Parsed `clock_period`: `{_format_seconds(facts.get('clock_period_s'))}`",
            f"- Parsed `clock_start`: `{_format_seconds(facts.get('clock_delay_s'))}`",
            f"- Parsed `reset_deassert`: `{_format_seconds(facts.get('reset_release_s'))}`",
        ])
        if "estimated_post_reset_edges" in facts:
            lines.append(f"- Estimated post-reset clock edges before stop: `{facts['estimated_post_reset_edges']}`")
            if int(facts["estimated_post_reset_edges"]) < 6:
                lines.extend([
                    "",
                    "Budget diagnosis:",
                    "- The current harness does not provide enough post-reset edges for the checker.",
                    "- Repair timing first. For example, with `tran stop=90n`, a `100n` clock period cannot produce enough post-reset sampled cycles; use an earlier reset release and a shorter clock period that fits multiple edges inside 90ns.",
                ])
    lines.extend([
        "",
        "Stop condition for this layer:",
        "- The next EVAS result should no longer contain `insufficient_post_reset_samples`, `too_few_edges`, `too_few_clock_edges`, or `no_clock_edges`.",
        "- If it still fails after this repair, it should expose a behavior metric such as code coverage, pointer count, pulse overlap, or sample mismatch.",
    ])
    return lines


def _inject_skill_reference(task_id: str) -> list[str]:
    """根据任务类型，注入 Skill 中对应的电路原理文档片段"""
    if not SKILL_REFS_DIR.exists():
        return []

    # 根据任务 ID 选择参考文档
    ref_mapping = {
        "pll": "pll-clock.md",
        "adpll": "pll-clock.md",
        "cppll": "pll-clock.md",
        "pfd": "pll-clock.md",
        "vco": "pll-clock.md",
        "mux": "digital-logic.md",
        "divider": "digital-logic.md",
        "clk_divider": "digital-logic.md",
        "counter": "digital-logic.md",
        "lfsr": "digital-logic.md",
        "prbs": "digital-logic.md",
        "digital": "digital-logic.md",
        "gate": "digital-logic.md",
        "dff": "digital-logic.md",
        "flip": "digital-logic.md",
        "dwa": "dac.md",
        "dac": "dac.md",
        "adc": "adc-sar.md",
        "sar": "adc-sar.md",
        "comparator": "comparator.md",
        "cmp": "comparator.md",
        "strongarm": "comparator.md",
        "hysteresis": "comparator.md",
        "sample_hold": "sample-hold.md",
        "sample": "sample-hold.md",
        "sampler": "sample-hold.md",
        "bbpd": "pll-clock.md",
        "filter": "amplifier-filter.md",
        "lpf": "amplifier-filter.md",
    }

    task_lower = _task_id_text_for_matching(task_id)
    matched_ref = None
    for key, ref_file in ref_mapping.items():
        if key in task_lower:
            matched_ref = ref_file
            break

    if not matched_ref:
        return []

    ref_path = SKILL_REFS_DIR / matched_ref
    if not ref_path.exists():
        return []

    # 读取文档，截取前 3000 字符（避免过长）
    content = ref_path.read_text(encoding="utf-8")
    if "dwa" in task_lower and matched_ref == "dac.md":
        match = re.search(
            r"### DWA / Thermometer Pointer.*?(?=\n## |\Z)",
            content,
            flags=re.DOTALL,
        )
        if match:
            content = match.group(0)
    # 只取原理说明部分，去掉代码示例的详细内容
    lines = content.splitlines()
    filtered_lines = []
    for line in lines:
        filtered_lines.append(line)
        if len(filtered_lines) > 100:  # 限制行数
            break

    filtered_content = "\n".join(filtered_lines)
    if len(filtered_content) > 2500:
        filtered_content = filtered_content[:2500] + "\n... (truncated)"

    return [
        "",
        "# Circuit-Specific Knowledge (from veriloga-skills)",
        "",
        f"Reference: `{matched_ref}`",
        "",
        filtered_content,
    ]


def _inject_check_expectations(task_dir: Path) -> list[str]:
    """直接传完整Checker源码给闭环AI，让它自己分析期望值"""
    # 获取 task_id
    meta_path = task_dir / "meta.json"
    task_id = ""
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            task_id = meta.get("task_id", meta.get("id", task_dir.name))
        except Exception:
            task_id = task_dir.name

    if not task_id:
        task_id = task_dir.name

    # 获取对应的 checker 函数名
    checker_name = get_checker_name_for_task(task_id)

    # 提取完整 checker 源码
    source = _extract_checker_source(checker_name)
    if not source:
        return []

    # 添加电路知识补充
    circuit_context = _get_circuit_context(task_id)

    # 直接传完整源码
    lines = [
        "",
        "# Checker Function (评分标准)",
        "",
        "以下是 evaluate your generated circuit 的 checker 函数源码。",
        "它定义了期望的电路行为（评分标准），不包含具体实现方案。",
        "",
        "请仔细阅读 checker 源码，理解期望的行为条件，然后修复你的代码使其满足这些条件。",
        "",
        "```python",
        source,
        "```",
    ]

    if circuit_context:
        lines.extend(["", "# Circuit Context", "", circuit_context])

    return lines


def _extract_checker_source(checker_name: str) -> Optional[str]:
    """从 simulate_evas.py 提取完整 checker 函数源码"""
    import re
    simulate_evas_path = ROOT / "runners" / "simulate_evas.py"

    if not simulate_evas_path.exists():
        return None

    content = simulate_evas_path.read_text(encoding="utf-8")

    # 匹配函数定义到下一个 def 或文件结束
    pattern = rf"^(def {checker_name}\([^)]*\).*?)(?=\ndef [a-z_]|\Z)"
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)

    if not match:
        return None

    source = match.group(1).strip()

    # 限制长度（避免过长）
    if len(source) > 3000:
        source = source[:3000] + "\n... (truncated)"

    return source


def _get_circuit_context(task_id: str) -> str:
    """根据 task_id 关键词提供简短的电路上下文"""
    task_lower = _task_id_text_for_matching(task_id)

    if "pll" in task_lower or "adpll" in task_lower or "cppll" in task_lower:
        return """
PLL (Phase-Locked Loop) basics:
- Lock condition: fb_clk frequency ≈ ref_clk frequency, phase aligned
- VCTRL (control voltage) should settle to a stable value
- Divider ratio: output_freq = vco_freq / divider_ratio
"""
    elif "pfd" in task_lower:
        return """
PFD (Phase-Frequency Detector) basics:
- UP pulse when ref leads fb (early)
- DN pulse when ref lags fb (late)
- UP/DN should NOT overlap when locked
"""
    elif "mux" in task_lower:
        return """
MUX (Multiplexer) basics:
- SEL signal selects which input passes to output
- SEL=00→d0, SEL=01→d1, SEL=10→d2, SEL=11→d3 (for 4-to-1)
"""
    elif "bbpd" in task_lower:
        return """
BBPD (Bang-Bang Phase Detector) basics:
- Used for clock/data recovery
- UP when data edge leads clock, DN when lags
"""
    elif "dac" in task_lower:
        return """
DAC (Digital-to-Analog) basics:
- Binary-weighted: each bit has different weight (1, 2, 4, 8...)
- Monotonic: increasing code → increasing output
"""
    elif "comparator" in task_lower or "cmp" in task_lower:
        return """
Comparator basics:
- Output HIGH when vinp > vinn (or threshold)
- Hysteresis: two thresholds (rising +vhys/2, falling -vhys/2)
"""
    elif "divider" in task_lower or "clk_div" in task_lower:
        return """
Clock Divider basics:
- Output frequency = input frequency / division_ratio
- Counter increments on each clock, output toggles at threshold
"""
    elif "sample_hold" in task_lower or "sample" in task_lower:
        return """
Sample-Hold basics:
- sample=HIGH: output tracks input
- sample=LOW: output holds last value
"""

    return ""


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _file_block(path: Path) -> str:
    suffix = path.suffix.lower()
    lang = "spectre" if suffix == ".scs" else "verilog-a"
    return f"### {path.name}\n\n```{lang}\n{path.read_text(encoding='utf-8', errors='ignore').strip()}\n```"


def _gold_dut_port_order_hints(task_dir: Path, notes: list[str]) -> list[str]:
    gold_dir = task_dir / "gold"
    if not gold_dir.is_dir():
        return []

    for note in notes:
        match = re.search(r"gold_dut_alias=([^;\s]+\.va)->([^;\s]+\.va)", note)
        if not match:
            continue
        gold_va_name = Path(match.group(1)).name
        staged_va_name = Path(match.group(2)).name
        gold_va_path = gold_dir / gold_va_name
        if not gold_va_path.exists():
            continue
        signature = extract_module_signature(gold_va_path)
        if not signature:
            continue
        module_name, ports = signature
        port_list = ", ".join(ports)
        return [
            "",
            "Gold DUT interface contract:",
            f"- EVAS mapped Gold DUT `{gold_va_name}` to testbench include `{staged_va_name}`.",
            f"- Gold DUT module name: `{module_name}`",
            f"- Gold DUT positional port order: `({port_list})`",
            f"- Instantiate exactly as: `XDUT ({port_list}) {module_name}`",
        ]
    return []


def _artifact_contract(family: str) -> str:
    if family in ("spec-to-va", "bugfix"):
        return (
            "Return exactly one complete Verilog-A DUT file in a fenced "
            "`verilog-a` code block. Do not return a testbench."
        )
    if family == "tb-generation":
        return (
            "Return exactly one complete Spectre testbench in a fenced "
            "`spectre` code block. Do not return a DUT."
        )
    return (
        "Return the complete DUT artifact set required by the task: one or "
        "more Verilog-A DUT files in separate `verilog-a` code blocks as "
        "needed, followed by exactly one complete Spectre testbench in a "
        "`spectre` code block. Do not omit an unchanged file."
    )


def _end_to_end_shape_guidance(task_prompt: str, family: str) -> str:
    if family != "end-to-end":
        return ""
    guidance = [
        "End-to-end shape requirements:",
        "- The final answer may contain multiple `verilog-a` code blocks if the task asks for multiple modules.",
        "- Output exactly one complete top-level `spectre` testbench block.",
        "- Do not concatenate several standalone mini-testbenches into one `.scs` file.",
        "- Put shared directives such as `simulator`, `global`, `save`, and `tran` in the single final testbench, not repeated per sub-block.",
        "- Every `ahdl_include` used by the testbench must correspond to a DUT file you emitted in this same answer.",
        "- Choose module granularity from the task contract, not from circuit size alone.",
        "- If the task asks for a single behavioral block, keep one coherent module; do not invent internal submodules just because the real circuit could be hierarchical.",
        "- If the task asks for multiple named blocks/modules, preserve that split and make each block independently meaningful while verifying the integrated top-level behavior.",
    ]
    lowered = task_prompt.lower()
    if "separate modules" in lowered or "implement four" in lowered or "implement two" in lowered:
        guidance.extend([
            "- This task explicitly asks for multiple DUT modules.",
            "- Emit one complete `verilog-a` block per requested module before the single `spectre` block.",
        ])
    return "\n".join(guidance)


def load_skill_bundle(path: Path | None = None) -> str:
    bundle_path = path or DEFAULT_SKILL_BUNDLE
    return bundle_path.read_text(encoding="utf-8").strip()


def _skill_section(skill_bundle_text: str | None) -> str:
    if not skill_bundle_text:
        return ""
    return textwrap.dedent(f"""\
        # Frozen Skill Bundle

        {skill_bundle_text.strip()}
    """).strip()


def _candidate_sections(sample_dir: Path) -> list[str]:
    sections: list[str] = []
    for va_path in sorted(sample_dir.glob("*.va")):
        sections.append(_file_block(va_path))
    tb_path = find_tb_file(sample_dir)
    if tb_path:
        sections.append(_file_block(tb_path))
    if not sections:
        sections.append("No previous candidate files were found.")
    return sections


def _score_summary(evas_result: dict) -> str:
    scores = evas_result.get("scores", {})
    # Include both evas_notes and spectre_notes (for Spectre backend results)
    notes = evas_result.get("evas_notes") or evas_result.get("notes") or []
    spectre_notes = evas_result.get("spectre_notes", [])
    all_notes = notes + [n for n in spectre_notes if n not in notes]
    note_text = "\n".join(f"- {note}" for note in all_notes[:20]) or "- <none>"
    required = ", ".join(evas_result.get("required_axes", [])) or "<unknown>"

    # Add structure diagnosis summary
    diag = evas_result.get("structure_diagnosis")
    diag_text = ""
    if diag:
        mismatch = diag.get("mismatch_detail", [])
        if mismatch:
            diag_text = "\n\nStructure mismatch:\n" + "\n".join(f"- {d}" for d in mismatch)

    return textwrap.dedent(f"""\
        EVAS status: {evas_result.get("status", "<unknown>")}
        Required axes: {required}
        Scores:
        - dut_compile: {scores.get("dut_compile", "<missing>")}
        - tb_compile: {scores.get("tb_compile", "<missing>")}
        - sim_correct: {scores.get("sim_correct", "<missing>")}
        - weighted_total: {scores.get("weighted_total", "<missing>")}

        EVAS notes:
        {note_text}{diag_text}
    """)


def _parse_metric_token(token: str) -> float | bool | str:
    cleaned = token.strip().strip("`")
    lowered = cleaned.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if _NUMERIC_TOKEN_RE.match(cleaned):
        try:
            return float(cleaned)
        except ValueError:
            pass
    return cleaned


def _extract_metrics_from_notes(notes: list[str]) -> dict[str, float | bool | str]:
    metrics: dict[str, float | bool | str] = {}
    for note in notes:
        for key, raw_value in _METRIC_TOKEN_RE.findall(note):
            metrics[key] = _parse_metric_token(raw_value)
    return metrics


def _dwa_plan_execute_section(task_id: str, notes: list[str]) -> list[str]:
    """Return a DWA-specific plan-and-execute repair block.

    This is intentionally written as a retrieval-style policy: EVAS metrics
    select the relevant DWA knowledge snippet and a bounded edit plan.
    """
    metrics = _extract_metrics_from_notes(notes)
    joined_notes = "\n".join(str(note) for note in notes).lower()
    task_allows_dwa = "dwa" in _task_id_text_for_matching(task_id) or any(
        marker in joined_notes
        for marker in (
            "ptr_",
            "cell_en_",
            "bad_ptr_rows",
            "bad_count_rows",
            "wrap_events",
            "overlap_count",
            "max_active_cells",
        )
    )
    if not task_allows_dwa:
        return []
    if not metrics and "insufficient_post_reset_samples" not in joined_notes:
        return []

    def fnum(key: str, default: float = 0.0) -> float:
        value = metrics.get(key, default)
        return float(value) if isinstance(value, (int, float)) else default

    lines = [
        "",
        "# Plan-and-Execute Repair Policy: DWA",
        "",
        "Do this repair in two phases. First reason from EVAS metrics, then edit the code.",
        "Do not rewrite unrelated testbench structure or module interfaces while fixing DWA behavior.",
        "",
        "## Retrieved DWA Skill Snippet",
        "",
        "- Keep `ptr_q`, `code_q`, and runtime loop index `j` as `integer` state.",
        "- Keep `cell_en_val[0:15]` and `ptr_val[0:15]` as real arrays storing output targets.",
        "- Use fixed-index reads for code bits inside the clock event; never use `V(code_i[i])` with integer `i`.",
        "- Clear all 16 `cell_en_val` and `ptr_val` entries before setting the next active window.",
        "- Drive buses with a module-scope `genvar k` contribution loop after the event logic.",
        "",
        "## Required Repair Plan",
        "",
        "1. Preserve compile-clean structure: no runtime analog bus indexing, no conditional `cross`, no `genvar` inside `analog begin`.",
        "2. Decode `code_q` once per rising clock edge from four fixed input bits.",
        "3. Compute a fresh 16-cell active window from `ptr_q` and `code_q`.",
        "4. Set exactly one pointer output high for the checker-visible pointer location.",
        "5. Set exactly `code_q` cell-enable outputs high when `code_q > 0`.",
        "6. Update `ptr_q` consistently with the selected window and task-specific wrap/no-overlap rule.",
        "7. Keep the observable CSV names required by the original task prompt.",
        "8. Keep reset release and transient stop consistent: reset must deassert before the checker sampling window, and `tran stop` must be after several post-reset clock edges.",
        "",
        "## DWA Behavior Skeleton",
        "",
        "- Treat `code_q` as the single decoded integer command for the current clock edge.",
        "- Treat `ptr_q` as the single pointer state; do not derive different pointer values for `ptr_o` and `cell_en_o`.",
        "- At each valid rising clock edge, clear all `ptr_val[*]` and `cell_en_val[*]` before setting the new outputs.",
        "- Drive exactly one pointer bit high unless reset is active.",
        "- Drive exactly `code_q` cell-enable bits high when `code_q > 0`; drive zero cells when `code_q == 0`.",
        "- Keep all output targets in arrays and drive electrical bus bits from those arrays with unconditional contributions.",
        "",
        "## DWA Bit/Port Order Guardrail",
        "",
        "- Check the positional bus expansion order before changing the algorithm.",
        "- For ports declared `[3:0] code_i`, scalar Spectre harnesses commonly connect MSB-to-LSB as `code_3 code_2 code_1 code_0`.",
        "- For ports declared `[15:0] ptr_o` or `cell_en_o`, scalar harnesses commonly connect `*_15 ... *_0`.",
        "- Therefore the Verilog-A decode should read fixed bus indices semantically: `code_i[0]` is LSB, `code_i[3]` is MSB, and output bit index `j` must mean checker column `ptr_j` or `cell_en_j`.",
        "- If EVAS reports `wrap_events` and `split_wrap_rows` are already good but `bad_ptr_rows`/`bad_count_rows` remain high, suspect pointer update order, output bit order, or one-cycle timing before redesigning the DWA concept.",
    ]

    if "no_overlap" in task_id:
        lines.extend([
            "",
            "## EVAS Metric Interpretation: No-Overlap DWA",
            f"- `sampled_cycles={_format_scalar(metrics.get('sampled_cycles', '<missing>'))}`",
            f"- `bad_ptr_rows={_format_scalar(metrics.get('bad_ptr_rows', '<missing>'))}`",
            f"- `max_active_cells={_format_scalar(metrics.get('max_active_cells', '<missing>'))}`",
            f"- `overlap_count={_format_scalar(metrics.get('overlap_count', '<missing>'))}`",
        ])
        if fnum("max_active_cells") <= 0.0:
            lines.extend([
                "- Root cause: the checker sees no active `cell_en_*` bit after reset.",
                "- Execute: after decoding nonzero `code_q`, set at least one `cell_en_val[index] = vdd`; do not leave the array cleared.",
            ])
        if fnum("bad_ptr_rows") > 0.0:
            lines.extend([
                "- Root cause: pointer output is not one-hot or has multiple active bits.",
                "- Execute: clear every `ptr_val[j]`, then set only `ptr_val[ptr_q] = vdd`.",
            ])
        if fnum("overlap_count") > 0.0:
            lines.extend([
                "- Root cause: consecutive active cell sets overlap.",
                "- Execute: advance `ptr_q` by the prior window width before selecting the next window, or choose a disjoint next start.",
                "- Also check feasibility: two consecutive windows cannot be disjoint if the active-cell count is too large for a 16-cell array.",
                "- If the generated testbench drives large codes such as 14 or 15, change the public stimulus to small nonzero codes such as 1 or 2 for the no-overlap smoke window.",
                "- Keep the DUT code-to-active-count relation correct for the sampled code; make the smoke stimulus choose a code sequence whose requested windows can actually be disjoint.",
            ])
        if fnum("max_active_cells") > 8.0:
            lines.extend([
                "- `max_active_cells` is larger than half the 16-cell array. That makes consecutive disjoint windows impossible for many cycles.",
                "- For this no-overlap smoke test, prefer low code stimulus values and verify the DUT selects exactly those small windows.",
            ])
        lines.extend([
            "- Success target for next EVAS run: `bad_ptr_rows=0`, `max_active_cells>0`, and `overlap_count=0`.",
        ])
    elif "wraparound" in task_id:
        lines.extend([
            "",
            "## EVAS Metric Interpretation: Wraparound DWA",
            f"- `sampled_cycles={_format_scalar(metrics.get('sampled_cycles', '<missing>'))}`",
            f"- `bad_ptr_rows={_format_scalar(metrics.get('bad_ptr_rows', '<missing>'))}`",
            f"- `bad_count_rows={_format_scalar(metrics.get('bad_count_rows', '<missing>'))}`",
            f"- `wrap_events={_format_scalar(metrics.get('wrap_events', '<missing>'))}`",
            f"- `split_wrap_rows={_format_scalar(metrics.get('split_wrap_rows', '<missing>'))}`",
        ])
        if "insufficient_post_reset_samples" in joined_notes:
            lines.extend([
                "- Root cause: the testbench produced too few post-reset samples. This usually happens when reset deasserts after the transient stop time, or the clock starts too late.",
                "- Execute: keep/reset `rst_ni` deasserted early enough and set `tran stop` long enough to include at least five post-reset rising clock edges.",
                "- Do not change the DUT algorithm for this failure until the testbench window is valid again.",
            ])
        if fnum("bad_ptr_rows") > 0.0:
            lines.extend([
                "- Root cause: the observed `ptr_*` columns are not one-hot at the checker-visible pointer index.",
                "- Execute: initialize `ptr_q` from the public task contract; on each valid clock, decode `code_q`, compute the next pointer once, clear all `ptr_val`, then set only `ptr_val[ptr_q] = vdd`.",
                "- Also verify bit order: a correct internal pointer can still fail if `ptr_o[15:0]` is connected or driven reversed relative to checker columns `ptr_15..ptr_0`.",
            ])
        if fnum("bad_count_rows") > 0.0:
            lines.extend([
                "- Root cause: active `cell_en_*` count does not equal decoded `code_q`.",
                "- Execute: after computing the active window, clear all `cell_en_val`; for `j=0..code_q-1`, enable exactly one unique cell index per `j` modulo 16.",
                "- Do not let pointer bit order and cell-enable bit order use opposite conventions.",
            ])
        if fnum("wrap_events") < 2.0 or fnum("split_wrap_rows") < 2.0:
            lines.extend([
                "- Root cause: the stimulus/selection does not visibly split across the 15-to-0 boundary often enough.",
                "- Execute: keep code stimulus values large enough to force at least two wraps from initial pointer 13, and make the enabled window split across indices near 15 and 0.",
            ])
        elif fnum("bad_ptr_rows") > 0.0 or fnum("bad_count_rows") > 0.0:
            lines.extend([
                "- Important: `wrap_events` and `split_wrap_rows` are already sufficient, so preserve the wrap-producing stimulus/window coverage.",
                "- Focus only on making the pointer one-hot and the enabled-cell count equal to `code_q` in the existing sampled cycles.",
            ])
        lines.extend([
            "- Success target for next EVAS run: `bad_ptr_rows=0`, `bad_count_rows=0`, `wrap_events>=2`, and `split_wrap_rows>=2`.",
        ])

    lines.extend([
        "",
        "## Execution Guardrail",
        "",
        "Before outputting code, mentally check the next EVAS note you want to see. If the task still fails, it should fail on a smaller behavior gap, not on compile, missing CSV columns, or unchanged DWA metrics.",
    ])
    return lines


def _implementation_safety_skeleton_section(task_dir: Path, evas_result: dict, sample_dir: Path | None) -> list[str]:
    """Inject syntax-safe implementation skeletons selected from functional IR.

    System relation cards explain what behavior should hold. This section adds
    the implementation pattern needed to make that behavior Spectre-safe before
    the model starts tuning metrics.
    """
    task_id = task_dir.name
    status = str(evas_result.get("status", ""))
    notes = evas_result.get("evas_notes") or evas_result.get("notes") or []
    spectre_notes = evas_result.get("spectre_notes", [])
    notes = notes + [n for n in spectre_notes if n not in notes]
    joined = "\n".join(str(note) for note in notes)
    lowered = joined.lower()
    tokens = _contract_mechanism_tokens(task_dir, notes)

    syntax_markers = {
        "dynamic_analog_vector_index",
        "conditional_transition",
        "conditional_cross",
        "genvar_inside_analog",
        "digital_verilog_syntax",
        "packed_bit_select",
    }
    has_syntax_marker = any(marker in lowered for marker in syntax_markers) or "transition() contribution is inside" in lowered
    has_duplicate_source = "duplicate_vsource_branch" in lowered
    has_timeout = "evas_timeout" in lowered

    is_dwa = bool({"onehot_no_overlap", "rotating_selection_window", "dwa-pointer-thermometer-mask", "dwa_pointer_window"} & tokens)
    is_pll = bool({"pll_clock_ratio_lock", "pll-dco-counter-feedback-loop", "ratio_edge_window", "ratio_hop_window"} & tokens)
    is_pulse = bool({"pulse_or_edge_protocol", "pfd-latched-pulse-delayed-clear", "bbpd-data-clock-lead-lag", "paired_edge_response", "bbpd_data_clock_lead_lag"} & tokens)
    is_adc_dac = bool({"adc_dac_code_or_output_coverage", "quantized_reconstruction", "monotonic_code_vs_input", "differential_code_response", "sar_sequence"} & tokens)
    is_serializer = bool({"sequence_frame_or_pulse_generation", "sequence-frame-alignment", "sequence_alignment", "frame_aligned_serial_sequence"} & tokens)

    if not (
        status in {"FAIL_DUT_COMPILE", "FAIL_TB_COMPILE", "FAIL_INFRA"}
        or has_syntax_marker
        or has_duplicate_source
        or has_timeout
        or is_dwa
        or is_pll
        or is_pulse
        or is_adc_dac
        or is_serializer
    ):
        return []

    lines = [
        "",
        "# Implementation-Safe Repair Skeleton",
        "",
        "Use this section before applying the mechanism card. The goal is to satisfy Spectre/EVAS syntax and artifact constraints while preserving the intended behavior relation.",
        "",
        "Repair order:",
        "1. If the current failure is compile, TB compile, timeout, missing CSV, or strict-preflight, fix that implementation layer first.",
        "2. Preserve module names, port order, filenames, `ahdl_include`, save columns, and fixed `tran` settings unless the EVAS note names that layer.",
        "3. After syntax/artifact safety is restored, apply the behavior mechanism card to reduce the metric gap.",
        "4. The next failure should move downward: compile/TB/infra -> runnable behavior metrics -> smaller metric gap.",
    ]

    if has_syntax_marker or status == "FAIL_DUT_COMPILE":
        lines.extend([
            "",
            "## Spectre-safe Verilog-A construction rules",
            "",
            "- Keep all `integer`, `real`, `parameter`, and `genvar` declarations at module scope before `analog begin`.",
            "- Use `integer`/`real` state variables for logic; do not use `reg`, `wire`, `logic`, `always`, or packed integer bit assignments.",
            "- Put `@(cross(...))` and `@(timer(...))` event statements at the top level of the analog block; put reset/enable decisions inside the event body.",
            "- Compute output target variables inside events or combinational assignments, then drive each electrical output with one unconditional `transition()` contribution.",
            "- Do not place `transition()` inside `if`, `else`, `case`, or loop branches whose execution can skip the contribution.",
            "- For multiple transition-driven outputs, use the generic target-buffer pattern: declare one `real` target per output, or a `real target[0:N-1]` array; update only those targets inside events/conditions; put every `V(out) <+ transition(target, ...)` contribution at analog top level.",
            "- If using an output target array, the contribution loop must use a module-scope `genvar`, not an `integer` runtime loop variable. If unsure, explicitly unroll each output contribution.",
            "- Do not read or write electrical buses using runtime integer indices inside `V(...)`; use fixed-index reads or module-scope `genvar` contribution loops.",
        ])

    if is_dwa:
        lines.extend([
            "",
            "## Spectre-safe DWA bus/state skeleton",
            "",
            "- If EVAS already reported `dynamic_analog_vector_index`, the next repair must explicitly unroll every offending bus access. Do not try another runtime `for (i=...) V(bus[i])` pattern.",
            "- Use fixed scalar reads for the command code. Example for a 4-bit input bus:",
            "  - `code_q = 0; if (V(code_i[0]) > vth) code_q = code_q + 1; if (V(code_i[1]) > vth) code_q = code_q + 2; if (V(code_i[2]) > vth) code_q = code_q + 4; if (V(code_i[3]) > vth) code_q = code_q + 8;`",
            "- Keep one `integer ptr_q` and one `integer code_q`; they are the source of truth for both pointer and cell-enable outputs.",
            "- Keep `real ptr_val[0:15]` and `real cell_en_val[0:15]` as held target arrays.",
            "- On reset or clock edge, clear all 16 target entries first, then set the selected pointer bit and selected cell-enable window.",
            "- For the first repair after a dynamic-index failure, prefer explicit unrolled output contributions over a loop:",
            "  - `V(ptr_o[0]) <+ transition(ptr_val[0], 0, tr, tf);`",
            "  - `V(ptr_o[1]) <+ transition(ptr_val[1], 0, tr, tf);`",
            "  - continue the same pattern through index 15 for both `ptr_o` and `cell_en_o`.",
            "- A module-scope `genvar k` contribution loop is acceptable only after the compile layer is already clean:",
            "  - `genvar k; analog begin ... for (k=0; k<16; k=k+1) begin V(ptr_o[k]) <+ transition(ptr_val[k], 0, tr, tf); V(cell_en_o[k]) <+ transition(cell_en_val[k], 0, tr, tf); end end`",
            "- Never write `V(code_i[i])`, `V(ptr_o[i])`, or `V(cell_en_o[i])` with `i` declared as `integer`.",
            "- For no-overlap DWA, choose the next window start so the new selected set is disjoint from the previous selected set.",
            "- For wraparound DWA, preserve modulo-16 selection and allow split windows across index 15 to 0.",
        ])

    if is_pll:
        lines.extend([
            "",
            "## Spectre-safe PLL timer/divider skeleton",
            "",
            "- Use one held oscillator or DCO state and one strictly future `t_next` timer; each timer event must schedule the next future event.",
            "- Derive `fb_clk` from DCO/divider state instead of creating an unrelated feedback timer.",
            "- Keep divider counters as `integer` state and toggle feedback from counter terminal count.",
            "- Drive `dco_clk`, `fb_clk`, `vctrl_mon`, and `lock` from held real targets with unconditional contributions.",
            "- If `late_edge_ratio` is wrong but clocks are alive, tune divider cadence before lock thresholds.",
            "- If `lock_time=nan`, do not force lock high; first make the late-window ratio stable, then assert lock from a stability counter.",
        ])

    if is_pulse:
        lines.extend([
            "",
            "## Spectre-safe PFD/BBPD pulse skeleton",
            "",
            "- Keep last-edge times or independent latch states for the two input edge streams.",
            "- On the leading side, assert the corresponding held UP/DN target; clear it with a finite timer or trailing-edge clear.",
            "- Use finite pulse widths that the checker can sample; avoid picosecond-only pulses unless the prompt requires them.",
            "- Drive UP and DN from held targets with unconditional `transition()` contributions.",
            "- For lead/lag tasks, the data/reference input is an edge stream, not a static Boolean level.",
        ])

    if is_adc_dac:
        lines.extend([
            "",
            "## Spectre-safe ADC/DAC code-output skeleton",
            "",
            "- Use one held integer code or trial code as the source of truth for all public output bits and analog reconstruction targets.",
            "- Decode electrical input bits with fixed-index threshold reads; avoid integer bit-slice syntax.",
            "- For code coverage failures, update the code on the specified clock/sample event and drive every bit from that code.",
            "- For output-span failures with code coverage present, preserve the code path and repair only the code-to-analog target calculation.",
            "- For differential outputs, compute one differential value and drive positive/negative targets around common mode with opposite polarity.",
            "- For timeout failures, reduce unnecessary internal timers/save traffic and avoid ultra-small transition times or maxstep pressure.",
        ])

    if is_serializer:
        lines.extend([
            "",
            "## Spectre-safe serializer state skeleton",
            "",
            "- Keep one held shift register and one bit index.",
            "- Load the parallel word only on the specified load event; then shift exactly one bit per valid clock edge.",
            "- Drive `sout` from the current bit and `frame` high only for the first serialized bit.",
            "- Drive output targets continuously with unconditional `transition()` contributions.",
        ])

    if has_duplicate_source or status == "FAIL_TB_COMPILE":
        lines.extend([
            "",
            "## Spectre-safe testbench single-driver skeleton",
            "",
            "- Each electrical branch must have one stimulus source. Do not drive the same node with both a base clock and a step/PWL source.",
            "- To model a frequency or phase step, replace the original source with one PWL/pulse schedule or generate the step inside the DUT monitor logic; do not add a second source on the same node.",
            "- Keep one canonical `save` list with plain scalar names only.",
            "- Keep `ahdl_include` filenames consistent with the generated module filenames.",
        ])

    if has_timeout:
        facts = _clock_reset_timing_facts(sample_dir)
        lines.extend([
            "",
            "## Timeout-safe simulation skeleton",
            "",
            "- Treat timeout as an implementation/runtime failure before behavior tuning.",
            "- Avoid ultra-small transition times, unbounded free-running timers, and excessive saved internal nodes.",
            "- Keep only checker-required public observables in the save list when possible.",
            "- Preserve the fixed public `tran` stop/maxstep unless EVAS says the tran line itself is invalid.",
        ])
        if facts.get("tran_lines"):
            lines.append("- Current tran line(s): `" + " | ".join(facts["tran_lines"]) + "`")

    return lines


def _format_scalar(value: float | bool | str) -> str:
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, (int, float)):
        return f"{float(value):.4g}"
    return str(value)


def _checker_expectation_bundle(task_dir: Path) -> dict:
    meta = read_meta(task_dir)
    task_id = meta.get("task_id", meta.get("id", task_dir.name))
    checker_name = get_checker_name_for_task(task_id)
    extracted = extract_expected_values(checker_name)
    if extracted.get("error"):
        return {
            "task_id": task_id,
            "checker_name": checker_name,
            "expected_conditions": {},
            "semantic_hints": [],
            "metric_aliases": metric_aliases_for_task(task_id),
        }
    return {
        "task_id": task_id,
        "checker_name": checker_name,
        "expected_conditions": extracted.get("expected_conditions", {}),
        "semantic_hints": extracted.get("semantic_hints", []),
        "formatted_lines": format_expected_for_prompt(extracted),
        "metric_aliases": metric_aliases_for_task(task_id),
    }


def _normalized_metric_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", name.lower())


def _observed_numeric_metrics(metrics: dict[str, float | bool | str]) -> dict[str, float]:
    ignored = {
        "returncode",
        "generated_include",
        "input_tokens",
        "output_tokens",
    }
    observed: dict[str, float] = {}
    for key, value in metrics.items():
        if key in ignored:
            continue
        if isinstance(value, bool):
            continue
        if isinstance(value, (int, float)):
            observed[key] = float(value)
    return observed


def _metric_candidate_keys(
    metric_name: str,
    metrics: dict[str, float | bool | str],
    metric_aliases: dict[str, list[str]],
) -> list[str]:
    candidates: list[str] = [metric_name]
    if metric_name in metric_aliases:
        candidates.extend(metric_aliases[metric_name])

    # Name-based fallback aliases for common conventions.
    if metric_name.endswith("_ns"):
        candidates.append(metric_name[:-3])
    if "ratio" in metric_name:
        candidates.append("freq_ratio")
    if metric_name.startswith("pre_") or metric_name.startswith("post_"):
        suffix = metric_name.split("_", 1)[1]
        candidates.append(suffix)

    norm_to_key: dict[str, str] = {}
    for key in metrics:
        norm_to_key.setdefault(_normalized_metric_name(key), key)

    resolved: list[str] = []
    seen = set()
    for cand in candidates:
        for key in (cand, norm_to_key.get(_normalized_metric_name(cand), "")):
            if key and key in metrics and key not in seen:
                resolved.append(key)
                seen.add(key)
    return resolved


def _threshold_spec(spec: str) -> tuple[str, float] | None:
    match = re.match(r"^(>=|<=|>|<)\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?)$", spec.strip(), re.IGNORECASE)
    if not match:
        return None
    try:
        return match.group(1), float(match.group(2))
    except ValueError:
        return None


def _metric_gap_line(name: str, actual: float | bool | str, spec: dict) -> tuple[bool, str] | None:
    if not isinstance(actual, (int, float)):
        return None
    actual_value = float(actual)
    target = spec.get("expected")
    tolerance = spec.get("tolerance")
    if isinstance(target, (int, float)) and isinstance(tolerance, (int, float)):
        target_value = float(target)
        tolerance_value = float(tolerance)
        deviation = abs(actual_value - target_value)
        ok = deviation <= tolerance_value
        detail = (
            f"`{name}` expected {target_value:.4g} +/- {tolerance_value:.4g}, "
            f"actual {actual_value:.4g} -> {'OK' if ok else f'ERROR (off by {deviation:.4g})'}"
        )
        return ok, detail
    if isinstance(target, str):
        parsed = _threshold_spec(target)
        if not parsed:
            return None
        op, threshold = parsed
        if op == ">=":
            ok = actual_value >= threshold
        elif op == "<=":
            ok = actual_value <= threshold
        elif op == ">":
            ok = actual_value > threshold
        else:
            ok = actual_value < threshold
        gap = abs(actual_value - threshold)
        detail = (
            f"`{name}` expected {target}, actual {actual_value:.4g} -> "
            f"{'OK' if ok else f'ERROR (gap {gap:.4g})'}"
        )
        return ok, detail
    return None


def _numeric_metric_gap(actual: float, spec: dict) -> float | None:
    target = spec.get("expected")
    tolerance = spec.get("tolerance")
    if isinstance(target, (int, float)) and isinstance(tolerance, (int, float)):
        raw = max(0.0, abs(actual - float(target)) - float(tolerance))
        return raw / max(abs(float(target)), abs(float(tolerance)), 1.0)
    if isinstance(target, str):
        parsed = _threshold_spec(target)
        if not parsed:
            return None
        op, threshold = parsed
        threshold = float(threshold)
        if op in (">=", ">"):
            raw = max(0.0, threshold - actual)
        else:
            raw = max(0.0, actual - threshold)
        return raw / max(abs(threshold), 1.0)
    return None


def metric_gap_summary(task_dir: Path, evas_result: dict) -> dict:
    """Return a compact checker-metric closeness score for loop selection.

    This is intentionally separate from PASS/FAIL scoring: many hard tasks sit
    at weighted_total=0.6667, so the repair loop needs a finer tie-breaker.
    """
    bundle = _checker_expectation_bundle(task_dir)
    expected_conditions = bundle.get("expected_conditions", {})
    aliases = bundle.get("metric_aliases", {})
    metrics = _extract_metrics_from_notes(evas_result.get("evas_notes", []))

    matched = 0
    violated = 0
    gap_sum = 0.0
    details: list[str] = []

    for metric_name, spec in expected_conditions.items():
        for observed_key in _metric_candidate_keys(metric_name, metrics, aliases):
            value = metrics.get(observed_key)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                continue
            gap = _numeric_metric_gap(float(value), spec)
            if gap is None:
                continue
            matched += 1
            gap_sum += gap
            if gap > 0.0:
                violated += 1
                alias = f" as {observed_key}" if observed_key != metric_name else ""
                details.append(f"{metric_name}{alias}: gap={gap:.4g}")
            break

    return {
        "matched": matched,
        "violated": violated,
        "gap_sum": round(gap_sum, 6),
        "details": details[:6],
    }


def _expected_vs_actual_lines(
    metrics: dict[str, float | bool | str],
    expected_conditions: dict,
    metric_aliases: dict[str, list[str]],
) -> tuple[list[str], list[str], list[str]]:
    already_good: list[str] = []
    remaining_gaps: list[str] = []
    matched_observed_keys: set[str] = set()

    for metric_name, spec in expected_conditions.items():
        candidate_keys = _metric_candidate_keys(metric_name, metrics, metric_aliases)
        if not candidate_keys:
            continue
        for observed_key in candidate_keys:
            comparison = _metric_gap_line(metric_name, metrics[observed_key], spec)
            if comparison is None:
                continue
            ok, detail = comparison
            matched_observed_keys.add(observed_key)
            if observed_key != metric_name:
                detail = f"{detail} (observed as `{observed_key}`)"
            if ok:
                already_good.append(f"- {detail}")
            else:
                remaining_gaps.append(f"- {detail}")
            break

    unmatched_numeric: list[str] = []
    observed_numeric = _observed_numeric_metrics(metrics)
    for key in sorted(observed_numeric):
        if key not in matched_observed_keys:
            unmatched_numeric.append(f"- `{key}={_format_scalar(observed_numeric[key])}`")
    return already_good, remaining_gaps, unmatched_numeric


def _loop_state_section(
    task_dir: Path,
    evas_result: dict,
    history: list[dict],
    loop_context: dict | None,
) -> str:
    if not history and not loop_context:
        return ""

    bundle = _checker_expectation_bundle(task_dir)
    metrics = _extract_metrics_from_notes(evas_result.get("evas_notes", []))
    expected_conditions = bundle.get("expected_conditions", {})
    metric_aliases = bundle.get("metric_aliases", {})
    already_good, remaining_gaps, unmatched_numeric = _expected_vs_actual_lines(
        metrics,
        expected_conditions,
        metric_aliases,
    )

    lines = ["# EVAS Loop State", ""]
    if loop_context:
        anchor = loop_context.get("repair_from_label", "baseline")
        best_status = loop_context.get("best_status", "<unknown>")
        best_scores = loop_context.get("best_scores", {})
        lines.append(
            f"- Start this round from the best-so-far candidate: `{anchor}` "
            f"(status={best_status}, weighted_total={float(best_scores.get('weighted_total', 0.0)):.3f})."
        )
        best_gap = loop_context.get("best_metric_gap") or {}
        if best_gap:
            lines.append(
                "- Best-so-far closeness: "
                f"matched_metrics={best_gap.get('matched', 0)}, "
                f"violated_metrics={best_gap.get('violated', 0)}, "
                f"gap_sum={float(best_gap.get('gap_sum', 0.0)):.4g}, "
                f"failure_subtype={loop_context.get('best_failure_subtype', '<unknown>')}."
            )
        last_transition = loop_context.get("last_transition_summary")
        if last_transition:
            lines.append(f"- Last loop diagnosis: {last_transition}")

        transition_policy = loop_context.get("last_transition")
        if transition_policy == "regressed":
            lines.extend([
                "- Policy for this round: continue from the best-so-far candidate, not from the latest regressed edit.",
                "- Preserve the EVAS behaviors that were already working before the regression.",
            ])
        elif transition_policy == "stalled":
            lines.extend([
                "- Policy for this round: the previous edit did not move EVAS; use a different repair mechanism.",
                "- Avoid cosmetic rewrites that preserve the same failing measurements.",
            ])
        elif transition_policy == "oscillating":
            lines.extend([
                "- Policy for this round: stop toggling interface/testbench details.",
                "- Keep the working file contract fixed and repair the remaining semantic bug from the best-so-far candidate.",
            ])
        elif transition_policy == "improved":
            lines.extend([
                "- Policy for this round: preserve the behavior that improved in the best-so-far candidate.",
                "- Change only the remaining failing logic exposed by EVAS.",
            ])

    if bundle.get("formatted_lines"):
        lines.extend(["", "# Checker Targets"])
        lines.extend(bundle["formatted_lines"])

    if already_good:
        lines.extend(["", "Metrics already consistent with the checker:"])
        lines.extend(already_good[:5])
        lines.append("- Do NOT modify the logic responsible for the metrics above unless EVAS proves they regressed.")

    if remaining_gaps:
        lines.extend(["", "Metrics still failing against the checker:"])
        lines.extend(remaining_gaps[:6])
        lines.append("- Focus the next edit on the failing metrics above; treat them as the EVAS optimization target.")
    elif unmatched_numeric:
        lines.extend(["", "Observed EVAS metrics (no direct checker-target mapping found):"])
        lines.extend(unmatched_numeric[:6])
        lines.append("- Use the metrics above as secondary targets; prioritize contract/alignment fixes first.")

    semantic_hints = bundle.get("semantic_hints", [])
    if semantic_hints and not remaining_gaps:
        lines.extend(["", "Checker hints still relevant for this repair:"])
        for hint in semantic_hints[:4]:
            lines.append(f"- {hint}")

    return "\n".join(lines)


def _classify_sim_correct_failure(notes: list[str], task_id: str) -> tuple[str, list[str]]:
    """Route FAIL_SIM_CORRECTNESS into semantic/contract/artifact subtypes."""
    subtype_order = ("simulation_artifact", "observability_contract", "behavior_semantic")
    counts = {k: 0 for k in subtype_order}
    exemplars: dict[str, list[str]] = {k: [] for k in subtype_order}
    for note in notes:
        translation = translate_diagnosis(note, task_id)
        subtype = translation.get("failure_type")
        if subtype not in counts:
            continue
        counts[subtype] += 1
        if len(exemplars[subtype]) < 2:
            exemplars[subtype].append(note)
    for subtype in subtype_order:
        if counts[subtype] > 0:
            return subtype, exemplars[subtype]
    return "behavior_semantic", []


def _primary_diagnosis(notes: list[str], task_id: str) -> dict:
    for note in notes:
        translation = translate_diagnosis(note, task_id)
        if translation.get("diagnosis"):
            return translation
    return {}


def _repair_policy_contract(task_id: str, notes: list[str], sim_subtype: str) -> list[str]:
    diagnosis = _primary_diagnosis(notes, task_id)
    rule = diagnosis.get("matched_rule", "")
    task_lower = _task_id_text_for_matching(task_id)

    lines = [
        "",
        "Repair policy v1 (mandatory):",
        "- Treat this as a conservative patch, not a fresh design.",
        "- Keep module names, port names/order, parameters, testbench stimulus, tran setup, and save names unchanged unless the failure is explicitly an observability/TB contract issue.",
        "- Output complete replacement code blocks, but internally make the smallest behavioral edit needed.",
        "- Before changing DUT behavior, preserve all parts that already compile and all metrics that EVAS reports as good.",
        "- Do not introduce a new architecture, new clocking scheme, or new signal naming convention to fix one metric.",
    ]

    if sim_subtype == "observability_contract":
        lines.extend([
            "",
            "Hard contract for OBSERVABILITY_CONTRACT:",
            "- Modify the testbench/save/export naming first; keep the DUT behavior byte-for-byte equivalent when possible.",
            "- Use plain scalar save names exactly as requested by the task/checker.",
            "- If a bus is used, expose each bit as the checker-visible scalar name.",
            "- Do not tune thresholds or state machines until the waveform columns are correct.",
        ])
    elif rule == "SERIALIZER_BIT_ORDER" or "serializer" in task_lower:
        lines.extend([
            "",
            "Hard contract for serializer repair:",
            "- Modify only load/shift direction, bit counter reset, or frame-boundary timing.",
            "- Decide whether the mismatch is MSB/LSB order or a one-cycle shift; do not rewrite unrelated stimulus.",
            "- The first sampled serial bit after frame start must correspond to the first expected bit.",
            "- For LOAD-framed serializers, LOAD should latch the parallel word and mark a pending frame; the first post-LOAD CLK should output the first bit, not the second bit.",
            "- Keep clock, reset, frame marker, and save names unchanged.",
        ])
    elif rule in {"CLOCK_DIVIDER_RATIO", "MULTIMOD_DIVIDER_COUNTS", "CLOCK_BURST"} or "divider" in task_lower:
        lines.extend([
            "",
            "Hard contract for clock/divider repair:",
            "- Modify only terminal-count, toggle, ratio-code decode, or lock/burst counter logic.",
            "- Use explicit integer counters updated once per clock crossing.",
            "- Do not change the observable clock/testbench names; the checker measures edge counts and intervals.",
            "- Avoid static lock assertions unless the measured period/count condition is satisfied.",
        ])
    elif rule in {"PFD_RESET_RACE", "BBPD_EDGE_ALIGNMENT"} or "pfd" in task_lower or "bbpd" in task_lower:
        lines.extend([
            "",
            "Hard contract for PFD/BBPD repair:",
            "- Modify only edge-order detection, UP/DN pulse generation, reset, and non-overlap logic.",
            "- Latch which edge arrived first, emit the matching finite pulse, then reset both outputs.",
            "- Keep UP/DN pulses local to the checker measurement window and avoid overlapping high states.",
            "- Do not alter testbench stimulus timing unless EVAS reports a missing/invalid waveform.",
        ])
    elif rule in {"PLL_FREQ_RATIO", "ADPLL_EDGE_RATIO", "PLL_RATIO_HOP"} or "pll" in task_lower:
        lines.extend([
            "",
            "Hard contract for PLL/ADPLL repair:",
            "- Modify only divider ratio, edge generation cadence, DCO/control update, or lock criteria.",
            "- Lock must be derived from stable measured behavior, not asserted by a fixed delay alone.",
            "- Keep reference/feedback/output observable names and simulation window unchanged.",
            "- For ratio-hop tasks, implement explicit pre-hop and post-hop ratio states.",
        ])
    elif rule in {"ADC_DAC_CODE_COVERAGE", "DAC_LEVEL_COVERAGE", "THERM_DAC_COUNT"} or any(k in task_lower for k in ("adc", "dac")):
        lines.extend([
            "",
            "Hard contract for ADC/DAC repair:",
            "- Modify only quantization thresholds, code mapping, bit decoding, or DAC weight/count logic.",
            "- Preserve input stimulus and save names; the checker relies on waveform coverage.",
            "- Clamp only at valid boundaries and keep the linear/monotonic region active.",
            "- If outputs are bits, drive every bit from the same integer code state.",
            "- For clocked ADC smoke tests, the public requirement is observable conversion samples: a pulse-style clock must produce enough rising edges inside the fixed `tran` window.",
            "- For ADC-to-DAC round-trip tasks, keep one code state as the source of truth: sampled input -> integer code -> output bits -> DAC output.",
            "- Prefer direct per-sample quantization when the checker measures code coverage, span, and round-trip error rather than internal SAR bit-cycle traces.",
            "- Use Verilog-A math function `floor(...)`, not digital/SystemVerilog-style `$floor(...)`; `$floor` can compile in some flows but produce non-portable behavior.",
            "- Declare temporary `real` and `integer` variables at module scope, not inside an event block.",
        ])
    elif rule == "GRAY_PROPERTY" or "gray" in task_lower:
        lines.extend([
            "",
            "Hard contract for Gray-code repair:",
            "- Keep a binary state internally and derive Gray output as binary ^ (binary >> 1).",
            "- Update the state exactly once per valid clock edge.",
            "- Do not independently toggle output bits.",
        ])
    elif rule == "SAMPLE_HOLD_DROOP" or "sample_hold" in task_lower:
        lines.extend([
            "",
            "Hard contract for sample-hold droop repair:",
            "- Modify only sampling aperture, hold state, and droop update logic.",
            "- On the intended sample edge, capture `vin` into one held state variable and immediately drive `vout` toward that sampled value.",
            "- During hold windows, do not track `vin`; update `vout` monotonically downward from the held value.",
            "- Use a small timer-based or state-based droop update so hold windows contain enough smooth samples.",
            "- Preserve `vin`, `clk`, `vout`, supply names, and transient/save setup.",
        ])

    return lines


def _subtype_specific_repair_policy(task_id: str, notes: list[str], status: str) -> list[str]:
    """Inject high-precision repair policies selected by concrete EVAS notes.

    These are deliberately narrower than the generic diagnosis text.  They turn
    repeated EVAS failure subtypes into bounded edit recipes so the model does
    not respond to every failure by rewriting the whole circuit.
    """
    task_lower = _task_id_text_for_matching(task_id)
    joined = "\n".join(str(note) for note in notes)
    lowered = joined.lower()
    lines: list[str] = []

    def add_header(title: str) -> None:
        if not lines:
            lines.extend(["", "# P1 Subtype-Specific Repair Policy", ""])
        lines.extend([f"## {title}", ""])

    if "dynamic_analog_vector_index=" in joined:
        add_header("Compile: dynamic analog vector indexing")
        lines.extend([
            "- This is a compile-layer bug, not a behavior bug. Do not tune algorithm constants until this is gone.",
            "- No expression inside `V(...)` may contain an `integer` loop variable such as `i` or `j`.",
            "- For input buses, decode with fixed reads only: `V(code_i[0])`, `V(code_i[1])`, ...",
            "- For output buses, store targets in real arrays such as `ptr_val[0:15]` and `cell_en_val[0:15]`.",
            "- For this repair round, explicitly unroll all offending reads and output contributions instead of using another runtime loop.",
            "- Write `V(out[0]) <+ transition(target[0], ...)`, `V(out[1]) <+ transition(target[1], ...)`, and so on through every required bit.",
            "- A module-scope `genvar k` contribution loop can be used in future cleanup, but the safest next fix after this EVAS note is full static unroll.",
            "- Do not output any line matching `V(<bus>[i])` or `V(<bus>[j])` when `i`/`j` is an `integer`.",
            "",
        ])

    if "conditional_cross=" in joined:
        add_header("Compile: conditional cross event")
        lines.extend([
            "- Move every `@(cross(...))` statement to the top level of `analog begin`.",
            "- Put reset, enable, and mode checks inside the event body.",
            "- Wrong shape: `if (enabled) @(cross(V(clk)-vth,+1)) begin ... end`.",
            "- Correct shape: `@(cross(V(clk)-vth,+1)) begin if (enabled) begin ... end end`.",
            "",
        ])

    if "conditional_transition=" in joined:
        add_header("Compile: conditional transition contribution")
        lines.extend([
            "- Make `transition()` contributions unconditional.",
            "- Compute a real/integer target in conditional logic, then drive the output once outside the conditional block.",
            "- Correct shape: `target = cond ? vh : vl; V(out) <+ transition(target, 0, tr, tf);`.",
            "",
        ])

    if "digital_verilog_syntax" in joined or "packed_bit_select" in joined:
        add_header("Compile: digital-Verilog syntax leakage")
        lines.extend([
            "- Do not use `reg`, `wire`, `logic`, `always`, `initial begin`, or packed bit assignments on integers.",
            "- Replace state vectors with integer state variables and explicit arithmetic.",
            "- Decode electrical buses with fixed threshold tests and integer additions.",
            "- Example: `code=0; if (V(dout[0])>vth) code=code+1; if (V(dout[1])>vth) code=code+2;`.",
            "",
        ])

    if "missing dout_code or dout_3..0" in lowered:
        add_header("Observable: ADC/DAC output code columns")
        lines.extend([
            "- This is an observable contract failure. Keep the ADC/DAC behavior and fix the testbench/export layer first.",
            "- The checker accepts either one scalar `dout_code` column or all four scalar columns `dout_3 dout_2 dout_1 dout_0`.",
            "- Prefer exposing all four bit columns because it is simulator-stable.",
            "- Use scalar node aliases in the testbench: connect ADC bus bits to nodes named `dout_3`, `dout_2`, `dout_1`, `dout_0`.",
            "- Save exactly these public names along with `vin`, `vout`, and `rst_n`: `save vin vout rst_n dout_3 dout_2 dout_1 dout_0`.",
            "- Do not rely on CSV headers such as `dout[3]`, hierarchical names, or instance-qualified names.",
            "",
        ])

    if re.search(r"missing .*ptr_0", lowered) or re.search(r"missing .*cell_en_0", lowered):
        add_header("Observable: DWA scalar CSV columns")
        lines.extend([
            "- This is an observable contract failure. Preserve current DWA DUT behavior if it compiles.",
            "- The checker needs plain scalar columns: `time`, `clk_i`, `rst_ni`, `ptr_0..ptr_15`, and `cell_en_0..cell_en_15`.",
            "- If the DUT uses vector ports, wire each bit to scalar testbench nodes with those exact names.",
            "- Save the scalar node names directly; do not save `ptr_o[0]`, `cell_en_o[0]`, or instance-qualified names.",
            "- Keep reset deasserted early enough and include several post-reset clock edges in the transient window.",
            "",
        ])

    if "missing dout_0..7" in lowered:
        add_header("Observable: SAR output code columns")
        lines.extend([
            "- The checker needs eight scalar output bit columns: `dout_0` through `dout_7`.",
            "- Wire or alias DUT output bits to scalar testbench nodes with exactly those names.",
            "- Save `vin`, `vin_sh`, `vout`, `rst_n`, and all `dout_0..dout_7` columns.",
            "- Do not rely on vector CSV headers or hierarchical bit names.",
            "",
        ])

    if "only_" in lowered and "codes" in lowered and ("flash_adc" in task_lower or "adc" in task_lower or "sar" in task_lower):
        add_header("Behavior: ADC/SAR code coverage")
        lines.extend([
            "- The circuit compiles, but the checker sees too few distinct output codes. Fix conversion behavior, not syntax.",
            "- Ensure the input ramp spans the active conversion range after reset and while clocks are present.",
            "- Decode/drive every output bit from one integer `code` state; do not leave high bits stuck at zero.",
            "- Use monotonic quantization: `code = floor((vin-vmin)/vstep)` clipped only at valid boundaries.",
            "- For flash ADC, implement seven ordered thresholds and produce all 8 binary codes over the ramp.",
            "- For SAR/ADC-DAC, the DAC output must change with the converted code; `vout_span=0` means the code/DAC path is stuck.",
            "",
        ])

    if "flash_adc" in task_lower and ("only_" in lowered and "codes" in lowered):
        add_header("Behavior: flash ADC threshold ladder")
        lines.extend([
            "- The harness now produces clock edges; repair the DUT quantizer and bit-drive path.",
            "- Use explicit threshold comparisons, or use `floor(...)` without the `$` prefix; avoid `$floor(...)` because it is not portable in this Verilog-A flow.",
            "- Start with `code = 0`, then increment or assign code from seven ordered thresholds at `vrefn + k*(vrefp-vrefn)/8` for k=1..7.",
            "- Update `code` only on `@(cross(V(clk)-vth,+1))`, and initialize output target variables in `@(initial_step)`.",
            "- Keep all temporary variables such as sampled input, bit flags, and next code declared at module scope.",
            "- Drive `dout2`, `dout1`, and `dout0` continuously from target variables using unconditional `transition()` contributions.",
            "- Verify bit order: `dout2` is MSB, `dout1` middle, `dout0` LSB.",
            "- Preserve the repaired pulse-clock/ramp testbench from the previous layer.",
            "",
        ])

    if "unique_codes=" in lowered and ("adc" in task_lower or "dac" in task_lower or "sar" in task_lower):
        add_header("Behavior: unique code span")
        lines.extend([
            "- Repair the code-generation path so EVAS observes many distinct codes, not just a compile-clean waveform.",
            "- Check reset release: code should remain reset only while `rst_n` is low, then update on clock/sample events.",
            "- Check stimulus coupling: converted `vin` or `vin_sh` must feed the quantizer, and quantizer code must feed DAC/output bits.",
            "- Keep output voltage monotonic and spanning most of the supply range.",
            "",
        ])

    if "flash_adc" in task_lower and any(key in lowered for key in ("too_few_edges=", "no_clock_edges", "only_0_edges")):
        add_header("Observable/Stimulus: flash ADC clock edges")
        lines.extend([
            "- The checker already found the public columns, but it did not observe enough rising `clk` crossings.",
            "- Repair the Spectre harness first and preserve the compiling ADC DUT unless the next EVAS note exposes code behavior.",
            "- Use a `type=pulse` clock between 0 V and 0.9 V rather than relying on a sinusoidal source for digital sampling.",
            "- Choose a clock period that gives at least 20 rising edges before the fixed `tran stop`, leaving settling time after each edge.",
            "- Drive `vin` with a monotonic full-scale PWL or ramp covering roughly 0 V to 0.9 V over the same edge window.",
            "- Save exact lowercase scalar names: `save vin clk dout2 dout1 dout0`.",
            "- The next failure, if any, should be `only_N_codes` or `not_monotonic`, not `too_few_edges`.",
            "",
        ])

    if "sar_adc_dac_weighted_8b" in task_lower and any(key in lowered for key in ("tran.csv missing", "returncode=1")):
        add_header("Runtime: SAR/ADC-DAC round-trip harness")
        lines.extend([
            "- Treat `tran.csv missing` with successful preflight as a runtime/harness failure before changing numeric targets.",
            "- Use simple Spectre-safe stimulus and module wiring: one top-level testbench, one `tran`, one canonical save list.",
            "- Do not add `run` or `exit` statements; the runner invokes Spectre and reads the transient output directly.",
            "- Prefer node `0` as ground and `global 0`; avoid custom `global gnd` unless every source and instance consistently uses it.",
            "- Avoid inline comments after `parameters` assignments and avoid line continuations in source definitions unless already proven in the candidate.",
            "- Avoid assigning `cross(...)` to a variable and then using `@(that_variable)`; write event blocks directly as `@(cross(V(clks)-vth,+1)) begin ... end`.",
            "- Keep Verilog-A event statements at top level inside `analog begin`; put reset checks inside the event body.",
            "- For this smoke contract, a direct sampled quantizer is acceptable: on each valid `clks` rising edge after reset, compute the clipped 8-bit code from `vin` or `vin_sh`.",
            "- Use `floor(...)`, not `$floor(...)`, when converting a real voltage into an integer code.",
            "- Drive all `dout_0..dout_7` bits from that one integer code state, with `dout_7` as MSB and `dout_0` as LSB.",
            "- The DAC must decode the same bit order and drive `vout = code / 255 * vdd`; a stuck `vout` means the code-to-DAC path is broken.",
            "- The sample/hold helper should make `vin_sh` track or sample `vin` in the checker-visible window; do not let reset hold it at zero after reset release.",
            "",
        ])

    if "bit_mismatch" in lowered or "serializer" in task_lower:
        add_header("Behavior: serializer bit order")
        lines.extend([
            "- Use the `expected=[...]` sequence reported by EVAS as the public repair target for this run.",
            "- Modify only load/shift order or the one-cycle phase alignment.",
            "- On load active, capture the parallel word once. After load deasserts, present the configured MSB-first or LSB-first order consistently on successive clock edges.",
            "- If EVAS observed the same sequence shifted by one, preload `sout` with the first intended bit at load deassertion before the first post-load clock sample.",
            "- Stronger LOAD/CLK skeleton: on LOAD rising edge, latch `shreg` and set `load_pending=1` but do not shift; on the first CLK rising edge with LOAD low, output `(shreg >> 7) & 1` and clear `load_pending`; only subsequent CLK edges shift left and output the next MSB.",
            "- Do not update `sout` to the second bit before the checker samples the first post-load clock edge.",
            "- Do not alter clock, load waveform, save names, or unrelated output scaling.",
            "",
        ])

    if "up_first=" in lowered or "dn_first=" in lowered or "pfd" in task_lower:
        add_header("Behavior: PFD pulse windows")
        lines.extend([
            "- Preserve compile-clean structure and modify only UP/DN pulse state logic.",
            "- When REF leads DIV, emit a finite UP pulse and no DN pulse in that comparison window.",
            "- When DIV leads REF, emit a finite DN pulse and no UP pulse in that comparison window.",
            "- Reset both outputs after the pulse width expires; do not let UP remain high across multiple windows.",
            "- Use the EVAS fractions as pulse-width diagnostics: if `up_pulses_first` or `dn_pulses_second` is already high enough but the corresponding fraction exceeds the allowed range, shorten pulse width instead of adding more pulses.",
            "- For reset-race smoke, the target is window-local finite pulses: `up_first` and `dn_second` should be visible but not wide, while `dn_first`, `up_second`, and `overlap_frac` stay near zero.",
            "- A robust implementation is edge-latched pulse timers: on REF-leading edge set `up_state=1` and `up_release_t=$abstime+pulse_w`; on DIV-leading edge set `dn_state=1` and `dn_release_t=$abstime+pulse_w`; clear each state when `$abstime` exceeds its release time.",
            "- If EVAS reports `dn_pulses_second=0`, the second-window DIV-leading case is not producing DN pulses; if it reports enough pulses but `dn_second` too large, shorten DN pulse width.",
            "- Do not use ultra-small transition times or free-running timers that force excessive simulator steps.",
            "",
        ])

    if "gray" in task_lower and (status == "FAIL_DUT_COMPILE" or "bad_transitions" in lowered or "missing_gray_codes" in lowered):
        add_header("Compile/Behavior: Gray counter")
        lines.extend([
            "- Use an integer binary counter as the only state variable.",
            "- Derive Gray output from the binary counter: `gray = binary ^ (binary >> 1)`.",
            "- Do not store Gray bits as packed arrays; drive each output bit from fixed arithmetic tests.",
            "- Update the binary counter exactly once per valid rising clock edge after reset.",
            "- Before rewriting a compile-clean Gray DUT, inspect reset/enable stimulus: an active-low reset must stay high after release, and enable must stay active during the checker window.",
            "- A finite `type=pulse val0=0 val1=VDD width=...` on an active-low reset reasserts reset low after `width`; use PWL or a source that holds reset deasserted through `tran stop`.",
            "",
        ])

    if (
        "sample_hold" in task_lower
        and (
            "droop_failures=" in lowered
            or "insufficient_high_hold_windows" in lowered
            or "sample_mismatch=" in lowered
        )
    ):
        add_header("Behavior: sample-hold droop window")
        lines.extend([
            "- The circuit compiles and the checker can observe sample/hold windows. Repair behavior, not the testbench contract.",
            "- Use one sampled state: capture `V(vin)` on each valid rising `clk` edge.",
            "- Drive `vout` to the sampled value shortly after the sample edge so `sample_mismatch` stays low.",
            "- In the hold portion between clock edges, do not read `vin` into `vout`; only evolve the held output state.",
            "- Droop must be monotonic downward in high hold windows; avoid upward steps caused by re-tracking input or recomputing from `$abstime - t_last` in a way that resets during hold.",
            "- Use a small periodic timer update during hold, for example `@(timer(0, dt)) if (V(clk)<vth) out_val = out_val * alpha;`.",
            "- Tune droop magnitude so each high hold window droops visibly but not excessively; EVAS rejects both near-zero droop and huge decay.",
            "- Preserve the verifier harness, scalar save names, and module ports.",
            "",
        ])

    return lines


def _complex_submodule_local_validation_section(task_id: str, notes: list[str]) -> list[str]:
    """Route complex-system failures through contract-defined local checks.

    This is not a request to expose gold internals.  It asks the model to verify
    each public block that the task already requires before rewriting the whole
    integrated system.
    """
    task_lower = _task_id_text_for_matching(task_id)
    joined = "\n".join(str(note) for note in notes).lower()
    if not any(key in task_lower for key in ("adpll", "sar_adc_dac_weighted_8b")):
        return []
    if not any(key in joined for key in ("tran.csv missing", "returncode=1", "late_edge_ratio", "not_enough_edges", "unique_codes", "vout_span", "fb=", "lock_time")):
        return []

    lines = [
        "",
        "# Complex-System Local Validation Skeleton",
        "",
        "- Do not repair a complex system as one opaque rewrite. Decompose only along modules/signals already present in the public task contract.",
        "- Keep exactly one final integrated Spectre testbench; do not output separate standalone mini-testbenches.",
        "- Before outputting code, perform these local checks mentally and make the smallest edit that fixes the first failed local contract.",
    ]

    if "sar_adc_dac_weighted_8b" in task_lower:
        lines.extend([
            "",
            "## SAR ADC/DAC local contracts",
            "",
            "- `sh_ideal`: `vin_sh` must follow or sample `vin` after `rst_n` is high; it must not stay reset/stuck near zero.",
            "- `sar_adc_weighted_8b`: on every valid rising `clks` edge after reset, compute exactly one integer code from `vin` or `vin_sh`, clipped to `[0,255]`.",
            "- `sar_adc_weighted_8b`: drive `dout_7..dout_0` from that one code state; `dout_7` is MSB and `dout_0` is LSB.",
            "- `dac_weighted_8b`: decode the same bit order and drive `vout = code/255*vdd` inside `[0,vdd]`.",
            "- Integrated check: if `tran.csv missing`, repair module interfaces and testbench wiring before changing quantization math.",
            "- Integrated check: if CSV exists but code coverage is low, keep the harness fixed and repair only the sampled-code-to-bit-to-DAC path.",
        ])
    if "adpll" in task_lower:
        lines.extend([
            "",
            "## ADPLL local contracts",
            "",
            "- Reference stimulus: `ref_clk` must provide many visible 50 MHz-class edges over the fixed `tran` window.",
            "- DCO edge generator: `dco_clk` must keep toggling from a timer-driven next-edge state; it must not stall after initialization.",
            "- Feedback divider: `fb_clk` must be derived from DCO/divider edges and must have nonzero late-window edges.",
            "- Control/lock path: `vctrl_mon` should remain in range and change consistently with phase/frequency error; `lock` should assert only after measured edge cadence is stable.",
            "- Integrated check: if EVAS reports `fb=0` or `not_enough_edges`, repair DCO/divider event scheduling before changing lock thresholds.",
            "- Integrated check: if EVAS reports `late_edge_ratio`, preserve the observable columns and adjust feedback cadence/divider ratio first.",
        ])
    return lines


def _multi_module_interface_harness_sanity_section(task_id: str, notes: list[str]) -> list[str]:
    """Recover runtime CSV failures caused by module/testbench mismatch."""
    task_lower = _task_id_text_for_matching(task_id)
    joined = "\n".join(str(note) for note in notes).lower()
    if not any(key in joined for key in ("tran.csv missing", "returncode=1", "dut_not_compiled")):
        return []
    if not any(key in task_lower for key in ("gain_extraction", "sar_adc_dac_weighted_8b", "dwa_ptr_gen")):
        return []

    lines = [
        "",
        "# Multi-Module Interface/Harness Sanity Skeleton",
        "",
        "- Treat this as a runtime/harness recovery task until EVAS produces `tran.csv`.",
        "- Do not tune numeric behavior while `returncode=1` or `tran.csv missing` remains.",
        "- Every `ahdl_include` must name a Verilog-A file emitted in this answer; every included file must declare the same module name as its filename stem.",
        "- Every instance must use Spectre-safe positional syntax: `Xname (node1 node2 ...) module_name params...`.",
        "- Do not use named-port instance syntax, nested vector groups, or extra parentheses inside the node list.",
        "- If a Verilog-A port is a bus, expand it to scalar nodes positionally in the same order expected by the task.",
        "- Use exactly one `simulator lang=spectre`, one `tran`, and one canonical `save` list with public scalar names.",
        "- Use node `0` as ground consistently; avoid mixing `gnd`, `vss`, and `0` unless the task module explicitly has a `vss` port and every source is wired consistently.",
    ]

    if "gain_extraction" in task_lower:
        lines.extend([
            "",
            "## Gain-extraction required interface sanity",
            "",
            "- Emit exactly these DUT modules and no estimator module: `vin_src`, `lfsr`, `dither_adder`, `gain_amp_fixed`.",
            "- Do not create or instantiate `gain_estimator`; the checker estimates gain from saved waveforms.",
            "- Instantiate `vin_src` with ports `(clk rst_n vinp vinn)`.",
            "- Instantiate `lfsr` with ports `(dpn vdd vss clk en rst_n)`.",
            "- Instantiate `dither_adder` with ports `(vinp vinn dpn vdin_p vdin_n)`.",
            "- Instantiate `gain_amp_fixed` with ports `(vdin_p vdin_n vamp_p vamp_n)`.",
            "- Keep `rst_n` deasserted high and `en` asserted during the measurement window.",
            "- Save exactly `vinp vinn vamp_p vamp_n` for the public checker columns.",
        ])
    if "sar_adc_dac_weighted_8b" in task_lower:
        lines.extend([
            "",
            "## SAR ADC/DAC required interface sanity",
            "",
            "- Emit exactly `sar_adc_weighted_8b`, `dac_weighted_8b`, `sh_ideal`, and one top-level testbench.",
            "- ADC instance order is `(vin clks rst_n dout_7 dout_6 dout_5 dout_4 dout_3 dout_2 dout_1 dout_0)` if scalar-expanded from `[7:0]` MSB-to-LSB.",
            "- DAC instance order is `(dout_7 dout_6 dout_5 dout_4 dout_3 dout_2 dout_1 dout_0 vout)` if scalar-expanded from `[7:0]` MSB-to-LSB.",
            "- SH instance order is `(vin clks vdd vss rst_n vin_sh)`.",
            "- Save `vin vin_sh clks rst_n vout dout_7 dout_6 dout_5 dout_4 dout_3 dout_2 dout_1 dout_0`.",
        ])
    if "dwa_ptr_gen" in task_lower:
        lines.extend([
            "",
            "## DWA pointer-generator required interface sanity",
            "",
            "- If using `v2b_4b`, include and instantiate it with plain scalar nodes; otherwise drive `code_3..code_0` directly.",
            "- The DWA DUT node list must be flat, with no nested groups: `Xdut (clk_i rst_ni code_3 code_2 code_1 code_0 cell_en_15 ... cell_en_0 ptr_15 ... ptr_0) dwa_ptr_gen`.",
            "- Do not write `dwa_ptr_gen dut (...)` and do not place `(code3 code2 code1 code0)` as a grouped argument inside the node list.",
            "- Save `clk_i rst_ni ptr_15..ptr_0 cell_en_15..cell_en_0` as plain scalar names.",
            "- Keep reset deasserted high through the full checking window.",
        ])
    return lines


def _pfd_pll_timing_window_section(task_id: str, notes: list[str]) -> list[str]:
    """Force timing-window failures to repair stimulus/check windows first."""
    task_lower = _task_id_text_for_matching(task_id)
    joined = "\n".join(str(note) for note in notes).lower()
    if not any(key in task_lower for key in ("pfd", "pll", "adpll", "cppll")):
        return []
    if not any(key in joined for key in ("behavior_eval_timeout", "late_edge_ratio", "not_enough_edges", "freq_ratio", "lock_time", "up_first", "dn_second", "overlap_frac")):
        return []

    lines = [
        "",
        "# PFD/PLL Timing-Window Skeleton",
        "",
        "- Treat this as a timing-window repair, not a broad rewrite.",
        "- The generated comments are not enough: the actual voltage sources and state machines must create the checker-visible windows.",
        "- Preserve public columns and fixed `tran` settings unless the current failure is `tran.csv missing`.",
    ]

    if "pfd" in task_lower:
        lines.extend([
            "",
            "## PFD reset-race windows",
            "",
            "- Create two explicit comparison windows in the actual stimulus, not only in comments.",
            "- First window: REF rising edges lead DIV rising edges by a small positive delta, so UP pulses are expected.",
            "- Second window: DIV rising edges lead REF rising edges by a small positive delta, so DN pulses are expected.",
            "- A single pair of periodic pulse sources with fixed delays cannot implement a lead/lag swap; use PWL edge lists or two gated pulse segments.",
            "- Keep UP/DN pulse widths finite and easy to sample, for example around `0.5n` to `2n`; avoid `1p` transition edges unless the task explicitly requires picosecond resolution.",
            "- Do not schedule timers at stale release times such as zero; only arm a release timer immediately after asserting a pulse.",
            "- Success shape: first window has visible UP and near-zero DN, second window has visible DN and near-zero UP, and `overlap_frac` remains near zero.",
        ])
    if "pll" in task_lower:
        lines.extend([
            "",
            "## PLL/ADPLL edge-count windows",
            "",
            "- Ensure both `ref_clk` and `fb_clk` have enough late-window edges; `fb=0` means the DCO/divider scheduling is broken, not merely the lock threshold.",
            "- Use monotonic `next_edge_time` style timer scheduling for DCO/feedback edges; after each timer event, schedule the next future event.",
            "- Keep feedback divider state tied to DCO edges so `fb_clk` cannot stop while `dco_clk` continues.",
            "- Tune lock only after edge cadence is visible; a high `lock` with wrong `late_edge_ratio` is still a behavior failure.",
        ])
    return lines


def _conservative_behavior_boundary_section(evas_result: dict) -> list[str]:
    """Protect a compile-clean candidate from behavior-repair regressions."""
    status = evas_result.get("status", "")
    scores = evas_result.get("scores", {})
    dut_compile = float(scores.get("dut_compile", 0.0))
    tb_compile = float(scores.get("tb_compile", 0.0))
    if status != "FAIL_SIM_CORRECTNESS" or dut_compile < 1.0 or tb_compile < 1.0:
        return []

    notes = evas_result.get("evas_notes") or evas_result.get("notes") or []
    lowered = "\n".join(str(note) for note in notes).lower()
    if "tran.csv missing" in lowered or "returncode=1" in lowered or "tb_not_executed" in lowered:
        return []

    return [
        "",
        "# High-Level Repair Template: Conservative Behavior-Only Patch",
        "",
        "EVAS already reached a compile-clean and simulation-runnable candidate. From this point, treat the testbench/interface/syntax as a protected anchor.",
        "",
        "Mandatory guardrails:",
        "- Do not change module names, port order, filenames, `ahdl_include` lines, save names, `tran` setup, or stimulus sources.",
        "- Do not introduce new submodules, new hierarchy, renamed nodes, alternate supplies, or a different clock/reset convention.",
        "- Do not replace a compile-clean Verilog-A style with SystemVerilog-like constructs.",
        "- Keep every existing observable column alive. If a column was present in the current `tran.csv`, the next candidate must still expose it.",
        "- Change only the internal state update, threshold/quantization math, pulse timer, divider counter, or output target assignment that explains the failing metric.",
        "- If the next edit would require touching both DUT interface and TB, stop and instead make a smaller DUT-internal semantic edit.",
        "",
        "Anti-regression checklist before output:",
        "- No `reg`, `wire`, `always`, packed integer bit assignments, dynamic `V(bus[i])`, conditional `cross`, or conditional `transition()` contributions.",
        "- All temporary `integer`/`real` declarations remain at module scope.",
        "- Electrical outputs are driven from target variables by unconditional `transition()` contributions.",
        "- Reset behavior, clock edge direction, and output bit order are preserved unless the failing metric directly identifies one of them.",
    ]


def _metric_to_mechanism_template(task_id: str, notes: list[str]) -> list[str]:
    """Map recurring EVAS metric symptoms to generic repair mechanisms."""
    joined = "\n".join(str(note) for note in notes)
    lowered = joined.lower()
    metrics = _extract_metrics_from_notes(notes)
    task_lower = _task_id_text_for_matching(task_id)
    lines: list[str] = []

    def has_metric(*names: str) -> bool:
        return any(name in metrics or f"{name}=" in lowered for name in names)

    def add_header() -> None:
        if not lines:
            lines.extend([
                "",
                "# High-Level Repair Template: Metric-to-Mechanism Map",
                "",
                "Use the EVAS metric as a symptom of a circuit mechanism, not as a string to satisfy cosmetically. Pick the matching mechanism below and make the smallest code change that changes that metric.",
            ])

    if (
        has_metric("fb", "ref", "late_edge_ratio", "freq_ratio", "lock_time", "pre_lock_edges", "post_lock_edges")
        or any(key in task_lower for key in ("adpll", "cppll", "pll"))
    ):
        add_header()
        lines.extend([
            "",
            "## Mechanism: PLL/ADPLL feedback and lock path",
            "",
            "- `fb=0`, `num=0`, `pre_lock_edges=0`, or `post_lock_edges=0` means the feedback edge generator/divider is not toggling in the checker window.",
            "- Do not fix this by changing only `lock` thresholds or forcing `lock=1`; first make feedback edges visible.",
            "- Use one monotonic timer state for oscillator edges: after each timer event, schedule the next strictly future edge.",
            "- Tie feedback divider toggling to oscillator/DCO edges; do not let `fb_clk` depend on a one-shot initialization event.",
            "- Ratio errors such as `freq_ratio` far from target mean terminal count/divider ratio is wrong; repair the counter threshold before touching analog control voltage.",
            "- `late_edge_ratio` failures mean visible edges exist but cadence is wrong; preserve columns and adjust DCO period/divider cadence.",
        ])

    if (
        has_metric("up_first", "dn_first", "up_second", "dn_second", "up_pulses_first", "dn_pulses_second", "too_few_updn_pulses", "overlap_frac")
        or any(key in task_lower for key in ("pfd", "bbpd"))
    ):
        add_header()
        lines.extend([
            "",
            "## Mechanism: phase-detector pulse generation",
            "",
            "- `up_pulses=0`, `dn_pulses=0`, or `too_few_updn_pulses` means the detector edge-order state is not producing finite pulses.",
            "- Implement edge-latched pulse state: record which edge arrived first, assert the corresponding output, and clear it after a finite pulse width.",
            "- Do not leave UP/DN as pure combinational comparisons of current input levels; the checker measures pulses over windows.",
            "- If overlap is high, shorten pulse width or reset both outputs after both edges are observed; do not remove all pulses.",
            "- For reset-race tasks, the first and second windows must exercise opposite lead/lag cases; preserve the checker stimulus and repair state timing.",
        ])

    if (
        has_metric("transitions", "hi_frac", "complement_err", "invert_match_frac")
        or any(key in task_lower for key in ("lfsr", "prbs", "digital", "dff", "nrz"))
    ):
        add_header()
        lines.extend([
            "",
            "## Mechanism: digital state-machine activity",
            "",
            "- `transitions=0` or `hi_frac=0` means the state machine is stuck in reset, never clocked, or never updates its output target.",
            "- First verify reset releases permanently and the clock crossing direction is correct.",
            "- Keep one integer state variable as the source of truth; update it exactly once per valid clock edge.",
            "- For LFSR/PRBS, compute feedback from fixed state bits, shift/update the integer state, and drive output from that state.",
            "- For differential/complement outputs, drive both outputs from the same state with opposite target values; do not compute them independently.",
            "- `invert_match_frac=0` usually means polarity is exactly inverted; flip the target assignment, not the whole harness.",
        ])

    if (
        has_metric("unique_codes", "vout_span", "avg_abs_err", "code_span", "settled_high")
        or any(key in task_lower for key in ("adc", "dac", "sar", "cal"))
    ):
        add_header()
        lines.extend([
            "",
            "## Mechanism: ADC/DAC/calibration code path",
            "",
            "- `unique_codes=1`, `vout_span=0`, or `code_span=0` means the code path is stuck, even if the waveform columns exist.",
            "- Keep one integer code as the source of truth: sampled input/calibration state -> code -> output bits/DAC voltage.",
            "- Drive every output bit and analog DAC output from that same code; do not maintain separate unsynchronized bit and voltage states.",
            "- Check reset release before changing quantization math; a valid code path cannot remain held in reset during the conversion window.",
            "- Use `floor(...)` and explicit clipping for quantization; avoid `$floor(...)` and declarations inside event blocks.",
            "- For multi-module ADC/DAC tasks, verify each public module boundary carries activity: sample/hold output changes, ADC bits change, DAC output changes.",
        ])

    if (
        has_metric("ratio_code", "in_edges", "out_edges", "period_match", "base", "pre_count", "post_count")
        or "divider" in task_lower
    ):
        add_header()
        lines.extend([
            "",
            "## Mechanism: divider ratio and dynamic switching",
            "",
            "- If input/output edges exist but `period_match=0` or counts are wrong, the divider terminal count or ratio decode is wrong.",
            "- Use one integer edge counter updated on each input clock crossing.",
            "- Toggle output only when the counter reaches the decoded ratio terminal count, then reset the counter.",
            "- For ratio-switch tasks, latch the new ratio at a safe clock boundary and avoid mid-cycle counter corruption.",
            "- Do not repair divider failures by changing the testbench clock if EVAS already reports many input edges.",
        ])

    if (
        "behavior_eval_timeout" in lowered
        or "pathological" in lowered
        or any(key in task_lower for key in ("bad_bus_output_loop",))
    ):
        add_header()
        lines.extend([
            "",
            "## Mechanism: pathological CSV/checker timeout",
            "",
            "- A checker timeout after `returncode=0` means the waveform exists but is too pathological or too dense for the Python evaluator.",
            "- Avoid uncontrolled high-frequency toggling, zero-delay feedback, or output loops that generate excessive events.",
            "- Keep output transitions bounded by explicit clock/reset events; do not create combinational oscillation through electrical outputs.",
            "- Reduce unnecessary saved internal nodes; preserve only public checker columns.",
            "- Repair the state/update mechanism before changing checker-facing names.",
        ])

    if (
        "tran.csv missing" in lowered
        or "returncode=1" in lowered
        or "dut_not_compiled" in lowered
    ):
        add_header()
        lines.extend([
            "",
            "## Mechanism: runtime/interface artifact loss",
            "",
            "- `returncode=1` with missing `tran.csv` is not yet a behavior failure; restore a runnable DUT/TB artifact first.",
            "- Check include filenames, module names, positional instance node counts, ground node consistency, and unsupported Spectre syntax.",
            "- Do not tune thresholds or counters until the next EVAS run produces a CSV and behavior metrics.",
        ])

    return lines


_SPECIFIC_DIAGNOSTIC_MARKERS = (
    "dynamic_analog_vector_index=",
    "conditional_cross=",
    "conditional_transition=",
    "digital_verilog_syntax=",
    "genvar_inside_analog=",
    "undefined_module=",
    "colon_instance_syntax_lines=",
    "evas_compile_errors:",
    "missing dout_code",
    "missing dout_0..7",
    "bit_mismatch",
    "only_",
    "unique_codes=",
    "up_first=",
    "dn_first=",
)


def _is_specific_diagnostic(note: str) -> bool:
    lowered = note.lower()
    return any(marker in lowered for marker in _SPECIFIC_DIAGNOSTIC_MARKERS)


def _specific_diagnostics(notes: list[str], limit: int = 8) -> list[str]:
    selected: list[str] = []
    seen: set[str] = set()
    for raw in notes:
        note = str(raw).strip()
        if not note or not _is_specific_diagnostic(note):
            continue
        if note in seen:
            continue
        seen.add(note)
        selected.append(note)
        if len(selected) >= limit:
            break
    return selected


def _history_specific_diagnostics(history: list[dict], limit: int = 8) -> list[str]:
    selected: list[str] = []
    seen: set[str] = set()
    for entry in reversed(history):
        candidates = list(entry.get("concrete_diagnostics") or [])
        candidates.extend(entry.get("evas_notes") or [])
        for note in _specific_diagnostics(candidates, limit=limit):
            tagged = f"R{entry.get('round', '?')}: {note}"
            if tagged in seen:
                continue
            seen.add(tagged)
            selected.append(tagged)
            if len(selected) >= limit:
                return selected
    return selected


def _diagnostic_retention_section(notes: list[str], history: list[dict]) -> str:
    current_specific = _specific_diagnostics(notes, limit=6)
    history_specific = _history_specific_diagnostics(history, limit=8)
    if not current_specific and not history_specific:
        return ""

    lowered = "\n".join(str(note) for note in notes).lower()
    current_is_generic_compile = (
        "dut_not_compiled" in lowered
        or "tb_not_executed" in lowered
        or "tran.csv missing" in lowered
    )

    lines = [
        "# Diagnostic Retention",
        "",
        "The following are EVAS failure classes and source locations observed during repair.",
        "They are not gold implementation details. Use them to avoid losing the concrete compile/observable diagnosis.",
        "",
    ]
    if current_specific:
        lines.append("Current concrete diagnostics:")
        lines.extend(f"- `{note}`" for note in current_specific)
        lines.append("")
    if history_specific:
        if current_is_generic_compile and not current_specific:
            lines.append(
                "The current result is generic, but previous rounds had more actionable diagnostics. Continue fixing these classes first:"
            )
        else:
            lines.append("Recent concrete diagnostics to preserve:")
        lines.extend(f"- `{note}`" for note in history_specific)
        lines.append("")
    lines.extend([
        "Retention policy:",
        "- If a later round only says `dut_not_compiled` or `tran.csv missing`, do not ignore earlier concrete diagnostics.",
        "- Fix the retained diagnostic class before changing circuit behavior.",
        "- Do not introduce benchmark-specific constants; use only public task contract, EVAS notes, and generic Verilog-A compatibility rules.",
    ])
    return "\n".join(lines)


def _targeted_repair_skill(
    task_dir: Path,
    evas_result: dict,
    include_skill: bool = True,
    sample_dir: Path | None = None,
) -> str:
    meta = read_meta(task_dir)
    family = meta.get("family", "end-to-end")
    task_prompt = build_prompt(task_dir)
    task_id = meta.get("task_id", meta.get("id", ""))
    status = evas_result.get("status", "FAIL_OTHER")
    # Include both evas_notes and spectre_notes (for Spectre backend results)
    notes = evas_result.get("evas_notes") or evas_result.get("notes") or []
    spectre_notes = evas_result.get("spectre_notes", [])
    notes = notes + [n for n in spectre_notes if n not in notes]

    lines = [
        "# EVAS-Guided Repair Skill",
        "",
        "Use only the repair rules relevant to the reported EVAS failure.",
        "Keep the original task contract fixed while repairing the candidate.",
    ]

    if family == "end-to-end":
        tran_params = _get_gold_tran_params(task_dir)
        tran_hint = (
            f"- **Use exactly this tran statement (from the reference design): `tran tran {tran_params}`**"
            if tran_params else
            "- Use a single `tran` analysis: stop time 5u~20u for PLL/slow circuits, 100n~2u for digital; maxstep at least 1n."
        )
        lines.extend([
            "",
            "End-to-end repair contract:",
            "- Return the full DUT artifact set required by the task plus exactly one top-level Spectre testbench.",
            "- Do not split the answer into several independent testbenches.",
            "- Preserve the task's intended module granularity: keep single-block behavioral tasks single-block, and preserve explicit multi-block tasks as separately named modules.",
            "- During repair, do not introduce or remove hierarchy unless EVAS reports an artifact/interface mismatch or the public task contract explicitly requires the split.",
            "- **DUT-TB filename consistency (critical):** The `ahdl_include` path in the TB must exactly match",
            "  the filename of your generated DUT. The DUT file is saved as `<module_name>.va` where",
            "  `<module_name>` is the identifier after the `module` keyword in your Verilog-A file.",
            "  Example: if your DUT declares `module lfsr(...)`, the file is `lfsr.va` and the TB must have",
            "  `ahdl_include \"lfsr.va\"` — not `./lfsr31_v.va` or any other name.",
            tran_hint,
            "- **NEVER set maxstep smaller than 1n** unless the gold reference uses a smaller value — tiny maxstep causes simulation timeout.",
            "- Do not use bare `errpreset=conservative` without an explicit `maxstep`.",
        ])

    implementation_skeleton_lines = _implementation_safety_skeleton_section(task_dir, evas_result, sample_dir)
    if implementation_skeleton_lines:
        lines.extend(implementation_skeleton_lines)

    if status == "FAIL_DUT_COMPILE":
        lines.extend([
            "",
            "Targeted DUT repair rules:",
            "- Preserve the exact module name expected by the task and any referenced testbench include.",
            "- **Port order convention: VDD/VSS first, then signal ports.**",
            "  - Example NOT gate: `module not_gate (inout VDD, inout VSS, input A, output Y);`",
            "  - Example DFF: `module dff_rst (inout VDD, inout VSS, input D, input CLK, input RST, output Q, output QB);`",
            "- Preserve port order exactly; do not silently reorder or rename interface pins.",
            "- **Do NOT re-declare ports after ANSI-style header.**",
            "  - Wrong: `module foo (input A, output Y); electrical A, Y;`",
            "  - Correct: `module foo (input electrical A, output electrical Y);`",
            "- Use voltage-domain Verilog-A only: `V() <+`, `transition`, `cross`, `timer`, `initial_step`.",
            "- Do not use `I()`, `ddt`, `idt`, `idtmod`, `laplace_*`, or plain Verilog `initial begin`.",
            "- Keep declarations at module scope and use `electrical` on signal ports.",
            "- For power rails, use `inout`, not plain `input`.",
            "- Prefer the smallest interface-preserving repair that resolves compile/linkage issues.",
            "",
            "## Verilog-A Mandatory Syntax Rules (Spectre VACOMP strict)",
            "",
            "These rules come from a curated library of 1,638 real Verilog-A designs.",
            "Violating any rule causes Spectre VACOMP to reject the file.",
            "",
            "**Rule 1 — Signal types: use `electrical`, never `reg`/`wire`/`logic`**",
            "- All ports and internal nets must use `electrical` (or `integer`/`real` for scalars).",
            "- `reg` does not exist in Verilog-A. Replace every `reg` with `integer`.",
            "  ```",
            "  // WRONG (SystemVerilog):  reg cnt_reg; reg lock;",
            "  // CORRECT (Verilog-A):   integer cnt_reg; integer lock;",
            "  ```",
            "",
            "**Rule 2 — No packed bit-select on `integer` variables**",
            "- Verilog-A has no packed arrays on scalar integers.",
            "- `x[0] = 1` is invalid when `x` is declared as `integer`.",
            "- To read individual bits from an electrical bus, unroll port-by-port:",
            "  ```",
            "  // WRONG:  div_val[0] = (V(d[0]) > vth) ? 1 : 0;",
            "  // CORRECT: integer b; div_val = 0;",
            "  //   if (V(d[0]) > vth) div_val = div_val + 1;",
            "  //   if (V(d[1]) > vth) div_val = div_val + 2;",
            "  //   if (V(d[2]) > vth) div_val = div_val + 4;",
            "  ```",
            "",
            "**Rule 3 — Edge detection: use `@(cross())`, not `always @`**",
            "- Rising edge: `@(cross(V(clk) - vth, +1))`",
            "- Falling edge: `@(cross(V(clk) - vth, -1))`",
            "- `always @(posedge clk)` does not exist in Verilog-A.",
            "",
            "**Rule 4 — All declarations at module scope, before `analog begin`**",
            "- `integer`, `real`, `parameter`, `genvar` must come before `analog begin`.",
            "",
            "**Rule 5 — Outputs use `transition()` with a discrete target variable**",
            "  ```",
            "  real out_target;",
            "  out_target = state ? vh : vl;",
            "  V(out_o) <+ transition(out_target, 0, tr, tf);",
            "  ```",
            "",
            "**Rule 6 — Initialize state in `@(initial_step)`**",
            "  ```",
            "  @(initial_step) begin",
            "      cnt = 0; state = 0; lock = 0;",
            "  end",
            "  ```",
        ])
    elif status == "FAIL_TB_COMPILE":
        lines.extend([
            "",
            "Targeted testbench repair rules:",
            "- Write a single top-level Spectre testbench, not several stitched mini-netlists.",
            "- Use `simulator lang=spectre` when the file uses Spectre directives such as `ahdl_include`, `save`, and `tran`.",
            "- Do not place `ahdl_include` or `save` in a spice-language section.",
            "- **Do NOT use colon-instance syntax in save statements** (e.g., `and_dut:A` is invalid).",
            "- Use plain signal names in save statements: `save a b y` not `save X1:A X1:B X1:Y`.",
            "- Match DUT instance module names and port order exactly to the emitted DUT modules.",
            "- Keep the save list aligned with the task-required observables.",
            "- Use a single `tran` statement: `tran tran stop=200n maxstep=5n`.",
            "- Use only `vsource` elements for stimulus (type=pulse or type=pwl). Do NOT use `vcvs`, `ccvs`, `capacitor`, or `resistor` unless the task explicitly requires them.",
            "- PWL `wave=[...]` time entries must be strictly increasing; use a tiny finite transition interval instead of duplicate timestamps.",
            "- For long instance node lists, either keep the whole `XDUT (...) module_name` instance on one line or use explicit `\\` continuation at each line break.",
            "- Write a single `tran` analysis. Do NOT add `dc` sweep or `ac` analysis.",
            "- In `save` statements, use plain signal names only: `save clk vin vout`. Do NOT use `XDUT:signal` colon syntax.",
            "- Add `global 0` on the line after `simulator lang=spectre`.",
            "- `ahdl_include` must be the absolute LAST line in the netlist.",
        ])
        lines.extend(_gold_dut_port_order_hints(task_dir, notes))
    elif status == "FAIL_SIM_CORRECTNESS":
        sim_subtype, subtype_examples = _classify_sim_correct_failure(notes, task_id)
        lines.extend(["", f"FAIL_SIM_CORRECTNESS subtype: `{sim_subtype}`"])
        if subtype_examples:
            lines.append("- Representative EVAS notes:")
            for example in subtype_examples:
                lines.append(f"  - `{example}`")
        lines.extend(_repair_policy_contract(task_id, notes, sim_subtype))
        lines.extend(build_observation_policy_section(notes))
        lines.extend(_conservative_behavior_boundary_section(evas_result))
        lines.extend(_metric_to_mechanism_template(task_id, notes))
        lines.extend(_complex_submodule_local_validation_section(task_id, notes))
        lines.extend(_multi_module_interface_harness_sanity_section(task_id, notes))
        lines.extend(_pfd_pll_timing_window_section(task_id, notes))
        if sim_subtype == "observability_contract":
            lines.extend([
                "",
                "Targeted observability/contract repair rules:",
                "- Prioritize checker-contract alignment before semantic rewrites.",
                "- Ensure save statement uses exact checker-required lowercase signal names.",
                "- Keep one canonical save list and avoid alias/instance-colon save syntax.",
                "- Preserve DUT behavior while fixing naming/export coverage.",
            ])
            observable_template_lines = _observable_scalar_alias_template(task_id, notes)
            if observable_template_lines:
                lines.extend(observable_template_lines)
            post_reset_template_lines = _post_reset_sample_budget_template(task_id, notes, sample_dir)
            if post_reset_template_lines:
                lines.extend(post_reset_template_lines)
            reset_hold_lines = _reset_hold_contract_template(task_id, notes, sample_dir)
            if reset_hold_lines:
                lines.extend(reset_hold_lines)
            settle_lines = _clocked_output_settle_template(task_id, notes, sample_dir)
            if settle_lines:
                lines.extend(settle_lines)
        elif sim_subtype == "simulation_artifact":
            lines.extend([
                "",
                "Targeted simulation-artifact repair rules:",
                "- Stabilize runability first: valid tran setup, realistic maxstep, complete includes.",
                "- Eliminate compile/runtime blockers before changing behavior logic.",
                "- Keep interfaces fixed; do not introduce broad rewrites until tran.csv is consistently produced.",
            ])
            reset_hold_lines = _reset_hold_contract_template(task_id, notes, sample_dir)
            if reset_hold_lines:
                lines.extend(reset_hold_lines)
            settle_lines = _clocked_output_settle_template(task_id, notes, sample_dir)
            if settle_lines:
                lines.extend(settle_lines)
        else:
            lines.extend([
                "",
                "Targeted behavioral repair rules:",
                "- Preserve interface and testbench structure; focus on semantics rather than broad rewrites.",
                "- Check threshold choice, edge direction, reset priority, initialization, and output complement rules.",
                "- Ensure the testbench stimulates and saves every signal required by the checker.",
                "- If the DUT is edge-driven, prefer explicit `@(cross(..., dir))` with correct direction.",
                "- If the output uses `transition`, drive a target variable continuously rather than embedding unstable expressions.",
                "- **For multi-module tasks, use module prefix in signal names**:",
                "  - NOT gate signals: `not_a`, `not_y` (or `a`, `y` if single module)",
                "  - AND gate signals: `and_a`, `and_b`, `and_y`",
                "  - DFF signals: `dff_d`, `dff_clk`, `dff_q`, `dff_qb`",
                "- **Instance syntax: use positional port order, not named ports**:",
                "  - Correct: `I_not (vdd vss a y) not_gate`",
                "  - Wrong: `I_not not_gate A=a VDD=vdd VSS=vss Y=y` (named port syntax may not work)",
            ])
            post_reset_template_lines = _post_reset_sample_budget_template(task_id, notes, sample_dir)
            if post_reset_template_lines:
                lines.extend(post_reset_template_lines)
            reset_hold_lines = _reset_hold_contract_template(task_id, notes, sample_dir)
            if reset_hold_lines:
                lines.extend(reset_hold_lines)
            settle_lines = _clocked_output_settle_template(task_id, notes, sample_dir)
            if settle_lines:
                lines.extend(settle_lines)
    elif status == "FAIL_INFRA":
        # Parse what's actually missing from the notes
        missing_files: list[str] = []
        for note in notes:
            if note.startswith("missing_generated_files:"):
                files_str = note[len("missing_generated_files:"):].strip()
                missing_files.extend([f.strip() for f in files_str.split(",") if f.strip()])

        if missing_files:
            missing_list = ", ".join(f"`{f}`" for f in missing_files)
            lines.extend([
                "",
                f"FAIL_INFRA: EVAS could not evaluate your submission because the following required files were not generated: {missing_list}",
                "",
                "Required action:",
            ])
            if any(f.endswith(".scs") for f in missing_files):
                lines.extend([
                    "- **You must generate a complete Spectre testbench** (`.scs` file) in addition to the DUT.",
                    "- The testbench must include `ahdl_include` for your DUT, stimulus sources, save directives, and a `tran` analysis.",
                    "- Both your DUT Verilog-A file(s) and the testbench must be present in this response.",
                    "- Do not return only the DUT — the testbench is required to evaluate correctness.",
                ])
            if any(f.endswith(".va") for f in missing_files):
                lines.extend([
                    f"- **You must generate the missing DUT Verilog-A file(s)**: {missing_list}",
                    "- Ensure the module name and port list exactly match what the testbench expects.",
                ])
        else:
            lines.extend([
                "",
                "FAIL_INFRA: EVAS could not evaluate your submission due to missing or unreadable artifacts.",
                "- Ensure you return ALL required files: DUT Verilog-A file(s) and Spectre testbench (if required by the task).",
                "- Each code block must be complete and syntactically correct so EVAS can extract it.",
                "- Do not truncate code blocks or mix multiple files into one block.",
            ])
    else:
        lines.extend([
            "",
            "Generic repair rules:",
            "- Preserve artifact shape and interface contract first.",
            "- Repair malformed code blocks, missing files, or obvious compatibility problems before changing behavior.",
        ])

    # Compile-related hints (keep existing)
    note_hints: list[str] = []
    for note in notes:
        if "undefined_module=" in note:
            import re as _re
            # undefined_module = what the TB is searching for (the NEEDED name)
            # available_modules = what the LLM provided (the WRONG name it used)
            _m_needed = _re.search(r"undefined_module=([^;]+)", note)
            _m_provided = _re.search(r"available_modules=([^;\s]+)", note)
            _needed = _m_needed.group(1).split(",")[0].strip() if _m_needed else None
            _provided = _m_provided.group(1).split(",")[0].strip() if _m_provided else None
            if _needed and _provided and _needed != _provided:
                note_hints.extend([
                    f"- **CRITICAL MODULE NAME ERROR.** Your code declares `module {_provided}` but the testbench expects `module {_needed}`.",
                    f"- **The ONLY fix required: change the single line `module {_provided}(` to `module {_needed}(`. Do not alter any other code.**",
                    f"- **Do NOT output a file named `{_needed}.va`. Output exactly one `verilog-a` code block containing `module {_needed}(...)`.**",
                ])
            else:
                note_hints.append("- EVAS saw an undefined module mismatch: make the declared module name exactly match what the testbench instantiates.")
        if "colon_instance_syntax_lines=" in note:
            note_hints.extend([
                "- **CRITICAL: Colon-instance syntax detected**. Spectre rejects this pattern.",
                "- Replace `save X1:A X1:B X1:Y` with plain signal names: `save a b y`.",
            ])
        if "nonincreasing_pwl_time=" in note:
            note_hints.extend([
                "- **CRITICAL: PWL time vector is not strictly increasing.** Spectre rejects duplicate timestamps.",
                "- Replace duplicate-time steps with small finite intervals, for example `3.99n old 4n new` rather than `4n old 4n new`.",
            ])
        if "uncontinued_multiline_instance=" in note:
            note_hints.extend([
                "- **CRITICAL: Bare multiline Spectre instance detected.** Spectre will parse the following lines as separate undefined instances.",
                "- Put the complete instance on one line or add `\\` at each continued instance line.",
            ])
        if "conditional_transition=" in note:
            note_hints.extend([
                "- **CRITICAL: Conditional transition pattern detected**. Spectre rejects this.",
                "- Use: `target = condition ? high : low; V(out) <+ transition(target, ...);`",
            ])
        if "conditional_cross=" in note:
            issue = note.split("conditional_cross=", 1)[-1].strip()
            hits = [hit.strip() for hit in issue.split(",") if hit.strip()]
            note_hints.extend([
                "- **CRITICAL: `@(cross(...))` is inside an `if`/`else`/`case` branch. EVAS/Spectre rejects this.**",
                "- Move every `@(cross(...))` event statement to the top level of the `analog begin` block.",
                "- Put reset/enable conditions inside the event body instead of wrapping the event statement.",
                "- Do not write `if (...) @(cross(...))` or `else @(cross(...))`.",
                "- Correct shape: `@(cross(V(clk)-vth,+1)) begin if (V(rst)>vth && V(en)>vth) begin ... end end`.",
            ])
            if hits:
                note_hints.append("- Offending conditional cross locations reported by EVAS:")
                for hit in hits[:8]:
                    note_hints.append(f"  - `{hit}`")
        if "genvar_inside_analog=" in note:
            issue = note.split("genvar_inside_analog=", 1)[-1].strip()
            hits = [hit.strip() for hit in issue.split(",") if hit.strip()]
            note_hints.extend([
                "- **CRITICAL: `genvar` was declared inside `analog begin`. Move it to module scope.**",
                "- Correct placement: declare `genvar k;` beside `integer`/`real` declarations, before `analog begin`.",
                "- Keep the `for (k=0; ...) begin V(bus[k]) <+ ... end` contribution inside `analog begin`.",
            ])
            if hits:
                note_hints.append("- Offending genvar locations reported by EVAS:")
                for hit in hits[:8]:
                    note_hints.append(f"  - `{hit}`")
        if "dynamic_analog_vector_index=" in note:
            issue = note.split("dynamic_analog_vector_index=", 1)[-1].strip()
            hits = [hit.strip() for hit in issue.split(",") if hit.strip()]
            note_hints.extend([
                "- **CRITICAL: runtime analog bus indexing detected.** EVAS/Spectre rejects `V(bus[i])` when `i` is an `integer` runtime loop variable.",
                "- This is a compile-layer error. Fix it before changing any behavioral algorithm.",
                "- Replace every offending `V(bus[i])` read with fixed-index reads such as `V(bus[0])`, `V(bus[1])`, `V(bus[2])`, `V(bus[3])`.",
                "- Replace every offending output contribution loop `for (i=0; ...) V(out[i]) <+ ...` with a `genvar k` loop, or explicitly write each output contribution.",
                "- Declare `genvar k;` at module scope before `analog begin`; do not declare `genvar` inside `analog begin`.",
                "- Do not use `integer i` inside `V(...)` for electrical bus reads or writes anywhere in the repaired code.",
            ])
            if hits:
                note_hints.append("- Offending locations reported by EVAS:")
                for hit in hits[:8]:
                    note_hints.append(f"  - `{hit}`")
            note_hints.extend([
                "- Example fixed-index input decode:",
                "  - `code = 0; if (V(code_i[0])>vth) code=code+1; if (V(code_i[1])>vth) code=code+2; if (V(code_i[2])>vth) code=code+4; if (V(code_i[3])>vth) code=code+8;`",
                "- Example static output bus contribution:",
                "  - `real ptr_val[0:15]; genvar k; analog begin ... for (k=0; k<16; k=k+1) begin V(ptr_o[k]) <+ transition(ptr_val[k], 0, tr, tf); end end`",
            ])
        if "no_ahdl_va_include_in_tb" in note:
            note_hints.append("- The current testbench does not properly include the DUT: add explicit `ahdl_include` lines.")
        if note.startswith("missing ") or "missing_" in note:
            # Try to inject exact checker-required column names for end-to-end tasks
            required_cols = _extract_checker_required_columns(task_id) if family == "end-to-end" else []
            if required_cols:
                save_stmt = " ".join(required_cols)
                note_hints.extend([
                    f"- **CRITICAL: Checker expects these exact lowercase column names in tran.csv: `{save_stmt}`**",
                    f"- Your testbench `save` statement must use exactly: `save {save_stmt}`",
                    "- Do NOT use uppercase (e.g. `DIN3`, `AOUT`) — the checker uses case-sensitive string matching.",
                ])
            else:
                note_hints.append("- EVAS reported missing required observables or files.")
        if "digital_verilog_syntax" in note:
            issue = note.split("digital_verilog_syntax=")[-1].split(" in ")[0] if "digital_verilog_syntax=" in note else note
            if "sv_param_header" in issue:
                note_hints.extend([
                    "- **CRITICAL: SystemVerilog parameterized header detected** (`module foo #(...)`). Spectre VACOMP rejects this.",
                    "- Fix: declare parameters inside the module body with `parameter real/integer name = value;`",
                    "- Correct: `module foo(port_a, port_b); parameter integer div = 4;`",
                ])
            if "digital_reg_decl" in issue:
                note_hints.extend([
                    "- **CRITICAL: `reg` keyword detected**. Verilog-A has no `reg` type — Spectre VACOMP rejects it.",
                    "- Fix: replace every `reg` variable with `integer` (for counters/flags/state) or `real` (for analog values).",
                    "  - Before: `reg clk_out_reg; reg lock_reg;`",
                    "  - After:  `integer clk_out_reg; integer lock_reg;`",
                ])
            if "digital_always_block" in issue:
                note_hints.extend([
                    "- **CRITICAL: `always @(` block detected**. Verilog-A uses `analog begin` with `@(cross(...))` events.",
                    "- Fix: replace `always @(posedge clk)` with `@(cross(V(clk) - vth, +1))` inside `analog begin`.",
                ])
            if "packed_bit_select" in issue:
                note_hints.extend([
                    "- **CRITICAL: bit-select indexing `var[N]` detected** (e.g. `div_val[0] = ...`). Verilog-A does not support packed bit arrays on `integer` variables.",
                    "- Fix: do NOT index an integer with `[N]`. Read individual bits by testing membership or using helper integers:",
                    "  - Before: `div_val[0] = (V(d[0]) > vth) ? 1 : 0;`",
                    "  - After:  `integer b0; b0 = (V(d[0]) > vth) ? 1 : 0; div_val = div_val | b0;`",
                    "  - Or unroll: `div_val = 0; if (V(d[0])>vth) div_val=div_val+1; if (V(d[1])>vth) div_val=div_val+2; ...`",
                ])
            if "shift_operator" in issue:
                note_hints.extend([
                    "- **CRITICAL: shift operator `<<` or `>>` on a `reg` variable**. These are invalid Verilog-A.",
                    "- Fix: replace `reg` with `integer`; `<<`/`>>` on `integer` is valid Verilog-A.",
                    "  - Before: `reg [7:0] cnt; cnt >> 1`",
                    "  - After:  `integer cnt; cnt / 2`  (or keep `>>` once `reg` is gone)",
                ])

        # generated_include: TB includes a specific file — check DUT consistency
        if note.startswith("generated_include=") and family == "end-to-end":
            import re as _re
            inc_match = _re.search(r"generated_include=(.+)", note)
            inc_file = inc_match.group(1).strip() if inc_match else None
            if inc_file:
                note_hints.extend([
                    f"- **DUT-TB include mismatch risk.** Your previous TB used `ahdl_include \"{inc_file}\"`.",
                    "- The Spectre scorer checks that this filename matches the actual generated DUT file.",
                    "- **The DUT file is saved as `<module_name>.va`.** If your DUT module is `lfsr`, the file is `lfsr.va`.",
                    f"- Ensure your new TB uses `ahdl_include \"<your_module_name>.va\"` — not `{inc_file}` unless that exactly matches your module name.",
                ])

        # evas_compile_errors: surface raw EVAS compile lines to the LLM
        if note.startswith("evas_compile_errors:"):
            error_text = note[len("evas_compile_errors:"):].strip()
            note_hints.extend([
                "- **EVAS reported the following compile error(s):**",
                *[f"  `{line.strip()}`" for line in error_text.split("|") if line.strip()],
                "- Fix the syntax or declaration issue indicated above before addressing anything else.",
            ])

    # === NEW: Automated diagnosis translation ===
    # Translate behavioral diagnostic messages into specific repair suggestions
    diagnosis_sections: list[str] = []
    csv_signal_lines: list[str] = []
    for note in notes:
        # Collect CSV signal summary lines separately
        if note.startswith("csv_signal:"):
            csv_signal_lines.append(note[len("csv_signal:"):].strip())
            continue
        # Skip compile-related notes (already handled above)
        if any(kw in note for kw in ["undefined_module", "colon_instance", "conditional_transition", "no_ahdl", "spectre_strict", "evas_compile_errors"]):
            continue
        # Use diagnosis translation system
        translation = translate_diagnosis(note, task_id)
        if translation["diagnosis"]:
            section = f"\n### Diagnostic: `{note}`\n\n{format_repair_section(translation)}"
            diagnosis_sections.append(section)

        # Behavioral correctness hints are now handled by diagnosis_translation system
        # (see DIAGNOSIS_RULES in diagnosis_translation.py)

    if note_hints:
        deduped: list[str] = []
        seen = set()
        for item in note_hints:
            if item not in seen:
                deduped.append(item)
                seen.add(item)
        lines.extend(["", "Compile-related repair hints:"])
        lines.extend(deduped)

    observable_template_lines = _observable_scalar_alias_template(task_id, notes)
    if observable_template_lines and "# Reusable Repair Skeleton: Observable Scalar CSV Alias" not in "\n".join(lines):
        lines.extend(observable_template_lines)

    post_reset_template_lines = _post_reset_sample_budget_template(task_id, notes, sample_dir)
    if post_reset_template_lines and "# Reusable Repair Skeleton: Post-Reset Sample Budget" not in "\n".join(lines):
        lines.extend(post_reset_template_lines)

    reset_hold_lines = _reset_hold_contract_template(task_id, notes, sample_dir)
    if reset_hold_lines and "# Reusable Repair Skeleton: Reset Release Must Persist" not in "\n".join(lines):
        lines.extend(reset_hold_lines)

    settle_lines = _clocked_output_settle_template(task_id, notes, sample_dir)
    if settle_lines and "# Reusable Repair Skeleton: Clocked Digital Output Settling" not in "\n".join(lines):
        lines.extend(settle_lines)

    # Add diagnosis-translated sections
    if diagnosis_sections:
        lines.extend(["", "# Behavioral Diagnosis Analysis", "", "Below are specific diagnostic findings from EVAS simulation and their repair suggestions:"])
        lines.extend(diagnosis_sections)

    subtype_policy_lines = _subtype_specific_repair_policy(task_id, notes, status)
    if subtype_policy_lines:
        lines.extend(subtype_policy_lines)

    dwa_plan_lines = _dwa_plan_execute_section(task_id, notes)
    if dwa_plan_lines:
        lines.extend(dwa_plan_lines)

    # Add CSV signal waveform summary when sim_correct failed
    if csv_signal_lines:
        lines.extend([
            "",
            "# Observed Waveform Summary (from EVAS tran.csv)",
            "",
            "The following signal statistics were measured from the simulation output.",
            "Use these to understand what the circuit actually produced and identify the functional bug:",
            "",
        ])
        for sig_line in csv_signal_lines:
            lines.append(f"- {sig_line}")
        lines.extend([
            "",
            "Compare these values against the expected behaviour described in the task to identify",
            "which signal is incorrect and what the root cause is (wrong threshold, missing edge, wrong polarity, etc.).",
        ])

    # Parse structure_diagnosis for additional repair hints
    diag = evas_result.get("structure_diagnosis")
    if diag:
        missing_modules = diag.get("missing_modules", [])
        extra_modules = diag.get("extra_modules", [])
        missing_signals = diag.get("missing_signals", [])
        extra_signals = diag.get("extra_signals", [])

        if missing_modules:
            expected = ", ".join(missing_modules)
            actual = ", ".join(extra_modules) or "<none>"
            lines.extend([
                "",
                "Module mismatch:",
                f"- Expected modules (from gold testbench): {expected}",
                f"- Your generated modules: {actual}",
                "- Align your ahdl_include directives and module names with the gold testbench structure.",
            ])

        if missing_signals:
            expected_sig = ", ".join(missing_signals)
            actual_sig = ", ".join(extra_signals[:10]) or "<different names>"
            lines.extend([
                "",
                "**Signal naming mismatch**:",
                f"- Expected save signals (from gold testbench): {expected_sig}",
                f"- Your CSV columns: {actual_sig}",
                "- **Fix: Rename your signals in the save statement to match expected names exactly.**",
                "- Example: If gold expects `not_a`, change `a_not` or `not_dut:A` to `not_a`.",
            ])

    shape_text = _end_to_end_shape_guidance(task_prompt, family)
    if shape_text:
        lines.extend(["", shape_text])

    # Inject Skill circuit-specific knowledge ONLY for behavioral errors (condition E)
    # Do NOT inject for FAIL_INFRA (missing files) — prioritize file generation first
    # Condition D: include_skill=False → no Skill injection
    if include_skill and status in ("FAIL_SIM_CORRECTNESS", "FAIL_DUT_COMPILE", "FAIL_TB_COMPILE"):
        skill_ref_lines = _inject_skill_reference(task_id)
        if skill_ref_lines:
            lines.extend(skill_ref_lines)

    # Inject checks.yaml expected behavior (Checker source) for behavioral errors
    # This is always included for both conditions D and E (Checker is fixed)
    if status == "FAIL_SIM_CORRECTNESS":
        check_lines = _inject_check_expectations(task_dir)
        if check_lines:
            lines.extend(check_lines)

    return "\n".join(lines)


def build_generic_retry_prompt(
    task_dir: Path,
    sample_dir: Path,
    *,
    skill_bundle_text: str | None = None,
) -> str:
    """Build a no-diagnostics retry prompt.

    This is the matched-budget control: it gives the model one extra chance and
    the previous files, but no EVAS failure attribution or validation notes.
    """
    meta = read_meta(task_dir)
    family = meta.get("family", "end-to-end")
    original_prompt = build_prompt(task_dir)
    candidate_text = "\n\n".join(_candidate_sections(sample_dir))
    skill_text = _skill_section(skill_bundle_text)
    shape_text = _end_to_end_shape_guidance(original_prompt, family)
    return textwrap.dedent(f"""\
        You are doing a generic second attempt for the same benchmark task.

        Important fairness rule:
        - You may inspect the previous candidate files below.
        - You are NOT given simulator diagnostics or validator feedback.
        - Produce a complete replacement answer that follows the original task.

        Artifact contract:
        {_artifact_contract(family)}

        Output rules:
        - Output code blocks only.
        - Do not include explanations outside code blocks.
        - Preserve required module names, port order, parameters, and observable names from the original task.
        - Use EVAS/Spectre-compatible voltage-domain Verilog-A only.
        - Do not use current-domain operators such as I(), ddt(), idt(), or laplace_*.
        - Avoid Verilog initial blocks; initialize inside analog @(initial_step).
        - Keep transition() contributions continuous rather than inside conditional begin/end branches.
        {shape_text}

        {skill_text}

        # Original Task Prompt

        {original_prompt.strip()}

        # Previous Candidate Files

        {candidate_text}
    """).strip() + "\n"


def build_skill_only_prompt(
    task_dir: Path,
    *,
    skill_bundle_text: str,
) -> str:
    meta = read_meta(task_dir)
    family = meta.get("family", "end-to-end")
    original_prompt = build_prompt(task_dir)
    skill_text = _skill_section(skill_bundle_text)
    shape_text = _end_to_end_shape_guidance(original_prompt, family)
    return textwrap.dedent(f"""\
        You are generating a benchmark candidate using a frozen Verilog-A skill bundle.

        Artifact contract:
        {_artifact_contract(family)}

        Output rules:
        - Output code blocks only.
        - Do not include explanations outside code blocks.
        - Preserve required module names, port order, parameters, and observable names from the original task.
        - Follow the frozen skill bundle strictly.
        {shape_text}

        {skill_text}

        # Original Task Prompt

        {original_prompt.strip()}
    """).strip() + "\n"


def build_evas_assisted_prompt(
    task_dir: Path,
    sample_dir: Path,
    evas_result: dict,
    *,
    skill_bundle_text: str | None = None,
) -> str:
    """Build a targeted repair prompt using EVAS status, scores, and notes."""
    meta = read_meta(task_dir)
    family = meta.get("family", "end-to-end")
    original_prompt = build_prompt(task_dir)
    candidate_text = "\n\n".join(_candidate_sections(sample_dir))
    score_text = _score_summary(evas_result)
    skill_text = _skill_section(skill_bundle_text)
    shape_text = _end_to_end_shape_guidance(original_prompt, family)
    status = evas_result.get("status", "FAIL_OTHER")
    task_id = meta.get("task_id", meta.get("id", task_dir.name))
    notes = evas_result.get("evas_notes") or evas_result.get("notes") or []
    contract_diagnosis_text = _behavior_contract_diagnosis_section(task_dir, evas_result)

    if status == "FAIL_DUT_COMPILE":
        focus = (
            "Focus first on Verilog-A DUT syntax, module/interface mismatch, "
            "unsupported AHDL constructs, and banned operators."
        )
    elif status == "FAIL_TB_COMPILE":
        focus = (
            "Focus first on Spectre testbench syntax, ahdl_include paths, DUT "
            "instance name/port order, stimulus sources, save directives, and "
            "observable naming."
        )
    elif status == "FAIL_SIM_CORRECTNESS":
        sim_subtype, _ = _classify_sim_correct_failure(notes, task_id)
        if sim_subtype == "observability_contract":
            focus = (
                "Focus first on observability/contract mismatches: save names, "
                "required signals, and checker-visible waveform columns. Keep DUT "
                "semantics stable until contract alignment is fixed."
            )
        elif sim_subtype == "simulation_artifact":
            focus = (
                "Focus first on simulation artifact recovery: produce stable tran.csv "
                "with valid run settings and complete includes before semantic tuning."
            )
        else:
            focus = (
                "Focus first on behavioral semantics. Decide whether the mismatch is "
                "DUT logic, stimulus inadequacy, reset/bring-up sequencing, or timing thresholds."
            )
    else:
        focus = (
            "Focus first on missing files, malformed code blocks, infrastructure "
            "compatibility, and preserving the required artifact contract."
        )

    return textwrap.dedent(f"""\
        You are repairing a generated Verilog-A/Spectre benchmark candidate using EVAS validator feedback.

        Repair focus:
        {focus}

        Artifact contract:
        {_artifact_contract(family)}

        Output rules:
        - Output complete replacement code blocks only.
        - Do not include explanations outside code blocks.
        - Preserve required module names, port order, parameters, and observable names from the original task.
        - Use EVAS/Spectre-compatible voltage-domain Verilog-A only.
        - Do not use current-domain operators such as I(), ddt(), idt(), or laplace_*.
        - Avoid Verilog initial blocks; initialize inside analog @(initial_step).
        - Keep transition() contributions continuous rather than inside conditional begin/end branches.
        - Prefer the smallest semantic change that addresses the validator failure.
        {shape_text}

        {skill_text}

        # EVAS Result

        {score_text.strip()}

        {contract_diagnosis_text}

        # Original Task Prompt

        {original_prompt.strip()}

        # Current Candidate Files

        {candidate_text}
    """).strip() + "\n"


def _history_section(history: list[dict], current_status: str = "FAIL") -> str:
    if not history:
        return ""

    lines = ["# Previous Repair Attempts", ""]
    lines.append("Use the summaries below to continue the search from the best-so-far candidate instead of repeating failed edits.")
    lines.append("")

    status_history = [(entry.get("round", "?"), entry.get("status", "?")) for entry in history]
    status_str = " → ".join(f"R{round_idx}:{status}" for round_idx, status in status_history)
    lines.append(f"**Status progression**: {status_str} → R{len(history)+1}:{current_status} (target: PASS)")
    lines.append("")

    for entry in history[-3:]:
        round_idx = entry.get("round", "?")
        scores = entry.get("scores", {})
        compared_to = entry.get("compared_to_round", 0)
        progress_label = entry.get("progress_label", "unknown")
        lines.append(
            f"- R{round_idx} vs `{('baseline' if compared_to == 0 else f'R{compared_to}')}`: "
            f"status={entry.get('status', '?')}, "
            f"weighted_total={float(scores.get('weighted_total', 0.0)):.3f}, "
            f"sim_correct={float(scores.get('sim_correct', 0.0)):.3f}, "
            f"loop_state={progress_label}"
        )
        progress_summary = entry.get("progress_summary")
        if progress_summary:
            lines.append(f"  {progress_summary}")

        metric_gap = entry.get("metric_gap", {})
        if metric_gap:
            lines.append(
                "  Closeness: "
                f"matched_metrics={metric_gap.get('matched', 0)}, "
                f"violated_metrics={metric_gap.get('violated', 0)}, "
                f"gap_sum={float(metric_gap.get('gap_sum', 0.0)):.4g}"
            )

        metrics = entry.get("metrics", {})
        if metrics:
            preview_items = []
            for key in sorted(metrics)[:4]:
                preview_items.append(f"{key}={_format_scalar(metrics[key])}")
            if preview_items:
                lines.append(f"  Metrics snapshot: {', '.join(preview_items)}")

    return "\n".join(lines)


def build_evas_guided_repair_prompt(
    task_dir: Path,
    sample_dir: Path,
    evas_result: dict,
    *,
    history: list[dict] | None = None,
    include_skill: bool = True,
    include_contract_diagnosis: bool = True,
    public_spec_mode: str = "legacy-extracted",
    loop_context: dict | None = None,
) -> str:
    """Build a targeted repair prompt.

    Args:
        history: list of previous round result dicts (each has 'round', 'evas_notes').
                 When provided, accumulated constraints are included to prevent oscillation.
        include_skill: If True, inject Skill circuit knowledge.
                       If False, use Checker + EVAS diagnosis only.
        include_contract_diagnosis: If True, include optional task-local
            contract diagnosis. Disable for clean F-style EVAS-only repair.
        public_spec_mode: Forwarded to generate.build_prompt so repair rounds
            can use the same public prompt/spec condition as initial generation.
    """
    meta = read_meta(task_dir)
    family = meta.get("family", "end-to-end")
    original_prompt = build_prompt(task_dir, public_spec_mode=public_spec_mode)
    candidate_text = "\n\n".join(_candidate_sections(sample_dir))
    score_text = _score_summary(evas_result)
    targeted_skill_text = _targeted_repair_skill(task_dir, evas_result, include_skill=include_skill, sample_dir=sample_dir)
    loop_state_text = _loop_state_section(task_dir, evas_result, history or [], loop_context)
    history_text = _history_section(history or [], current_status=evas_result.get("status", "FAIL"))
    notes = evas_result.get("evas_notes") or evas_result.get("notes") or []
    diagnostic_retention_text = _diagnostic_retention_section(notes, history or [])
    contract_diagnosis_text = (
        _behavior_contract_diagnosis_section(task_dir, evas_result)
        if include_contract_diagnosis
        else ""
    )
    circuit_rag_text = _circuit_mechanism_rag_section(task_dir, evas_result)
    lego_skill_text = _lego_mechanism_skill_section(task_dir, evas_result)

    skill_label = "Checker + EVAS + Skill" if include_skill else "Checker + EVAS only"

    return textwrap.dedent(f"""\
        You are repairing a generated Verilog-A/Spectre benchmark candidate using EVAS validator feedback and a targeted repair skill ({skill_label}).

        Artifact contract:
        {_artifact_contract(family)}

        Output rules:
        - Output complete replacement code blocks only.
        - Do not include explanations outside code blocks.
        - Preserve required module names, port order, parameters, and observable names from the original task.
        - Apply the targeted repair skill below instead of doing a broad rewrite.
        - Prefer the smallest change that resolves the EVAS-reported failure; copy unchanged code exactly when possible.
        - If the current candidate already compiles, do not change syntax style, module boundaries, or testbench structure unless EVAS identifies that layer as the failure.
        - While fixing the current failure, do NOT revert any fix that resolved a prior round's failure.

        {targeted_skill_text}

        {diagnostic_retention_text}

        {contract_diagnosis_text}

        {circuit_rag_text}

        {lego_skill_text}

        # EVAS Result

        {score_text.strip()}

        {loop_state_text}

        {history_text}

        # Original Task Prompt

        {original_prompt.strip()}

        # Current Candidate Files

        {candidate_text}
    """).strip() + "\n"


def build_prompt_from_paths(
    *,
    mode: str,
    task_dir: Path,
    sample_dir: Path,
    evas_result_path: Path | None,
    skill_bundle_path: Path | None,
) -> str:
    skill_bundle_text = load_skill_bundle(skill_bundle_path) if skill_bundle_path else None
    if mode == "generic-retry":
        return build_generic_retry_prompt(task_dir, sample_dir, skill_bundle_text=skill_bundle_text)
    if mode == "skill-only":
        if not skill_bundle_text:
            raise ValueError("skill-only prompt requires --skill-bundle")
        return build_skill_only_prompt(task_dir, skill_bundle_text=skill_bundle_text)
    if mode == "skill-evas-informed":
        if not evas_result_path:
            raise ValueError("skill-evas-informed prompt requires --evas-result")
        if not skill_bundle_text:
            raise ValueError("skill-evas-informed prompt requires --skill-bundle")
        return build_evas_assisted_prompt(
            task_dir,
            sample_dir,
            _read_json(evas_result_path),
            skill_bundle_text=skill_bundle_text,
        )
    if mode == "evas-guided-repair":
        if not evas_result_path:
            raise ValueError("evas-guided-repair prompt requires --evas-result")
        return build_evas_guided_repair_prompt(task_dir, sample_dir, _read_json(evas_result_path), include_skill=True)
    if mode == "evas-guided-repair-no-skill":
        # Experiment condition D: Checker + EVAS only (no Skill)
        if not evas_result_path:
            raise ValueError("evas-guided-repair-no-skill prompt requires --evas-result")
        return build_evas_guided_repair_prompt(task_dir, sample_dir, _read_json(evas_result_path), include_skill=False)
    if not evas_result_path:
        raise ValueError("evas-assisted prompt requires --evas-result")
    return build_evas_assisted_prompt(
        task_dir,
        sample_dir,
        _read_json(evas_result_path),
        skill_bundle_text=skill_bundle_text,
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="Build prompts for mainline retry / skill / EVAS-assisted modes.")
    ap.add_argument(
        "--mode",
        choices=["generic-retry", "evas-assisted", "skill-only", "skill-evas-informed", "evas-guided-repair", "evas-guided-repair-no-skill"],
        required=True,
        help="Mode: evas-guided-repair (condition E: +Skill) or evas-guided-repair-no-skill (condition D: no Skill)",
    )
    ap.add_argument("--task-dir", required=True)
    ap.add_argument("--sample-dir", required=True)
    ap.add_argument("--evas-result", default="")
    ap.add_argument("--skill-bundle", default="")
    ap.add_argument("--output", default="", help="Write prompt to this file. Defaults to stdout.")
    args = ap.parse_args()

    prompt = build_prompt_from_paths(
        mode=args.mode,
        task_dir=Path(args.task_dir),
        sample_dir=Path(args.sample_dir),
        evas_result_path=Path(args.evas_result) if args.evas_result else None,
        skill_bundle_path=Path(args.skill_bundle) if args.skill_bundle else None,
    )
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(prompt, encoding="utf-8")
        print(out)
    else:
        print(prompt, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
