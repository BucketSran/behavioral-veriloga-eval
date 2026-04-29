#!/usr/bin/env python3
"""Materialize benchmark-v2 draft tasks from the v2-small manifest."""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "benchmark-v2"
MANIFEST = BENCH / "manifests" / "v2-small.json"
TASK_ROOT = BENCH / "tasks"


def _ports_decl(inputs: list[str], outputs: list[str]) -> str:
    lines = []
    if inputs:
        lines.append("    input " + ", ".join(inputs) + ";")
    if outputs:
        lines.append("    output " + ", ".join(outputs) + ";")
    lines.append("    electrical " + ", ".join(inputs + outputs) + ";")
    return "\n".join(lines)


def _adc_dac_va(module: str, vin: str, clk: str, rst: str, bits_lsb: list[str], vout: str, *, settled: str | None = None) -> str:
    outputs = list(reversed(bits_lsb)) + [vout] + ([settled] if settled else [])
    width = len(bits_lsb)
    max_code = (1 << width) - 1
    bit_reals = "\n".join(f"    real {b}_t;" for b in bits_lsb)
    bit_init = "\n".join(f"            {b}_t = V(vss);" for b in bits_lsb)
    bit_update = "\n".join(f"            {b}_t = ((code_q & {1 << i}) != 0) ? V(vdd) : V(vss);" for i, b in enumerate(bits_lsb))
    bit_drive = "\n".join(f"        V({b}) <+ transition({b}_t, 0.0, tr, tr);" for b in bits_lsb)
    settled_decl = "    integer stable_count;\n    real settled_t;\n" if settled else ""
    settled_init = "            stable_count = 0;\n            settled_t = V(vss);\n" if settled else ""
    settled_update = "            stable_count = stable_count + 1;\n            if (stable_count > 8) settled_t = V(vdd);\n" if settled else ""
    settled_drive = f"        V({settled}) <+ transition(settled_t, 0.0, tr, tr);\n" if settled else ""
    return f"""`include "constants.vams"
`include "disciplines.vams"

module {module}({", ".join([vin, clk, rst, "vdd", "vss"] + outputs)});
{_ports_decl([vin, clk, rst, "vdd", "vss"], outputs)}
    parameter real vth = 0.45;
    parameter real tr = 50p;
    integer code_q;
    real step_q;
    real vout_t;
{bit_reals}
{settled_decl}    analog begin
        @(initial_step) begin
            code_q = 0;
            vout_t = V(vss);
{bit_init}
{settled_init}        end

        @(cross(V({clk}) - vth, +1)) begin
            if (V({rst}) < vth) begin
                code_q = 0;
                vout_t = V(vss);
{bit_init}
{settled_init}            end else begin
                step_q = (V(vdd) - V(vss)) / {max_code + 1}.0;
                code_q = (V({vin}) - V(vss)) / step_q;
                if (code_q < 0) code_q = 0;
                if (code_q > {max_code}) code_q = {max_code};
                vout_t = V(vss) + (V(vdd) - V(vss)) * code_q / {max_code}.0;
{bit_update}
{settled_update}            end
        end

{bit_drive}
        V({vout}) <+ transition(vout_t, 0.0, tr, tr);
{settled_drive}    end
endmodule
"""


def _binary_dac_va(module: str, bits_lsb: list[str], out: str, *, guard: str | None = None) -> str:
    outputs = [out] + ([guard] if guard else [])
    max_code = (1 << len(bits_lsb)) - 1
    code_lines = "\n".join(f"        if (V({bit}) >= vth) code_q = code_q + {1 << i};" for i, bit in enumerate(bits_lsb))
    guard_drive = f"        V({guard}) <+ transition(V(vdd), 0.0, tr, tr);\n" if guard else ""
    return f"""`include "constants.vams"
`include "disciplines.vams"

module {module}({", ".join(bits_lsb + ["vdd", "vss"] + outputs)});
{_ports_decl(bits_lsb + ["vdd", "vss"], outputs)}
    parameter real vth = 0.45;
    parameter real tr = 40p;
    integer code_q;
    real out_t;

    analog begin
        code_q = 0;
{code_lines}
        out_t = V(vss) + (V(vdd) - V(vss)) * code_q / {max_code}.0;
        V({out}) <+ transition(out_t, 0.0, tr, tr);
{guard_drive}    end
endmodule
"""


def _dwa_va(module: str, clk: str, rst: str, code_bits: list[str], cells: list[str]) -> str:
    clear = "\n".join(f"                {c}_t = V(vss);" for c in cells)
    drive = "\n".join(f"        V({c}) <+ transition({c}_t, 0.0, tr, tr);" for c in cells)
    reals = "\n".join(f"    real {c}_t;" for c in cells)
    decode = "\n".join(f"                if (V({bit}) >= vth) count_q = count_q + {1 << i};" for i, bit in enumerate(code_bits))
    set_lines = []
    for j in range(4):
        set_lines.append(f"                idx_q = (ptr_q + {j}) % 8;")
        for i, cell in enumerate(cells):
            set_lines.append(f"                if (count_q > {j} && idx_q == {i}) {cell}_t = V(vdd);")
    return f"""`include "constants.vams"
`include "disciplines.vams"

module {module}({", ".join([clk, rst] + code_bits + ["vdd", "vss"] + cells)});
{_ports_decl([clk, rst] + code_bits + ["vdd", "vss"], cells)}
    parameter real vth = 0.45;
    parameter real tr = 50p;
    integer ptr_q;
    integer count_q;
    integer prev_count_q;
    integer idx_q;
{reals}

    analog begin
        @(initial_step) begin
            ptr_q = 0;
            count_q = 3;
            prev_count_q = 3;
{clear}
        end

        @(cross(V({clk}) - vth, +1)) begin
            if (V({rst}) < vth) begin
                ptr_q = 0;
                prev_count_q = 3;
            end else begin
                ptr_q = (ptr_q + prev_count_q) % 8;
            end
            count_q = 0;
{decode}
            if (count_q < 1) count_q = 1;
            if (count_q > 4) count_q = 4;
{clear}
{chr(10).join(set_lines)}
            prev_count_q = count_q;
        end

{drive}
    end
endmodule
"""


def _pfd_va(module: str, ref: str, div: str, up: str, dn: str, *, lock: str | None = None) -> str:
    lock_decl = "    integer stable_count;\n    real lock_t;\n" if lock else ""
    lock_init = "            stable_count = 0;\n            lock_t = V(vss);\n" if lock else ""
    lock_update_ref = "            stable_count = stable_count + 1;\n            if (stable_count > 5) lock_t = V(vdd);\n" if lock else ""
    lock_drive = f"        V({lock}) <+ transition(lock_t, 0.0, tr, tr);\n" if lock else ""
    outputs = [up, dn] + ([lock] if lock else [])
    return f"""`include "constants.vams"
`include "disciplines.vams"

module {module}({", ".join([ref, div, "vdd", "vss"] + outputs)});
{_ports_decl([ref, div, "vdd", "vss"], outputs)}
    parameter real vth = 0.45;
    parameter real pulse_width = 1.0n;
    parameter real tr = 40p;
    integer up_q;
    integer dn_q;
    real up_clear_t;
    real dn_clear_t;
{lock_decl}
    analog begin
        @(initial_step) begin
            up_q = 0;
            dn_q = 0;
            up_clear_t = 1.0;
            dn_clear_t = 1.0;
{lock_init}        end

        @(cross(V({ref}) - vth, +1)) begin
            up_q = 1;
            dn_q = 0;
            up_clear_t = $abstime + pulse_width;
{lock_update_ref}        end

        @(cross(V({div}) - vth, +1)) begin
            dn_q = 1;
            up_q = 0;
            dn_clear_t = $abstime + pulse_width;
        end

        @(timer(up_clear_t)) begin
            up_q = 0;
            up_clear_t = 1.0;
        end

        @(timer(dn_clear_t)) begin
            dn_q = 0;
            dn_clear_t = 1.0;
        end

        V({up}) <+ transition(up_q ? V(vdd) : V(vss), 0.0, tr, tr);
        V({dn}) <+ transition(dn_q ? V(vdd) : V(vss), 0.0, tr, tr);
{lock_drive}    end
endmodule
"""


def _divider_va(module: str, clk: str, rst: str, out: str, *, counter_bits: list[str] | None = None, ratio_sel: str | None = None, ratio: int = 3) -> str:
    outputs = [out] + (counter_bits or [])
    sel_input = [ratio_sel] if ratio_sel else []
    bit_reals = "\n".join(f"    real {b}_t;" for b in (counter_bits or []))
    bit_update = "\n".join(f"                {b}_t = ((count_state_q & {1 << i}) != 0) ? V(vdd) : V(vss);" for i, b in enumerate(counter_bits or []))
    bit_drive = "\n".join(f"        V({b}) <+ transition({b}_t, 0.0, tr, tr);" for b in (counter_bits or []))
    ratio_line = f"                ratio_q = (V({ratio_sel}) >= vth) ? {ratio + 2} : {ratio};" if ratio_sel else f"                ratio_q = {ratio};"
    return f"""`include "constants.vams"
`include "disciplines.vams"

module {module}({", ".join([clk, rst] + sel_input + ["vdd", "vss"] + outputs)});
{_ports_decl([clk, rst] + sel_input + ["vdd", "vss"], outputs)}
    parameter real vth = 0.45;
    parameter real tr = 40p;
    integer div_count_q;
    integer count_state_q;
    integer out_q;
    integer ratio_q;
{bit_reals}

    analog begin
        @(initial_step) begin
            div_count_q = 0;
            count_state_q = 0;
            out_q = 0;
            ratio_q = {ratio};
        end

        @(cross(V({clk}) - vth, +1)) begin
            if (V({rst}) < vth) begin
                div_count_q = 0;
                count_state_q = 0;
                out_q = 0;
            end else begin
{ratio_line}
                count_state_q = (count_state_q + 1) % 16;
                div_count_q = div_count_q + 1;
                if (div_count_q >= ratio_q) begin
                    div_count_q = 0;
                    out_q = !out_q;
                end
{bit_update}
            end
        end

        V({out}) <+ transition(out_q ? V(vdd) : V(vss), 0.0, tr, tr);
{bit_drive}
    end
endmodule
"""


def _sample_hold_va(module: str, vin: str, clk: str, vout: str, *, settled: str | None = None) -> str:
    outputs = [vout] + ([settled] if settled else [])
    settled_decl = "    integer sample_count;\n    real settled_t;\n" if settled else ""
    settled_init = "            sample_count = 0;\n            settled_t = V(vss);\n" if settled else ""
    settled_update = "            sample_count = sample_count + 1;\n            if (sample_count > 6) settled_t = V(vdd);\n" if settled else ""
    settled_drive = f"        V({settled}) <+ transition(settled_t, 0.0, tr, tr);\n" if settled else ""
    return f"""`include "constants.vams"
`include "disciplines.vams"

module {module}({", ".join([vin, clk, "vdd", "vss"] + outputs)});
{_ports_decl([vin, clk, "vdd", "vss"], outputs)}
    parameter real vth = 0.45;
    parameter real tr = 50p;
    real held_v;
{settled_decl}
    analog begin
        @(initial_step) begin
            held_v = V(vss);
{settled_init}        end

        @(cross(V({clk}) - vth, +1)) begin
            held_v = V({vin});
{settled_update}        end

        V({vout}) <+ transition(held_v, 0.0, tr, tr);
{settled_drive}    end
endmodule
"""


def _pulse_source(name: str, node: str, period: str, width: str, delay: str = "0") -> str:
    return f"{name} ({node} 0) vsource type=pulse val0=0 val1=0.9 delay={delay} rise=50p fall=50p width={width} period={period}"


def _tb(module: str, includes: str, instance_ports: list[str], sources: list[str], save: list[str], *, stop: str = "120n", maxstep: str = "50p") -> str:
    return "\n".join(
        [
            "simulator lang=spectre",
            "global 0",
            "",
            'ahdl_include "dut.va"',
            "",
            "Vvdd (vdd 0) vsource dc=0.9",
            "Vvss (vss 0) vsource dc=0",
            *sources,
            "",
            f"XDUT ({' '.join(instance_ports)}) {module}",
            "",
            f"tran tran stop={stop} maxstep={maxstep}",
            "save " + " ".join(save),
            "",
        ]
    )


def _checker_wrapper() -> str:
    return """#!/usr/bin/env python3
from pathlib import Path
import importlib.util
import json

TASK_DIR = Path(__file__).resolve().parent
COMMON = TASK_DIR.parents[1] / "common_checker.py"
spec = importlib.util.spec_from_file_location("benchmark_v2_common_checker", COMMON)
common = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(common)


def check_csv(csv_path):
    meta = json.loads((TASK_DIR / "meta.json").read_text(encoding="utf-8"))
    return common.check_csv(csv_path, meta["v2_checker_spec"])


if __name__ == "__main__":
    import sys
    print(json.dumps(check_csv(sys.argv[1]), indent=2))
"""


def _make_spec(entry: dict[str, Any]) -> dict[str, Any]:
    tid = entry["task_id"]
    if tid.startswith("v2_adc_dac"):
        width = 5 if "5b" in tid else 3 if "3b" in tid else 4
        prefix = "dec" if "keywordless" in tid else "bit" if "alias" in tid else "q"
        bits = [f"{prefix}{i}" for i in range(width)]
        vin = "measured_level" if "alias" in tid else "sense_value" if "keywordless" in tid else "external_drive"
        clk = "sample_clock" if "alias" in tid else "cadence"
        rst = "clear_n"
        vout = "held_level" if "alias" in tid else "estimate_level" if "keywordless" in tid else "reconstructed_level"
        settled = "settled" if "calibrated" in tid else None
        return {"kind": "adc_dac", "width": width, "vin": vin, "clock": clk, "rst": rst, "bits_lsb_first": bits, "vout": vout, "settled": settled, "min_unique_codes": min(8, 1 << width)}
    if tid.startswith("v2_binary_dac"):
        width = 6 if "6b" in tid else 5 if "5b" in tid else 4
        bits = [f"weight{i}" for i in range(width)]
        guard = "glitch_guard" if "glitch_guard" in tid else None
        return {"kind": "binary_dac", "bits_lsb_first": bits, "vout": "analog_sum", "guard": guard, "min_unique_codes": min(8, 1 << width)}
    if tid.startswith("v2_dwa"):
        cells = [f"cell{i}" for i in range(8)]
        return {"kind": "dwa", "clock": "advance", "rst": "clear_n", "bits_lsb_first": ["qty0", "qty1", "qty2"], "cell_outputs": cells, "active_count": 3, "min_distinct_windows": 4}
    if tid.startswith("v2_pfd"):
        return {"kind": "pfd", "ref": "early_event", "div": "late_event", "up": "raise_pulse", "dn": "lower_pulse", "lock": "locked" if "lock" in tid else None}
    if tid.startswith("v2_divider") or tid.startswith("v2_counter"):
        if "counter_not_gray" in tid:
            return {"kind": "divider", "clock": "advance", "output": "tick_out", "counter_bits": ["cnt0", "cnt1", "cnt2", "cnt3"], "min_unique_codes": 5}
        return {"kind": "divider", "clock": "advance", "output": "tick_out", "ratio": 3 if "odd" in tid else 4}
    if tid.startswith("v2_sample_hold"):
        return {"kind": "sample_hold", "vin": "sense_node", "clock": "capture", "vout": "latched_level", "settled": "settled" if "calibration" in tid else None}
    raise ValueError(tid)


def _prompt(entry: dict[str, Any], spec: dict[str, Any]) -> str:
    tid = entry["task_id"]
    lines = [
        f"Write a pure Verilog-A module named `{tid}`.",
        "",
        "Use voltage-domain electrical ports only. Provide one DUT file `dut.va` and one Spectre/EVAS testbench `tb_ref.scs`.",
        "The implementation must be compatible with real Cadence Spectre: declare port direction and electrical discipline separately, and drive outputs with unconditional transition contributions.",
        "",
        f"Mechanism intent: {entry['prompt_strategy']}",
        "",
        "Public interface:",
    ]
    if spec["kind"] == "adc_dac":
        lines.append(f"- Inputs: `{spec['vin']}`, `{spec['clock']}`, `{spec['rst']}`, `vdd`, `vss`.")
        lines.append(f"- Outputs: `{', '.join(reversed(spec['bits_lsb_first']))}`, `{spec['vout']}`" + (f", `{spec['settled']}`." if spec.get("settled") else "."))
        lines.append("Behavior: sample the input on the clock, hold one shared quantized code, drive both the code pins and reconstructed level from that same held code.")
    elif spec["kind"] == "binary_dac":
        lines.append(f"- Inputs: `{', '.join(spec['bits_lsb_first'])}`, `vdd`, `vss`.")
        lines.append(f"- Outputs: `{spec['vout']}`" + (f", `{spec['guard']}`." if spec.get("guard") else "."))
        lines.append("Behavior: binary-weighted reconstruction. Do not implement thermometer or unit-cell active-count coding.")
    elif spec["kind"] == "dwa":
        lines.append("- Inputs: `advance`, `clear_n`, `qty0`, `qty1`, `qty2`, `vdd`, `vss`.")
        lines.append(f"- Outputs: `{', '.join(spec['cell_outputs'])}`.")
        lines.append("Behavior: rotate a contiguous active-cell window on each advance event; do not randomize or scramble the selection.")
    elif spec["kind"] == "pfd":
        lines.append("- Inputs: `early_event`, `late_event`, `vdd`, `vss`.")
        lines.append("- Outputs: `raise_pulse`, `lower_pulse`" + (", `locked`." if spec.get("lock") else "."))
        lines.append("Behavior: generate mutually exclusive event-order pulses. This is not an XOR detector.")
    elif spec["kind"] == "divider":
        lines.append("- Inputs: `advance`, `clear_n`, `vdd`, `vss`.")
        outs = ["tick_out"] + spec.get("counter_bits", [])
        lines.append(f"- Outputs: `{', '.join(outs)}`.")
        lines.append("Behavior: count input events and update outputs synchronously; binary counter tasks are not Gray-code tasks.")
    elif spec["kind"] == "sample_hold":
        lines.append("- Inputs: `sense_node`, `capture`, `vdd`, `vss`.")
        lines.append("- Outputs: `latched_level`" + (", `settled`." if spec.get("settled") else "."))
        lines.append("Behavior: sample only at capture events and hold between events. Do not build a continuous follower.")
    lines.append("")
    lines.append("The testbench should exercise the observable behavior and save every public input/output used by the checker.")
    return "\n".join(lines) + "\n"


def _materialize(entry: dict[str, Any]) -> None:
    tid = entry["task_id"]
    spec = _make_spec(entry)
    task_dir = TASK_ROOT / tid
    if task_dir.exists():
        shutil.rmtree(task_dir)
    gold = task_dir / "gold"
    gold.mkdir(parents=True)

    if spec["kind"] == "adc_dac":
        va = _adc_dac_va(tid, spec["vin"], spec["clock"], spec["rst"], spec["bits_lsb_first"], spec["vout"], settled=spec.get("settled"))
        sources = [
            _pulse_source("Vclk", spec["clock"], "2n", "0.9n"),
            f"Vrst ({spec['rst']} 0) vsource type=pwl wave=[ 0 0 3n 0 3.1n 0.9 90n 0.9 ]",
            f"Vvin ({spec['vin']} 0) vsource type=pwl wave=[ 0 0 90n 0.9 ]",
        ]
        ports = [spec["vin"], spec["clock"], spec["rst"], "vdd", "vss"] + list(reversed(spec["bits_lsb_first"])) + [spec["vout"]] + ([spec["settled"]] if spec.get("settled") else [])
        save = [spec["vin"], spec["clock"], spec["rst"], spec["vout"], *spec["bits_lsb_first"]] + ([spec["settled"]] if spec.get("settled") else [])
    elif spec["kind"] == "binary_dac":
        va = _binary_dac_va(tid, spec["bits_lsb_first"], spec["vout"], guard=spec.get("guard"))
        sources = [_pulse_source(f"V{bit}", bit, f"{2 ** (i + 1)}n", f"{2 ** i}n", "1n") for i, bit in enumerate(spec["bits_lsb_first"])]
        ports = spec["bits_lsb_first"] + ["vdd", "vss", spec["vout"]] + ([spec["guard"]] if spec.get("guard") else [])
        save = [*spec["bits_lsb_first"], spec["vout"]] + ([spec["guard"]] if spec.get("guard") else [])
    elif spec["kind"] == "dwa":
        va = _dwa_va(tid, spec["clock"], spec["rst"], spec["bits_lsb_first"], spec["cell_outputs"])
        sources = [
            _pulse_source("Vclk", spec["clock"], "4n", "1.8n"),
            f"Vrst ({spec['rst']} 0) vsource type=pwl wave=[ 0 0 4n 0 4.1n 0.9 120n 0.9 ]",
            "Vqty0 (qty0 0) vsource dc=0.9",
            "Vqty1 (qty1 0) vsource dc=0.9",
            "Vqty2 (qty2 0) vsource dc=0",
        ]
        ports = [spec["clock"], spec["rst"], *spec["bits_lsb_first"], "vdd", "vss", *spec["cell_outputs"]]
        save = [spec["clock"], spec["rst"], *spec["bits_lsb_first"], *spec["cell_outputs"]]
    elif spec["kind"] == "pfd":
        va = _pfd_va(tid, spec["ref"], spec["div"], spec["up"], spec["dn"], lock=spec.get("lock"))
        sources = [
            _pulse_source("Vref", spec["ref"], "10n", "4n", "1n"),
            _pulse_source("Vdiv", spec["div"], "10n", "4n", "4n"),
        ]
        ports = [spec["ref"], spec["div"], "vdd", "vss", spec["up"], spec["dn"]] + ([spec["lock"]] if spec.get("lock") else [])
        save = [spec["ref"], spec["div"], spec["up"], spec["dn"]] + ([spec["lock"]] if spec.get("lock") else [])
    elif spec["kind"] == "divider":
        va = _divider_va(tid, spec["clock"], "clear_n", spec["output"], counter_bits=spec.get("counter_bits"), ratio=spec.get("ratio", 3))
        sources = [
            _pulse_source("Vclk", spec["clock"], "1n", "0.45n"),
            "Vrst (clear_n 0) vsource type=pwl wave=[ 0 0 2n 0 2.1n 0.9 120n 0.9 ]",
        ]
        ports = [spec["clock"], "clear_n", "vdd", "vss", spec["output"]] + spec.get("counter_bits", [])
        save = [spec["clock"], "clear_n", spec["output"]] + spec.get("counter_bits", [])
    elif spec["kind"] == "sample_hold":
        va = _sample_hold_va(tid, spec["vin"], spec["clock"], spec["vout"], settled=spec.get("settled"))
        sources = [
            _pulse_source("Vclk", spec["clock"], "12n", "5n", "1n"),
            f"Vvin ({spec['vin']} 0) vsource type=pwl wave=[ 0 0.1 10n 0.8 30n 0.2 55n 0.75 90n 0.3 120n 0.85 ]",
        ]
        ports = [spec["vin"], spec["clock"], "vdd", "vss", spec["vout"]] + ([spec["settled"]] if spec.get("settled") else [])
        save = [spec["vin"], spec["clock"], spec["vout"]] + ([spec["settled"]] if spec.get("settled") else [])
    else:
        raise ValueError(spec["kind"])

    (gold / "dut.va").write_text(va, encoding="utf-8")
    (gold / "tb_ref.scs").write_text(_tb(tid, "dut.va", ports, sources, save), encoding="utf-8")
    (task_dir / "prompt.md").write_text(_prompt(entry, spec), encoding="utf-8")
    (task_dir / "checker.py").write_text(_checker_wrapper(), encoding="utf-8")
    meta = {
        "task_id": tid,
        "family": "benchmark-v2",
        "source_seed": entry.get("source_seed"),
        "mechanism_family": entry.get("mechanism_family"),
        "perturbation_level": entry.get("perturbation_level"),
        "status": "materialized_draft",
        "scoring": ["dut_compile", "tb_compile", "sim_correct"],
        "gold": {"dut": "gold/dut.va", "tb": "gold/tb_ref.scs"},
        "v2_checker_spec": spec,
        "manifest_entry": entry,
    }
    (task_dir / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")


def main() -> int:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    entries = data.get("tasks", data if isinstance(data, list) else [])
    TASK_ROOT.mkdir(parents=True, exist_ok=True)
    for entry in entries:
        _materialize(entry)
        entry["status"] = "materialized_draft"
    data["tasks"] = entries
    data["materialized_at"] = "2026-04-29"
    MANIFEST.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"[benchmark-v2] materialized {len(entries)} tasks under {TASK_ROOT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
