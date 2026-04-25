#!/usr/bin/env python3
"""Template-guided EVAS repair probe.

This runner is intentionally small and deterministic.  It tests whether a
bounded mechanism-level repair space can produce candidates that the earlier
LLM-only local patch loop failed to generate.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from simulate_evas import run_case


ROOT = Path(__file__).resolve().parents[1]
CLK_DIVIDER_TASK = ROOT / "tasks/spec-to-va/voltage/digital-logic/clk_divider"
CLK_DIVIDER_TB = CLK_DIVIDER_TASK / "gold/tb_clk_divider_ref.scs"
DEFAULT_ANCHOR = (
    ROOT
    / "generated-experiment/condition-A/kimi-k2.5/kimi-k2.5/clk_divider/sample_0"
    / "clk_divider_ref.va"
)


@dataclass(frozen=True)
class TemplateVariant:
    name: str
    description: str
    body: str


def _json_write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _extract_interval_gap(result: dict) -> int | None:
    notes = "\n".join(str(note) for note in result.get("notes", []))
    ratio_match = re.search(r"\bratio_code=([0-9]+)", notes)
    hist_match = re.search(r"\binterval_hist=\{([^}]*)\}", notes)
    if not ratio_match or not hist_match:
        return None
    ratio = int(ratio_match.group(1))
    keys = [int(key) for key in re.findall(r"([0-9]+)\s*:", hist_match.group(1))]
    if not keys:
        return None
    return min(abs(key - ratio) for key in keys)


def _rank(result: dict) -> tuple:
    scores = result.get("scores", {})
    gap = _extract_interval_gap(result)
    return (
        int(result.get("status") == "PASS"),
        float(scores.get("weighted_total", 0.0)),
        -9999 if gap is None else -gap,
    )


def _base_module(body: str) -> str:
    return f"""`include "constants.vams"
`include "disciplines.vams"

module clk_divider_ref (
    clk_in,
    rst_n,
    div_code_0,
    div_code_1,
    div_code_2,
    div_code_3,
    div_code_4,
    div_code_5,
    div_code_6,
    div_code_7,
    clk_out,
    lock
);

    input clk_in;
    input rst_n;
    input div_code_0;
    input div_code_1;
    input div_code_2;
    input div_code_3;
    input div_code_4;
    input div_code_5;
    input div_code_6;
    input div_code_7;
    output clk_out;
    output lock;

    electrical clk_in;
    electrical rst_n;
    electrical div_code_0;
    electrical div_code_1;
    electrical div_code_2;
    electrical div_code_3;
    electrical div_code_4;
    electrical div_code_5;
    electrical div_code_6;
    electrical div_code_7;
    electrical clk_out;
    electrical lock;

    parameter real vth = 0.45;
    parameter real vhigh = 0.9;
    parameter real vlow = 0.0;
    parameter real trf = 10p;

    integer ratio;
    integer counter;
    integer out_state;
    integer lock_state;
    integer edge_count;
    integer low_len;
    integer high_len;
    integer segment_len;

{body}

endmodule
"""


def _common_ratio_code() -> str:
    return """
            ratio = (V(div_code_0) > vth ? 1 : 0)
                  + (V(div_code_1) > vth ? 2 : 0)
                  + (V(div_code_2) > vth ? 4 : 0)
                  + (V(div_code_3) > vth ? 8 : 0)
                  + (V(div_code_4) > vth ? 16 : 0)
                  + (V(div_code_5) > vth ? 32 : 0)
                  + (V(div_code_6) > vth ? 64 : 0)
                  + (V(div_code_7) > vth ? 128 : 0);
            if (ratio < 1)
                ratio = 1;
"""


def _segment_variant(name: str, description: str, low_expr: str, high_expr: str) -> TemplateVariant:
    body = f"""    analog begin
        @(initial_step) begin
            ratio = 1;
            counter = 0;
            out_state = 0;
            lock_state = 0;
            edge_count = 0;
            low_len = 1;
            high_len = 1;
            segment_len = 1;
        end

        @(cross(V(clk_in) - vth, +1)) begin
{_common_ratio_code()}
            if (V(rst_n) < vth) begin
                counter = 0;
                out_state = 0;
                lock_state = 0;
                edge_count = 0;
                segment_len = 1;
            end else if (ratio == 1) begin
                out_state = 1;
                lock_state = 1;
                counter = 0;
                edge_count = edge_count + 1;
            end else begin
                low_len = {low_expr};
                high_len = {high_expr};
                if (low_len < 1)
                    low_len = 1;
                if (high_len < 1)
                    high_len = 1;

                if (counter <= 0)
                    counter = (out_state == 0) ? low_len : high_len;

                counter = counter - 1;
                edge_count = edge_count + 1;
                if (edge_count >= ratio)
                    lock_state = 1;
                if (counter <= 0)
                    out_state = (out_state == 0) ? 1 : 0;
            end
        end

        @(cross(V(clk_in) - vth, -1)) begin
            if (V(rst_n) < vth) begin
                out_state = 0;
            end else if (ratio == 1) begin
                out_state = 0;
                lock_state = 1;
            end
        end

        V(clk_out) <+ transition(out_state ? vhigh : vlow, 0, trf, trf);
        V(lock) <+ transition(lock_state ? vhigh : vlow, 0, trf, trf);
    end"""
    return TemplateVariant(name=name, description=description, body=_base_module(body))


def _pulse_variant(name: str, description: str, threshold_expr: str, reset_expr: str) -> TemplateVariant:
    body = f"""    analog begin
        @(initial_step) begin
            ratio = 1;
            counter = 0;
            out_state = 0;
            lock_state = 0;
            edge_count = 0;
            low_len = 1;
            high_len = 1;
            segment_len = 1;
        end

        @(cross(V(clk_in) - vth, +1)) begin
{_common_ratio_code()}
            if (V(rst_n) < vth) begin
                counter = 0;
                out_state = 0;
                lock_state = 0;
                edge_count = 0;
            end else begin
                edge_count = edge_count + 1;
                counter = counter + 1;
                out_state = 0;
                if (counter >= {threshold_expr}) begin
                    out_state = 1;
                    counter = {reset_expr};
                    lock_state = 1;
                end
            end
        end

        @(cross(V(clk_in) - vth, -1)) begin
            if (V(rst_n) < vth)
                out_state = 0;
        end

        V(clk_out) <+ transition(out_state ? vhigh : vlow, 0, trf, trf);
        V(lock) <+ transition(lock_state ? vhigh : vlow, 0, trf, trf);
    end"""
    return TemplateVariant(name=name, description=description, body=_base_module(body))


def clk_divider_variants() -> list[TemplateVariant]:
    return [
        _segment_variant(
            "segment_floor_low_ceil_high",
            "Alternating low/high segment lengths floor(N/2), ceil(N/2).",
            "ratio / 2",
            "ratio - (ratio / 2)",
        ),
        _segment_variant(
            "segment_ceil_low_floor_high",
            "Alternating low/high segment lengths ceil(N/2), floor(N/2).",
            "(ratio + 1) / 2",
            "ratio - ((ratio + 1) / 2)",
        ),
        _pulse_variant(
            "pulse_every_ratio_reset_zero",
            "One-cycle output pulse every N input rising edges.",
            "ratio",
            "0",
        ),
        _pulse_variant(
            "pulse_every_ratio_reset_one",
            "One-cycle output pulse every N input rising edges with count-after-event phase.",
            "ratio",
            "1",
        ),
        _pulse_variant(
            "pulse_every_ratio_minus_one",
            "One-cycle output pulse using an N-1 terminal-count hypothesis.",
            "(ratio - 1)",
            "0",
        ),
    ]


def run_clk_divider_probe(args: argparse.Namespace) -> dict:
    anchor = Path(args.anchor).resolve()
    generated_root = Path(args.generated_root).resolve()
    output_root = Path(args.output_root).resolve()
    generated_root.mkdir(parents=True, exist_ok=True)
    output_root.mkdir(parents=True, exist_ok=True)

    baseline_dir = generated_root / "baseline"
    baseline_dir.mkdir(parents=True, exist_ok=True)
    baseline_dut = baseline_dir / "clk_divider_ref.va"
    shutil.copy2(anchor, baseline_dut)
    baseline_result = run_case(
        CLK_DIVIDER_TASK,
        baseline_dut,
        CLK_DIVIDER_TB,
        output_root=output_root / "baseline",
        timeout_s=args.timeout_s,
        task_id_override="clk_divider",
    )
    _json_write(output_root / "baseline/result.json", baseline_result)

    attempts: list[dict] = []
    best = {"variant": "baseline", "result": baseline_result, "rank": _rank(baseline_result)}
    for idx, variant in enumerate(clk_divider_variants(), start=1):
        variant_dir = generated_root / f"{idx:02d}_{variant.name}"
        variant_dir.mkdir(parents=True, exist_ok=True)
        dut_path = variant_dir / "clk_divider_ref.va"
        dut_path.write_text(variant.body, encoding="utf-8")
        result = run_case(
            CLK_DIVIDER_TASK,
            dut_path,
            CLK_DIVIDER_TB,
            output_root=output_root / f"{idx:02d}_{variant.name}",
            timeout_s=args.timeout_s,
            task_id_override="clk_divider",
        )
        rank = _rank(result)
        attempt = {
            "idx": idx,
            "variant": variant.name,
            "description": variant.description,
            "status": result.get("status"),
            "scores": result.get("scores"),
            "notes": result.get("notes"),
            "rank": list(rank),
            "interval_gap": _extract_interval_gap(result),
            "dut_path": str(dut_path),
            "result_path": str(output_root / f"{idx:02d}_{variant.name}" / "result.json"),
        }
        attempts.append(attempt)
        _json_write(output_root / f"{idx:02d}_{variant.name}" / "result.json", result)
        print(
            f"[template] {idx:02d} {variant.name}: "
            f"{result.get('status')} rank={rank} notes={result.get('notes')}"
        )
        if rank > best["rank"]:
            best = {"variant": variant.name, "result": result, "rank": rank}

    summary = {
        "mode": "template_guided_repair_probe",
        "task_id": "clk_divider",
        "anchor": str(anchor),
        "baseline": {
            "status": baseline_result.get("status"),
            "scores": baseline_result.get("scores"),
            "notes": baseline_result.get("notes"),
            "rank": list(_rank(baseline_result)),
            "interval_gap": _extract_interval_gap(baseline_result),
        },
        "attempts": attempts,
        "best_variant": best["variant"],
        "best_status": best["result"].get("status"),
        "best_scores": best["result"].get("scores"),
        "best_notes": best["result"].get("notes"),
        "best_rank": list(best["rank"]),
    }
    _json_write(output_root / "summary.json", summary)
    print(
        f"[template] best={summary['best_variant']} "
        f"status={summary['best_status']} notes={summary['best_notes']}"
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run template-guided EVAS repair probe.")
    parser.add_argument("--task", choices=["clk_divider"], default="clk_divider")
    parser.add_argument("--anchor", default=str(DEFAULT_ANCHOR))
    parser.add_argument("--generated-root", default="generated-template-guided-repair-probe")
    parser.add_argument("--output-root", default="results/template-guided-repair-probe")
    parser.add_argument("--timeout-s", type=int, default=120)
    args = parser.parse_args()
    run_clk_divider_probe(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
