#!/usr/bin/env python3
"""Materialize reviewed exact-five semantic decisions without editing prep inputs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PREP = ROOT / "operations" / "tri_form_derivation_prep"
DEFAULT_OUTPUT = ROOT / "operations" / "dut_base_exact_five" / "SEMANTIC_SELECTION_DECISIONS.json"


OVERRIDES = {
    "003": ["neg_004_middle_code_wrong", "neg_001_threshold_too_wide", "neg_006_live_vin_on_phi2", "neg_007_missing_residue_clamp", "neg_003_residue_feedback_sign_swapped"],
    "007": ["neg_001_too_slow_alpha", "neg_003_inverted_input", "neg_002_passthrough_timer", "neg_006_wrong_initial_state", "neg_007_wrong_update_period"],
    "019": ["neg_001_missing_phase_increment", "neg_004_missing_phase_wrap", "neg_002_phase_increment_too_small", "neg_006_control_direction_inverted", "neg_005_wrap_does_not_toggle_clock"],
    "031": ["neg_001_linear_gain_error", "neg_002_positive_limit_slope", "neg_003_negative_limit_slope", "neg_006_asynchronous_tracking", "neg_007_output_clamp_missing"],
    "032": ["neg_001_reduced_small_signal_gain", "neg_002_positive_compression_bypass", "neg_003_negative_compression_bypass", "neg_005_output_clamp_bypass", "neg_007_reset_ignored"],
    "048": ["neg_001_off_by_one_count", "neg_002_reversed_thermometer_bus", "neg_003_enable_ignored", "neg_005_reversed_bit_order", "neg_006_weak_high_level"],
    "067": ["neg_001_force_zero", "neg_002_instantaneous_error_only", "neg_003_reversed_observed_bits", "neg_004_rounds_ideal_code", "neg_006_signed_error_only"],
    "070": ["neg_001_zero", "neg_002_no_jitter", "neg_004_unbounded", "neg_005_ignore_seed", "neg_006_nonrepeating_sequence"],
    "075": ["neg_001_zero", "neg_002_threshold_shifted", "neg_004_reset_polarity_wrong", "neg_005_metric_scale_low", "neg_006_monotonic_notch"],
    "105": ["neg_001_zero", "neg_002_short_pulse", "neg_003_falling_edge_trigger", "neg_004_stuck_high_after_first", "neg_006_no_output_delay"],
    "108": ["neg_001_zero", "neg_002_rising_only", "neg_003_short_pulse", "neg_004_no_delay", "neg_006_no_output_delay"],
    "343": ["neg_001_stage1_threshold_shift", "neg_002_residue_gain_low", "neg_003_stage2_threshold_shift", "neg_004_coarse_alignment_weight", "neg_005_valid_stuck_low"],
    "380": ["neg_002_envelope_dbg_stuck", "neg_001_no_modulation", "neg_005_carrier_inverted", "neg_004_missing_clear", "neg_006_output_not_clamped"],
    "386": ["neg_002_gain_metric_wrong", "neg_001_no_compression", "neg_003_phase_metric_stuck", "neg_004_flag_stuck_low", "neg_006_output_not_clamped"],
    "398": ["neg_001_stage1_wrong", "neg_002_no_slew_limit", "neg_003_settled_stuck_high", "neg_005_clamp_flag_stuck_low", "neg_006_asynchronous_update"],
}


CHANGE_REASONS = {
    "003": "Retain residue-feedback sign coverage; two sub-ADC code-region faults were less diverse than a direct MDAC residue-mapping fault.",
    "007": "Retain the independent periodic-update cadence fault; archive the stuck-zero response proxy because low-pass liveness is already exercised by richer response faults.",
    "019": "Retain VCO control-direction monotonicity; archive timer-period error because periodic phase update already has several direct representatives.",
    "031": "A limiting amplifier must cover both positive and negative limiting slopes; metric/reset proxies cannot replace the primary transfer curve.",
    "032": "LNA compression requires both positive and negative main-output compression paths; archive the auxiliary metric and asynchronous proxy.",
    "048": "Retain thermometer-bus orientation; missing-top-cell duplicates endpoint/count semantics already covered by off-by-one count.",
    "067": "Retain maximum-error state across samples; archive half-scale metric because output scaling is less central than retention semantics.",
    "070": "Retain actual jitter modulation; archive weak-high output and slow-period variants because bounds, seed, and repeatability already cover timing quality.",
    "075": "Retain sampled threshold and peak-retention behavior; archive low-amplitude and smoothing proxies that are less central to peak detection.",
    "105": "One-shot pulse width is core behavior and outranks the generic low-metric proxy.",
    "108": "Bidirectional crossing detection is core behavior and outranks the generic low-metric proxy.",
    "343": "Pipeline ADC dataflow must include residue gain; reset clear is secondary to stage thresholds, alignment, valid latency, and residue transfer.",
    "380": "Carrier polarity belongs to the AM transfer equation; the auxiliary valid flag is less central than the carrier path.",
    "386": "AM/PM phase observability is named core behavior; reset/disable clear is secondary to gain, phase, compression, flag, and clamp behavior.",
    "398": "A slew macromodel must test slew limiting; generic clear behavior is secondary to stage metric, slew, settling, clamp, and clocked update.",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--active-index", type=Path, default=PREP / "ACTIVE_MUTATION_SUITE_INDEX.json")
    parser.add_argument("--archive-index", type=Path, default=PREP / "EXCLUDED_MUTATION_ARCHIVE_INDEX.json")
    parser.add_argument("--overfive-review", type=Path, default=PREP / "OVERFIVE_REVIEW.json")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    active = read_json(args.active_index)
    archive = read_json(args.archive_index)
    review = read_json(args.overfive_review)
    active_by = {str(row["family_id"]): row for row in active["families"]}
    archive_by = {str(row["family_id"]): row for row in archive["families"]}
    review_by = {str(row["family_id"]): row for row in review["families"]}
    families = []
    for family in sorted(archive_by):
        review_row = review_by[family]
        catalog = review_row["catalog"]
        semantics = {
            str(row["id"]): row
            for row in (catalog.get("proposed_suite_semantics") or []) + (catalog.get("excluded_semantics") or [])
        }
        active_ids = list(OVERRIDES.get(family, active_by[family]["testbench_suite"]))
        excluded_ids = sorted(set(semantics) - set(active_ids))
        active_faults = sorted({str(semantics[value].get("fault_class") or "unspecified") for value in active_ids})
        active_properties = sorted({
            str(prop) for value in active_ids for prop in semantics[value].get("violated_property_ids") or []
        })
        exclusion_reasons = {}
        for mutation_id in excluded_ids:
            row = semantics[mutation_id]
            overlapping = sorted(set(row.get("violated_property_ids") or []) & set(active_properties))
            overlap_text = ", ".join(overlapping) if overlapping else "the active suite's broader trigger coverage"
            exclusion_reasons[mutation_id] = (
                f"Archive {row.get('fault_class') or 'this fault'} as provenance-only: its observable coverage overlaps "
                f"{overlap_text}, while the selected five retain broader fault-class and trigger diversity."
            )
        families.append({
            "family_id": family,
            "decision": "changed_after_semantic_review" if family in OVERRIDES else "approved_after_semantic_review",
            "active_mutation_ids": active_ids,
            "excluded_mutation_ids": excluded_ids,
            "selection_reason": CHANGE_REASONS.get(
                family,
                "Retain the Bugfix seed and five complementary observable faults spanning "
                + ", ".join(active_faults)
                + "; exclusions add less property or trigger diversity.",
            ),
            "exclusion_reasons": exclusion_reasons,
        })
    supplemental = [
        {
            "family_id": "092",
            "status": "approved_distinct_trigger_semantics",
            "finding": "The gain-transfer labels repeat, but unity-gain tests a fixed transfer error while ignores-gain-parameter tests parameter override behavior across gain settings; both are observably distinct.",
        },
        {
            "family_id": "098",
            "status": "approved_distinct_trigger_semantics",
            "finding": "The spectral-error labels repeat, but no-frequency-step removes the pre/post period transition while late-switch preserves both periods at the wrong transition time; both are observably distinct.",
        },
    ]
    payload = {
        "schema_version": "v4-exact-five-semantic-decisions-v1",
        "policy": "Manual semantic review selects by observable fault, property, and trigger diversity; mutation ID order is not a selection criterion.",
        "family_count": len(families),
        "changed_family_count": sum(row["decision"].startswith("changed") for row in families),
        "families": families,
        "supplemental_exact_five_reviews": supplemental,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"family_count": len(families), "changed_family_count": payload["changed_family_count"], "output": str(args.output)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
