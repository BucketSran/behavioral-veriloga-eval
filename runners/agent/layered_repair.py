"""Layered repair policy — absorbed from ``runners/run_adaptive_repair.py``.

When ``config.loop.layered_repair`` is enabled, each failed round is routed
to a narrow editable layer and the LLM is instructed to change ONLY that
layer, freezing everything else. This focuses the repair and prevents the
model from rewriting working code.

Five layers (narrowest → broadest):
    compile_dut        — fix Verilog-A DUT syntax/interface only
    compile_tb         — fix Spectre testbench wiring only
    runtime_interface  — coupled DUT/TB interface problem (returncode=1, no CSV)
    observable         — harness/stimulus problem; DUT frozen, repair TB only
    behavior           — semantic correctness; gold harness frozen, repair DUT only

The generalization vs the legacy runner: progress ranking no longer hardcodes
DWA-specific metric keys (max_active_cells, overlap_count). Instead,
``failure_phase_score`` ranks purely by failure phase (0..6) and any
``key=value`` metrics found in evas_notes are used as tiebreakers generically.
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path


_OBSERVABLE_NOTE_MARKERS = (
    "missing ",
    "tran.csv missing",
    "insufficient_post_reset_samples",
    "too_few_edges",
    "too_few_clock_edges",
    "too_few_rising_edges",
    "seen_out_never_high",
)

_MAIN_MODULE_PATTERNS = [
    re.compile(r"Main module name:\s*`([^`]+)`", re.IGNORECASE),
    re.compile(r"Module name:\s*`([^`]+)`", re.IGNORECASE),
    re.compile(r"module named\s*`([^`]+)`", re.IGNORECASE),
]


def classify_repair_layer(result: dict) -> str:
    """Route a failure to the narrowest editable layer."""
    if result.get("status") == "PASS":
        return "done"

    scores = result.get("scores", {})
    dut_compile = float(scores.get("dut_compile", 0.0))
    tb_compile = float(scores.get("tb_compile", 0.0))
    notes = " ".join(str(note) for note in result.get("evas_notes", [])).lower()

    if dut_compile < 1.0:
        return "compile_dut"
    if tb_compile < 1.0:
        return "compile_tb"
    if "tran.csv missing" in notes or "returncode=1" in notes or "tb_not_executed" in notes:
        return "runtime_interface"
    if any(marker in notes for marker in _OBSERVABLE_NOTE_MARKERS):
        return "observable"
    if result.get("status") == "FAIL_SIM_CORRECTNESS":
        return "behavior"
    return "infra"


def failure_phase_score(result: dict) -> int:
    """Rank failure-surface progress on a 0..6 scale (6 = PASS).

    Useful when ``weighted_total`` ties across rounds but the failure surface
    has actually advanced (e.g. checker now reads CSV columns it couldn't before).
    """
    status = result.get("status")
    if status == "PASS":
        return 6
    notes = " ".join(str(note) for note in result.get("evas_notes", [])).lower()
    if status == "FAIL_SIM_CORRECTNESS":
        if "tran.csv missing" in notes or "tb_not_executed" in notes:
            return 2
        if "missing " in notes or "missing_" in notes:
            return 3
        if any(marker in notes for marker in _OBSERVABLE_NOTE_MARKERS):
            return 4
        return 5
    if status == "FAIL_TB_COMPILE":
        return 1
    if status == "FAIL_DUT_COMPILE":
        return 0
    return 0


def generic_progress_rank(result: dict) -> tuple:
    """Generalized version of run_adaptive_repair._progress_rank.

    Replaces hardcoded DWA metric keys with: generic failure_phase_score +
    any numeric ``key=value`` metrics found in evas_notes (lower bad-metric
    counts are better, so we negate them; this is heuristic but task-agnostic).
    """
    scores = result.get("scores", {})
    status = result.get("status", "FAIL")
    base = (
        int(status == "PASS"),
        float(scores.get("weighted_total", 0.0)),
        float(scores.get("dut_compile", 0.0)),
        float(scores.get("tb_compile", 0.0)),
        failure_phase_score(result),
    )
    # Tiebreak: collect numeric metrics from notes. Bad-count metrics (those
    # whose name suggests a problem count) are negated so lower is better.
    tiebreaks: list[float] = []
    for note in result.get("evas_notes", []):
        for key, raw in re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)=([^\s,;]+)", str(note)):
            try:
                val = float(raw)
            except ValueError:
                continue
            kl = key.lower()
            if any(bad in kl for bad in ("bad_", "error", "violation", "mismatch", "missing")):
                tiebreaks.append(-val)
            else:
                tiebreaks.append(val)
    return (*base, *sorted(tiebreaks, reverse=True))


def layer_policy_section(layer: str, task_dir: Path) -> str:
    """Build the 'only change THIS layer' instruction for the repair prompt."""
    if layer == "compile_dut":
        return (
            "\n\n# Layered Only-Repair Policy: DUT Compile\n"
            "The current failure is in DUT compile/interface. Change only the Verilog-A DUT files needed to compile. "
            "Preserve the testbench stimulus, save statements, tran setup, module intent, and behavior policy unless "
            "a compile error directly requires an interface adjustment.\n"
        )
    if layer == "compile_tb":
        return (
            "\n\n# Layered Only-Repair Policy: Testbench Compile\n"
            "The current failure is in testbench compile/interface. Change only the Spectre testbench wiring, includes, "
            "instances, parameters, save statements, or tran setup needed to compile. Preserve DUT Verilog-A behavior.\n"
        )
    if layer == "observable":
        return (
            "\n\n# Layered Only-Repair Policy: Observable Harness\n"
            "The current failure is an observable/stimulus problem, not a DUT behavior problem. The runner will preserve "
            "the existing Verilog-A DUT files and evaluate only your repaired Spectre testbench/harness. Focus on reset "
            "release, transient stop, required save names, include paths, and stimulus coverage. Do not redesign DUT logic.\n"
        )
    if layer == "runtime_interface":
        return (
            "\n\n# Layered Only-Repair Policy: Runtime Interface/Harness\n"
            "The current failure is `returncode=1`, `tran.csv missing`, or equivalent runtime artifact loss after strict "
            "preflight. This is usually a coupled DUT/TB interface problem. Repair the smallest consistent set of "
            "Verilog-A module declarations, file names, ahdl_include lines, Spectre instance node lists, reset/enable "
            "sources, and save/tran setup needed to produce a stable `tran.csv`. Do not tune semantic constants until "
            "the waveform CSV exists.\n"
        )
    if layer == "behavior":
        harness_params = _gold_harness_parameter_names(task_dir)
        param_text = ", ".join(f"`{name}`" for name in harness_params) if harness_params else "the verifier parameters"
        return (
            "\n\n# Layered Only-Repair Policy: DUT Behavior\n"
            "The current failure is behavior correctness. The runner will use the benchmark verifier harness for stimulus "
            "and saved observables, so repair the DUT behavior only. Do not spend tokens redesigning the Spectre testbench. "
            "Preserve the required DUT module name and ports exactly.\n"
            f"The DUT must accept these verifier parameters if present in the harness: {param_text}. "
            "Use the verifier supply parameter (for example `vdd`) for output HIGH and verifier initialization parameters "
            "for reset state when those names are present.\n"
        )
    return (
        "\n\n# Layered Only-Repair Policy: Infrastructure\n"
        "The failure is not yet classified as compile, observable, or behavior. Make the smallest change needed to expose "
        "a concrete EVAS diagnostic, and do not rewrite working layers.\n"
    )


# ─── Gold harness freeze (behavior layer) ──────────────────────
# When the failure is in the behavior layer, we want to evaluate ONLY the
# candidate's DUT. We copy the gold testbench + helper .va files but skip the
# gold DUT module, so the candidate's DUT isn't overwritten.

def freeze_gold_harness(task_dir: Path, sample_dir: Path) -> list[str]:
    """Stage the gold verifier harness into sample_dir, preserving the candidate DUT.

    Returns the list of copied file names. This is NOT copying the gold DUT —
    we copy Spectre testbenches and helper stimulus modules, but skip the
    Verilog-A file whose module matches the task's main DUT.
    """
    gold_dir = task_dir / "gold"
    if not gold_dir.exists():
        return []
    protected = _protected_dut_modules(task_dir, sample_dir)
    copied: list[str] = []

    for existing in sample_dir.glob("*.scs"):
        existing.unlink()
    for src in sorted(gold_dir.glob("*.scs")):
        shutil.copy2(src, sample_dir / src.name)
        copied.append(src.name)
    for src in sorted(gold_dir.glob("*.va")):
        gold_module = _module_name_of(src) or src.stem
        if gold_module in protected:
            continue
        shutil.copy2(src, sample_dir / src.name)
        copied.append(src.name)
    return copied


def _protected_dut_modules(task_dir: Path, sample_dir: Path) -> set[str]:
    """Return generated DUT module names that the gold harness freeze must not overwrite."""
    prompt_path = task_dir / "prompt.md"
    prompt = prompt_path.read_text(encoding="utf-8", errors="ignore") if prompt_path.exists() else ""
    protected: set[str] = set()
    for pattern in _MAIN_MODULE_PATTERNS:
        m = pattern.search(prompt)
        if m:
            protected.add(m.group(1).strip())
    for m in re.finditer(
        r"\bmodules?\s+named\s+((?:`[^`]+`(?:\s*(?:,|and)\s*)?)+)", prompt, re.IGNORECASE
    ):
        protected.update(re.findall(r"`([^`]+)`", m.group(1)))
    for m in re.finditer(
        r"\b(?:ADC|DAC|DUT|main)\s+module\s+`([^`]+)`", prompt, re.IGNORECASE
    ):
        protected.add(m.group(1))
    if protected:
        return protected
    # Fallback: protect any module declared in the candidate sample dir.
    return _declared_modules(sorted(sample_dir.glob("*.va")))


def _declared_modules(paths: list[Path]) -> set[str]:
    modules: set[str] = set()
    for path in paths:
        name = _module_name_of(path)
        if name:
            modules.add(name)
    return modules


def _module_name_of(va_path: Path) -> str | None:
    try:
        text = va_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None
    m = re.search(r"\bmodule\s+(\w+)", text)
    return m.group(1) if m else None


def _gold_harness_parameter_names(task_dir: Path) -> list[str]:
    names: set[str] = set()
    gold_dir = task_dir / "gold"
    if not gold_dir.exists():
        return []
    for tb in sorted(gold_dir.glob("*.scs")):
        text = tb.read_text(encoding="utf-8", errors="ignore")
        for name in re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*=", text):
            if name not in {"type", "val0", "val1", "period", "delay", "rise", "fall",
                            "width", "wave", "stop", "maxstep"}:
                names.add(name)
    return sorted(names)
