#!/usr/bin/env python3
"""
score.py — Score model-generated Verilog-A candidates against the vaEvas benchmark.

Takes generated DUT and/or testbench files (from generate.py or hand-written)
and runs them through the existing EVAS scoring pipeline.

Expected generated directory layout (output of generate.py):
  <generated-dir>/<model>/<task_id>/sample_<idx>/
    ├── *.va              (generated DUT — for spec-to-va, bugfix, end-to-end)
    ├── tb_*.scs          (generated testbench — for end-to-end, tb-generation)
    └── generation_meta.json   (metadata from generate.py)

For families that only generate one artifact:
  spec-to-va, bugfix   → generated DUT + gold testbench from task/gold/
  tb-generation        → gold DUT + generated testbench
  end-to-end           → both generated DUT and testbench

Outputs:
  <output-dir>/<model>/<task_id>/sample_<idx>/result.json   per-task result
  <output-dir>/<model>/model_results.json                   aggregate summary

Usage:
  cd behavioral-veriloga-eval
  python runners/score.py --model claude-sonnet-4-6 --generated-dir generated/
  python runners/score.py --model gpt-4o --task digital_basics_smoke --generated-dir generated/
  python runners/score.py --model claude-sonnet-4-6 --all --family spec-to-va --generated-dir generated/
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from failure_attribution import attach_failure_attribution
from interface_parameter_guard import check_interface_parameter_paths, format_issue_notes
from simulate_evas import has_behavior_check, run_case

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]
ALL_FAMILIES = ("end-to-end", "spec-to-va", "bugfix", "tb-generation")

def family_task_root(family: str) -> Path:
    base = ROOT / "tasks"
    mapping = {
        "end-to-end": base / "end-to-end" / "voltage",
        "spec-to-va": base / "spec-to-va" / "voltage",
        "bugfix": base / "bugfix" / "voltage",
        "tb-generation": base / "tb-generation" / "voltage",
    }
    return mapping[family]


def read_meta(task_dir: Path) -> dict:
    return json.loads((task_dir / "meta.json").read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Task and generated-file discovery
# ---------------------------------------------------------------------------

def list_all_task_dirs(families: tuple[str, ...] = ALL_FAMILIES,
                       selected: set[str] | None = None) -> list[tuple[str, Path]]:
    """Return (task_id, task_dir) pairs for all tasks with gold/ directories."""
    result = []
    for family in families:
        root = family_task_root(family)
        if not root.exists():
            continue
        for meta_path in sorted(root.rglob("meta.json")):
            task_dir = meta_path.parent
            if not (task_dir / "gold").is_dir():
                continue
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            task_id = meta.get("task_id") or meta.get("id") or task_dir.name
            if selected and task_id not in selected:
                continue
            # Skip scope-guard tasks by default (they have no LLM prompt intent)
            if meta.get("tier") == "scope-guard":
                continue
            result.append((task_id, task_dir))
    return result


def list_bench_task_dirs(
    bench_dir: Path,
    families: tuple[str, ...] = ALL_FAMILIES,
    selected: set[str] | None = None,
) -> list[tuple[str, Path]]:
    """Return scoreable task dirs from a benchmark root such as benchmark-balanced/."""
    task_root = bench_dir / "tasks"
    result: list[tuple[str, Path]] = []
    family_set = set(families)
    for meta_path in sorted(task_root.glob("*/meta.json")):
        task_dir = meta_path.parent
        if not (task_dir / "gold").is_dir():
            continue
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        family = meta.get("family", "end-to-end")
        if family not in family_set:
            continue
        task_id = meta.get("task_id") or meta.get("id") or task_dir.name
        if selected and task_id not in selected:
            continue
        if meta.get("tier") == "scope-guard":
            continue
        result.append((task_id, task_dir))
    return result


def _checks_yaml_declares_sim_correct(task_dir: Path) -> bool:
    checks_path = task_dir / "checks.yaml"
    if not checks_path.exists():
        return False
    text = checks_path.read_text(encoding="utf-8", errors="ignore")
    return bool(re.search(r"(?m)^\s*sim_correct\s*:\s*$", text))


def _audit_checker_contract(task_list: list[tuple[str, Path]]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    for task_id, task_dir in task_list:
        meta = read_meta(task_dir)
        scoring = meta.get("scoring", ["dut_compile", "tb_compile", "sim_correct"])
        requires_sim = "sim_correct" in scoring
        has_check = has_behavior_check(task_id)
        yaml_has_sim = _checks_yaml_declares_sim_correct(task_dir)

        if requires_sim and not has_check:
            errors.append(task_id)
        if yaml_has_sim and not has_check:
            warnings.append(f"{task_id}: checks.yaml declares sim_correct but CHECKS has no entry")
    return errors, warnings


def find_generated_dir(generated_root: Path, model: str, task_id: str,
                       sample_idx: int) -> Path | None:
    """Return the sample directory for a (model, task_id, sample_idx) triple."""
    candidate = generated_root / model / task_id / f"sample_{sample_idx}"
    return candidate if candidate.is_dir() else None


def find_va_file(sample_dir: Path) -> Path | None:
    """Return the first .va file found in a sample directory."""
    vas = sorted(sample_dir.glob("*.va"))
    return vas[0] if vas else None


def find_tb_file(sample_dir: Path) -> Path | None:
    """Return the first .scs file found in a sample directory (prefer tb_*.scs)."""
    preferred = sorted(sample_dir.glob("tb_*.scs"))
    if preferred:
        return preferred[0]
    fallbacks = sorted(sample_dir.glob("*.scs"))
    return fallbacks[0] if fallbacks else None


def choose_gold_tb(gold_dir: Path) -> Path | None:
    preferred = sorted(gold_dir.glob("tb*_ref.scs"))
    if preferred:
        return preferred[0]
    fallbacks = sorted(gold_dir.glob("tb*.scs"))
    return fallbacks[0] if fallbacks else None


def ahdl_includes(tb_path: Path) -> list[str]:
    text = tb_path.read_text(encoding="utf-8")
    return re.findall(r'^\s*ahdl_include\s+"([^"]+)"', text, flags=re.MULTILINE)


def save_signals(tb_path: Path) -> list[str]:
    """Extract signal names from save statement in Spectre testbench.

    Handles formats:
    - save a y          -> ["a", "y"]
    - save v(a) v(y)    -> ["a", "y"]
    - save all          -> []  (wildcard, not parsed)
    """
    text = tb_path.read_text(encoding="utf-8")
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("save "):
            rest = stripped[5:].strip()
            if rest.lower() == "all":
                return []  # wildcard, cannot determine specific signals
            signals = []
            for token in rest.split():
                token = token.strip()
                if not token:
                    continue
                # Handle v(sig) format
                match = re.match(r"v\s*\(\s*([^)]+)\s*\)", token, re.IGNORECASE)
                if match:
                    signals.append(match.group(1))
                else:
                    # Plain signal name (could be node or bus)
                    signals.append(token)
            return signals
    return []


def all_save_signals(tb_path: Path) -> list[str] | None:
    """Return all explicit saved signal tokens, or None for wildcard saves.

    Unlike save_signals(), this scans every save line so contract pruning can
    preserve multi-line save lists.  A wildcard save is intentionally ambiguous,
    so callers should preserve the original save directives in that case.
    """
    text = tb_path.read_text(encoding="utf-8", errors="ignore").replace("\\\n", " ")
    signals: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.lower().startswith("save "):
            continue
        rest = stripped[5:].strip()
        if rest.lower() in {"all", "allpub"}:
            return None
        for token in rest.split():
            token = token.strip().strip(",")
            if not token:
                continue
            match = re.match(r"v\s*\(\s*([^)]+)\s*\)", token, re.IGNORECASE)
            signals.append(match.group(1) if match else token)

    deduped: list[str] = []
    seen: set[str] = set()
    for signal in signals:
        if signal not in seen:
            seen.add(signal)
            deduped.append(signal)
    return deduped


def tb_structure(tb_path: Path) -> dict:
    """Extract structural metadata from a Spectre testbench.

    Returns:
        {
            "ahdl_includes": ["not_gate.va", ...],
            "save_signals": ["a", "y", ...],
            "modules": ["not_gate", ...],  # stem of .va includes
        }
    """
    includes = ahdl_includes(tb_path)
    signals = save_signals(tb_path)
    modules = [Path(inc).stem for inc in includes if Path(inc).suffix.lower() == ".va"]
    return {
        "ahdl_includes": includes,
        "save_signals": signals,
        "modules": modules,
    }


def normalize_tb_save_signals(tb_path: Path) -> int:
    """Rewrite hierarchical save tokens to flat node names for stable CSV headers.

    Example:
      save adpll:ref_clk adpll:fb_clk  -> save ref_clk fb_clk
      save xdut.clk_in xdut.div_out    -> save clk_in div_out
    """
    original_lines = tb_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    updated_lines: list[str] = []
    rewrite_count = 0

    for line in original_lines:
        stripped = line.strip()
        if not stripped.lower().startswith("save "):
            updated_lines.append(line)
            continue
        indent = line[: len(line) - len(line.lstrip())]
        parts = stripped.split()
        if len(parts) <= 1:
            updated_lines.append(line)
            continue

        rewritten = [parts[0]]
        for token in parts[1:]:
            norm = token
            low = token.lower()
            if (
                token in {"\\", ","}
                or "*" in token
                or token.startswith("V(")
                or token.startswith("I(")
                or low in {"all", "allpub", "options"}
                or low.startswith("save=")
            ):
                rewritten.append(norm)
                continue
            if ":" in norm:
                norm = norm.split(":")[-1]
            if "." in norm:
                norm = norm.split(".")[-1]
            if norm != token:
                rewrite_count += 1
            rewritten.append(norm)

        updated_lines.append(indent + " ".join(rewritten))

    if rewrite_count > 0:
        tb_path.write_text("\n".join(updated_lines) + "\n", encoding="utf-8")
    return rewrite_count


def rewrite_tb_save_signals(tb_path: Path, desired_signals: list[str]) -> tuple[int, int]:
    """Replace save directives with a compact explicit list.

    Returns (removed_save_lines, inserted_save_lines).  An empty desired list
    removes all save directives, useful when the scoring contract does not need
    behavior/CSV inspection.
    """
    original_lines = tb_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    updated_lines: list[str] = []
    removed = 0
    inserted = 0
    inserted_save = False
    idx = 0
    while idx < len(original_lines):
        line = original_lines[idx]
        stripped = line.strip()
        if not stripped.lower().startswith("save "):
            updated_lines.append(line)
            idx += 1
            continue
        removed += 1
        if desired_signals and not inserted_save:
            indent = line[: len(line) - len(line.lstrip())]
            updated_lines.append(indent + "save " + " ".join(desired_signals))
            inserted += 1
            inserted_save = True
        idx += 1
        # A Spectre save statement may span multiple physical lines using a
        # trailing backslash.  Once the first save line is replaced/removed,
        # all continuation lines must be removed too; otherwise real Spectre
        # can parse the orphaned continuation as a new instance line.
        while idx < len(original_lines) and original_lines[idx - 1].rstrip().endswith("\\"):
            removed += 1
            idx += 1

    if removed > 0 or inserted > 0:
        tb_path.write_text("\n".join(updated_lines) + "\n", encoding="utf-8")
    return removed, inserted


def _safe_inc_path(stage_dir: Path, inc_name: str) -> Path:
    inc = Path(inc_name)
    if inc.is_absolute() or ".." in inc.parts:
        return stage_dir / inc.name
    return stage_dir / inc


def _copy_as(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def _copy_if_exists(src: Path, dst: Path) -> bool:
    if src.exists():
        _copy_as(src, dst)
        return True
    return False


def _sample_ref_alias(sample_dir: Path, inc_name: str) -> Path | None:
    """Return an emitted sample file that safely satisfies a missing *_ref include.

    End-to-end repair sometimes preserves the benchmark TB while emitting public
    DUT filenames without the verifier `_ref` suffix, for example a TB include
    `dac_ideal_4b_ref.va` beside an emitted `dac_ideal_4b.va`.  This alias is
    safe only when the include stem differs by exactly `_ref`; otherwise callers
    should keep the missing-include failure visible.
    """
    inc = Path(inc_name)
    if inc.suffix.lower() != ".va" or not inc.stem.endswith("_ref"):
        return None

    alias_name = inc.with_name(inc.stem[: -len("_ref")] + inc.suffix)
    candidates = [
        sample_dir / alias_name,
        sample_dir / alias_name.name,
    ]
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


SPECTRE_PRIMITIVE_MODELS = {
    "bsource",
    "capacitor",
    "cccs",
    "ccvs",
    "diode",
    "inductor",
    "iprobe",
    "isource",
    "port",
    "resistor",
    "switch",
    "vccs",
    "vcvs",
    "vsource",
}


def _strip_line_comments(text: str) -> str:
    return "\n".join(line.split("//", 1)[0] for line in text.splitlines())


def verilog_module_names(va_path: Path) -> list[str]:
    text = va_path.read_text(encoding="utf-8", errors="ignore")
    return re.findall(r"\bmodule\s+([A-Za-z_][A-Za-z0-9_$]*)\b", text)


def spectre_instance_models(tb_path: Path) -> list[str]:
    text = tb_path.read_text(encoding="utf-8", errors="ignore")
    text = _strip_line_comments(text.replace("\\\n", " "))
    models: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.lower().startswith(("simulator ", "global ", "ahdl_include", "save ", "tran ")):
            continue
        match = re.match(r"^[A-Za-z_][A-Za-z0-9_.$]*\s*\([^)]*\)\s+([A-Za-z_][A-Za-z0-9_.$]*)\b", stripped)
        if not match:
            continue
        model = match.group(1)
        if model.lower() not in SPECTRE_PRIMITIVE_MODELS:
            models.append(model)
    return models


def _module_port_orders(va_paths: list[Path]) -> dict[str, list[str]]:
    """Return Verilog-A module port order keyed by module name."""
    orders: dict[str, list[str]] = {}
    keywords = {"input", "output", "inout", "electrical", "wire", "real", "integer"}
    for va_path in va_paths:
        text = _strip_line_comments(va_path.read_text(encoding="utf-8", errors="ignore"))
        for match in re.finditer(r"\bmodule\s+([A-Za-z_][A-Za-z0-9_$]*)\s*\((.*?)\)\s*;", text, flags=re.DOTALL):
            module = match.group(1)
            ports: list[str] = []
            for raw_item in match.group(2).replace("\n", " ").split(","):
                item = re.sub(r"\[[^\]]+\]", " ", raw_item)
                tokens = [tok for tok in re.split(r"\s+", item.strip()) if tok]
                candidates = [
                    tok
                    for tok in tokens
                    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_$]*", tok) and tok.lower() not in keywords
                ]
                if candidates:
                    width = 1
                    range_match = re.search(r"\[\s*(\d+)\s*:\s*(\d+)\s*\]", raw_item)
                    if range_match:
                        width = abs(int(range_match.group(1)) - int(range_match.group(2))) + 1
                    ports.extend([candidates[-1]] * width)
            orders[module] = ports
    return orders


def _spectre_instance_records(tb_path: Path) -> list[tuple[int, str, list[str], str, str]]:
    """Return `(lineno, instance, nodes, model, tail)` for Spectre instances."""
    text = _strip_line_comments(tb_path.read_text(encoding="utf-8", errors="ignore"))
    records: list[tuple[int, str, list[str], str, str]] = []
    pending = ""
    start_lineno = 0
    skip_prefixes = ("simulator ", "global ", "ahdl_include", "include ", "save ", "tran ", "parameters ")

    for lineno, raw_line in enumerate(text.splitlines(), start=1):
        stripped = raw_line.strip()
        if not stripped:
            continue
        if pending:
            pending += " " + stripped.rstrip("\\").strip()
        else:
            start_lineno = lineno
            pending = stripped.rstrip("\\").strip()
        if stripped.endswith("\\"):
            continue

        lowered = pending.lower()
        if not lowered.startswith(skip_prefixes):
            match = re.match(
                r"^([A-Za-z_][A-Za-z0-9_.$]*)\s*\(([^)]*)\)\s+([A-Za-z_][A-Za-z0-9_.$]*)\b(.*)$",
                pending,
            )
            if match:
                inst = match.group(1)
                nodes = [node for node in re.split(r"\s+", match.group(2).strip()) if node]
                records.append((start_lineno, inst, nodes, match.group(3), match.group(4).strip()))
        pending = ""
        start_lineno = 0

    return records


def spectre_instance_port_count_mismatch_lines(tb_path: Path, va_paths: list[Path]) -> list[str]:
    module_ports = _module_port_orders(va_paths)
    bad: list[str] = []
    for lineno, inst, nodes, model, _tail in _spectre_instance_records(tb_path):
        if model.lower() in SPECTRE_PRIMITIVE_MODELS or model not in module_ports:
            continue
        ports = module_ports[model]
        if len(nodes) != len(ports):
            bad.append(f"{lineno}:{inst}:{model}:nodes={len(nodes)}:ports={len(ports)}")
    return bad


def spectre_parameters_keyword_instance_lines(tb_path: Path) -> list[str]:
    bad: list[str] = []
    for lineno, inst, _nodes, model, tail in _spectre_instance_records(tb_path):
        if model.lower() in SPECTRE_PRIMITIVE_MODELS:
            continue
        if re.search(r"\bparameters\b", tail):
            bad.append(f"{lineno}:{inst}:{model}:parameters_keyword")
    return bad


def _spectre_vsource_nodes(tb_path: Path) -> set[str]:
    nodes: set[str] = {"0"}
    text = _strip_line_comments(tb_path.read_text(encoding="utf-8", errors="ignore"))
    pattern = re.compile(r"^\s*[A-Za-z_][A-Za-z0-9_.$]*\s*\(([^)]*)\)\s+vsource\b", re.IGNORECASE)
    for line in text.splitlines():
        match = pattern.search(line)
        if not match:
            continue
        parts = [node for node in re.split(r"\s+", match.group(1).strip()) if node]
        nodes.update(parts[:2])
    return nodes


def _module_single_ended_voltage_drives(va_paths: list[Path]) -> dict[str, set[str]]:
    drives: dict[str, set[str]] = {}
    for va_path in va_paths:
        text = _strip_line_comments(va_path.read_text(encoding="utf-8", errors="ignore"))
        modules = list(re.finditer(r"\bmodule\s+([A-Za-z_][A-Za-z0-9_$]*)\b", text))
        if not modules:
            continue
        for idx, match in enumerate(modules):
            module = match.group(1)
            start = match.end()
            end = modules[idx + 1].start() if idx + 1 < len(modules) else len(text)
            body = text[start:end]
            hits = set()
            for drive in re.finditer(r"\bV\s*\(\s*([A-Za-z_][A-Za-z0-9_$]*)\s*\)\s*<\+", body):
                hits.add(drive.group(1))
            if hits:
                drives.setdefault(module, set()).update(hits)
    return drives


def spectre_sourced_port_drive_hits(tb_path: Path, va_paths: list[Path]) -> list[str]:
    """Detect Verilog-A ports driven while mapped to a vsource-fixed node."""
    source_nodes = _spectre_vsource_nodes(tb_path)
    if not source_nodes:
        return []
    module_ports = _module_port_orders(va_paths)
    module_drives = _module_single_ended_voltage_drives(va_paths)
    bad: list[str] = []
    for lineno, inst, nodes, model, _tail in _spectre_instance_records(tb_path):
        ports = module_ports.get(model)
        drives = module_drives.get(model)
        if not ports or not drives:
            continue
        for idx, port in enumerate(ports):
            if port not in drives or idx >= len(nodes):
                continue
            node = nodes[idx]
            if node in source_nodes:
                bad.append(f"{lineno}:{inst}:{model}:{port}->{node}")
    return bad


def spectre_colon_instance_lines(tb_path: Path) -> list[int]:
    text = _strip_line_comments(tb_path.read_text(encoding="utf-8", errors="ignore"))
    bad_lines: list[int] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        if re.match(r"^[A-Za-z_][A-Za-z0-9_.$]*\s*:", stripped):
            bad_lines.append(lineno)
    return bad_lines


def spectre_unsupported_directive_lines(tb_path: Path) -> list[str]:
    text = _strip_line_comments(tb_path.read_text(encoding="utf-8", errors="ignore"))
    bad: list[str] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        lowered = stripped.lower()
        if lowered.startswith("plot "):
            bad.append(f"{lineno}:plot")
        if "{" in stripped or "}" in stripped:
            bad.append(f"{lineno}:curly_block")
        if "'" in stripped:
            bad.append(f"{lineno}:single_quote")
    return bad


def spectre_reversed_source_syntax_lines(tb_path: Path) -> list[str]:
    """Detect reversed Spectre primitive syntax such as `vsource vdd (...)`.

    Spectre instance syntax is `Vname (node 0) vsource ...`.  EVAS may be able
    to salvage the intent of the reversed form, but real Spectre interprets the
    line as an instance named `vsource` and often reports undefined model `0` or
    duplicate instance failures.
    """
    text = _strip_line_comments(tb_path.read_text(encoding="utf-8", errors="ignore"))
    bad: list[str] = []
    pattern = re.compile(r"^\s*(?:vsource|isource)\s+[A-Za-z_][A-Za-z0-9_.$]*\s*\(", re.IGNORECASE)
    for lineno, line in enumerate(text.splitlines(), start=1):
        if pattern.search(line):
            compact = re.sub(r"\s+", " ", line.strip())
            bad.append(f"{lineno}:{compact}")
    return bad


def spectre_pulse_nonpositive_timing_lines(tb_path: Path) -> list[str]:
    """Detect pulse sources with zero rise/fall time.

    The bridge's real Spectre rejects `type=pulse ... fall=0` during hierarchy
    flattening.  Keep this in preflight so EVAS does not accept a candidate that
    cannot run in Spectre.
    """
    text = _strip_line_comments(tb_path.read_text(encoding="utf-8", errors="ignore"))
    bad: list[str] = []
    pattern = re.compile(
        r"\btype\s*=\s*pulse\b.*\b(rise|fall)\s*=\s*0(?:\.0*)?(?:\s|$|[fpnum]?s\b)",
        re.IGNORECASE,
    )
    for lineno, line in enumerate(text.splitlines(), start=1):
        match = pattern.search(line)
        if not match:
            continue
        compact = re.sub(r"\s+", " ", line.strip())
        bad.append(f"{lineno}:{match.group(1).lower()}=0:{compact}")
    return bad


def _spectre_numeric_token(token: str) -> float | None:
    token = token.strip().strip("{}")
    match = re.fullmatch(
        r"([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)([A-Za-z]*)",
        token,
    )
    if not match:
        return None
    value = float(match.group(1))
    suffix = match.group(2).lower()
    scale = {
        "": 1.0,
        "s": 1.0,
        "f": 1e-15,
        "fs": 1e-15,
        "p": 1e-12,
        "ps": 1e-12,
        "n": 1e-9,
        "ns": 1e-9,
        "u": 1e-6,
        "us": 1e-6,
        "m": 1e-3,
        "ms": 1e-3,
        "k": 1e3,
        "meg": 1e6,
        "g": 1e9,
        "t": 1e12,
    }.get(suffix)
    if scale is None:
        return None
    return value * scale


def _spectre_pwl_wave_blocks(tb_path: Path) -> list[tuple[int, str, str]]:
    """Return `(start_lineno, body, compact_first_line)` for PWL wave blocks."""
    text = _strip_line_comments(tb_path.read_text(encoding="utf-8", errors="ignore"))
    blocks: list[tuple[int, str, str]] = []
    collecting = False
    start_lineno = 0
    first_line = ""
    parts: list[str] = []
    start_re = re.compile(r"\btype\s*=\s*pwl\b.*?\bwave\s*=\s*\[", re.IGNORECASE)

    for lineno, line in enumerate(text.splitlines(), start=1):
        if not collecting:
            match = start_re.search(line)
            if not match:
                continue
            collecting = True
            start_lineno = lineno
            first_line = re.sub(r"\s+", " ", line.strip())
            tail = line[match.end():]
        else:
            tail = line

        if "]" in tail:
            before, _after = tail.split("]", 1)
            parts.append(before)
            blocks.append((start_lineno, "\n".join(parts), first_line))
            collecting = False
            start_lineno = 0
            first_line = ""
            parts = []
        else:
            parts.append(tail)

    if collecting:
        blocks.append((start_lineno, "\n".join(parts), first_line))
    return blocks


def spectre_malformed_pwl_wave_lines(tb_path: Path) -> list[str]:
    """Detect PWL wave lists that are not simple time/value pairs.

    Spectre PWL sources in these benchmarks should use a flat `wave=[t0 v0
    t1 v1 ...]` list.  An odd token count usually means the model mixed up a
    time and a value, which EVAS later reports only as `tran.csv missing`.
    """
    bad: list[str] = []
    for lineno, body, compact in _spectre_pwl_wave_blocks(tb_path):
        body = body.replace(",", " ").replace("\\", " ")
        tokens = [tok for tok in re.split(r"\s+", body.strip()) if tok]
        if len(tokens) < 4 or len(tokens) % 2 != 0:
            bad.append(f"{lineno}:tokens={len(tokens)}:{compact}")
    return bad


def spectre_nonincreasing_pwl_time_lines(tb_path: Path) -> list[str]:
    """Detect PWL time vectors that real Spectre rejects.

    Cadence Spectre requires PWL times to be strictly increasing; duplicate
    timestamps that EVAS could treat as ideal steps fail with CMI-2204.
    """
    bad: list[str] = []
    for lineno, body, compact in _spectre_pwl_wave_blocks(tb_path):
        tokens = [tok for tok in re.split(r"\s+", body.replace(",", " ").replace("\\", " ").strip()) if tok]
        if len(tokens) < 4 or len(tokens) % 2 != 0:
            continue
        times: list[float] = []
        parse_failed = False
        for tok in tokens[0::2]:
            value = _spectre_numeric_token(tok)
            if value is None:
                parse_failed = True
                break
            times.append(value)
        if parse_failed:
            continue
        for idx in range(1, len(times)):
            if times[idx] <= times[idx - 1]:
                bad.append(
                    f"{lineno}:t{idx - 1}={times[idx - 1]:.6g},t{idx}={times[idx]:.6g}:{compact}"
                )
                break
    return bad


def spectre_uncontinued_multiline_instance_lines(tb_path: Path) -> list[str]:
    """Detect bare multiline instance node lists that Spectre does not join.

    EVAS historically joined parenthesized lines, but Spectre requires an
    explicit trailing `\\` for instance/source continuations.
    """
    text = _strip_line_comments(tb_path.read_text(encoding="utf-8", errors="ignore"))
    bad: list[str] = []
    skip_prefixes = (
        "simulator ",
        "global ",
        "parameters ",
        "ahdl_include",
        "include ",
        "save ",
        "tran ",
    )
    for lineno, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.lower().startswith(skip_prefixes):
            continue
        if stripped.endswith("\\"):
            continue
        if re.match(r"^[A-Za-z_][A-Za-z0-9_.$]*\s*\(", stripped) and ")" not in stripped:
            compact = re.sub(r"\s+", " ", stripped)
            bad.append(f"{lineno}:{compact}")
    return bad


def _has_verilog_initial_begin(va_path: Path) -> bool:
    text = va_path.read_text(encoding="utf-8", errors="ignore")
    return bool(re.search(r"(?m)^\s*initial\s+begin\b", _strip_line_comments(text)))


def _module_header_backslash_continuation_hits(va_path: Path) -> list[str]:
    """Detect shell-style `\` continuations inside Verilog-A module headers.

    Spectre testbenches require backslashes for continued instance lines, but
    Verilog-A module declarations do not.  A generated header such as
    `module foo (a, \` can pass EVAS parsing heuristics while Spectre VACOMP
    reports a syntax error during AHDL read-in.
    """
    lines = _strip_line_comments(va_path.read_text(encoding="utf-8", errors="ignore")).splitlines()
    hits: list[str] = []
    in_header = False
    header_start = 0
    for lineno, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not in_header and re.search(r"\bmodule\s+[A-Za-z_][A-Za-z0-9_$]*\s*\(", stripped):
            in_header = True
            header_start = lineno
        if not in_header:
            continue
        if stripped.endswith("\\"):
            compact = re.sub(r"\s+", " ", stripped)
            hits.append(f"{va_path.name}:{lineno}:header_start={header_start}:{compact}")
        if re.search(r"\)\s*;", stripped):
            in_header = False
            header_start = 0
    return hits


def _has_transition_inside_conditional(va_path: Path) -> bool:
    """Heuristic for a Spectre AHDL restriction EVAS may otherwise miss."""
    text = _strip_line_comments(va_path.read_text(encoding="utf-8", errors="ignore"))
    pattern = re.compile(
        r"\b(?:if|else)\b[^{;]*\bbegin\b(?:(?!\bend\b).)*\btransition\s*\(",
        flags=re.DOTALL,
    )
    single_line = re.compile(
        r"\b(?:if|else)\b[^\n;]*\n\s*V\s*\([^;]+<\+\s*transition\s*\(",
        flags=re.DOTALL,
    )
    return bool(pattern.search(text) or single_line.search(text))


def _conditional_cross_hits(va_path: Path) -> list[str]:
    text = _strip_line_comments(va_path.read_text(encoding="utf-8", errors="ignore"))
    hits: list[str] = []
    inline_pattern = re.compile(r"\b(?:if|else)\b[^{;\n]*@\s*\(\s*cross\s*\(")
    block_pattern = re.compile(
        r"\b(?:if|else)\b[^{;]*\bbegin\b(?:(?!\bend\b).)*@\s*\(\s*cross\s*\(",
        flags=re.DOTALL,
    )
    if block_pattern.search(text):
        for lineno, line in enumerate(text.splitlines(), start=1):
            if re.search(r"\b(?:if|else)\b", line):
                hits.append(f"{va_path.name}:{lineno}:conditional_block")
                break
    for lineno, line in enumerate(text.splitlines(), start=1):
        if inline_pattern.search(line):
            compact = re.sub(r"\s+", " ", line.strip())
            hits.append(f"{va_path.name}:{lineno}:{compact}")
    return hits


def _genvar_inside_analog_hits(va_path: Path) -> list[str]:
    text = _strip_line_comments(va_path.read_text(encoding="utf-8", errors="ignore"))
    in_analog = False
    hits: list[str] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if re.search(r"\banalog\s+begin\b", stripped):
            in_analog = True
        if in_analog and re.search(r"\bgenvar\b", stripped):
            compact = re.sub(r"\s+", " ", stripped)
            hits.append(f"{va_path.name}:{lineno}:{compact}")
        if in_analog and re.match(r"^endmodule\b", stripped):
            in_analog = False
    return hits


def _dynamic_analog_vector_index_hits(va_path: Path) -> list[str]:
    text = _strip_line_comments(va_path.read_text(encoding="utf-8", errors="ignore"))
    integer_vars = set()
    for decl in re.findall(r"\binteger\s+([^;]+);", text):
        for name in re.split(r"[, ]+", decl):
            name = name.strip()
            if re.match(r"^[A-Za-z_][A-Za-z0-9_$]*$", name):
                integer_vars.add(name)
    hits: list[str] = []
    lines = text.splitlines()
    for var in integer_vars:
        pattern = re.compile(rf"\bV\s*\(([^)]*\[\s*{re.escape(var)}\s*\][^)]*)\)")
        for lineno, line in enumerate(lines, start=1):
            for match in pattern.finditer(line):
                expr = re.sub(r"\s+", "", match.group(1))
                hits.append(f"{va_path.name}:{lineno}:{var}:{expr}")
    return hits


def _has_dynamic_analog_vector_index(va_path: Path) -> bool:
    return bool(_dynamic_analog_vector_index_hits(va_path))


def _embedded_declaration_hits(va_path: Path) -> list[str]:
    """Detect declarations after executable statements in an analog block."""
    text = _strip_line_comments(va_path.read_text(encoding="utf-8", errors="ignore"))
    hits: list[str] = []
    in_analog = False
    seen_statement = False
    declaration_pattern = re.compile(r"^\s*(?:real|integer)\s+[A-Za-z_][A-Za-z0-9_$]*(?:\s*[,;\[]|$)")

    for lineno, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        if re.search(r"\banalog\s+begin\b", stripped):
            in_analog = True
            seen_statement = False
            continue
        if not in_analog:
            continue
        if re.match(r"^endmodule\b", stripped):
            in_analog = False
            seen_statement = False
            continue
        if declaration_pattern.match(stripped):
            if seen_statement:
                compact = re.sub(r"\s+", " ", stripped)
                hits.append(f"{va_path.name}:{lineno}:{compact}")
            continue
        if re.match(r"^(begin|end)\b", stripped):
            continue
        seen_statement = True
    return hits


def _has_digital_verilog_syntax(va_path: Path) -> list[str]:
    """Detect digital Verilog/SystemVerilog constructs that EVAS tolerates but Spectre VACOMP rejects.

    Returns a list of all offending patterns found (empty list if clean).
    All issues are reported so the repair prompt can address them all at once.
    """
    text = _strip_line_comments(va_path.read_text(encoding="utf-8", errors="ignore"))
    issues: list[str] = []

    # SystemVerilog parameterized module header: module foo #( ...
    if re.search(r"\bmodule\s+\w+\s*#\s*\(", text):
        issues.append("sv_param_header: module name #()")

    # Digital 'reg' declaration (not inside a string or comment)
    has_reg_decl = bool(re.search(r"(?m)^\s*reg\s+", text))
    if has_reg_decl:
        issues.append("digital_reg_decl: reg keyword")

    # Digital always block
    if re.search(r"\balways\s*@\s*\(", text):
        issues.append("digital_always_block: always @(")

    # Packed bit-select on *scalar* integer variables: var[N] = ...
    # Valid Verilog-A allows integer/real array element access (integer arr[0:9]; arr[3] = 1)
    # but NOT bit-select on a scalar integer (integer x; x[0] = 1 is SystemVerilog, not Verilog-A).
    # Strategy: collect all names declared as arrays, then flag var[N] assignments where
    # var is NOT an array.
    _array_names: set[str] = set(re.findall(
        r"\b(?:integer|real)\s+(\w+)\s*\[", text
    ))
    # Find assignment-side bit-select: varname[digit] =
    _bit_sel_assigns = re.findall(r"\b(\w+)\s*\[\s*\d+\s*\]\s*=", text)
    _bad_bit_sel = [v for v in _bit_sel_assigns if v not in _array_names]
    if _bad_bit_sel:
        issues.append(f"packed_bit_select: scalar-integer bit-indexing ({', '.join(sorted(set(_bad_bit_sel)))}[N] = ...)")

    # Shift operators are invalid on reg-type variables; valid on integer.
    # Flag only when reg is present AND no integer declaration (shift is on a digital type).
    if re.search(r"<<|>>", text):
        has_integer_decl = bool(re.search(r"\binteger\s+\w", text))
        if has_reg_decl and not has_integer_decl:
            issues.append("shift_operator_on_reg: << or >> with reg declaration")

    if re.search(r"\binteger\s*\(", text):
        issues.append("integer_function_cast: integer(...)")

    return issues


def _direct_filename_fileio_hits(va_path: Path) -> list[str]:
    """Detect Spectre-incompatible file I/O using a string as the descriptor.

    EVAS can defensively accept `$fstrobe("file", ...)` to avoid crashing on
    malformed output code, but Spectre VACOMP requires an integer descriptor
    returned by `$fopen`.  Keep this in strict preflight so EVAS compatibility
    does not turn into a false Spectre-compatible pass.
    """
    text = _strip_line_comments(va_path.read_text(encoding="utf-8", errors="ignore"))
    pattern = re.compile(r"\$(fstrobe|fwrite|fdisplay)\s*\(\s*\"([^\"]+)\"")
    hits: list[str] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        for match in pattern.finditer(line):
            func = match.group(1)
            filename = match.group(2)
            hits.append(f"{va_path.name}:{lineno}:${func}(\"{filename}\",...)")
    return hits


def _combined_direction_discipline_hits(va_path: Path) -> list[str]:
    """Detect direction/discipline declarations Spectre VACOMP rejects.

    EVAS accepts compact declarations like `input electrical vin;`, but the
    Spectre version used by the bridge reports VACOMP-2259/VACOMP-2418 for
    these.  The Spectre-compatible form separates direction and discipline,
    e.g. `input vin; electrical vin;`.
    """
    text = _strip_line_comments(va_path.read_text(encoding="utf-8", errors="ignore"))
    hits: list[str] = []
    pattern = re.compile(r"^\s*(input|output|inout)\s+electrical\b", re.IGNORECASE)
    in_module_header = False
    for lineno, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if re.search(r"\bmodule\b", stripped):
            in_module_header = not bool(re.search(r"\)\s*;", stripped))
            continue
        if in_module_header:
            if re.search(r"\)\s*;", stripped):
                in_module_header = False
            continue
        if pattern.search(line):
            compact = re.sub(r"\s+", " ", stripped)
            hits.append(f"{va_path.name}:{lineno}:{compact}")
    return hits


def _declared_names_by_type(text: str) -> dict[str, set[str]]:
    names_by_type: dict[str, set[str]] = {"real": set(), "integer": set()}
    for match in re.finditer(r"\b(real|integer)\s+([^;]+);", text, flags=re.IGNORECASE):
        decl_type = match.group(1).lower()
        body = match.group(2)
        for item in body.split(","):
            item = re.sub(r"\[[^\]]+\]", " ", item)
            item = item.split("=")[0].strip()
            name_match = re.match(r"([A-Za-z_]\w*)\b", item)
            if name_match:
                names_by_type.setdefault(decl_type, set()).add(name_match.group(1))
    return names_by_type


def _module_port_names(text: str) -> set[str]:
    ports: set[str] = set()
    for match in re.finditer(r"\bmodule\s+\w+\s*\((.*?)\)\s*;", text, flags=re.DOTALL):
        for raw_item in match.group(1).replace("\n", " ").split(","):
            item = re.sub(r"\[[^\]]+\]", " ", raw_item)
            tokens = [tok for tok in re.split(r"\s+", item.strip()) if tok]
            for token in reversed(tokens):
                if re.fullmatch(r"[A-Za-z_]\w*", token):
                    ports.add(token)
                    break
    return ports


def _parameter_port_conflict_hits(va_path: Path) -> list[str]:
    """Detect Spectre VACOMP failures from parameters shadowing port names.

    EVAS may accept `parameter real vdd = ...;` even when `vdd` is also a port,
    but Spectre rejects the redeclaration during AHDL read-in.
    """
    text = _strip_line_comments(va_path.read_text(encoding="utf-8", errors="ignore"))
    ports = _module_port_names(text)
    if not ports:
        return []
    hits: list[str] = []
    pattern = re.compile(r"\bparameter\s+(?:real|integer)\s+([A-Za-z_]\w*)\b", re.IGNORECASE)
    for lineno, line in enumerate(text.splitlines(), start=1):
        for match in pattern.finditer(line):
            name = match.group(1)
            if name in ports:
                compact = re.sub(r"\s+", " ", line.strip())
                hits.append(f"{va_path.name}:{lineno}:{compact}")
    return hits


def _parameter_default_range_hits(va_path: Path) -> list[str]:
    """Detect parameter defaults outside their Spectre `from` range.

    Spectre rejects even a default like `parameter real vlo = 0 from (0:inf);`
    before transient simulation starts. EVAS can evaluate the model, so strict
    preflight needs to keep this as a compile-time parity guardrail.
    """
    text = _strip_line_comments(va_path.read_text(encoding="utf-8", errors="ignore"))
    hits: list[str] = []
    pattern = re.compile(
        r"\bparameter\s+(?:real|integer)\s+([A-Za-z_]\w*)\s*=\s*"
        r"([^;\s]+)\s+from\s*([\[\(])\s*([^:\]]+)\s*:\s*([^\]\)]+)\s*([\]\)])",
        re.IGNORECASE,
    )

    def _bound_value(raw: str) -> float | None:
        token = raw.strip()
        if token.lower() in {"inf", "+inf", "infinity", "+infinity"}:
            return float("inf")
        if token.lower() in {"-inf", "-infinity"}:
            return float("-inf")
        return _spectre_numeric_token(token)

    for lineno, line in enumerate(text.splitlines(), start=1):
        for match in pattern.finditer(line):
            name = match.group(1)
            value = _spectre_numeric_token(match.group(2))
            low_open = match.group(3) == "("
            low = _bound_value(match.group(4))
            high = _bound_value(match.group(5))
            high_open = match.group(6) == ")"
            if value is None or low is None or high is None:
                continue

            violates_low = value <= low if low_open else value < low
            violates_high = value >= high if high_open else value > high
            if violates_low or violates_high:
                compact = re.sub(r"\s+", " ", line.strip())
                hits.append(f"{va_path.name}:{lineno}:{name}:{compact}")
    return hits


def _parameter_open_upper_range_hits(va_path: Path) -> list[str]:
    """Detect Spectre-incompatible empty upper bounds in `from` ranges.

    Spectre rejects declarations like `from (0:)` and `from [0:)` during AHDL
    read-in. EVAS may otherwise parse/evaluate them, so strict preflight must
    catch the syntax before EVAS can false-accept a candidate.
    """
    text = _strip_line_comments(va_path.read_text(encoding="utf-8", errors="ignore"))
    hits: list[str] = []
    pattern = re.compile(
        r"\bparameter\s+(?:real|integer)\s+([A-Za-z_]\w*)\s*=\s*"
        r"[^;]+?\s+from\s*[\[\(]\s*[^:\]\)]*\s*:\s*[\]\)]",
        re.IGNORECASE,
    )
    for lineno, line in enumerate(text.splitlines(), start=1):
        for match in pattern.finditer(line):
            compact = re.sub(r"\s+", " ", line.strip())
            hits.append(f"{va_path.name}:{lineno}:{match.group(1)}:{compact}")
    return hits


def _random_distribution_seed_hits(va_path: Path) -> list[str]:
    """Detect Spectre-incompatible random distribution calls with real seeds."""
    text = _strip_line_comments(va_path.read_text(encoding="utf-8", errors="ignore"))
    declared = _declared_names_by_type(text)
    real_names = declared.get("real", set())
    hits: list[str] = []
    pattern = re.compile(r"\$(?:rdist|dist)_\w+\s*\(\s*([A-Za-z_]\w*)\b", re.IGNORECASE)
    for lineno, line in enumerate(text.splitlines(), start=1):
        for match in pattern.finditer(line):
            seed_name = match.group(1)
            if seed_name in real_names:
                compact = re.sub(r"\s+", " ", line.strip())
                hits.append(f"{va_path.name}:{lineno}:real_seed={seed_name}:{compact}")
    return hits


def _modulo_array_index_hits(va_path: Path) -> list[str]:
    """Detect direct modulo expressions inside array subscripts.

    Spectre can evaluate negative modulo results as negative array indices,
    causing runtime ASL-5401 out-of-bounds errors that EVAS may not reproduce.
    The robust pattern is to normalize the index into a bounded integer before
    using it as an array subscript.
    """
    text = _strip_line_comments(va_path.read_text(encoding="utf-8", errors="ignore"))
    hits: list[str] = []
    pattern = re.compile(r"\b([A-Za-z_]\w*)\s*\[\s*([^\]]*%[^\]]*)\]")
    for lineno, line in enumerate(text.splitlines(), start=1):
        for match in pattern.finditer(line):
            array_name = match.group(1)
            expr = re.sub(r"\s+", "", match.group(2))
            hits.append(f"{va_path.name}:{lineno}:{array_name}[{expr}]")
    return hits


def _duplicate_vsource_branch_hits(tb_path: Path) -> list[str]:
    """Detect repeated ideal voltage sources across the same node pair.

    Spectre reports these as rigid-branch loops during topology check, for
    example a DC source and a PWL source both connected from `in` to `0`.
    """
    text = _strip_line_comments(tb_path.read_text(encoding="utf-8", errors="ignore"))
    branches: dict[tuple[str, str], list[tuple[int, str]]] = {}
    pattern = re.compile(r"^\s*([A-Za-z_]\w*)\s*\(([^)]*)\)\s+vsource\b", re.IGNORECASE)
    for lineno, line in enumerate(text.splitlines(), start=1):
        match = pattern.search(line)
        if not match:
            continue
        inst = match.group(1)
        nodes = [node for node in re.split(r"\s+", match.group(2).strip()) if node]
        if len(nodes) < 2:
            continue
        key = tuple(sorted((nodes[0], nodes[1])))
        branches.setdefault(key, []).append((lineno, inst))

    hits: list[str] = []
    for (n0, n1), instances in sorted(branches.items()):
        if len(instances) < 2:
            continue
        locs = ",".join(f"{inst}@{lineno}" for lineno, inst in instances[:6])
        hits.append(f"{tb_path.name}:{n0}-{n1}:{locs}")
    return hits


def _normalized_required_axes(required_axes: list[str]) -> list[str]:
    aliases = {
        "syntax": "dut_compile",
        "routing": "tb_compile",
        "simulation": "sim_correct",
        "behavior": "sim_correct",
    }
    normalized: list[str] = []
    for axis in required_axes:
        mapped = aliases.get(axis, axis)
        if mapped not in normalized:
            normalized.append(mapped)
    return normalized


def _weighted_total(scores: dict[str, float], required_axes: list[str]) -> float:
    axes = [axis for axis in _normalized_required_axes(required_axes) if axis in {"dut_compile", "tb_compile", "sim_correct"}]
    if not axes:
        axes = ["dut_compile", "tb_compile", "sim_correct"]
    return round(sum(scores.get(axis, 0.0) for axis in axes) / len(axes), 4)


def _strict_fail_scores(
    *,
    family: str,
    required_axes: list[str],
    failure_kind: str,
) -> tuple[str, dict[str, float]]:
    scores = {"dut_compile": 1.0, "tb_compile": 1.0, "sim_correct": 1.0}

    if failure_kind == "module_linkage":
        if family in ("spec-to-va", "bugfix"):
            scores["dut_compile"] = 0.0
            scores["sim_correct"] = 0.0
            status = "FAIL_DUT_COMPILE"
        elif family == "tb-generation":
            scores["tb_compile"] = 0.0
            if "sim_correct" in required_axes:
                scores["sim_correct"] = 0.0
            status = "FAIL_TB_COMPILE"
        else:
            scores["tb_compile"] = 0.0
            scores["sim_correct"] = 0.0
            status = "FAIL_TB_COMPILE"
    elif failure_kind == "tb_syntax":
        scores["tb_compile"] = 0.0
        if "sim_correct" in required_axes:
            scores["sim_correct"] = 0.0
        status = "FAIL_TB_COMPILE"
    else:
        # AHDL syntax restrictions live in the VA artifact. In DUT-generation
        # families this is a DUT failure; in tb-generation the VA is gold, but
        # keeping this branch explicit makes unexpected failures conservative.
        if family == "tb-generation":
            scores["tb_compile"] = 0.0
            status = "FAIL_TB_COMPILE"
        else:
            scores["dut_compile"] = 0.0
            scores["sim_correct"] = 0.0
            status = "FAIL_DUT_COMPILE"

    for axis in ("dut_compile", "tb_compile", "sim_correct"):
        if axis not in required_axes and axis == "sim_correct":
            scores[axis] = 1.0
    scores["weighted_total"] = _weighted_total(scores, required_axes)
    return status, scores


def spectre_strict_preflight(
    *,
    family: str,
    required_axes: list[str],
    staged_tb: Path,
    staged_va_paths: list[Path],
) -> tuple[str | None, dict[str, float] | None, list[str]]:
    """Catch Spectre-obvious failures before EVAS scoring can false-accept.

    Accumulates ALL detected issues into notes so the repair prompt can address
    everything at once, rather than stopping at the first problem.
    """
    notes: list[str] = []
    first_status: str | None = None
    first_scores: dict[str, float] | None = None

    def _record_failure(kind: str) -> None:
        nonlocal first_status, first_scores
        if first_status is None:
            first_status, first_scores = _strict_fail_scores(
                family=family,
                required_axes=required_axes,
                failure_kind=kind,
            )

    # --- TB linkage checks ---
    module_names: set[str] = set()
    for va_path in staged_va_paths:
        if "_candidate_original" in va_path.parts:
            continue
        module_names.update(verilog_module_names(va_path))

    instance_models = spectre_instance_models(staged_tb)
    missing_models = sorted({model for model in instance_models if model not in module_names})
    if missing_models:
        _record_failure("module_linkage")
        notes.append(
            "spectre_strict:undefined_module="
            f"{','.join(missing_models)};available_modules={','.join(sorted(module_names)) or '<none>'}"
        )

    port_count_mismatches = spectre_instance_port_count_mismatch_lines(staged_tb, staged_va_paths)
    if port_count_mismatches:
        _record_failure("module_linkage")
        notes.append(
            "spectre_strict:instance_port_count_mismatch="
            + ",".join(port_count_mismatches[:8])
        )

    instance_parameter_keywords = spectre_parameters_keyword_instance_lines(staged_tb)
    if instance_parameter_keywords:
        _record_failure("tb_syntax")
        notes.append(
            "spectre_strict:instance_parameters_keyword="
            + ",".join(instance_parameter_keywords[:8])
        )

    colon_lines = spectre_colon_instance_lines(staged_tb)
    if colon_lines:
        _record_failure("module_linkage")
        notes.append(
            "spectre_strict:colon_instance_syntax_lines="
            f"{','.join(str(line) for line in colon_lines[:8])}"
        )

    bad_directives = spectre_unsupported_directive_lines(staged_tb)
    if bad_directives:
        _record_failure("module_linkage")
        notes.append(
            "spectre_strict:unsupported_tb_directives="
            f"{','.join(bad_directives[:8])}"
        )

    reversed_source_lines = spectre_reversed_source_syntax_lines(staged_tb)
    if reversed_source_lines:
        _record_failure("tb_syntax")
        notes.append(
            "spectre_strict:reversed_source_syntax="
            + ",".join(reversed_source_lines[:8])
        )

    pulse_timing_lines = spectre_pulse_nonpositive_timing_lines(staged_tb)
    if pulse_timing_lines:
        _record_failure("tb_syntax")
        notes.append(
            "spectre_strict:pulse_nonpositive_timing="
            + ",".join(pulse_timing_lines[:8])
        )

    malformed_pwl_lines = spectre_malformed_pwl_wave_lines(staged_tb)
    if malformed_pwl_lines:
        _record_failure("tb_syntax")
        notes.append(
            "spectre_strict:malformed_pwl_wave="
            + ",".join(malformed_pwl_lines[:8])
        )

    nonincreasing_pwl_lines = spectre_nonincreasing_pwl_time_lines(staged_tb)
    if nonincreasing_pwl_lines:
        _record_failure("tb_syntax")
        notes.append(
            "spectre_strict:nonincreasing_pwl_time="
            + ",".join(nonincreasing_pwl_lines[:8])
        )

    multiline_instance_lines = spectre_uncontinued_multiline_instance_lines(staged_tb)
    if multiline_instance_lines:
        _record_failure("tb_syntax")
        notes.append(
            "spectre_strict:uncontinued_multiline_instance="
            + ",".join(multiline_instance_lines[:8])
        )

    duplicate_vsource_hits = _duplicate_vsource_branch_hits(staged_tb)
    if duplicate_vsource_hits:
        _record_failure("tb_syntax")
        notes.append(
            "spectre_strict:duplicate_vsource_branch="
            + ",".join(duplicate_vsource_hits[:8])
        )

    sourced_port_drive_hits = spectre_sourced_port_drive_hits(staged_tb, staged_va_paths)
    if sourced_port_drive_hits:
        _record_failure("tb_syntax")
        notes.append(
            "spectre_strict:sourced_port_voltage_drive="
            + ",".join(sourced_port_drive_hits[:8])
        )

    interface_parameter_issues = check_interface_parameter_paths(
        va_paths=staged_va_paths,
        tb_paths=[staged_tb],
    )
    if interface_parameter_issues:
        # Spectre treats invalid instance parameters on a Verilog-A primitive as
        # warnings and ignores them (SFE-29/SFE-30), rather than rejecting the
        # run. Keep the diagnostic for repair prompts, but do not turn it into
        # a hard EVAS preflight failure; behavior checkers will catch cases
        # where the ignored parameter matters.
        notes.extend(
            "spectre_strict:" + note
            for note in format_issue_notes(interface_parameter_issues[:8])
        )

    # --- Per-VA AHDL syntax checks (check all files, collect all issues) ---
    for va_path in staged_va_paths:
        if "_candidate_original" in va_path.parts:
            continue
        if _has_verilog_initial_begin(va_path):
            _record_failure("ahdl_syntax")
            notes.append(f"spectre_strict:verilog_initial_begin={va_path.name}")
        header_backslash_hits = _module_header_backslash_continuation_hits(va_path)
        if header_backslash_hits:
            _record_failure("ahdl_syntax")
            notes.append(
                "spectre_strict:module_header_backslash_continuation="
                + ",".join(header_backslash_hits[:8])
            )
        if _has_transition_inside_conditional(va_path):
            _record_failure("ahdl_syntax")
            notes.append(f"spectre_strict:conditional_transition={va_path.name}")
        conditional_cross_hits = _conditional_cross_hits(va_path)
        if conditional_cross_hits:
            _record_failure("ahdl_syntax")
            notes.append(
                "spectre_strict:conditional_cross="
                + ",".join(conditional_cross_hits[:8])
            )
        genvar_hits = _genvar_inside_analog_hits(va_path)
        if genvar_hits:
            _record_failure("ahdl_syntax")
            notes.append(
                "spectre_strict:genvar_inside_analog="
                + ",".join(genvar_hits[:8])
            )
        dynamic_hits = _dynamic_analog_vector_index_hits(va_path)
        if dynamic_hits:
            _record_failure("ahdl_syntax")
            notes.append(
                "spectre_strict:dynamic_analog_vector_index="
                + ",".join(dynamic_hits[:12])
            )
        embedded_decl_hits = _embedded_declaration_hits(va_path)
        if embedded_decl_hits:
            _record_failure("ahdl_syntax")
            notes.append(
                "spectre_strict:embedded_declaration="
                + ",".join(embedded_decl_hits[:12])
            )
        for digital_issue in _has_digital_verilog_syntax(va_path):
            _record_failure("ahdl_syntax")
            notes.append(f"spectre_strict:digital_verilog_syntax={digital_issue} in {va_path.name}")
        direct_fileio_hits = _direct_filename_fileio_hits(va_path)
        if direct_fileio_hits:
            _record_failure("ahdl_syntax")
            notes.append(
                "spectre_strict:direct_filename_fileio="
                + ",".join(direct_fileio_hits[:8])
            )
        direction_discipline_hits = _combined_direction_discipline_hits(va_path)
        if direction_discipline_hits:
            _record_failure("ahdl_syntax")
            notes.append(
                "spectre_strict:combined_direction_discipline="
                + ",".join(direction_discipline_hits[:12])
            )
        parameter_conflict_hits = _parameter_port_conflict_hits(va_path)
        if parameter_conflict_hits:
            _record_failure("ahdl_syntax")
            notes.append(
                "spectre_strict:parameter_port_conflict="
                + ",".join(parameter_conflict_hits[:12])
            )
        parameter_range_hits = _parameter_default_range_hits(va_path)
        if parameter_range_hits:
            _record_failure("ahdl_syntax")
            notes.append(
                "spectre_strict:parameter_default_range="
                + ",".join(parameter_range_hits[:12])
            )
        parameter_open_upper_hits = _parameter_open_upper_range_hits(va_path)
        if parameter_open_upper_hits:
            _record_failure("ahdl_syntax")
            notes.append(
                "spectre_strict:parameter_open_upper_range="
                + ",".join(parameter_open_upper_hits[:12])
            )
        random_seed_hits = _random_distribution_seed_hits(va_path)
        if random_seed_hits:
            _record_failure("ahdl_syntax")
            notes.append(
                "spectre_strict:random_dist_real_seed="
                + ",".join(random_seed_hits[:8])
            )
        modulo_index_hits = _modulo_array_index_hits(va_path)
        if modulo_index_hits:
            _record_failure("ahdl_syntax")
            notes.append(
                "spectre_strict:modulo_array_index="
                + ",".join(modulo_index_hits[:8])
            )

    if first_status is not None:
        return first_status, first_scores, notes

    notes.append("spectre_strict:preflight_pass")
    return None, None, notes


def stage_candidate_case(
    *,
    family: str,
    gold_dir: Path,
    sample_dir: Path,
    dut_path: Path,
    tb_path: Path,
    stage_dir: Path,
    auxiliary_gold_vas: list[Path] | None = None,
    save_policy: str = "contract",
    required_axes: list[str] | None = None,
    contract_save_signals: list[str] | None = None,
) -> tuple[Path, Path, list[str]]:
    """Stage DUT/TB so the selected candidate, not a gold fallback, is tested.

    The EVAS simulator resolves `ahdl_include` paths relative to the testbench.
    If we copy a whole gold directory beside a gold TB, a DUT-generation task can
    accidentally use the gold DUT.  This staging step instead places the
    generated DUT under the include filename expected by the TB.
    """
    notes: list[str] = []
    auxiliary_gold_vas = auxiliary_gold_vas or []

    staged_tb = stage_dir / tb_path.name
    _copy_as(tb_path, staged_tb)
    rewritten_save_tokens = normalize_tb_save_signals(staged_tb)
    if rewritten_save_tokens > 0:
        notes.append(f"normalized_tb_save_tokens={rewritten_save_tokens}")
    staged_save_signals = all_save_signals(staged_tb)
    required_axes = required_axes or []
    requires_behavior = "sim_correct" in required_axes or "behavior" in required_axes
    if save_policy == "contract":
        if requires_behavior and contract_save_signals:
            removed, inserted = rewrite_tb_save_signals(staged_tb, contract_save_signals)
            if removed or inserted:
                notes.append(
                    f"contract_save_pruned=removed:{removed},inserted:{inserted},signals:{len(contract_save_signals)}"
                )
        elif not requires_behavior:
            # Do not remove every save line: EVAS may otherwise fall back to
            # saving many/all nodes.  One existing public signal is enough to
            # prove the transient ran while keeping CSV output bounded.
            minimal_signals = staged_save_signals[:1] if staged_save_signals else []
            removed, inserted = rewrite_tb_save_signals(staged_tb, minimal_signals)
            if removed or inserted:
                notes.append(
                    f"nonbehavior_save_minimized=removed:{removed},inserted:{inserted},signals:{len(minimal_signals)}"
                )

    includes = ahdl_includes(tb_path)
    va_includes = [name for name in includes if Path(name).suffix.lower() == ".va"]
    primary_dut: Path | None = None
    primary_dut_consumed = False

    for inc_name in includes:
        staged_inc = _safe_inc_path(stage_dir, inc_name)
        inc_suffix = Path(inc_name).suffix.lower()

        if family in ("spec-to-va", "bugfix") and inc_suffix == ".va" and not primary_dut_consumed:
            _copy_as(dut_path, staged_inc)
            primary_dut = staged_inc
            primary_dut_consumed = True
            if Path(inc_name).name != dut_path.name:
                notes.append(f"generated_dut_staged_as={inc_name}")
        elif family == "tb-generation" and inc_suffix == ".va":
            gold_match = gold_dir / inc_name
            if _copy_if_exists(gold_match, staged_inc):
                primary_dut = primary_dut or staged_inc
                notes.append(f"gold_dut_include={inc_name}")
            elif len(auxiliary_gold_vas) == 1:
                _copy_as(auxiliary_gold_vas[0], staged_inc)
                primary_dut = primary_dut or staged_inc
                notes.append(f"gold_dut_alias={auxiliary_gold_vas[0].name}->{inc_name}")
            else:
                notes.append(f"missing_include={inc_name}")
        elif family == "end-to-end" and inc_suffix == ".va":
            sample_match = sample_dir / inc_name
            if _copy_if_exists(sample_match, staged_inc):
                primary_dut = primary_dut or staged_inc
                notes.append(f"generated_include={inc_name}")
            elif alias_match := _sample_ref_alias(sample_dir, inc_name):
                _copy_as(alias_match, staged_inc)
                primary_dut = primary_dut or staged_inc
                notes.append(f"generated_include_ref_alias={alias_match.name}->{inc_name}")
            elif not primary_dut_consumed:
                _copy_as(dut_path, staged_inc)
                primary_dut = staged_inc
                primary_dut_consumed = True
                notes.append(f"generated_dut_alias={dut_path.name}->{inc_name}")
            else:
                notes.append(f"missing_include={inc_name}")
        else:
            if _copy_if_exists(tb_path.parent / inc_name, staged_inc):
                notes.append(f"aux_include={inc_name}")
            elif _copy_if_exists(gold_dir / inc_name, staged_inc):
                notes.append(f"gold_aux_include={inc_name}")
            elif _copy_if_exists(sample_dir / inc_name, staged_inc):
                notes.append(f"sample_aux_include={inc_name}")
            else:
                notes.append(f"missing_include={inc_name}")

    if primary_dut is None:
        primary_dut = stage_dir / dut_path.name
        _copy_as(dut_path, primary_dut)
        if not va_includes:
            notes.append("no_ahdl_va_include_in_tb")
        else:
            notes.append("primary_dut_uploaded_but_not_referenced_by_tb")

    trace_dut = stage_dir / "_candidate_original" / dut_path.name
    if trace_dut != primary_dut:
        _copy_as(dut_path, trace_dut)

    return primary_dut, staged_tb, notes


# ---------------------------------------------------------------------------
# Per-task scoring
# ---------------------------------------------------------------------------

def score_one_task(
    task_id: str,
    task_dir: Path,
    sample_dir: Path,
    output_dir: Path,
    *,
    model: str,
    sample_idx: int,
    temperature: float,
    top_p: float,
    timeout_s: int = 180,
    save_policy: str = "contract",
) -> dict:
    """Score one generated candidate and return a structured result.json payload."""
    meta = read_meta(task_dir)
    family = meta.get("family", "end-to-end")
    category = meta.get("category", "unknown")
    required_axes: list[str] = meta.get("scoring", ["dut_compile", "tb_compile", "sim_correct"])
    gold_dir = task_dir / "gold"

    # Generation metadata (may not exist if files were hand-written)
    gen_meta_path = sample_dir / "generation_meta.json"
    gen_meta: dict = {}
    if gen_meta_path.exists():
        try:
            gen_meta = json.loads(gen_meta_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    invalid_generation_reasons: list[str] = []
    if gen_meta.get("dry_run") or gen_meta.get("status") == "dry_run":
        invalid_generation_reasons.append("dry_run_generation")
    placeholder_files = sorted(
        p.name
        for p in sample_dir.glob("*placeholder*")
        if p.is_file() and p.suffix.lower() in {".va", ".scs"}
    )
    if placeholder_files:
        shown = ", ".join(placeholder_files[:4])
        suffix = "" if len(placeholder_files) <= 4 else f", +{len(placeholder_files) - 4} more"
        invalid_generation_reasons.append(f"placeholder_artifacts: {shown}{suffix}")
    if invalid_generation_reasons:
        result = _fail_result(
            task_id, model, family, category, sample_idx, temperature, top_p,
            required_axes, "; ".join(invalid_generation_reasons),
            None, None,
        )
        result["generation_meta"] = gen_meta
        result["artifacts"]["sample_dir"] = str(sample_dir)
        _save_result(result, output_dir)
        return result

    # Resolve DUT and testbench paths based on family
    generated_va = find_va_file(sample_dir)
    generated_tb = find_tb_file(sample_dir)
    gold_tb = choose_gold_tb(gold_dir)
    contract_save_signals = all_save_signals(gold_tb) if gold_tb and gold_tb.exists() else None

    if family in ("spec-to-va", "bugfix"):
        # Model generates DUT; use gold testbench
        dut_path = generated_va
        tb_path = gold_tb
    elif family == "tb-generation":
        # Model generates testbench; use gold DUT
        gold_vas = sorted(gold_dir.glob("*.va"))
        dut_path = gold_vas[0] if gold_vas else None
        tb_path = generated_tb
        auxiliary_gold_vas = gold_vas
    else:
        # end-to-end: model generates both
        dut_path = generated_va
        tb_path = generated_tb
        auxiliary_gold_vas = []
    if family in ("spec-to-va", "bugfix"):
        auxiliary_gold_vas = []

    # Fail early if required files are missing
    missing = []
    if dut_path is None or not dut_path.exists():
        missing.append("dut.va")
    if tb_path is None or not tb_path.exists():
        missing.append("testbench.scs")
    if missing:
        result = _fail_result(
            task_id, model, family, category, sample_idx, temperature, top_p,
            required_axes, f"missing_generated_files: {', '.join(missing)}",
            dut_path, tb_path,
        )
        result["generation_meta"] = gen_meta
        result["artifacts"]["sample_dir"] = str(sample_dir)
        _save_result(result, output_dir)
        return result

    # Build a temporary run directory with DUT + TB co-located (EVAS requires it).
    # The staging helper also prevents DUT-generation tasks from silently using
    # the gold DUT that lives beside the gold testbench.
    with tempfile.TemporaryDirectory(prefix=f"score_{task_id}_") as tmp:
        tmp_path = Path(tmp)
        tmp_dut, tmp_tb, staging_notes = stage_candidate_case(
            family=family,
            gold_dir=gold_dir,
            sample_dir=sample_dir,
            dut_path=dut_path,
            tb_path=tb_path,
            stage_dir=tmp_path,
            auxiliary_gold_vas=auxiliary_gold_vas,
            save_policy=save_policy,
            required_axes=required_axes,
            contract_save_signals=contract_save_signals,
        )

        strict_status, strict_scores, strict_notes = spectre_strict_preflight(
            family=family,
            required_axes=required_axes,
            staged_tb=tmp_tb,
            staged_va_paths=sorted(tmp_path.rglob("*.va")),
        )
        if strict_status is not None and strict_scores is not None:
            evas_result = {
                "status": strict_status,
                "scores": strict_scores,
                "notes": strict_notes,
            }
        else:
            try:
                evas_result = run_case(
                    task_dir,
                    tmp_dut,
                    tmp_tb,
                    output_root=output_dir / task_id,
                    timeout_s=timeout_s,
                    task_id_override=task_id,
                )
                evas_result["notes"] = strict_notes + evas_result.get("notes", [])
            except subprocess.TimeoutExpired:
                evas_result = {
                    "status": "FAIL_INFRA",
                    "scores": {
                        "dut_compile": 0.0,
                        "tb_compile": 0.0,
                        "sim_correct": 0.0,
                        "weighted_total": 0.0,
                    },
                    "notes": strict_notes + [f"evas_timeout>{timeout_s}s"],
                }

    scores: dict[str, float] = evas_result.get("scores", {})
    status = evas_result.get("status", "FAIL_INFRA")

    result = {
        "model": model,
        "task_id": task_id,
        "family": family,
        "category": category,
        "sample_idx": sample_idx,
        "temperature": temperature,
        "top_p": top_p,
        "status": status,
        "scores": scores,
        "required_axes": required_axes,
        "artifacts": {
            "dut_path": str(dut_path),
            "tb_path": str(tb_path),
            "result_json": str(output_dir / task_id / "result.json"),
        },
        "generation_meta": gen_meta,
        "evas_notes": evas_result.get("notes", []),
        "evas_timing": evas_result.get("timing", {}),
    }
    if status != "PASS" and evas_result.get("stdout_tail"):
        result["evas_stdout_tail"] = evas_result.get("stdout_tail")
    result["evas_notes"] = staging_notes + result["evas_notes"]
    attach_failure_attribution(result)
    _save_result(result, output_dir)
    return result


def _fail_result(task_id, model, family, category, sample_idx, temperature, top_p,
                 required_axes, reason, dut_path, tb_path) -> dict:
    scores = {"dut_compile": 0.0, "tb_compile": 0.0, "sim_correct": 0.0, "weighted_total": 0.0}
    result = {
        "model": model,
        "task_id": task_id,
        "family": family,
        "category": category,
        "sample_idx": sample_idx,
        "temperature": temperature,
        "top_p": top_p,
        "status": "FAIL_INFRA",
        "scores": scores,
        "required_axes": required_axes,
        "artifacts": {
            "dut_path": str(dut_path) if dut_path else None,
            "tb_path": str(tb_path) if tb_path else None,
            "result_json": None,
        },
        "generation_meta": {},
        "evas_notes": [reason],
    }
    attach_failure_attribution(result)
    return result


def _save_result(result: dict, output_dir: Path) -> None:
    if "failure_attribution" not in result:
        attach_failure_attribution(result)
    task_dir_out = output_dir / result["task_id"]
    task_dir_out.mkdir(parents=True, exist_ok=True)
    result_path = task_dir_out / "result.json"
    result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _fingerprint_tree(root: Path, patterns: tuple[str, ...]) -> list[dict[str, str]]:
    if not root.exists():
        return []
    paths: list[Path] = []
    for pattern in patterns:
        paths.extend(root.rglob(pattern))
    items: list[dict[str, str]] = []
    for path in sorted(set(paths)):
        if path.is_file():
            items.append(
                {
                    "path": str(path.relative_to(root)),
                    "sha256": _sha256_file(path),
                }
            )
    return items


def _score_cache_key(
    *,
    task_id: str,
    task_dir: Path,
    sample_dir: Path,
    model_slug: str,
    sample_idx: int,
    temperature: float,
    top_p: float,
    timeout_s: int,
    save_policy: str,
) -> dict:
    return {
        "version": 1,
        "task_id": task_id,
        "model": model_slug,
        "sample_idx": sample_idx,
        "temperature": temperature,
        "top_p": top_p,
        "timeout_s": timeout_s,
        "save_policy": save_policy,
        "task_gold": _fingerprint_tree(task_dir / "gold", ("*.scs", "*.va", "*.csv")),
        "sample": _fingerprint_tree(sample_dir, ("*.scs", "*.va", "generation_meta.json")),
        "score_py": _sha256_file(Path(__file__).resolve()),
        "simulate_evas_py": _sha256_file((ROOT / "runners" / "simulate_evas.py").resolve()),
    }


def _load_cached_result(out_root: Path, task_id: str, expected_key: dict) -> dict | None:
    result_path = out_root / task_id / "result.json"
    if not result_path.exists():
        return None
    try:
        result = json.loads(result_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if result.get("_score_cache_key") != expected_key:
        return None
    result["_cache_hit"] = True
    return result


# ---------------------------------------------------------------------------
# Aggregate: Pass@1 + family breakdown
# ---------------------------------------------------------------------------

def _task_pass(result: dict) -> bool:
    """A task passes Pass@1 if all required axes are 1.0."""
    scores = result.get("scores", {})
    required = _normalized_required_axes(
        result.get("required_axes", ["dut_compile", "tb_compile", "sim_correct"])
    )
    return all(scores.get(ax, 0.0) >= 1.0 for ax in required)


def build_model_results(model: str, results: list[dict], temperature: float,
                        top_p: float) -> dict:
    total = len(results)
    if total == 0:
        return {"model": model, "total": 0, "pass_at_1": 0.0}

    n_pass = sum(1 for r in results if _task_pass(r))

    # Per-family breakdown
    families: dict[str, dict[str, int]] = {}
    for r in results:
        fam = r.get("family", "unknown")
        if fam not in families:
            families[fam] = {"total": 0, "pass": 0}
        families[fam]["total"] += 1
        if _task_pass(r):
            families[fam]["pass"] += 1

    family_rates = {
        fam: round(s["pass"] / s["total"], 4) if s["total"] else 0.0
        for fam, s in families.items()
    }

    # Per-axis rates (denominator = tasks where that axis is required)
    axis_stats: dict[str, dict[str, int]] = {}
    for r in results:
        scores = r.get("scores", {})
        required = _normalized_required_axes(r.get("required_axes", []))
        for ax in required:
            if ax not in axis_stats:
                axis_stats[ax] = {"denom": 0, "numer": 0}
            axis_stats[ax]["denom"] += 1
            if scores.get(ax, 0.0) >= 1.0:
                axis_stats[ax]["numer"] += 1

    axis_rates = {
        ax: round(s["numer"] / s["denom"], 4) if s["denom"] else 0.0
        for ax, s in axis_stats.items()
    }

    # Failure taxonomy
    fail_taxonomy: dict[str, int] = {}
    failure_domain_taxonomy: dict[str, int] = {}
    repair_owner_taxonomy: dict[str, int] = {}
    for r in results:
        attribution = r.get("failure_attribution") or attach_failure_attribution(dict(r))["failure_attribution"]
        domain = attribution.get("domain", "unknown")
        owner = attribution.get("repair_owner", "unknown")
        failure_domain_taxonomy[domain] = failure_domain_taxonomy.get(domain, 0) + 1
        repair_owner_taxonomy[owner] = repair_owner_taxonomy.get(owner, 0) + 1
        if not _task_pass(r):
            scores = r.get("scores", {})
            required = r.get("required_axes", [])
            if r.get("status") == "FAIL_INFRA":
                label = "FAIL_INFRA"
            elif scores.get("dut_compile", 1.0) < 1.0:
                label = "FAIL_DUT_COMPILE"
            elif scores.get("tb_compile", 1.0) < 1.0:
                label = "FAIL_TB_COMPILE"
            elif scores.get("sim_correct", 1.0) < 1.0:
                label = "FAIL_SIM_CORRECTNESS"
            else:
                label = "FAIL_OTHER"
            fail_taxonomy[label] = fail_taxonomy.get(label, 0) + 1

    return {
        "model": model,
        "temperature": temperature,
        "top_p": top_p,
        "total_tasks": total,
        "pass_at_1": round(n_pass / total, 4),
        "pass_count": n_pass,
        "by_family": family_rates,
        "axis_rates": axis_rates,
        "failure_taxonomy": fail_taxonomy,
        "failure_domain_taxonomy": failure_domain_taxonomy,
        "repair_owner_taxonomy": repair_owner_taxonomy,
        "status": "MODEL_EVALUATED",
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _score_task_entry(
    *,
    task_id: str,
    task_dir: Path,
    generated_root: Path,
    model_slug: str,
    out_root: Path,
    sample_idx: int,
    temperature: float,
    top_p: float,
    timeout_s: int,
    resume: bool,
    save_policy: str,
) -> dict:
    sample_dir = find_generated_dir(generated_root, model_slug, task_id, sample_idx)
    if sample_dir is None:
        meta = read_meta(task_dir)
        result = _fail_result(
            task_id,
            model_slug,
            meta.get("family", "unknown"),
            meta.get("category", "unknown"),
            sample_idx,
            temperature,
            top_p,
            meta.get("scoring", ["dut_compile", "tb_compile", "sim_correct"]),
            "missing_generated_sample",
            None,
            None,
        )
        _save_result(result, out_root)
        return result

    cache_key = _score_cache_key(
        task_id=task_id,
        task_dir=task_dir,
        sample_dir=sample_dir,
        model_slug=model_slug,
        sample_idx=sample_idx,
        temperature=temperature,
        top_p=top_p,
        timeout_s=timeout_s,
        save_policy=save_policy,
    )
    if resume:
        cached = _load_cached_result(out_root, task_id, cache_key)
        if cached is not None:
            return cached

    result = score_one_task(
        task_id,
        task_dir,
        sample_dir,
        out_root,
        model=model_slug,
        sample_idx=sample_idx,
        temperature=temperature,
        top_p=top_p,
        timeout_s=timeout_s,
        save_policy=save_policy,
    )
    result["_score_cache_key"] = cache_key
    _save_result(result, out_root)
    return result


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Score model-generated Verilog-A candidates against the vaEvas benchmark."
    )
    ap.add_argument("--model", required=True, help="Model name slug (e.g. claude-sonnet-4-6)")
    ap.add_argument(
        "--generated-dir",
        default="generated",
        help="Root directory produced by generate.py. Default: generated/",
    )
    ap.add_argument(
        "--output-dir",
        default="",
        help="Root for scoring results. Default: results/model-eval-<model>/",
    )
    ap.add_argument(
        "--bench-dir",
        default="",
        help=(
            "Optional benchmark root containing tasks/. Use this for benchmark-v2 "
            "or benchmark-balanced instead of the official tasks/ tree."
        ),
    )
    ap.add_argument(
        "--task", action="append", default=[],
        help="Score only these task_ids (repeatable). Omit for all.",
    )
    ap.add_argument(
        "--family", action="append",
        choices=list(ALL_FAMILIES),
        help="Limit to these families. Omit for all.",
    )
    ap.add_argument("--sample-idx", type=int, default=0, help="Sample index to score. Default: 0")
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--top-p", type=float, default=1.0)
    ap.add_argument("--timeout-s", type=int, default=180)
    ap.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Parallel EVAS scoring workers. Default: 1 (serial).",
    )
    ap.add_argument(
        "--resume",
        action="store_true",
        help="Reuse per-task result.json only when input/checker fingerprints match.",
    )
    ap.add_argument(
        "--save-policy",
        choices=["contract", "debug"],
        default="contract",
        help=(
            "contract: prune save directives to public checker/gold observables, "
            "and remove saves when behavior is not scored. debug: preserve original save directives."
        ),
    )
    args = ap.parse_args()

    generated_root = Path(args.generated_dir)
    if not generated_root.is_absolute():
        generated_root = ROOT / generated_root

    model_slug = args.model.replace("/", "_")
    out_root = (
        Path(args.output_dir)
        if args.output_dir
        else ROOT / "results" / f"model-eval-{model_slug}"
    )
    if not out_root.is_absolute():
        out_root = ROOT / out_root
    out_root.mkdir(parents=True, exist_ok=True)

    families = tuple(args.family) if args.family else ALL_FAMILIES
    selected = set(args.task) if args.task else None

    bench_dir = Path(args.bench_dir) if args.bench_dir else None
    if bench_dir is not None and not bench_dir.is_absolute():
        bench_dir = ROOT / bench_dir
    task_list = (
        list_bench_task_dirs(bench_dir, families=families, selected=selected)
        if bench_dir is not None
        else list_all_task_dirs(families=families, selected=selected)
    )
    if not task_list:
        print("[score] No tasks found.")
        return 1
    coverage_errors, contract_warnings = _audit_checker_contract(task_list)
    for warn in contract_warnings:
        print(f"[score] WARN {warn}")
    if coverage_errors:
        print("[score] ERROR missing behavior checker for sim_correct-required tasks:")
        for task_id in coverage_errors:
            print(f"  - {task_id}")
        print("[score] Fix CHECKS mapping in runners/simulate_evas.py before scoring.")
        return 2

    results: list[dict] = []
    worker_count = max(1, min(args.workers, len(task_list)))
    if worker_count == 1:
        for task_id, task_dir in task_list:
            print(f"[score] scoring {task_id} ...", end=" ", flush=True)
            result = _score_task_entry(
                task_id=task_id,
                task_dir=task_dir,
                generated_root=generated_root,
                model_slug=model_slug,
                out_root=out_root,
                sample_idx=args.sample_idx,
                temperature=args.temperature,
                top_p=args.top_p,
                timeout_s=args.timeout_s,
                resume=args.resume,
                save_policy=args.save_policy,
            )
            status = result["status"]
            if status == "FAIL_INFRA" and "missing_generated_sample" in result.get("evas_notes", []):
                print(f"{status} (missing generated files)")
            elif result.get("_cache_hit"):
                print(f"{status} (cached)")
            else:
                print(status)
            results.append(result)
    else:
        print(f"[score] parallel EVAS scoring with {worker_count} workers")
        with concurrent.futures.ThreadPoolExecutor(max_workers=worker_count) as executor:
            future_to_task = {
                executor.submit(
                    _score_task_entry,
                    task_id=task_id,
                    task_dir=task_dir,
                    generated_root=generated_root,
                    model_slug=model_slug,
                    out_root=out_root,
                    sample_idx=args.sample_idx,
                    temperature=args.temperature,
                    top_p=args.top_p,
                    timeout_s=args.timeout_s,
                    resume=args.resume,
                    save_policy=args.save_policy,
                ): task_id
                for task_id, task_dir in task_list
            }
            for future in concurrent.futures.as_completed(future_to_task):
                task_id = future_to_task[future]
                result = future.result()
                cache_suffix = " (cached)" if result.get("_cache_hit") else ""
                print(f"[score] scoring {task_id} ... {result['status']}{cache_suffix}", flush=True)
                results.append(result)

    if not results:
        print("[score] No results produced.")
        return 1

    task_order = {task_id: idx for idx, (task_id, _) in enumerate(task_list)}
    results.sort(key=lambda result: task_order.get(result.get("task_id", ""), 10**9))
    aggregate = build_model_results(model_slug, results, args.temperature, args.top_p)
    agg_path = out_root / "model_results.json"
    agg_path.write_text(json.dumps(aggregate, indent=2), encoding="utf-8")

    print(f"\n[score] {model_slug}  tasks={aggregate['total_tasks']}"
          f"  Pass@1={aggregate['pass_at_1']:.3f}"
          f"  ({aggregate['pass_count']}/{aggregate['total_tasks']})")
    for fam, rate in aggregate.get("by_family", {}).items():
        print(f"         {fam}: {rate:.3f}")
    print(f"\n  → {agg_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
