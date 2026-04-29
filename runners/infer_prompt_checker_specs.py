#!/usr/bin/env python3
"""Infer mechanism-level checker specs from public task prompts.

This tool is intentionally advisory. It does not replace official checkers or
modify scoring. It maps prompt text, public save names, and simple signal-role
rules to parameterized checker-spec templates, then validates those inferences
against a small curated mechanism-label set before writing adopted specs.
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IDENT_RE = r"[A-Za-z_][A-Za-z0-9_]*"
BACKTICK_RE = re.compile(r"`([^`]+)`")
PORT_RE = re.compile(rf"[-*]\s*`?({IDENT_RE}(?:\[\d+:\d+\])?)`?\s*:\s*(input|output|inout)?\s*electrical", re.IGNORECASE)
TRAN_RE = re.compile(r"tran\s+tran\s+([^\n`]+)", re.IGNORECASE)


@dataclass
class TemplateSpec:
    template: str
    confidence: float
    signals: dict[str, object] = field(default_factory=dict)
    parameters: dict[str, object] = field(default_factory=dict)
    evidence: list[str] = field(default_factory=list)


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def _words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _has_word_like(words: list[str], target: str, *, threshold: float = 0.86) -> bool:
    target_l = target.lower()
    for word in words:
        if word == target_l:
            return True
        if len(word) >= 5 and SequenceMatcher(None, word, target_l).ratio() >= threshold:
            return True
    return False


def _has_any_word_like(words: list[str], *targets: str, threshold: float = 0.86) -> bool:
    return any(_has_word_like(words, target, threshold=threshold) for target in targets)


def _squash_space(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def _expand_bus(token: str) -> list[str]:
    match = re.fullmatch(rf"({IDENT_RE})\[(\d+):(\d+)\]", token.strip())
    if not match:
        return [token.strip()]
    base = match.group(1)
    left = int(match.group(2))
    right = int(match.group(3))
    if abs(left - right) > 64:
        return [token.strip()]
    step = 1 if right >= left else -1
    return [f"{base}_{idx}" for idx in range(left, right + step, step)]


def _normalize_token(token: str) -> list[str]:
    cleaned = token.strip().strip(",.;:")
    if not cleaned:
        return []
    if re.fullmatch(rf"{IDENT_RE}\[\d+:\d+\]", cleaned):
        return _expand_bus(cleaned)
    if re.fullmatch(rf"{IDENT_RE}", cleaned):
        return [cleaned]
    return []


def list_task_dirs(selected: set[str] | None = None) -> list[tuple[str, Path]]:
    tasks: list[tuple[str, Path]] = []
    for meta_path in sorted((ROOT / "tasks").rglob("meta.json")):
        task_dir = meta_path.parent
        try:
            meta = _read_json(meta_path)
        except Exception:
            continue
        task_id = meta.get("task_id") or meta.get("id") or task_dir.name
        if selected and task_id not in selected:
            continue
        if not (task_dir / "prompt.md").exists():
            continue
        tasks.append((task_id, task_dir))
    return tasks


def gold_save_names(task_dir: Path) -> list[str]:
    names: list[str] = []
    for tb in sorted((task_dir / "gold").glob("*.scs")):
        text = tb.read_text(encoding="utf-8", errors="ignore").replace("\\\n", " ")
        for raw in text.splitlines():
            stripped = raw.strip()
            if not stripped.lower().startswith("save "):
                continue
            for token in stripped.split()[1:]:
                token = token.strip().strip(",")
                if not token or token.lower() in {"all", "allpub"}:
                    continue
                if ":" in token:
                    token = token.split(":")[-1]
                if "." in token:
                    token = token.split(".")[-1]
                names.extend(_normalize_token(token))
    return _dedupe(names)


def prompt_signals(prompt: str) -> tuple[list[str], dict[str, str]]:
    signals: list[str] = []
    roles: dict[str, str] = {}

    for token in BACKTICK_RE.findall(prompt):
        for signal in _normalize_token(token):
            signals.append(signal)

    for match in PORT_RE.finditer(prompt):
        for signal in _normalize_token(match.group(1)):
            signals.append(signal)
            role = (match.group(2) or "").lower()
            if role:
                roles[signal] = role

    for raw in re.findall(rf"\b{IDENT_RE}(?:\[\d+:\d+\])?\b", prompt):
        low = raw.lower()
        if (
            "clk" in low
            or low in {"clock", "ref", "div", "up", "dn", "lock", "locked", "rst_n", "reset", "rst"}
            or low.startswith(("dout", "din", "trim", "vout", "aout", "vctrl"))
        ):
            for signal in _normalize_token(raw):
                signals.append(signal)

    return _dedupe(signals), roles


def _group_bits(signals: list[str]) -> dict[str, list[str]]:
    groups: dict[str, list[tuple[int, str]]] = {}
    for signal in signals:
        for pattern in (
            re.compile(r"^(.+)_([0-9]+)$"),
            re.compile(r"^([A-Za-z]+)([0-9]+)$"),
        ):
            match = pattern.fullmatch(signal)
            if not match:
                continue
            prefix = match.group(1)
            idx = int(match.group(2))
            groups.setdefault(prefix, []).append((idx, signal))
            break
    return {
        prefix: [name for _idx, name in sorted(items, key=lambda item: item[0], reverse=True)]
        for prefix, items in groups.items()
        if len(items) >= 2
    }


def signal_roles(signals: list[str], prompt_roles: dict[str, str]) -> dict[str, object]:
    roles: dict[str, object] = {
        "clock": [],
        "reset": [],
        "reference_clock": [],
        "feedback_clock": [],
        "lock": [],
        "up": [],
        "down": [],
        "analog_input": [],
        "analog_output": [],
        "code_bits": {},
        "control": [],
        "settled": [],
    }
    for signal in signals:
        low = signal.lower()
        collapsed = low.replace("_", "")
        if low in {"ref", "ref_clk", "refclk"} or collapsed in {"refclk", "referenceclock"}:
            roles["reference_clock"].append(signal)
        elif low in {"fb", "fb_clk", "fbclk"} or collapsed in {"fbclk", "feedbackclock"}:
            roles["feedback_clock"].append(signal)
        elif "clk" in low or low in {"clock", "rdy", "clks"}:
            roles["clock"].append(signal)
        if "rst" in low or "reset" in low:
            roles["reset"].append(signal)
        if low in {"lock", "locked"}:
            roles["lock"].append(signal)
        if low in {"up", "up_out", "upout"}:
            roles["up"].append(signal)
        if low in {"dn", "down", "dn_out", "dnout"}:
            roles["down"].append(signal)
        if low in {"settled", "settle"}:
            roles["settled"].append(signal)
        if "ctrl" in low or low.startswith("vctrl") or "ratio" in low:
            if not low.endswith("_ref"):
                roles["control"].append(signal)
        if low in {"vin", "vinp", "vinn", "input", "comp_out"} or low.startswith("din"):
            roles["analog_input"].append(signal)
        if (
            low in {"vout", "aout", "out", "y", "vout_p", "vout_n", "vdac_p", "vdac_n"}
            or low.startswith("vout")
            or low.endswith("_out")
            or prompt_roles.get(signal) == "output"
        ):
            roles["analog_output"].append(signal)

    bit_groups = _group_bits(signals)
    for prefix, bits in bit_groups.items():
        roles["code_bits"][prefix] = bits

    for key, value in list(roles.items()):
        if isinstance(value, list):
            roles[key] = _dedupe(value)
    roles["prompt_port_roles"] = prompt_roles
    return roles


def _parse_bit_width(prompt: str, roles: dict[str, object]) -> int | None:
    widths = [int(raw) for raw in re.findall(r"\b(\d+)\s*[- ]?\s*bit\b", prompt, flags=re.IGNORECASE)]
    if widths:
        return max(widths)
    groups = roles.get("code_bits", {})
    if isinstance(groups, dict) and groups:
        return max(len(bits) for bits in groups.values())
    return None


def _parse_divide_ratios(prompt: str) -> list[int]:
    ratios: list[int] = []
    for pattern in (
        r"divide[- ]?by[- ]?(\d+)",
        r"divide\s+by\s+(\d+)",
        r"ratio\s*(?:is|=|should be)?\s*(\d+)",
    ):
        ratios.extend(int(raw) for raw in re.findall(pattern, prompt, flags=re.IGNORECASE))
    return sorted(set(ratios))


def _parse_target_times(prompt: str) -> list[float]:
    times: list[float] = []
    for number, unit in re.findall(r"(\d+(?:\.\d+)?)\s*(ns|us|ms|s)\b", prompt, flags=re.IGNORECASE):
        value = float(number)
        unit_l = unit.lower()
        if unit_l == "ns":
            times.append(value * 1e-9)
        elif unit_l == "us":
            times.append(value * 1e-6)
        elif unit_l == "ms":
            times.append(value * 1e-3)
        else:
            times.append(value)
    return times[:16]


def _tran_setting(prompt: str) -> str | None:
    match = TRAN_RE.search(prompt)
    if not match:
        return None
    return "tran tran " + re.sub(r"\s+", " ", match.group(1).strip())


def _first_list(roles: dict[str, object], key: str) -> str | None:
    value = roles.get(key, [])
    if isinstance(value, list) and value:
        return value[0]
    return None


def _first_role_signal(roles: dict[str, object], key: str, *, contains: str | None = None) -> str | None:
    value = roles.get(key, [])
    if not isinstance(value, list):
        return None
    filtered = [item for item in value if not item.lower().endswith("_ref")]
    if contains:
        preferred = [item for item in filtered if contains.lower() in item.lower()]
        if preferred:
            return preferred[0]
    return filtered[0] if filtered else None


def _best_bits(roles: dict[str, object], preferred: tuple[str, ...]) -> list[str]:
    groups = roles.get("code_bits", {})
    if not isinstance(groups, dict):
        return []
    normalized = {
        key: key.lower().replace("_", "")
        for key in groups
    }
    for prefix in preferred:
        if prefix in groups:
            return list(groups[prefix])
        prefix_norm = prefix.lower().replace("_", "")
        for key, bits in groups.items():
            if key.lower() == prefix.lower():
                return list(bits)
        for key, bits in groups.items():
            key_norm = normalized[key]
            if len(prefix_norm) >= 3 and (key_norm.startswith(prefix_norm) or prefix_norm.startswith(key_norm)):
                return list(bits)
    if groups:
        return list(next(iter(groups.values())))
    return []


def _choose_signal(signals: list[str], *candidates: str) -> str | None:
    by_lower = {signal.lower(): signal for signal in signals}
    for candidate in candidates:
        match = by_lower.get(candidate.lower())
        if match:
            return match
    return None


def _choose_signal_contains(signals: list[str], *needles: str) -> str | None:
    lowered_needles = [needle.lower() for needle in needles]
    for signal in signals:
        low = signal.lower()
        if any(needle in low for needle in lowered_needles):
            return signal
    return None


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


def _infer_functional_ir(prompt: str, signals: list[str], roles: dict[str, object], width: int | None) -> dict:
    """Extract a small prompt-level functional IR.

    The IR is deliberately compact: it captures behavior relations that can be
    mapped to checker templates without relying on one exact word such as
    "monotonic".  It is not intended to be a full natural-language parser.
    """
    lower = prompt.lower()
    lower_flat = _squash_space(prompt)
    words = _words(prompt)
    claims: list[dict[str, object]] = []

    def has_phrase(*phrases: str) -> bool:
        return any(phrase in lower_flat for phrase in phrases)

    def add_claim(
        claim_type: str,
        confidence: float,
        evidence: list[str],
        operands: dict[str, object] | None = None,
        parameters: dict[str, object] | None = None,
    ) -> None:
        if any(item.get("type") == claim_type for item in claims):
            return
        claims.append(
            {
                "type": claim_type,
                "confidence": round(confidence, 3),
                "operands": operands or {},
                "parameters": {k: v for k, v in (parameters or {}).items() if v is not None},
                "evidence": evidence,
            }
        )

    has_adc_text = (
        "adc" in lower
        or "analog-to-digital" in lower
        or "analog to digital" in lower
    )
    has_dac_text = (
        "dac" in lower
        or "digital-to-analog" in lower
        or "digital to analog" in lower
    )
    bits = _best_bits(roles, ("din", "dinp", "code", "d", "D", "therm", "therm_in", "dout", "out"))
    analog_input = "vin" if "vin" in signals else _first_list(roles, "analog_input")
    analog_output = (
        "vout" if "vout" in signals else _first_list(roles, "analog_output")
    )
    code_operand = bits or _best_bits(roles, ("dout", "code"))

    negates_order = has_phrase(
        "no ordering guarantee",
        "need not be monotonic",
        "not monotonic",
        "may go down",
        "can go down",
        "arbitrary order",
        "unconstrained order",
    )
    ordered_relation = (
        _has_any_word_like(words, "monotonic", "monotone")
        or bool(re.search(r"\b(?:larger|greater|higher)\b.{0,100}\b(?:must|should)?\s*(?:not|never|no)\s+(?:\w+\s+){0,4}(?:be\s+)?(?:lower|smaller|decreas|drop|fall|go\s+down)", lower_flat))
        or bool(re.search(r"\b(?:increase|increases|increasing|rises|rising)\b.{0,100}\b(?:never|not|no)\s+(?:decreas|drop|fall|go\s+down|be\s+lower)", lower_flat))
        or bool(re.search(r"\b(?:must|should)\s+(?:not|never)\s+(?:decrease|drop|fall|go\s+down)\b", lower_flat))
    ) and not negates_order

    transfer_like = (
        has_phrase("decode", "map", "maps", "convert", "converted", "input word", "unsigned integer")
        or "produced voltage" in lower_flat
        or "output voltage" in lower_flat
        or ordered_relation
    )
    if has_dac_text and transfer_like and (code_operand or "code" in lower or "input word" in lower) and (analog_output or "voltage" in lower):
        add_claim(
            "code_to_analog_transfer",
            0.84 if ordered_relation else 0.76,
            ["functional text relates a digital code/input word to an analog output"],
            {"code": code_operand, "output": analog_output},
            {"bit_width": width},
        )
    if ordered_relation:
        add_claim(
            "ordered_transfer",
            0.86,
            ["functional text states that increasing the input relation must not lower the output relation"],
            {"x": code_operand or analog_input, "y": analog_output or code_operand},
            {"direction": "nondecreasing"},
        )

    negates_thermometer = bool(re.search(r"\bnot\s+(?:a\s+)?(?:thermometer|unary)\b", lower_flat))
    count_high_relation = (
        has_phrase("count of ones", "population count")
        or bool(re.search(r"\b(?:number|count|how many)\b.{0,80}\b(?:high|asserted|on|enabled|active)\b", lower_flat))
        or bool(re.search(r"\b(?:high|asserted|enabled|active)\b.{0,80}\b(?:cells|controls|inputs)\b", lower_flat))
        or "unit cells" in lower_flat
    ) and not negates_thermometer
    if has_dac_text and count_high_relation:
        add_claim(
            "count_high_to_analog",
            0.88,
            ["functional text maps the number of asserted unit controls to analog output"],
            {"bits": bits, "output": analog_output},
            {"bit_width": width},
        )

    quantized_relation = (
        has_phrase("bucket index", "bucket that", "bin index", "encoded number", "stored index")
        or "quantized" in lower
        or ("larger vin" in lower_flat and "smaller" in lower_flat)
    )
    if has_adc_text and quantized_relation:
        add_claim(
            "quantized_encoding",
            0.86,
            ["functional text maps analog input buckets to encoded digital outputs"],
            {"input": analog_input, "code": _best_bits(roles, ("dout", "out", "code"))},
            {"bit_width": width},
        )

    sample_edge_relation = (
        ("edge" in lower or "clock" in lower or "clk" in lower)
        and has_phrase("capture", "captures", "captured", "store", "stores", "stored", "sample", "samples", "sampled", "latch", "latched")
    )
    if sample_edge_relation:
        add_claim(
            "sample_on_clock_edge",
            0.78,
            ["functional text says values are captured or stored on a clock edge"],
            {"clock": _first_list(roles, "clock"), "sampled": analog_input or code_operand},
        )

    data_clock_relation = (
        ("data" in lower and ("clock" in lower or "clk" in lower))
        and ("up" in lower and ("dn" in lower or "down" in lower))
        and (
            has_phrase("arrives before", "arrive before", "arrives after", "arrive after")
            or "leads" in lower
            or "lags" in lower
            or "lead" in lower
            or "lag" in lower
        )
    )
    if data_clock_relation:
        add_claim(
            "data_clock_lead_lag_pulses",
            0.90,
            ["functional text maps data/clock lead-lag ordering to UP/DN pulses"],
            {"data": _choose_signal(signals, "data") or _choose_signal_contains(signals, "data"),
             "clock": _choose_signal(signals, "clk", "clock") or _first_list(roles, "clock"),
            "up": _first_list(roles, "up"), "down": _first_list(roles, "down")},
        )

    dwa_relation = (
        ("dwa" in lower or "data weighted averaging" in lower)
        and ("pointer" in lower or "ptr" in lower)
        and ("cell" in lower or "cell_en" in lower or "selection window" in lower)
        and ("rotate" in lower or "rotating" in lower or "wrap" in lower or "window" in lower)
    )
    if dwa_relation:
        add_claim(
            "rotating_selection_window",
            0.90,
            ["functional text describes a DWA rotating pointer/cell-enable selection window"],
            {
                "clock": _first_list(roles, "clock"),
                "reset": _first_list(roles, "reset"),
                "pointer": _best_bits(roles, ("ptr", "ptr_o")),
                "cell_enable": _best_bits(roles, ("cell_en", "cell_en_o")),
                "code": _best_bits(roles, ("code", "code_i", "code_msb_i")),
            },
        )

    if "counter" in lower and bool(re.search(r"\b(?:adjacent|successive|consecutive|neighboring)\b.{0,80}\b(?:one|single|1)\s+bit\b", lower_flat)):
        add_claim(
            "one_bit_adjacent_transition",
            0.86,
            ["functional text requires adjacent counter states to differ by one bit"],
            {"clock": _first_list(roles, "clock"), "bits": _best_bits(roles, ("g", "gray", "state", "count"))},
            {"encoding": "one_bit_change"},
        )

    if (
        ("serial" in lower or "shift" in lower or "send" in lower)
        and "frame" in lower
        and ("first" in lower or "alignment" in lower or "aligned" in lower)
    ):
        add_claim(
            "frame_aligned_serial_sequence",
            0.80,
            ["functional text ties serial output order to a frame marker"],
            {"clock": _first_list(roles, "clock"), "outputs": roles.get("analog_output", [])},
        )

    if (
        "reps" in lower
        and ("pulse" in lower or "pulses" in lower)
        and ("exactly" in lower or "equals" in lower or "equal to" in lower)
    ):
        add_claim(
            "parameterized_repetition",
            0.84,
            ["functional text ties emitted pulse count to a parameter"],
            {"outputs": roles.get("analog_output", [])},
        )

    return {
        "version": "functional-ir-v1",
        "claims": sorted(claims, key=lambda item: float(item.get("confidence", 0.0)), reverse=True),
    }


def infer_specs(task_id: str, task_dir: Path, *, include_gold_save_names: bool = False) -> dict:
    prompt_path = task_dir / "prompt.md"
    prompt = prompt_path.read_text(encoding="utf-8", errors="ignore")
    semantic_prompt = _semantic_prompt_text(prompt)
    lower = semantic_prompt.lower()
    lower_flat = _squash_space(semantic_prompt)
    prompt_words = _words(semantic_prompt)
    signals, prompt_roles = prompt_signals(prompt)
    gold_signals = gold_save_names(task_dir) if include_gold_save_names else []
    signals = _dedupe(signals + gold_signals)
    roles = signal_roles(signals, prompt_roles)
    width = _parse_bit_width(prompt, roles)
    ratios = _parse_divide_ratios(prompt)
    tran = _tran_setting(prompt)
    functional_ir = _infer_functional_ir(semantic_prompt, signals, roles, width)
    functional_claim_types = {str(item.get("type")) for item in functional_ir.get("claims", [])}
    specs: list[TemplateSpec] = []

    def add(template: str, confidence: float, evidence: list[str], signals_payload: dict[str, object] | None = None, parameters: dict[str, object] | None = None) -> None:
        specs.append(
            TemplateSpec(
                template=template,
                confidence=confidence,
                signals=signals_payload or {},
                parameters=parameters or {},
                evidence=evidence,
            )
        )

    def has_claim(claim_type: str) -> bool:
        return claim_type in functional_claim_types

    has_adc = (
        "adc" in lower
        or "analog-to-digital" in lower
        or "analog to digital" in lower
        or has_claim("quantized_encoding")
    )
    has_dac = (
        "dac" in lower
        or "digital-to-analog" in lower
        or "digital to analog" in lower
        or has_claim("code_to_analog_transfer")
        or has_claim("count_high_to_analog")
    )
    has_pll = (
        "pll" in lower
        or "phase-locked loop" in lower
        or "phase locked loop" in lower
    )
    has_sar = (
        "sar" in lower
        or "successive approximation" in lower
    )
    has_divider = (
        "divider" in lower
        or "divide-by" in lower
        or "divide by" in lower
        or "clock divider" in lower
        or "frequency divider" in lower
    ) and not has_pll
    has_pfd = "pfd" in lower or "phase frequency detector" in lower
    has_bbpd = "bbpd" in lower or "bang-bang phase detector" in lower or "bang bang phase detector" in lower
    has_dwa = (
        "dwa" in lower
        or "data weighted averaging" in lower
        or has_claim("rotating_selection_window")
    )
    negates_thermometer = bool(re.search(r"\bnot\s+(?:a\s+)?(?:thermometer|unary)\b", lower_flat))
    has_thermometer_dac = (
        (
            _has_any_word_like(prompt_words, "thermometer", "unary")
            or "count of ones" in lower_flat
            or "population count" in lower_flat
            or has_claim("count_high_to_analog")
        )
        and not negates_thermometer
    )
    negates_parameter_override = any(
        phrase in lower_flat
        for phrase in (
            "no instance parameter override",
            "no instance parameter overrides",
            "no parameter override",
            "no parameter overrides",
            "without instance parameter override",
            "without parameter override",
        )
    )
    monotonic_like = _has_any_word_like(prompt_words, "monotonic", "monotone") or has_claim("ordered_transfer")
    span_like = _has_word_like(prompt_words, "span")
    level_like = _has_any_word_like(prompt_words, "level", "levels")
    weighted_like = _has_word_like(prompt_words, "weighted")

    if has_adc and has_dac and ("round-trip" in lower or "round trip" in lower or "vout" in lower):
        bits = _best_bits(roles, ("dout", "dout_", "code"))
        add(
            "quantized_reconstruction",
            0.93,
            ["prompt mentions ADC-DAC round trip and reconstructed vout"],
            {
                "input": "vin" if "vin" in signals else _first_list(roles, "analog_input"),
                "output": "vout" if "vout" in signals else _first_list(roles, "analog_output"),
                "bits": bits,
                "clock": _first_list(roles, "clock"),
                "reset": _first_list(roles, "reset"),
            },
            {"bit_width": width, "min_unique_codes": max(12, (1 << min(width or 4, 4)) - 4) if width else 12},
        )
    if has_adc and ("code" in lower or "quantization" in lower or "floor" in lower or has_claim("quantized_encoding")):
        add(
            "monotonic_code_vs_input",
            0.86 if "ramp" in lower or monotonic_like else 0.74,
            ["prompt mentions ADC code/quantization or functional IR quantized encoding"],
            {"input": "vin" if "vin" in signals else _first_list(roles, "analog_input"), "bits": _best_bits(roles, ("dout", "code"))},
            {"direction": "nondecreasing", "bit_width": width},
        )
    if has_adc and ("rising edge" in lower or "@(cross" in lower or "sample" in lower or has_claim("sample_on_clock_edge")):
        add(
            "sample_after_clock",
            0.78,
            ["prompt mentions sampled update on a clock edge or functional IR sample relation"],
            {"clock": _first_list(roles, "clock"), "bits": _best_bits(roles, ("dout", "code"))},
            {"edge": "rising"},
        )
    if has_sar and ("logic" in lower or "successive" in lower or "eoc" in lower or "rdy" in lower or "ready" in lower):
        add(
            "sar_sequence",
            0.88,
            ["prompt describes SAR state sequencing or end-of-conversion/ready behavior"],
            {
                "clock": _first_list(roles, "clock"),
                "comparator": "DCOMP" if "DCOMP" in signals else _first_role_signal(roles, "analog_input", contains="comp"),
                "ready": "RDY" if "RDY" in signals else "rdy" if "rdy" in signals else None,
                "eoc": "EOC" if "EOC" in signals else "eoc" if "eoc" in signals else None,
                "bits": _best_bits(roles, ("DP_DAC", "DP_CAP", "dp_dac", "dp_cap")),
            },
            {"bit_width": width},
        )

    if has_dwa:
        add(
            "onehot_no_overlap",
            0.91 if "no overlap" in lower or "wrap" in lower else 0.84,
            ["prompt describes DWA rotating pointer/cell-enable selection-window behavior"],
            {
                "clock": _first_list(roles, "clock"),
                "reset": _first_list(roles, "reset"),
                "pointer_bits": _best_bits(roles, ("ptr", "ptr_o")),
                "cell_bits": _best_bits(roles, ("cell_en", "cell_en_o")),
                "code_bits": _best_bits(roles, ("code", "code_i", "code_msb_i")),
            },
            {
                "cells": 16 if "16" in lower or "cell_en_o[15:0]" in lower else None,
                "require_no_overlap": "no overlap" in lower or "do not reuse" in lower,
                "require_wraparound": "wrap" in lower,
            },
        )

    if has_dac and (monotonic_like or span_like or level_like or has_thermometer_dac or weighted_like or has_claim("code_to_analog_transfer")):
        if "differential" in lower:
            template = "differential_code_response"
        elif "segmented" in lower:
            template = "dac_code_to_output_span"
        elif has_thermometer_dac:
            template = "thermometer_dac_code_to_output_span"
        else:
            template = "dac_code_to_output_span"
        add(
            template,
            0.86 if monotonic_like or span_like or has_claim("code_to_analog_transfer") else 0.76,
            ["prompt describes DAC code-to-output behavior or functional IR code-to-analog transfer"],
            {
                "bits": _best_bits(roles, ("din", "d", "D", "therm", "therm_in", "code")),
                "output": _first_list(roles, "analog_output"),
                "clock": _first_list(roles, "clock"),
            },
            {"bit_width": width, "require_monotonic": monotonic_like},
        )

    if "differential" in lower and any(name in signals for name in ("VOUT_P", "VOUT_N", "VDAC_P", "VDAC_N", "vout_p", "vout_n")):
        add(
            "differential_code_response",
            0.82,
            ["prompt has differential output ports"],
            {"positive": "VOUT_P" if "VOUT_P" in signals else "VDAC_P" if "VDAC_P" in signals else None,
             "negative": "VOUT_N" if "VOUT_N" in signals else "VDAC_N" if "VDAC_N" in signals else None},
            {"bit_width": width},
        )
    if "differential output" in lower or "v(outp, outn)" in lower or "v(out_p, out_n)" in lower:
        add(
            "differential_step_response",
            0.88,
            ["prompt describes differential output branch levels over time"],
            {
                "positive": _choose_signal(signals, "outp", "out_p", "OUTP", "OUT_P"),
                "negative": _choose_signal(signals, "outn", "out_n", "OUTN", "OUT_N"),
            },
            {"mode": "timed_step" if "timer" in lower or "20 ns" in lower else "differential"},
        )

    if has_divider:
        mode = "pulse" if "pulse" in lower else "toggle" if "toggle" in lower else "edge_ratio"
        add(
            "counter_cadence",
            0.90,
            ["prompt describes divider/counter ratio behavior"],
            {
                "input_clock": _first_list(roles, "clock") or _first_list(roles, "reference_clock"),
                "output": "div_out" if "div_out" in signals else _first_list(roles, "analog_output"),
                "control": _first_role_signal(roles, "control", contains="ctrl"),
            },
            {"expected_ratios": ratios, "mode": mode},
        )
        if "ratio_ctrl" in lower or "ratio" in lower and len(ratios) > 1:
            add("ratio_control_window", 0.80, ["prompt describes ratio control changes"], {"control": _first_role_signal(roles, "control", contains="ctrl")}, {"expected_ratios": ratios})

    if ("gray" in lower and "counter" in lower) or has_claim("one_bit_adjacent_transition"):
        add(
            "gray_counter_sequence",
            0.90,
            ["prompt describes Gray-code or one-bit-adjacent counter transition behavior"],
            {
                "clock": _first_list(roles, "clock"),
                "reset": _first_list(roles, "reset"),
                "bits": _best_bits(roles, ("g", "gray")),
            },
            {"encoding": "binary_to_gray"},
        )

    has_data_clock_lead_lag = has_claim("data_clock_lead_lag_pulses")
    if has_pfd or has_bbpd or has_data_clock_lead_lag:
        if (has_bbpd or has_data_clock_lead_lag) and not has_pfd:
            reference_signal = _choose_signal(signals, "data") or _choose_signal_contains(signals, "data")
            feedback_signal = _choose_signal(signals, "clk", "clock") or _first_list(roles, "clock")
            edge_evidence = ["prompt describes data/clock lead-lag bang-bang phase detection or functional IR lead-lag pulses"]
            edge_template = "bbpd_data_clock_lead_lag"
        else:
            reference_signal = "ref" if "ref" in signals else _first_list(roles, "reference_clock")
            feedback_signal = "div" if "div" in signals else None
            edge_evidence = ["prompt describes ref/div edge-triggered up/dn response"]
            edge_template = "paired_edge_response"
        add(
            edge_template,
            0.91,
            edge_evidence,
            {"reference": reference_signal, "feedback": feedback_signal, "up": _first_list(roles, "up"), "down": _first_list(roles, "down")},
            {"edge": "rising"},
        )
        if has_bbpd or has_data_clock_lead_lag or "overlap" in lower or "reset race" in lower or "both outputs" in lower:
            add("pulse_non_overlap", 0.88, ["prompt requires up/dn not overlap significantly"], {"up": _first_list(roles, "up"), "down": _first_list(roles, "down")})
        if "pulse" in lower:
            add("pulse_width_window", 0.75, ["prompt describes pulse behavior"], {"up": _first_list(roles, "up"), "down": _first_list(roles, "down")})

    if "absolute timer grid" in lower or ("timer(" in lower and "tstart" in lower and "tstep" in lower):
        add(
            "absolute_event_window",
            0.94,
            ["prompt states absolute timer grid/target event times"],
            {"signal": "clk_out" if "clk_out" in signals else _first_list(roles, "analog_output")},
            {"target_times_s": _parse_target_times(prompt), "tran": tran},
        )
    if "$bound_step" in lower or "bound_step" in lower:
        add(
            "bounded_step_window",
            0.88,
            ["prompt requires bounded-step preservation of narrow periodic windows"],
            {"outputs": roles.get("analog_output", [])},
            {"tran": tran},
        )
    if (
        "parameter" in lower
        and not negates_parameter_override
        and (
            "finite pulse" in lower
            or "pulse train" in lower
            or "emitted pulses" in lower
            or ("override" in lower and "pulses" in lower)
        ) or has_claim("parameterized_repetition")
    ):
        add(
            "parameterized_event_sequence",
            0.86,
            ["prompt requires parameterized finite pulse/event behavior"],
            {"outputs": roles.get("analog_output", [])},
            {"tran": tran},
        )
    if "timer" in lower and ("@(timer" in lower or "timer-based" in lower):
        add(
            "timer_future_event_liveness",
            0.80 if "pll" not in lower else 0.76,
            ["prompt uses timer-driven output generation"],
            {"outputs": [s for s in signals if "clk" in s.lower() or s.lower().endswith("out")]},
            {"tran": tran},
        )

    if has_pll and (_first_list(roles, "reference_clock") or "ref_clk" in lower) and (_first_list(roles, "feedback_clock") or "fb_clk" in lower):
        add(
            "ratio_edge_window",
            0.91,
            ["prompt describes ref/fb frequency tracking"],
            {"reference": _first_list(roles, "reference_clock") or "ref_clk", "feedback": _first_list(roles, "feedback_clock") or "fb_clk"},
            {"expected_ratio": 1, "window": "late"},
        )
        if _first_list(roles, "lock") or "lock" in lower:
            add("lock_after_ratio_stable", 0.84, ["prompt requires lock assertion after convergence"], {"lock": _first_list(roles, "lock"), "reference": _first_list(roles, "reference_clock"), "feedback": _first_list(roles, "feedback_clock")})
        if "hop" in lower or "ratio" in lower and "change" in lower:
            add("ratio_hop_window", 0.80, ["prompt describes ratio/control hop behavior"], {"control": _first_list(roles, "control")})
    if "dco" in lower and ("frequency" in lower or "vctrl" in lower or "control-voltage" in lower):
        add(
            "control_to_frequency_step",
            0.84,
            ["prompt describes DCO/control-voltage frequency response"],
            {"control": _first_role_signal(roles, "control") or "vctrl", "output": _first_list(roles, "analog_output")},
            {"tran": tran},
        )

    has_sample_hold_phrase = bool(re.search(r"\bsample\s*/\s*hold\b|\bsample[- ]and[- ]hold\b|\bsample\s+hold\b", lower))
    if has_sample_hold_phrase:
        add(
            "droop_window" if "droop" in lower else "sample_hold_tracking",
            0.82,
            ["prompt describes sample/hold behavior"],
            {"input": "vin" if "vin" in signals else _first_list(roles, "analog_input"), "output": "vout" if "vout" in signals else _first_list(roles, "analog_output"), "clock": _first_list(roles, "clock")},
        )

    if ("calibration" in lower or "calibrate" in lower) and ("trim" in lower or "settled" in lower):
        add(
            "calibration_settling_code",
            0.87,
            ["prompt describes trim-code calibration and settled flag"],
            {"clock": _first_list(roles, "clock"), "comparator": "COMP_OUT" if "COMP_OUT" in signals else _first_list(roles, "analog_input"), "settled": _first_list(roles, "settled"), "trim_bits": _best_bits(roles, ("TRIM", "trim"))},
            {"settled_cycles": 8 if "8 consecutive" in lower else None},
        )

    if "comparator" in lower or "cmp" in lower:
        add("threshold_crossing", 0.74, ["prompt describes comparator/threshold behavior"], {"inputs": roles.get("analog_input", []), "outputs": roles.get("analog_output", [])})
        if "hysteresis" in lower:
            add("hysteresis_window", 0.80, ["prompt describes comparator hysteresis"], {"inputs": roles.get("analog_input", []), "outputs": roles.get("analog_output", [])})

    if ("and gate" in lower or "or gate" in lower or "not gate" in lower or "logic" in lower) and not specs:
        add("logic_truth_table", 0.78, ["prompt describes digital logic behavior"], {"inputs": roles.get("analog_input", []), "outputs": roles.get("analog_output", [])})

    if (
        "serializer" in lower
        or "parallel-to-serial" in lower
        or "parallel to serial" in lower
        or ("shift data out" in lower and "frame" in lower)
        or ("serialized bit" in lower and "frame" in lower)
        or has_claim("frame_aligned_serial_sequence")
    ):
        add("sequence_alignment", 0.78, ["prompt describes serializer/frame sequencing"], {"clock": _first_list(roles, "clock"), "outputs": roles.get("analog_output", [])})

    deduped_specs: dict[str, TemplateSpec] = {}
    for spec in specs:
        current = deduped_specs.get(spec.template)
        if current is None or spec.confidence > current.confidence:
            deduped_specs[spec.template] = spec
    specs = sorted(deduped_specs.values(), key=lambda item: item.confidence, reverse=True)
    payload_specs = [
        {
            "template": spec.template,
            "confidence": round(spec.confidence, 3),
            "signals": spec.signals,
            "parameters": {k: v for k, v in spec.parameters.items() if v is not None},
            "evidence": spec.evidence,
        }
        for spec in specs
    ]
    overall_confidence = max((spec.confidence for spec in specs), default=0.0)
    return {
        "task_id": task_id,
        "task_dir": str(task_dir.relative_to(ROOT)),
        "confidence": round(overall_confidence, 3),
        "signals_observed": signals,
        "signal_sources": {
            "prompt": True,
            "gold_save_names": bool(include_gold_save_names),
            "gold_save_name_count": len(gold_signals),
        },
        "roles": roles,
        "functional_ir": functional_ir,
        "templates": payload_specs,
        "tran": tran,
    }


def load_validation(path: Path | None) -> dict[str, dict]:
    if not path:
        return {}
    data = _read_json(path)
    return data.get("tasks", data)


def validate_spec(spec: dict, expected: dict | None) -> dict:
    inferred = {item["template"] for item in spec.get("templates", [])}
    required = set((expected or {}).get("required_templates", []))
    missing = sorted(required - inferred)
    return {
        "expected_templates": sorted(required),
        "inferred_templates": sorted(inferred),
        "matched": not missing if required else None,
        "missing_templates": missing,
    }


def render_markdown(summary: dict, records: list[dict]) -> str:
    lines = [
        "# Prompt Checker Spec Inference Report",
        "",
        "## Summary",
        "",
        f"- Tasks: `{summary['tasks']}`",
        f"- Validated tasks: `{summary['validated_tasks']}`",
        f"- Validation matches: `{summary['validation_matches']}`",
        f"- Mechanism match rate: `{summary['mechanism_match_rate']:.3f}`",
        f"- Adopted specs: `{summary['adopted_specs']}`",
        f"- Adopt threshold: `{summary['adopt_threshold']}`",
        "",
        "## Task Results",
        "",
        "| Task | Confidence | Adopted | Expected | Inferred | Missing |",
        "|---|---:|---:|---|---|---|",
    ]
    for record in records:
        validation = record.get("validation", {})
        expected = ", ".join(validation.get("expected_templates", [])) or "-"
        inferred = ", ".join(item["template"] for item in record.get("templates", [])[:5]) or "-"
        missing = ", ".join(validation.get("missing_templates", [])) or "-"
        lines.append(
            f"| `{record['task_id']}` | `{record['confidence']:.3f}` | `{str(record['adopted']).lower()}` | "
            f"{expected} | {inferred} | {missing} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--all", action="store_true", help="Infer specs for all prompt-bearing tasks; adoption still requires validation unless --adopt-unvalidated is set.")
    parser.add_argument("--task", action="append", default=[])
    parser.add_argument("--validation-set", type=Path, default=ROOT / "docs" / "PROMPT_CHECKER_SPEC_VALIDATION_SET.json")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results" / "prompt-checker-spec-inference")
    parser.add_argument("--adopted-out", type=Path, default=ROOT / "docs" / "PROMPT_CHECKER_SPECS_ADOPTED.json")
    parser.add_argument("--adopt-threshold", type=float, default=0.70)
    parser.add_argument("--adopt-unvalidated", action="store_true")
    parser.add_argument(
        "--include-gold-save-names",
        action="store_true",
        help="Compatibility mode for old audits. Live cold-start/I-clean inference should leave this disabled.",
    )
    args = parser.parse_args()

    validation = load_validation(args.validation_set if args.validation_set.exists() else None)
    selected = None if args.all else set(args.task) if args.task else set(validation) if validation else None
    tasks = list_task_dirs(selected=selected)
    if not tasks:
        raise SystemExit("No tasks selected")

    records: list[dict] = []
    adopted: list[dict] = []
    validation_total = 0
    validation_matches = 0
    for task_id, task_dir in tasks:
        record = infer_specs(task_id, task_dir, include_gold_save_names=args.include_gold_save_names)
        expected = validation.get(task_id)
        record["validation"] = validate_spec(record, expected)
        if expected:
            validation_total += 1
            if record["validation"]["matched"]:
                validation_matches += 1
        high_confidence = record["confidence"] >= args.adopt_threshold
        validation_ok = record["validation"]["matched"] is True or (args.adopt_unvalidated and record["validation"]["matched"] is None)
        record["adopted"] = bool(high_confidence and validation_ok)
        if record["adopted"]:
            adopted.append(
                {
                    "task_id": task_id,
                    "confidence": record["confidence"],
                    "templates": record["templates"],
                    "signals_observed": record["signals_observed"],
                    "roles": record["roles"],
                    "source": "prompt_checker_spec_inference",
                }
            )
        records.append(record)

    match_rate = validation_matches / validation_total if validation_total else 0.0
    summary = {
        "tasks": len(records),
        "validated_tasks": validation_total,
        "validation_matches": validation_matches,
        "mechanism_match_rate": round(match_rate, 4),
        "adopted_specs": len(adopted),
        "adopt_threshold": args.adopt_threshold,
        "validation_set": str(args.validation_set),
    }
    result = {"summary": summary, "records": records}
    adopted_payload = {
        "version": 1,
        "description": "Prompt-inferred checker specs adopted after validation. Advisory only; not official scoring gates.",
        "adopt_threshold": args.adopt_threshold,
        "summary": summary,
        "specs": adopted,
    }

    out_dir = args.output_dir
    _write_json(out_dir / "prompt_checker_specs.json", result)
    _write_json(out_dir / "prompt_checker_specs_adopted.json", adopted_payload)
    (out_dir / "README.md").write_text(render_markdown(summary, records), encoding="utf-8")
    if match_rate >= 0.80 and adopted:
        _write_json(args.adopted_out, adopted_payload)

    print(json.dumps(summary, indent=2))
    if match_rate < 0.80:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
