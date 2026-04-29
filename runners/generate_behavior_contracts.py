#!/usr/bin/env python3
"""Generate repair-facing behavior contracts from failed benchmark artifacts.

The generator is intentionally conservative.  It instantiates a small library
of reusable smoke-contract templates from public prompt observables, existing
failed-run CSV headers, EVAS notes, and gold harness save names when available.
It does not attempt to reproduce full task checkers or gold behavior.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
from collections import defaultdict
from pathlib import Path

try:
    from infer_prompt_checker_specs import infer_specs as _infer_prompt_checker_specs
except ImportError:  # pragma: no cover - script is normally run from runners/
    _infer_prompt_checker_specs = None

ROOT = Path(__file__).resolve().parents[1]

_BACKTICK_RE = re.compile(r"`([^`]+)`")
_METRIC_TOKEN_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)=([^\s,;]+)")
_STRING_LITERAL_RE = re.compile(r'"([^"]+)"')
_PORT_ROLE_RE = re.compile(r"-\s*`?([A-Za-z_][A-Za-z0-9_]*)`?\s*:\s*(input|output|inout)\s+electrical", re.IGNORECASE)
_BIT_SUFFIX_PATTERNS = (
    re.compile(r"^(.+)_([0-9]+)$"),
    re.compile(r"^([A-Za-z]+)([0-9]+)$"),
)
_REFERENCE_CLOCK_NAMES = {
    "ref",
    "refclk",
    "clkref",
    "referenceclk",
    "referenceclock",
    "refclock",
}
_FEEDBACK_CLOCK_NAMES = {
    "fb",
    "fbclk",
    "clkfb",
    "feedbackclk",
    "feedbackclock",
    "fbclock",
}
_LOCK_NAMES = {"lock", "locked", "lockdet", "lockdetect", "lockdetector"}
_CONTROL_NAMES = {
    "vctrl",
    "vctrlmon",
    "ctrl",
    "ctrlmon",
    "control",
    "controlvoltage",
    "controlcode",
}
_UP_PULSE_NAMES = {"up", "upout", "up_pulse", "uppulse"}
_DOWN_PULSE_NAMES = {"dn", "down", "dnout", "downout", "dn_pulse", "down_pulse", "dnpulse", "downpulse"}


def _semantic_prompt_text(prompt: str) -> str:
    """Return prompt text for mechanism inference without task/module names."""
    kept: list[str] = []
    for line in prompt.splitlines():
        lowered = line.strip().lower()
        if lowered.startswith("# task:"):
            continue
        if "module named" in lowered or "**module name**" in lowered:
            continue
        kept.append(line)
    text = "\n".join(kept)
    text = re.sub(r"`[A-Za-z_][A-Za-z0-9_]*(?:_smoke|_ref|_dut)`", " ", text)
    return text


def _read_semantic_prompt(task_dir: Path) -> str:
    prompt_path = task_dir / "prompt.md"
    if not prompt_path.exists():
        return ""
    return _semantic_prompt_text(prompt_path.read_text(encoding="utf-8", errors="ignore"))


def _differential_repair_family(semantic_lower: str, fallback: str) -> str:
    if "segmented" in semantic_lower:
        return "segmented-dac-differential-weighted-sum"
    if "cdac" in semantic_lower or ("calibration" in semantic_lower and "dac" in semantic_lower):
        return "calibration-code-to-differential-output"
    if "dac" in semantic_lower or "digital-to-analog" in semantic_lower or "digital to analog" in semantic_lower:
        return "dac-differential-output-from-code"
    return fallback


_GENERIC_CONTRACT_FAMILIES = {
    "runtime_or_timeout",
    "unclassified_behavior",
    "behavior_semantic",
    "missing_edges_or_clock_activity",
}
_GENERIC_REPAIR_TEMPLATES = {
    "runtime-interface-minimal-harness",
    "manual-contract-extraction-needed",
    "clock-event-generator-or-reset-release",
}
_PROMPT_TEMPLATE_SEMANTIC_HINTS: dict[str, tuple[str, str]] = {
    "quantized_reconstruction": ("adc_dac_code_or_output_coverage", "clocked-quantizer-code-update"),
    "monotonic_code_vs_input": ("adc_dac_code_or_output_coverage", "clocked-quantizer-code-update"),
    "dac_code_to_output_span": ("adc_dac_code_or_output_coverage", "dac-differential-output-from-code"),
    "thermometer_dac_code_to_output_span": ("adc_dac_code_or_output_coverage", "dwa-pointer-thermometer-mask"),
    "onehot_no_overlap": ("dwa_pointer_window", "dwa-pointer-thermometer-mask"),
    "calibration_settling_code": ("adc_dac_code_or_output_coverage", "calibration-settled-flag-from-stable-cycles"),
    "sar_sequence": ("adc_dac_code_or_output_coverage", "sar-sequence-state-machine"),
    "differential_code_response": ("adc_dac_code_or_output_coverage", "segmented-dac-differential-weighted-sum"),
    "differential_step_response": ("adc_dac_code_or_output_coverage", "differential-output-polarity"),
    "ratio_edge_window": ("pll_clock_ratio_lock", "pll-dco-counter-feedback-loop"),
    "ratio_hop_window": ("pll_clock_ratio_lock", "pll-dco-counter-feedback-loop"),
    "ratio_control_window": ("pll_clock_ratio_lock", "pll-dco-counter-feedback-loop"),
    "lock_after_ratio_stable": ("pll_clock_ratio_lock", "pll-dco-counter-feedback-loop"),
    "control_to_frequency_step": ("pll_clock_ratio_lock", "pll-dco-counter-feedback-loop"),
    "paired_edge_response": ("pulse_or_edge_protocol", "pfd-latched-pulse-delayed-clear"),
    "bbpd_data_clock_lead_lag": ("pulse_or_edge_protocol", "bbpd-data-clock-lead-lag"),
    "pulse_non_overlap": ("pulse_or_edge_protocol", "pfd-latched-pulse-delayed-clear"),
    "pulse_width_window": ("pulse_or_edge_protocol", "pfd-windowed-latched-pulse-symmetry"),
    "counter_cadence": ("counter_cadence_or_timer_grid", "counter-cadence-off-by-one"),
    "timer_future_event_liveness": ("counter_cadence_or_timer_grid", "timer-event-liveness"),
    "absolute_event_window": ("counter_cadence_or_timer_grid", "timer-event-liveness"),
    "bounded_step_window": ("counter_cadence_or_timer_grid", "counter-cadence-off-by-one"),
    "parameterized_event_sequence": ("sequence_frame_or_pulse_generation", "sequence-frame-alignment"),
    "sequence_alignment": ("sequence_frame_or_pulse_generation", "sequence-frame-alignment"),
    "gray_counter_sequence": ("sequence_frame_or_pulse_generation", "gray-counter-one-bit-sequence"),
    "sample_hold_tracking": ("analog_or_logic_window_behavior", "analog-window-or-truth-table-repair"),
    "sample_after_clock": ("analog_or_logic_window_behavior", "analog-window-or-truth-table-repair"),
    "droop_window": ("analog_or_logic_window_behavior", "analog-window-or-truth-table-repair"),
    "logic_truth_table": ("analog_or_logic_window_behavior", "analog-window-or-truth-table-repair"),
    "threshold_crossing": ("analog_or_logic_window_behavior", "analog-window-or-truth-table-repair"),
    "hysteresis_window": ("analog_or_logic_window_behavior", "analog-window-or-truth-table-repair"),
}
_PROMPT_TEMPLATE_PRIORITY = (
    "calibration_settling_code",
    "quantized_reconstruction",
    "sar_sequence",
    "differential_code_response",
    "thermometer_dac_code_to_output_span",
    "onehot_no_overlap",
    "dac_code_to_output_span",
    "monotonic_code_vs_input",
    "ratio_edge_window",
    "ratio_hop_window",
    "ratio_control_window",
    "lock_after_ratio_stable",
    "control_to_frequency_step",
    "paired_edge_response",
    "bbpd_data_clock_lead_lag",
    "pulse_non_overlap",
    "pulse_width_window",
    "counter_cadence",
    "timer_future_event_liveness",
    "absolute_event_window",
    "bounded_step_window",
    "parameterized_event_sequence",
    "sequence_alignment",
    "gray_counter_sequence",
    "sample_hold_tracking",
    "sample_after_clock",
    "droop_window",
    "logic_truth_table",
    "threshold_crossing",
    "hysteresis_window",
)


def _prompt_template_names(prompt_spec: dict | None) -> list[str]:
    if not prompt_spec:
        return []
    names: list[str] = []
    for spec in prompt_spec.get("templates", []):
        if not isinstance(spec, dict):
            continue
        template = str(spec.get("template", ""))
        if template:
            names.append(template)
    return _dedupe(names)


def _semantic_hint_from_prompt_templates(templates: list[str]) -> tuple[str, str]:
    template_set = set(templates)
    for template in _PROMPT_TEMPLATE_PRIORITY:
        if template in template_set:
            return _PROMPT_TEMPLATE_SEMANTIC_HINTS[template]
    for template in templates:
        if template in _PROMPT_TEMPLATE_SEMANTIC_HINTS:
            return _PROMPT_TEMPLATE_SEMANTIC_HINTS[template]
    return "", ""


def _failure_rule_field(failure: dict, field: str, key: str) -> str:
    value = failure.get(field, {})
    if isinstance(value, dict):
        return str(value.get(key, "") or "")
    return ""


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _task_dir(task_id: str) -> Path:
    matches = sorted((ROOT / "tasks").glob(f"*/*/{task_id}"))
    if not matches:
        matches = sorted((ROOT / "tasks").glob(f"**/{task_id}"))
    if not matches:
        raise FileNotFoundError(f"task directory not found for {task_id}")
    return matches[0]


def _csv_header(csv_path: Path) -> list[str]:
    if not csv_path.exists() or csv_path.stat().st_size == 0:
        return []
    with csv_path.open(newline="", encoding="utf-8", errors="ignore") as f:
        try:
            return list(next(csv.reader(f)))
        except StopIteration:
            return []


def _prompt_observables(prompt_path: Path) -> list[str]:
    if not prompt_path.exists():
        return []
    text = prompt_path.read_text(encoding="utf-8", errors="ignore")
    observables: list[str] = []
    lines = text.splitlines()
    for idx, line in enumerate(lines):
        lowered = line.lower()
        starts_column_section = (
            "required public waveform columns" in lowered
            or "waveform csv must expose" in lowered
            or "required `save` signals" in lowered
        )
        inline_csv_requirement = "must appear in the waveform csv" in lowered
        if not starts_column_section and not inline_csv_requirement:
            continue
        if inline_csv_requirement:
            observables.extend(_BACKTICK_RE.findall(line))
        for offset, follow in enumerate(lines[idx + 1 : min(len(lines), idx + 20)], start=1):
            follow_lower = follow.lower().strip()
            if not follow.strip() and offset > 1:
                break
            if (
                follow.startswith("## ")
                or follow_lower.startswith("use plain scalar")
                or follow_lower.startswith("timing/checking-window contract")
                or follow_lower.startswith("minimum simulation goal")
                or follow_lower.startswith("implementation constraints")
                or follow_lower.startswith("ports:")
            ):
                break
            if not (follow.lstrip().startswith("-") or "`" in follow):
                continue
            observables.extend(_BACKTICK_RE.findall(follow))
    return _drop_redundant_bus_aliases(_dedupe(_normalize_signal_list(observables)))


def _prompt_port_roles(prompt_path: Path) -> dict[str, str]:
    if not prompt_path.exists():
        return {}
    text = prompt_path.read_text(encoding="utf-8", errors="ignore")
    roles: dict[str, str] = {}
    for signal, role in _PORT_ROLE_RE.findall(text):
        normalized_role = role.lower()
        if normalized_role == "input":
            roles[signal] = "input_stimulus"
        elif normalized_role == "output":
            roles[signal] = "output"
        else:
            roles[signal] = "inout"
    return roles


def _drop_redundant_bus_aliases(signals: list[str]) -> list[str]:
    """Remove aggregate names such as `dout` when scalar `dout_3` bits exist."""
    result: list[str] = []
    for signal in signals:
        has_scalar_bits = any(
            other != signal and re.fullmatch(rf"{re.escape(signal)}_?\d+", other)
            for other in signals
        )
        if has_scalar_bits:
            continue
        result.append(signal)
    return result


def _gold_save_names(task_dir: Path) -> list[str]:
    names: list[str] = []
    for tb in sorted((task_dir / "gold").glob("*.scs")):
        text = tb.read_text(encoding="utf-8", errors="ignore")
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped.startswith("save "):
                continue
            for token in stripped.split()[1:]:
                token = token.strip()
                if not token or token.startswith("/"):
                    continue
                token = token.split(":")[-1]
                token = token.split(".")[-1]
                if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", token):
                    names.append(token)
    return _dedupe(names)


def _checker_name_for_task(task_id: str) -> str | None:
    sim_path = ROOT / "runners" / "simulate_evas.py"
    if not sim_path.exists():
        return None
    src = sim_path.read_text(encoding="utf-8", errors="ignore")
    match = re.search(rf'"{re.escape(task_id)}"\s*:\s*(check_\w+)', src)
    return match.group(1) if match else None


def _checker_function_body(checker_name: str) -> str:
    sim_path = ROOT / "runners" / "simulate_evas.py"
    src = sim_path.read_text(encoding="utf-8", errors="ignore")
    start = re.search(rf"^def {re.escape(checker_name)}\s*\(", src, flags=re.MULTILINE)
    if not start:
        return ""
    next_def = re.search(r"^def \w+\s*\(", src[start.end() :], flags=re.MULTILINE)
    end = start.end() + next_def.start() if next_def else len(src)
    return src[start.start() : end]


def _checker_required_columns(task_id: str) -> list[str]:
    """Best-effort extraction of public checker columns.

    This intentionally extracts only column names, not numeric windows or gold
    behavior. Some checkers accept alternate column sets; in those cases prefer
    the column set used by the benchmark smoke harness when known.
    """
    streaming_aliases = {
        # The streaming fast checker accepts either a/y or not_a/not_y. The
        # bundled smoke harness and successful high-confidence repair use the
        # prefixed NOT-gate names, so make those the hard observability anchor.
        "digital_basics_smoke": ["not_a", "not_y"],
        "digital_basics": ["not_a", "not_y"],
    }
    if task_id in streaming_aliases:
        return streaming_aliases[task_id]

    checker_name = _checker_name_for_task(task_id)
    if not checker_name:
        return []
    body = _checker_function_body(checker_name)
    if not body:
        return []

    candidates: list[list[str]] = []
    for payload in re.findall(r"required\s*=\s*\{([^}]+)\}", body):
        candidates.append(_STRING_LITERAL_RE.findall(payload))
    for payload in re.findall(r"\{([^}]+)\}\.issubset\((?:rows\[0\]|fields|keys|keymap)\)", body):
        candidates.append(_STRING_LITERAL_RE.findall(payload))

    for candidate in candidates:
        normalized = _drop_redundant_bus_aliases(_dedupe(_normalize_signal_list(candidate)))
        if normalized:
            return normalized
    return []


def _normalize_signal_list(signals: list[str]) -> list[str]:
    normalized: list[str] = []
    for signal in signals:
        item = signal.strip().strip(",.")
        if not item:
            continue
        if "[" in item or "]" in item:
            continue
        if " " in item:
            continue
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", item):
            continue
        normalized.append(item)
    return normalized


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def _compact_signal_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


def _semantic_roles(signals: list[str]) -> dict[str, list[str]]:
    roles: dict[str, list[str]] = defaultdict(list)
    for signal in signals:
        compact = _compact_signal_name(signal)
        lower = signal.lower()
        if compact in _REFERENCE_CLOCK_NAMES or (
            ("ref" in compact or "reference" in compact) and ("clk" in compact or "clock" in compact)
        ):
            roles["reference_clock"].append(signal)
        if compact in _FEEDBACK_CLOCK_NAMES or (
            ("fb" in compact or "feedback" in compact) and ("clk" in compact or "clock" in compact)
        ):
            roles["feedback_clock"].append(signal)
        if compact in _LOCK_NAMES:
            roles["lock"].append(signal)
        if compact in _CONTROL_NAMES or compact.startswith("vctrl") or "controlvoltage" in compact:
            roles["control"].append(signal)
        if compact in _UP_PULSE_NAMES:
            roles["up_pulse"].append(signal)
        if compact in _DOWN_PULSE_NAMES:
            roles["down_pulse"].append(signal)
    return {role: _dedupe(items) for role, items in roles.items()}


def _metric_tokens(notes: list[str]) -> dict[str, str]:
    metrics: dict[str, str] = {}
    for note in notes:
        for key, value in _METRIC_TOKEN_RE.findall(str(note)):
            metrics[key] = value
    return metrics


def _is_clock_like(name: str, family: str) -> bool:
    lower = name.lower()
    compact = _compact_signal_name(name)
    if lower == "time":
        return False
    if compact in _REFERENCE_CLOCK_NAMES or compact in _FEEDBACK_CLOCK_NAMES:
        return True
    if "clk" in lower or "clock" in lower:
        return True
    if family in {"pll_or_ratio_tracking", "missing_edges_or_clock_activity", "runtime_or_timeout"}:
        if lower in {"ref", "div", "ref_clk", "fb_clk", "dco_clk", "clk_in", "div_out", "data"}:
            return True
    return False


def _is_reset_like(name: str) -> bool:
    lower = name.lower()
    return "rst" in lower or "reset" in lower


def _is_analog_output_like(name: str) -> bool:
    lower = name.lower()
    compact = _compact_signal_name(name)
    if lower == "time" or _is_reset_like(name):
        return False
    if compact in _CONTROL_NAMES:
        return True
    return any(
        token in lower
        for token in (
            "vout",
            "aout",
            "vdac",
            "vamp",
            "vctrl",
            "metric",
            "lock",
            "out",
            "up",
            "dn",
            "down",
            "flag",
            "sout",
        )
    )


def _differential_output_pairs(fields: list[str]) -> dict[str, list[str]]:
    lower_to_signal = {signal.lower(): signal for signal in fields}
    pairs: dict[str, list[str]] = {}
    for signal in fields:
        lower = signal.lower()
        if lower.endswith("_p"):
            base = lower[:-2]
            mate = lower_to_signal.get(base + "_n")
            if mate:
                pairs[base] = [signal, mate]
        if lower.endswith("_n"):
            base = lower[:-2]
            mate = lower_to_signal.get(base + "_p")
            if mate:
                pairs.setdefault(base, [mate, signal])
    return pairs


def _signal_alias(name: str, fields: list[str]) -> str | None:
    if name in fields:
        return name
    candidates = [name, f"{name}_clk", f"{name}_out"]
    for candidate in candidates:
        if candidate in fields:
            return candidate
    for field in fields:
        if field.lower() == name.lower():
            return field
    for field in fields:
        lower = field.lower()
        if lower.startswith(name.lower()) or name.lower() in lower:
            return field
    return None


def _bit_groups(fields: list[str]) -> dict[str, list[str]]:
    groups: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for signal in fields:
        if signal.lower() == "time":
            continue
        for pattern in _BIT_SUFFIX_PATTERNS:
            match = pattern.match(signal)
            if not match:
                continue
            prefix, idx_s = match.group(1), match.group(2)
            if prefix.lower() in {"v", "vin", "vout"}:
                continue
            groups[prefix].append((int(idx_s), signal))
            break
    return {
        prefix: [name for _, name in sorted(items, reverse=True)]
        for prefix, items in groups.items()
        if len(items) >= 2
    }


def _contract(
    *,
    name: str,
    ctype: str,
    diagnostic_hint: str,
    repair_family: str,
    severity: str = "hard",
    **kwargs,
) -> dict:
    payload = {
        "name": name,
        "type": ctype,
        "severity": "advisory" if severity == "advisory" else "hard",
        "diagnostic_hint": diagnostic_hint,
        "repair_family": repair_family,
    }
    payload.update(kwargs)
    return payload


def _add_unique(contracts: list[dict], contract: dict) -> None:
    key = contract["name"]
    if any(existing.get("name") == key for existing in contracts):
        return
    contracts.append(contract)


def _base_signals(task_dir: Path, header: list[str], task_id: str) -> tuple[list[str], str]:
    checker_signals = _checker_required_columns(task_id)
    if checker_signals:
        return _dedupe(["time", *checker_signals]), "checker_required"

    gold_signals = _gold_save_names(task_dir)
    if gold_signals:
        return _dedupe(["time", *gold_signals]), "gold_save"

    prompt_signals = _prompt_observables(task_dir / "prompt.md")
    if prompt_signals:
        return _dedupe(["time", *prompt_signals]), "prompt_public_contract"
    return header, "csv_header"


def _is_stimulus_bit_group(prefix: str) -> bool:
    lower = prefix.lower()
    return lower.startswith("din") or lower.startswith("vin") or lower.startswith("input")


def _load_prompt_spec_policy(path: Path | None) -> dict[str, object]:
    policy: dict[str, object] = {
        "enabled": False,
        "path": str(path) if path else "",
        "catalog_specs": 0,
        "approved_templates": [],
        "adopt_threshold": 0.70,
        "mode": "disabled",
    }
    if path is None or not path.exists():
        return policy
    data = _read_json(path)
    specs = data.get("specs", [])
    approved_templates: set[str] = set()
    for item in specs:
        for template_spec in item.get("templates", []):
            if not isinstance(template_spec, dict):
                continue
            template = template_spec.get("template")
            if template:
                approved_templates.add(str(template))
    threshold = data.get("adopt_threshold", data.get("summary", {}).get("adopt_threshold", 0.70))
    policy.update(
        {
            "enabled": True,
            "catalog_specs": len(specs),
            "approved_templates": sorted(approved_templates),
            "adopt_threshold": float(threshold),
            "mode": "live_prompt_inference_with_adopted_template_catalog",
        }
    )
    return policy


def _infer_prompt_spec_from_prompt(task_id: str, task_dir: Path, policy: dict[str, object]) -> dict | None:
    if not policy.get("enabled") or _infer_prompt_checker_specs is None:
        return None
    record = _infer_prompt_checker_specs(task_id, task_dir)
    threshold = float(policy.get("adopt_threshold", 0.70))
    approved_templates = set(policy.get("approved_templates", []))
    filtered_templates: list[dict] = []
    for template_spec in record.get("templates", []):
        template = str(template_spec.get("template", ""))
        if not template:
            continue
        try:
            confidence = float(template_spec.get("confidence", 0.0))
        except (TypeError, ValueError):
            confidence = 0.0
        if confidence < threshold:
            continue
        if approved_templates and template not in approved_templates:
            continue
        filtered_templates.append(template_spec)
    functional_claims = [
        str(item.get("type", ""))
        for item in (record.get("functional_ir", {}) or {}).get("claims", [])
        if item.get("type")
    ]
    if not filtered_templates and not functional_claims:
        return None
    inferred = dict(record)
    inferred["templates"] = filtered_templates
    inferred["source"] = "live_prompt_inference"
    inferred["policy"] = {
        "mode": policy.get("mode", ""),
        "catalog_specs": policy.get("catalog_specs", 0),
        "adopt_threshold": threshold,
    }
    return inferred


def _resolve_prompt_signal(value: object, fields: list[str]) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    return _signal_alias(value, fields)


def _resolve_prompt_bits(value: object, fields: list[str]) -> list[str]:
    if not isinstance(value, list):
        return []
    bits: list[str] = []
    for item in value:
        resolved = _resolve_prompt_signal(item, fields)
        if resolved:
            bits.append(resolved)
    return _dedupe(bits)


def _first_resolved(items: object, fields: list[str]) -> str | None:
    if isinstance(items, list):
        for item in items:
            resolved = _resolve_prompt_signal(item, fields)
            if resolved:
                return resolved
    return _resolve_prompt_signal(items, fields)


def _add_prompt_spec_contracts(
    contracts: list[dict],
    *,
    task_id: str,
    prompt_spec: dict | None,
    fields: list[str],
    default_repair_family: str,
) -> list[str]:
    if not prompt_spec:
        return []

    applied_templates: list[str] = []

    def add_from_template(template: str, contract: dict) -> None:
        _add_unique(contracts, contract)
        if template not in applied_templates:
            applied_templates.append(template)

    for spec in prompt_spec.get("templates", []):
        template = str(spec.get("template", ""))
        signals = spec.get("signals", {}) if isinstance(spec.get("signals"), dict) else {}
        params = spec.get("parameters", {}) if isinstance(spec.get("parameters"), dict) else {}
        repair_family = f"prompt-spec:{template}" if template else default_repair_family

        if template in {"quantized_reconstruction", "monotonic_code_vs_input"}:
            bits = _resolve_prompt_bits(signals.get("bits"), fields)
            input_signal = _resolve_prompt_signal(signals.get("input"), fields)
            output_signal = _resolve_prompt_signal(signals.get("output"), fields)
            min_unique = int(params.get("min_unique_codes", 4))
            if bits:
                add_from_template(
                    template,
                    _contract(
                        name=f"prompt_{template}_code_coverage",
                        ctype="code_coverage",
                        bits=bits,
                        threshold=0.45,
                        min_unique=max(2, min_unique),
                        diagnostic_hint="Prompt-inferred ADC/code mechanism requires observable code coverage.",
                        repair_family=repair_family,
                        severity="hard" if template == "quantized_reconstruction" else "advisory",
                    ),
                )
            if output_signal and template == "quantized_reconstruction":
                add_from_template(
                    template,
                    _contract(
                        name="prompt_quantized_reconstruction_output_span",
                        ctype="output_span",
                        signal=output_signal,
                        min_span=float(params.get("min_output_span", 0.1)),
                        diagnostic_hint="Prompt-inferred ADC-DAC reconstruction requires the analog output to move with the code.",
                        repair_family=repair_family,
                        severity="hard",
                    ),
                )
            if input_signal:
                add_from_template(
                    template,
                    _contract(
                        name=f"prompt_{template}_input_span",
                        ctype="input_span",
                        signal=input_signal,
                        min_span=0.05,
                        diagnostic_hint="Prompt-inferred conversion mechanism assumes the public input stimulus remains active.",
                        repair_family=repair_family,
                        severity="advisory",
                    ),
                )

        elif template in {"dac_code_to_output_span", "thermometer_dac_code_to_output_span", "sample_hold_tracking", "droop_window"}:
            bits = _resolve_prompt_bits(signals.get("bits"), fields)
            output_signal = _resolve_prompt_signal(signals.get("output"), fields)
            input_signal = _resolve_prompt_signal(signals.get("input"), fields)
            if bits:
                add_from_template(
                    template,
                    _contract(
                        name=f"prompt_{template}_code_coverage",
                        ctype="code_coverage",
                        bits=bits,
                        threshold=0.45,
                        min_unique=4,
                        diagnostic_hint="Prompt-inferred code-driven analog behavior should exercise multiple code states.",
                        repair_family=repair_family,
                        severity="advisory",
                    ),
                )
            if output_signal:
                add_from_template(
                    template,
                    _contract(
                        name=f"prompt_{template}_output_span",
                        ctype="output_span",
                        signal=output_signal,
                        min_span=0.05 if template == "droop_window" else 0.1,
                        diagnostic_hint="Prompt-inferred analog output should show the requested behavior rather than remain stuck.",
                        repair_family=repair_family,
                        severity="hard" if template in {"dac_code_to_output_span", "thermometer_dac_code_to_output_span"} else "advisory",
                    ),
                )
            if input_signal:
                add_from_template(
                    template,
                    _contract(
                        name=f"prompt_{template}_input_span",
                        ctype="input_span",
                        signal=input_signal,
                        min_span=0.05,
                        diagnostic_hint="Prompt-inferred sampled/tracking behavior needs active input stimulus.",
                        repair_family=repair_family,
                        severity="advisory",
                    ),
                )

        elif template == "onehot_no_overlap":
            pointer_bits = _resolve_prompt_bits(signals.get("pointer_bits"), fields)
            cell_bits = _resolve_prompt_bits(signals.get("cell_bits"), fields)
            code_bits = _resolve_prompt_bits(signals.get("code_bits"), fields)
            if pointer_bits:
                add_from_template(
                    template,
                    _contract(
                        name="prompt_onehot_no_overlap_pointer_active",
                        ctype="active_count_range",
                        bits=pointer_bits,
                        threshold=0.45,
                        min_active=1,
                        max_active=1,
                        diagnostic_hint="Prompt-inferred DWA pointer should be one-hot on sampled post-reset cycles.",
                        repair_family=repair_family,
                        severity="hard",
                    ),
                )
            if cell_bits:
                add_from_template(
                    template,
                    _contract(
                        name="prompt_onehot_no_overlap_cell_enable_active",
                        ctype="active_count_range",
                        bits=cell_bits,
                        threshold=0.45,
                        min_active=1,
                        diagnostic_hint="Prompt-inferred DWA cell-enable window should assert a nonzero selected-cell set.",
                        repair_family=repair_family,
                        severity="hard",
                    ),
                )
            if code_bits:
                add_from_template(
                    template,
                    _contract(
                        name="prompt_onehot_no_overlap_code_coverage",
                        ctype="code_coverage",
                        bits=code_bits,
                        threshold=0.45,
                        min_unique=2,
                        diagnostic_hint="Prompt-inferred DWA test should exercise multiple requested selection sizes.",
                        repair_family=repair_family,
                        severity="advisory",
                    ),
                )

        elif template in {"counter_cadence", "control_to_frequency_step"}:
            input_clock = _resolve_prompt_signal(signals.get("input_clock"), fields)
            output_signal = _resolve_prompt_signal(signals.get("output"), fields)
            if input_clock:
                add_from_template(
                    template,
                    _contract(
                        name=f"prompt_{template}_{input_clock}_edges",
                        ctype="edge_count",
                        signal=input_clock,
                        threshold=0.45,
                        min_edges=4,
                        diagnostic_hint="Prompt-inferred cadence mechanism requires an active input/control clock.",
                        repair_family=repair_family,
                        severity="advisory",
                    ),
                )
            if output_signal:
                add_from_template(
                    template,
                    _contract(
                        name=f"prompt_{template}_{output_signal}_edges",
                        ctype="edge_count",
                        signal=output_signal,
                        threshold=0.45,
                        min_edges=2,
                        diagnostic_hint="Prompt-inferred cadence/frequency mechanism requires output events.",
                        repair_family=repair_family,
                        severity="hard",
                    ),
                )

        elif template == "gray_counter_sequence":
            bits = _resolve_prompt_bits(signals.get("bits"), fields)
            if bits:
                add_from_template(
                    template,
                    _contract(
                        name="prompt_gray_counter_code_coverage",
                        ctype="code_coverage",
                        bits=bits,
                        threshold=0.45,
                        min_unique=min(4, 2 ** min(len(bits), 8)),
                        diagnostic_hint="Prompt-inferred Gray counter should cover multiple observable states after reset release.",
                        repair_family=repair_family,
                        severity="advisory",
                    ),
                )
                add_from_template(
                    template,
                    _contract(
                        name="prompt_gray_counter_one_bit_transitions",
                        ctype="code_hamming_distance",
                        bits=bits,
                        threshold=0.45,
                        max_hamming=1,
                        min_transitions=4,
                        diagnostic_hint="Prompt-inferred Gray counter should flip only one output bit between adjacent states.",
                        repair_family=repair_family,
                        severity="hard",
                    ),
                )

        elif template in {"ratio_edge_window", "ratio_hop_window"}:
            reference = _resolve_prompt_signal(signals.get("reference"), fields)
            feedback = _resolve_prompt_signal(signals.get("feedback"), fields)
            if reference and feedback:
                add_from_template(
                    template,
                    _contract(
                        name=f"prompt_{template}_{reference}_{feedback}_ratio",
                        ctype="frequency_ratio",
                        reference=reference,
                        feedback=feedback,
                        threshold=0.45,
                        min_edges=4,
                        expected_ratio=float(params.get("expected_ratio", 1.0)),
                        tolerance=0.05,
                        diagnostic_hint="Prompt-inferred ratio mechanism requires feedback/reference edge rates to align in the relevant window.",
                        repair_family=repair_family,
                        severity="hard" if template == "ratio_edge_window" else "advisory",
                    ),
                )

        elif template == "lock_after_ratio_stable":
            lock = _resolve_prompt_signal(signals.get("lock"), fields)
            if lock:
                add_from_template(
                    template,
                    _contract(
                        name=f"prompt_{template}_{lock}_asserts",
                        ctype="high_fraction",
                        signal=lock,
                        threshold=0.45,
                        min_fraction=0.05,
                        diagnostic_hint="Prompt-inferred lock mechanism requires the lock indicator to assert after convergence.",
                        repair_family=repair_family,
                        severity="advisory",
                    ),
                )

        elif template in {"paired_edge_response", "bbpd_data_clock_lead_lag", "pulse_non_overlap", "pulse_width_window"}:
            reference = _resolve_prompt_signal(signals.get("reference"), fields)
            feedback = _resolve_prompt_signal(signals.get("feedback"), fields)
            up = _resolve_prompt_signal(signals.get("up"), fields)
            down = _resolve_prompt_signal(signals.get("down"), fields)
            if up and down and template == "pulse_non_overlap":
                add_from_template(
                    template,
                    _contract(
                        name="prompt_pulse_non_overlap",
                        ctype="non_overlap",
                        signals=[up, down],
                        threshold=0.45,
                        max_overlap_fraction=0.02,
                        diagnostic_hint="Prompt-inferred pulse mechanism requires UP/DN-like outputs not to overlap.",
                        repair_family=repair_family,
                        severity="hard",
                    ),
                )
            if reference and feedback and up and down and template in {"paired_edge_response", "bbpd_data_clock_lead_lag"}:
                add_from_template(
                    template,
                    _contract(
                        name="prompt_bbpd_data_clock_lead_lag" if template == "bbpd_data_clock_lead_lag" else "prompt_paired_edge_response",
                        ctype="paired_edge_response",
                        reference=reference,
                        feedback=feedback,
                        up=up,
                        down=down,
                        threshold=0.45,
                        min_total_pairs=4,
                        min_response_fraction=0.5,
                        max_wrong_responses=1,
                        max_pair_gap_s=2e-9,
                        response_tail_s=2e-9,
                        diagnostic_hint=(
                            "Prompt-inferred BBPD mechanism should emit UP/DN according to data/clock lead-lag."
                            if template == "bbpd_data_clock_lead_lag"
                            else "Prompt-inferred paired edge mechanism should respond on the side indicated by the leading edge."
                        ),
                        repair_family=repair_family,
                        severity="advisory",
                    ),
                )

        elif template == "timer_future_event_liveness":
            raw_outputs = signals.get("outputs")
            resolved_outputs = []
            if isinstance(raw_outputs, list):
                for item in raw_outputs:
                    resolved = _resolve_prompt_signal(item, fields)
                    if resolved and not resolved.lower().startswith("ref"):
                        resolved_outputs.append(resolved)
            resolved_outputs = _dedupe(resolved_outputs)
            for output_signal in resolved_outputs[:4]:
                add_from_template(
                    template,
                    _contract(
                        name=f"prompt_{template}_{output_signal}_edges",
                        ctype="edge_count",
                        signal=output_signal,
                        threshold=0.45,
                        min_edges=2,
                        diagnostic_hint="Prompt-inferred timer mechanism requires generated output events, not just a live reference input.",
                        repair_family=repair_family,
                        severity="hard",
                    ),
                )

        elif template in {"absolute_event_window", "bounded_step_window", "parameterized_event_sequence", "sequence_alignment", "logic_truth_table", "threshold_crossing", "hysteresis_window"}:
            outputs = signals.get("outputs")
            output_signal = _first_resolved(outputs, fields) or _resolve_prompt_signal(signals.get("output"), fields)
            if template == "absolute_event_window":
                output_signal = output_signal or _resolve_prompt_signal(signals.get("signal"), fields)
            if output_signal:
                ctype = "edge_count" if any(token in output_signal.lower() for token in ("clk", "clock", "out")) and template in {"absolute_event_window", "timer_future_event_liveness", "sequence_alignment"} else "output_span"
                kwargs = (
                    {"signal": output_signal, "threshold": 0.45, "min_edges": 2}
                    if ctype == "edge_count"
                    else {"signal": output_signal, "min_span": 0.05}
                )
                add_from_template(
                    template,
                    _contract(
                        name=f"prompt_{template}_{output_signal}_{ctype}",
                        ctype=ctype,
                        diagnostic_hint="Prompt-inferred mechanism requires the public output to show observable behavior.",
                        repair_family=repair_family,
                        severity="advisory",
                        **kwargs,
                    ),
                )

        elif template in {"differential_code_response", "differential_step_response"}:
            positive = _resolve_prompt_signal(signals.get("positive"), fields)
            negative = _resolve_prompt_signal(signals.get("negative"), fields)
            if positive and negative:
                add_from_template(
                    template,
                    _contract(
                        name=f"prompt_{template}_differential_range",
                        ctype="differential_range",
                        positive=positive,
                        negative=negative,
                        min_diff_span=0.05,
                        diagnostic_hint="Prompt-inferred differential mechanism requires meaningful differential movement.",
                        repair_family=repair_family,
                        severity="hard",
                    ),
                )

        elif template in {"calibration_settling_code", "sar_sequence"}:
            clock = _resolve_prompt_signal(signals.get("clock"), fields)
            flag = (
                _resolve_prompt_signal(signals.get("settled"), fields)
                or _resolve_prompt_signal(signals.get("ready"), fields)
                or _resolve_prompt_signal(signals.get("eoc"), fields)
            )
            bits = _resolve_prompt_bits(signals.get("trim_bits") or signals.get("bits"), fields)
            if bits:
                add_from_template(
                    template,
                    _contract(
                        name=f"prompt_{template}_code_coverage",
                        ctype="code_coverage",
                        bits=bits,
                        threshold=0.45,
                        min_unique=2,
                        diagnostic_hint="Prompt-inferred sequencing/calibration mechanism should exercise multiple code states.",
                        repair_family=repair_family,
                        severity="advisory",
                    ),
                )
            if clock and flag and bits and template == "calibration_settling_code":
                add_from_template(
                    template,
                    _contract(
                        name="prompt_calibration_settled_after_stable",
                        ctype="settled_flag_after_stable_cycles",
                        clock=clock,
                        flag=flag,
                        state_bits=bits,
                        threshold=0.45,
                        min_stable_cycles=int(params.get("settled_cycles", 8)),
                        diagnostic_hint="Prompt-inferred calibration mechanism requires SETTLED after stable trim/code cycles.",
                        repair_family=repair_family,
                        severity="hard",
                    ),
                )
            elif flag:
                add_from_template(
                    template,
                    _contract(
                        name=f"prompt_{template}_{flag}_asserts",
                        ctype="high_fraction",
                        signal=flag,
                        threshold=0.45,
                        min_fraction=0.02,
                        diagnostic_hint="Prompt-inferred sequence completion flag should assert during the run.",
                        repair_family=repair_family,
                        severity="advisory",
                    ),
                )

    return applied_templates


def generate_contract_spec(
    failure: dict,
    *,
    result_root: Path | None = None,
    prompt_spec: dict | None = None,
    prompt_spec_policy: dict[str, object] | None = None,
) -> dict:
    task_id = failure["task_id"]
    raw_family = str(failure.get("contract_family", "runtime_or_timeout"))
    raw_repair_family = str(failure.get("repair_template", "runtime-interface-minimal-harness"))
    family = raw_family
    repair_family = raw_repair_family
    task_dir = _task_dir(task_id)
    semantic_lower = _read_semantic_prompt(task_dir).lower()
    has_pll = (
        "pll" in semantic_lower
        or "phase-locked loop" in semantic_lower
        or "phase locked loop" in semantic_lower
    )
    has_pfd = "pfd" in semantic_lower or "phase frequency detector" in semantic_lower
    has_bbpd = "bbpd" in semantic_lower or "bang-bang phase detector" in semantic_lower
    has_adc = (
        "adc" in semantic_lower
        or "analog-to-digital" in semantic_lower
        or "analog to digital" in semantic_lower
    )
    has_gray = "gray" in semantic_lower
    has_deadzone = "deadzone" in semantic_lower or "dead zone" in semantic_lower
    has_reset_race = "reset race" in semantic_lower or ("reset" in semantic_lower and "race" in semantic_lower)
    result_path = Path(failure.get("result_path", ""))
    if result_root is not None:
        result_path = result_root / task_id / "result.json"
    csv_path = result_path.parent / "tran.csv" if result_path else Path()
    header = _csv_header(csv_path)
    public_signals, public_signal_source = _base_signals(task_dir, header, task_id)
    fields = _dedupe([*(header or []), *public_signals]) or public_signals
    prompt_roles = _prompt_port_roles(task_dir / "prompt.md")
    public_prompt_roles = {
        signal: role
        for signal, role in prompt_roles.items()
        if signal in fields and role in {"input_stimulus", "output"}
    }
    if prompt_spec is None and prompt_spec_policy is not None:
        prompt_spec = _infer_prompt_spec_from_prompt(task_id, task_dir, prompt_spec_policy)
    prompt_templates = _prompt_template_names(prompt_spec)
    prompt_semantic_family, prompt_semantic_repair_template = _semantic_hint_from_prompt_templates(prompt_templates)
    triage_semantic_family = _failure_rule_field(failure, "semantic_family", "family")
    triage_semantic_repair_template = _failure_rule_field(failure, "semantic_family", "repair_template")
    triage_semantic_summary = _failure_rule_field(failure, "semantic_family", "summary")
    blocking_family = _failure_rule_field(failure, "blocking_family", "family") or raw_family
    blocking_repair_template = _failure_rule_field(failure, "blocking_family", "repair_template") or raw_repair_family
    semantic_family = (
        triage_semantic_family
        if triage_semantic_family and triage_semantic_family not in _GENERIC_CONTRACT_FAMILIES
        else prompt_semantic_family or triage_semantic_family
    )
    semantic_repair_template = (
        triage_semantic_repair_template
        if triage_semantic_repair_template and triage_semantic_repair_template not in _GENERIC_REPAIR_TEMPLATES
        else prompt_semantic_repair_template or triage_semantic_repair_template
    )
    calibration_source = "triage_primary"
    if family in _GENERIC_CONTRACT_FAMILIES and semantic_family:
        family = semantic_family
        calibration_source = "triage_semantic_layer" if triage_semantic_family else "prompt_semantic_templates"
    if repair_family in _GENERIC_REPAIR_TEMPLATES and semantic_repair_template:
        repair_family = semantic_repair_template
    stimulus_signals = {
        signal for signal, role in public_prompt_roles.items() if role == "input_stimulus"
    }
    metrics = _metric_tokens(failure.get("notes", []))
    groups = _bit_groups(fields)
    grouped_bits = {bit for bits in groups.values() for bit in bits}
    differential_pairs = _differential_output_pairs(fields)
    differential_members = {signal for pair in differential_pairs.values() for signal in pair}
    roles = _semantic_roles(fields)

    contracts: list[dict] = []
    if public_signals:
        _add_unique(
            contracts,
            _contract(
                name="csv_has_observables",
                ctype="signal_present",
                signals=public_signals,
                diagnostic_hint="Checker-visible waveform columns must be present; preserve these saved observables.",
                repair_family="runtime-interface-minimal-harness",
                severity="hard",
            ),
        )

    if public_prompt_roles:
        _add_unique(
            contracts,
            _contract(
                name="public_signal_roles",
                ctype="signal_role_integrity",
                roles=public_prompt_roles,
                constant_input_ok=True,
                diagnostic_hint="Public prompt roles identify stimulus inputs versus DUT outputs; do not repair constant inputs as if they were stuck outputs.",
                repair_family="runtime-interface-minimal-harness",
                severity="advisory",
            ),
        )

    clock_signals = [signal for signal in fields if _is_clock_like(signal, family)]
    for signal in clock_signals[:4]:
        _add_unique(
            contracts,
            _contract(
                name=f"{signal}_edges_present",
                ctype="edge_count",
                signal=signal,
                threshold=0.45,
                min_edges=10 if has_pll or "clk" in signal.lower() else 4,
                diagnostic_hint=f"`{signal}` should show enough post-startup transitions.",
                repair_family="clock-event-generator-or-reset-release",
            ),
        )

    reference_clock = (roles.get("reference_clock") or [None])[0]
    feedback_clock = (roles.get("feedback_clock") or [None])[0]
    if reference_clock and feedback_clock:
        _add_unique(
            contracts,
            _contract(
                name=f"{reference_clock}_{feedback_clock}_frequency_ratio_near_one",
                ctype="frequency_ratio",
                reference=reference_clock,
                feedback=feedback_clock,
                threshold=0.45,
                min_edges=4,
                expected_ratio=1.0,
                tolerance=0.05,
                diagnostic_hint="Feedback clock edge rate should track the reference clock in the checking window.",
                repair_family="pll-dco-counter-feedback-loop",
            ),
        )

    if "clk_in" in fields and "div_out" in fields:
        _add_unique(
            contracts,
            _contract(
                name="divider_output_edges_present",
                ctype="edge_count",
                signal="div_out",
                threshold=0.45,
                min_edges=4,
                diagnostic_hint="Divider output should toggle under the input clock.",
                repair_family="clock-event-generator-or-reset-release",
            ),
        )

    lock_signal = (roles.get("lock") or ([] if "lock" not in fields else ["lock"]) or [None])[0]
    if lock_signal:
        _add_unique(
            contracts,
            _contract(
                name=f"{lock_signal}_asserts_somewhere",
                ctype="high_fraction",
                signal=lock_signal,
                threshold=0.45,
                min_fraction=0.05,
                diagnostic_hint="Lock indicator should eventually assert for part of the transient.",
                repair_family="pll-dco-counter-feedback-loop",
            ),
        )

    up_pulse = (roles.get("up_pulse") or [None])[0]
    down_pulse = (roles.get("down_pulse") or [None])[0]
    pfd_deadzone_like = has_pfd and has_deadzone
    analog_output_exclusions: set[str] = set()
    if up_pulse and down_pulse:
        pulse_repair_family = (
            "bbpd-data-clock-lead-lag"
            if (has_bbpd and not has_pfd)
            else "pfd-latched-pulse-delayed-clear"
            if has_pfd
            else repair_family
        )
        pulse_required_signals = [up_pulse] if pfd_deadzone_like else [up_pulse, down_pulse]
        for signal in pulse_required_signals:
            _add_unique(
                contracts,
                _contract(
                    name=f"{signal}_pulses_present",
                    ctype="pulse_count",
                    signal=signal,
                    threshold=0.45,
                    min_pulses=2,
                    diagnostic_hint=f"`{signal}` should produce visible pulses, not just a static level.",
                    repair_family=pulse_repair_family,
                ),
            )
        if pfd_deadzone_like:
            analog_output_exclusions.add(down_pulse)
            _add_unique(
                contracts,
                _contract(
                    name=f"{down_pulse}_mostly_low",
                    ctype="high_fraction",
                    signal=down_pulse,
                    threshold=0.45,
                    max_fraction=0.02,
                    diagnostic_hint=f"`{down_pulse}` should remain mostly low for this deadzone stimulus.",
                    repair_family=pulse_repair_family,
                ),
            )
        _add_unique(
            contracts,
            _contract(
                name=f"{up_pulse}_{down_pulse}_non_overlap",
                ctype="non_overlap",
                signals=[up_pulse, down_pulse],
                threshold=0.45,
                max_overlap_fraction=0.02,
                diagnostic_hint=f"`{up_pulse}` and `{down_pulse}` should not be high at the same time.",
                repair_family=pulse_repair_family,
            ),
        )
        if has_pfd or has_bbpd:
            if has_bbpd and not has_pfd:
                edge_pair_kwargs = {
                    "reference": "data" if "data" in fields else up_pulse,
                    "feedback": "clk" if "clk" in fields else down_pulse,
                    "up": up_pulse,
                    "down": down_pulse,
                    "threshold": 0.45,
                    "max_pair_gap_s": 2e-9,
                    "response_tail_s": 2e-9,
                }
                paired_name = "bbpd_data_clock_paired_edge_response"
                paired_hint = "Each near-paired DATA/CLK edge should produce UP for data-leading pairs and DN for data-lagging pairs."
                paired_family = "bbpd-data-clock-lead-lag"
            else:
                edge_pair_kwargs = {
                    "reference": "ref" if "ref" in fields else up_pulse,
                    "feedback": "div" if "div" in fields else down_pulse,
                    "up": up_pulse,
                    "down": down_pulse,
                    "threshold": 0.45,
                    "max_pair_gap_s": 2e-9,
                    "response_tail_s": 2e-9,
                }
                paired_name = "pfd_paired_edge_response"
                paired_hint = "Each near-paired REF/DIV edge should produce a pulse on the side indicated by the leading edge."
                paired_family = "pfd-windowed-latched-pulse-symmetry"
            if edge_pair_kwargs["reference"] in fields and edge_pair_kwargs["feedback"] in fields:
                if has_pfd and has_reset_race:
                    _add_unique(
                        contracts,
                        _contract(
                            name="pfd_pulse_symmetry_window",
                            ctype="pulse_symmetry_window",
                            min_pairs_per_side=4,
                            max_wrong_responses=0,
                            diagnostic_hint="PFD reset-race stimulus should produce UP for reference-leading pairs and DN for feedback-leading pairs.",
                            repair_family="pfd-windowed-latched-pulse-symmetry",
                            severity="hard",
                            **edge_pair_kwargs,
                        ),
                    )
                _add_unique(
                    contracts,
                    _contract(
                        name=paired_name,
                        ctype="paired_edge_response",
                        min_total_pairs=8,
                        min_response_fraction=0.8,
                        max_wrong_responses=0,
                        diagnostic_hint=paired_hint,
                        repair_family=paired_family,
                        severity="advisory",
                        **edge_pair_kwargs,
                    ),
                )
                if has_pfd:
                    _add_unique(
                        contracts,
                        _contract(
                            name="pfd_pulse_width_fraction_window",
                            ctype="pulse_width_fraction_window",
                            min_expected_fraction=0.001,
                            max_expected_fraction=0.6,
                            max_wrong_fraction=0.02,
                            diagnostic_hint="PFD pulses should be visible but finite in the paired-edge response windows, with the non-leading side mostly low.",
                            repair_family="pfd-windowed-latched-pulse-symmetry",
                            severity="advisory",
                            **edge_pair_kwargs,
                        ),
                    )

    for base, signals in sorted(differential_pairs.items()):
        if any(_is_analog_output_like(signal) for signal in signals):
            diff_repair_family = _differential_repair_family(semantic_lower, repair_family)
            _add_unique(
                contracts,
                _contract(
                    name=f"{base}_differential_output_moves",
                    ctype="any_output_span",
                    signals=signals,
                    min_span=0.1,
                    diagnostic_hint=f"At least one side of differential output `{base}` should show activity.",
                    repair_family=diff_repair_family,
                    severity="advisory",
                ),
            )
            _add_unique(
                contracts,
                _contract(
                    name=f"{base}_differential_range",
                    ctype="differential_range",
                    positive=signals[0],
                    negative=signals[1],
                    min_diff_span=0.1,
                    diagnostic_hint=f"Differential output `{signals[0]} - {signals[1]}` should show meaningful movement, not just common-mode or stuck nodes.",
                    repair_family=diff_repair_family,
                    severity="hard",
                ),
            )
            _add_unique(
                contracts,
                _contract(
                    name=f"{base}_differential_polarity",
                    ctype="differential_sign_or_polarity",
                    positive=signals[0],
                    negative=signals[1],
                    min_diff_span=0.05,
                    max_common_to_diff_ratio=1.5,
                    diagnostic_hint=f"Differential pair `{signals[0]}`/`{signals[1]}` should primarily move as a differential signal rather than common-mode only.",
                    repair_family="differential-output-polarity",
                    severity="advisory",
                ),
            )

    analog_candidates = [
        signal
        for signal in fields
        if _is_analog_output_like(signal) and signal not in clock_signals and signal.lower() != "lock"
        and signal not in stimulus_signals
        and signal not in grouped_bits
        and signal not in differential_members
        and signal not in analog_output_exclusions
    ]
    for signal in analog_candidates[:6]:
        min_span = 0.01 if "vctrl" in signal.lower() or "metric" in signal.lower() else 0.1
        _add_unique(
            contracts,
            _contract(
                name=f"{signal}_moves",
                ctype="output_span",
                signal=signal,
                min_span=min_span,
                diagnostic_hint=f"`{signal}` should not remain stuck when its driving stimulus changes.",
                repair_family=repair_family,
            ),
        )

    for signal in fields:
        lower = signal.lower()
        should_check_input_span = (
            lower == "vin"
            and (
                "vin_span" in metrics
                or has_adc
                or family in {"code_coverage_or_quantizer", "analog_output_stuck"}
            )
        )
        if lower.startswith("vin") and lower != "vin":
            should_check_input_span = (
                f"{signal}_span" in metrics
                or f"{lower}_span" in metrics
                or family in {"code_coverage_or_quantizer", "analog_output_stuck"}
            )
        if should_check_input_span:
            _add_unique(
                contracts,
                _contract(
                    name=f"{signal}_input_activity",
                    ctype="input_span",
                    signal=signal,
                    min_span=0.05,
                    diagnostic_hint=f"`{signal}` stimulus should cover a nontrivial range; preserve it if this passes.",
                    repair_family=repair_family,
                    severity="advisory",
                ),
            )

    for prefix, bits in sorted(groups.items()):
        lower = prefix.lower()
        if lower in {"time"}:
            continue
        if len(bits) >= 2:
            max_unique = min(4, 2 ** min(len(bits), 8))
            _add_unique(
                contracts,
                _contract(
                    name=f"{prefix}_code_changes",
                    ctype="code_coverage",
                    bits=bits,
                    threshold=0.45,
                    min_unique=max_unique,
                    diagnostic_hint=f"`{prefix}` bit group should cover multiple observable states.",
                    repair_family=repair_family,
                    severity="advisory" if _is_stimulus_bit_group(prefix) else "hard",
                ),
            )
        if lower.startswith("cell_en") or lower.startswith("ptr"):
            kwargs = {"max_active": 1} if lower.startswith("ptr") else {}
            _add_unique(
                contracts,
                _contract(
                    name=f"{prefix}_has_active_bits",
                    ctype="active_count_range",
                    bits=bits,
                    threshold=0.45,
                    min_active=1,
                    diagnostic_hint=f"`{prefix}` should assert at least one bit during the run.",
                    repair_family="dwa-pointer-thermometer-mask",
                    **kwargs,
                ),
            )
        if lower.startswith("trim") and "SETTLED" in fields:
            clock = _signal_alias("CLK", fields) or _signal_alias("clk", fields)
            if clock:
                _add_unique(
                    contracts,
                    _contract(
                        name="settled_after_trim_stable",
                        ctype="settled_flag_after_stable_cycles",
                        clock=clock,
                        state_bits=bits,
                        flag="SETTLED",
                        threshold=0.45,
                        min_stable_cycles=8,
                        diagnostic_hint="Trim code changes enough, but SETTLED must assert after the trim code stops changing for consecutive cycles.",
                        repair_family="calibration-settled-flag-from-stable-cycles",
                    ),
                )
        if has_gray or lower in {"g", "gray"}:
            _add_unique(
                contracts,
                _contract(
                    name=f"{prefix}_one_bit_transitions",
                    ctype="code_hamming_distance",
                    bits=bits,
                    threshold=0.45,
                    max_hamming=1,
                    min_transitions=4,
                    diagnostic_hint=f"`{prefix}` state transitions should flip one bit at a time.",
                    repair_family="gray-counter-one-bit-sequence",
                ),
            )

    for metric_name in ("fb", "out", "pulses", "count", "transitions"):
        raw = metrics.get(metric_name)
        if raw not in {"0", "0.0", "0.000"}:
            continue
        signal = _signal_alias(metric_name, fields)
        if signal and not any(c.get("signal") == signal and c.get("type") == "edge_count" for c in contracts):
            _add_unique(
                contracts,
                _contract(
                    name=f"{signal}_activity_from_failure_metric",
                    ctype="edge_count",
                    signal=signal,
                    threshold=0.45,
                    min_edges=2,
                    diagnostic_hint=f"Failure metrics indicate `{signal}` has too little activity.",
                    repair_family=repair_family,
                ),
            )

    prompt_templates_applied = _add_prompt_spec_contracts(
        contracts,
        task_id=task_id,
        prompt_spec=prompt_spec,
        fields=fields,
        default_repair_family=repair_family,
    )

    return {
        "task_id": task_id,
        "source": {
            "generator": "generate_behavior_contracts.py",
            "contract_family": family,
            "repair_template": repair_family,
            "raw_contract_family": raw_family,
            "raw_repair_template": raw_repair_family,
            "blocking_family": blocking_family,
            "blocking_repair_template": blocking_repair_template,
            "semantic_family": semantic_family,
            "semantic_repair_template": semantic_repair_template,
            "semantic_summary": triage_semantic_summary,
            "prompt_semantic_family": prompt_semantic_family,
            "prompt_semantic_repair_template": prompt_semantic_repair_template,
            "contract_family_calibration_source": calibration_source,
            "result_path": str(result_path) if result_path else "",
            "csv_path": str(csv_path) if csv_path else "",
            "public_signal_source": public_signal_source,
            "public_prompt_roles": public_prompt_roles,
            "prompt_checker_spec_source": prompt_spec.get("source") if prompt_spec else "",
            "prompt_checker_inferred_for": prompt_spec.get("task_id") if prompt_spec else "",
            "prompt_checker_signal_sources": prompt_spec.get("signal_sources", {}) if prompt_spec else {},
            "prompt_functional_ir": prompt_spec.get("functional_ir", {}) if prompt_spec else {},
            "prompt_functional_claims": [
                str(item.get("type", ""))
                for item in (prompt_spec.get("functional_ir", {}) or {}).get("claims", [])
                if item.get("type")
            ] if prompt_spec else [],
            "prompt_checker_policy": prompt_spec.get("policy", {}) if prompt_spec else {},
            "prompt_semantic_templates": prompt_templates,
            "prompt_checker_templates": prompt_templates_applied,
        },
        "contracts": contracts,
    }


def _load_failures(args: argparse.Namespace) -> list[dict]:
    data = _read_json(Path(args.triage_json))
    failures = list(data.get("failures", []))
    if args.task:
        selected = set(args.task)
        failures = [failure for failure in failures if failure.get("task_id") in selected]
    if args.include_scoring_mismatch:
        return failures
    return [failure for failure in failures if failure.get("contract_family") != "scoring_contract_mismatch"]


def _apply_contract(task_id: str, generated_path: Path, *, overwrite: bool) -> str:
    task_dir = _task_dir(task_id)
    dst = task_dir / "contracts.json"
    if dst.exists() and not overwrite:
        return "kept_existing"
    if dst.exists():
        backup = dst.with_suffix(".json.bak")
        if not backup.exists():
            shutil.copy2(dst, backup)
    shutil.copy2(generated_path, dst)
    return "written"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--triage-json", default="results/behavior-contract-triage-H-on-F-stable-2026-04-26.json")
    parser.add_argument("--result-root", default="")
    parser.add_argument("--out-root", required=True)
    parser.add_argument("--task", action="append", default=[])
    parser.add_argument("--apply", action="store_true", help="Copy generated contracts into task directories.")
    parser.add_argument("--overwrite", action="store_true", help="When applying, replace existing task contracts after backing them up.")
    parser.add_argument("--include-scoring-mismatch", action="store_true")
    parser.add_argument("--prompt-specs", default="docs/PROMPT_CHECKER_SPECS_ADOPTED.json",
                        help="Adopted prompt-inferred checker spec catalog. Used as a mechanism-template whitelist/threshold, not as a task-id lookup table.")
    parser.add_argument("--disable-prompt-specs", action="store_true",
                        help="Disable adopted prompt checker spec augmentation.")
    args = parser.parse_args()

    out_root = Path(args.out_root)
    result_root = Path(args.result_root) if args.result_root else None
    prompt_specs_path = None if args.disable_prompt_specs else Path(args.prompt_specs)
    if prompt_specs_path is not None and not prompt_specs_path.is_absolute():
        prompt_specs_path = ROOT / prompt_specs_path
    prompt_spec_policy = (
        {"enabled": False, "mode": "disabled", "path": "", "catalog_specs": 0, "approved_templates": [], "adopt_threshold": 0.70}
        if args.disable_prompt_specs
        else _load_prompt_spec_policy(prompt_specs_path)
    )
    failures = _load_failures(args)
    summary = {
        "triage_json": args.triage_json,
        "result_root": args.result_root,
        "prompt_specs": "" if args.disable_prompt_specs else str(prompt_specs_path),
        "prompt_specs_loaded": prompt_spec_policy.get("catalog_specs", 0),
        "prompt_spec_mode": prompt_spec_policy.get("mode", ""),
        "prompt_spec_approved_templates": prompt_spec_policy.get("approved_templates", []),
        "generated_tasks": 0,
        "applied": {},
        "tasks": [],
    }

    for failure in failures:
        task_id = failure["task_id"]
        spec = generate_contract_spec(
            failure,
            result_root=result_root,
            prompt_spec_policy=prompt_spec_policy,
        )
        if not spec.get("contracts"):
            continue
        out_path = out_root / task_id / "contracts.json"
        _write_json(out_path, spec)
        apply_status = ""
        if args.apply:
            apply_status = _apply_contract(task_id, out_path, overwrite=args.overwrite)
            summary["applied"][task_id] = apply_status
        summary["generated_tasks"] += 1
        summary["tasks"].append(
            {
                "task_id": task_id,
                "contract_count": len(spec["contracts"]),
                "contract_family": spec["source"]["contract_family"],
                "repair_template": spec["source"]["repair_template"],
                "raw_contract_family": spec["source"].get("raw_contract_family", ""),
                "raw_repair_template": spec["source"].get("raw_repair_template", ""),
                "blocking_family": spec["source"].get("blocking_family", ""),
                "blocking_repair_template": spec["source"].get("blocking_repair_template", ""),
                "semantic_family": spec["source"].get("semantic_family", ""),
                "semantic_repair_template": spec["source"].get("semantic_repair_template", ""),
                "contract_family_calibration_source": spec["source"].get("contract_family_calibration_source", ""),
                "prompt_checker_templates": spec["source"].get("prompt_checker_templates", []),
                "path": str(out_path),
                "apply_status": apply_status,
            }
        )

    _write_json(out_root / "summary.json", summary)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
