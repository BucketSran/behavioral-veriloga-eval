#!/usr/bin/env python3
"""Slot-bound completion-package materializer for benchmark-v2 prompts.

Unlike the benchmark authoring materializer, this reads public `prompt.md`
files and writes generated candidates under a normal generated-root layout. It
does not read the gold DUT/testbench.  The task-local checker is used later only
for validation.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path
from typing import Any

from materialize_benchmark_v2_tasks import (
    _adc_dac_va,
    _binary_dac_va,
    _divider_va,
    _dwa_va,
    _pfd_va,
    _pulse_source,
    _sample_hold_va,
    _tb,
)


ROOT = Path(__file__).resolve().parents[1]
TASK_ROOT = ROOT / "benchmark-v2" / "tasks"


def _extract_module(prompt: str) -> str:
    match = re.search(r"module named `([^`]+)`", prompt)
    if not match:
        raise ValueError("module name not found in prompt")
    return match.group(1)


def _extract_bullet_ports(prompt: str, label: str) -> list[str]:
    match = re.search(rf"- {label}:\s*(.*)", prompt)
    if not match:
        return []
    line = match.group(1)
    ports: list[str] = []
    for chunk in re.findall(r"`([^`]+)`", line):
        for part in chunk.split(","):
            name = part.strip().rstrip(".")
            if name:
                ports.append(name)
    return ports


def _bits_from_ports(ports: list[str]) -> list[str]:
    bit_ports = [port for port in ports if re.search(r"\d+$", port)]
    return sorted(bit_ports, key=lambda name: int(re.search(r"(\d+)$", name).group(1)))


def _spec_from_prompt(prompt: str) -> dict[str, Any]:
    low = prompt.lower()
    inputs = _extract_bullet_ports(prompt, "Inputs")
    outputs = _extract_bullet_ports(prompt, "Outputs")
    if "shared quantized code" in low or "reconstructed level" in low:
        bits = _bits_from_ports(outputs)
        vout = next(port for port in outputs if port not in bits and port != "settled")
        return {
            "kind": "adc_dac",
            "vin": inputs[0],
            "clock": inputs[1],
            "rst": inputs[2],
            "bits_lsb_first": bits,
            "vout": vout,
            "settled": "settled" if "settled" in outputs else None,
        }
    if "binary-weighted reconstruction" in low:
        bits = [port for port in inputs if port not in {"vdd", "vss"}]
        vout = next(port for port in outputs if port != "glitch_guard")
        return {
            "kind": "binary_dac",
            "bits_lsb_first": _bits_from_ports(bits),
            "vout": vout,
            "guard": "glitch_guard" if "glitch_guard" in outputs else None,
        }
    if "rotate a contiguous active-cell window" in low:
        return {
            "kind": "dwa",
            "clock": "advance",
            "rst": "clear_n",
            "bits_lsb_first": ["qty0", "qty1", "qty2"],
            "cell_outputs": outputs,
        }
    if "mutually exclusive event-order pulses" in low:
        return {
            "kind": "pfd",
            "ref": inputs[0],
            "div": inputs[1],
            "up": outputs[0],
            "dn": outputs[1],
            "lock": "locked" if "locked" in outputs else None,
        }
    if "count input events" in low:
        counter_bits = [port for port in outputs if port.startswith("cnt")]
        return {
            "kind": "divider",
            "clock": inputs[0],
            "rst": inputs[1],
            "output": "tick_out",
            "counter_bits": _bits_from_ports(counter_bits) if counter_bits else None,
            "ratio": 3 if "odd" in low else 4,
        }
    if "sample only at capture" in low:
        return {
            "kind": "sample_hold",
            "vin": inputs[0],
            "clock": inputs[1],
            "vout": outputs[0],
            "settled": "settled" if "settled" in outputs else None,
        }
    raise ValueError("unsupported prompt mechanism")


def _materialize_task(task_dir: Path, sample_dir: Path) -> dict[str, Any]:
    prompt = (task_dir / "prompt.md").read_text(encoding="utf-8")
    module = _extract_module(prompt)
    spec = _spec_from_prompt(prompt)
    if sample_dir.exists():
        shutil.rmtree(sample_dir)
    sample_dir.mkdir(parents=True)

    if spec["kind"] == "adc_dac":
        va = _adc_dac_va(module, spec["vin"], spec["clock"], spec["rst"], spec["bits_lsb_first"], spec["vout"], settled=spec.get("settled"))
        sources = [
            _pulse_source("Vclk", spec["clock"], "2n", "0.9n"),
            f"Vrst ({spec['rst']} 0) vsource type=pwl wave=[ 0 0 3n 0 3.1n 0.9 90n 0.9 ]",
            f"Vvin ({spec['vin']} 0) vsource type=pwl wave=[ 0 0 90n 0.9 ]",
        ]
        ports = [spec["vin"], spec["clock"], spec["rst"], "vdd", "vss"] + list(reversed(spec["bits_lsb_first"])) + [spec["vout"]] + ([spec["settled"]] if spec.get("settled") else [])
        save = [spec["vin"], spec["clock"], spec["rst"], spec["vout"], *spec["bits_lsb_first"]] + ([spec["settled"]] if spec.get("settled") else [])
    elif spec["kind"] == "binary_dac":
        va = _binary_dac_va(module, spec["bits_lsb_first"], spec["vout"], guard=spec.get("guard"))
        sources = [_pulse_source(f"V{bit}", bit, f"{2 ** (i + 1)}n", f"{2 ** i}n", "1n") for i, bit in enumerate(spec["bits_lsb_first"])]
        ports = spec["bits_lsb_first"] + ["vdd", "vss", spec["vout"]] + ([spec["guard"]] if spec.get("guard") else [])
        save = [*spec["bits_lsb_first"], spec["vout"]] + ([spec["guard"]] if spec.get("guard") else [])
    elif spec["kind"] == "dwa":
        va = _dwa_va(module, spec["clock"], spec["rst"], spec["bits_lsb_first"], spec["cell_outputs"])
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
        va = _pfd_va(module, spec["ref"], spec["div"], spec["up"], spec["dn"], lock=spec.get("lock"))
        sources = [
            _pulse_source("Vref", spec["ref"], "10n", "4n", "1n"),
            _pulse_source("Vdiv", spec["div"], "10n", "4n", "4n"),
        ]
        ports = [spec["ref"], spec["div"], "vdd", "vss", spec["up"], spec["dn"]] + ([spec["lock"]] if spec.get("lock") else [])
        save = [spec["ref"], spec["div"], spec["up"], spec["dn"]] + ([spec["lock"]] if spec.get("lock") else [])
    elif spec["kind"] == "divider":
        va = _divider_va(module, spec["clock"], spec["rst"], spec["output"], counter_bits=spec.get("counter_bits"), ratio=spec.get("ratio", 3))
        sources = [
            _pulse_source("Vclk", spec["clock"], "1n", "0.45n"),
            f"Vrst ({spec['rst']} 0) vsource type=pwl wave=[ 0 0 2n 0 2.1n 0.9 120n 0.9 ]",
        ]
        ports = [spec["clock"], spec["rst"], "vdd", "vss", spec["output"]] + (spec.get("counter_bits") or [])
        save = [spec["clock"], spec["rst"], spec["output"]] + (spec.get("counter_bits") or [])
    elif spec["kind"] == "sample_hold":
        va = _sample_hold_va(module, spec["vin"], spec["clock"], spec["vout"], settled=spec.get("settled"))
        sources = [
            _pulse_source("Vclk", spec["clock"], "12n", "5n", "1n"),
            f"Vvin ({spec['vin']} 0) vsource type=pwl wave=[ 0 0.1 10n 0.8 30n 0.2 55n 0.75 90n 0.3 120n 0.85 ]",
        ]
        ports = [spec["vin"], spec["clock"], "vdd", "vss", spec["vout"]] + ([spec["settled"]] if spec.get("settled") else [])
        save = [spec["vin"], spec["clock"], spec["vout"]] + ([spec["settled"]] if spec.get("settled") else [])
    else:
        raise ValueError(spec["kind"])

    (sample_dir / "dut.va").write_text(va, encoding="utf-8")
    (sample_dir / "tb_ref.scs").write_text(_tb(module, "dut.va", ports, sources, save), encoding="utf-8")
    meta = {
        "task_id": task_dir.name,
        "generator": "completion_package_materialize_benchmark_v2.py",
        "source": "public prompt + completion package templates",
        "claim_boundary": "template_transfer_not_gold_replay",
        "slot_spec": spec,
    }
    (sample_dir / "generation_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output-dir", default="generated-completion-package-benchmark-v2-2026-04-29")
    ap.add_argument("--model", default="completion-package-v0")
    ap.add_argument("--task", action="append", default=[])
    args = ap.parse_args()

    out_root = Path(args.output_dir)
    if not out_root.is_absolute():
        out_root = ROOT / out_root
    model = args.model.replace("/", "_")
    selected = set(args.task) if args.task else None
    task_dirs = [path for path in sorted(TASK_ROOT.glob("*/prompt.md")) if selected is None or path.parent.name in selected]
    manifest: dict[str, Any] = {
        "generated_root": str(out_root),
        "model": model,
        "source": "public benchmark-v2 prompts",
        "tasks": {},
    }
    for prompt_path in task_dirs:
        task_id = prompt_path.parent.name
        sample_dir = out_root / model / task_id / "sample_0"
        manifest["tasks"][task_id] = _materialize_task(prompt_path.parent, sample_dir)
    out_root.mkdir(parents=True, exist_ok=True)
    (out_root / "completion_package_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"[completion-package-v2] materialized {len(task_dirs)} tasks under {out_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
