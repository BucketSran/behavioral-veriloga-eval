#!/usr/bin/env python3
"""Generate benchmark-v2 expansion manifests.

The script creates larger perturbation splits without touching the official
tasks tree.  Materialization and validation are handled by
``materialize_benchmark_v2_tasks.py`` and ``validate_benchmark_v2_gold.py``.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_DIR = ROOT / "benchmark-v2" / "manifests"


ALIASES = {
    "vin": ["sense_level", "measured_quantity", "external_drive", "observed_level", "analog_sample"],
    "clk": ["cadence", "sample_event", "capture_tick", "advance_edge", "strobe"],
    "rst": ["clear_n", "release_n", "armed_n"],
    "vout": ["held_level", "reconstructed_level", "estimate_node", "drive_estimate", "latched_level"],
    "bits": ["q", "dec", "state", "mark", "level"],
    "ref": ["early_event", "lead_edge", "reference_event", "arrival_a", "phase_a"],
    "div": ["late_event", "lag_edge", "feedback_event", "arrival_b", "phase_b"],
    "up": ["raise_pulse", "lead_pulse", "advance_pulse", "up_mark"],
    "dn": ["lower_pulse", "lag_pulse", "retard_pulse", "down_mark"],
    "tick": ["tick_out", "slow_event", "divided_tick", "feedback_tick"],
    "capture_out": ["latched_level", "held_sample", "capture_level", "remembered_level"],
}


def _entry(
    task_id: str,
    *,
    source_seed: str,
    mechanism_family: str,
    perturbation_level: str,
    prompt_strategy: str,
    split: str,
    perturbation_axes: list[str],
    spec_overrides: dict[str, Any] | None = None,
    source_type: str = "seed_92_perturbation",
    external_source_url: str = "not_applicable",
    external_source_license: str = "not_applicable",
    negative_constraints: list[str] | None = None,
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "task_id": task_id,
        "source_type": source_type,
        "source_seed": source_seed,
        "mechanism_family": mechanism_family,
        "perturbation_level": perturbation_level,
        "prompt_strategy": prompt_strategy,
        "gold_required": True,
        "checker_required": True,
        "spectre_parity_required": True,
        "split": split,
        "status": "draft_manifest",
        "perturbation_axes": perturbation_axes,
        "external_source_url": external_source_url,
        "external_source_license": external_source_license,
    }
    if spec_overrides:
        out["spec_overrides"] = spec_overrides
    if negative_constraints:
        out["negative_constraints"] = negative_constraints
    return out


def _manifest(name: str, purpose: str, tasks: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "manifest_version": 1,
        "name": name,
        "created": "2026-04-29",
        "purpose": purpose,
        "storage_rule": "Keep these tasks under benchmark-v2/tasks until gold EVAS and Spectre validation are reviewed.",
        "task_count": len(tasks),
        "required_task_fields": ["prompt.md", "gold/dut.va", "gold/tb_ref.scs", "checker.py", "meta.json"],
        "tasks": tasks,
    }


def _adc_entries(split: str, count: int, hard: bool = False) -> list[dict[str, Any]]:
    tasks = []
    for i in range(count):
        width = [3, 4, 5, 6][i % 4]
        vin = ALIASES["vin"][i % len(ALIASES["vin"])]
        clk = ALIASES["clk"][i % len(ALIASES["clk"])]
        vout = ALIASES["vout"][i % len(ALIASES["vout"])]
        bits_prefix = ALIASES["bits"][i % len(ALIASES["bits"])]
        settled = "settled" if i % 5 == 0 else None
        tag = "not_raw_follower" if hard else "alias_sampled_code"
        level = "P4_negative_distractor" if hard else ["P2_semantic_alias", "P3_keyword_removal", "P5_parameter_checker", "P6_system_composition"][i % 4]
        axes = ["rename", "width", "shared_state"] + (["negative_constraint"] if hard else [])
        tasks.append(
            _entry(
                f"v2_adc_dac_{tag}_{width}b_{i:03d}",
                source_seed="adc_dac_ideal_4b",
                mechanism_family="adc_dac_quantize_reconstruct",
                perturbation_level=level,
                prompt_strategy=(
                    "Require sampled decision bits and one held reconstructed level from the same quantized state; "
                    "do not let the reconstruction continuously follow the raw input."
                    if hard
                    else "Perturb the sampled quantize/reconstruct interface with aliased names and width changes."
                ),
                split=split,
                perturbation_axes=axes,
                spec_overrides={
                    "width": width,
                    "vin": vin,
                    "clock": clk,
                    "vout": vout,
                    "bits_prefix": bits_prefix,
                    "settled": settled,
                    "min_unique_codes": min(8, 1 << width),
                },
                negative_constraints=["not_continuous_tracking", "single_code_source_of_truth"] if hard else None,
            )
        )
    return tasks


def _binary_dac_entries(split: str, count: int, hard: bool = False) -> list[dict[str, Any]]:
    tasks = []
    for i in range(count):
        width = [4, 5, 6][i % 3]
        prefix = ["weight", "input", "scale", "tap"][i % 4]
        guard = "glitch_guard" if i % 4 == 0 else None
        tag = "not_thermometer" if hard else "weighted_sum"
        tasks.append(
            _entry(
                f"v2_binary_dac_{tag}_{width}b_{i:03d}",
                source_seed="dac_binary_clk_4b_smoke",
                mechanism_family="binary_weighted_dac",
                perturbation_level="P4_negative_distractor" if hard else ["P2_semantic_alias", "P3_keyword_removal", "P5_parameter_checker"][i % 3],
                prompt_strategy=(
                    "Require binary-weighted reconstruction and explicitly reject thermometer or unary active-count behavior."
                    if hard
                    else "Perturb a binary-weighted analog reconstruction task with width and naming changes."
                ),
                split=split,
                perturbation_axes=["width", "role_binding"] + (["negative_constraint"] if hard else ["rename"]),
                spec_overrides={
                    "width": width,
                    "bits_prefix": prefix,
                    "vout": ["analog_sum", "weighted_level", "recon_value"][i % 3],
                    "guard": guard,
                    "min_unique_codes": min(8, 1 << width),
                },
                negative_constraints=["not_thermometer", "not_unit_cell_count"] if hard else None,
            )
        )
    return tasks


def _dwa_entries(split: str, count: int, hard: bool = False) -> list[dict[str, Any]]:
    tasks = []
    for i in range(count):
        tag = "not_random_scramble" if hard else "circular_cursor"
        tasks.append(
            _entry(
                f"v2_dwa_{tag}_{i:03d}",
                source_seed="dwa_ptr_gen_smoke",
                mechanism_family="dwa_pointer_rotation",
                perturbation_level="P4_negative_distractor" if hard else ["P2_semantic_alias", "P3_keyword_removal", "P5_parameter_checker", "P6_system_composition"][i % 4],
                prompt_strategy=(
                    "Use a deterministic rotating contiguous unit-cell window; random scramble or static selection is forbidden."
                    if hard
                    else "Describe rotating unit-cell selection with cursor/window wording and wraparound checks."
                ),
                split=split,
                perturbation_axes=["wraparound", "window", "coverage"] + (["negative_constraint"] if hard else ["keyword_removal"]),
                spec_overrides={
                    "clock": ["advance", "rotate_tick", "next_window", "selection_event"][i % 4],
                    "rst": ["clear_n", "release_n"][i % 2],
                    "bits_lsb_first": [f"qty{i % 3}_{j}" for j in range(3)],
                    "cell_outputs": [f"unit{j}" for j in range(8)] if i % 2 else [f"cell{j}" for j in range(8)],
                    "min_distinct_windows": 4,
                },
                negative_constraints=["not_random", "not_static_window"] if hard else None,
            )
        )
    return tasks


def _pfd_entries(split: str, count: int, hard: bool = False) -> list[dict[str, Any]]:
    tasks = []
    for i in range(count):
        lock = "locked" if i % 5 == 0 else None
        tag = "not_xor" if hard else "lead_lag"
        tasks.append(
            _entry(
                f"v2_pfd_{tag}_{i:03d}",
                source_seed="pfd_reset_race_smoke",
                mechanism_family="pfd_event_order",
                perturbation_level="P4_negative_distractor" if hard else ["P2_semantic_alias", "P3_keyword_removal", "P5_parameter_checker", "P6_system_composition"][i % 4],
                prompt_strategy=(
                    "Generate event-order pulses with internal state and reset timing; a stateless XOR phase detector is forbidden."
                    if hard
                    else "Perturb event-order pulse generation using lead/lag aliases and optional lock indication."
                ),
                split=split,
                perturbation_axes=["event_order", "mutual_exclusion"] + (["negative_constraint"] if hard else ["rename"]),
                spec_overrides={
                    "ref": ALIASES["ref"][i % len(ALIASES["ref"])],
                    "div": ALIASES["div"][i % len(ALIASES["div"])],
                    "up": ALIASES["up"][i % len(ALIASES["up"])],
                    "dn": ALIASES["dn"][i % len(ALIASES["dn"])],
                    "lock": lock,
                },
                negative_constraints=["not_xor_detector", "must_remember_event_order"] if hard else None,
            )
        )
    return tasks


def _divider_entries(split: str, count: int, hard: bool = False) -> list[dict[str, Any]]:
    tasks = []
    for i in range(count):
        counter = hard and i % 2 == 0
        prefix = "counter_not_gray_code" if counter else ("event_counter_not_async" if hard else "event_counter")
        spec: dict[str, Any] = {
            "clock": ALIASES["clk"][i % len(ALIASES["clk"])],
            "output": ALIASES["tick"][i % len(ALIASES["tick"])],
            "ratio": [2, 3, 4, 5, 6][i % 5],
        }
        if counter:
            spec["counter_bits"] = [f"cnt{i % 3}_{j}" for j in range(4)]
            spec["min_unique_codes"] = 5
        tasks.append(
            _entry(
                f"v2_{prefix}_{i:03d}",
                source_seed="clk_divider",
                mechanism_family="divider_counter",
                perturbation_level="P4_negative_distractor" if hard else ["P2_semantic_alias", "P3_keyword_removal", "P5_parameter_checker"][i % 3],
                prompt_strategy=(
                    "Require synchronous counted-event behavior; reject Gray-code or asynchronous toggle shortcuts when binary state is requested."
                    if hard
                    else "Perturb event-counting divider behavior with ratio and naming changes."
                ),
                split=split,
                perturbation_axes=["ratio", "reset", "encoding"] + (["negative_constraint"] if hard else ["rename"]),
                spec_overrides=spec,
                negative_constraints=["not_gray_code", "not_async_toggle_only"] if hard else None,
            )
        )
    return tasks


def _sample_hold_entries(split: str, count: int, hard: bool = False) -> list[dict[str, Any]]:
    tasks = []
    for i in range(count):
        settled = "settled" if i % 4 == 0 else None
        tag = "not_follower" if hard else "latched_level"
        tasks.append(
            _entry(
                f"v2_sample_hold_{tag}_{i:03d}",
                source_seed="sample_hold_smoke",
                mechanism_family="sample_hold",
                perturbation_level="P4_negative_distractor" if hard else ["P2_semantic_alias", "P3_keyword_removal", "P5_parameter_checker", "P6_system_composition"][i % 4],
                prompt_strategy=(
                    "Capture only on the event and hold between events; continuous follower behavior is forbidden."
                    if hard
                    else "Perturb event-captured held-level behavior using renamed sense/capture/output roles."
                ),
                split=split,
                perturbation_axes=["aperture", "latched_state"] + (["negative_constraint"] if hard else ["rename"]),
                spec_overrides={
                    "vin": ALIASES["vin"][i % len(ALIASES["vin"])],
                    "clock": ALIASES["clk"][i % len(ALIASES["clk"])],
                    "vout": ALIASES["capture_out"][i % len(ALIASES["capture_out"])],
                    "settled": settled,
                },
                negative_constraints=["not_continuous_follower"] if hard else None,
            )
        )
    return tasks


def build_seed_r2() -> dict[str, Any]:
    split = "v2-seed-perturbation-r2"
    tasks: list[dict[str, Any]] = []
    for builder in [_adc_entries, _binary_dac_entries, _dwa_entries, _pfd_entries, _divider_entries, _sample_hold_entries]:
        tasks.extend(builder(split, 20, hard=False))
    return _manifest(split, "120-task seed perturbation split derived from original-92 mechanism families.", tasks)


def build_hard_negative() -> dict[str, Any]:
    split = "v2-hard-negative-r1"
    tasks: list[dict[str, Any]] = []
    counts = [17, 17, 17, 17, 16, 16]
    for builder, count in zip([_adc_entries, _binary_dac_entries, _dwa_entries, _pfd_entries, _divider_entries, _sample_hold_entries], counts):
        tasks.extend(builder(split, count, hard=True))
    return _manifest(split, "100-task hard-negative split designed to catch tempting but wrong mechanism templates.", tasks)


def build_external() -> dict[str, Any]:
    split = "v2-external-architecture-r1"
    tasks: list[dict[str, Any]] = []
    external_source_url = "pattern-derived:public-analog-behavioral-modeling"
    external_source_license = "not_applicable_behavioral_pattern"
    for i in range(30):
        tasks.append(
            _entry(
                f"v2_ext_threshold_detector_{i:03d}",
                source_seed=external_source_url,
                mechanism_family="threshold_detector",
                perturbation_level=["P2_semantic_alias", "P3_keyword_removal", "P4_negative_distractor"][i % 3],
                prompt_strategy="Convert a sensor level into a digital-like voltage decision using threshold behavior.",
                split=split,
                perturbation_axes=["external_architecture", "threshold", "rename"],
                spec_overrides={"vin": ["sense_level", "sensor_reading", "probe_voltage"][i % 3], "vout": ["decision_level", "trip_flag", "threshold_state"][i % 3]},
                source_type="external_architecture",
                external_source_url=external_source_url,
                external_source_license=external_source_license,
            )
        )
        tasks.append(
            _entry(
                f"v2_ext_window_detector_{i:03d}",
                source_seed=external_source_url,
                mechanism_family="window_detector",
                perturbation_level=["P2_semantic_alias", "P5_parameter_checker", "P6_system_composition"][i % 3],
                prompt_strategy="Classify a sensor voltage into below/inside/above window flags.",
                split=split,
                perturbation_axes=["external_architecture", "window", "multi_output"],
                spec_overrides={"vin": ["sensor_level", "measured_voltage", "monitor_node"][i % 3]},
                source_type="external_architecture",
                external_source_url=external_source_url,
                external_source_license=external_source_license,
            )
        )
        tasks.append(
            _entry(
                f"v2_ext_limiter_model_{i:03d}",
                source_seed=external_source_url,
                mechanism_family="analog_limiter",
                perturbation_level=["P2_semantic_alias", "P4_negative_distractor", "P5_parameter_checker"][i % 3],
                prompt_strategy="Model a bounded analog transfer that follows midrange input but clamps outside lower and upper limits.",
                split=split,
                perturbation_axes=["external_architecture", "nonlinear_transfer", "negative_constraint"],
                spec_overrides={"vin": ["raw_level", "unbounded_signal", "input_quantity"][i % 3], "vout": ["limited_level", "clamped_level", "safe_output"][i % 3]},
                source_type="external_architecture",
                external_source_url=external_source_url,
                external_source_license=external_source_license,
                negative_constraints=["not_unbounded_follower"],
            )
        )
        tasks.append(
            _entry(
                f"v2_ext_pulse_stretcher_{i:03d}",
                source_seed=external_source_url,
                mechanism_family="event_pulse_stretcher",
                perturbation_level=["P2_semantic_alias", "P3_keyword_removal", "P5_parameter_checker"][i % 3],
                prompt_strategy="Convert each rising event into a finite-width voltage pulse and return low after the pulse window.",
                split=split,
                perturbation_axes=["external_architecture", "event_to_pulse", "timing"],
                spec_overrides={"trigger": ["event_in", "trigger_level", "arrival_mark"][i % 3], "vout": ["stretched_pulse", "pulse_out", "one_shot_level"][i % 3]},
                source_type="external_architecture",
                external_source_url=external_source_url,
                external_source_license=external_source_license,
            )
        )
    return _manifest(split, "120-task external architecture split from compact behavioral analog model patterns.", tasks)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--only", choices=["all", "seed-r2", "hard-negative", "external"], default="all")
    args = ap.parse_args()
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    builders = {
        "seed-r2": build_seed_r2,
        "hard-negative": build_hard_negative,
        "external": build_external,
    }
    selected = builders if args.only == "all" else {args.only: builders[args.only]}
    for _name, builder in selected.items():
        data = builder()
        path = MANIFEST_DIR / f"{data['name']}.json"
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        print(f"[benchmark-v2] wrote {path} tasks={len(data['tasks'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
