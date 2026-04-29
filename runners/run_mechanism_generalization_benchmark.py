#!/usr/bin/env python3
"""Probe whether mechanism cards generalize beyond the original task strings.

The benchmark is intentionally no-API and no-gold.  It creates synthetic public
prompts that perturb values, signal names, and nearby structures, then checks:

1. prompt -> mechanism-template inference;
2. inferred template/failure vector -> repair-card retrieval;
3. negative controls do not trigger specialized cards.

This does not claim repair pass-rate.  It is an overfitting guard for the
contract/card routing layer before spending model calls on no-leak repair
replay.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from contract_repair_cards import select_contract_repair_cards
from infer_prompt_checker_specs import infer_specs


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "results" / "mechanism-generalization-benchmark-2026-04-27"


@dataclass(frozen=True)
class Case:
    case_id: str
    axis: str
    prompt: str
    required_claims: list[str] = field(default_factory=list)
    forbidden_claims: list[str] = field(default_factory=list)
    required_templates: list[str] = field(default_factory=list)
    forbidden_templates: list[str] = field(default_factory=list)
    required_cards: list[str] = field(default_factory=list)
    forbidden_cards: list[str] = field(default_factory=list)


def _prompt(body: str) -> str:
    return body.strip() + "\n"


CASES: list[Case] = [
    Case(
        case_id="therm_dac_width12_vstep025",
        axis="value_perturbation",
        required_templates=["thermometer_dac_code_to_output_span"],
        forbidden_templates=["dac_code_to_output_span"],
        required_cards=["thermometer_dac_count_to_voltage"],
        forbidden_cards=["dac_differential_output_from_code"],
        prompt=_prompt(
            """
            Write a 12-bit thermometer-coded DAC in pure voltage-domain Verilog-A.
            The input bus is `din_therm[11:0]`, reset is active-low `rst_n`, and
            the output is `vout`.  The output must equal the count of asserted
            thermometer cells times parameter `vstep`, with default `vstep=0.25`.
            Ports:
            - `din_therm[11:0]`: input electrical
            - `rst_n`: input electrical
            - `vout`: output electrical
            Required public waveform columns: `rst_n`, `din_therm[11:0]`, `vout`.
            """
        ),
    ),
    Case(
        case_id="unary_dac_renamed_nodes",
        axis="name_perturbation",
        required_templates=["thermometer_dac_code_to_output_span"],
        required_cards=["thermometer_dac_count_to_voltage"],
        forbidden_cards=["dac_differential_output_from_code"],
        prompt=_prompt(
            """
            Build an 8-bit unary thermometer DAC.  The public stimulus bus is
            named `therm_in[7:0]`, the active-low reset is `reset_b`, and the
            single-ended analog output is `analog_out`.  After reset release,
            `analog_out` should be proportional to the population count of
            `therm_in[7:0]` using a 0.7 V step.
            Ports:
            - `therm_in[7:0]`: input electrical
            - `reset_b`: input electrical
            - `analog_out`: output electrical
            """
        ),
    ),
    Case(
        case_id="gray_counter_width5_renamed",
        axis="value_and_name_perturbation",
        required_templates=["gray_counter_sequence"],
        required_cards=["gray_counter_one_bit_sequence"],
        prompt=_prompt(
            """
            Create a 5-bit Gray-code counter.  Use input clock `clock_i`, reset
            `reset_i`, and outputs `gray[4:0]`.  On each valid rising clock edge,
            increment an internal binary count and drive Gray outputs so adjacent
            public states differ by exactly one bit.
            Ports:
            - `clock_i`: input electrical
            - `reset_i`: input electrical
            - `gray[4:0]`: output electrical
            """
        ),
    ),
    Case(
        case_id="serializer_lsb_first_width4",
        axis="structure_perturbation",
        required_templates=["sequence_alignment"],
        required_cards=["serializer_frame_alignment_sequence"],
        prompt=_prompt(
            """
            Implement a 4-bit parallel-to-serial serializer with explicit frame
            alignment.  Latch `word[3:0]` when `load` is high on `clk`, then shift
            the word out LSB-first on `serial_out`.  Assert `frame_o` only for the
            first serialized bit of each loaded word.
            Ports:
            - `clk`: input electrical
            - `load`: input electrical
            - `word[3:0]`: input electrical
            - `serial_out`: output electrical
            - `frame_o`: output electrical
            """
        ),
    ),
    Case(
        case_id="parameterized_pulse_vhi11_reps7",
        axis="value_perturbation",
        required_templates=["parameterized_event_sequence"],
        required_cards=["parameterized_pulse_train_from_instance_overrides"],
        prompt=_prompt(
            """
            Write a Verilog-A pulse source whose behavior depends on instance
            parameter overrides.  Declare real parameter `vhi` and integer
            parameter `reps`; the testbench will override them to `vhi=1.1` and
            `reps=7`.  The output `pulse_out` must emit exactly `reps` pulses and
            the high level must follow `vhi`.
            Ports:
            - `pulse_out`: output electrical
            - `vss`: inout electrical
            """
        ),
    ),
    Case(
        case_id="bbpd_renamed_data_clock",
        axis="name_and_timing_perturbation",
        required_templates=["bbpd_data_clock_lead_lag", "pulse_non_overlap"],
        forbidden_templates=["paired_edge_response"],
        required_cards=["bbpd_data_clock_lead_lag_pulses"],
        forbidden_cards=["pfd_paired_up_dn_pulses"],
        prompt=_prompt(
            """
            Build a bang-bang phase detector for data/clock edge alignment.  The
            clock input is `clk_i` and the data edge input is `edge_data`.  Emit
            bounded `up` pulses when data leads the clock and bounded `dn` pulses
            when data lags the clock.  UP and DN should remain mostly
            non-overlapping.
            Ports:
            - `clk_i`: input electrical
            - `edge_data`: input electrical
            - `up`: output electrical
            - `dn`: output electrical
            - `retimed`: output electrical
            """
        ),
    ),
    Case(
        case_id="adc_dac_width5_roundtrip",
        axis="value_perturbation",
        required_templates=["quantized_reconstruction"],
        required_cards=["adc_dac_reconstruction_chain"],
        prompt=_prompt(
            """
            Create a 5-bit ADC-DAC round-trip behavioral model.  The input `vin`
            is sampled on `clk`, quantized into output bits `dout[4:0]`, and the
            analog output `vout` reconstructs the quantized code over the public
            reference range.  The reconstructed output must move with the code.
            Ports:
            - `vin`: input electrical
            - `clk`: input electrical
            - `rst`: input electrical
            - `dout[4:0]`: output electrical
            - `vout`: output electrical
            """
        ),
    ),
    Case(
        case_id="differential_segmented_dac_variant",
        axis="structure_perturbation",
        required_templates=["differential_code_response"],
        required_cards=["segmented_dac_differential_weighted_sum"],
        prompt=_prompt(
            """
            Build a segmented differential DAC.  The MSB segment is thermometer
            coded and the LSB segment is binary weighted.  Combine both segments
            into one normalized code and drive `out_p` and `out_n` around common
            mode with opposite polarity.
            Ports:
            - `therm[3:0]`: input electrical
            - `bin[3:0]`: input electrical
            - `out_p`: output electrical
            - `out_n`: output electrical
            """
        ),
    ),
    Case(
        case_id="binary_dac_no_thermometer_control",
        axis="negative_control",
        required_templates=["dac_code_to_output_span"],
        forbidden_templates=["thermometer_dac_code_to_output_span"],
        forbidden_cards=["thermometer_dac_count_to_voltage"],
        prompt=_prompt(
            """
            Build a 12-bit binary-weighted DAC.  Decode `code[11:0]` as a binary
            integer and map that value monotonically to `vout`.  This is not a
            thermometer or unary DAC.
            Ports:
            - `code[11:0]`: input electrical
            - `vout`: output electrical
            """
        ),
    ),
    Case(
        case_id="binary_dac_monotocin_dinp_alias",
        axis="typo_and_alias_perturbation",
        required_templates=["dac_code_to_output_span"],
        forbidden_templates=["thermometer_dac_code_to_output_span"],
        forbidden_cards=["thermometer_dac_count_to_voltage"],
        prompt=_prompt(
            """
            Build a 10-bit binary DAC.  Decode public input bus `dinp[9:0]` as a
            binary integer and make `analog_out` monotocin with that code over
            the output range.  The word monotocin is a typo for monotonic in the
            user prompt; the intended behavior is still monotonic code-to-output
            conversion.
            Ports:
            - `dinp[9:0]`: input electrical
            - `analog_out`: output electrical
            """
        ),
    ),
    Case(
        case_id="binary_counter_no_gray_control",
        axis="negative_control",
        forbidden_templates=["gray_counter_sequence"],
        forbidden_cards=["gray_counter_one_bit_sequence"],
        prompt=_prompt(
            """
            Implement a 5-bit binary counter.  On every rising edge of `clk`,
            increment `count[4:0]` in normal binary order.  Adjacent binary states
            may flip multiple output bits.
            Ports:
            - `clk`: input electrical
            - `rst`: input electrical
            - `count[4:0]`: output electrical
            """
        ),
    ),
    Case(
        case_id="pfd_no_bbpd_control",
        axis="negative_control",
        required_templates=["paired_edge_response", "pulse_non_overlap"],
        forbidden_templates=["bbpd_data_clock_lead_lag"],
        forbidden_cards=["bbpd_data_clock_lead_lag_pulses"],
        prompt=_prompt(
            """
            Implement a phase frequency detector.  REF rising edges should drive
            UP, DIV rising edges should drive DN, and the two outputs should be
            reset after both edges arrive.  UP and DN should not overlap.
            Ports:
            - `ref`: input electrical
            - `div`: input electrical
            - `up`: output electrical
            - `dn`: output electrical
            """
        ),
    ),
    Case(
        case_id="fixed_pulse_no_override_control",
        axis="negative_control",
        forbidden_templates=["parameterized_event_sequence"],
        forbidden_cards=["parameterized_pulse_train_from_instance_overrides"],
        prompt=_prompt(
            """
            Generate a fixed pulse train on `out` with a hard-coded amplitude of
            0.5 V and a fixed count of three pulses.  There are no instance
            parameter overrides in this task.
            Ports:
            - `out`: output electrical
            - `vss`: inout electrical
            """
        ),
    ),
    Case(
        case_id="binary_dac_functional_order_no_keyword",
        axis="functional_paraphrase",
        required_claims=["code_to_analog_transfer", "ordered_transfer"],
        required_templates=["dac_code_to_output_span"],
        forbidden_templates=["thermometer_dac_code_to_output_span"],
        prompt=_prompt(
            """
            Build an 8-bit digital-to-analog converter.  Treat `word[7:0]` as an
            unsigned integer and drive `vout` as the produced voltage.  If one
            input word represents a greater integer than another, the produced
            voltage must not be lower.
            Ports:
            - `word[7:0]`: input electrical
            - `vout`: output electrical
            """
        ),
    ),
    Case(
        case_id="unit_cell_dac_count_high_no_keyword",
        axis="functional_paraphrase",
        required_claims=["count_high_to_analog"],
        required_templates=["thermometer_dac_code_to_output_span"],
        required_cards=["thermometer_dac_count_to_voltage"],
        prompt=_prompt(
            """
            Build an 8-cell DAC.  There are one-bit controls `cell[7:0]`; each
            enabled cell contributes the same amount.  The output `vout` should
            equal `vstep` multiplied by how many controls are high.
            Ports:
            - `cell[7:0]`: input electrical
            - `vout`: output electrical
            """
        ),
    ),
    Case(
        case_id="adc_bucket_index_no_keyword",
        axis="functional_paraphrase",
        required_claims=["quantized_encoding", "sample_on_clock_edge", "ordered_transfer"],
        required_templates=["monotonic_code_vs_input", "sample_after_clock"],
        prompt=_prompt(
            """
            Create a 4-bit analog-to-digital converter.  At each rising edge of
            `clk`, store the bucket index for `vin` into `out[3:0]`.  A larger
            `vin` must never produce a smaller stored index.
            Ports:
            - `vin`: input electrical
            - `clk`: input electrical
            - `out[3:0]`: output electrical
            """
        ),
    ),
    Case(
        case_id="edge_alignment_functional_no_bbpd_word",
        axis="functional_paraphrase",
        required_claims=["data_clock_lead_lag_pulses"],
        required_templates=["bbpd_data_clock_lead_lag", "pulse_non_overlap"],
        forbidden_templates=["paired_edge_response"],
        required_cards=["bbpd_data_clock_lead_lag_pulses"],
        forbidden_cards=["pfd_paired_up_dn_pulses"],
        prompt=_prompt(
            """
            Create an edge alignment detector.  When a transition on `data_i`
            arrives before the transition on `clk_i`, emit a bounded `up` pulse.
            When the data transition arrives after the clock transition, emit a
            bounded `dn` pulse.  The two pulse outputs should not overlap.
            Ports:
            - `data_i`: input electrical
            - `clk_i`: input electrical
            - `up`: output electrical
            - `dn`: output electrical
            """
        ),
    ),
    Case(
        case_id="one_bit_counter_no_gray_word",
        axis="functional_paraphrase",
        required_claims=["one_bit_adjacent_transition"],
        required_templates=["gray_counter_sequence"],
        required_cards=["gray_counter_one_bit_sequence"],
        prompt=_prompt(
            """
            Implement a 4-bit counter on `clk`.  Adjacent public states of
            `state[3:0]` must differ in exactly one bit, then continue through a
            repeating cycle after reset.
            Ports:
            - `clk`: input electrical
            - `rst`: input electrical
            - `state[3:0]`: output electrical
            """
        ),
    ),
    Case(
        case_id="non_ordered_dac_control",
        axis="functional_negative_control",
        forbidden_claims=["ordered_transfer", "count_high_to_analog"],
        forbidden_templates=["thermometer_dac_code_to_output_span"],
        forbidden_cards=["thermometer_dac_count_to_voltage"],
        prompt=_prompt(
            """
            Build a DAC-like lookup table with input `addr[3:0]` and output
            `vout`.  The table entries are intentionally arbitrary: there is no
            ordering guarantee, and the output may go down when the address is
            larger.
            Ports:
            - `addr[3:0]`: input electrical
            - `vout`: output electrical
            """
        ),
    ),
]


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _failed_contracts_for_template(template: str) -> list[dict[str, str]]:
    family = f"prompt-spec:{template}"
    if template == "thermometer_dac_code_to_output_span":
        return [
            {
                "name": "prompt_thermometer_dac_code_to_output_span_output_span",
                "repair_family": family,
                "severity": "hard",
            }
        ]
    if template == "dac_code_to_output_span":
        return [
            {
                "name": "prompt_dac_code_to_output_span_output_span",
                "repair_family": family,
                "severity": "hard",
            }
        ]
    if template == "quantized_reconstruction":
        return [
            {"name": "dout_code_changes", "repair_family": family, "severity": "hard"},
            {"name": "vout_moves", "repair_family": family, "severity": "hard"},
        ]
    if template == "gray_counter_sequence":
        return [
            {
                "name": "prompt_gray_counter_one_bit_transitions",
                "repair_family": family,
                "severity": "hard",
            }
        ]
    if template == "sequence_alignment":
        return [
            {
                "name": "prompt_sequence_alignment_sout_edge_count",
                "repair_family": family,
                "severity": "hard",
            }
        ]
    if template == "parameterized_event_sequence":
        return [
            {
                "name": "prompt_parameterized_event_sequence_out_output_span",
                "repair_family": family,
                "severity": "hard",
            }
        ]
    if template == "timer_future_event_liveness":
        return [
            {
                "name": "prompt_timer_future_event_liveness_out_edges",
                "repair_family": family,
                "severity": "hard",
            }
        ]
    if template == "bbpd_data_clock_lead_lag":
        return [
            {"name": "up_pulses_present", "repair_family": family, "severity": "hard"},
            {"name": "dn_pulses_present", "repair_family": family, "severity": "hard"},
            {
                "name": "prompt_bbpd_data_clock_lead_lag",
                "repair_family": family,
                "severity": "advisory",
            },
        ]
    if template == "paired_edge_response":
        return [
            {"name": "up_pulses_present", "repair_family": family, "severity": "hard"},
            {"name": "dn_pulses_present", "repair_family": family, "severity": "hard"},
            {
                "name": "prompt_paired_edge_response",
                "repair_family": family,
                "severity": "advisory",
            },
        ]
    if template == "pulse_non_overlap":
        return [
            {
                "name": "prompt_pulse_non_overlap",
                "repair_family": family,
                "severity": "hard",
            }
        ]
    if template == "differential_code_response":
        return [
            {
                "name": "vout_differential_range",
                "repair_family": family,
                "severity": "hard",
            }
        ]
    if template == "logic_truth_table":
        return [
            {
                "name": "prompt_logic_truth_table_y_output_span",
                "repair_family": family,
                "severity": "advisory",
            }
        ]
    return [
        {
            "name": f"prompt_{template}_synthetic_failure",
            "repair_family": family,
            "severity": "advisory",
        }
    ]


def _synthetic_report(task_id: str, templates: list[str]) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for template in templates:
        for item in _failed_contracts_for_template(template):
            payload = {
                "name": item["name"],
                "passed": False,
                "severity": item["severity"],
                "repair_family": item["repair_family"],
            }
            results.append(payload)

    # PFD cards require evidence that the reference/divider edges are alive.
    if "paired_edge_response" in templates and "pfd" in task_id:
        for name in ("ref_edges_present", "div_edges_present"):
            results.append({"name": name, "passed": True, "severity": "hard"})
    if "differential_code_response" in templates and "segmented" in task_id:
        results.append({"name": "code_code_changes", "passed": True, "severity": "hard"})

    failed = [str(item["name"]) for item in results if not item.get("passed")]
    hard = [str(item["name"]) for item in results if not item.get("passed") and item.get("severity") == "hard"]
    advisory = [
        str(item["name"])
        for item in results
        if not item.get("passed") and item.get("severity") != "hard"
    ]
    passed = [str(item["name"]) for item in results if item.get("passed")]
    return {
        "task_id": task_id,
        "status": "FAIL_CONTRACT" if failed else "PASS",
        "passed_contracts": passed,
        "failed_contracts": failed,
        "failed_hard_contracts": hard,
        "failed_advisory_contracts": advisory,
        "contract_results": results,
    }


def _case_result(case: Case, *, out_root: Path, threshold: float, card_limit: int) -> dict[str, Any]:
    task_dir = out_root / "synthetic_tasks" / case.case_id
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "prompt.md").write_text(case.prompt, encoding="utf-8")

    record = infer_specs(case.case_id, task_dir)
    inferred_claims = [
        str(claim.get("type"))
        for claim in record.get("functional_ir", {}).get("claims", [])
    ]
    adopted_templates = [
        str(spec.get("template"))
        for spec in record.get("templates", [])
        if float(spec.get("confidence", 0.0)) >= threshold
    ]
    report = _synthetic_report(case.case_id, adopted_templates)
    cards = select_contract_repair_cards(report, task_id=case.case_id, limit=card_limit)
    selected_cards = [str(card.get("id")) for card in cards]

    missing_claims = [item for item in case.required_claims if item not in inferred_claims]
    forbidden_claims = [item for item in case.forbidden_claims if item in inferred_claims]
    missing_templates = [item for item in case.required_templates if item not in adopted_templates]
    forbidden_templates = [item for item in case.forbidden_templates if item in adopted_templates]
    missing_cards = [item for item in case.required_cards if item not in selected_cards]
    forbidden_cards = [item for item in case.forbidden_cards if item in selected_cards]

    claim_pass = not missing_claims and not forbidden_claims
    template_pass = not missing_templates and not forbidden_templates
    card_pass = not missing_cards and not forbidden_cards
    overall_pass = claim_pass and template_pass and card_pass
    return {
        "case_id": case.case_id,
        "axis": case.axis,
        "status": "PASS" if overall_pass else "FAIL",
        "claim_pass": claim_pass,
        "template_pass": template_pass,
        "card_pass": card_pass,
        "inferred_claims": inferred_claims,
        "adopted_templates": adopted_templates,
        "selected_cards": selected_cards,
        "missing_claims": missing_claims,
        "forbidden_claims_triggered": forbidden_claims,
        "missing_templates": missing_templates,
        "forbidden_templates_triggered": forbidden_templates,
        "missing_cards": missing_cards,
        "forbidden_cards_triggered": forbidden_cards,
        "prompt_path": str(task_dir / "prompt.md"),
        "inference_record": record,
        "synthetic_contract_report": report,
    }


def _summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    by_axis: dict[str, dict[str, int]] = {}
    for result in results:
        axis = str(result["axis"])
        bucket = by_axis.setdefault(axis, {"total": 0, "pass": 0})
        bucket["total"] += 1
        if result["status"] == "PASS":
            bucket["pass"] += 1
    for bucket in by_axis.values():
        total = bucket["total"]
        bucket["pass_rate"] = round(bucket["pass"] / total, 4) if total else 0.0
    passed = sum(1 for result in results if result["status"] == "PASS")
    return {
        "total_cases": len(results),
        "pass_cases": passed,
        "pass_rate": round(passed / len(results), 4) if results else 0.0,
        "by_axis": by_axis,
        "failed_cases": [result["case_id"] for result in results if result["status"] != "PASS"],
    }


def _write_markdown(out_root: Path, summary: dict[str, Any], results: list[dict[str, Any]]) -> None:
    lines = [
        "# Mechanism Generalization Benchmark",
        "",
        "This no-leak benchmark perturbs public prompts and checks whether prompt",
        "mechanism inference and repair-card retrieval remain mechanism-driven.",
        "",
        "## Summary",
        "",
        f"- Cases: `{summary['pass_cases']}/{summary['total_cases']}` PASS",
        f"- Pass rate: `{summary['pass_rate']:.4f}`",
        "",
        "## By Axis",
        "",
        "| Axis | PASS | Total | Rate |",
        "|---|---:|---:|---:|",
    ]
    for axis, bucket in sorted(summary["by_axis"].items()):
        lines.append(f"| `{axis}` | {bucket['pass']} | {bucket['total']} | {bucket['pass_rate']:.4f} |")
    lines.extend([
        "",
        "## Cases",
        "",
        "| Case | Axis | Status | Functional Claims | Templates | Cards | Issues |",
        "|---|---|---|---|---|---|---|",
    ])
    for result in results:
        issues = []
        for key in ("missing_claims", "forbidden_claims_triggered", "missing_templates", "forbidden_templates_triggered", "missing_cards", "forbidden_cards_triggered"):
            values = result.get(key) or []
            if values:
                issues.append(f"{key}={','.join(values)}")
        lines.append(
            "| `{case}` | `{axis}` | `{status}` | {claims} | {templates} | {cards} | {issues} |".format(
                case=result["case_id"],
                axis=result["axis"],
                status=result["status"],
                claims=", ".join(f"`{item}`" for item in result["inferred_claims"]) or "-",
                templates=", ".join(f"`{item}`" for item in result["adopted_templates"]) or "-",
                cards=", ".join(f"`{item}`" for item in result["selected_cards"]) or "-",
                issues="; ".join(issues) or "-",
            )
        )
    lines.extend([
        "",
        "## Interpretation",
        "",
        "Passing this benchmark means the routing layer handles value perturbations,",
        "renamed public signals, nearby structural variants, and negative controls",
        "without relying on the original benchmark task strings. Functional",
        "paraphrase cases additionally require prompt text to be lifted into a",
        "small behavior-relation IR before template/card routing. It is not a",
        "repair pass-rate claim; the next step is a no-leak model replay on generated",
        "near-neighbor tasks.",
        "",
    ])
    (out_root / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--threshold", type=float, default=0.70)
    parser.add_argument("--card-limit", type=int, default=4)
    args = parser.parse_args()

    out_root = args.out_root
    if not out_root.is_absolute():
        out_root = ROOT / out_root
    out_root.mkdir(parents=True, exist_ok=True)
    results = [
        _case_result(case, out_root=out_root, threshold=args.threshold, card_limit=args.card_limit)
        for case in CASES
    ]
    summary = _summarize(results)
    _write_json(out_root / "case_results.json", {"summary": summary, "cases": results})
    _write_json(out_root / "summary.json", summary)
    _write_markdown(out_root, summary, results)
    print(json.dumps(summary, indent=2))
    return 0 if summary["pass_cases"] == summary["total_cases"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
