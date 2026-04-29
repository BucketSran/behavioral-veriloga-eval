#!/usr/bin/env python3
"""Audit a minimal circuit-mechanism RAG layer.

This is a no-API, no-gold experiment.  It tests whether public prompt semantics
plus inferred functional IR can retrieve useful circuit-mechanism knowledge
from three current sources:

1. existing contract repair cards;
2. prompt-inferred checker templates;
3. gold/R26 mechanism templates that were parameter-perturbation validated.

It does not claim repair pass rate.  It is a routing/retrieval audit before
spending model calls on a RAG-guided repair loop.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from contract_repair_cards import select_contract_repair_cards
from infer_prompt_checker_specs import infer_specs
from run_mechanism_generalization_benchmark import CASES as GENERALIZATION_CASES
from run_mechanism_generalization_benchmark import Case as GeneralizationCase
from run_mechanism_generalization_benchmark import _synthetic_report


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "results" / "circuit-mechanism-rag-audit-2026-04-29"
CARD_PATH = ROOT / "docs" / "CONTRACT_REPAIR_CARDS.json"
ADOPTED_SPECS = ROOT / "docs" / "PROMPT_CHECKER_SPECS_ADOPTED.json"
R26_TEMPLATES = ROOT / "results" / "gold-r26-template-generalization-2026-04-29" / "gold_r26_mechanism_templates.json"
SKELETONS = ROOT / "docs" / "CIRCUIT_MECHANISM_SKELETONS.json"
SKILL_CATEGORY_ROOT = ROOT.parent / "veriloga-skills" / "veriloga" / "references" / "categories"


@dataclass(frozen=True)
class KnowledgeNode:
    node_id: str
    kind: str
    title: str
    text: str
    source: str
    tags: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RagCase:
    case_id: str
    axis: str
    prompt: str
    required_node_any: tuple[str, ...]
    forbidden_node_any: tuple[str, ...] = ()
    note: str = ""


def _tokens(text: str) -> list[str]:
    pieces = re.findall(r"[A-Za-z0-9_]+", text.lower())
    out: list[str] = []
    for piece in pieces:
        out.append(piece)
        out.extend(part for part in piece.split("_") if part and part != piece)
    return [tok for tok in out if len(tok) > 1]


def _flatten_json(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    if isinstance(value, list):
        return " ".join(_flatten_json(item) for item in value)
    if isinstance(value, dict):
        return " ".join(f"{key} {_flatten_json(val)}" for key, val in value.items())
    return str(value)


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _card_nodes() -> list[KnowledgeNode]:
    data = _read_json(CARD_PATH)
    nodes: list[KnowledgeNode] = []
    for card in data.get("cards", []):
        match = card.get("match", {})
        text = " ".join(
            [
                str(card.get("id", "")),
                str(card.get("title", "")),
                _flatten_json(match),
                " ".join(str(item) for item in card.get("text", [])),
            ]
        )
        tags = tuple(sorted(set(_tokens(_flatten_json(match)))))
        nodes.append(
            KnowledgeNode(
                node_id=f"card:{card.get('id')}",
                kind="repair_card",
                title=str(card.get("title", card.get("id", ""))),
                text=text,
                source=str(card.get("source", CARD_PATH)),
                tags=tags,
                metadata={"match": match},
            )
        )
    return nodes


def _template_nodes() -> list[KnowledgeNode]:
    by_template: dict[str, dict[str, Any]] = {}

    def add_template(name: str, *, task: str = "", evidence: str = "", signals: str = "") -> None:
        if not name:
            return
        bucket = by_template.setdefault(name, {"tasks": set(), "evidence": [], "signals": []})
        if task:
            bucket["tasks"].add(task)
        if evidence:
            bucket["evidence"].append(evidence)
        if signals:
            bucket["signals"].append(signals)

    if ADOPTED_SPECS.exists():
        for spec in _read_json(ADOPTED_SPECS).get("specs", []):
            for template in spec.get("templates", []):
                name = str(template.get("template", "") or "")
                add_template(
                    name,
                    task=str(spec.get("task_id", "")),
                    evidence=" ".join(str(item) for item in template.get("evidence", [])),
                    signals=_flatten_json(template.get("signals", {})),
                )

    # The adopted spec catalog only contains templates seen in real tasks.
    # Add templates that are declared in cards or in the no-leak synthetic
    # benchmark so the RAG layer can retrieve mechanism names directly.
    for card in _read_json(CARD_PATH).get("cards", []):
        match = card.get("match", {})
        evidence = " ".join([str(card.get("id", "")), str(card.get("title", "")), " ".join(card.get("text", []))])
        for key in ("prompt_template_any", "prompt_template_all"):
            for name in match.get(key, []) or []:
                add_template(str(name), evidence=evidence)
    for case in GENERALIZATION_CASES:
        for name in [*case.required_templates, *case.forbidden_templates]:
            add_template(str(name), task=case.case_id, evidence=case.prompt[:500])
    nodes: list[KnowledgeNode] = []
    for name, info in sorted(by_template.items()):
        tasks = sorted(info["tasks"])
        text = " ".join([name, " ".join(info["evidence"]), " ".join(info["signals"]), " ".join(tasks[:10])])
        nodes.append(
            KnowledgeNode(
                node_id=f"template:{name}",
                kind="prompt_template",
                title=name,
                text=text,
                source=str(ADOPTED_SPECS),
                tags=tuple(sorted(set(_tokens(text)))),
                metadata={"task_count": len(tasks), "example_tasks": tasks[:10]},
            )
        )
    return nodes


def _r26_nodes() -> list[KnowledgeNode]:
    if not R26_TEMPLATES.exists():
        return []
    nodes: list[KnowledgeNode] = []
    for template in _read_json(R26_TEMPLATES).get("templates", []):
        template_id = str(template.get("template_id", ""))
        family = str(template.get("family", ""))
        text = " ".join(
            [
                template_id,
                family,
                str(template.get("source_task", "")),
                str(template.get("mechanism_summary", "")),
                _flatten_json(template.get("variant_params", [])),
            ]
        )
        nodes.append(
            KnowledgeNode(
                node_id=f"r26:{template_id}",
                kind="r26_template",
                title=template_id,
                text=text,
                source=str(R26_TEMPLATES),
                tags=tuple(sorted(set(_tokens(text)))),
                metadata=template,
            )
        )
    return nodes


def _skeleton_nodes() -> list[KnowledgeNode]:
    if not SKELETONS.exists():
        return []
    nodes: list[KnowledgeNode] = []
    for skeleton in _read_json(SKELETONS).get("skeletons", []):
        skeleton_id = str(skeleton.get("id", ""))
        match = skeleton.get("match", {})
        text = " ".join(
            [
                skeleton_id,
                str(skeleton.get("title", "")),
                _flatten_json(match),
                _flatten_json(skeleton.get("slot_schema", {})),
                " ".join(str(item) for item in skeleton.get("implementation_skeleton", [])),
                " ".join(str(item) for item in skeleton.get("veriloga_shape", [])),
                " ".join(str(item) for item in skeleton.get("anti_patterns", [])),
            ]
        )
        tags = tuple(sorted(set(_tokens(_flatten_json(match)))))
        nodes.append(
            KnowledgeNode(
                node_id=f"skeleton:{skeleton_id}",
                kind="mechanism_skeleton",
                title=str(skeleton.get("title", skeleton_id)),
                text=text,
                source=str(SKELETONS),
                tags=tags,
                metadata=skeleton,
            )
        )
    return nodes


def _skill_nodes(max_chars: int = 6000) -> list[KnowledgeNode]:
    nodes: list[KnowledgeNode] = []
    if not SKILL_CATEGORY_ROOT.exists():
        return nodes
    for path in sorted(SKILL_CATEGORY_ROOT.glob("*.md")):
        text = path.read_text(encoding="utf-8", errors="ignore")[:max_chars]
        nodes.append(
            KnowledgeNode(
                node_id=f"skill:{path.stem}",
                kind="veriloga_skill",
                title=path.stem,
                text=f"{path.stem}\n{text}",
                source=str(path),
                tags=tuple(sorted(set(_tokens(f"{path.stem} {text}")))),
            )
        )
    return nodes


def build_knowledge_base(include_skills: bool = True) -> list[KnowledgeNode]:
    nodes = []
    nodes.extend(_card_nodes())
    nodes.extend(_template_nodes())
    nodes.extend(_r26_nodes())
    nodes.extend(_skeleton_nodes())
    if include_skills:
        nodes.extend(_skill_nodes())
    return nodes


def _idf(nodes: list[KnowledgeNode]) -> dict[str, float]:
    df: Counter[str] = Counter()
    for node in nodes:
        df.update(set(_tokens(node.text)) | set(node.tags))
    total = max(len(nodes), 1)
    return {tok: math.log((1 + total) / (1 + count)) + 1.0 for tok, count in df.items()}


def _query_text(prompt: str, record: dict, report: dict) -> str:
    claims = [str(item.get("type", "")) for item in record.get("functional_ir", {}).get("claims", []) if isinstance(item, dict)]
    templates = [str(item.get("template", "")) for item in record.get("templates", []) if isinstance(item, dict)]
    parts = [
        prompt,
        "functional_claims " + " ".join(claims),
        "prompt_templates " + " ".join(templates),
        "failed_contracts " + " ".join(str(item) for item in report.get("failed_contracts", [])),
        "failed_hard_contracts " + " ".join(str(item) for item in report.get("failed_hard_contracts", [])),
        "repair_families " + " ".join(str(item.get("repair_family", "")) for item in report.get("contract_results", [])),
    ]
    return "\n".join(parts)


def retrieve(nodes: list[KnowledgeNode], query: str, *, top_k: int = 5) -> list[dict[str, Any]]:
    idf = _idf(nodes)
    q_tokens = _tokens(query)
    q_counts = Counter(q_tokens)
    q_set = set(q_tokens)
    query_l = query.lower()
    results: list[dict[str, Any]] = []
    for node in nodes:
        if _query_negates_node(query_l, node):
            continue
        node_tokens = _tokens(node.text)
        node_counts = Counter(node_tokens)
        overlap = q_set & (set(node_tokens) | set(node.tags))
        lexical = sum(idf.get(tok, 1.0) * min(q_counts[tok], node_counts.get(tok, 1) or 1) for tok in overlap)
        lexical = lexical / math.sqrt(max(len(set(node_tokens)), 1))
        exact_boost = 0.0
        for tag in node.tags:
            if tag in q_set:
                exact_boost += 0.5
        # Prefer compact mechanism nodes over broad skill documents when scores tie.
        kind_boost = {
            "mechanism_skeleton": 3.25,
            "repair_card": 3.0,
            "r26_template": 2.5,
            "prompt_template": 2.0,
            "veriloga_skill": 0.25,
        }.get(node.kind, 0.0)
        score = lexical + exact_boost + kind_boost
        if score <= 0:
            continue
        results.append(
            {
                "node_id": node.node_id,
                "kind": node.kind,
                "title": node.title,
                "score": round(score, 4),
                "source": node.source,
                "overlap": sorted(overlap)[:20],
            }
        )
    results.sort(key=lambda item: (-float(item["score"]), str(item["node_id"])))
    return results[:top_k]


def _query_negates_node(query_l: str, node: KnowledgeNode) -> bool:
    query_l = re.sub(r"\s+", " ", query_l)
    node_l = f"{node.node_id} {node.title} {node.text}".lower()
    binary_code = (
        "binary" in query_l
        or "unsigned integer" in query_l
        or "binary-weighted" in query_l
        or bool(re.search(r"\b\d+\s*[- ]?\s*bit\s+(?:digital\s+)?code\b", query_l))
        or bool(re.search(r"\bcode\s+bits?\b", query_l))
    )
    count_style = any(word in query_l for word in ("population count", "count of", "how many", "thermometer", "unary", "unit-cell", "unit cell"))
    if (
        "not a thermometer" in query_l
        or "not thermometer" in query_l
        or "not a unary" in query_l
        or "not unary" in query_l
        or (binary_code and not count_style and "thermometer" not in query_l)
    ) and (
        "thermometer" in node_l or "unary" in node_l
    ) and "dwa" not in node_l:
        return True
    if ("no instance parameter override" in query_l or "no parameter override" in query_l or "there are no instance parameter" in query_l) and (
        "parameterized_event_sequence" in node_l or "parameterized_pulse" in node_l or "instance override" in node_l
    ):
        return True
    if "binary counter" in query_l and "may flip multiple" in query_l and ("gray" in node_l or "one_bit_adjacent" in node_l):
        return True
    data_clock = ("data" in query_l or "edge_data" in query_l or "data_i" in query_l) and ("clock" in query_l or "clk" in query_l)
    ref_div = ("ref" in query_l or "reference" in query_l) and ("div" in query_l or "feedback" in query_l)
    if data_clock and not ref_div and "pfd_paired_up_dn_pulses" in node_l:
        return True
    if ("arbitrary" in query_l and ("no ordering" in query_l or "ordering guarantee" in query_l)) and (
        "ordered_transfer" in node_l or "thermometer" in node_l or "monotonic_code" in node_l
    ):
        return True
    return False


def _adopted_templates(record: dict, threshold: float) -> list[str]:
    return [
        str(spec.get("template"))
        for spec in record.get("templates", [])
        if float(spec.get("confidence", 0.0)) >= threshold
    ]


def _case_expected_nodes(case: GeneralizationCase) -> tuple[set[str], set[str]]:
    required = {f"card:{item}" for item in case.required_cards}
    required.update(f"template:{item}" for item in case.required_templates)
    forbidden = {f"card:{item}" for item in case.forbidden_cards}
    forbidden.update(f"template:{item}" for item in case.forbidden_templates)
    text = f"{case.case_id}\n{case.prompt}".lower()
    if "adc" in text and "dac" in text:
        required.add("r26:adc_dac_quantize_reconstruct")
        required.add("card:adc_dac_reconstruction_chain")
        required.add("card:adc_dac_system_quantize_reconstruct_graph")
    if "dwa" in text or ("pointer" in text and "cell" in text):
        required.add("r26:dwa_rotating_pointer_window")
        required.add("card:dwa_pointer_cell_enable_activity")
        required.add("card:dwa_system_rotating_window_graph")
    if "pfd" in text or ("ref" in text and "div" in text and "up" in text and ("dn" in text or "down" in text)):
        required.add("r26:pfd_mutual_exclusion_pulse_windows")
        required.add("card:pfd_paired_up_dn_pulses")
        required.add("card:pfd_windowed_latched_pulse_symmetry")
    if "pll" in text or ("feedback" in text and "lock" in text and "divider" in text):
        required.add("r26:pll_feedback_cadence_lock")
        required.add("card:pll_feedback_ratio_stage")
        required.add("card:pll_lock_after_stable_ratio_stage")
        required.add("card:pll_system_feedback_graph")
    return required, forbidden


EXTRA_RAG_CASES = [
    RagCase(
        case_id="pll_ref_period_ratio_lock_variant",
        axis="r26_near_neighbor",
        required_node_any=(
            "r26:pll_feedback_cadence_lock",
            "card:pll_feedback_ratio_stage",
            "card:pll_lock_after_stable_ratio_stage",
            "card:pll_system_feedback_graph",
            "template:ratio_edge_window",
            "template:ratio_hop_window",
            "template:lock_after_ratio_stable",
        ),
        prompt="""
        Build a voltage-domain ADPLL timing model.  It receives `ref_clk`,
        generates a DCO clock, divides that clock by public parameter
        `div_ratio`, and exposes `fb_clk` and `lock`.  When the reference period
        changes, feedback edge cadence should settle so the late-window ref/fb
        ratio is near one before lock asserts.
        """,
    ),
    RagCase(
        case_id="dwa_window_wrap_near_neighbor",
        axis="r26_near_neighbor",
        required_node_any=(
            "r26:dwa_rotating_pointer_window",
            "card:dwa_pointer_cell_enable_activity",
            "card:dwa_system_rotating_window_graph",
            "template:onehot_no_overlap",
        ),
        prompt="""
        Build a data-weighted averaging pointer generator.  Decode a public code
        into an active cell count, maintain a wrapped pointer over the unit-cell
        array, expose pointer bits and cell enable bits, and ensure the enabled
        cell window follows the pointer with wraparound.
        """,
    ),
    RagCase(
        case_id="pfd_edge_order_pulse_window_near_neighbor",
        axis="r26_near_neighbor",
        required_node_any=(
            "r26:pfd_mutual_exclusion_pulse_windows",
            "card:pfd_paired_up_dn_pulses",
            "card:pfd_windowed_latched_pulse_symmetry",
            "template:pulse_non_overlap",
            "template:paired_edge_response",
        ),
        prompt="""
        Build a phase-frequency detector with `ref`, `div`, `up`, and `dn`.
        REF-leading events should create bounded UP pulses, DIV-leading events
        should create bounded DN pulses, and the two outputs should not overlap.
        Pulse width is a parameter.
        """,
    ),
    RagCase(
        case_id="adc_dac_vdd_ramp_near_neighbor",
        axis="r26_near_neighbor",
        required_node_any=(
            "r26:adc_dac_quantize_reconstruct",
            "card:adc_dac_reconstruction_chain",
            "card:adc_dac_system_quantize_reconstruct_graph",
            "template:quantized_reconstruction",
        ),
        prompt="""
        Build an ADC-DAC round-trip model.  Quantize `vin` into output code bits
        over a public VDD/reference range and reconstruct `vout` from the same
        held code.  Changing VDD or ramp duration should preserve code coverage
        and monotonic reconstruction.
        """,
    ),
]


def _run_generalization_case(case: GeneralizationCase, *, out_root: Path, nodes: list[KnowledgeNode], threshold: float, top_k: int) -> dict[str, Any]:
    task_dir = out_root / "synthetic_tasks" / case.case_id
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "prompt.md").write_text(case.prompt, encoding="utf-8")
    record = infer_specs(case.case_id, task_dir)
    adopted = _adopted_templates(record, threshold)
    report = _synthetic_report(case.case_id, adopted)
    _enrich_report_with_prompt_semantics(report, record, adopted)
    rule_cards = select_contract_repair_cards(report, task_id=case.case_id, limit=3)
    retrieved = retrieve(nodes, _query_text(case.prompt, record, report), top_k=top_k)
    required, forbidden = _case_expected_nodes(case)
    top_ids = [str(item["node_id"]) for item in retrieved]
    return {
        "case_id": case.case_id,
        "axis": case.axis,
        "source": "mechanism_generalization_cases",
        "required_node_any": sorted(required),
        "forbidden_node_any": sorted(forbidden),
        "rule_cards": [str(card.get("id")) for card in rule_cards],
        "inferred_templates": adopted,
        "rag_top": retrieved,
        "rag_top1_hit": bool(required and top_ids[:1] and top_ids[0] in required),
        "rag_top3_hit": bool(required and any(node_id in required for node_id in top_ids[:3])),
        "rag_top5_hit": bool(required and any(node_id in required for node_id in top_ids[:5])),
        "rag_forbidden_top3": [node_id for node_id in top_ids[:3] if node_id in forbidden],
    }


def _run_extra_case(case: RagCase, *, out_root: Path, nodes: list[KnowledgeNode], threshold: float, top_k: int) -> dict[str, Any]:
    task_dir = out_root / "synthetic_tasks" / case.case_id
    task_dir.mkdir(parents=True, exist_ok=True)
    prompt = case.prompt.strip() + "\n"
    (task_dir / "prompt.md").write_text(prompt, encoding="utf-8")
    record = infer_specs(case.case_id, task_dir)
    adopted = _adopted_templates(record, threshold)
    report = _synthetic_report(case.case_id, adopted)
    _enrich_report_with_prompt_semantics(report, record, adopted)
    retrieved = retrieve(nodes, _query_text(prompt, record, report), top_k=top_k)
    top_ids = [str(item["node_id"]) for item in retrieved]
    required = set(case.required_node_any)
    forbidden = set(case.forbidden_node_any)
    return {
        "case_id": case.case_id,
        "axis": case.axis,
        "source": "extra_r26_near_neighbor_cases",
        "required_node_any": sorted(required),
        "forbidden_node_any": sorted(forbidden),
        "rule_cards": [],
        "inferred_templates": adopted,
        "rag_top": retrieved,
        "rag_top1_hit": bool(required and top_ids[:1] and top_ids[0] in required),
        "rag_top3_hit": bool(required and any(node_id in required for node_id in top_ids[:3])),
        "rag_top5_hit": bool(required and any(node_id in required for node_id in top_ids[:5])),
        "rag_forbidden_top3": [node_id for node_id in top_ids[:3] if node_id in forbidden],
        "note": case.note,
    }


def _enrich_report_with_prompt_semantics(report: dict[str, Any], record: dict[str, Any], adopted_templates: list[str]) -> None:
    claims = [
        str(item.get("type", ""))
        for item in record.get("functional_ir", {}).get("claims", [])
        if isinstance(item, dict) and item.get("type")
    ]
    report["prompt_checker_templates"] = list(adopted_templates)
    report["prompt_functional_claims"] = claims
    report["source"] = {
        "prompt_checker_templates": list(adopted_templates),
        "prompt_functional_claims": claims,
        "prompt_functional_ir": record.get("functional_ir", {}),
    }


def _summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    by_axis: dict[str, dict[str, int]] = defaultdict(lambda: {"total": 0, "top1": 0, "top3": 0, "top5": 0, "forbidden_top3": 0})
    for result in results:
        bucket = by_axis[str(result["axis"])]
        bucket["total"] += 1
        has_expected = bool(result.get("required_node_any"))
        bucket["top1"] += int(has_expected and bool(result["rag_top1_hit"]))
        bucket["top3"] += int(has_expected and bool(result["rag_top3_hit"]))
        bucket["top5"] += int(has_expected and bool(result["rag_top5_hit"]))
        bucket["forbidden_top3"] += int(bool(result["rag_forbidden_top3"]))
    total = len(results)
    positives = [r for r in results if r.get("required_node_any")]
    positive_total = len(positives)
    top1 = sum(int(bool(r["rag_top1_hit"])) for r in positives)
    top3 = sum(int(bool(r["rag_top3_hit"])) for r in positives)
    top5 = sum(int(bool(r["rag_top5_hit"])) for r in positives)
    forbidden = sum(int(bool(r["rag_forbidden_top3"])) for r in results)
    return {
        "total_cases": total,
        "positive_cases": positive_total,
        "negative_or_no_expected_cases": total - positive_total,
        "top1_hits": top1,
        "top3_hits": top3,
        "top5_hits": top5,
        "forbidden_top3": forbidden,
        "top1_rate": round(top1 / positive_total, 4) if positive_total else 0.0,
        "top3_rate": round(top3 / positive_total, 4) if positive_total else 0.0,
        "top5_rate": round(top5 / positive_total, 4) if positive_total else 0.0,
        "forbidden_top3_rate": round(forbidden / total, 4) if total else 0.0,
        "by_axis": {
            axis: {
                **bucket,
                "top1_rate": round(bucket["top1"] / bucket["total"], 4) if bucket["total"] else 0.0,
                "top3_rate": round(bucket["top3"] / bucket["total"], 4) if bucket["total"] else 0.0,
                "top5_rate": round(bucket["top5"] / bucket["total"], 4) if bucket["total"] else 0.0,
                "forbidden_top3_rate": round(bucket["forbidden_top3"] / bucket["total"], 4) if bucket["total"] else 0.0,
            }
            for axis, bucket in sorted(by_axis.items())
        },
        "miss_top3_cases": [r["case_id"] for r in positives if not r["rag_top3_hit"]],
        "forbidden_top3_cases": [r["case_id"] for r in results if r["rag_forbidden_top3"]],
    }


def _write_markdown(out_root: Path, summary: dict[str, Any], results: list[dict[str, Any]], nodes: list[KnowledgeNode]) -> None:
    lines = [
        "# Circuit-Mechanism RAG Audit",
        "",
        "This is a no-API retrieval audit. It does not claim LLM repair pass rate.",
        "",
        "## Knowledge Base",
        "",
        f"- Nodes: `{len(nodes)}`",
    ]
    counts = Counter(node.kind for node in nodes)
    for kind, count in sorted(counts.items()):
        lines.append(f"- `{kind}`: `{count}`")
    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- Positive cases with expected mechanisms: `{summary['positive_cases']}`",
            f"- Negative/no-expected cases: `{summary['negative_or_no_expected_cases']}`",
            f"- Top-1 mechanism hit: `{summary['top1_hits']}/{summary['positive_cases']}` (`{summary['top1_rate']:.4f}`)",
            f"- Top-3 mechanism hit: `{summary['top3_hits']}/{summary['positive_cases']}` (`{summary['top3_rate']:.4f}`)",
            f"- Top-5 mechanism hit: `{summary['top5_hits']}/{summary['positive_cases']}` (`{summary['top5_rate']:.4f}`)",
            f"- Forbidden top-3 retrievals: `{summary['forbidden_top3']}/{summary['total_cases']}` (`{summary['forbidden_top3_rate']:.4f}`)",
            "",
            "## By Axis",
            "",
            "| Axis | Total | Top-1 | Top-3 | Top-5 | Forbidden Top-3 |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for axis, bucket in summary["by_axis"].items():
        lines.append(
            f"| `{axis}` | {bucket['total']} | {bucket['top1']} | {bucket['top3']} | "
            f"{bucket['top5']} | {bucket['forbidden_top3']} |"
        )
    lines.extend(
        [
            "",
            "## Cases",
            "",
            "| Case | Axis | Required | Rule Cards | RAG Top-3 | Top-3 Hit | Forbidden |",
            "|---|---|---|---|---|---:|---|",
        ]
    )
    for result in results:
        top3 = [item["node_id"] for item in result["rag_top"][:3]]
        lines.append(
            f"| `{result['case_id']}` | `{result['axis']}` | "
            f"{', '.join(f'`{item}`' for item in result['required_node_any']) or '-'} | "
            f"{', '.join(f'`card:{item}`' for item in result['rule_cards']) or '-'} | "
            f"{', '.join(f'`{item}`' for item in top3) or '-'} | "
            f"{'yes' if result['rag_top3_hit'] else 'no'} | "
            f"{', '.join(f'`{item}`' for item in result['rag_forbidden_top3']) or '-'} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "A top-k hit means the RAG layer retrieved at least one expected mechanism node",
            "from cards, prompt templates, or R26-validated mechanism templates. Forbidden",
            "top-3 hits indicate an over-trigger risk. The next experiment should use the",
            "retrieved nodes to build repair prompts and compare rule-card vs RAG+card on",
            "the same G/F residual failures.",
        ]
    )
    (out_root / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--threshold", type=float, default=0.7)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--no-skills", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    out_root = args.output_root
    if not out_root.is_absolute():
        out_root = ROOT / out_root
    if out_root.exists() and args.overwrite:
        import shutil

        shutil.rmtree(out_root)
    out_root.mkdir(parents=True, exist_ok=True)

    nodes = build_knowledge_base(include_skills=not args.no_skills)
    results: list[dict[str, Any]] = []
    for case in GENERALIZATION_CASES:
        results.append(_run_generalization_case(case, out_root=out_root, nodes=nodes, threshold=args.threshold, top_k=args.top_k))
    for case in EXTRA_RAG_CASES:
        results.append(_run_extra_case(case, out_root=out_root, nodes=nodes, threshold=args.threshold, top_k=args.top_k))

    summary = _summarize(results)
    payload = {
        "summary": summary,
        "knowledge_nodes": [
            {
                "node_id": node.node_id,
                "kind": node.kind,
                "title": node.title,
                "source": node.source,
            }
            for node in nodes
        ],
        "results": results,
    }
    (out_root / "summary.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    _write_markdown(out_root, summary, results, nodes)
    print(json.dumps({"output_root": str(out_root.relative_to(ROOT)), **summary}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
