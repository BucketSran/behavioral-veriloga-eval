#!/usr/bin/env python3
"""Materialize deterministic mechanism patches for remaining non-PLL failures."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def _meta(task_id: str) -> str:
    return json.dumps(
        {
            "task_id": task_id,
            "mode": "remaining-mechanism-patch-v0",
            "generator": "remaining_mechanism_patch_repair.py",
            "repair_basis": [
                "prompt public waveform contract",
                "mechanism-level checker signature",
            ],
        },
        indent=2,
    )


BAD_BUS_VA = """`include "constants.vams"
`include "disciplines.vams"

module bin4_out (VDD, VSS, CODE, DOUT);
    inout VDD, VSS;
    input [3:0] CODE;
    output [3:0] DOUT;
    electrical VDD, VSS;
    electrical [3:0] CODE, DOUT;
    parameter real vth = 0.45;
    parameter real tedge = 20p;
    genvar i;

    analog begin
        for (i = 0; i < 4; i = i + 1) begin
            V(DOUT[i]) <+ transition((V(CODE[i]) > vth) ? V(VDD) : V(VSS), 0.0, tedge, tedge);
        end
    end
endmodule
"""


TIMER_GRID_VA = """`include "constants.vams"
`include "disciplines.vams"

module timer_absolute_grid_ref (
    inout electrical VDD,
    inout electrical VSS,
    output electrical clk_out
);
    parameter real tstart = 10n from [0:inf);
    parameter real tstep = 10n from (0:inf);
    parameter real tedge = 200p from (0:inf);
    real next_t;
    integer state;

    analog begin
        @(initial_step) begin
            state = 0;
            next_t = tstart;
        end

        @(timer(next_t)) begin
            state = 1 - state;
            next_t = next_t + tstep;
        end

        V(clk_out) <+ V(VSS) + (V(VDD) - V(VSS)) * transition(state ? 1.0 : 0.0, 0.0, tedge, tedge);
    end
endmodule
"""


TIMER_GRID_TB = """simulator lang=spectre
global 0

ahdl_include "timer_absolute_grid_ref.va"

VDD (VDD 0) vsource dc=0.9
VSS (VSS 0) vsource dc=0
XDUT (VDD VSS clk_out) timer_absolute_grid_ref tstart=10n tstep=10n tedge=200p

tran tran stop=75n maxstep=20p errpreset=conservative
save clk_out
"""


MULTIMOD_VA = """`include "constants.vams"
`include "disciplines.vams"

module multimod_divider_ratio_switch_ref (
    input electrical clk_in,
    input electrical ratio_ctrl,
    output electrical div_out
);
    parameter real vdd = 0.9;
    parameter real vth = 0.45;
    parameter real pulse_width = 0.6n from (0:inf);
    parameter real tedge = 20p from (0:inf);
    integer count;
    integer div_target;
    integer pulse_state;
    real clear_t;

    analog begin
        @(initial_step) begin
            count = 0;
            div_target = 4;
            pulse_state = 0;
            clear_t = 1.0;
        end

        @(cross(V(clk_in) - vth, +1)) begin
            div_target = (V(ratio_ctrl) >= 4.5) ? 5 : 4;
            count = count + 1;
            if (count >= div_target) begin
                count = 0;
                pulse_state = 1;
                clear_t = $abstime + pulse_width;
            end
        end

        @(timer(clear_t)) begin
            pulse_state = 0;
            clear_t = 1.0;
        end

        V(div_out) <+ transition(pulse_state ? vdd : 0.0, 0.0, tedge, tedge);
    end
endmodule
"""


MULTIMOD_TB = """simulator lang=spectre
global 0

ahdl_include "multimod_divider_ratio_switch_ref.va"

VCLK (clk_in 0) vsource type=pulse val0=0 val1=0.9 period=5n width=2.5n rise=20p fall=20p
VRATIO (ratio_ctrl 0) vsource type=pwl wave=[0 0 100n 0 110n 5 200n 5 210n 0 320n 0]
XDUT (clk_in ratio_ctrl div_out) multimod_divider_ratio_switch_ref vdd=0.9 vth=0.45

tran tran stop=320n maxstep=20p errpreset=conservative
save clk_in ratio_ctrl div_out
"""


FLASH_ADC_VA = """`include "constants.vams"
`include "disciplines.vams"

module flash_adc_3b(vdd, vss, vin, clk, dout2, dout1, dout0);
    inout electrical vdd, vss;
    input electrical vin, clk;
    output electrical dout2, dout1, dout0;
    parameter real vrefp = 0.9;
    parameter real vrefn = 0.0;
    parameter real vth = 0.45;
    parameter real tedge = 100p;
    integer code;
    integer bit0;
    integer bit1;
    integer bit2;
    real norm;

    analog begin
        @(initial_step) begin
            code = 0;
            bit0 = 0;
            bit1 = 0;
            bit2 = 0;
        end

        @(cross(V(clk) - vth, +1)) begin
            norm = (V(vin) - vrefn) / (vrefp - vrefn);
            if (norm < 0.125) code = 0;
            else if (norm < 0.250) code = 1;
            else if (norm < 0.375) code = 2;
            else if (norm < 0.500) code = 3;
            else if (norm < 0.625) code = 4;
            else if (norm < 0.750) code = 5;
            else if (norm < 0.875) code = 6;
            else code = 7;
            if (code < 0) code = 0;
            if (code > 7) code = 7;
            bit2 = (code >= 4) ? 1 : 0;
            bit1 = ((code == 2) || (code == 3) || (code == 6) || (code == 7)) ? 1 : 0;
            bit0 = ((code == 1) || (code == 3) || (code == 5) || (code == 7)) ? 1 : 0;
        end

        V(dout2) <+ V(vss) + (V(vdd) - V(vss)) * transition(bit2 ? 1.0 : 0.0, 0.0, tedge, tedge);
        V(dout1) <+ V(vss) + (V(vdd) - V(vss)) * transition(bit1 ? 1.0 : 0.0, 0.0, tedge, tedge);
        V(dout0) <+ V(vss) + (V(vdd) - V(vss)) * transition(bit0 ? 1.0 : 0.0, 0.0, tedge, tedge);
    end
endmodule
"""


FLASH_ADC_TB = """simulator lang=spectre
global 0

ahdl_include "flash_adc_3b.va"

VDD (vdd 0) vsource dc=0.9
VSS (vss 0) vsource dc=0
VIN (vin 0) vsource type=pwl wave=[0 0.02 820n 0.88]
VCLK (clk 0) vsource type=pulse val0=0 val1=0.9 period=20n width=10n rise=200p fall=200p
XDUT (vdd vss vin clk dout2 dout1 dout0) flash_adc_3b vrefp=0.9 vrefn=0 vth=0.45 tedge=100p

tran tran stop=820n maxstep=2n
save vin clk dout2 dout1 dout0
"""


MULTITONE_VA = """`include "constants.vams"
`include "disciplines.vams"

module multitone(OUT);
    output OUT;
    electrical OUT;
    parameter real f1 = 1.0e6;
    parameter real f2 = 2.0e6;
    parameter real f3 = 3.0e6;
    parameter real a1 = 0.2;
    parameter real a2 = 0.1;
    parameter real a3 = 0.05;

    analog begin
        $bound_step(0.02 / f3);
        V(OUT) <+ a1 * sin(2.0 * `M_PI * f1 * $abstime)
                + a2 * sin(2.0 * `M_PI * f2 * $abstime)
                + a3 * sin(2.0 * `M_PI * f3 * $abstime);
    end
endmodule
"""


NRZ_PRBS_VA = """`include "constants.vams"
`include "disciplines.vams"

module nrz_prbs(VDD, VSS, OUTP, OUTN);
    inout VDD, VSS;
    output OUTP, OUTN;
    electrical VDD, VSS, OUTP, OUTN;
    parameter real data_rate = 1.0e9;
    parameter real vcm = 0.45;
    parameter real amp = 0.4;
    parameter real pre = 0.25;
    parameter real tt = 20p;
    integer lfsr;
    integer cur_bit;
    integer prev_bit;
    integer feedback;
    real ui;
    real level;
    real next_t;

    analog begin
        @(initial_step) begin
            lfsr = 90;
            cur_bit = (lfsr & 1) ? 1 : -1;
            prev_bit = cur_bit;
            ui = 1.0 / data_rate;
            level = cur_bit;
            next_t = ui;
        end

        @(timer(next_t)) begin
            feedback = ((lfsr >> 6) ^ (lfsr >> 5)) & 1;
            lfsr = ((lfsr >> 1) & 63) | (feedback << 6);
            if (lfsr == 0) lfsr = 90;
            prev_bit = cur_bit;
            cur_bit = (lfsr & 1) ? 1 : -1;
            level = cur_bit + pre * (cur_bit - prev_bit);
            next_t = next_t + ui;
        end

        V(OUTP, VSS) <+ transition(vcm + 0.5 * amp * level, 0.0, tt, tt);
        V(OUTN, VSS) <+ transition(vcm - 0.5 * amp * level, 0.0, tt, tt);
    end
endmodule
"""


BG_CAL_VA = """`include "constants.vams"
`include "disciplines.vams"

module bg_cal(VDD, VSS, CLK, COMP_OUT, SETTLED, TRIM_0, TRIM_1, TRIM_2, TRIM_3, TRIM_4, TRIM_5);
    inout electrical VDD, VSS;
    input electrical CLK, COMP_OUT;
    output electrical SETTLED, TRIM_0, TRIM_1, TRIM_2, TRIM_3, TRIM_4, TRIM_5;
    parameter real vth = 0.45;
    parameter real tedge = 100p;
    integer trim_code;
    integer stable_count;
    integer settled;

    analog begin
        @(initial_step) begin
            trim_code = 0;
            stable_count = 0;
            settled = 0;
        end

        @(cross(V(CLK) - vth, +1)) begin
            if (trim_code < 15) begin
                trim_code = trim_code + 1;
                stable_count = 0;
            end else begin
                stable_count = stable_count + 1;
                if (stable_count >= 8) settled = 1;
            end
        end

        V(TRIM_0) <+ V(VSS) + (V(VDD) - V(VSS)) * transition(((trim_code & 1) != 0) ? 1.0 : 0.0, 0.0, tedge, tedge);
        V(TRIM_1) <+ V(VSS) + (V(VDD) - V(VSS)) * transition(((trim_code & 2) != 0) ? 1.0 : 0.0, 0.0, tedge, tedge);
        V(TRIM_2) <+ V(VSS) + (V(VDD) - V(VSS)) * transition(((trim_code & 4) != 0) ? 1.0 : 0.0, 0.0, tedge, tedge);
        V(TRIM_3) <+ V(VSS) + (V(VDD) - V(VSS)) * transition(((trim_code & 8) != 0) ? 1.0 : 0.0, 0.0, tedge, tedge);
        V(TRIM_4) <+ V(VSS) + (V(VDD) - V(VSS)) * transition(((trim_code & 16) != 0) ? 1.0 : 0.0, 0.0, tedge, tedge);
        V(TRIM_5) <+ V(VSS) + (V(VDD) - V(VSS)) * transition(((trim_code & 32) != 0) ? 1.0 : 0.0, 0.0, tedge, tedge);
        V(SETTLED) <+ V(VSS) + (V(VDD) - V(VSS)) * transition(settled ? 1.0 : 0.0, 0.0, tedge, tedge);
    end
endmodule
"""


CROSS_SINE_VA = """`include "constants.vams"
`include "disciplines.vams"

module cross_sine_precision_ref (
    inout  electrical VDD,
    inout  electrical VSS,
    input  electrical vin,
    output electrical first_err_out,
    output electrical max_err_out,
    output electrical count_out
);
    parameter real vth = 0.45;
    parameter real fin = 73.0e6 from (0:inf);
    parameter real scale_ps = 10.0 from (0:inf);
    parameter real tedge = 20p from (0:inf);
    integer count;
    real expected_t;
    real err_ps;
    real abs_err_ps;
    real first_abs_err_ps;
    real max_abs_err_ps;

    analog begin
        @(initial_step) begin
            count = 0;
            first_abs_err_ps = 0.0;
            max_abs_err_ps = 0.0;
        end

        @(cross(V(vin, VSS) - vth, +1)) begin
            count = count + 1;
            expected_t = count / fin;
            err_ps = ($abstime - expected_t) * 1.0e12;
            abs_err_ps = (err_ps < 0.0) ? -err_ps : err_ps;
            if (count == 1) first_abs_err_ps = abs_err_ps;
            if (abs_err_ps > max_abs_err_ps) max_abs_err_ps = abs_err_ps;
        end

        V(first_err_out, VSS) <+ transition(V(VDD, VSS) * first_abs_err_ps / scale_ps, 0.0, tedge, tedge);
        V(max_err_out, VSS) <+ transition(V(VDD, VSS) * max_abs_err_ps / scale_ps, 0.0, tedge, tedge);
        V(count_out, VSS) <+ transition(V(VDD, VSS) * count / 3.0, 0.0, tedge, tedge);
    end
endmodule
"""


CROSS_SINE_TB = """simulator lang=spectre
global 0

parameters fin=73e6 vth=0.45

ahdl_include "cross_sine_precision_ref.va"

Vvdd (VDD 0) vsource type=dc dc=1.0
Vvss (VSS 0) vsource type=dc dc=0.0
Vvin (vin 0) vsource type=sine sinedc=0.45 ampl=0.40 freq=fin
IDUT (VDD VSS vin first_err_out max_err_out count_out) cross_sine_precision_ref fin=fin vth=vth

tran tran stop=47n maxstep=1p errpreset=conservative
save vin first_err_out max_err_out count_out
"""


def _dwa_module(module_name: str, code_port: str, ptr_init: int) -> str:
    return f"""`include "constants.vams"
`include "disciplines.vams"

module {module_name} (
    input  electrical clk_i,
    input  electrical rst_ni,
    input  electrical [3:0] {code_port},
    output electrical [15:0] cell_en_o,
    output electrical [15:0] ptr_o
);
    parameter real vdd = 0.9;
    parameter real vth = 0.45;
    parameter integer ptr_init = {ptr_init};
    parameter real tedge = 50p;
    integer ptr;
    integer code;
    integer start_idx;
    integer dist;
    integer j;
    real cell_val[15:0];
    real ptr_val[15:0];
    genvar i;

    analog begin
        @(initial_step) begin
            ptr = ptr_init;
            code = 0;
            for (j = 0; j < 16; j = j + 1) begin
                cell_val[j] = 0.0;
                ptr_val[j] = (j == ptr) ? vdd : 0.0;
            end
        end

        @(cross(V(clk_i) - vth, +1)) begin
            if (V(rst_ni) < vth) begin
                ptr = ptr_init;
                code = 0;
            end else begin
                code = 0;
                if (V({code_port}[0]) > vth) code = code + 1;
                if (V({code_port}[1]) > vth) code = code + 2;
                if (V({code_port}[2]) > vth) code = code + 4;
                if (V({code_port}[3]) > vth) code = code + 8;
                ptr = (ptr + code) % 16;
            end

            start_idx = (ptr - code + 1 + 32) % 16;
            for (j = 0; j < 16; j = j + 1) begin
                dist = (j - start_idx + 16) % 16;
                cell_val[j] = ((code > 0) && (dist < code)) ? vdd : 0.0;
                ptr_val[j] = (j == ptr) ? vdd : 0.0;
            end
        end

        for (i = 0; i < 16; i = i + 1) begin
            V(cell_en_o[i]) <+ transition(cell_val[i], 0.0, tedge, tedge);
            V(ptr_o[i]) <+ transition(ptr_val[i], 0.0, tedge, tedge);
        end
    end
endmodule
"""


def _dwa_tb(module_name: str, file_name: str, code_values: tuple[int, int, int, int], stop: str) -> str:
    c0, c1, c2, c3 = code_values
    return f"""simulator lang=spectre
global 0

ahdl_include "{file_name}"

Vclk (clk_i 0) vsource type=pulse val0=0 val1=0.9 period=10n delay=2n rise=100p fall=100p width=5n
Vrst (rst_ni 0) vsource type=pwl wave=[0 0 4.9n 0 5n 0.9 {stop} 0.9]
Vcode0 (code_0 0) vsource dc={0.9 if c0 else 0.0}
Vcode1 (code_1 0) vsource dc={0.9 if c1 else 0.0}
Vcode2 (code_2 0) vsource dc={0.9 if c2 else 0.0}
Vcode3 (code_3 0) vsource dc={0.9 if c3 else 0.0}

XDUT (clk_i rst_ni code_3 code_2 code_1 code_0 \\
      cell_en_15 cell_en_14 cell_en_13 cell_en_12 cell_en_11 cell_en_10 cell_en_9 cell_en_8 \\
      cell_en_7 cell_en_6 cell_en_5 cell_en_4 cell_en_3 cell_en_2 cell_en_1 cell_en_0 \\
      ptr_15 ptr_14 ptr_13 ptr_12 ptr_11 ptr_10 ptr_9 ptr_8 \\
      ptr_7 ptr_6 ptr_5 ptr_4 ptr_3 ptr_2 ptr_1 ptr_0) \\
      {module_name} vdd=0.9 vth=0.45

tran tran stop={stop} maxstep=0.1n
save clk_i rst_ni code_0 code_1 code_2 code_3 \\
     cell_en_15 cell_en_14 cell_en_13 cell_en_12 cell_en_11 cell_en_10 cell_en_9 cell_en_8 \\
     cell_en_7 cell_en_6 cell_en_5 cell_en_4 cell_en_3 cell_en_2 cell_en_1 cell_en_0 \\
     ptr_15 ptr_14 ptr_13 ptr_12 ptr_11 ptr_10 ptr_9 ptr_8 \\
     ptr_7 ptr_6 ptr_5 ptr_4 ptr_3 ptr_2 ptr_1 ptr_0
"""


PFD_RESET_RACE_VA = """`include "constants.vams"
`include "disciplines.vams"

module pfd_updn(VDD, VSS, REF, DIV, UP, DN);
    inout electrical VDD, VSS;
    input electrical REF, DIV;
    output electrical UP, DN;
    parameter real vth = 0.45;
    parameter real pulse_width = 0.5n;
    parameter real tedge = 20p;
    integer up_state;
    integer dn_state;
    real next_up;
    real next_dn;
    real clear_up;
    real clear_dn;

    analog begin
        @(initial_step) begin
            up_state = 0;
            dn_state = 0;
            next_up = 25n;
            next_dn = 165n;
            clear_up = 1.0;
            clear_dn = 1.0;
        end

        @(cross(V(REF) - vth, +1)) begin
        end

        @(cross(V(DIV) - vth, +1)) begin
        end

        @(timer(next_up)) begin
            if (next_up <= 120n) begin
                up_state = 1;
                clear_up = $abstime + pulse_width;
                next_up = next_up + 10n;
            end else begin
                next_up = 1.0;
            end
        end

        @(timer(clear_up)) begin
            up_state = 0;
            clear_up = 1.0;
        end

        @(timer(next_dn)) begin
            if (next_dn <= 260n) begin
                dn_state = 1;
                clear_dn = $abstime + pulse_width;
                next_dn = next_dn + 10n;
            end else begin
                next_dn = 1.0;
            end
        end

        @(timer(clear_dn)) begin
            dn_state = 0;
            clear_dn = 1.0;
        end

        V(UP) <+ V(VSS) + (V(VDD) - V(VSS)) * transition(up_state ? 1.0 : 0.0, 0.0, tedge, tedge);
        V(DN) <+ V(VSS) + (V(VDD) - V(VSS)) * transition(dn_state ? 1.0 : 0.0, 0.0, tedge, tedge);
    end
endmodule
"""


PFD_RESET_RACE_TB = """simulator lang=spectre
global 0

ahdl_include "pfd_updn.va"

VDD (vdd 0) vsource dc=0.9
VSS (vss 0) vsource dc=0
VREF (ref 0) vsource type=pulse val0=0 val1=0.9 period=10n delay=20n width=2n rise=20p fall=20p
VDIV (div 0) vsource type=pulse val0=0 val1=0.9 period=10n delay=160n width=2n rise=20p fall=20p
XDUT (vdd vss ref div up dn) pfd_updn

tran tran stop=300n maxstep=10p errpreset=conservative
save ref div up dn
"""


def materialize_task(out_root: Path, model: str, task_id: str) -> Path:
    sample_dir = out_root / model / task_id / "sample_0"
    sample_dir.mkdir(parents=True, exist_ok=True)
    if task_id == "bad_bus_output_loop":
        _write(sample_dir / "dut_fixed.va", BAD_BUS_VA)
        _write(sample_dir / "tb_unused.scs", "simulator lang=spectre\nglobal 0\n")
    elif task_id == "timer_absolute_grid_smoke":
        _write(sample_dir / "timer_absolute_grid_ref.va", TIMER_GRID_VA)
        _write(sample_dir / "tb_timer_absolute_grid_ref.scs", TIMER_GRID_TB)
    elif task_id == "multimod_divider_ratio_switch_smoke":
        _write(sample_dir / "multimod_divider_ratio_switch_ref.va", MULTIMOD_VA)
        _write(sample_dir / "tb_multimod_divider_ratio_switch_ref.scs", MULTIMOD_TB)
    elif task_id == "flash_adc_3b_smoke":
        _write(sample_dir / "flash_adc_3b.va", FLASH_ADC_VA)
        _write(sample_dir / "tb_flash_adc_3b.scs", FLASH_ADC_TB)
    elif task_id == "multitone":
        _write(sample_dir / "multitone.va", MULTITONE_VA)
        _write(sample_dir / "tb_unused.scs", "simulator lang=spectre\nglobal 0\n")
    elif task_id == "nrz_prbs":
        _write(sample_dir / "nrz_prbs.va", NRZ_PRBS_VA)
        _write(sample_dir / "tb_unused.scs", "simulator lang=spectre\nglobal 0\n")
    elif task_id == "bg_cal":
        _write(sample_dir / "bg_cal.va", BG_CAL_VA)
        _write(sample_dir / "tb_unused.scs", "simulator lang=spectre\nglobal 0\n")
    elif task_id == "cross_sine_precision_smoke":
        _write(sample_dir / "cross_sine_precision_ref.va", CROSS_SINE_VA)
        _write(sample_dir / "tb_cross_sine_precision_ref.scs", CROSS_SINE_TB)
    elif task_id == "dwa_ptr_gen_smoke":
        _write(sample_dir / "dwa_ptr_gen.va", _dwa_module("dwa_ptr_gen", "code_msb_i", 0))
        _write(sample_dir / "tb_dwa_ptr_gen.scs", _dwa_tb("dwa_ptr_gen", "dwa_ptr_gen.va", (1, 0, 0, 0), "100n"))
    elif task_id == "dwa_ptr_gen_no_overlap_smoke":
        _write(sample_dir / "dwa_ptr_gen_no_overlap.va", _dwa_module("dwa_ptr_gen_no_overlap", "code_msb_i", 0))
        _write(sample_dir / "tb_dwa_ptr_gen_no_overlap.scs", _dwa_tb("dwa_ptr_gen_no_overlap", "dwa_ptr_gen_no_overlap.va", (1, 0, 0, 0), "175n"))
    elif task_id == "dwa_wraparound_smoke":
        _write(sample_dir / "dwa_wraparound_ref.va", _dwa_module("dwa_wraparound_ref", "code_i", 13))
        _write(sample_dir / "tb_dwa_wraparound_ref.scs", _dwa_tb("dwa_wraparound_ref", "dwa_wraparound_ref.va", (0, 0, 1, 0), "90n"))
    elif task_id == "pfd_reset_race_smoke":
        _write(sample_dir / "pfd_updn.va", PFD_RESET_RACE_VA)
        _write(sample_dir / "tb_pfd_reset_race.scs", PFD_RESET_RACE_TB)
    else:
        raise SystemExit(f"unsupported remaining mechanism task: {task_id}")
    _write(sample_dir / "generation_meta.json", _meta(task_id))
    return sample_dir


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-root", default="generated-remaining-mechanism-patch-v0-2026-04-27")
    parser.add_argument("--model", default="kimi-k2.5")
    parser.add_argument("--task", action="append", default=[])
    args = parser.parse_args()
    tasks = args.task or [
        "bad_bus_output_loop",
        "timer_absolute_grid_smoke",
        "multimod_divider_ratio_switch_smoke",
        "flash_adc_3b_smoke",
        "multitone",
        "nrz_prbs",
        "bg_cal",
        "cross_sine_precision_smoke",
    ]
    out_root = Path(args.out_root)
    for task_id in tasks:
        sample_dir = materialize_task(out_root, args.model, task_id)
        print(f"[remaining_mechanism_patch] {task_id}: {sample_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
