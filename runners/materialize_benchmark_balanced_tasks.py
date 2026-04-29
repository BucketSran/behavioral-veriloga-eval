#!/usr/bin/env python3
"""Materialize a task-form-balanced benchmark expansion.

The generated benchmark is intentionally separate from the original 92-task
tree.  It imports the original 92 with normalized task-form metadata, then adds
four external core functions in four task forms: end-to-end, DUT/spec-to-VA,
testbench generation, and bugfix.

The 16 added balanced tasks were validated with both EVAS and real Spectre on
2026-04-30.
"""
from __future__ import annotations

import json
import shutil
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ORIGINAL_TASK_ROOT = ROOT / "tasks"
BENCH = ROOT / "benchmark-balanced"
TASK_ROOT = BENCH / "tasks"


@dataclass(frozen=True)
class Core:
    slug: str
    kind: str
    title: str
    module: str
    inputs: list[str]
    outputs: list[str]
    checker_spec: dict[str, Any]
    prompt_intent: str


CORES = [
    Core(
        slug="threshold_detector",
        kind="threshold",
        title="threshold detector",
        module="balanced_threshold_detector",
        inputs=["sense_level", "vdd", "vss"],
        outputs=["decision_level"],
        checker_spec={"kind": "threshold", "vin": "sense_level", "vout": "decision_level"},
        prompt_intent="Convert a single sensor voltage into a rail-referenced decision level using threshold behavior.",
    ),
    Core(
        slug="window_detector",
        kind="window",
        title="window detector",
        module="balanced_window_detector",
        inputs=["sensor_level", "vdd", "vss"],
        outputs=["inside_window", "below_window", "above_window"],
        checker_spec={
            "kind": "window",
            "vin": "sensor_level",
            "inside": "inside_window",
            "below": "below_window",
            "above": "above_window",
        },
        prompt_intent="Classify a sensor voltage into below-window, inside-window, and above-window flags.",
    ),
    Core(
        slug="analog_limiter",
        kind="limiter",
        title="analog limiter",
        module="balanced_analog_limiter",
        inputs=["raw_level", "vdd", "vss"],
        outputs=["limited_level"],
        checker_spec={"kind": "limiter", "vin": "raw_level", "vout": "limited_level"},
        prompt_intent="Model a bounded analog transfer that follows the input in the middle range and clamps outside limits.",
    ),
    Core(
        slug="pulse_stretcher",
        kind="pulse",
        title="event pulse stretcher",
        module="balanced_pulse_stretcher",
        inputs=["event_in", "vdd", "vss"],
        outputs=["stretched_pulse"],
        checker_spec={"kind": "pulse", "trigger": "event_in", "vout": "stretched_pulse", "min_high_samples": 50},
        prompt_intent="Convert each rising input event into a finite-width output pulse and return low afterwards.",
    ),
]


TASK_FORMS = [
    ("end-to-end", "e2e"),
    ("dut-only/spec-to-va", "dut"),
    ("tb-generation", "tb"),
    ("bugfix", "bugfix"),
]

SOURCE_TASKS = {
    "threshold_detector": "v2_ext_threshold_detector_000",
    "window_detector": "v2_ext_window_detector_000",
    "analog_limiter": "v2_ext_limiter_model_000",
    "pulse_stretcher": "v2_ext_pulse_stretcher_000",
}

FAMILY_TO_TASK_FORM = {
    "end-to-end": "end-to-end",
    "spec-to-va": "dut-only/spec-to-va",
    "tb-generation": "tb-generation",
    "bugfix": "bugfix",
}

TASK_FORM_TO_FAMILY = {
    "end-to-end": "end-to-end",
    "dut-only/spec-to-va": "spec-to-va",
    "tb-generation": "tb-generation",
    "bugfix": "bugfix",
}

FORM_SUFFIX = {
    "end-to-end": "e2e",
    "dut-only/spec-to-va": "dut",
    "tb-generation": "tb",
    "bugfix": "bugfix",
}

SOURCE_FORM_PRIORITY = (
    "end-to-end",
    "dut-only/spec-to-va",
    "tb-generation",
    "bugfix",
)


def _task_id(meta: dict[str, Any], task_dir: Path) -> str:
    return str(meta.get("task_id") or meta.get("id") or task_dir.name)


def _original_core_function(meta: dict[str, Any], task_id: str) -> str:
    """Use the existing category as the first stable core-function label.

    The original 92 were not authored with a strict core-function ontology, so
    preserving the public category is less lossy than inventing a brittle name
    mapping at materialization time.
    """
    return str(meta.get("core_function") or meta.get("category") or "unknown")


def _original_checker(source_task_id: str) -> str:
    return f'''#!/usr/bin/env python3
from pathlib import Path
import json
import sys

TASK_DIR = Path(__file__).resolve().parent
ROOT = TASK_DIR.parents[2]
sys.path.insert(0, str(ROOT / "runners"))
from simulate_evas import evaluate_behavior  # noqa: E402


def check_csv(csv_path):
    meta = json.loads((TASK_DIR / "meta.json").read_text(encoding="utf-8"))
    source_task_id = meta.get("source_task_id", {source_task_id!r})
    score, notes = evaluate_behavior(source_task_id, Path(csv_path))
    return {{"pass": score >= 1.0, "score": score, "notes": notes}}


if __name__ == "__main__":
    print(json.dumps(check_csv(sys.argv[1]), indent=2))
'''


def _copy_original92_tasks(manifest: list[dict[str, Any]]) -> None:
    for meta_path in sorted(ORIGINAL_TASK_ROOT.rglob("meta.json")):
        src_dir = meta_path.parent
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        source_task_id = _task_id(meta, src_dir)
        dst_task_id = f"original92_{source_task_id}"
        dst_dir = TASK_ROOT / dst_task_id
        if dst_dir.exists():
            shutil.rmtree(dst_dir)
        shutil.copytree(src_dir, dst_dir)

        source_family = str(meta.get("family") or "unknown")
        enriched = dict(meta)
        enriched.update(
            {
                "task_id": dst_task_id,
                "benchmark_split": "benchmark-balanced",
                "source_collection": "original92",
                "source_task_id": source_task_id,
                "source_family": source_family,
                "source_relative_path": str(src_dir.relative_to(ROOT)),
                "core_function": _original_core_function(meta, source_task_id),
                "task_form": FAMILY_TO_TASK_FORM.get(source_family, source_family),
                "balanced_role": "imported_original92",
                "promotion_status": "imported_original92_with_normalized_metadata",
            }
        )
        (dst_dir / "meta.json").write_text(json.dumps(enriched, indent=2), encoding="utf-8")
        if not (dst_dir / "checker.py").exists():
            (dst_dir / "checker.py").write_text(_original_checker(source_task_id), encoding="utf-8")

        manifest.append(
            {
                "task_id": dst_task_id,
                "source_collection": "original92",
                "source_task_id": source_task_id,
                "core_function": enriched["core_function"],
                "task_form": enriched["task_form"],
                "status": "imported_original92_with_normalized_metadata",
                "gold_required": (dst_dir / "gold").is_dir(),
                "checker_required": True,
                "spectre_parity_required": True,
            }
        )


def _original_entries() -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for meta_path in sorted(ORIGINAL_TASK_ROOT.rglob("meta.json")):
        task_dir = meta_path.parent
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        source_task_id = _task_id(meta, task_dir)
        family = str(meta.get("family") or "unknown")
        entries.append(
            {
                "task_id": source_task_id,
                "task_dir": task_dir,
                "meta": meta,
                "family": family,
                "task_form": FAMILY_TO_TASK_FORM.get(family, family),
                "core_function": _original_core_function(meta, source_task_id),
            }
        )
    return entries


def _slug(text: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in text.lower()).strip("_")


def _representative_for_core(entries: list[dict[str, Any]], core: str) -> dict[str, Any]:
    core_entries = [entry for entry in entries if entry["core_function"] == core]
    for form in SOURCE_FORM_PRIORITY:
        candidates = [entry for entry in core_entries if entry["task_form"] == form]
        if candidates:
            return sorted(candidates, key=lambda item: item["task_id"])[0]
    return sorted(core_entries, key=lambda item: item["task_id"])[0]


def _completion_prompt(source_prompt: str, *, core: str, source_task_id: str, target_form: str) -> str:
    header: list[str]
    if target_form == "end-to-end":
        header = [
            "Create an end-to-end Verilog-A evaluation case for the core function below.",
            "Return the DUT Verilog-A model and a minimal Spectre/EVAS testbench.",
        ]
    elif target_form == "dut-only/spec-to-va":
        header = [
            "Create only the DUT Verilog-A model for the core function below.",
            "Do not generate a testbench; the evaluator will use a fixed public harness.",
        ]
    elif target_form == "tb-generation":
        header = [
            "Create only a Spectre/EVAS testbench for the core function below.",
            "The DUT Verilog-A model will be provided by the evaluator.",
        ]
    elif target_form == "bugfix":
        header = [
            "Fix a Verilog-A implementation for the core function below without changing its public behavior.",
            "Return the corrected Verilog-A artifact requested by the benchmark.",
        ]
    else:
        raise ValueError(target_form)

    return "\n".join(
        [
            *header,
            "",
            f"Core function family: {core}.",
            f"Balanced task-form completion derived from original task: `{source_task_id}`.",
            "",
            "Spectre/Verilog-A compatibility requirements:",
            "- Use voltage-domain electrical ports where applicable.",
            "- Keep the public interface and saved observable behavior compatible with the evaluation harness.",
            "- Prefer explicit `transition(...)` on driven voltage outputs.",
            "- Avoid current contributions, `ddt()`, `idt()`, simulator control blocks, and non-Spectre syntax.",
            "",
            "Source behavioral specification:",
            "",
            source_prompt.strip(),
            "",
        ]
    )


def _materialize_original92_taskform_completions(manifest: list[dict[str, Any]]) -> None:
    entries = _original_entries()
    forms = [form for form, _suffix in TASK_FORMS]
    by_core: dict[str, set[str]] = {}
    for entry in entries:
        by_core.setdefault(entry["core_function"], set()).add(entry["task_form"])

    for core in sorted(by_core):
        missing_forms = [form for form in forms if form not in by_core[core]]
        if not missing_forms:
            continue
        representative = _representative_for_core(entries, core)
        source_dir = representative["task_dir"]
        source_task_id = representative["task_id"]
        source_prompt = (source_dir / "prompt.md").read_text(encoding="utf-8", errors="ignore")

        for target_form in missing_forms:
            suffix = FORM_SUFFIX[target_form]
            task_id = f"completion92_{_slug(core)}_{suffix}"
            task_dir = TASK_ROOT / task_id
            if task_dir.exists():
                shutil.rmtree(task_dir)
            shutil.copytree(source_dir, task_dir)

            meta = dict(representative["meta"])
            meta.update(
                {
                    "task_id": task_id,
                    "benchmark_split": "benchmark-balanced",
                    "source_collection": "original92_taskform_completion_v1",
                    "source_task_id": source_task_id,
                    "source_family": representative["family"],
                    "source_relative_path": str(source_dir.relative_to(ROOT)),
                    "core_function": core,
                    "task_form": target_form,
                    "family": TASK_FORM_TO_FAMILY[target_form],
                    "category": core,
                    "balanced_role": "taskform_completion_for_original92_core",
                    "completion_target_form": target_form,
                    "completion_method": "source_gold_recontextualized_as_missing_task_form",
                    "promotion_status": "structural_completion_pending_gold_revalidation",
                }
            )
            (task_dir / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
            (task_dir / "prompt.md").write_text(
                _completion_prompt(source_prompt, core=core, source_task_id=source_task_id, target_form=target_form),
                encoding="utf-8",
            )
            (task_dir / "checker.py").write_text(_original_checker(source_task_id), encoding="utf-8")

            manifest.append(
                {
                    "task_id": task_id,
                    "source_collection": "original92_taskform_completion_v1",
                    "source_task_id": source_task_id,
                    "core_function": core,
                    "task_form": target_form,
                    "status": "structural_completion_pending_gold_revalidation",
                    "gold_required": (task_dir / "gold").is_dir(),
                    "checker_required": True,
                    "spectre_parity_required": True,
                }
            )


def _ports_decl(inputs: list[str], outputs: list[str]) -> str:
    lines = []
    if inputs:
        lines.append("    input " + ", ".join(inputs) + ";")
    if outputs:
        lines.append("    output " + ", ".join(outputs) + ";")
    lines.append("    electrical " + ", ".join(inputs + outputs) + ";")
    return "\n".join(lines)


def _va(core: Core, *, buggy: bool = False) -> str:
    module = core.module
    ports = core.inputs + core.outputs
    if core.kind == "threshold":
        condition = "V(sense_level) < threshold" if buggy else "V(sense_level) >= threshold"
        body = f"""    parameter real threshold = 0.45;
    parameter real tr = 40p;
    real out_t;

    analog begin
        out_t = ({condition}) ? V(vdd) : V(vss);
        V(decision_level) <+ transition(out_t, 0.0, tr, tr);
    end"""
    elif core.kind == "window":
        if buggy:
            assigns = """        below_t = (V(sensor_level) > hi) ? V(vdd) : V(vss);
        above_t = (V(sensor_level) < lo) ? V(vdd) : V(vss);
        inside_t = (V(sensor_level) >= lo && V(sensor_level) <= hi) ? V(vdd) : V(vss);"""
        else:
            assigns = """        below_t = (V(sensor_level) < lo) ? V(vdd) : V(vss);
        above_t = (V(sensor_level) > hi) ? V(vdd) : V(vss);
        inside_t = (V(sensor_level) >= lo && V(sensor_level) <= hi) ? V(vdd) : V(vss);"""
        body = f"""    parameter real lo = 0.25;
    parameter real hi = 0.65;
    parameter real tr = 40p;
    real inside_t;
    real below_t;
    real above_t;

    analog begin
{assigns}
        V(inside_window) <+ transition(inside_t, 0.0, tr, tr);
        V(below_window) <+ transition(below_t, 0.0, tr, tr);
        V(above_window) <+ transition(above_t, 0.0, tr, tr);
    end"""
    elif core.kind == "limiter":
        clamp = "" if buggy else """        if (y < vlo) y = vlo;
        if (y > vhi) y = vhi;"""
        body = f"""    parameter real vlo = 0.18;
    parameter real vhi = 0.72;
    parameter real tr = 40p;
    real y;

    analog begin
        y = V(raw_level);
{clamp}
        V(limited_level) <+ transition(y, 0.0, tr, tr);
    end"""
    elif core.kind == "pulse":
        if buggy:
            body = """    parameter real vth = 0.45;
    parameter real tr = 40p;

    analog begin
        V(stretched_pulse) <+ transition((V(event_in) >= vth) ? V(vdd) : V(vss), 0.0, tr, tr);
    end"""
        else:
            body = """    parameter real vth = 0.45;
    parameter real width = 4.0n;
    parameter real tr = 40p;
    integer pulse_q;
    real clear_t;

    analog begin
        @(initial_step) begin
            pulse_q = 0;
            clear_t = 1.0;
        end

        @(cross(V(event_in) - vth, +1)) begin
            pulse_q = 1;
            clear_t = $abstime + width;
        end

        @(timer(clear_t)) begin
            pulse_q = 0;
            clear_t = 1.0;
        end

        V(stretched_pulse) <+ transition(pulse_q ? V(vdd) : V(vss), 0.0, tr, tr);
    end"""
    else:
        raise ValueError(core.kind)

    return f"""`include "constants.vams"
`include "disciplines.vams"

module {module}({", ".join(ports)});
{_ports_decl(core.inputs, core.outputs)}
{body}
endmodule
"""


def _stimulus(core: Core) -> list[str]:
    if core.kind == "threshold":
        return ["Vsig (sense_level 0) vsource type=pwl wave=[ 0 0 20n 0.2 45n 0.7 70n 0.3 95n 0.85 120n 0.1 ]"]
    if core.kind == "window":
        return ["Vsig (sensor_level 0) vsource type=pwl wave=[ 0 0.1 20n 0.1 40n 0.45 70n 0.45 90n 0.82 120n 0.82 ]"]
    if core.kind == "limiter":
        return ["Vsig (raw_level 0) vsource type=pwl wave=[ 0 0.0 25n 0.1 50n 0.45 75n 0.85 100n 0.9 120n 0.35 ]"]
    if core.kind == "pulse":
        return ["Vtrig (event_in 0) vsource type=pulse val0=0 val1=0.9 delay=5n rise=40p fall=40p width=600p period=18n"]
    raise ValueError(core.kind)


def _tb(core: Core) -> str:
    stop = "140n" if core.kind == "pulse" else "120n"
    maxstep = "200p" if core.kind == "pulse" else "500p"
    return "\n".join(
        [
            "simulator lang=spectre",
            "global 0",
            "",
            'ahdl_include "dut.va"',
            "",
            "Vvdd (vdd 0) vsource dc=0.9",
            "Vvss (vss 0) vsource dc=0",
            *_stimulus(core),
            "",
            f"XDUT ({' '.join(core.inputs + core.outputs)}) {core.module}",
            "",
            f"tran tran stop={stop} maxstep={maxstep}",
            "save " + " ".join([name for name in core.inputs + core.outputs if name not in {"vdd", "vss"}]),
            "",
        ]
    )


def _prompt(core: Core, task_form: str, task_id: str) -> str:
    port_lines = [
        f"- Inputs: `{', '.join(core.inputs)}`.",
        f"- Outputs: `{', '.join(core.outputs)}`.",
    ]
    if task_form == "end-to-end":
        lead = [
            f"Write a pure Verilog-A module named `{core.module}` and a minimal Spectre/EVAS testbench.",
            "",
            "Return two files: `dut.va` and `tb_ref.scs`.",
        ]
    elif task_form == "dut-only/spec-to-va":
        lead = [
            f"Write only the pure Verilog-A DUT module named `{core.module}`.",
            "",
            "Do not include a testbench. The evaluator will use a fixed public harness.",
        ]
    elif task_form == "tb-generation":
        lead = [
            f"Given a voltage-domain DUT module named `{core.module}`, generate only a Spectre/EVAS testbench.",
            "",
            "The DUT file will be available as `dut.va`; include it with `ahdl_include \"dut.va\"` and instantiate by positional ports.",
        ]
    elif task_form == "bugfix":
        lead = [
            f"The following Verilog-A module named `{core.module}` has a behavioral bug. Fix it without changing the public interface.",
            "",
            "```verilog-a",
            _va(core, buggy=True).strip(),
            "```",
            "",
            "Return exactly one fixed Verilog-A file named `dut.va`.",
        ]
    else:
        raise ValueError(task_form)

    common = [
        "",
        f"Core function: {core.title}.",
        f"Behavioral intent: {core.prompt_intent}",
        "",
        "Public interface:",
        *port_lines,
        "",
        "Compatibility requirements:",
        "- Use voltage-domain electrical ports only.",
        "- Be compatible with real Cadence Spectre.",
        "- Declare port direction and electrical discipline separately.",
        "- Drive output targets with `transition(...)`.",
        "- Do not use current contributions, `ddt()`, or `idt()`.",
        "",
        "Public evaluation contract:",
        "- The checker reads the saved public input/output waveform columns.",
        "- The task should exercise all required observable behavior, including low/high or below/inside/above regions where applicable.",
    ]
    return "\n".join(lead + common) + "\n"


def _checker() -> str:
    return """#!/usr/bin/env python3
from pathlib import Path
import importlib.util
import json

TASK_DIR = Path(__file__).resolve().parent
COMMON = TASK_DIR.parents[1] / "common_checker.py"
spec = importlib.util.spec_from_file_location("benchmark_balanced_common_checker", COMMON)
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


def _common_checker() -> str:
    return '''#!/usr/bin/env python3
"""Shared checkers for benchmark-balanced tasks.

This file deliberately reuses the already Spectre-validated benchmark-v2
checker kernels so the balanced split does not fork scoring semantics.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

COMMON = Path(__file__).resolve().parents[1] / "benchmark-v2" / "common_checker.py"
spec = importlib.util.spec_from_file_location("benchmark_v2_common_checker", COMMON)
_module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(_module)

check_csv = _module.check_csv
check_with_meta = _module.check_with_meta
'''


def _checks_yaml(core: Core) -> str:
    return "\n".join(
        [
            "syntax:",
            "  must_include:",
            '    - "transition("',
            "  must_not_include:",
            '    - "I("',
            '    - "ddt("',
            '    - "idt("',
            "dut_compile:",
            '  backend: "evas"',
            "tb_compile:",
            '  backend: "evas"',
            "sim_correct:",
            "  checks:",
            f'    - "{core.kind}_behavior"',
            "parity:",
            "  required: true",
            '  tolerance_notes: "Gold must pass both EVAS and real Spectre."',
            "",
        ]
    )


def materialize() -> list[dict[str, Any]]:
    if TASK_ROOT.exists():
        shutil.rmtree(TASK_ROOT)
    TASK_ROOT.mkdir(parents=True)
    (BENCH / "common_checker.py").write_text(_common_checker(), encoding="utf-8")

    manifest: list[dict[str, Any]] = []
    _copy_original92_tasks(manifest)
    _materialize_original92_taskform_completions(manifest)
    for core in CORES:
        for task_form, suffix in TASK_FORMS:
            task_id = f"balanced_{core.slug}_{suffix}"
            task_dir = TASK_ROOT / task_id
            gold = task_dir / "gold"
            gold.mkdir(parents=True)
            (task_dir / "prompt.md").write_text(_prompt(core, task_form, task_id), encoding="utf-8")
            (task_dir / "checker.py").write_text(_checker(), encoding="utf-8")
            (task_dir / "checks.yaml").write_text(_checks_yaml(core), encoding="utf-8")
            (gold / "dut.va").write_text(_va(core), encoding="utf-8")
            (gold / "tb_ref.scs").write_text(_tb(core), encoding="utf-8")
            meta = {
                "task_id": task_id,
                "family": TASK_FORM_TO_FAMILY[task_form],
                "benchmark_split": "benchmark-balanced",
                "source_collection": "balanced_supplement_v1",
                "source": "benchmark-v2 external architecture representative",
                "source_task": SOURCE_TASKS[core.slug],
                "core_function": core.slug,
                "task_form": task_form,
                "category": core.slug,
                "domain": "voltage",
                "difficulty": "easy" if task_form != "bugfix" else "medium",
                "expected_backend": "evas",
                "scoring": ["dut_compile", "tb_compile", "sim_correct"],
                "gold": {"dut": "gold/dut.va", "tb": "gold/tb_ref.scs"},
                "v2_checker_spec": core.checker_spec,
                "promotion_status": "benchmark_balanced_v1_gold_validated",
            }
            (task_dir / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
            manifest.append(
                {
                    "task_id": task_id,
                    "source_collection": "balanced_supplement_v1",
                    "core_function": core.slug,
                    "task_form": task_form,
                    "status": "gold_validated_evas_spectre",
                    "gold_required": True,
                    "checker_required": True,
                    "spectre_parity_required": True,
                }
            )

    (BENCH / "manifest.json").write_text(json.dumps({"tasks": manifest}, indent=2), encoding="utf-8")
    (BENCH / "README.md").write_text(_readme(manifest), encoding="utf-8")
    return manifest


def _readme(manifest: list[dict[str, Any]]) -> str:
    source_counts = Counter(item.get("source_collection", "unknown") for item in manifest)
    task_form_counts = Counter(item.get("task_form", "unknown") for item in manifest)
    core_counts = Counter(item.get("core_function", "unknown") for item in manifest)
    supplement = [item for item in manifest if item.get("source_collection") == "balanced_supplement_v1"]
    supplement_rows = "\n".join(
        f"| `{item['task_id']}` | {item['core_function']} | {item['task_form']} |"
        for item in supplement
    )
    source_rows = "\n".join(
        f"| {source} | {count} |"
        for source, count in sorted(source_counts.items())
    )
    form_rows = "\n".join(
        f"| {form} | {count} |"
        for form, count in sorted(task_form_counts.items())
    )
    core_rows = "\n".join(
        f"| {core} | {count} |"
        for core, count in sorted(core_counts.items())
    )
    return f"""# Benchmark Balanced

This split is a task-form-balanced benchmark expansion. It does not modify the
original 92-task tree. Instead, it imports the original 92 with normalized
metadata, fills the missing task-form cells for the original 92 core-function
families, and adds a small set of external task-form-balanced supplement tasks.

Total tasks: **{len(manifest)}**

| source collection | count |
|---|---:|
{source_rows}

| task form | count |
|---|---:|
{form_rows}

| core function | count |
|---|---:|
{core_rows}

## Original 92 Task-Form Completion

The original 92 use the public `category` field as the first-pass core-function
label. Under that ontology, 18 original core-function families are present. This
split adds 35 `completion92_*` tasks so every original core-function family has
at least one task in each of the four forms:

- end-to-end
- DUT/spec-to-VA
- testbench generation
- bugfix

The completion tasks are marked as `original92_taskform_completion_v1` in
`manifest.json`. They keep a `source_task_id` pointing to the original task used
as the seed artifact.

## External Balanced Supplement

It covers four external core functions:

- threshold detector
- window detector
- analog limiter
- event pulse stretcher

Each core function is materialized in four task forms:

- end-to-end
- DUT/spec-to-VA (`dut-only`)
- testbench generation
- bugfix

| task id | core function | task form |
|---|---|---|
{supplement_rows}

## Gold Validation

The 16 added supplement gold artifacts were validated on 2026-04-30:

| backend | result |
|---|---:|
| EVAS | 16/16 PASS |
| real Spectre | 16/16 PASS |

A four-task smoke sample from `original92_taskform_completion_v1` was also
validated:

| backend | result |
|---|---:|
| EVAS | 4/4 PASS |
| real Spectre | 4/4 PASS |

Reproduce supplement validation from `behavioral-veriloga-eval/`:

```bash
python3 runners/materialize_benchmark_balanced_tasks.py
python3 runners/validate_benchmark_v2_gold.py \\
  --bench-dir benchmark-balanced \\
  --family benchmark-balanced \\
  --backend evas \\
  --output-dir results/benchmark-balanced-supplement-gold-evas-2026-04-30-r2 \\
  --timeout-s 180 \\
  --task balanced_threshold_detector_e2e \\
  --task balanced_threshold_detector_dut \\
  --task balanced_threshold_detector_tb \\
  --task balanced_threshold_detector_bugfix \\
  --task balanced_window_detector_e2e \\
  --task balanced_window_detector_dut \\
  --task balanced_window_detector_tb \\
  --task balanced_window_detector_bugfix \\
  --task balanced_analog_limiter_e2e \\
  --task balanced_analog_limiter_dut \\
  --task balanced_analog_limiter_tb \\
  --task balanced_analog_limiter_bugfix \\
  --task balanced_pulse_stretcher_e2e \\
  --task balanced_pulse_stretcher_dut \\
  --task balanced_pulse_stretcher_tb \\
  --task balanced_pulse_stretcher_bugfix
python3 runners/validate_benchmark_v2_gold.py \\
  --bench-dir benchmark-balanced \\
  --family benchmark-balanced \\
  --backend spectre \\
  --output-dir results/benchmark-balanced-supplement-gold-spectre-2026-04-30-r2 \\
  --timeout-s 180 \\
  --spectre-mode spectre \\
  --task balanced_threshold_detector_e2e \\
  --task balanced_threshold_detector_dut \\
  --task balanced_threshold_detector_tb \\
  --task balanced_threshold_detector_bugfix \\
  --task balanced_window_detector_e2e \\
  --task balanced_window_detector_dut \\
  --task balanced_window_detector_tb \\
  --task balanced_window_detector_bugfix \\
  --task balanced_analog_limiter_e2e \\
  --task balanced_analog_limiter_dut \\
  --task balanced_analog_limiter_tb \\
  --task balanced_analog_limiter_bugfix \\
  --task balanced_pulse_stretcher_e2e \\
  --task balanced_pulse_stretcher_dut \\
  --task balanced_pulse_stretcher_tb \\
  --task balanced_pulse_stretcher_bugfix
```
"""


def main() -> int:
    manifest = materialize()
    print(f"[benchmark-balanced] wrote {len(manifest)} tasks under {TASK_ROOT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
