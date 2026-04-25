#!/usr/bin/env python3
"""Small-set template-guided EVAS repair probe.

This script checks whether bounded mechanism templates can rescue several
clear behavior-failure families before we scale the idea to Hard16/full92.
It is a deterministic probe, not yet the production repair policy.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from simulate_evas import run_case
from template_guided_repair import clk_divider_variants


ROOT = Path(__file__).resolve().parents[1]
A_KIMI_ROOT = ROOT / "generated-experiment/condition-A/kimi-k2.5/kimi-k2.5"
G_KIMI_ROOT = ROOT / "generated-table2-evas-guided-repair-3round-skill/kimi-k2.5"


@dataclass(frozen=True)
class Variant:
    name: str
    description: str
    file_name: str
    body: str


@dataclass(frozen=True)
class TaskConfig:
    task_id: str
    task_dir: Path
    tb_path: Path
    anchor: Path
    variants: tuple[Variant, ...]


def _json_write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _rank(result: dict) -> tuple:
    scores = result.get("scores", {})
    return (
        int(result.get("status") == "PASS"),
        float(scores.get("weighted_total", 0.0)),
    )


def _run_case_safe(
    task_dir: Path,
    dut_path: Path,
    tb_path: Path,
    output_root: Path,
    timeout_s: int,
    task_id: str,
) -> dict:
    try:
        return run_case(
            task_dir,
            dut_path,
            tb_path,
            output_root=output_root,
            timeout_s=timeout_s,
            task_id_override=task_id,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "task_id": task_id,
            "status": "FAIL_INFRA",
            "backend_used": "evas",
            "scores": {
                "dut_compile": 0.0,
                "tb_compile": 0.0,
                "sim_correct": 0.0,
                "weighted_total": 0.0,
            },
            "artifacts": [str(dut_path), str(tb_path), str(output_root / "tran.csv")],
            "notes": [f"evas_timeout>{timeout_s}s", f"cmd={getattr(exc, 'cmd', '')}"],
            "stdout_tail": "",
        }


def _safe_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", name)


def _lfsr_body(output_invert: bool = False, output_bit: int = 31) -> str:
    invert = "!" if output_invert else ""
    return f"""`include "constants.vams"
`include "disciplines.vams"

module lfsr(DPN, VDD, VSS, CLK, EN, RSTB);
    output DPN;
    inout VDD, VSS;
    input CLK, EN, RSTB;
    electrical DPN, VDD, VSS, CLK, EN, RSTB;

    parameter integer seed = 123;
    parameter real vth = 0.45;
    parameter real trf = 50p;

    integer state;
    integer feedback;
    integer out_bit;
    real dpn_level;

    analog begin
        @(initial_step or cross(V(RSTB) - vth, -1)) begin
            state = seed;
            if (state == 0)
                state = 1;
            out_bit = (state >> {output_bit}) & 1;
            dpn_level = ({invert}out_bit) ? V(VDD, VSS) : 0.0;
        end

        @(cross(V(CLK) - vth, +1)) begin
            if (V(RSTB) > vth && V(EN) > vth) begin
                feedback = ((state >> 30) ^ (state >> 20) ^ (state >> 1) ^ state) & 1;
                state = ((state << 1) & 2147483647) | feedback;
                if (state == 0)
                    state = 1;
                out_bit = (state >> {output_bit}) & 1;
                dpn_level = ({invert}out_bit) ? V(VDD, VSS) : 0.0;
            end
        end

        V(DPN, VSS) <+ transition(dpn_level, 0, trf, trf);
    end
endmodule
"""


def _pfd_body(clear_mode: str = "immediate") -> str:
    clear_delay = "0.5n" if clear_mode == "timer_0p5n" else "0.2n"
    timer_block = ""
    ref_block = """
        @(cross(V(REF) - vth, +1)) begin
            up_state = 1;
            if (dn_state) begin
                up_state = 0;
                dn_state = 0;
            end
        end
"""
    div_block = """
        @(cross(V(DIV) - vth, +1)) begin
            dn_state = 1;
            if (up_state) begin
                up_state = 0;
                dn_state = 0;
            end
        end
"""
    if clear_mode != "immediate":
        ref_block = """
        @(cross(V(REF) - vth, +1)) begin
            up_state = 1;
            if (dn_state)
                clear_pending = 1;
        end
"""
        div_block = """
        @(cross(V(DIV) - vth, +1)) begin
            dn_state = 1;
            if (up_state)
                clear_pending = 1;
        end
"""
        timer_block = f"""
        @(timer($abstime + {clear_delay})) begin
            if (clear_pending) begin
                up_state = 0;
                dn_state = 0;
                clear_pending = 0;
            end
        end
"""
    return f"""`include "constants.vams"
`include "disciplines.vams"

module pfd_updn(VDD, VSS, REF, DIV, UP, DN);
    inout VDD, VSS;
    input REF, DIV;
    output UP, DN;
    electrical VDD, VSS, REF, DIV, UP, DN;

    parameter real vth = 0.45;
    parameter real tedge = 20p;
    integer up_state;
    integer dn_state;
    integer clear_pending;

    analog begin
        @(initial_step) begin
            up_state = 0;
            dn_state = 0;
            clear_pending = 0;
        end
{ref_block}
{div_block}
{timer_block}
        V(UP, VSS) <+ transition(up_state ? V(VDD, VSS) : 0.0, 0, tedge, tedge);
        V(DN, VSS) <+ transition(dn_state ? V(VDD, VSS) : 0.0, 0, tedge, tedge);
    end
endmodule
"""


def _multimod_body(reset_to_one: bool = False) -> str:
    reset_expr = "1" if reset_to_one else "0"
    return f"""`include "constants.vams"
`include "disciplines.vams"

module multimod_divider_ref(clk_in, mod, mod_0, mod_1, mod_2, mod_3, prescaler_out);
    input clk_in, mod, mod_0, mod_1, mod_2, mod_3;
    output prescaler_out;
    electrical clk_in, mod, mod_0, mod_1, mod_2, mod_3, prescaler_out;

    parameter real vdd = 0.9;
    parameter real vth = 0.45;
    parameter real trf = 10p;

    integer base_count;
    integer target_count;
    integer edge_count;
    integer pulse_state;

    analog begin
        @(initial_step) begin
            base_count = 1;
            target_count = 1;
            edge_count = 0;
            pulse_state = 0;
        end

        @(cross(V(clk_in) - vth, +1)) begin
            base_count = (V(mod_0) > vth ? 1 : 0)
                       + (V(mod_1) > vth ? 2 : 0)
                       + (V(mod_2) > vth ? 4 : 0)
                       + (V(mod_3) > vth ? 8 : 0);
            if (base_count < 1)
                base_count = 1;
            target_count = base_count + (V(mod) > vth ? 1 : 0);
            edge_count = edge_count + 1;
            if (edge_count >= target_count) begin
                pulse_state = 1;
                edge_count = {reset_expr};
            end else begin
                pulse_state = 0;
            end
        end

        V(prescaler_out) <+ transition(pulse_state ? vdd : 0.0, 0, trf, trf);
    end
endmodule
"""


def _serializer_frame_body(load_on_high: bool = True) -> str:
    load_cond = "V(load, vss) > vth" if load_on_high else "V(load, vss) <= vth"
    return f"""`include "constants.vams"
`include "disciplines.vams"

module serializer_frame_alignment_ref(
    vdd, vss, clk, load,
    din7, din6, din5, din4, din3, din2, din1, din0,
    sout, frame
);
    inout vdd, vss;
    input clk, load;
    input din7, din6, din5, din4, din3, din2, din1, din0;
    output sout, frame;
    electrical vdd, vss, clk, load;
    electrical din7, din6, din5, din4, din3, din2, din1, din0;
    electrical sout, frame;

    parameter real vth = 0.45;
    parameter real trf = 40p;

    integer shreg;
    integer bit_idx;
    integer active;
    real sout_val;
    real frame_val;

    analog begin
        @(initial_step) begin
            shreg = 0;
            bit_idx = 7;
            active = 0;
            sout_val = 0.0;
            frame_val = 0.0;
        end

        @(cross(V(clk, vss) - vth, +1)) begin
            if ({load_cond}) begin
                shreg = 0;
                if (V(din0, vss) > vth) shreg = shreg + 1;
                if (V(din1, vss) > vth) shreg = shreg + 2;
                if (V(din2, vss) > vth) shreg = shreg + 4;
                if (V(din3, vss) > vth) shreg = shreg + 8;
                if (V(din4, vss) > vth) shreg = shreg + 16;
                if (V(din5, vss) > vth) shreg = shreg + 32;
                if (V(din6, vss) > vth) shreg = shreg + 64;
                if (V(din7, vss) > vth) shreg = shreg + 128;
                bit_idx = 7;
                active = 1;
                frame_val = 0.0;
            end else if (active) begin
                sout_val = (((shreg >> bit_idx) & 1) == 1) ? V(vdd, vss) : 0.0;
                frame_val = (bit_idx == 7) ? V(vdd, vss) : 0.0;
                if (bit_idx == 0) begin
                    bit_idx = 7;
                    active = 0;
                end else begin
                    bit_idx = bit_idx - 1;
                end
            end else begin
                frame_val = 0.0;
            end
        end

        V(sout, vss) <+ transition(sout_val, 0, trf, trf);
        V(frame, vss) <+ transition(frame_val, 0, trf, trf);
    end
endmodule
"""


def _dff_rst_body() -> str:
    return """`include "constants.vams"
`include "disciplines.vams"

module dff_rst(VDD, VSS, D, CLK, RST, Q, QB);
    inout VDD, VSS;
    input D, CLK, RST;
    output Q, QB;
    electrical VDD, VSS, D, CLK, RST, Q, QB;

    parameter real tedge = 10p;
    real q_level;
    real qb_level;
    real vth;

    analog begin
        @(initial_step) begin
            q_level = 0.0;
            qb_level = V(VDD, VSS);
            vth = 0.5 * V(VDD, VSS);
        end

        @(cross(V(CLK, VSS) - vth, +1)) begin
            vth = 0.5 * V(VDD, VSS);
            if (V(RST, VSS) > vth)
                q_level = 0.0;
            else
                q_level = (V(D, VSS) > vth) ? V(VDD, VSS) : 0.0;
            qb_level = V(VDD, VSS) - q_level;
        end

        V(Q, VSS) <+ transition(q_level, 0, tedge, tedge);
        V(QB, VSS) <+ transition(qb_level, 0, tedge, tedge);
    end
endmodule
"""


def _clk_div4_body() -> str:
    return """`include "constants.vams"
`include "disciplines.vams"

module clk_div(CLK_IN, RST_N, CLK_OUT);
    input CLK_IN, RST_N;
    output CLK_OUT;
    electrical CLK_IN, RST_N, CLK_OUT;

    parameter real vth = 0.45;
    parameter real vdd = 0.9;
    parameter real tedge = 100p;

    integer count;
    real out_level;

    analog begin
        @(initial_step or cross(V(RST_N) - vth, -1)) begin
            count = 0;
            out_level = 0.0;
        end

        @(cross(V(CLK_IN) - vth, +1)) begin
            if (V(RST_N) > vth) begin
                count = count + 1;
                if (count >= 4)
                    count = 0;
                out_level = (count < 2) ? vdd : 0.0;
            end
        end

        V(CLK_OUT) <+ transition(out_level, 0, tedge, tedge);
    end
endmodule
"""


def _gray_counter_4b_body(module_name: str, reset_active_high: bool, has_enable: bool) -> str:
    if has_enable:
        ports = "VDD, VSS, CLK, EN, RSTB, G3, G2, G1, G0"
        declarations = """    inout VDD, VSS;
    input CLK, EN, RSTB;
    output G3, G2, G1, G0;
    electrical VDD, VSS, CLK, EN, RSTB, G3, G2, G1, G0;"""
        reset_expr = "V(RSTB, VSS) < vth"
        active_expr = "V(RSTB, VSS) > vth && V(EN, VSS) > vth"
        vdd = "V(VDD, VSS)"
        vss = "VSS"
        clk = "V(CLK, VSS)"
    else:
        ports = "vdd, vss, clk, rst, g0, g1, g2, g3"
        declarations = """    inout vdd, vss;
    input clk, rst;
    output g0, g1, g2, g3;
    electrical vdd, vss, clk, rst, g0, g1, g2, g3;"""
        reset_expr = "V(rst, vss) > vth" if reset_active_high else "V(rst, vss) < vth"
        active_expr = "V(rst, vss) < vth" if reset_active_high else "V(rst, vss) > vth"
        vdd = "V(vdd, vss)"
        vss = "vss"
        clk = "V(clk, vss)"
    out_lines = (
        """
        V(G3, VSS) <+ transition(g3_level, 0, tedge, tedge);
        V(G2, VSS) <+ transition(g2_level, 0, tedge, tedge);
        V(G1, VSS) <+ transition(g1_level, 0, tedge, tedge);
        V(G0, VSS) <+ transition(g0_level, 0, tedge, tedge);"""
        if has_enable
        else """
        V(g0, vss) <+ transition(g0_level, 0, tedge, tedge);
        V(g1, vss) <+ transition(g1_level, 0, tedge, tedge);
        V(g2, vss) <+ transition(g2_level, 0, tedge, tedge);
        V(g3, vss) <+ transition(g3_level, 0, tedge, tedge);"""
    )
    return f"""`include "constants.vams"
`include "disciplines.vams"

module {module_name}({ports});
{declarations}

    parameter real vth = 0.45;
    parameter real tedge = 100p;
    integer binary_count;
    integer gray_code;
    real g0_level, g1_level, g2_level, g3_level;

    analog begin
        @(initial_step) begin
            binary_count = 0;
            gray_code = 0;
            g0_level = 0.0;
            g1_level = 0.0;
            g2_level = 0.0;
            g3_level = 0.0;
        end

        @(cross({clk} - vth, +1)) begin
            if ({reset_expr}) begin
                binary_count = 0;
                gray_code = 0;
            end else if ({active_expr}) begin
                binary_count = (binary_count + 1) & 15;
                gray_code = binary_count ^ (binary_count >> 1);
            end
            g0_level = ((gray_code >> 0) & 1) ? {vdd} : 0.0;
            g1_level = ((gray_code >> 1) & 1) ? {vdd} : 0.0;
            g2_level = ((gray_code >> 2) & 1) ? {vdd} : 0.0;
            g3_level = ((gray_code >> 3) & 1) ? {vdd} : 0.0;
        end
{out_lines}
    end
endmodule
"""


def _dac_binary_clk_4b_body() -> str:
    return """`include "constants.vams"
`include "disciplines.vams"

module dac_binary_clk_4b(DIN3, DIN2, DIN1, DIN0, CLK, AOUT);
    input DIN3, DIN2, DIN1, DIN0, CLK;
    output AOUT;
    electrical DIN3, DIN2, DIN1, DIN0, CLK, AOUT;

    parameter real vref = 0.9;
    parameter real vth = 0.45;
    parameter real tedge = 100p;
    integer code;
    real out_level;

    analog begin
        @(initial_step) begin
            code = 0;
            out_level = 0.0;
        end

        @(cross(V(CLK) - vth, +1)) begin
            code = (V(DIN3) > vth ? 8 : 0)
                 + (V(DIN2) > vth ? 4 : 0)
                 + (V(DIN1) > vth ? 2 : 0)
                 + (V(DIN0) > vth ? 1 : 0);
            out_level = (code / 16.0) * vref;
        end

        V(AOUT) <+ transition(out_level, 0, tedge, tedge);
    end
endmodule
"""


def _flash_adc_3b_body() -> str:
    return """`include "constants.vams"
`include "disciplines.vams"

module flash_adc_3b(VDD, VSS, VIN, CLK, DOUT2, DOUT1, DOUT0);
    inout VDD, VSS;
    input VIN, CLK;
    output DOUT2, DOUT1, DOUT0;
    electrical VDD, VSS, VIN, CLK, DOUT2, DOUT1, DOUT0;

    parameter real vrefp = 0.9;
    parameter real vrefn = 0.0;
    parameter real vth = 0.45;
    parameter real tedge = 100p;

    integer code;
    real b2, b1, b0;
    real lsb;

    analog begin
        @(initial_step) begin
            code = 0;
            b2 = 0.0;
            b1 = 0.0;
            b0 = 0.0;
        end

        @(cross(V(CLK, VSS) - vth, +1)) begin
            lsb = (vrefp - vrefn) / 8.0;
            code = floor((V(VIN, VSS) - vrefn) / lsb);
            if (code < 0)
                code = 0;
            if (code > 7)
                code = 7;
            b2 = ((code >> 2) & 1) ? V(VDD, VSS) : 0.0;
            b1 = ((code >> 1) & 1) ? V(VDD, VSS) : 0.0;
            b0 = ((code >> 0) & 1) ? V(VDD, VSS) : 0.0;
        end

        V(DOUT2, VSS) <+ transition(b2, 0, tedge, tedge);
        V(DOUT1, VSS) <+ transition(b1, 0, tedge, tedge);
        V(DOUT0, VSS) <+ transition(b0, 0, tedge, tedge);
    end
endmodule
"""


def _bad_bus_output_loop_body() -> str:
    return """`include "constants.vams"
`include "disciplines.vams"

module bin4_out(VDD, VSS, CODE, DOUT);
    inout VDD, VSS;
    input [3:0] CODE;
    output [3:0] DOUT;
    electrical VDD, VSS;
    electrical [3:0] CODE, DOUT;

    parameter real vth = 0.45;
    parameter real trf = 20p;

    analog begin
        V(DOUT[0]) <+ transition((V(CODE[0]) > vth) ? V(VDD, VSS) : 0.0, 0, trf, trf);
        V(DOUT[1]) <+ transition((V(CODE[1]) > vth) ? V(VDD, VSS) : 0.0, 0, trf, trf);
        V(DOUT[2]) <+ transition((V(CODE[2]) > vth) ? V(VDD, VSS) : 0.0, 0, trf, trf);
        V(DOUT[3]) <+ transition((V(CODE[3]) > vth) ? V(VDD, VSS) : 0.0, 0, trf, trf);
    end
endmodule
"""


def _dac_therm_16b_body() -> str:
    return """`include "constants.vams"
`include "disciplines.vams"

module dac_therm_16b(din_therm, rst_n, vout);
    input [15:0] din_therm;
    input rst_n;
    output vout;
    electrical [15:0] din_therm;
    electrical rst_n, vout;

    parameter real vstep = 1.0;
    parameter real vth = 0.4;
    parameter real tr = 10p;

    integer k;
    integer ones_count;
    real out_level;

    analog begin
        ones_count = 0;
        if (V(rst_n) > vth) begin
            for (k = 0; k < 16; k = k + 1) begin
                if (V(din_therm[k]) > vth)
                    ones_count = ones_count + 1;
            end
        end
        out_level = ones_count * vstep;
        V(vout) <+ transition(out_level, 0, tr, tr);
    end
endmodule
"""


def _dwa_ptr_gen_body(no_overlap: bool = False) -> str:
    module_name = "dwa_ptr_gen_no_overlap" if no_overlap else "dwa_ptr_gen"
    include_boundary = "dist > 0 && dist <= code" if no_overlap else "dist < code"
    return f"""`include "constants.vams"
`include "disciplines.vams"

module {module_name}(
    clk_i, rst_ni,
    code_3, code_2, code_1, code_0,
    cell_en_15, cell_en_14, cell_en_13, cell_en_12, cell_en_11, cell_en_10, cell_en_9, cell_en_8,
    cell_en_7, cell_en_6, cell_en_5, cell_en_4, cell_en_3, cell_en_2, cell_en_1, cell_en_0,
    ptr_15, ptr_14, ptr_13, ptr_12, ptr_11, ptr_10, ptr_9, ptr_8,
    ptr_7, ptr_6, ptr_5, ptr_4, ptr_3, ptr_2, ptr_1, ptr_0
);
    input clk_i, rst_ni, code_3, code_2, code_1, code_0;
    output cell_en_15, cell_en_14, cell_en_13, cell_en_12, cell_en_11, cell_en_10, cell_en_9, cell_en_8;
    output cell_en_7, cell_en_6, cell_en_5, cell_en_4, cell_en_3, cell_en_2, cell_en_1, cell_en_0;
    output ptr_15, ptr_14, ptr_13, ptr_12, ptr_11, ptr_10, ptr_9, ptr_8;
    output ptr_7, ptr_6, ptr_5, ptr_4, ptr_3, ptr_2, ptr_1, ptr_0;
    electrical clk_i, rst_ni, code_3, code_2, code_1, code_0;
    electrical cell_en_15, cell_en_14, cell_en_13, cell_en_12, cell_en_11, cell_en_10, cell_en_9, cell_en_8;
    electrical cell_en_7, cell_en_6, cell_en_5, cell_en_4, cell_en_3, cell_en_2, cell_en_1, cell_en_0;
    electrical ptr_15, ptr_14, ptr_13, ptr_12, ptr_11, ptr_10, ptr_9, ptr_8;
    electrical ptr_7, ptr_6, ptr_5, ptr_4, ptr_3, ptr_2, ptr_1, ptr_0;

    parameter real vdd = 0.9;
    parameter real vth = 0.45;
    parameter integer ptr_init = 0;
    parameter real trf = 10p;

    integer ptr;
    integer code;
    integer old_ptr;
    integer dist;
    real cell0, cell1, cell2, cell3, cell4, cell5, cell6, cell7;
    real cell8, cell9, cell10, cell11, cell12, cell13, cell14, cell15;
    real p0, p1, p2, p3, p4, p5, p6, p7;
    real p8, p9, p10, p11, p12, p13, p14, p15;

    analog begin
        @(initial_step) begin
            ptr = ptr_init;
            code = 0;
        end

        @(cross(V(clk_i) - vth, +1)) begin
            if (V(rst_ni) < vth) begin
                ptr = ptr_init;
                code = 0;
            end else begin
                old_ptr = ptr;
                code = (V(code_0) > vth ? 1 : 0)
                     + (V(code_1) > vth ? 2 : 0)
                     + (V(code_2) > vth ? 4 : 0)
                     + (V(code_3) > vth ? 8 : 0);
                ptr = (ptr + code) % 16;
            end

            dist = (ptr - 0 + 16) % 16;  cell0  = (({include_boundary}) ? vdd : 0.0); p0  = (ptr == 0)  ? vdd : 0.0;
            dist = (ptr - 1 + 16) % 16;  cell1  = (({include_boundary}) ? vdd : 0.0); p1  = (ptr == 1)  ? vdd : 0.0;
            dist = (ptr - 2 + 16) % 16;  cell2  = (({include_boundary}) ? vdd : 0.0); p2  = (ptr == 2)  ? vdd : 0.0;
            dist = (ptr - 3 + 16) % 16;  cell3  = (({include_boundary}) ? vdd : 0.0); p3  = (ptr == 3)  ? vdd : 0.0;
            dist = (ptr - 4 + 16) % 16;  cell4  = (({include_boundary}) ? vdd : 0.0); p4  = (ptr == 4)  ? vdd : 0.0;
            dist = (ptr - 5 + 16) % 16;  cell5  = (({include_boundary}) ? vdd : 0.0); p5  = (ptr == 5)  ? vdd : 0.0;
            dist = (ptr - 6 + 16) % 16;  cell6  = (({include_boundary}) ? vdd : 0.0); p6  = (ptr == 6)  ? vdd : 0.0;
            dist = (ptr - 7 + 16) % 16;  cell7  = (({include_boundary}) ? vdd : 0.0); p7  = (ptr == 7)  ? vdd : 0.0;
            dist = (ptr - 8 + 16) % 16;  cell8  = (({include_boundary}) ? vdd : 0.0); p8  = (ptr == 8)  ? vdd : 0.0;
            dist = (ptr - 9 + 16) % 16;  cell9  = (({include_boundary}) ? vdd : 0.0); p9  = (ptr == 9)  ? vdd : 0.0;
            dist = (ptr - 10 + 16) % 16; cell10 = (({include_boundary}) ? vdd : 0.0); p10 = (ptr == 10) ? vdd : 0.0;
            dist = (ptr - 11 + 16) % 16; cell11 = (({include_boundary}) ? vdd : 0.0); p11 = (ptr == 11) ? vdd : 0.0;
            dist = (ptr - 12 + 16) % 16; cell12 = (({include_boundary}) ? vdd : 0.0); p12 = (ptr == 12) ? vdd : 0.0;
            dist = (ptr - 13 + 16) % 16; cell13 = (({include_boundary}) ? vdd : 0.0); p13 = (ptr == 13) ? vdd : 0.0;
            dist = (ptr - 14 + 16) % 16; cell14 = (({include_boundary}) ? vdd : 0.0); p14 = (ptr == 14) ? vdd : 0.0;
            dist = (ptr - 15 + 16) % 16; cell15 = (({include_boundary}) ? vdd : 0.0); p15 = (ptr == 15) ? vdd : 0.0;
        end

        V(cell_en_0)  <+ transition(cell0,  0, trf, trf); V(cell_en_1)  <+ transition(cell1,  0, trf, trf);
        V(cell_en_2)  <+ transition(cell2,  0, trf, trf); V(cell_en_3)  <+ transition(cell3,  0, trf, trf);
        V(cell_en_4)  <+ transition(cell4,  0, trf, trf); V(cell_en_5)  <+ transition(cell5,  0, trf, trf);
        V(cell_en_6)  <+ transition(cell6,  0, trf, trf); V(cell_en_7)  <+ transition(cell7,  0, trf, trf);
        V(cell_en_8)  <+ transition(cell8,  0, trf, trf); V(cell_en_9)  <+ transition(cell9,  0, trf, trf);
        V(cell_en_10) <+ transition(cell10, 0, trf, trf); V(cell_en_11) <+ transition(cell11, 0, trf, trf);
        V(cell_en_12) <+ transition(cell12, 0, trf, trf); V(cell_en_13) <+ transition(cell13, 0, trf, trf);
        V(cell_en_14) <+ transition(cell14, 0, trf, trf); V(cell_en_15) <+ transition(cell15, 0, trf, trf);

        V(ptr_0)  <+ transition(p0,  0, trf, trf); V(ptr_1)  <+ transition(p1,  0, trf, trf);
        V(ptr_2)  <+ transition(p2,  0, trf, trf); V(ptr_3)  <+ transition(p3,  0, trf, trf);
        V(ptr_4)  <+ transition(p4,  0, trf, trf); V(ptr_5)  <+ transition(p5,  0, trf, trf);
        V(ptr_6)  <+ transition(p6,  0, trf, trf); V(ptr_7)  <+ transition(p7,  0, trf, trf);
        V(ptr_8)  <+ transition(p8,  0, trf, trf); V(ptr_9)  <+ transition(p9,  0, trf, trf);
        V(ptr_10) <+ transition(p10, 0, trf, trf); V(ptr_11) <+ transition(p11, 0, trf, trf);
        V(ptr_12) <+ transition(p12, 0, trf, trf); V(ptr_13) <+ transition(p13, 0, trf, trf);
        V(ptr_14) <+ transition(p14, 0, trf, trf); V(ptr_15) <+ transition(p15, 0, trf, trf);
    end
endmodule
"""


def _nrz_prbs_body() -> str:
    return """`include "constants.vams"
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
            cur_bit = 1;
            prev_bit = 1;
            ui = 1.0 / data_rate;
            level = 1.0;
            next_t = ui;
        end

        @(timer(next_t)) begin
            feedback = ((lfsr >> 6) ^ (lfsr >> 5)) & 1;
            lfsr = ((lfsr >> 1) & 63) | (feedback << 6);
            if (lfsr == 0)
                lfsr = 90;
            prev_bit = cur_bit;
            cur_bit = (lfsr & 1) ? 1 : -1;
            level = cur_bit + pre * (cur_bit - prev_bit);
            next_t = next_t + ui;
        end

        V(OUTP, VSS) <+ transition(vcm + 0.5 * amp * level, 0, tt, tt);
        V(OUTN, VSS) <+ transition(vcm - 0.5 * amp * level, 0, tt, tt);
    end
endmodule
"""


def _parameter_type_override_body() -> str:
    return """`include "constants.vams"
`include "disciplines.vams"

module parameter_type_override_ref(out, vss);
    inout out, vss;
    electrical out, vss;

    parameter real vhi = 0.55;
    parameter integer reps = 2;
    parameter real period = 10n from (0:inf);
    parameter real width = 3n from (0:inf);
    parameter real trf = 50p from (0:inf);

    integer emitted;
    real target;
    real t0;

    analog begin
        @(initial_step) begin
            emitted = 0;
            target = 0.0;
            t0 = 10n;
        end
        @(timer(10n, 10n)) begin
            if (emitted < reps)
                target = vhi;
        end
        @(timer(13n, 10n)) begin
            if (emitted < reps) begin
                target = 0.0;
                emitted = emitted + 1;
            end
        end
        V(out, vss) <+ transition(target, 0, trf, trf);
    end
endmodule
"""


def _timer_absolute_grid_body() -> str:
    return """`include "constants.vams"
`include "disciplines.vams"

module timer_absolute_grid_ref(VDD, VSS, clk_out);
    inout VDD, VSS;
    output clk_out;
    electrical VDD, VSS, clk_out;

    parameter real tstart = 10n from [0:inf);
    parameter real tstep = 10n from (0:inf);
    parameter real tedge = 200p from (0:inf);

    integer clk_state;
    real next_t;

    analog begin
        @(initial_step) begin
            clk_state = 0;
            next_t = tstart;
        end
        @(timer(next_t)) begin
            clk_state = 1 - clk_state;
            next_t = next_t + tstep;
        end
        V(clk_out, VSS) <+ transition(clk_state ? V(VDD, VSS) : 0.0, 0, tedge, tedge);
    end
endmodule
"""


def _transition_branch_target_body() -> str:
    return """`include "constants.vams"
`include "disciplines.vams"

module transition_branch_target_ref(VDD, VSS, mode, clk, out);
    inout VDD, VSS;
    input mode, clk;
    output out;
    electrical VDD, VSS, mode, clk, out;

    parameter real vth = 0.45;
    parameter real tedge = 500p;
    real target;

    analog begin
        @(initial_step)
            target = 0.0;
        @(cross(V(clk, VSS) - vth, +1)) begin
            target = (V(mode, VSS) > vth) ? V(VDD, VSS) : 0.0;
        end
        V(out, VSS) <+ transition(target, 0, tedge, tedge);
    end
endmodule
"""


def _anchor(root: Path, task_id: str, file_name: str) -> Path:
    candidates = [
        root / task_id / "sample_0_round3" / file_name,
        root / task_id / "sample_0_round2" / file_name,
        root / task_id / "sample_0_round1" / file_name,
        root / task_id / "sample_0" / file_name,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _configs(anchor_root: Path) -> list[TaskConfig]:
    return [
        TaskConfig(
            "clk_divider",
            ROOT / "tasks/spec-to-va/voltage/digital-logic/clk_divider",
            ROOT / "tasks/spec-to-va/voltage/digital-logic/clk_divider/gold/tb_clk_divider_ref.scs",
            _anchor(anchor_root, "clk_divider", "clk_divider_ref.va"),
            tuple(
                Variant(v.name, v.description, "clk_divider_ref.va", v.body)
                for v in clk_divider_variants()
            ),
        ),
        TaskConfig(
            "lfsr_smoke",
            ROOT / "tasks/end-to-end/voltage/lfsr_smoke",
            ROOT / "tasks/end-to-end/voltage/lfsr_smoke/gold/tb_lfsr_ref.scs",
            _anchor(anchor_root, "lfsr_smoke", "lfsr.va"),
            (
                Variant("lfsr_msb_fibonacci", "Fibonacci LFSR, MSB observable.", "lfsr.va", _lfsr_body(False, 30)),
                Variant("lfsr_lsb_fibonacci", "Fibonacci LFSR, LSB observable.", "lfsr.va", _lfsr_body(False, 0)),
                Variant("lfsr_inverted_msb", "Fibonacci LFSR, inverted MSB observable.", "lfsr.va", _lfsr_body(True, 30)),
            ),
        ),
        TaskConfig(
            "pfd_updn_smoke",
            ROOT / "tasks/end-to-end/voltage/pfd_updn_smoke",
            ROOT / "tasks/end-to-end/voltage/pfd_updn_smoke/gold/tb_pfd_updn_ref.scs",
            _anchor(anchor_root, "pfd_updn_smoke", "pfd_updn.va"),
            (
                Variant("pfd_immediate_reset", "Paired UP/DN latch with immediate mutual reset.", "pfd_updn.va", _pfd_body("immediate")),
                Variant("pfd_delayed_reset_0p2n", "Paired UP/DN latch with short delayed reset.", "pfd_updn.va", _pfd_body("timer_0p2n")),
            ),
        ),
        TaskConfig(
            "pfd_reset_race_smoke",
            ROOT / "tasks/end-to-end/voltage/pfd_reset_race_smoke",
            ROOT / "tasks/end-to-end/voltage/pfd_reset_race_smoke/gold/tb_pfd_reset_race_ref.scs",
            _anchor(anchor_root, "pfd_reset_race_smoke", "pfd_updn.va"),
            (
                Variant("pfd_immediate_reset", "Paired UP/DN latch with immediate mutual reset.", "pfd_updn.va", _pfd_body("immediate")),
                Variant("pfd_delayed_reset_0p2n", "Paired UP/DN latch with short delayed reset.", "pfd_updn.va", _pfd_body("timer_0p2n")),
                Variant("pfd_delayed_reset_0p5n", "Paired UP/DN latch with wider delayed reset.", "pfd_updn.va", _pfd_body("timer_0p5n")),
            ),
        ),
        TaskConfig(
            "multimod_divider",
            ROOT / "tasks/spec-to-va/voltage/pll-clock/multimod_divider",
            ROOT / "tasks/spec-to-va/voltage/pll-clock/multimod_divider/gold/tb_multimod_divider_ref.scs",
            _anchor(anchor_root, "multimod_divider", "multimod_divider_ref.va"),
            (
                Variant("pulse_base_plus_mod_reset0", "Pulse every base_count + mod input edges.", "multimod_divider_ref.va", _multimod_body(False)),
                Variant("pulse_base_plus_mod_reset1", "Pulse every base_count + mod with count phase reset to one.", "multimod_divider_ref.va", _multimod_body(True)),
            ),
        ),
        TaskConfig(
            "serializer_frame_alignment_smoke",
            ROOT / "tasks/end-to-end/voltage/serializer_frame_alignment_smoke",
            ROOT / "tasks/end-to-end/voltage/serializer_frame_alignment_smoke/gold/tb_serializer_frame_alignment_ref.scs",
            _anchor(anchor_root, "serializer_frame_alignment_smoke", "serializer_frame_alignment_ref.va"),
            (
                Variant("load_high_msb_frame", "Load while LOAD high, emit MSB-first with one-bit frame.", "serializer_frame_alignment_ref.va", _serializer_frame_body(True)),
                Variant("load_low_msb_frame", "Alternative polarity: load while LOAD low.", "serializer_frame_alignment_ref.va", _serializer_frame_body(False)),
            ),
        ),
        TaskConfig(
            "dff_rst_smoke",
            ROOT / "tasks/end-to-end/voltage/dff_rst_smoke",
            ROOT / "tasks/end-to-end/voltage/dff_rst_smoke/gold/tb_dff_rst_ref.scs",
            _anchor(anchor_root, "dff_rst_smoke", "dff_rst.va"),
            (
                Variant("sync_reset_dff_q_qb", "Synchronous-reset DFF with complementary QB.", "dff_rst.va", _dff_rst_body()),
            ),
        ),
        TaskConfig(
            "clk_div_smoke",
            ROOT / "tasks/end-to-end/voltage/clk_div_smoke",
            ROOT / "tasks/end-to-end/voltage/clk_div_smoke/gold/tb_clk_div_ref.scs",
            _anchor(anchor_root, "clk_div_smoke", "clk_div.va"),
            (
                Variant("divide_by_4_two_high_two_low", "Divide-by-4 clock with two high and two low input cycles.", "clk_div.va", _clk_div4_body()),
            ),
        ),
        TaskConfig(
            "gray_counter_4b_smoke",
            ROOT / "tasks/end-to-end/voltage/gray_counter_4b_smoke",
            ROOT / "tasks/end-to-end/voltage/gray_counter_4b_smoke/gold/tb_gray_counter_4b_ref.scs",
            _anchor(anchor_root, "gray_counter_4b_smoke", "gray_counter_4b.va"),
            (
                Variant(
                    "binary_count_to_gray_active_low_reset",
                    "Binary counter with Gray-code output, active-low reset, enable high.",
                    "gray_counter_4b.va",
                    _gray_counter_4b_body("gray_counter_4b", reset_active_high=False, has_enable=True),
                ),
            ),
        ),
        TaskConfig(
            "gray_counter_one_bit_change_smoke",
            ROOT / "tasks/end-to-end/voltage/gray_counter_one_bit_change_smoke",
            ROOT / "tasks/end-to-end/voltage/gray_counter_one_bit_change_smoke/gold/tb_gray_counter_one_bit_change_ref.scs",
            _anchor(anchor_root, "gray_counter_one_bit_change_smoke", "gray_counter_one_bit_change_ref.va"),
            (
                Variant(
                    "binary_count_to_gray_active_high_reset",
                    "Binary counter with Gray-code output and active-high reset.",
                    "gray_counter_one_bit_change_ref.va",
                    _gray_counter_4b_body("gray_counter_one_bit_change_ref", reset_active_high=True, has_enable=False),
                ),
            ),
        ),
        TaskConfig(
            "dac_binary_clk_4b_smoke",
            ROOT / "tasks/end-to-end/voltage/dac_binary_clk_4b_smoke",
            ROOT / "tasks/end-to-end/voltage/dac_binary_clk_4b_smoke/gold/tb_dac_binary_clk_4b_ref.scs",
            _anchor(anchor_root, "dac_binary_clk_4b_smoke", "dac_binary_clk_4b.va"),
            (
                Variant("clocked_binary_weighted_dac", "Clocked 4-bit binary-weighted DAC.", "dac_binary_clk_4b.va", _dac_binary_clk_4b_body()),
            ),
        ),
        TaskConfig(
            "flash_adc_3b_smoke",
            ROOT / "tasks/end-to-end/voltage/flash_adc_3b_smoke",
            ROOT / "tasks/end-to-end/voltage/flash_adc_3b_smoke/gold/tb_flash_adc_3b_ref.scs",
            _anchor(anchor_root, "flash_adc_3b_smoke", "flash_adc_3b.va"),
            (
                Variant("uniform_threshold_clocked_flash_adc", "3-bit clocked quantizer with saturated binary output.", "flash_adc_3b.va", _flash_adc_3b_body()),
            ),
        ),
        TaskConfig(
            "bad_bus_output_loop",
            ROOT / "tasks/bugfix/voltage/bad_bus_output_loop",
            ROOT / "tasks/bugfix/voltage/bad_bus_output_loop/gold/tb_bad_bus_output_loop.scs",
            _anchor(anchor_root, "bad_bus_output_loop", "dut_fixed.va"),
            (
                Variant("independent_bus_bit_outputs", "Drive each bus bit from the matching input bit.", "dut_fixed.va", _bad_bus_output_loop_body()),
            ),
        ),
        TaskConfig(
            "dac_therm_16b_smoke",
            ROOT / "tasks/end-to-end/voltage/dac_therm_16b_smoke",
            ROOT / "tasks/end-to-end/voltage/dac_therm_16b_smoke/gold/tb_dac_therm_16b_ref.scs",
            _anchor(anchor_root, "dac_therm_16b_smoke", "dac_therm_16b.va"),
            (
                Variant("thermometer_count_to_voltage", "Count thermometer ones and drive vout=count*vstep.", "dac_therm_16b.va", _dac_therm_16b_body()),
            ),
        ),
        TaskConfig(
            "dwa_ptr_gen_smoke",
            ROOT / "tasks/end-to-end/voltage/dwa_ptr_gen_smoke",
            ROOT / "tasks/end-to-end/voltage/dwa_ptr_gen_smoke/gold/tb_dwa_ptr_gen_ref.scs",
            _anchor(anchor_root, "dwa_ptr_gen_smoke", "dwa_ptr_gen.va"),
            (
                Variant("dwa_rotating_pointer_with_boundary_cell", "Rotate pointer by input code and enable a contiguous cell span.", "dwa_ptr_gen.va", _dwa_ptr_gen_body(False)),
            ),
        ),
        TaskConfig(
            "dwa_ptr_gen_no_overlap_smoke",
            ROOT / "tasks/end-to-end/voltage/dwa_ptr_gen_no_overlap_smoke",
            ROOT / "tasks/end-to-end/voltage/dwa_ptr_gen_no_overlap_smoke/gold/tb_dwa_ptr_gen_no_overlap_ref.scs",
            _anchor(anchor_root, "dwa_ptr_gen_no_overlap_smoke", "dwa_ptr_gen_no_overlap.va"),
            (
                Variant("dwa_rotating_pointer_no_overlap", "Rotate pointer and exclude the new pointer boundary cell.", "dwa_ptr_gen_no_overlap.va", _dwa_ptr_gen_body(True)),
            ),
        ),
        TaskConfig(
            "nrz_prbs",
            ROOT / "tasks/spec-to-va/voltage/signal-source/nrz_prbs",
            ROOT / "tasks/spec-to-va/voltage/signal-source/nrz_prbs/gold/tb_nrz_prbs_ref.scs",
            _anchor(anchor_root, "nrz_prbs", "nrz_prbs.va"),
            (
                Variant("timer_lfsr_differential_prbs", "Timer-driven LFSR NRZ PRBS with complementary outputs.", "nrz_prbs.va", _nrz_prbs_body()),
            ),
        ),
        TaskConfig(
            "parameter_type_override_smoke",
            ROOT / "tasks/end-to-end/voltage/parameter_type_override_smoke",
            ROOT / "tasks/end-to-end/voltage/parameter_type_override_smoke/gold/tb_parameter_type_override_ref.scs",
            _anchor(anchor_root, "parameter_type_override_smoke", "parameter_type_override_ref.va"),
            (
                Variant("periodic_parameterized_pulses", "Use overridden vhi/reps/period parameters to emit finite pulses.", "parameter_type_override_ref.va", _parameter_type_override_body()),
            ),
        ),
        TaskConfig(
            "timer_absolute_grid_smoke",
            ROOT / "tasks/end-to-end/voltage/timer_absolute_grid_smoke",
            ROOT / "tasks/end-to-end/voltage/timer_absolute_grid_smoke/gold/tb_timer_absolute_grid_ref.scs",
            _anchor(anchor_root, "timer_absolute_grid_smoke", "timer_absolute_grid_ref.va"),
            (
                Variant("absolute_timer_grid", "Toggle output on an absolute timer grid.", "timer_absolute_grid_ref.va", _timer_absolute_grid_body()),
            ),
        ),
        TaskConfig(
            "transition_branch_target_smoke",
            ROOT / "tasks/end-to-end/voltage/transition_branch_target_smoke",
            ROOT / "tasks/end-to-end/voltage/transition_branch_target_smoke/gold/tb_transition_branch_target_ref.scs",
            _anchor(anchor_root, "transition_branch_target_smoke", "transition_branch_target_ref.va"),
            (
                Variant("branch_target_registered_then_transition", "Update target in event block and contribute transition unconditionally.", "transition_branch_target_ref.va", _transition_branch_target_body()),
            ),
        ),
    ]


def run_task(config: TaskConfig, generated_root: Path, output_root: Path, timeout_s: int) -> dict:
    task_gen = generated_root / config.task_id
    task_out = output_root / config.task_id
    task_gen.mkdir(parents=True, exist_ok=True)
    task_out.mkdir(parents=True, exist_ok=True)

    baseline_dir = task_gen / "baseline"
    baseline_dir.mkdir(parents=True, exist_ok=True)
    baseline_dut = baseline_dir / config.anchor.name
    shutil.copy2(config.anchor, baseline_dut)
    baseline = _run_case_safe(
        config.task_dir,
        baseline_dut,
        config.tb_path,
        task_out / "baseline",
        timeout_s,
        config.task_id,
    )
    _json_write(task_out / "baseline/result.json", baseline)

    best = {"name": "baseline", "result": baseline, "rank": _rank(baseline)}
    attempts: list[dict] = []
    for idx, variant in enumerate(config.variants, start=1):
        name = f"{idx:02d}_{_safe_name(variant.name)}"
        variant_dir = task_gen / name
        variant_dir.mkdir(parents=True, exist_ok=True)
        dut_path = variant_dir / variant.file_name
        dut_path.write_text(variant.body, encoding="utf-8")
        result = _run_case_safe(
            config.task_dir,
            dut_path,
            config.tb_path,
            task_out / name,
            timeout_s,
            config.task_id,
        )
        rank = _rank(result)
        _json_write(task_out / name / "result.json", result)
        attempts.append(
            {
                "idx": idx,
                "variant": variant.name,
                "description": variant.description,
                "status": result.get("status"),
                "scores": result.get("scores"),
                "notes": result.get("notes"),
                "rank": list(rank),
                "dut_path": str(dut_path),
            }
        )
        print(f"[smallset] {config.task_id} {variant.name}: {result.get('status')} notes={result.get('notes')}")
        if rank > best["rank"]:
            best = {"name": variant.name, "result": result, "rank": rank}

    summary = {
        "task_id": config.task_id,
        "baseline_status": baseline.get("status"),
        "baseline_scores": baseline.get("scores"),
        "baseline_notes": baseline.get("notes"),
        "attempts": attempts,
        "best_variant": best["name"],
        "best_status": best["result"].get("status"),
        "best_scores": best["result"].get("scores"),
        "best_notes": best["result"].get("notes"),
        "best_rank": list(best["rank"]),
    }
    _json_write(task_out / "summary.json", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run small-set template-guided EVAS probe.")
    parser.add_argument("--generated-root", default="generated-template-guided-smallset")
    parser.add_argument("--output-root", default="results/template-guided-smallset")
    parser.add_argument("--timeout-s", type=int, default=120)
    parser.add_argument("--tasks", nargs="*", default=None)
    parser.add_argument("--anchor-root", default=str(A_KIMI_ROOT))
    args = parser.parse_args()

    generated_root = Path(args.generated_root).resolve()
    output_root = Path(args.output_root).resolve()
    anchor_root = Path(args.anchor_root).resolve()
    wanted = set(args.tasks or [])
    configs = [c for c in _configs(anchor_root) if not wanted or c.task_id in wanted]

    summaries = [run_task(c, generated_root, output_root, args.timeout_s) for c in configs]
    total = len(summaries)
    baseline_pass = sum(1 for s in summaries if s["baseline_status"] == "PASS")
    best_pass = sum(1 for s in summaries if s["best_status"] == "PASS")
    improved = sum(1 for s in summaries if _rank({"status": s["best_status"], "scores": s["best_scores"]}) > _rank({"status": s["baseline_status"], "scores": s["baseline_scores"]}))
    overall = {
        "mode": "template_guided_smallset",
        "anchor_root": str(anchor_root),
        "total": total,
        "baseline_pass": baseline_pass,
        "best_pass": best_pass,
        "improved": improved,
        "tasks": summaries,
    }
    _json_write(output_root / "summary.json", overall)
    print(f"[smallset] baseline_pass={baseline_pass}/{total} best_pass={best_pass}/{total} improved={improved}/{total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
