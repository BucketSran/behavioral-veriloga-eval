#!/usr/bin/env python3
"""LEGO-style mechanism skill library and functional router.

The library turns existing closed-set/R26/gold-derived mechanism skeletons into
typed, inspectable skills.  Retrieval is deliberately functional: by default it
does not use task ids or manifest mechanism labels.  It extracts behavior
concepts from the public prompt, binds likely public ports to skill slots, and
returns skill packets that can be injected into EVAS repair prompts.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SKELETONS_PATH = ROOT / "docs" / "CIRCUIT_MECHANISM_SKELETONS.json"


@dataclass(frozen=True)
class LegoSkill:
    skill_id: str
    title: str
    mechanism_family: str
    source: str
    concepts: tuple[str, ...]
    slot_schema: dict[str, str]
    implementation_skeleton: tuple[str, ...]
    code_shape: tuple[str, ...]
    checker_expectations: tuple[str, ...]
    spectre_constraints: tuple[str, ...]
    anti_patterns: tuple[str, ...]
    aliases: tuple[str, ...] = ()
    reject_concepts: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_prompt_packet(self, *, bound_slots: dict[str, list[str]], score: float) -> dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "title": self.title,
            "mechanism_family": self.mechanism_family,
            "score": round(score, 4),
            "bound_slots": bound_slots,
            "slot_schema": self.slot_schema,
            "implementation_skeleton": list(self.implementation_skeleton),
            "code_shape": list(self.code_shape),
            "checker_expectations": list(self.checker_expectations),
            "spectre_constraints": list(self.spectre_constraints),
            "anti_patterns": list(self.anti_patterns),
            "source": self.source,
        }


@dataclass(frozen=True)
class FunctionalIR:
    concepts: tuple[str, ...]
    negative_constraints: tuple[str, ...]
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    identifiers: tuple[str, ...]
    evidence: dict[str, list[str]]


COMMON_SPECTRE_CONSTRAINTS = (
    "Use pure Verilog-A and Cadence Spectre-compatible syntax.",
    "Declare port directions and electrical disciplines separately.",
    "Keep state variables at module scope; avoid declarations inside analog/event/if/loop bodies.",
    "Update held real/integer targets inside events, then drive electrical outputs with unconditional transition() contributions.",
    "Do not use runtime integer indexing into electrical vectors; prefer fixed scalar ports or unrolled accesses.",
    "Use Spectre positional instance syntax in testbenches and keep ahdl_include filenames aligned with generated DUT files.",
)


SKILL_OVERLAYS: dict[str, dict[str, Any]] = {
    "adc_dac_quantize_reconstruct_skeleton": {
        "family": "adc_dac_quantize_reconstruct",
        "aliases": ("converter_quantize_reconstruct_or_decode", "sampled_code_reconstruct"),
        "concepts": ("sample_event", "held_state", "quantized_code", "reconstruct_from_code", "shared_source_of_truth"),
        "checker": (
            "Code pins cover multiple quantized states under ramp or dwell stimulus.",
            "The reconstructed analog level is derived from the same held code, not directly from raw input.",
            "Code and reconstructed output remain stable between sample events unless reset changes them.",
            "Reference range, bit width, and output bit order are bound from public ports/parameters.",
        ),
        "reject": ("continuous_follower",),
    },
    "dac_decode_binary_thermometer_skeleton": {
        "family": "binary_weighted_dac",
        "aliases": ("converter_quantize_reconstruct_or_decode", "binary_or_thermometer_decode"),
        "concepts": ("weighted_sum", "code_or_bits", "held_state", "decode_to_analog"),
        "checker": (
            "Output follows the weighted value of named decision/code inputs.",
            "Binary-weighted tasks must not be treated as thermometer or unary active-count tasks.",
            "Bit order is bound by public names or checker-visible columns, not by declaration order alone.",
            "Clocked variants update only on the public sample/cadence event.",
        ),
        "reject": ("thermometer_required_without_binary",),
    },
    "dwa_pointer_window_skeleton": {
        "family": "dwa_rotating_pointer_window",
        "aliases": ("dem_rotating_window", "cursor_wrap_unit_cells"),
        "concepts": ("sample_event", "rotating_window", "contiguous_window", "wraparound", "active_count_code"),
        "checker": (
            "The active cell window is contiguous modulo the cell count.",
            "The pointer/cursor advances deterministically according to the prior or current active count specified by the prompt.",
            "Exactly the requested number of cell outputs is high in each valid window.",
            "Negative prompts such as not-random and not-scramble must block independent per-cell toggling.",
        ),
        "reject": ("random_scramble", "independent_cell_toggle"),
    },
    "pfd_edge_pulse_window_skeleton": {
        "family": "pfd_updn_reset_race",
        "aliases": ("phase_detector_pulse_relation", "event_order_pulses"),
        "concepts": ("edge_pair", "pulse_window", "mutual_exclusion", "event_order_state"),
        "checker": (
            "REF/early-leading windows produce bounded UP/raise pulses; DIV/late-leading windows produce bounded DN/lower pulses.",
            "The two correction outputs do not overlap unless the public prompt explicitly asks to measure overlap.",
            "Near-simultaneous arrivals clear or suppress pulses according to the reset-delay/window rule.",
            "A not-XOR prompt must block duty-cycle XOR implementations.",
        ),
        "reject": ("xor_detector",),
    },
    "pll_feedback_cadence_skeleton": {
        "family": "pll_feedback_cadence",
        "aliases": ("pll_ratio_lock", "feedback_divider_lock"),
        "concepts": ("edge_pair", "divider_ratio", "feedback_loop", "lock_after_settle", "frequency_control"),
        "checker": (
            "Feedback edge cadence is derived from oscillator/divider state rather than an unrelated timer.",
            "Lock is asserted only after the ref/fb relation settles over the checker window.",
            "Ratio hops or frequency steps temporarily unsettle lock and then reacquire.",
            "Control observables such as vctrl must be connected to cadence or phase error, not cosmetic ramps.",
        ),
        "reject": ("standalone_divider_only",),
    },
    "divider_counter_ratio_skeleton": {
        "family": "divider_counter_ratio",
        "aliases": ("counter_or_divider_sequence", "binary_counter_ratio"),
        "concepts": ("sample_event", "divider_ratio", "edge_counting", "held_state"),
        "checker": (
            "Output events/toggles occur after the requested number of input events.",
            "Odd ratios preserve the expected rising-edge interval while allowing approximate duty balance.",
            "Runtime ratio changes take effect on safe event boundaries.",
            "Binary counter prompts must not be repaired as Gray-code one-bit-change outputs.",
        ),
        "reject": ("gray_code_required",),
    },
    "comparator_threshold_hysteresis_skeleton": {
        "family": "comparator_threshold_hysteresis",
        "aliases": ("threshold_decision", "hysteresis_window"),
        "concepts": ("threshold_decision", "latched_decision", "hysteresis_window"),
        "checker": (
            "Output polarity changes when the public input relation crosses the required threshold.",
            "Hysteresis variants use separate rising/falling thresholds and avoid chatter inside the window.",
            "Delay/strongarm variants preserve reset priority and event timing requirements.",
        ),
        "reject": (),
    },
    "sample_hold_track_latch_skeleton": {
        "family": "sample_hold_discrete_update",
        "aliases": ("sample_hold_track_latch", "latched_level"),
        "concepts": ("sample_event", "held_state", "latched_level", "not_continuous_follower"),
        "checker": (
            "Output copies the input only in the public capture/sample aperture.",
            "Output remains held between capture instants except for explicitly modeled droop.",
            "A not-follower prompt must block continuous buffer behavior.",
            "Aperture/delay tolerance is checked at public observation times.",
        ),
        "reject": ("continuous_follower",),
    },
    "lfsr_prbs_sequence_skeleton": {
        "family": "lfsr_prbs_sequence",
        "aliases": ("lfsr_sequence", "prbs_sequence"),
        "concepts": ("sample_event", "feedback_sequence", "held_state", "bit_sequence"),
        "checker": (
            "State advances only on public clock events.",
            "Feedback taps create the expected nontrivial repeating bit sequence.",
            "Reset/seed handling produces the required initial state without stuck output.",
        ),
        "reject": ("binary_counter_only",),
    },
    "calibration_search_settle_skeleton": {
        "family": "calibration_search_settle",
        "aliases": ("offset_search_settle", "trim_search"),
        "concepts": ("calibration_search", "settled_flag", "bounded_error", "held_state"),
        "checker": (
            "Search/trim code updates according to the observed error metric.",
            "Settled/done asserts only after the required bounded-error or stable-window condition.",
            "Final analog behavior uses the calibrated code/offset, not the uncalibrated raw path.",
        ),
        "reject": ("static_code_only",),
    },
    "serializer_frame_sequence_skeleton": {
        "family": "serializer_frame_sequence",
        "aliases": ("serializer_frame_alignment", "parallel_to_serial"),
        "concepts": ("sample_event", "bit_sequence", "frame_alignment", "held_state"),
        "checker": (
            "Serial output follows the public bit order and frame cadence.",
            "Frame/alignment flags assert on the requested boundaries.",
            "Reset restarts bit index and frame state deterministically.",
        ),
        "reject": (),
    },
}


EXTRA_LEGO_SKILLS = (
    LegoSkill(
        skill_id="transition_glitch_guard",
        title="Bounded Transition/Glitch Guard",
        mechanism_family="transition_glitch_guard",
        source="R26/92PASS ledger: segmented DAC glitch guard and transition-output repairs",
        concepts=("sample_event", "bounded_transition_glitch", "settling_window", "held_state"),
        aliases=("bounded_step_window", "glitch_guard_settle"),
        slot_schema={
            "clock": "Public event after which the transition/glitch window is checked.",
            "analog_output": "Analog value whose transition must settle or remain bounded.",
            "guard_output": "Optional public guard/flag output indicating a valid bounded window.",
            "reference": "Supply/reference pins used for high/low levels.",
        },
        implementation_skeleton=(
            "Keep the main analog value in a held real target updated only at the public event.",
            "Track the previous value and event time so the guard can describe the post-event settling window.",
            "Drive the analog output and guard output with unconditional transition() contributions from held targets.",
            "Use the public prompt/checker window as a bounded-settling constraint; do not create a separate functional code path only for the guard.",
        ),
        code_shape=(
            "real out_target, prev_target, guard_target, last_event_t;",
            "analog begin",
            "  @(initial_step) begin out_target=vlo; prev_target=vlo; guard_target=vlo; last_event_t=0; end",
            "  @(cross(V(clock)-vth,+1)) begin prev_target=out_target; out_target=compute_next_value(); last_event_t=$abstime; guard_target=vhi; end",
            "  V(analog_output) <+ transition(out_target,0,tr,tr);",
            "  V(guard_output) <+ transition(guard_target,0,tr,tr);",
            "end",
        ),
        checker_expectations=(
            "After a public clock/event edge, the analog output reaches the new target within the bounded checker window.",
            "The guard flag is derived from the same held state/timing relation as the analog output.",
            "A segmented or code-driven analog output should not show unrelated intermediate states after the accepted settling time.",
        ),
        spectre_constraints=COMMON_SPECTRE_CONSTRAINTS,
        anti_patterns=(
            "Do not put transition() inside conditional branches.",
            "Do not fake the guard as a constant pass flag if the analog output is not connected to the same state.",
            "Do not use discontinuous ideal assignments for outputs that the checker samples near transitions.",
        ),
    ),
)


CONCEPT_PATTERNS: dict[str, tuple[str, ...]] = {
    "sample_event": (
        r"\bsample(?:d|s|ing)?\b",
        r"\bcapture(?:d|s|_strobe)?\b",
        r"\bstrobe\b",
        r"\bclock\b",
        r"\bcadence\b",
        r"\badvance\b",
        r"\bevent\b",
        r"\binput events?\b",
    ),
    "held_state": (
        r"\bhold\b",
        r"\bheld\b",
        r"\blatched\b",
        r"\bpreserv(?:e|ing|ed)\b",
        r"\bbetween\b.*\b(?:events|strobes|samples|captures)\b",
        r"\bshared\b.*\b(?:state|code)\b",
    ),
    "quantized_code": (
        r"\bquant",
        r"\bcode\b",
        r"\bdecision outputs?\b",
        r"\bdiscrete\b",
        r"\bdec\d+\b",
        r"\bdout_?\d+\b",
    ),
    "reconstruct_from_code": (
        r"\breconstruct",
        r"\bestimate(?:d|_level)?\b",
        r"\bcode[- ]centered\b",
        r"\bfrom that same held code\b",
    ),
    "shared_source_of_truth": (
        r"\bsame held code\b",
        r"\bshared quantized code\b",
        r"\bsingle .*source",
        r"\bone shared\b",
    ),
    "weighted_sum": (
        r"\bweighted sum\b",
        r"\bbinary[- ]weighted\b",
        r"\bplace value\b",
        r"\beach input line has binary\b",
        r"\bMSB\b|\bLSB\b",
    ),
    "code_or_bits": (
        r"\bbits?\b",
        r"\bcode\b",
        r"\bdecision lines?\b",
        r"\bdin\w*\b",
        r"\bqty\d+\b",
    ),
    "decode_to_analog": (
        r"\banalog output\b",
        r"\bdrive[_ ]estimate\b",
        r"\bweighted value\b",
        r"\boutput drive\b",
    ),
    "rotating_window": (
        r"\brotat",
        r"\bcursor\b",
        r"\bpointer\b",
        r"\bcyclic\b",
        r"\bwrap",
    ),
    "contiguous_window": (
        r"\bcontiguous\b",
        r"\bwindow\b",
        r"\bunit[- ]cell\b",
        r"\bactive[- ]cell\b",
        r"\bcell\d+\b",
    ),
    "wraparound": (r"\bwrap", r"\bmodulo\b"),
    "active_count_code": (r"\bactive count\b", r"\bquantity\b", r"\bqty\d+\b", r"\bselected cells?\b"),
    "edge_pair": (
        r"\btwo edge streams?\b",
        r"\bref\b.*\bdiv\b",
        r"\bearly[_ ]event\b.*\blate[_ ]event\b",
        r"\bboth have arrived\b",
        r"\bfeedback\b.*\breference\b",
    ),
    "pulse_window": (r"\bpulse", r"\bcorrection", r"\breset[- ]delay\b", r"\bdeadzone\b"),
    "mutual_exclusion": (r"\bmutually exclusive\b", r"\bnot overlap\b", r"\bno overlap\b"),
    "event_order_state": (r"\bevent[- ]order\b", r"\bleading\b", r"\blead/lag\b", r"\bearly\b.*\blate\b"),
    "divider_ratio": (
        r"\bdivide\b",
        r"\bdivider\b",
        r"\bratio\b",
        r"\bevery[_ -]?(?:fifth|third|fourth|sixth|\d+)\b",
        r"\bfixed number of input events\b",
    ),
    "edge_counting": (r"\bcount(?:er|ing)?\b", r"\bafter .* input events?\b", r"\binput rising edges?\b"),
    "feedback_loop": (r"\bfeedback\b", r"\bfb[_ ]?clk\b", r"\bdivided events?\b"),
    "lock_after_settle": (r"\block\b", r"\bsettle", r"\breacquire\b", r"\bstable window\b"),
    "frequency_control": (r"\bDCO\b", r"\bVCO\b", r"\bvctrl\b", r"\bfrequency\b", r"\bperiod\b"),
    "threshold_decision": (r"\bcomparator\b", r"\bthreshold\b", r"\bvinp\b", r"\bvinn\b", r"\bcross"),
    "latched_decision": (r"\bstrongarm\b", r"\breset priority\b", r"\bdecision\b"),
    "hysteresis_window": (r"\bhysteresis\b", r"\bwindow\b"),
    "latched_level": (r"\belectrical level\b", r"\blatched level\b", r"\bcopying\b.*\blevel\b"),
    "not_continuous_follower": (r"\bnot .*follower\b", r"\bnot .*continuous\b", r"\bonly change\b"),
    "calibration_search": (r"\bcalibration\b", r"\btrim\b", r"\boffset[- ]search\b", r"\bsearch\b"),
    "settled_flag": (r"\bsettled\b", r"\bdone\b", r"\braises settled\b"),
    "bounded_error": (r"\bbounded errors?\b", r"\berror metric\b", r"\bconsecutive\b"),
    "feedback_sequence": (r"\bLFSR\b", r"\bPRBS\b", r"\bfeedback taps?\b"),
    "bit_sequence": (r"\bsequence\b", r"\bbit order\b", r"\bserial\b"),
    "frame_alignment": (r"\bframe\b", r"\balignment\b", r"\bparallel\b.*\bserial\b"),
    "continuous_voltage": (r"\bramp\b", r"\bstep\b", r"\btime\b.*\bvoltage\b"),
    "bounded_transition_glitch": (
        r"\bglitch\b",
        r"\bglitch[_ -]?guard\b",
        r"\bbounded .*transition\b",
        r"\bbounded .*settling\b",
        r"\bsettling .*glitch\b",
    ),
    "settling_window": (
        r"\bsettling\b",
        r"\bsettle\b",
        r"\bafter .*edge\b",
        r"\bpost[- ]?event\b",
        r"\bwithin .*window\b",
    ),
}


NEGATIVE_PATTERNS: dict[str, tuple[str, ...]] = {
    "continuous_follower": (r"\bnot .*continuous\b", r"\bnot .*follower\b", r"\bnot .*track\b"),
    "random_scramble": (r"\bnot random\b", r"\bnot .*scrambl", r"\bdeterministic cyclic\b"),
    "independent_cell_toggle": (r"\bnot .*independent per[- ]cell\b",),
    "xor_detector": (r"\bnot .*xor\b", r"\breject .*xor\b"),
    "gray_code_required": (r"\bgray[- ]code\b", r"\bone[- ]bit[- ]change\b"),
    "binary_counter_only": (r"\bbinary count\b", r"\borderinary binary\b", r"\breject gray\b"),
    "thermometer_required_without_binary": (
        r"\bnot thermometer\b",
        r"\bnot unary\b",
        r"\bdo not .*thermometer\b",
        r"\bdo not .*unit[- ]cell\b",
        r"\bbinary place value\b",
    ),
    "static_code_only": (r"\bnot static\b", r"\bsearch\b", r"\bsettled\b"),
}


SLOT_HINTS: dict[str, tuple[str, ...]] = {
    "clock": ("clk", "clock", "cadence", "strobe", "advance", "sample", "capture", "event"),
    "sample_control": ("clk", "clock", "cadence", "strobe", "capture", "sample", "advance"),
    "reset": ("rst", "reset", "clear", "clear_n", "reset_n"),
    "vin": ("vin", "sense", "measured", "input", "level", "value"),
    "positive_input": ("vinp", "inp", "plus", "sense"),
    "negative_input": ("vinn", "inn", "minus", "ref", "threshold"),
    "code_bits": ("code", "dec", "dout", "bit", "qty", "din", "weight"),
    "code_inputs": ("code", "din", "bit", "weight", "msb", "lsb"),
    "code_outputs": ("code", "dec", "dout", "bit", "weight"),
    "cell_outputs": ("cell", "unit", "active", "window", "sel"),
    "ptr_outputs": ("ptr", "pointer", "cursor"),
    "vout": ("vout", "out", "estimate", "held", "reconstructed", "level", "drive", "analog_sum"),
    "output": ("out", "output", "mark", "y", "q", "analog_sum"),
    "analog_output": ("vout", "out", "analog", "analog_sum", "sum", "drive", "level"),
    "guard_output": ("guard", "glitch", "settled", "valid"),
    "ref_edge": ("ref", "early", "reference"),
    "div_edge": ("div", "late", "fb", "feedback"),
    "up": ("up", "raise", "accelerate"),
    "dn": ("dn", "down", "lower", "retard"),
    "ref_clk": ("ref", "reference"),
    "fb_clk": ("fb", "feedback", "div"),
    "lock": ("lock", "settled"),
    "vctrl": ("vctrl", "control"),
    "ratio": ("ratio", "divide", "every", "count"),
    "parallel_or_data": ("data", "parallel", "word", "byte"),
    "serial_output": ("serial", "tx", "out"),
    "frame": ("frame", "align"),
    "code_or_trim": ("code", "trim", "cal", "offset"),
    "metric": ("metric", "error", "offset", "measure"),
    "settled_or_done": ("settled", "done", "lock"),
    "reference": ("vdd", "vss", "vref", "reference"),
    "vhi_vlo_vth": ("vdd", "vss", "vth", "vh", "vl"),
}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower())


def _extract_backtick_identifiers(text: str) -> list[str]:
    out: list[str] = []
    for match in re.findall(r"`([^`]+)`", text):
        for token in re.split(r"[\s,]+", match):
            token = token.strip()
            if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", token):
                out.append(token)
    return _dedupe(out)


def _extract_interface(prompt: str) -> tuple[list[str], list[str]]:
    inputs: list[str] = []
    outputs: list[str] = []
    for raw in prompt.splitlines():
        line = raw.strip()
        low = line.lower()
        if low.startswith("- inputs:") or low.startswith("inputs:"):
            inputs.extend(_extract_backtick_identifiers(line))
        elif low.startswith("- outputs:") or low.startswith("outputs:"):
            outputs.extend(_extract_backtick_identifiers(line))
    if not inputs and not outputs:
        ids = _extract_backtick_identifiers(prompt)
        # Fall back to all identifiers as ambiguous public names.
        outputs.extend(ids)
    return _dedupe(inputs), _dedupe(outputs)


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _regex_hits(text_l: str, patterns: tuple[str, ...]) -> list[str]:
    return [pattern for pattern in patterns if re.search(pattern, text_l, flags=re.IGNORECASE)]


def extract_functional_ir(prompt: str, *, notes: list[str] | None = None) -> FunctionalIR:
    evidence: dict[str, list[str]] = {}
    combined = "\n".join([prompt, *[str(note) for note in (notes or [])]])
    text_l = _norm(combined)
    concepts: list[str] = []
    for concept, patterns in CONCEPT_PATTERNS.items():
        hits = _regex_hits(text_l, patterns)
        if hits:
            concepts.append(concept)
            evidence[concept] = hits[:4]

    negatives: list[str] = []
    for concept, patterns in NEGATIVE_PATTERNS.items():
        hits = _regex_hits(text_l, patterns)
        if hits:
            negatives.append(concept)
            evidence[f"negative:{concept}"] = hits[:4]

    inputs, outputs = _extract_interface(prompt)
    identifiers = _dedupe([*inputs, *outputs, *_extract_backtick_identifiers(prompt)])
    return FunctionalIR(
        concepts=tuple(_dedupe(concepts)),
        negative_constraints=tuple(_dedupe(negatives)),
        inputs=tuple(inputs),
        outputs=tuple(outputs),
        identifiers=tuple(identifiers),
        evidence=evidence,
    )


def _slot_candidates(slot: str, ir: FunctionalIR) -> list[str]:
    hints = SLOT_HINTS.get(slot, (slot,))
    names: list[str] = []
    pool = list(ir.inputs) + list(ir.outputs) + list(ir.identifiers)
    for name in pool:
        if any(_name_matches_hint(name, hint) for hint in hints):
            names.append(name)
    return _dedupe(names)


def _name_matches_hint(name: str, hint: str) -> bool:
    low = name.lower()
    hint_l = hint.lower()
    if low == hint_l:
        return True
    parts = [part for part in re.split(r"[_\W]+", low) if part]
    if hint_l in parts:
        return True
    if re.match(rf"^{re.escape(hint_l)}\d+$", low):
        return True
    if low.startswith(hint_l + "_") or low.endswith("_" + hint_l):
        return True
    # Long hints such as analog_sum or capture_strobe are safe substring
    # matches. Short hints like rst are not, because they match words such as
    # first/reordered.
    return len(hint_l) >= 4 and hint_l in low


def bind_slots(skill: LegoSkill, ir: FunctionalIR, *, meta: dict[str, Any] | None = None, use_meta_slots: bool = False) -> dict[str, list[str]]:
    bound: dict[str, list[str]] = {}
    if use_meta_slots and meta:
        checker = meta.get("v2_checker_spec", {}) if isinstance(meta.get("v2_checker_spec"), dict) else {}
        for key, value in checker.items():
            if value is None:
                continue
            names = value if isinstance(value, list) else [value]
            for slot in skill.slot_schema:
                if key in slot or slot in key or key in {"vin", "clock", "rst", "vout", "ref", "div", "up", "dn", "lock"}:
                    bound.setdefault(slot, [])
                    bound[slot].extend(str(item) for item in names if isinstance(item, str))
    for slot in skill.slot_schema:
        candidates = _slot_candidates(slot, ir)
        if candidates:
            bound.setdefault(slot, [])
            bound[slot].extend(candidates)
    return {key: _dedupe(value) for key, value in bound.items() if value}


def load_lego_skills(root: Path = ROOT) -> list[LegoSkill]:
    data = _read_json(root / "docs" / "CIRCUIT_MECHANISM_SKELETONS.json")
    out: list[LegoSkill] = []
    for skeleton in data.get("skeletons", []):
        sid = str(skeleton.get("id", ""))
        overlay = SKILL_OVERLAYS.get(sid)
        if not overlay:
            continue
        out.append(
            LegoSkill(
                skill_id=sid.replace("_skeleton", ""),
                title=str(skeleton.get("title", sid)),
                mechanism_family=str(overlay["family"]),
                source=str(skeleton.get("source", "")),
                concepts=tuple(overlay.get("concepts", ())),
                aliases=tuple(overlay.get("aliases", ())),
                reject_concepts=tuple(overlay.get("reject", ())),
                slot_schema=dict(skeleton.get("slot_schema", {})),
                implementation_skeleton=tuple(str(item) for item in skeleton.get("implementation_skeleton", [])),
                code_shape=tuple(str(item) for item in skeleton.get("veriloga_shape", [])),
                checker_expectations=tuple(str(item) for item in overlay.get("checker", ())),
                spectre_constraints=COMMON_SPECTRE_CONSTRAINTS,
                anti_patterns=tuple(str(item) for item in skeleton.get("anti_patterns", [])),
                metadata={"skeleton_id": sid, "match": skeleton.get("match", {})},
            )
        )
    out.extend(EXTRA_LEGO_SKILLS)
    return out


def _score_skill(
    skill: LegoSkill,
    ir: FunctionalIR,
    bound_slots: dict[str, list[str]],
    *,
    meta: dict[str, Any] | None = None,
    use_meta_family: bool = False,
) -> tuple[float, list[str], list[str]]:
    concepts = set(ir.concepts)
    negatives = set(ir.negative_constraints)
    skill_concepts = set(skill.concepts)
    if skill.mechanism_family == "transition_glitch_guard" and "bounded_transition_glitch" not in concepts:
        return -1.0, [], []
    hits = sorted(concepts & skill_concepts)
    rejected = sorted(negatives & set(skill.reject_concepts))
    slot_score = len(bound_slots) / max(len(skill.slot_schema), 1)
    score = 1.8 * len(hits) + 2.0 * slot_score
    if "sample_event" in hits and len(hits) > 1:
        score += 0.5
    if "held_state" in hits and len(hits) > 1:
        score += 0.5
    if skill.mechanism_family == "binary_weighted_dac" and "weighted_sum" in hits:
        score += 2.0
    if skill.mechanism_family == "binary_weighted_dac" and "thermometer_required_without_binary" in negatives:
        score += 1.5
    if skill.mechanism_family == "dwa_rotating_pointer_window" and "thermometer_required_without_binary" in negatives:
        score -= 2.5
    if skill.mechanism_family == "transition_glitch_guard" and "bounded_transition_glitch" in hits:
        score += 2.0
    if skill.mechanism_family == "transition_glitch_guard" and "settling_window" in hits:
        score += 1.0
    if rejected:
        # Most reject concepts are phrased as public negative constraints that
        # protect the skill from common wrong implementations, so a matching
        # reject concept should boost the correct skill rather than block it.
        score += 0.8 * len(rejected)
    if use_meta_family and meta:
        family = str(meta.get("mechanism_family") or meta.get("manifest_entry", {}).get("mechanism_family") or "")
        if family and (family == skill.mechanism_family or family in skill.aliases):
            score += 5.0
    if not hits:
        score -= 1.0
    return score, hits, rejected


def retrieve_lego_skills(
    prompt: str,
    *,
    meta: dict[str, Any] | None = None,
    notes: list[str] | None = None,
    top_k: int = 4,
    use_meta_family: bool = False,
    use_meta_slots: bool = False,
    skills: list[LegoSkill] | None = None,
) -> dict[str, Any]:
    ir = extract_functional_ir(prompt, notes=notes)
    skills = skills or load_lego_skills()
    candidates: list[dict[str, Any]] = []
    for skill in skills:
        bound = bind_slots(skill, ir, meta=meta, use_meta_slots=use_meta_slots)
        score, hits, negative_hits = _score_skill(skill, ir, bound, meta=meta, use_meta_family=use_meta_family)
        if score <= 0:
            continue
        packet = skill.to_prompt_packet(bound_slots=bound, score=score)
        packet["matched_concepts"] = hits
        packet["matched_negative_constraints"] = negative_hits
        packet["slot_coverage"] = round(len(bound) / max(len(skill.slot_schema), 1), 4)
        candidates.append(packet)
    candidates.sort(key=lambda item: (-float(item["score"]), str(item["skill_id"])))
    return {
        "functional_ir": {
            "concepts": list(ir.concepts),
            "negative_constraints": list(ir.negative_constraints),
            "inputs": list(ir.inputs),
            "outputs": list(ir.outputs),
            "identifiers": list(ir.identifiers),
            "evidence": ir.evidence,
        },
        "skills": candidates[:top_k],
    }


def format_lego_skill_prompt(packets: list[dict[str, Any]], *, max_chars_per_skill: int = 1800) -> str:
    if not packets:
        return ""
    lines = [
        "# LEGO-Style Mechanism Skills",
        "",
        "Use these retrieved mechanism skills as typed construction blocks. They are selected from public functional behavior, not from task id. Keep the task prompt, EVAS notes, and public interface authoritative.",
    ]
    for idx, item in enumerate(packets, start=1):
        lines.extend(
            [
                "",
                f"## Skill {idx}: `{item['skill_id']}`",
                f"- Mechanism: `{item['mechanism_family']}`",
                f"- Matched concepts: {', '.join(f'`{c}`' for c in item.get('matched_concepts', [])) or '`none`'}",
                f"- Bound slots: {json.dumps(item.get('bound_slots', {}), ensure_ascii=False)}",
                "- Checker expectations:",
            ]
        )
        lines.extend(f"  - {text}" for text in item.get("checker_expectations", []))
        lines.append("- Implementation skeleton:")
        lines.extend(f"  - {text}" for text in item.get("implementation_skeleton", []))
        if item.get("code_shape"):
            shape = " | ".join(str(part) for part in item["code_shape"])
            if len(shape) > max_chars_per_skill:
                shape = shape[: max_chars_per_skill - 3].rstrip() + "..."
            lines.append(f"- Code shape: {shape}")
        lines.append("- Spectre constraints:")
        lines.extend(f"  - {text}" for text in item.get("spectre_constraints", [])[:6])
        if item.get("anti_patterns"):
            lines.append("- Avoid:")
            lines.extend(f"  - {text}" for text in item["anti_patterns"])
    return "\n".join(lines)


def dump_library(path: Path) -> None:
    skills = load_lego_skills()
    payload = {
        "version": "lego-mechanism-skills-v1",
        "purpose": "Typed mechanism skills distilled from R26/92PASS/gold-derived skeletons for functional RAG retrieval.",
        "skills": [
            {
                "skill_id": skill.skill_id,
                "title": skill.title,
                "mechanism_family": skill.mechanism_family,
                "aliases": list(skill.aliases),
                "concepts": list(skill.concepts),
                "slot_schema": skill.slot_schema,
                "implementation_skeleton": list(skill.implementation_skeleton),
                "code_shape": list(skill.code_shape),
                "checker_expectations": list(skill.checker_expectations),
                "spectre_constraints": list(skill.spectre_constraints),
                "anti_patterns": list(skill.anti_patterns),
                "source": skill.source,
            }
            for skill in skills
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prompt-file", help="route one prompt.md and print retrieved skills")
    ap.add_argument("--meta-file", help="optional public meta.json for slot binding")
    ap.add_argument("--dump-library", help="write materialized skill JSON")
    ap.add_argument("--use-meta-family", action="store_true")
    ap.add_argument("--use-meta-slots", action="store_true")
    ap.add_argument("--top-k", type=int, default=4)
    args = ap.parse_args()

    if args.dump_library:
        dump_library(Path(args.dump_library))
        print(f"[lego] wrote {args.dump_library}")

    if args.prompt_file:
        prompt = Path(args.prompt_file).read_text(encoding="utf-8")
        meta = json.loads(Path(args.meta_file).read_text(encoding="utf-8")) if args.meta_file else None
        result = retrieve_lego_skills(
            prompt,
            meta=meta,
            top_k=args.top_k,
            use_meta_family=args.use_meta_family,
            use_meta_slots=args.use_meta_slots,
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
