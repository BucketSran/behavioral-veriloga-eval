from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runners"))

from compile_vector_unroll_guard import apply_vector_unroll_guard  # noqa: E402


def test_vector_unroll_guard_materializes_scalar_input_bus(tmp_path: Path) -> None:
    sample = tmp_path / "sample_0"
    sample.mkdir()
    (sample / "tb_generated.scs").write_text(
        "simulator lang=spectre\n"
        "ahdl_include \"dac_therm_16b.va\"\n"
        "XDUT (d15 d14 d13 d12 d11 d10 d9 d8 d7 d6 d5 d4 d3 d2 d1 d0 rst_n vout) dac_therm_16b\n",
        encoding="utf-8",
    )
    (sample / "dac_therm_16b.va").write_text(
        "`include \"disciplines.vams\"\n"
        "module dac_therm_16b (din_therm, rst_n, vout);\n"
        "  input [15:0] din_therm;\n"
        "  input rst_n;\n"
        "  output vout;\n"
        "  electrical [15:0] din_therm;\n"
        "  electrical rst_n, vout;\n"
        "  integer i;\n"
        "  integer count;\n"
        "  analog begin\n"
        "    count = 0;\n"
        "    for (i = 0; i < 16; i = i + 1) begin\n"
        "      if (V(din_therm[i]) > 0.5) count = count + 1;\n"
        "    end\n"
        "    V(vout) <+ count / 16.0;\n"
        "  end\n"
        "endmodule\n",
        encoding="utf-8",
    )

    edits = apply_vector_unroll_guard(
        sample,
        notes=["spectre_strict:instance_port_count_mismatch", "dynamic_analog_vector_index"],
    )

    va_text = (sample / "dac_therm_16b.va").read_text(encoding="utf-8")
    assert edits == ["vector_unroll:dac_therm_16b:din_therm:loops=1:dac_therm_16b.va"]
    assert "module dac_therm_16b (" in va_text
    assert "d15, d14, d13, d12, d11, d10, d9, d8" in va_text
    assert "input [15:0] din_therm" not in va_text
    assert "electrical [15:0] din_therm" not in va_text
    assert "V(din_therm[i])" not in va_text
    assert "if (V(d0) > 0.5) count = count + 1;" in va_text
    assert "if (V(d15) > 0.5) count = count + 1;" in va_text


def test_vector_unroll_guard_normalizes_tb_nodes_and_output_loops(tmp_path: Path) -> None:
    sample = tmp_path / "sample_0"
    sample.mkdir()
    code_nodes = " ".join(f"code_msb_i[{idx}]" for idx in range(3, -1, -1))
    cell_nodes = " ".join(f"cell_en_o[{idx}]" for idx in range(15, -1, -1))
    ptr_nodes = " ".join(f"ptr_o[{idx}]" for idx in range(15, -1, -1))
    (sample / "tb_generated.scs").write_text(
        "simulator lang=spectre\n"
        "ahdl_include \"dwa_ptr_gen_no_overlap.va\"\n"
        f"XDUT (clk_i rst_ni {code_nodes} {cell_nodes} {ptr_nodes}) \\\n"
        "      dwa_ptr_gen_no_overlap\n",
        encoding="utf-8",
    )
    (sample / "dwa_ptr_gen_no_overlap.va").write_text(
        "`include \"disciplines.vams\"\n"
        "module dwa_ptr_gen_no_overlap (clk_i, rst_ni, code_msb_i, cell_en_o, ptr_o);\n"
        "  input clk_i, rst_ni;\n"
        "  input [3:0] code_msb_i;\n"
        "  output [15:0] cell_en_o;\n"
        "  output [15:0] ptr_o;\n"
        "  electrical clk_i, rst_ni;\n"
        "  electrical [3:0] code_msb_i;\n"
        "  electrical [15:0] cell_en_o;\n"
        "  electrical [15:0] ptr_o;\n"
        "  integer i;\n"
        "  integer ptr[0:15];\n"
        "  integer en[0:15];\n"
        "  analog begin\n"
        "    if (V(code_msb_i[3]) > 0.5) en[3] = 1;\n"
        "    for (i = 0; i < 16; i = i + 1) begin\n"
        "      V(ptr_o[i]) <+ transition(ptr[i] ? 1.0 : 0.0, 0, 1p);\n"
        "      V(cell_en_o[i]) <+ transition(en[i] ? 1.0 : 0.0, 0, 1p);\n"
        "    end\n"
        "  end\n"
        "endmodule\n",
        encoding="utf-8",
    )

    edits = apply_vector_unroll_guard(
        sample,
        notes=["dynamic_analog_vector_index=dwa_ptr_gen_no_overlap.va:99:i:ptr_o[i]"],
    )

    tb_text = (sample / "tb_generated.scs").read_text(encoding="utf-8")
    va_text = (sample / "dwa_ptr_gen_no_overlap.va").read_text(encoding="utf-8")
    assert "spectre_bus_nodes_to_scalars:tb_generated.scs" in edits
    assert "vector_unroll:dwa_ptr_gen_no_overlap:cell_en_o,code_msb_i,ptr_o:loops=1:dwa_ptr_gen_no_overlap.va" in edits
    assert "code_msb_i[3]" not in tb_text
    assert "code_msb_i_3" in tb_text
    assert "output [15:0] ptr_o" not in va_text
    assert "electrical [15:0] cell_en_o" not in va_text
    assert "V(code_msb_i[3])" not in va_text
    assert "V(code_msb_i_3)" in va_text
    assert "V(ptr_o[i])" not in va_text
    assert "V(cell_en_o[i])" not in va_text
    assert "V(ptr_o_0) <+ transition(ptr[0] ? 1.0 : 0.0, 0, 1p);" in va_text
    assert "V(cell_en_o_15) <+ transition(en[15] ? 1.0 : 0.0, 0, 1p);" in va_text
