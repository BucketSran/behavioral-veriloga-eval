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
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from simulate_evas import evaluate_behavior, has_behavior_check, run_case

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
        stripped = line.strip().lower()
        if stripped.startswith("plot "):
            bad.append(f"{lineno}:plot")
    return bad


def _has_verilog_initial_begin(va_path: Path) -> bool:
    text = va_path.read_text(encoding="utf-8", errors="ignore")
    return bool(re.search(r"(?m)^\s*initial\s+begin\b", _strip_line_comments(text)))


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

    return issues


def _weighted_total(scores: dict[str, float], required_axes: list[str]) -> float:
    axes = [axis for axis in required_axes if axis in {"dut_compile", "tb_compile", "sim_correct"}]
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

    # --- Per-VA AHDL syntax checks (check all files, collect all issues) ---
    for va_path in staged_va_paths:
        if "_candidate_original" in va_path.parts:
            continue
        if _has_verilog_initial_begin(va_path):
            _record_failure("ahdl_syntax")
            notes.append(f"spectre_strict:verilog_initial_begin={va_path.name}")
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
        for digital_issue in _has_digital_verilog_syntax(va_path):
            _record_failure("ahdl_syntax")
            notes.append(f"spectre_strict:digital_verilog_syntax={digital_issue} in {va_path.name}")

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

    # Resolve DUT and testbench paths based on family
    generated_va = find_va_file(sample_dir)
    generated_tb = find_tb_file(sample_dir)
    gold_tb = choose_gold_tb(gold_dir)

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
                    output_root=output_dir,
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
    }
    result["evas_notes"] = staging_notes + result["evas_notes"]
    _save_result(result, output_dir)
    return result


def _fail_result(task_id, model, family, category, sample_idx, temperature, top_p,
                 required_axes, reason, dut_path, tb_path) -> dict:
    scores = {"dut_compile": 0.0, "tb_compile": 0.0, "sim_correct": 0.0, "weighted_total": 0.0}
    return {
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


def _save_result(result: dict, output_dir: Path) -> None:
    task_dir_out = output_dir / result["task_id"]
    task_dir_out.mkdir(parents=True, exist_ok=True)
    result_path = task_dir_out / "result.json"
    result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Aggregate: Pass@1 + family breakdown
# ---------------------------------------------------------------------------

def _task_pass(result: dict) -> bool:
    """A task passes Pass@1 if all required axes are 1.0."""
    scores = result.get("scores", {})
    required = result.get("required_axes", ["dut_compile", "tb_compile", "sim_correct"])
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
        required = r.get("required_axes", [])
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
    for r in results:
        if not _task_pass(r):
            scores = r.get("scores", {})
            required = r.get("required_axes", [])
            if scores.get("dut_compile", 1.0) < 1.0:
                label = "FAIL_DUT_COMPILE"
            elif scores.get("tb_compile", 1.0) < 1.0:
                label = "FAIL_TB_COMPILE"
            elif scores.get("sim_correct", 1.0) < 1.0:
                label = "FAIL_SIM_CORRECTNESS"
            elif r.get("status") == "FAIL_INFRA":
                label = "FAIL_INFRA"
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
        "status": "MODEL_EVALUATED",
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

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

    task_list = list_all_task_dirs(families=families, selected=selected)
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
    for task_id, task_dir in task_list:
        sample_dir = find_generated_dir(generated_root, model_slug, task_id, args.sample_idx)
        if sample_dir is None:
            print(f"[score] SKIP {task_id} — no generated files at "
                  f"{generated_root}/{model_slug}/{task_id}/sample_{args.sample_idx}/")
            continue

        print(f"[score] scoring {task_id} ...", end=" ", flush=True)
        result = score_one_task(
            task_id, task_dir, sample_dir,
            out_root,
            model=model_slug,
            sample_idx=args.sample_idx,
            temperature=args.temperature,
            top_p=args.top_p,
            timeout_s=args.timeout_s,
        )
        status = result["status"]
        print(status)
        results.append(result)

    if not results:
        print("[score] No results produced.")
        return 1

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
