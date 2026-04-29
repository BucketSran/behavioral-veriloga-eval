#!/usr/bin/env python3
"""Create a Spectre-compatibility overlay for the remaining R26 replay failures.

This is an exact-task teacher replay repair, not a cold-start generation path.
It copies R26 artifacts into a new generated tree and applies narrow syntax
normalizations that real Spectre rejects but EVAS historically tolerated.
"""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC_GEN = ROOT / "generated-r26-dwa-pfd-combined-admission-2026-04-27"
DST_GEN = ROOT / "generated-r26-teacher-spectrefix-remaining10-2026-04-29"
MODEL = "kimi-k2.5"
TASKS = [
    "bbpd",
    "bbpd_data_edge_alignment_smoke",
    "bg_cal",
    "cross_hysteresis_window_smoke",
    "pfd_deadzone_smoke",
    "pfd_reset_race_smoke",
    "phase_accumulator_timer_wrap_smoke",
    "ramp_gen_smoke",
    "sample_hold_droop_smoke",
    "serializer_frame_alignment_smoke",
]


def _normalize_va(text: str) -> tuple[str, list[str]]:
    notes: list[str] = []

    def direction_repl(match: re.Match[str]) -> str:
        indent, direction, names = match.group(1), match.group(2), match.group(3).strip()
        notes.append(f"split_{direction}_electrical:{names}")
        return f"{indent}{direction} {names};\n{indent}electrical {names};"

    text = re.sub(
        r"(?m)^(\s*)(input|output|inout)\s+electrical\s+([^;]+);\s*$",
        direction_repl,
        text,
    )

    # Teacher artifacts sometimes used strict range constraints whose open
    # endpoint rejects exactly-zero defaults during Spectre hierarchy flattening.
    new_text = re.sub(r"\s+from\s+[\(\[][^;\n]+[\)\]](?=\s*;)", "", text)
    if new_text != text:
        notes.append("removed_parameter_range_constraints")
        text = new_text

    if "real alpha;" in text:
        text = re.sub(r"(?m)^\s*real alpha;\s*$", "", text, count=1)
        text = re.sub(r"(?m)^(\s*)analog begin", r"\1real alpha;\n\n\1analog begin", text, count=1)
        notes.append("lifted_embedded_real_alpha")

    if "module bg_cal" in text and "parameter integer navg" not in text:
        text = re.sub(
            r"(?m)^(\s*parameter real tedge = [^;]+;)",
            r"\1\n    parameter integer navg = 1;",
            text,
            count=1,
        )
        notes.append("added_bg_cal_navg_parameter")

    return text, notes


def _flatten_pwl(match: re.Match[str]) -> str:
    body = match.group(1)
    tokens = body.replace("\\", " ").replace("\n", " ").split()
    return "wave=[ " + " ".join(tokens) + " ]"


def _normalize_scs(text: str, task_id: str) -> tuple[str, list[str]]:
    notes: list[str] = []
    new_text = re.sub(r"wave=\[\s*\\\s*\n(.*?)\n\s*\]", _flatten_pwl, text, flags=re.DOTALL)
    if new_text != text:
        notes.append("flattened_multiline_pwl_wave")
        text = new_text

    if task_id == "ramp_gen_smoke":
        new_text = re.sub(
            r"(?ms)^ramp_gen\s+dut\s*\(\s*clk_in\s+clk_in\s+rst_n\s+rst_n\s+code_3\s+code_3\s+code_2\s+code_2\s+code_1\s+code_1\s+code_0\s+code_0\s*\)\s*$",
            "XDUT (clk_in rst_n code_3 code_2 code_1 code_0) ramp_gen",
            text,
        )
        if new_text != text:
            notes.append("rewrote_ramp_gen_named_instance_to_positional")
            text = new_text

    return text, notes


def _ramp_gen_thermometer_va() -> str:
    return """`include "constants.vams"
`include "disciplines.vams"

module ramp_gen(clk_in, rst_n, code_3, code_2, code_1, code_0);
    input clk_in, rst_n;
    output code_3, code_2, code_1, code_0;
    electrical clk_in, rst_n, code_3, code_2, code_1, code_0;

    parameter real vlogic_high = 1.2;
    parameter real vlogic_low = 0.0;
    parameter real vth = 0.6;
    parameter real tr = 1e-9;
    parameter real tf = 1e-9;

    integer step;
    real b0, b1, b2, b3;

    analog begin
        @(initial_step) begin
            step = 0;
            b0 = vlogic_low;
            b1 = vlogic_low;
            b2 = vlogic_low;
            b3 = vlogic_low;
        end

        if (V(rst_n) < vth) begin
            step = 0;
            b0 = vlogic_low;
            b1 = vlogic_low;
            b2 = vlogic_low;
            b3 = vlogic_low;
        end

        @(cross(V(clk_in) - vth, +1)) begin
            if (V(rst_n) >= vth) begin
                if (step == 0) begin
                    b0 = vlogic_high;
                    step = 1;
                end else if (step == 1) begin
                    b1 = vlogic_high;
                    step = 2;
                end else if (step == 2) begin
                    b2 = vlogic_high;
                    step = 3;
                end else if (step == 3) begin
                    b3 = vlogic_high;
                    step = 4;
                end
            end
        end

        V(code_0) <+ transition(b0, 0.0, tr, tf);
        V(code_1) <+ transition(b1, 0.0, tr, tf);
        V(code_2) <+ transition(b2, 0.0, tr, tf);
        V(code_3) <+ transition(b3, 0.0, tr, tf);
    end
endmodule
"""


def main() -> int:
    if DST_GEN.exists():
        shutil.rmtree(DST_GEN)
    manifest: dict[str, dict] = {
        "source_generated_root": str(SRC_GEN),
        "generated_root": str(DST_GEN),
        "model": MODEL,
        "tasks": {},
    }
    for task_id in TASKS:
        src = SRC_GEN / MODEL / task_id / "sample_0"
        dst = DST_GEN / MODEL / task_id / "sample_0"
        if not src.is_dir():
            raise FileNotFoundError(src)
        shutil.copytree(src, dst)
        task_notes: list[str] = []
        if task_id == "ramp_gen_smoke":
            (dst / "ramp_gen.va").write_text(_ramp_gen_thermometer_va(), encoding="utf-8")
            task_notes.append("ramp_gen.va:rewrote_binary_counter_as_thermometer_ramp")
        for path in sorted(dst.glob("*.va")):
            text, notes = _normalize_va(path.read_text(encoding="utf-8", errors="ignore"))
            if notes:
                path.write_text(text, encoding="utf-8")
                task_notes.extend(f"{path.name}:{note}" for note in notes)
        for path in sorted(dst.glob("*.scs")):
            text, notes = _normalize_scs(path.read_text(encoding="utf-8", errors="ignore"), task_id)
            if notes:
                path.write_text(text, encoding="utf-8")
                task_notes.extend(f"{path.name}:{note}" for note in notes)
        meta_path = dst / "generation_meta.json"
        meta = {}
        if meta_path.exists():
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta["spectre_fix_overlay"] = {
            "source": "R26 teacher replay",
            "claim_boundary": "not cold-start",
            "notes": task_notes,
        }
        meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        manifest["tasks"][task_id] = {"sample_dir": str(dst), "notes": task_notes}

    (DST_GEN / "overlay_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"[r26-spectrefix-overlay] wrote {DST_GEN}")
    for task_id, item in manifest["tasks"].items():
        print(task_id, item["notes"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
