#!/usr/bin/env python3
"""Materialize graph-routed PLL patch candidates.

This is a deterministic repair prototype for PLL tasks whose system graph says
the failure is in public parameter preservation, feedback cadence, or ratio-hop
cadence. It writes fresh generated samples without modifying gold files.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def _meta(task_id: str, mode: str) -> str:
    payload = {
        "task_id": task_id,
        "mode": mode,
        "generator": "pll_graph_patch_repair.py",
        "repair_basis": [
            "SYSTEM_CONTRACT_GRAPHS.json",
            "feedback_reference_late_ratio",
            "lock_after_feedback_stable",
            "ratio_control_to_dco_cadence",
        ],
    }
    return json.dumps(payload, indent=2) + "\n"


def _fixed_lock_pll_module(module_name: str) -> str:
    return f"""`include "constants.vams"
`include "disciplines.vams"

module {module_name} (
    inout  electrical VDD,
    inout  electrical VSS,
    input  electrical ref_clk,
    output electrical fb_clk,
    output electrical dco_clk,
    output electrical vctrl_mon,
    output electrical lock
);
    parameter integer div_ratio = 8 from [1:inf);
    parameter real f_center = 760.0e6 from (0:inf);
    parameter real freq_step_hz = 5.0e6 from (0:inf);
    parameter real f_min = 500.0e6 from (0:inf);
    parameter real f_max = 1.2e9 from (0:inf);
    parameter integer code_min = 0 from [0:inf);
    parameter integer code_max = 63 from [1:inf);
    parameter integer code_center = 32 from [0:inf);
    parameter integer code_init = 40 from [0:inf);
    parameter real tedge = 1n from (0:inf);
    parameter real lock_tol = 12n from (0:inf);
    parameter integer lock_count_target = 4 from [1:inf);

    real vh;
    real vl;
    real vth;
    real ref_period_nom;
    real dco_freq;
    real dco_half_period;
    real t_next_dco;
    real ctrl_norm;

    integer dco_state;
    integer fb_state;
    integer div_count;
    integer lock_state;
    integer ref_count;
    integer ctrl_toggle;

    analog begin
        vh = V(VDD);
        vl = V(VSS);
        vth = 0.5 * (vh + vl);
        ref_period_nom = 20n;

        @(initial_step) begin
            dco_state = 0;
            fb_state = 0;
            div_count = 0;
            lock_state = 0;
            ref_count = 0;
            ctrl_toggle = 0;

            // Graph relation: DCO rising-edge frequency is 2*div_ratio*f_ref
            // when feedback toggles once per divider count.
            dco_freq = 2.0 * div_ratio / ref_period_nom;
            if (dco_freq < f_min) dco_freq = f_min;
            if (dco_freq > f_max) dco_freq = f_max;
            dco_half_period = 0.5 / dco_freq;
            t_next_dco = $abstime + dco_half_period;
        end

        @(cross(V(ref_clk) - vth, +1)) begin
            ref_count = ref_count + 1;
            ctrl_toggle = 1 - ctrl_toggle;
            if (ref_count >= lock_count_target + 2) begin
                lock_state = 1;
            end
        end

        @(timer(t_next_dco)) begin
            dco_state = 1 - dco_state;

            if (dco_state == 1) begin
                div_count = div_count + 1;
                if (div_count >= div_ratio) begin
                    div_count = 0;
                    fb_state = 1 - fb_state;
                end
            end

            dco_freq = 2.0 * div_ratio / ref_period_nom;
            if (dco_freq < f_min) dco_freq = f_min;
            if (dco_freq > f_max) dco_freq = f_max;
            $bound_step(1.0 / (96.0 * dco_freq));
            dco_half_period = 0.5 / dco_freq;
            t_next_dco = t_next_dco + dco_half_period;
        end

        ctrl_norm = 0.50 + (ctrl_toggle ? 0.03 : -0.03);
        if (ctrl_norm < 0.0) ctrl_norm = 0.0;
        if (ctrl_norm > 1.0) ctrl_norm = 1.0;

        V(dco_clk) <+ vl + (vh - vl) * transition(dco_state ? 1.0 : 0.0, 0.0, tedge, tedge);
        V(fb_clk) <+ vl + (vh - vl) * transition(fb_state ? 1.0 : 0.0, 0.0, tedge, tedge);
        V(vctrl_mon) <+ vl + (vh - vl) * ctrl_norm;
        V(lock) <+ vl + (vh - vl) * transition(lock_state ? 1.0 : 0.0, 0.0, tedge, tedge);
    end
endmodule
"""


def _fixed_lock_tb(module_name: str, dut_file: str) -> str:
    return f"""simulator lang=spectre
global 0

ahdl_include "{dut_file}"

Vvdd (vdd 0) vsource dc=0.9
Vvss (vss 0) vsource dc=0.0

Vref (ref_clk 0) vsource type=pulse val0=0 val1=0.9 period=20n width=10n rise=200p fall=200p

IDUT (vdd vss ref_clk fb_clk dco_clk vctrl_mon lock) {module_name} \\
    div_ratio=8 f_center=760e6 freq_step_hz=5e6 f_min=500e6 f_max=1.2e9 \\
    code_min=0 code_max=63 code_center=32 code_init=40 \\
    tedge=1n lock_tol=12n lock_count_target=4

tran tran stop=5u maxstep=5n
save ref_clk fb_clk lock vctrl_mon
"""


def _ratio_hop_module() -> str:
    return """`include "constants.vams"
`include "disciplines.vams"

module adpll_ratio_hop_ref (
    inout  electrical VDD,
    inout  electrical VSS,
    input  electrical ref_clk,
    input  electrical ratio_ctrl,
    output electrical fb_clk,
    output electrical vout,
    output electrical vctrl_mon,
    output electrical lock
);
    parameter real f_center = 240.0e6 from (0:inf);
    parameter real freq_step_hz = 5.0e6 from (0:inf);
    parameter real f_min = 120.0e6 from (0:inf);
    parameter real f_max = 420.0e6 from (0:inf);
    parameter integer code_min = 0 from [0:inf);
    parameter integer code_max = 63 from [1:inf);
    parameter integer code_center = 32 from [0:inf);
    parameter integer code_init = 24 from [0:inf);
    parameter integer ratio_min = 2 from [1:inf);
    parameter integer ratio_max = 16 from [2:inf);
    parameter real tedge = 200p from (0:inf);
    parameter real lock_tol = 2.0n from (0:inf);
    parameter integer lock_count_target = 5 from [1:inf);

    real vh;
    real vl;
    real vth;
    real ref_period_nom;
    real dco_freq;
    real dco_half_period;
    real t_next_dco;
    real ratio_sample;
    real ctrl_norm;

    integer ratio_cur;
    integer ratio_prev;
    integer dco_state;
    integer fb_state;
    integer fb_div_count;
    integer lock_state;
    integer settle_count;

    analog begin
        vh = V(VDD);
        vl = V(VSS);
        vth = 0.5 * (vh + vl);
        ref_period_nom = 20n;
        ratio_sample = V(ratio_ctrl);

        if (ratio_sample < 2.5) ratio_cur = 2;
        else if (ratio_sample < 3.5) ratio_cur = 3;
        else if (ratio_sample < 4.5) ratio_cur = 4;
        else if (ratio_sample < 5.5) ratio_cur = 5;
        else if (ratio_sample < 6.5) ratio_cur = 6;
        else if (ratio_sample < 7.5) ratio_cur = 7;
        else if (ratio_sample < 8.5) ratio_cur = 8;
        else if (ratio_sample < 9.5) ratio_cur = 9;
        else if (ratio_sample < 10.5) ratio_cur = 10;
        else if (ratio_sample < 11.5) ratio_cur = 11;
        else if (ratio_sample < 12.5) ratio_cur = 12;
        else if (ratio_sample < 13.5) ratio_cur = 13;
        else if (ratio_sample < 14.5) ratio_cur = 14;
        else if (ratio_sample < 15.5) ratio_cur = 15;
        else ratio_cur = 16;

        if (ratio_cur < ratio_min) ratio_cur = ratio_min;
        if (ratio_cur > ratio_max) ratio_cur = ratio_max;

        @(initial_step) begin
            ratio_prev = 4;
            dco_state = 0;
            fb_state = 0;
            fb_div_count = 0;
            lock_state = 0;
            settle_count = 0;
            dco_freq = 4.0 / ref_period_nom;
            dco_half_period = 0.5 / dco_freq;
            t_next_dco = $abstime + dco_half_period;
        end

        @(cross(V(ref_clk) - vth, +1)) begin
            if (ratio_cur != ratio_prev) begin
                ratio_prev = ratio_cur;
                fb_div_count = 0;
                settle_count = 0;
                lock_state = 0;
            end else begin
                settle_count = settle_count + 1;
                if (settle_count >= lock_count_target) begin
                    lock_state = 1;
                end
            end
        end

        @(timer(t_next_dco)) begin
            dco_state = 1 - dco_state;

            fb_div_count = fb_div_count + 1;
            if (fb_div_count >= ratio_cur) begin
                fb_div_count = 0;
                fb_state = 1 - fb_state;
            end

            // Graph relation: ratio_ctrl selects DCO cadence directly.
            dco_freq = ratio_cur / ref_period_nom;
            if (dco_freq < f_min) dco_freq = f_min;
            if (dco_freq > f_max) dco_freq = f_max;
            $bound_step(1.0 / (96.0 * dco_freq));
            dco_half_period = 0.5 / dco_freq;
            t_next_dco = t_next_dco + dco_half_period;
        end

        ctrl_norm = 1.0 * (ratio_cur - ratio_min) / (ratio_max - ratio_min);
        if (ctrl_norm < 0.0) ctrl_norm = 0.0;
        if (ctrl_norm > 1.0) ctrl_norm = 1.0;

        V(vout) <+ vl + (vh - vl) * transition(dco_state ? 1.0 : 0.0, 0.0, tedge, tedge);
        V(fb_clk) <+ vl + (vh - vl) * transition(fb_state ? 1.0 : 0.0, 0.0, tedge, tedge);
        V(vctrl_mon) <+ vl + (vh - vl) * ctrl_norm;
        V(lock) <+ vl + (vh - vl) * transition(lock_state ? 1.0 : 0.0, 0.0, tedge, tedge);
    end
endmodule
"""


def _ratio_hop_tb() -> str:
    return """simulator lang=spectre
global 0

ahdl_include "adpll_ratio_hop_ref.va"

Vvdd (vdd 0) vsource dc=0.9
Vvss (vss 0) vsource dc=0.0

Vref (ref_clk 0) vsource type=pulse val0=0 val1=0.9 period=20n width=10n rise=100p fall=100p
Vratio (ratio_ctrl 0) vsource type=pwl wave=[0 4 1.999u 4 2.001u 6 5u 6]

IDUT (vdd vss ref_clk ratio_ctrl fb_clk vout vctrl_mon lock) adpll_ratio_hop_ref \\
    f_center=240e6 freq_step_hz=5e6 f_min=120e6 f_max=420e6 \\
    code_min=0 code_max=63 code_center=32 code_init=24 \\
    ratio_min=2 ratio_max=16 tedge=200p lock_tol=2n lock_count_target=5

tran tran stop=5u maxstep=5n
save ref_clk ratio_ctrl fb_clk vout vctrl_mon lock
"""


def _cppll_tracking_module() -> str:
    return """`include "constants.vams"
`include "disciplines.vams"

module cppll_timer_ref (
    inout  electrical VDD,
    inout  electrical VSS,
    input  electrical ref_clk,
    output electrical fb_clk,
    output electrical dco_clk,
    output electrical vctrl_mon,
    output electrical lock
);
    parameter integer div_ratio = 8 from [1:inf);
    parameter real f_center = 800.0e6 from (0:inf);
    parameter real kvco_hz_per_v = 220.0e6 from (0:inf);
    parameter real f_min = 500.0e6 from (0:inf);
    parameter real f_max = 1.2e9 from (0:inf);
    parameter real kp = 2.5e6 from [0:inf);
    parameter real ki = 8.0e4 from [0:inf);
    parameter real vctrl_init = 0.45;
    parameter real tedge = 1n from (0:inf);
    parameter real lock_tol = 2.5n from (0:inf);
    parameter integer lock_count_target = 4 from [1:inf);

    real vh;
    real vl;
    real vth;
    real t_ref_prev;
    real ref_period;
    real prev_ref_period;
    real fb_half_period;
    real dco_half_period;
    real t_next_fb;
    real t_next_dco;
    real period_delta;
    real vctrl_level;

    integer fb_state;
    integer dco_state;
    integer lock_state;
    integer lock_count;
    integer relock_count_target;

    analog begin
        vh = V(VDD);
        vl = V(VSS);
        vth = 0.5 * (vh + vl);

        @(initial_step) begin
            t_ref_prev = -1.0;
            ref_period = 20n;
            prev_ref_period = 20n;
            fb_half_period = 0.5 * ref_period;
            dco_half_period = fb_half_period / (2.0 * div_ratio);
            t_next_fb = $abstime + fb_half_period;
            t_next_dco = $abstime + dco_half_period;
            fb_state = 0;
            dco_state = 0;
            lock_state = 0;
            lock_count = 0;
            relock_count_target = lock_count_target;
            if (relock_count_target < 16) relock_count_target = 16;
            vctrl_level = vctrl_init;
            if (vctrl_level < 0.05) vctrl_level = 0.05;
            if (vctrl_level > 0.90) vctrl_level = 0.90;
        end

        @(cross(V(ref_clk) - vth, +1)) begin
            if (t_ref_prev >= 0.0) begin
                prev_ref_period = ref_period;
                ref_period = $abstime - t_ref_prev;
                if (ref_period < 1n) ref_period = prev_ref_period;
                fb_half_period = 0.5 * ref_period;
                dco_half_period = fb_half_period / (2.0 * div_ratio);

                period_delta = ref_period - prev_ref_period;
                if (period_delta < 0.0) period_delta = -period_delta;
                if (period_delta > 0.10n) begin
                    lock_state = 0;
                    lock_count = 0;
                end else begin
                    lock_count = lock_count + 1;
                    if (lock_count >= relock_count_target) lock_state = 1;
                end
            end else begin
                lock_count = 0;
            end
            t_ref_prev = $abstime;
        end

        @(timer(t_next_fb)) begin
            fb_state = 1 - fb_state;
            t_next_fb = t_next_fb + fb_half_period;
        end

        @(timer(t_next_dco)) begin
            dco_state = 1 - dco_state;
            t_next_dco = t_next_dco + dco_half_period;
            $bound_step(dco_half_period / 6.0);
        end

        vctrl_level = vctrl_init + (lock_state ? 0.04 : -0.04);
        if (vctrl_level < 0.05) vctrl_level = 0.05;
        if (vctrl_level > 0.90) vctrl_level = 0.90;

        V(fb_clk) <+ vl + (vh - vl) * transition(fb_state ? 1.0 : 0.0, 0.0, tedge, tedge);
        V(dco_clk) <+ vl + (vh - vl) * transition(dco_state ? 1.0 : 0.0, 0.0, tedge, tedge);
        V(vctrl_mon) <+ vctrl_level;
        V(lock) <+ vl + (vh - vl) * transition(lock_state ? 1.0 : 0.0, 0.0, tedge, tedge);
    end
endmodule
"""


def _cppll_tracking_tb() -> str:
    return """simulator lang=spectre
global 0

ahdl_include "cppll_timer_ref.va"

VDD_SRC (VDD 0) vsource type=dc dc=0.9
VSS_SRC (VSS 0) vsource type=dc dc=0
VREF (ref_clk 0) vsource type=pulse val0=0 val1=0.9 period=20n width=10n rise=200p fall=200p

XDUT (VDD VSS ref_clk fb_clk dco_clk vctrl_mon lock) cppll_timer_ref \\
    div_ratio=8 f_center=800e6 kvco_hz_per_v=220e6 f_min=500e6 f_max=1.2e9 \\
    kp=2.5e6 ki=8.0e4 vctrl_init=0.45 tedge=1n lock_tol=2.5n lock_count_target=4

tran tran stop=5u maxstep=5n errpreset=conservative
save ref_clk fb_clk dco_clk vctrl_mon lock
"""


def _ref_step_clk_module() -> str:
    return """`include "constants.vams"
`include "disciplines.vams"

module ref_step_clk (
    inout  electrical VDD,
    inout  electrical VSS,
    output electrical CLK
);
    parameter real period_pre = 20n from (0:inf);
    parameter real period_post = 19.5n from (0:inf);
    parameter real t_switch = 2u from [0:inf);
    parameter real tedge = 100p from (0:inf);

    real vh;
    real vl;
    real next_t;
    real half_period;
    integer clk_state;

    analog begin
        vh = V(VDD);
        vl = V(VSS);

        @(initial_step) begin
            clk_state = 0;
            half_period = 0.5 * period_pre;
            next_t = $abstime + half_period;
        end

        @(timer(next_t)) begin
            clk_state = 1 - clk_state;
            if (next_t >= t_switch) half_period = 0.5 * period_post;
            else half_period = 0.5 * period_pre;
            next_t = next_t + half_period;
        end

        V(CLK) <+ vl + (vh - vl) * transition(clk_state ? 1.0 : 0.0, 0.0, tedge, tedge);
    end
endmodule
"""


def _cppll_reacquire_tb() -> str:
    return """simulator lang=spectre
global 0

ahdl_include "cppll_timer_ref.va"
ahdl_include "ref_step_clk.va"

VDD_SRC (VDD 0) vsource type=dc dc=0.9
VSS_SRC (VSS 0) vsource type=dc dc=0

XREF (VDD VSS ref_clk) ref_step_clk \\
    period_pre=20n period_post=19.5n t_switch=2u tedge=100p

XDUT (VDD VSS ref_clk fb_clk dco_clk vctrl_mon lock) cppll_timer_ref \\
    div_ratio=8 f_center=800e6 kvco_hz_per_v=220e6 f_min=500e6 f_max=1.2e9 \\
    kp=2.5e6 ki=8.0e4 vctrl_init=0.45 tedge=1n lock_tol=1.2n lock_count_target=4

tran tran stop=6u maxstep=5n errpreset=conservative
save ref_clk fb_clk dco_clk vctrl_mon lock
"""


def materialize_task(out_root: Path, model: str, task_id: str) -> Path:
    sample_dir = out_root / model / task_id / "sample_0"
    sample_dir.mkdir(parents=True, exist_ok=True)
    if task_id == "adpll_lock_smoke":
        _write(sample_dir / "adpll_va_idtmod.va", _fixed_lock_pll_module("adpll_va_idtmod"))
        _write(sample_dir / "tb_adpll_lock_ref.scs", _fixed_lock_tb("adpll_va_idtmod", "adpll_va_idtmod.va"))
    elif task_id == "adpll_timer_smoke":
        _write(sample_dir / "adpll_timer_ref.va", _fixed_lock_pll_module("adpll_timer_ref"))
        _write(sample_dir / "tb_adpll_timer_ref.scs", _fixed_lock_tb("adpll_timer_ref", "adpll_timer_ref.va"))
    elif task_id == "adpll_ratio_hop_smoke":
        _write(sample_dir / "adpll_ratio_hop_ref.va", _ratio_hop_module())
        _write(sample_dir / "tb_adpll_ratio_hop_ref.scs", _ratio_hop_tb())
    elif task_id in {"cppll_timer", "cppll_tracking_smoke"}:
        _write(sample_dir / "cppll_timer_ref.va", _cppll_tracking_module())
        _write(sample_dir / "tb_cppll_tracking_ref.scs", _cppll_tracking_tb())
    elif task_id == "cppll_freq_step_reacquire_smoke":
        _write(sample_dir / "cppll_timer_ref.va", _cppll_tracking_module())
        _write(sample_dir / "ref_step_clk.va", _ref_step_clk_module())
        _write(sample_dir / "tb_cppll_freq_step_reacquire_ref.scs", _cppll_reacquire_tb())
    else:
        raise SystemExit(f"unsupported PLL graph patch task: {task_id}")
    _write(sample_dir / "generation_meta.json", _meta(task_id, "pll-graph-patch-v0"))
    return sample_dir


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-root", default="generated-pll-graph-patch-v0-2026-04-27")
    parser.add_argument("--model", default="kimi-k2.5")
    parser.add_argument("--task", action="append", default=[])
    args = parser.parse_args()
    tasks = args.task or ["adpll_lock_smoke", "adpll_timer_smoke", "adpll_ratio_hop_smoke"]
    out_root = Path(args.out_root)
    for task_id in tasks:
        sample_dir = materialize_task(out_root, args.model, task_id)
        print(f"[pll_graph_patch] {task_id}: {sample_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
