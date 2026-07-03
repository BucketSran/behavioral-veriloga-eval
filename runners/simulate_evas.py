#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import atexit
import contextlib
import csv
import inspect
import io
import json
import math
import multiprocessing as mp
import os
import queue
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import warnings
from pathlib import Path
from typing import Iterable

from main120_stable_checks import (
    check_background_calibration_accumulator as check_vbm1_background_calibration_accumulator,
    check_barrel_pointer_window as check_vbm1_barrel_pointer_window,
    check_cdac_calibration as check_vbm1_cdac_calibration,
    check_debounce_latch as check_vbm1_debounce_latch,
    check_edge_detector as check_vbm1_edge_detector,
    check_element_shuffler as check_vbm1_element_shuffler,
    check_file_metric_writer as check_vbm1_file_metric_writer,
    check_first_order_lowpass as check_vbm1_first_order_lowpass,
    check_gain_trim_controller as check_vbm1_gain_trim_controller,
    check_leaky_hold as check_vbm1_leaky_hold,
    check_lock_detector as check_vbm1_lock_detector,
    check_one_shot_timer as check_vbm1_one_shot_timer,
    check_offset_calibration_fsm as check_vbm1_offset_calibration_fsm,
    check_offset_comparator as check_vbm1_offset_comparator,
    check_peak_detector as check_vbm1_peak_detector,
    check_precision_rectifier as check_vbm1_precision_rectifier,
    check_resettable_counter_divider as check_vbm1_resettable_counter_divider,
    check_resettable_integrator as check_vbm1_resettable_integrator,
    check_rotating_element_selector as check_vbm1_rotating_element_selector,
    check_sar_logic_4b as check_vbm1_sar_logic_4b,
    check_segmented_dac as check_vbm1_segmented_dac,
    check_settling_time_measurement_tb as check_vbm1_settling_time_measurement_tb,
    check_slew_rate_limiter as check_vbm1_slew_rate_limiter,
    check_strongarm_comparator_behavior as check_vbm1_strongarm_comparator_behavior,
    check_thermometer_dac as check_vbm1_thermometer_dac,
    check_thermometer_decoder_guarded as check_vbm1_thermometer_decoder_guarded,
    check_track_hold_aperture as check_vbm1_track_hold_aperture,
    check_vco_phase_integrator as check_vbm1_vco_phase_integrator,
    check_voltage_clamp as check_vbm1_voltage_clamp,
)


def read_meta(task_dir: Path) -> dict:
    meta_path = task_dir / "meta.json"
    if meta_path.exists():
        return json.loads(meta_path.read_text(encoding="utf-8"))
    release_task_path = task_dir / "task_release_card.json"
    if not release_task_path.exists():
        release_task_path = task_dir / "release_task.json"
    if release_task_path.exists():
        release_task = json.loads(release_task_path.read_text(encoding="utf-8"))
        return {
            "id": release_task.get("id"),
            "task_id": release_task.get("id"),
            "release_entry_id": release_task.get("release_entry_id"),
            "form": release_task.get("family"),
            "scoring": ["dut_compile", "tb_compile", "sim_correct"],
        }
    raise FileNotFoundError(f"missing meta.json, task_release_card.json, or release_task.json in {task_dir}")


def _extract_yaml_list_after_key(text: str, key: str) -> list[str]:
    lines = text.splitlines()
    for line_index, line in enumerate(lines):
        if line.strip() != f"{key}:":
            continue
        base_indent = len(line) - len(line.lstrip())
        items: list[str] = []
        for raw in lines[line_index + 1 :]:
            stripped = raw.strip()
            if not stripped:
                continue
            indent = len(raw) - len(raw.lstrip())
            if indent <= base_indent and not stripped.startswith("- "):
                break
            if stripped.startswith("- "):
                items.append(stripped[2:].strip().strip('"').strip("'"))
        return items
    return []


def _extract_yaml_scalar_after_parent(text: str, parent: str, key: str) -> str | None:
    lines = text.splitlines()
    for line_index, line in enumerate(lines):
        if line.strip() != f"{parent}:":
            continue
        base_indent = len(line) - len(line.lstrip())
        for raw in lines[line_index + 1 :]:
            stripped = raw.strip()
            if not stripped:
                continue
            indent = len(raw) - len(raw.lstrip())
            if indent <= base_indent:
                break
            prefix = f"{key}:"
            if stripped.startswith(prefix):
                return stripped[len(prefix):].strip().strip('"').strip("'")
    return None


def _extract_yaml_mapping_after_parent(text: str, parent: str) -> dict[str, str]:
    lines = text.splitlines()
    for line_index, line in enumerate(lines):
        if line.strip() != f"{parent}:":
            continue
        base_indent = len(line) - len(line.lstrip())
        mapping: dict[str, str] = {}
        for raw in lines[line_index + 1 :]:
            stripped = raw.strip()
            if not stripped:
                continue
            indent = len(raw) - len(raw.lstrip())
            if indent <= base_indent:
                break
            if stripped.startswith("- ") or ":" not in stripped:
                continue
            key, value = stripped.split(":", 1)
            value = value.strip()
            if value:
                mapping[key.strip()] = value.strip('"').strip("'")
        return mapping
    return {}


def _float_values(values: list[str]) -> list[float]:
    parsed: list[float] = []
    for value in values:
        try:
            parsed.append(float(value))
        except ValueError:
            continue
    return parsed


def load_v2_checks_config(task_dir: Path) -> dict[str, object]:
    for checks_path in (
        task_dir / "private" / "invisible_checker_config.yaml",
        task_dir / "checks.yaml",
        task_dir / "private" / "checks.yaml",
    ):
        if not checks_path.exists():
            continue
        checks_text = checks_path.read_text(encoding="utf-8")
        if "vabench-release-v2-checks" not in checks_text:
            continue
        checker_parameters: dict[str, object] = _extract_yaml_mapping_after_parent(
            checks_text,
            "checker_parameters",
        )
        sample_times_ns = _float_values(_extract_yaml_list_after_key(checks_text, "sample_times_ns"))
        if sample_times_ns:
            checker_parameters["sample_times_ns"] = sample_times_ns
        return {
            "path": checks_path,
            "checker_task_id": _extract_yaml_scalar_after_parent(checks_text, "checker", "task_id"),
            "syntax_must_include": _extract_yaml_list_after_key(checks_text, "must_include"),
            "syntax_must_not_include": _extract_yaml_list_after_key(checks_text, "must_not_include"),
            "checker_parameters": checker_parameters,
        }
    return {}


def v2_checks_syntax_failures(checks_config: dict[str, object], run_dir: Path) -> list[str]:
    if not checks_config:
        return []
    source_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in sorted([*run_dir.glob("*.va"), *run_dir.glob("*.scs")])
    )
    failures: list[str] = []
    for phrase in checks_config.get("syntax_must_include", []):
        if str(phrase) and str(phrase) not in source_text:
            failures.append(f"checker_config_must_include_missing={phrase}")
    for phrase in checks_config.get("syntax_must_not_include", []):
        if str(phrase) and str(phrase) in source_text:
            failures.append(f"checker_config_must_not_include_present={phrase}")
    return failures


def read_task_artifact_targets(task_dir: Path) -> list[str]:
    return _read_task_artifact_list(task_dir, "target")


def read_task_artifact_supports(task_dir: Path) -> list[str]:
    return _read_task_artifact_list(task_dir, "support")


def _read_task_artifact_list(task_dir: Path, key: str) -> list[str]:
    task_toml = task_dir / "task.toml"
    if not task_toml.exists():
        return []
    text = task_toml.read_text(encoding="utf-8", errors="ignore")
    match = re.search(rf"(?m)^\s*{re.escape(key)}\s*=\s*(\[[^\n]*\])", text)
    if not match:
        return []
    try:
        parsed = ast.literal_eval(match.group(1))
    except (SyntaxError, ValueError):
        return []
    if not isinstance(parsed, list):
        return []
    targets: list[str] = []
    for item in parsed:
        name = str(item).strip()
        if name and "/" not in name and "\\" not in name:
            targets.append(name)
    return targets


def copy_inputs(
    run_dir: Path,
    dut_path: Path,
    tb_path: Path,
    *,
    target_filenames: Iterable[str] = (),
    primary_target_filename: str | None = None,
    companion_search_dirs: Iterable[Path] = (),
) -> tuple[Path, Path]:
    example_dir = tb_path.parent
    for src in example_dir.iterdir():
        dst = run_dir / src.name
        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)

    # If the candidate DUT lives outside the example directory, stage it too.
    # Multi-artifact DUT tasks may need companion Verilog-A files from the
    # same directory as the main candidate.
    if dut_path.parent != example_dir:
        for src in sorted(dut_path.parent.glob("*.va")):
            shutil.copy2(src, run_dir / src.name)
        shutil.copy2(dut_path, run_dir / dut_path.name)

    # Negative variants often keep their own filenames, while the Spectre deck
    # includes the canonical artifact name from task.toml. Stage the selected
    # DUT under that canonical name too so failures are behavioral, not a stale
    # include-name mismatch.
    for target_name in target_filenames:
        target_path = run_dir / target_name
        if target_path.exists() or target_path.name == dut_path.name:
            continue
        if primary_target_filename is not None and target_name == primary_target_filename:
            shutil.copy2(dut_path, target_path)
            continue
        copied_companion = False
        for search_dir in companion_search_dirs:
            companion_path = search_dir / target_name
            if companion_path.exists() and companion_path.is_file():
                shutil.copy2(companion_path, target_path)
                copied_companion = True
                break
        if not copied_companion:
            shutil.copy2(dut_path, target_path)

    dut_dst = run_dir / dut_path.name
    tb_dst = run_dir / tb_path.name
    return dut_dst, tb_dst


REPO_ROOT = Path(__file__).resolve().parents[1]


def evas_module_python() -> str:
    if sys.version_info >= (3, 9):
        return sys.executable
    system_python = Path("/usr/bin/python3")
    if system_python.exists():
        probe = subprocess.run(
            [str(system_python), "-c", "import sys; raise SystemExit(sys.version_info < (3, 9))"],
            capture_output=True,
            text=True,
            check=False,
        )
        if probe.returncode == 0:
            return str(system_python)
    return sys.executable


def _candidate_evas_source_roots() -> list[Path]:
    roots: list[Path] = []
    explicit = os.environ.get("VAEVAS_EVAS_REPO", "").strip()
    if explicit:
        roots.append(Path(explicit).expanduser())
    roots.extend([REPO_ROOT.parent / "EVAS", REPO_ROOT / "EVAS"])
    return roots


def evas_source_env() -> dict[str, str] | None:
    for source_root in _candidate_evas_source_roots():
        if (source_root / "evas" / "__main__.py").exists():
            env = os.environ.copy()
            env["PYTHONPATH"] = str(source_root) + os.pathsep + env.get("PYTHONPATH", "")
            return env
    return None


def evas_command_and_env() -> tuple[list[str], dict[str, str] | None]:
    env = evas_source_env()
    if env is not None:
        return [evas_module_python(), "-m", "evas"], env
    evas_cli = shutil.which("evas")
    if evas_cli:
        return [evas_cli], None
    return ["evas"], None


def _env_truthy(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on", "enabled"}


def _persistent_worker_enabled() -> bool:
    # Default-on per RUSTIFICATION_WORKLIST_20260605 decision (P0 087): the
    # accepted trade is speed over per-row isolation; cross-row state leakage
    # is fixed reactively. Set VAEVAS_EVAS_PERSISTENT_WORKER=0 to opt out.
    raw = os.environ.get("VAEVAS_EVAS_PERSISTENT_WORKER", "").strip().lower()
    if raw in {"0", "false", "no", "off", "disabled"}:
        return False
    return True


DEFAULT_EVAS_ENGINE = "evas2"


def default_evas_engine() -> str:
    """Return the benchmark default EVAS engine.

    `EVAS_ENGINE=evas2` is consumed by the EVAS netlist runner and selects the
    strict Rust EVAS2 full-model path.  Keep an explicit environment override
    so legacy Python-EVAS debugging is still possible without editing fixtures.
    """

    return os.environ.get("VAEVAS_DEFAULT_EVAS_ENGINE", DEFAULT_EVAS_ENGINE).strip().lower()


def effective_evas_engine(env: dict[str, str] | None = None) -> str:
    source = env if env is not None else os.environ
    explicit = source.get("EVAS_ENGINE", "").strip().lower()
    return explicit or default_evas_engine()


def _with_default_evas_engine(env: dict[str, str] | None) -> dict[str, str]:
    effective_env = dict(env or os.environ.copy())
    if not effective_env.get("EVAS_ENGINE", "").strip():
        engine = default_evas_engine()
        if engine:
            effective_env["EVAS_ENGINE"] = engine
    return effective_env


def _encode_required_trace_signals(signals: set[str] | frozenset[str] | list[str] | tuple[str, ...] | None) -> str:
    if not signals:
        return ""
    ordered: list[str] = []
    seen: set[str] = set()
    for signal in signals:
        name = str(signal).strip()
        if not name or name.lower() == "time" or name in seen:
            continue
        seen.add(name)
        ordered.append(name)
    return ",".join(sorted(ordered))


class _PersistentEvasWorker:
    def __init__(self) -> None:
        self.cmd = [evas_module_python(), str(Path(__file__).resolve()), "--evas-worker"]
        self.proc = subprocess.Popen(
            self.cmd,
            cwd=str(REPO_ROOT),
            env=_with_default_evas_engine(evas_source_env()),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self._responses: queue.Queue[dict[str, object]] = queue.Queue()
        self._stderr_tail: list[str] = []
        self._lock = threading.Lock()
        threading.Thread(target=self._read_stdout, daemon=True).start()
        threading.Thread(target=self._read_stderr, daemon=True).start()

    def is_alive(self) -> bool:
        return self.proc.poll() is None

    def _read_stdout(self) -> None:
        if self.proc.stdout is None:
            return
        for line in self.proc.stdout:
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                payload = {
                    "returncode": 1,
                    "stdout": "",
                    "stderr": f"evas_worker_protocol_error={exc}: {line[-500:]}",
                }
            if isinstance(payload, dict):
                self._responses.put(payload)

    def _read_stderr(self) -> None:
        if self.proc.stderr is None:
            return
        for line in self.proc.stderr:
            self._stderr_tail.append(line)
            if len(self._stderr_tail) > 200:
                del self._stderr_tail[: len(self._stderr_tail) - 200]

    def _stderr_text(self) -> str:
        return "".join(self._stderr_tail)[-4000:]

    def run(
        self,
        run_dir: Path,
        tb_file: Path,
        output_dir: Path,
        timeout_s: int,
        required_trace_signals: set[str] | frozenset[str] | list[str] | tuple[str, ...] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        if self.proc.stdin is None or not self.is_alive():
            return subprocess.CompletedProcess(
                self.cmd,
                1,
                stdout="",
                stderr=f"evas_worker_not_running\n{self._stderr_text()}",
            )
        request = {
            "run_dir": str(run_dir),
            "tb_file": tb_file.name,
            "output_dir": str(output_dir),
            "required_trace_signals": _encode_required_trace_signals(required_trace_signals),
        }
        with self._lock:
            try:
                self.proc.stdin.write(json.dumps(request) + "\n")
                self.proc.stdin.flush()
                response = self._responses.get(timeout=timeout_s)
            except queue.Empty:
                self.close(kill=True)
                return subprocess.CompletedProcess(
                    self.cmd,
                    -9,
                    stdout="",
                    stderr=f"evas_worker_timeout>{timeout_s}s\n{self._stderr_text()}",
                )
            except OSError as exc:
                return subprocess.CompletedProcess(
                    self.cmd,
                    1,
                    stdout="",
                    stderr=f"evas_worker_write_error={exc}\n{self._stderr_text()}",
                )
        return subprocess.CompletedProcess(
            self.cmd,
            int(response.get("returncode", 1)),
            stdout=str(response.get("stdout", "")),
            stderr=str(response.get("stderr", "")),
        )

    def close(self, *, kill: bool = False) -> None:
        if self.proc.poll() is not None:
            return
        if kill:
            self.proc.kill()
            try:
                self.proc.wait(timeout=1)
            except Exception:
                pass
            return
        try:
            if self.proc.stdin is not None:
                self.proc.stdin.write(json.dumps({"cmd": "shutdown"}) + "\n")
                self.proc.stdin.flush()
            self.proc.wait(timeout=1)
        except Exception:
            try:
                self.proc.terminate()
                self.proc.wait(timeout=1)
            except Exception:
                self.proc.kill()


_worker_state = threading.local()
_worker_registry: list[_PersistentEvasWorker] = []
_worker_registry_lock = threading.Lock()


def _persistent_evas_worker() -> _PersistentEvasWorker:
    worker = getattr(_worker_state, "worker", None)
    if not isinstance(worker, _PersistentEvasWorker) or not worker.is_alive():
        worker = _PersistentEvasWorker()
        _worker_state.worker = worker
        with _worker_registry_lock:
            _worker_registry.append(worker)
    return worker


def _close_persistent_evas_worker() -> None:
    with _worker_registry_lock:
        workers = list(_worker_registry)
        _worker_registry.clear()
    for worker in workers:
        worker.close()


atexit.register(_close_persistent_evas_worker)


def run_evas(
    run_dir: Path,
    tb_file: Path,
    output_dir: Path,
    timeout_s: int,
    required_trace_signals: set[str] | frozenset[str] | list[str] | tuple[str, ...] | None = None,
) -> subprocess.CompletedProcess[str]:
    if _persistent_worker_enabled():
        return _persistent_evas_worker().run(
            run_dir,
            tb_file,
            output_dir,
            timeout_s,
            required_trace_signals=required_trace_signals,
        )
    base_cmd, env = evas_command_and_env()
    cmd = [*base_cmd, "simulate", tb_file.name, "-o", str(output_dir)]
    required_trace_value = _encode_required_trace_signals(required_trace_signals)
    env = _with_default_evas_engine(env)
    env["EVAS_SIDE_EFFECT_OUTPUT_DIR"] = str(output_dir)
    if required_trace_value:
        env["EVAS_REQUIRED_TRACE_SIGNALS"] = required_trace_value
    else:
        env.pop("EVAS_REQUIRED_TRACE_SIGNALS", None)
    return subprocess.run(
        cmd,
        cwd=run_dir,
        capture_output=True,
        text=True,
        timeout=timeout_s,
        env=env,
    )


def _veriloga_code_without_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    return "\n".join(line.split("//", 1)[0] for line in text.splitlines())


SPECTRE_RESERVED_IDENTIFIERS = frozenset(
    {
        # Spectre built-in functions.
        "abs",
        "acos",
        "acosh",
        "asin",
        "asinh",
        "atan",
        "atan2",
        "atanh",
        "ceil",
        "cos",
        "cosh",
        "exp",
        "floor",
        "hypot",
        "ln",
        "log",
        "max",
        "min",
        "pow",
        "sin",
        "sinh",
        "sqrt",
        "tan",
        "tanh",
        # Spectre/AHDL library functions and event helpers.
        "above",
        "analysis",
        "cross",
        "ddt",
        "final_step",
        "flicker_noise",
        "idt",
        "initial_step",
        "last_crossing",
        "limexp",
        "noise_table",
        "slew",
        "timer",
        "transition",
        "white_noise",
        # Verilog-A declaration/control keywords that must not become names.
        "analog",
        "begin",
        "case",
        "electrical",
        "else",
        "end",
        "endmodule",
        "for",
        "if",
        "inout",
        "input",
        "integer",
        "module",
        "output",
        "parameter",
        "real",
        "while",
    }
)


DECLARATION_STARTERS = frozenset(
    {
        "electrical",
        "genvar",
        "inout",
        "input",
        "integer",
        "output",
        "real",
    }
)


def _strip_veriloga_ranges_and_attributes(text: str) -> str:
    # Ranges may include macro expressions such as [`NUM_BITS-1:0].
    text = re.sub(r"\[[^\]]*\]", " ", text)
    text = re.sub(r"\b(?:from|exclude)\s*\([^)]*\)", " ", text)
    text = re.sub(r"\b(?:from|exclude)\s*\[[^\]]*\]", " ", text)
    return text


def _declared_identifier_tokens(declaration_tail: str) -> list[str]:
    cleaned = _strip_veriloga_ranges_and_attributes(declaration_tail)
    cleaned = re.sub(
        r"\b(?:input|output|inout|electrical|real|integer|parameter|genvar|reg|wire|logic)\b",
        " ",
        cleaned,
    )
    names: list[str] = []
    for part in cleaned.split(","):
        part = part.strip()
        if not part:
            continue
        part = part.split("=", 1)[0].strip()
        match = re.match(r"([A-Za-z_][A-Za-z0-9_$]*)", part)
        if match:
            names.append(match.group(1))
    return names


def _module_header_identifiers(code: str) -> list[tuple[str, str]]:
    identifiers: list[tuple[str, str]] = []
    for match in re.finditer(
        r"\bmodule\s+([A-Za-z_][A-Za-z0-9_$]*)\s*\((.*?)\)\s*;",
        code,
        flags=re.DOTALL,
    ):
        module_name, port_text = match.groups()
        identifiers.append(("module", module_name))
        for name in _declared_identifier_tokens(port_text):
            identifiers.append(("module_port", name))
    return identifiers


def _declaration_identifiers(code: str) -> list[tuple[str, str]]:
    identifiers: list[tuple[str, str]] = []
    declaration_re = re.compile(
        r"\b(?:(parameter)\s+(?:real|integer)?|(input|output|inout|electrical|real|integer|genvar))\b([^;]*);",
        flags=re.DOTALL,
    )
    for match in declaration_re.finditer(code):
        kind = "parameter" if match.group(1) else str(match.group(2))
        if kind not in DECLARATION_STARTERS and kind != "parameter":
            continue
        for name in _declared_identifier_tokens(match.group(3)):
            identifiers.append((kind, name))
    return identifiers


def spectre_reserved_identifier_failures(filename: str, code: str) -> list[str]:
    """Return Spectre/AHDL reserved identifier failures for declared names."""
    failures: list[str] = []
    seen: set[tuple[str, str]] = set()
    for context, name in [*_module_header_identifiers(code), *_declaration_identifiers(code)]:
        key = (context, name)
        if key in seen:
            continue
        seen.add(key)
        if name.lower() in SPECTRE_RESERVED_IDENTIFIERS:
            failures.append(f"{filename}:spectre_reserved_identifier:{context}:{name}")
    return failures


def spectre_aligned_veriloga_preflight(run_dir: Path) -> list[str]:
    """Reject .va files outside the shared EVAS/Spectre release subset."""
    failures: list[str] = []
    for path in sorted(run_dir.glob("*.va")):
        try:
            code = _veriloga_code_without_comments(path.read_text(encoding="utf-8", errors="replace"))
        except OSError as exc:
            failures.append(f"{path.name}:read_error={exc}")
            continue
        uses_electrical = re.search(r"\belectrical\b", code) is not None
        has_disciplines = re.search(r"`\s*include\s+\"disciplines\.vams\"", code) is not None
        if uses_electrical and not has_disciplines:
            failures.append(f"{path.name}:missing_disciplines_vams")
        if re.search(r"\bwhile\s*\(\s*(?:1|1\.0|true)\s*\)|\bforever\b", code):
            failures.append(f"{path.name}:unsupported_unbounded_event_loop")
        failures.extend(spectre_reserved_identifier_failures(path.name, code))
    return failures


FILE_METRIC_WRITER_TASKS = {
    "vbm1_file_metric_writer_dut",
    "vbm1_file_metric_writer_tb",
    "vbm1_file_metric_writer_e2e",
}

FINAL_STEP_FILE_METRIC_TASKS = {
    "final_step_file_metric_smoke",
    "vbr1_l2_measurement_flow_tb",
    "vbr1_l2_measurement_flow_e2e",
}


def _remove_stale_metric_file(task_id: str, run_dir: Path) -> None:
    for name in behavior_side_output_names(task_id):
        metric_path = run_dir / name
        if metric_path.exists():
            metric_path.unlink()


def _rising_crossing_time(rows: list[dict[str, float]], signal: str, threshold: float = 0.45) -> float | None:
    for idx in range(1, len(rows)):
        prev = rows[idx - 1]
        cur = rows[idx]
        t0 = prev.get("time")
        t1 = cur.get("time")
        v0 = prev.get(signal)
        v1 = cur.get(signal)
        if t0 is None or t1 is None or v0 is None or v1 is None:
            continue
        if not (v0 <= threshold < v1):
            continue
        if v1 == v0:
            return t1
        alpha = (threshold - v0) / (v1 - v0)
        return t0 + alpha * (t1 - t0)
    return None


def _parse_metric_time_token(token: str) -> float:
    try:
        return float(token)
    except ValueError:
        pass

    match = re.fullmatch(r"([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)([a-zA-Zµ]*)", token.strip())
    if match is None:
        raise ValueError(token)
    number_text, suffix = match.groups()
    value = float(number_text)
    if "e" in number_text.lower():
        return value
    normalized = suffix.lower().removesuffix("s")
    scale = {
        "f": 1e-15,
        "p": 1e-12,
        "n": 1e-9,
        "u": 1e-6,
        "µ": 1e-6,
        "m": 1e-3,
        "": 1.0,
    }.get(normalized)
    if scale is None:
        raise ValueError(token)
    return value * scale


def _validate_file_metric_output(task_id: str, run_dir: Path, csv_path: Path) -> tuple[bool, str] | None:
    if task_id in FINAL_STEP_FILE_METRIC_TASKS:
        candidate_paths = []
        for path in (run_dir / "candidate.out", csv_path.parent / "candidate.out"):
            if path not in candidate_paths:
                candidate_paths.append(path)
        metric_path = next((path for path in candidate_paths if path.exists()), None)
        if metric_path is None:
            return False, "candidate_file_missing"
        text = metric_path.read_text(encoding="utf-8").strip()
        match = re.fullmatch(
            r"count=([0-9]+)\s+metric=([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)",
            text,
        )
        if match is None:
            return False, f"candidate_file_bad_format={text!r}"
        count = int(match.group(1))
        metric = float(match.group(2))
        ok = count == 4 and abs(metric - 1.0) <= 0.02
        return ok, f"candidate_file_count={count} metric={metric:.3f}"

    if task_id not in FILE_METRIC_WRITER_TASKS:
        return None
    candidate_paths = []
    for path in (run_dir / "metric.out", csv_path.parent / "metric.out"):
        if path not in candidate_paths:
            candidate_paths.append(path)
    metric_path = next((path for path in candidate_paths if path.exists()), None)
    if metric_path is None:
        return False, "metric_file_missing"
    lines = [line.strip() for line in metric_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(lines) != 1:
        return False, f"metric_file_line_count={len(lines)} expected=1"
    parts = lines[0].split()
    if len(parts) != 2 or parts[0] != "cross":
        return False, f"metric_file_bad_format={lines[0]!r}"
    try:
        metric_time = _parse_metric_time_token(parts[1])
    except ValueError:
        return False, f"metric_file_bad_time={parts[1]!r}"
    crossing_time = _rising_crossing_time(load_csv(csv_path), "vin")
    if crossing_time is None:
        return False, "metric_file_no_waveform_crossing"
    delta = abs(metric_time - crossing_time)
    ok = delta <= 1e-9
    return ok, f"metric_file_time={metric_time:.3e} waveform_cross={crossing_time:.3e} delta={delta:.3e}"


def validate_behavior_side_outputs(task_id: str, run_dir: Path, csv_path: Path) -> tuple[bool, str] | None:
    return _validate_file_metric_output(task_id, run_dir, csv_path)


def behavior_side_output_names(task_id: str) -> tuple[str, ...]:
    if task_id in FINAL_STEP_FILE_METRIC_TASKS:
        return ("candidate.out",)
    if task_id in FILE_METRIC_WRITER_TASKS:
        return ("metric.out",)
    return ()


def load_csv(csv_path: Path) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({k: float(v) for k, v in row.items()})
    return rows


def _v11_rows(rows: list[dict[str, float]]) -> tuple[bool, str, list[dict[str, float]]]:
    required = {"time", "clk", "in", "out", "metric", "rst"}
    if not rows:
        return False, "v11_empty_csv", []
    missing = sorted(required - set(rows[0]))
    if missing:
        return False, f"v11_missing_columns={','.join(missing)}", []
    return True, "ok", rows


def _v11_range(rows: list[dict[str, float]], key: str) -> float:
    values = [row[key] for row in rows]
    return max(values) - min(values)


def _v11_window_mean(rows: list[dict[str, float]], key: str, start: float, stop: float) -> float | None:
    values = [row[key] for row in rows if start <= row["time"] <= stop]
    if not values:
        return None
    return sum(values) / len(values)


def _v11_final(rows: list[dict[str, float]], key: str) -> float:
    return rows[-1][key]


def _v11_high_fraction(rows: list[dict[str, float]], key: str, threshold: float = 0.5) -> float:
    if not rows:
        return 0.0
    return sum(1 for row in rows if row[key] > threshold) / len(rows)


def _v11_correlation(rows: list[dict[str, float]], x_key: str, y_key: str) -> float:
    if not rows:
        return 0.0
    xs = [row[x_key] for row in rows]
    ys = [row[y_key] for row in rows]
    x_mean = sum(xs) / len(xs)
    y_mean = sum(ys) / len(ys)
    cov = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
    x_var = sum((x - x_mean) ** 2 for x in xs)
    y_var = sum((y - y_mean) ** 2 for y in ys)
    denom = math.sqrt(max(x_var * y_var, 1e-24))
    return cov / denom


def check_v11_sigma_delta_modulator_loop(rows: list[dict[str, float]]) -> tuple[bool, str]:
    ok, note, rows = _v11_rows(rows)
    if not ok:
        return False, note
    out_span = _v11_range(rows, "out")
    metric_final = _v11_final(rows, "metric")
    high_fraction = _v11_high_fraction(rows, "out", 0.5)
    passed = out_span >= 0.75 and 0.20 <= metric_final <= 0.80 and 0.20 <= high_fraction <= 0.80
    return passed, f"v11_sigma_delta out_span={out_span:.3f} metric_final={metric_final:.3f} high_fraction={high_fraction:.3f}"


def check_v11_time_interleaved_adc_mismatch(rows: list[dict[str, float]]) -> tuple[bool, str]:
    ok, note, rows = _v11_rows(rows)
    if not ok:
        return False, note
    out_span = _v11_range(rows, "out")
    metric_span = _v11_range(rows, "metric")
    metric_final = _v11_final(rows, "metric")
    passed = out_span >= 0.75 and metric_span >= 0.65 and 0.05 <= metric_final <= 1.05
    return passed, f"v11_tiadc out_span={out_span:.3f} metric_span={metric_span:.3f} metric_final={metric_final:.3f}"


def check_v11_metastability_window_comparator(rows: list[dict[str, float]]) -> tuple[bool, str]:
    ok, note, rows = _v11_rows(rows)
    if not ok:
        return False, note
    near = [row["metric"] for row in rows if -0.075 <= row["in"] <= 0.075]
    far = [row["metric"] for row in rows if row["in"] <= -0.25 or row["in"] >= 0.25]
    if not near or not far:
        return False, "v11_meta_missing_near_or_far_samples"
    near_mean = sum(near) / len(near)
    far_mean = sum(far) / len(far)
    out_span = _v11_range(rows, "out")
    passed = out_span >= 0.75 and near_mean >= far_mean + 0.25 and near_mean >= 0.45
    return passed, f"v11_meta out_span={out_span:.3f} near_metric={near_mean:.3f} far_metric={far_mean:.3f}"


def check_v11_bootstrapped_sample_switch(rows: list[dict[str, float]]) -> tuple[bool, str]:
    ok, note, rows = _v11_rows(rows)
    if not ok:
        return False, note
    out_span = _v11_range(rows, "out")
    late_metric = _v11_window_mean(rows, "metric", rows[-1]["time"] * 0.65, rows[-1]["time"])
    corr = _v11_correlation(rows, "in", "out")
    passed = late_metric is not None and out_span >= 0.25 and late_metric >= 0.75 and corr >= 0.20
    return passed, f"v11_bootstrap out_span={out_span:.3f} late_metric={(late_metric or 0.0):.3f} corr={corr:.3f}"


def check_v11_fractional_n_pll_divider(rows: list[dict[str, float]]) -> tuple[bool, str]:
    ok, note, rows = _v11_rows(rows)
    if not ok:
        return False, note
    pulse_fraction = _v11_high_fraction(rows, "out", 0.5)
    metric_span = _v11_range(rows, "metric")
    passed = 0.04 <= pulse_fraction <= 0.40 and metric_span >= 0.45
    return passed, f"v11_fracn pulse_fraction={pulse_fraction:.3f} metric_span={metric_span:.3f}"


def check_v11_bandgap_startup_trim(rows: list[dict[str, float]]) -> tuple[bool, str]:
    ok, note, rows = _v11_rows(rows)
    if not ok:
        return False, note
    early_out = _v11_window_mean(rows, "out", 0.0, rows[-1]["time"] * 0.15)
    late_out = _v11_window_mean(rows, "out", rows[-1]["time"] * 0.75, rows[-1]["time"])
    late_metric = _v11_window_mean(rows, "metric", rows[-1]["time"] * 0.75, rows[-1]["time"])
    passed = (
        early_out is not None
        and late_out is not None
        and late_metric is not None
        and early_out <= 0.45
        and 1.05 <= late_out <= 1.30
        and late_metric >= 0.75
    )
    return passed, f"v11_bandgap early_out={(early_out or 0.0):.3f} late_out={(late_out or 0.0):.3f} late_metric={(late_metric or 0.0):.3f}"


def check_v11_quadrature_iq_imbalance_corrector(rows: list[dict[str, float]]) -> tuple[bool, str]:
    ok, note, rows = _v11_rows(rows)
    if not ok:
        return False, note
    corr = _v11_correlation(rows, "in", "out")
    out_span = _v11_range(rows, "out")
    metric_final = _v11_final(rows, "metric")
    passed = corr >= 0.55 and out_span >= 0.70 and metric_final >= 0.70
    return passed, f"v11_iq corr={corr:.3f} out_span={out_span:.3f} metric_final={metric_final:.3f}"


def check_v11_cppll_tracking_frequency_step_reacquire(rows: list[dict[str, float]]) -> tuple[bool, str]:
    ok, note, rows = _v11_rows(rows)
    if not ok:
        return False, note
    early_metric = _v11_window_mean(rows, "metric", 0.0, rows[-1]["time"] * 0.25)
    late_metric = _v11_window_mean(rows, "metric", rows[-1]["time"] * 0.70, rows[-1]["time"])
    late_out = _v11_window_mean(rows, "out", rows[-1]["time"] * 0.70, rows[-1]["time"])
    passed = (
        early_metric is not None
        and late_metric is not None
        and late_out is not None
        and early_metric <= 0.30
        and late_metric >= 0.70
        and 0.45 <= late_out <= 0.95
    )
    return passed, f"v11_cppll early_metric={(early_metric or 0.0):.3f} late_metric={(late_metric or 0.0):.3f} late_out={(late_out or 0.0):.3f}"


def evaluate_noise_gen_csv(csv_path: Path) -> tuple[float, list[str]]:
    """Fast streaming checker for noise_gen tasks on very large CSV files."""
    count = 0
    mean = 0.0
    m2 = 0.0
    max_abs = 0.0
    missing_cols = False

    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fields = set(reader.fieldnames or [])
        if not {"vin_i", "vout_o"}.issubset(fields):
            missing_cols = True
        else:
            for row in reader:
                try:
                    x = float(row["vout_o"]) - float(row["vin_i"])
                except (TypeError, ValueError):
                    continue
                count += 1
                delta = x - mean
                mean += delta / count
                m2 += delta * (x - mean)
                ax = abs(x)
                if ax > max_abs:
                    max_abs = ax

    if missing_cols:
        return 0.0, ["missing vin_i/vout_o"]
    if count == 0:
        return 0.0, ["noise_gen_empty_csv"]

    var = m2 / count
    std = math.sqrt(max(var, 0.0))
    ok = std > 0.01 and max_abs > 0.05
    return (1.0 if ok else 0.0), [f"noise_std={std:.4f} max_abs={max_abs:.4f} samples={count}"]


def _csv_fields(csv_path: Path) -> set[str]:
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return set(reader.fieldnames or [])


def _float_cell(row: dict[str, str], key: str, default: float = 0.0) -> float:
    try:
        return float(row.get(key, default))
    except (TypeError, ValueError):
        return default


def _csv_header_indices(csv_path: Path) -> tuple[list[str], dict[str, int]]:
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, [])
    return header, {name: idx for idx, name in enumerate(header)}


def _csv_required_indices(csv_path: Path, required: set[str]) -> tuple[dict[str, int] | None, list[str]]:
    header, index = _csv_header_indices(csv_path)
    missing = sorted(required - set(header))
    if missing:
        return None, missing
    return {name: index[name] for name in required}, []


def _float_at(row: list[str], index: int, default: float = 0.0) -> float:
    try:
        return float(row[index])
    except (IndexError, TypeError, ValueError):
        return default


def _stream_max(csv_path: Path, key: str) -> float:
    max_val = 0.0
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            max_val = max(max_val, _float_cell(row, key))
    return max_val


def _stream_pfd_deadzone_csv(csv_path: Path) -> tuple[float, list[str]]:
    fields = _csv_fields(csv_path)
    required = {"time", "ref", "div", "up", "dn"}
    if not required.issubset(fields):
        return 0.0, ["missing ref/div/up/dn"]

    vth = 0.5 * _stream_max(csv_path, "ref")
    prev_time: float | None = None
    prev_up = 0.0
    prev_dn = 0.0
    prev_up_bit = 0
    initialized = False
    high_up_dt = 0.0
    high_dn_dt = 0.0
    total_dt = 0.0
    run_len = 0
    max_run = 0
    up_pulses = 0

    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            time = _float_cell(row, "time")
            up = _float_cell(row, "up")
            dn = _float_cell(row, "dn")
            up_bit = 1 if up > vth else 0
            dn_bit = 1 if dn > vth else 0
            if initialized:
                dt = time - (prev_time if prev_time is not None else time)
                if dt > 0.0:
                    total_dt += dt
                    if 0.5 * (prev_up + up) > vth:
                        high_up_dt += dt
                    if 0.5 * (prev_dn + dn) > vth:
                        high_dn_dt += dt
                if prev_up_bit == 0 and up_bit == 1:
                    up_pulses += 1
            if up_bit and dn_bit:
                run_len += 1
                max_run = max(max_run, run_len)
            else:
                run_len = 0
            initialized = True
            prev_time = time
            prev_up = up
            prev_dn = dn
            prev_up_bit = up_bit

    up_frac = high_up_dt / max(total_dt, 1e-18)
    dn_frac = high_dn_dt / max(total_dt, 1e-18)
    if not (0.001 <= up_frac <= 0.03):
        return 0.0, [f"up_frac_out_of_range={up_frac:.4f}"]
    if dn_frac > 0.002:
        return 0.0, [f"dn_frac_too_high={dn_frac:.4f}"]
    if max_run > 6:
        return 0.0, [f"overlap_too_long={max_run}"]
    if up_pulses < 10:
        return 0.0, [f"too_few_up_pulses={up_pulses}"]
    return 1.0, [f"up_frac={up_frac:.4f} dn_frac={dn_frac:.4f} up_pulses={up_pulses}"]


def _stream_pfd_reset_race_csv(csv_path: Path) -> tuple[float, list[str]]:
    fields = _csv_fields(csv_path)
    required = {"time", "ref", "div", "up", "dn"}
    if not required.issubset(fields):
        return 0.0, ["missing ref/div/up/dn"]

    vth = 0.5 * _stream_max(csv_path, "ref")
    windows = {
        "first": {"start": 20e-9, "end": 120e-9, "up_dt": 0.0, "dn_dt": 0.0, "dt": 0.0, "up_pulses": 0, "dn_pulses": 0, "rows": 0},
        "second": {"start": 160e-9, "end": 260e-9, "up_dt": 0.0, "dn_dt": 0.0, "dt": 0.0, "up_pulses": 0, "dn_pulses": 0, "rows": 0},
    }
    total_dt = 0.0
    overlap_dt = 0.0
    prev: dict[str, float] | None = None
    prev_up_bit = 0
    prev_dn_bit = 0

    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cur = {
                "time": _float_cell(row, "time"),
                "up": _float_cell(row, "up"),
                "dn": _float_cell(row, "dn"),
            }
            up_bit = 1 if cur["up"] > vth else 0
            dn_bit = 1 if cur["dn"] > vth else 0
            for state in windows.values():
                if state["start"] <= cur["time"] <= state["end"]:
                    state["rows"] += 1
                    if prev_up_bit == 0 and up_bit == 1:
                        state["up_pulses"] += 1
                    if prev_dn_bit == 0 and dn_bit == 1:
                        state["dn_pulses"] += 1
            if prev is not None:
                dt = cur["time"] - prev["time"]
                if dt > 0.0:
                    total_dt += dt
                    up_mid = 0.5 * (prev["up"] + cur["up"])
                    dn_mid = 0.5 * (prev["dn"] + cur["dn"])
                    if up_mid > vth and dn_mid > vth:
                        overlap_dt += dt
                    mid_t = 0.5 * (prev["time"] + cur["time"])
                    for state in windows.values():
                        if state["start"] <= mid_t <= state["end"]:
                            state["dt"] += dt
                            if up_mid > vth:
                                state["up_dt"] += dt
                            if dn_mid > vth:
                                state["dn_dt"] += dt
            prev = cur
            prev_up_bit = up_bit
            prev_dn_bit = dn_bit

    first = windows["first"]
    second = windows["second"]
    if first["rows"] < 4 or second["rows"] < 4:
        return 0.0, ["insufficient_window_samples"]
    up_first = first["up_dt"] / max(first["dt"], 1e-18)
    dn_first = first["dn_dt"] / max(first["dt"], 1e-18)
    up_second = second["up_dt"] / max(second["dt"], 1e-18)
    dn_second = second["dn_dt"] / max(second["dt"], 1e-18)
    overlap_frac = overlap_dt / max(total_dt, 1e-18)
    ok = (
        0.001 <= up_first <= 0.08
        and dn_first <= 0.01
        and 0.001 <= dn_second <= 0.08
        and up_second <= 0.01
        and first["up_pulses"] >= 4
        and second["dn_pulses"] >= 4
        and overlap_frac <= 0.01
    )
    return (1.0 if ok else 0.0), [
        f"up_first={up_first:.4f} dn_first={dn_first:.4f} "
        f"up_second={up_second:.4f} dn_second={dn_second:.4f} "
        f"up_pulses_first={int(first['up_pulses'])} "
        f"dn_pulses_second={int(second['dn_pulses'])} "
        f"overlap_frac={overlap_frac:.4f}"
    ]


def _stream_cppll_freq_step_reacquire_csv(csv_path: Path) -> tuple[float, list[str]]:
    fields = _csv_fields(csv_path)
    required = {"time", "ref_clk", "fb_clk", "lock", "vctrl_mon"}
    if not required.issubset(fields):
        return 0.0, ["missing ref_clk/fb_clk/lock/vctrl_mon"]

    vth = 0.45
    ref_edges: list[float] = []
    fb_edges: list[float] = []
    lock_edges: list[float] = []
    lock_window_total_dt = 0.0
    lock_window_high_dt = 0.0
    vctrl_min = float("inf")
    vctrl_max = float("-inf")
    vctrl_in_range = True
    prev: dict[str, float] | None = None

    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cur = {
                "time": _float_cell(row, "time"),
                "ref_clk": _float_cell(row, "ref_clk"),
                "fb_clk": _float_cell(row, "fb_clk"),
                "lock": _float_cell(row, "lock"),
                "vctrl_mon": _float_cell(row, "vctrl_mon"),
            }
            vctrl_min = min(vctrl_min, cur["vctrl_mon"])
            vctrl_max = max(vctrl_max, cur["vctrl_mon"])
            if not (-1e-6 <= cur["vctrl_mon"] <= 0.95):
                vctrl_in_range = False
            if prev is not None:
                if prev["ref_clk"] < vth <= cur["ref_clk"]:
                    ref_edges.append(cur["time"])
                if prev["fb_clk"] < vth <= cur["fb_clk"]:
                    fb_edges.append(cur["time"])
                if prev["lock"] < vth <= cur["lock"]:
                    lock_edges.append(cur["time"])
                dt = cur["time"] - prev["time"]
                if dt > 0.0 and 2.05e-6 <= prev["time"] and cur["time"] <= 2.8e-6:
                    lock_window_total_dt += dt
                    if 0.5 * (prev["lock"] + cur["lock"]) > vth:
                        lock_window_high_dt += dt
            prev = cur

    if len(ref_edges) < 12 or len(fb_edges) < 12:
        return 0.0, [f"not_enough_edges ref={len(ref_edges)} fb={len(fb_edges)}"]

    ref_late = [t for t in ref_edges if 4.5e-6 <= t <= 5.9e-6]
    fb_late = [t for t in fb_edges if 4.5e-6 <= t <= 5.9e-6]
    if len(ref_late) < 4 or len(fb_late) < 4:
        return 0.0, [
            f"not_enough_late_edges ref_late={len(ref_late)} fb_late={len(fb_late)}"
        ]

    ref_periods = [b - a for a, b in zip(ref_late, ref_late[1:])]
    fb_periods = [b - a for a, b in zip(fb_late, fb_late[1:])]
    ref_period = sum(ref_periods) / len(ref_periods)
    fb_period = sum(fb_periods) / len(fb_periods)
    if ref_period <= 0.0 or fb_period <= 0.0:
        return 0.0, ["non_positive_period"]
    freq_ratio = ref_period / fb_period

    pre_lock_edges = [t for t in lock_edges if t < 2.0e-6]
    post_lock_edges = [t for t in lock_edges if 2.2e-6 <= t <= 5.9e-6]
    relock_time = post_lock_edges[0] if post_lock_edges else float("nan")
    lock_high_frac = lock_window_high_dt / max(lock_window_total_dt, 1e-18)
    disturb_low_frac = 1.0 - lock_high_frac
    ok = (
        bool(pre_lock_edges)
        and disturb_low_frac >= 0.25
        and bool(post_lock_edges)
        and 0.97 <= freq_ratio <= 1.03
        and vctrl_in_range
    )
    return (1.0 if ok else 0.0), [
        f"freq_ratio={freq_ratio:.4f} relock_time={relock_time:.3e} "
        f"disturb_low_frac={disturb_low_frac:.3f} "
        f"vctrl_min={vctrl_min:.3f} vctrl_max={vctrl_max:.3f}"
    ]


def _stream_dac_binary_clk_4b_csv(csv_path: Path) -> tuple[float, list[str]]:
    fields = _csv_fields(csv_path)
    required = {"din3", "din2", "din1", "din0", "aout"}
    if not required.issubset(fields):
        return 0.0, ["missing din*/aout"]
    sums = {idx: 0.0 for idx in range(16)}
    counts = {idx: 0 for idx in range(16)}
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = (
                (1 if _float_cell(row, "din3") > 0.45 else 0) * 8
                + (1 if _float_cell(row, "din2") > 0.45 else 0) * 4
                + (1 if _float_cell(row, "din1") > 0.45 else 0) * 2
                + (1 if _float_cell(row, "din0") > 0.45 else 0)
            )
            sums[code] += _float_cell(row, "aout")
            counts[code] += 1
    medians = {code: sums[code] / counts[code] for code in counts if counts[code] > 0}
    sorted_codes = sorted(medians)
    monotonic = all(medians[sorted_codes[i]] <= medians[sorted_codes[i + 1]] + 1e-9 for i in range(len(sorted_codes) - 1))
    span = medians[sorted_codes[-1]] - medians[sorted_codes[0]] if sorted_codes else 0.0
    ok = len(sorted_codes) >= 14 and monotonic and span > 0.7
    return (1.0 if ok else 0.0), [f"levels={len(sorted_codes)} aout_span={span:.3f}"]


def _stream_sar_adc_dac_weighted_8b_csv(csv_path: Path) -> tuple[float, list[str]]:
    fields = _csv_fields(csv_path)
    required = {"time", "vin", "vin_sh", "clks", "vout", "rst_n"} | {f"dout_{idx}" for idx in range(8)}
    if not required.issubset(fields):
        return 0.0, ["missing time/vin/vin_sh/clks/vout/rst_n or dout_0..7"]
    bit_names = [f"dout_{idx}" for idx in range(8)]
    sample_on_conv_done = {"conv_done", "vin_sample"}.issubset(fields)
    sample_count = 0
    quant_err_sum = 0.0
    dac_err_sum = 0.0
    roundtrip_err_sum = 0.0
    max_quant_err = 0.0
    max_dac_err = 0.0
    min_code = 255
    max_code = 0
    min_vin_sh = float("inf")
    max_vin_sh = float("-inf")
    min_vout = float("inf")
    max_vout = float("-inf")
    codes: set[int] = set()
    sorted_pairs: list[tuple[float, int]] = []
    pending_samples: list[float] = []
    prev_clk = 0.0
    prev_conv_done = 0.0
    initialized = False
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            time = _float_cell(row, "time")
            clk = _float_cell(row, "clks")
            if sample_on_conv_done:
                conv_done = _float_cell(row, "conv_done")
                if initialized and prev_conv_done <= 0.45 < conv_done:
                    pending_samples.append(time + 1.0e-9)
                prev_conv_done = conv_done
            elif initialized and prev_clk < 0.45 <= clk:
                pending_samples.append(time + 1.0e-9)
            while pending_samples and time >= pending_samples[0]:
                pending_samples.pop(0)
                if _float_cell(row, "rst_n") <= 0.45:
                    continue
                code = sum((1 if _float_cell(row, bit_name) > 0.45 else 0) << idx for idx, bit_name in enumerate(bit_names))
                vin_sh = _float_cell(row, "vin_sample" if sample_on_conv_done else "vin_sh")
                vout = _float_cell(row, "vout")
                code_voltage = code / 255.0 * 0.9
                quant_err = abs(vin_sh - code_voltage)
                dac_err = abs(vout - code_voltage)
                roundtrip_err = abs(vin_sh - vout)
                codes.add(code)
                min_code = min(min_code, code)
                max_code = max(max_code, code)
                min_vin_sh = min(min_vin_sh, vin_sh)
                max_vin_sh = max(max_vin_sh, vin_sh)
                min_vout = min(min_vout, vout)
                max_vout = max(max_vout, vout)
                quant_err_sum += quant_err
                dac_err_sum += dac_err
                roundtrip_err_sum += roundtrip_err
                max_quant_err = max(max_quant_err, quant_err)
                max_dac_err = max(max_dac_err, dac_err)
                sorted_pairs.append((vin_sh, code))
                sample_count += 1
            prev_clk = clk
            initialized = True
    if sample_count == 0:
        return 0.0, ["no post-reset edge samples"]
    unique_codes = len(codes)
    sample_span = max_vin_sh - min_vin_sh
    vout_span = max_vout - min_vout
    avg_quant_err = quant_err_sum / sample_count
    avg_dac_err = dac_err_sum / sample_count
    avg_roundtrip_err = roundtrip_err_sum / sample_count
    sorted_pairs.sort(key=lambda item: item[0])
    monotonic_reversals = sum(
        1 for (_, prev_code), (_, curr_code) in zip(sorted_pairs, sorted_pairs[1:])
        if curr_code + 2 < prev_code
    )
    ok = (
        sample_count >= 48
        and unique_codes >= 48
        and min_code <= 8
        and max_code >= 247
        and sample_span > 0.75
        and vout_span > 0.75
        and avg_quant_err < 0.025
        and max_quant_err < 0.060
        and avg_dac_err < 0.020
        and max_dac_err < 0.060
        and avg_roundtrip_err < 0.030
        and monotonic_reversals <= max(2, len(sorted_pairs) // 50)
        and min_vout >= -0.02
        and max_vout <= 0.92
    )
    return (1.0 if ok else 0.0), [
        f"{'done_samples' if sample_on_conv_done else 'edge_samples'}={sample_count} "
        f"unique_codes={unique_codes} code_range={min_code}..{max_code} "
        f"sample_span={sample_span:.3f} vout_span={vout_span:.3f} "
        f"avg_quant_err={avg_quant_err:.4f} max_quant_err={max_quant_err:.4f} "
        f"avg_dac_err={avg_dac_err:.4f} max_dac_err={max_dac_err:.4f} "
        f"avg_roundtrip_err={avg_roundtrip_err:.4f} monotonic_reversals={monotonic_reversals}"
    ]


def _stream_sar_adc_dac_weighted_8b_release_csv(csv_path: Path) -> tuple[float, list[str]]:
    score, notes = _stream_sar_adc_dac_weighted_8b_csv(csv_path)
    return score, ["public_contract"] + notes


def _stream_dwa_ptr_gen_no_overlap_csv(csv_path: Path) -> tuple[float, list[str]]:
    fields = _csv_fields(csv_path)
    required = {"time", "clk_i", "rst_ni", "ptr_0", "cell_en_0"}
    if not required.issubset(fields):
        return 0.0, ["missing time/clk_i/rst_ni/ptr_0/cell_en_0"]
    ptr_cols = sorted([name for name in fields if re.fullmatch(r"ptr_\d+", name)], key=lambda n: int(n.rsplit("_", 1)[1]))
    cell_cols = sorted([name for name in fields if re.fullmatch(r"cell_en_\d+", name)], key=lambda n: int(n.rsplit("_", 1)[1]))
    if not ptr_cols or not cell_cols:
        return 0.0, ["missing ptr_* or cell_en_* columns"]

    pending_samples: list[float] = []
    sampled_cycles = 0
    bad_ptr_rows = 0
    max_active_cells = 0
    overlap_count = 0
    prev_active: set[int] | None = None
    prev_clk = 0.0
    initialized = False

    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            time = _float_cell(row, "time")
            clk = _float_cell(row, "clk_i")
            if initialized and prev_clk < 0.45 <= clk:
                pending_samples.append(time + 1.0e-9)
            while pending_samples and time >= pending_samples[0]:
                pending_samples.pop(0)
                if _float_cell(row, "rst_ni") <= 0.45:
                    continue
                sampled_cycles += 1
                ptr_active = {idx for idx, col in enumerate(ptr_cols) if _float_cell(row, col) > 0.45}
                if len(ptr_active) not in (0, 1):
                    bad_ptr_rows += 1
                active_cells = {idx for idx, col in enumerate(cell_cols) if _float_cell(row, col) > 0.45}
                max_active_cells = max(max_active_cells, len(active_cells))
                if prev_active is not None and prev_active & active_cells:
                    overlap_count += 1
                prev_active = active_cells
            prev_clk = clk
            initialized = True
    if sampled_cycles < 2:
        return 0.0, [f"insufficient_post_reset_samples count={sampled_cycles}"]
    ok = bad_ptr_rows == 0 and max_active_cells > 0 and overlap_count == 0
    return (1.0 if ok else 0.0), [
        f"sampled_cycles={sampled_cycles} bad_ptr_rows={bad_ptr_rows} "
        f"max_active_cells={max_active_cells} overlap_count={overlap_count}"
    ]


def _stream_not_gate_csv(csv_path: Path) -> tuple[float, list[str]]:
    fields = _csv_fields(csv_path)
    if {"a", "y"}.issubset(fields):
        a_col, y_col = "a", "y"
    elif {"not_a", "not_y"}.issubset(fields):
        a_col, y_col = "not_a", "not_y"
    else:
        return 0.0, ["missing a/y"]
    sampled_count = 0
    good = 0
    last_t = -1.0
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            time = _float_cell(row, "time")
            if time - last_t < 5e-10:
                continue
            last_t = time
            sampled_count += 1
            if (_float_cell(row, a_col) > 0.4) != (_float_cell(row, y_col) > 0.4):
                good += 1
    if sampled_count < 10:
        return 0.0, [f"too_few_samples={sampled_count}"]
    frac = good / sampled_count
    return (1.0 if frac > 0.9 else 0.0), [f"invert_match_frac={frac:.3f}"]


def _stream_gray_counter_one_bit_change_csv(csv_path: Path) -> tuple[float, list[str]]:
    fields = _csv_fields(csv_path)

    def pick(names: list[str]) -> str | None:
        lower = {field.lower(): field for field in fields}
        for name in names:
            if name.lower() in lower:
                return lower[name.lower()]
        return None

    clk_col = pick(["clk", "CLK"])
    rst_col = pick(["rst", "RST", "rstb", "RSTB"])
    g_cols = [pick([f"g{idx}", f"G{idx}"]) for idx in range(4)]
    if clk_col is None or rst_col is None or any(col is None for col in g_cols):
        return 0.0, ["missing clk/rst/g0..g3"]

    total_rows = 0
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for _ in reader:
            total_rows += 1
    if total_rows == 0:
        return 0.0, ["empty"]
    reset_prefix_rows = max(4, total_rows // 10)

    rst_prefix_high = False
    edge_count = 0
    post_reset_codes: list[int] = []
    pending_offsets: list[int] = []
    prev_clk: float | None = None

    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row_idx, row in enumerate(reader):
            clk = _float_cell(row, clk_col)
            rst = _float_cell(row, rst_col)
            if row_idx < reset_prefix_rows and rst > 0.45:
                rst_prefix_high = True
            if prev_clk is not None and prev_clk <= 0.45 < clk:
                # Match the row-based checker's settle=min(edge_idx + 8, last_row).
                # The current edge row is processed below, so start at 9.
                pending_offsets.append(9)
                edge_count += 1
            prev_clk = clk

            for pending_idx in range(len(pending_offsets) - 1, -1, -1):
                pending_offsets[pending_idx] -= 1
                if pending_offsets[pending_idx] > 0:
                    continue
                del pending_offsets[pending_idx]
                if (rst_prefix_high and rst > 0.45) or ((not rst_prefix_high) and rst < 0.45):
                    continue
                code = 0
                for bit_idx, col in enumerate(g_cols):
                    assert col is not None
                    if _float_cell(row, col) > 0.45:
                        code |= 1 << bit_idx
                post_reset_codes.append(code)

    if edge_count < 20:
        return 0.0, [f"not_enough_clk_edges={edge_count}"]
    if len(post_reset_codes) < 16:
        return 0.0, [f"not_enough_post_reset_codes={len(post_reset_codes)}"]

    bad_transitions = sum(
        1
        for a, b in zip(post_reset_codes[:-1], post_reset_codes[1:])
        if bin(a ^ b).count("1") != 1
    )
    unique_codes = set(post_reset_codes)
    expected_grays = {i ^ (i >> 1) for i in range(16)}
    if bad_transitions:
        return 0.0, [f"gray_property_violated bad_transitions={bad_transitions}"]
    missing = 16 - len(expected_grays & unique_codes)
    if missing:
        return 0.0, [f"missing_gray_codes count={missing}"]
    return 1.0, [f"unique_codes={len(unique_codes)} bad_transitions={bad_transitions}"]


def _stream_dwa_wraparound_csv(csv_path: Path) -> tuple[float, list[str]]:
    fields = _csv_fields(csv_path)
    required = {"time", "clk_i", "rst_ni", "ptr_0", "cell_en_0", "code_0"}
    if not required.issubset(fields):
        return 0.0, ["missing time/clk_i/rst_ni/ptr_0/cell_en_0/code_0"]

    ptr_cols = sorted(
        [field for field in fields if re.fullmatch(r"ptr_\d+", field)],
        key=lambda item: int(item.rsplit("_", 1)[1]),
    )
    cell_cols = sorted(
        [field for field in fields if re.fullmatch(r"cell_en_\d+", field)],
        key=lambda item: int(item.rsplit("_", 1)[1]),
    )
    code_cols = sorted(
        [field for field in fields if re.fullmatch(r"code_\d+", field)],
        key=lambda item: int(item.rsplit("_", 1)[1]),
    )
    if len(ptr_cols) != 16 or len(cell_cols) != 16 or len(code_cols) != 4:
        return 0.0, ["expected ptr_0..15, cell_en_0..15, and code_0..3 columns"]

    pending_samples: list[float] = []
    sampled: list[tuple[int, list[int], set[int]]] = []
    initialized = False
    prev_clk = 0.0
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            time = _float_cell(row, "time")
            clk = _float_cell(row, "clk_i")
            if initialized and prev_clk < 0.45 <= clk:
                pending_samples.append(time + 1.0e-9)
            while pending_samples and time >= pending_samples[0]:
                pending_samples.pop(0)
                if _float_cell(row, "rst_ni") <= 0.45:
                    continue
                code = sum(
                    (1 if _float_cell(row, col) > 0.45 else 0) << int(col[5:])
                    for col in code_cols
                )
                ptr_active = [idx for idx, col in enumerate(ptr_cols) if _float_cell(row, col) > 0.45]
                active_cells = {idx for idx, col in enumerate(cell_cols) if _float_cell(row, col) > 0.45}
                sampled.append((code, ptr_active, active_cells))
            prev_clk = clk
            initialized = True

    if len(sampled) < 5:
        return 0.0, [f"insufficient_post_reset_samples count={len(sampled)}"]

    expected_ptr = 13
    bad_ptr_rows = 0
    bad_count_rows = 0
    wrap_events = 0
    split_wrap_rows = 0
    prev_ptr = expected_ptr
    for code, ptr_active, active_cells in sampled:
        expected_ptr = (expected_ptr + code) % 16
        if expected_ptr < prev_ptr:
            wrap_events += 1
        if ptr_active != [expected_ptr]:
            bad_ptr_rows += 1
        if len(active_cells) != code:
            bad_count_rows += 1
        if active_cells and (max(active_cells) - min(active_cells) + 1) > len(active_cells):
            split_wrap_rows += 1
        prev_ptr = expected_ptr

    ok = bad_ptr_rows == 0 and bad_count_rows == 0 and wrap_events >= 2 and split_wrap_rows >= 2
    return (1.0 if ok else 0.0), [
        f"sampled_cycles={len(sampled)} bad_ptr_rows={bad_ptr_rows} "
        f"bad_count_rows={bad_count_rows} wrap_events={wrap_events} "
        f"split_wrap_rows={split_wrap_rows}"
    ]


def _stream_gain_extraction_csv(csv_path: Path) -> tuple[float, list[str]]:
    fields = _csv_fields(csv_path)
    required = {"vinp", "vinn", "vamp_p", "vamp_n"}
    if not required.issubset(fields):
        return 0.0, ["missing vinp/vinn/vamp_p/vamp_n"]

    count = 0
    mean_in = 0.0
    mean_out = 0.0
    m2_in = 0.0
    m2_out = 0.0
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            vin = _float_cell(row, "vinp") - _float_cell(row, "vinn")
            vout = _float_cell(row, "vamp_p") - _float_cell(row, "vamp_n")
            count += 1
            delta_in = vin - mean_in
            mean_in += delta_in / count
            m2_in += delta_in * (vin - mean_in)
            delta_out = vout - mean_out
            mean_out += delta_out / count
            m2_out += delta_out * (vout - mean_out)
    if count == 0:
        return 0.0, ["empty"]
    std_in = math.sqrt(max(m2_in / count, 0.0))
    std_out = math.sqrt(max(m2_out / count, 0.0))
    gain = std_out / std_in if std_in > 1e-12 else 0.0
    ok = gain > 4.0 and std_out > std_in
    return (1.0 if ok else 0.0), [f"diff_gain={gain:.2f}"]


def _stream_gain_estimator_csv(csv_path: Path) -> tuple[float, list[str]]:
    required = {"time", "vinp", "vinn", "voutp", "voutn", "gain_out", "valid"}
    indices, missing = _csv_required_indices(csv_path, required)
    if indices is None:
        # The row-based checker has no aliases for these required outputs, so
        # missing columns would fail after loading the full CSV.
        return 0.0, [f"required_columns_missing={'/'.join(missing)}"]
    assert indices is not None

    last_time = 0.0
    final_valid = 0.0
    max_valid = 0.0
    valid_count = 0
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            last_time = _float_at(row, indices["time"])
            valid = final_valid = _float_at(row, indices["valid"])
            if valid > 0.45:
                valid_count += 1
            if valid > max_valid:
                max_valid = valid

    if valid_count < 20:
        return 0.0, [f"insufficient_valid_samples={valid_count}"]

    late_start = last_time * 0.65
    late_valid_count = 0
    vin_min = math.inf
    vin_max = -math.inf
    vout_min = math.inf
    vout_max = -math.inf
    gain_sum = 0.0
    vdd_est = max(max_valid, 1e-6)

    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            time_value = _float_at(row, indices["time"])
            if time_value < late_start:
                continue
            valid = _float_at(row, indices["valid"])
            if valid <= 0.45:
                continue
            vin_diff = _float_at(row, indices["vinp"]) - _float_at(row, indices["vinn"])
            vout_diff = _float_at(row, indices["voutp"]) - _float_at(row, indices["voutn"])
            vin_min = min(vin_min, vin_diff)
            vin_max = max(vin_max, vin_diff)
            vout_min = min(vout_min, vout_diff)
            vout_max = max(vout_max, vout_diff)
            gain_sum += _float_at(row, indices["gain_out"]) / vdd_est * 10.0
            late_valid_count += 1

    if late_valid_count < 10:
        return 0.0, [f"late_valid_samples={late_valid_count}"]

    in_span = vin_max - vin_min
    out_span = vout_max - vout_min
    waveform_gain = out_span / in_span if in_span > 1e-12 else 0.0
    gain_est = gain_sum / late_valid_count
    gain_err = abs(gain_est - waveform_gain)
    valid_final = final_valid > 0.45
    ok = (
        valid_final
        and 0.045 <= in_span <= 0.075
        and 0.27 <= out_span <= 0.45
        and 5.0 <= waveform_gain <= 7.2
        and gain_err <= 0.35
    )
    return (1.0 if ok else 0.0), [
        f"in_span={in_span:.4f} out_span={out_span:.4f} "
        f"waveform_gain={waveform_gain:.2f} gain_est={gain_est:.2f} "
        f"gain_err={gain_err:.2f} valid_final={valid_final}"
    ]


def _stream_cdac_cal_csv(csv_path: Path) -> tuple[float, list[str]]:
    header, indices = _csv_header_indices(csv_path)
    vdac_cols = [col for col in header if "vdac" in col.lower() or "vcap" in col.lower() or "vout" in col.lower()]
    if not vdac_cols:
        return 0.0, [f"missing vdac columns; keys={header[:10]}"]

    cols = vdac_cols[:2]
    mins = {col: math.inf for col in cols}
    maxs = {col: -math.inf for col in cols}
    count = 0
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            count += 1
            for col in cols:
                value = _float_at(row, indices[col])
                if value < mins[col]:
                    mins[col] = value
                if value > maxs[col]:
                    maxs[col] = value

    if count == 0:
        return 0.0, ["empty"]
    for col in cols:
        value_range = maxs[col] - mins[col]
        if value_range > 0.05:
            return 1.0, [f"vdac_activity col={col} range={value_range:.3f}"]
    return 0.0, [f"no vdac activity in {vdac_cols[:4]}"]


def _stream_multimod_divider_ratio_switch_csv(csv_path: Path) -> tuple[float, list[str]]:
    fields = _csv_fields(csv_path)
    required = {"time", "clk_in", "div_out"}
    if not required.issubset(fields):
        return 0.0, ["missing time/clk_in/div_out"]

    in_edges: list[float] = []
    out_edges: list[float] = []
    initialized = False
    prev_in = 0.0
    prev_out = 0.0
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            time = _float_cell(row, "time")
            clk_in = _float_cell(row, "clk_in")
            div_out = _float_cell(row, "div_out")
            if initialized and prev_in < 0.45 <= clk_in:
                in_edges.append(time)
            if initialized and prev_out < 0.45 <= div_out:
                out_edges.append(time)
            prev_in = clk_in
            prev_out = div_out
            initialized = True

    if len(in_edges) < 40 or len(out_edges) < 10:
        return 0.0, [f"not_enough_edges in={len(in_edges)} out={len(out_edges)}"]

    windows = [
        (10e-9, 90e-9, 4, "pre_div4"),
        (120e-9, 190e-9, 5, "mid_div5"),
        (220e-9, 300e-9, 4, "post_div4"),
    ]
    details: list[str] = []
    for t0, t1, expected_ratio, label in windows:
        win_in = [time for time in in_edges if t0 <= time <= t1]
        win_out = [time for time in out_edges if t0 <= time <= t1]
        if len(win_in) < expected_ratio * 2 or len(win_out) < 2:
            return 0.0, [f"{label}_insufficient_edges in={len(win_in)} out={len(win_out)}"]
        measured_ratio = len(win_in) / max(len(win_out), 1)
        details.append(f"{label}={measured_ratio:.2f}")
        if abs(measured_ratio - expected_ratio) > 0.35:
            return 0.0, [";".join(details)]
    return 1.0, [";".join(details)]


def _stream_lfsr_csv(csv_path: Path) -> tuple[float, list[str]]:
    indices, missing = _csv_required_indices(csv_path, {"dpn", "rstb"})
    if indices is None:
        return 0.0, [f"missing {'/'.join(missing)}"]
    assert indices is not None

    count = 0
    hi_count = 0
    transitions = 0
    prev_bit: int | None = None
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            if _float_at(row, indices["rstb"]) <= 0.45:
                continue
            bit = 1 if _float_at(row, indices["dpn"]) > 0.45 else 0
            count += 1
            hi_count += bit
            if prev_bit is not None and bit != prev_bit:
                transitions += 1
            prev_bit = bit

    if count < 2:
        return 0.0, ["not enough post-reset samples"]
    hi_frac = hi_count / count
    ok = 0.05 < hi_frac < 0.95 and transitions >= 10
    return (1.0 if ok else 0.0), [f"transitions={transitions} hi_frac={hi_frac:.3f}"]


def _stream_prbs7_csv(csv_path: Path) -> tuple[float, list[str]]:
    required = {"time", "clk", "rst_n", "en", "serial_out"} | {f"state_{idx}" for idx in range(7)}
    indices, missing = _csv_required_indices(csv_path, required)
    if indices is None:
        return 0.0, [f"missing_columns={','.join(missing)}"]
    assert indices is not None

    def logic(row: list[str], name: str) -> int | None:
        value = _float_at(row, indices[name])
        if value >= 0.7:
            return 1
        if value <= 0.2:
            return 0
        return None

    stable_codes: list[int] = []
    serial_bits: list[int] = []

    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            if (
                _float_at(row, indices["time"]) <= 2e-9
                or _float_at(row, indices["rst_n"]) <= 0.7
                or _float_at(row, indices["en"]) <= 0.7
            ):
                continue
            state = 0
            stable = True
            for idx in range(7):
                bit = logic(row, f"state_{idx}")
                if bit is None:
                    stable = False
                    break
                state |= bit << idx
            serial = logic(row, "serial_out")
            if not stable or serial is None:
                continue
            if serial != ((state >> 6) & 1):
                return 0.0, [f"serial_state_mismatch code={state}"]
            if not stable_codes or stable_codes[-1] != state:
                stable_codes.append(state)
                serial_bits.append(serial)

    if len(stable_codes) < 10:
        return 0.0, [f"unique_state_steps={len(stable_codes)}"]
    if 0 in stable_codes:
        return 0.0, ["entered_zero_state"]

    mismatches = 0
    checked = 0
    for current, observed_next in zip(stable_codes, stable_codes[1:]):
        feedback = ((current >> 6) & 1) ^ ((current >> 5) & 1)
        expected_next = ((current & 0x3F) << 1) | feedback
        checked += 1
        if observed_next != expected_next:
            mismatches += 1

    serial_transitions = sum(1 for idx in range(len(serial_bits) - 1) if serial_bits[idx] != serial_bits[idx + 1])
    ok = checked >= 8 and mismatches == 0 and serial_transitions >= 3
    return (1.0 if ok else 0.0), [
        f"state_steps={len(stable_codes)} checked_transitions={checked} "
        f"mismatches={mismatches} serial_transitions={serial_transitions}"
    ]


def _stream_bbpd_csv(csv_path: Path) -> tuple[float, list[str]]:
    required = {"time", "data", "clk", "retimed_data", "up", "down"}
    indices, missing = _csv_required_indices(csv_path, required)
    if indices is None:
        return 0.0, ["missing time/data/clk/retimed_data/up/down"]
    assert indices is not None

    vth = 0.45
    response_window_s = 0.2e-9
    total_rows = 0
    overlap = 0
    data_edges = 0
    up_edges = 0
    down_edges = 0
    directional_counts = {
        "up_expected": 0,
        "down_expected": 0,
        "up_correct": 0,
        "down_correct": 0,
        "none_expected": 0,
        "none_correct": 0,
        "wrong": 0,
        "missing": 0,
        "false_pulse": 0,
    }
    pending_windows: list[dict[str, object]] = []

    def update_window(window: dict[str, object], up: float, down: float) -> None:
        expected = str(window["expected"])
        wrong = str(window["wrong"])
        if (expected == "up" and up > vth) or (expected == "down" and down > vth):
            window["expected_hit"] = True
        if (wrong == "up" and up > vth) or (wrong == "down" and down > vth):
            window["wrong_hit"] = True

    def finalize_window(window: dict[str, object]) -> None:
        expected = str(window["expected"])
        if bool(window["expected_hit"]) and not bool(window["wrong_hit"]):
            directional_counts[f"{expected}_correct"] += 1
        elif bool(window["wrong_hit"]):
            directional_counts["wrong"] += 1
        else:
            directional_counts["missing"] += 1

    prev_data: float | None = None
    prev_up: float | None = None
    prev_down: float | None = None
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            total_rows += 1
            time_s = _float_at(row, indices["time"])
            data = _float_at(row, indices["data"])
            clk = _float_at(row, indices["clk"])
            retimed_data = _float_at(row, indices["retimed_data"])
            up = _float_at(row, indices["up"])
            down = _float_at(row, indices["down"])

            if up > vth and down > vth:
                overlap += 1

            active_windows: list[dict[str, object]] = []
            for window in pending_windows:
                if time_s <= float(window["end_time"]):
                    update_window(window, up, down)
                    active_windows.append(window)
                else:
                    finalize_window(window)
            pending_windows = active_windows

            if prev_data is not None and prev_up is not None and prev_down is not None:
                if prev_up < vth <= up:
                    up_edges += 1
                if prev_down < vth <= down:
                    down_edges += 1
                if (prev_data < vth <= data) or (prev_data > vth >= data):
                    data_edges += 1
                    clk_high = clk > vth
                    retimed_high = retimed_data > vth
                    if clk_high and not retimed_high:
                        expected = "up"
                    elif not clk_high and retimed_high:
                        expected = "down"
                    else:
                        expected = None
                    if expected is not None:
                        directional_counts[f"{expected}_expected"] += 1
                        wrong = "down" if expected == "up" else "up"
                        window = {
                            "end_time": time_s + response_window_s,
                            "expected": expected,
                            "wrong": wrong,
                            "expected_hit": False,
                            "wrong_hit": False,
                        }
                        update_window(window, up, down)
                        pending_windows.append(window)

            prev_data = data
            prev_up = up
            prev_down = down

    for window in pending_windows:
        finalize_window(window)

    if data_edges < 6:
        return 0.0, ["not enough data edges"]

    overlap_frac = overlap / max(total_rows, 1)
    edge_trigger_ok = up_edges + down_edges >= max(4, data_edges // 4)
    pulse_presence_ok = up_edges >= 2 and down_edges >= 2
    non_overlap_ok = overlap_frac < 0.02
    directional_ok = (
        directional_counts["up_expected"] >= 2
        and directional_counts["down_expected"] >= 2
        and directional_counts["up_correct"] >= max(2, int(0.75 * directional_counts["up_expected"]))
        and directional_counts["down_correct"] >= max(2, int(0.75 * directional_counts["down_expected"]))
        and directional_counts["wrong"] == 0
    )
    ok = edge_trigger_ok and pulse_presence_ok and non_overlap_ok and directional_ok
    return (1.0 if ok else 0.0), [
        f"data_edges={data_edges} up_edges={up_edges} down_edges={down_edges} "
        f"overlap_frac={overlap_frac:.4f} "
        f"direction_up={directional_counts['up_correct']}/{directional_counts['up_expected']} "
        f"direction_down={directional_counts['down_correct']}/{directional_counts['down_expected']} "
        f"wrong_direction={directional_counts['wrong']} missing_direction={directional_counts['missing']}"
    ]


def _stream_cross_hysteresis_window_csv(csv_path: Path) -> tuple[float, list[str]]:
    indices, missing = _csv_required_indices(csv_path, {"time", "vin", "out"})
    if indices is None:
        return 0.0, [f"missing {'/'.join(missing)}"]
    assert indices is not None

    out_min = float("inf")
    out_max = float("-inf")
    windows = {
        "low1": [0.0, 0],
        "high": [0.0, 0],
        "low2": [0.0, 0],
    }
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            time_s = _float_at(row, indices["time"])
            out = _float_at(row, indices["out"])
            out_min = min(out_min, out)
            out_max = max(out_max, out)
            if time_s <= 20e-9:
                windows["low1"][0] += out
                windows["low1"][1] += 1
            if 35e-9 <= time_s <= 55e-9:
                windows["high"][0] += out
                windows["high"][1] += 1
            if time_s >= 75e-9:
                windows["low2"][0] += out
                windows["low2"][1] += 1

    span = out_max - out_min
    if span < 0.3:
        return 0.0, [f"out_span_too_small={span:.3f}"]
    if any(count == 0 for _, count in windows.values()):
        return 0.0, ["insufficient_window_samples"]
    low1 = windows["low1"][0] / windows["low1"][1]
    high = windows["high"][0] / windows["high"][1]
    low2 = windows["low2"][0] / windows["low2"][1]
    ok = (high - low1) > 0.45 * span and (high - low2) > 0.45 * span
    return (1.0 if ok else 0.0), [f"low1={low1:.3f} high={high:.3f} low2={low2:.3f} span={span:.3f}"]


def _stream_cross_interval_163p333_csv(csv_path: Path) -> tuple[float, list[str]]:
    indices, missing = _csv_required_indices(csv_path, {"time", "delay_out", "seen_out"})
    if indices is None:
        return 0.0, [f"missing {'/'.join(missing)}"]
    assert indices is not None

    seen_hi = 0.0
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            seen_hi = max(seen_hi, _float_at(row, indices["seen_out"]))
    if seen_hi < 0.3:
        return 0.0, [f"seen_out_never_high={seen_hi:.3f}"]

    seen_th = 0.5 * seen_hi
    first_seen_time: float | None = None
    seen_delay_values: list[float] = []
    settled_delay_values: list[float] = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            time_value = _float_at(row, indices["time"])
            seen = _float_at(row, indices["seen_out"])
            if seen <= seen_th:
                continue
            if first_seen_time is None:
                first_seen_time = time_value
            delay = _float_at(row, indices["delay_out"])
            seen_delay_values.append(delay)
            if time_value >= first_seen_time + 0.2e-9:
                settled_delay_values.append(delay)

    if first_seen_time is None:
        return 0.0, ["seen_out_no_logic_high_samples"]
    if len(settled_delay_values) < 3:
        settled_delay_values = seen_delay_values
    tail_count = min(len(settled_delay_values), max(5, len(settled_delay_values) // 3))
    tail = sorted(settled_delay_values[-tail_count:])
    if not tail:
        return 0.0, ["no_post_seen_delay_samples"]
    delay_level = tail[len(tail) // 2]
    delay_ps = delay_level / max(seen_hi, 1e-6) * 200.0
    ok = 130.0 <= delay_ps <= 190.0
    return (1.0 if ok else 0.0), [
        f"delay_ps={delay_ps:.3f} seen_hi={seen_hi:.3f} post_seen_samples={len(settled_delay_values)}"
    ]


def _stream_phase_accumulator_timer_wrap_csv(csv_path: Path) -> tuple[float, list[str]]:
    indices, missing = _csv_required_indices(csv_path, {"time", "clk_out", "phase_out"})
    if indices is None:
        return 0.0, [f"missing {'/'.join(missing)}"]
    assert indices is not None

    phase_min = float("inf")
    phase_max = float("-inf")
    clk_min = float("inf")
    clk_max = float("-inf")
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            phase = _float_at(row, indices["phase_out"])
            clk = _float_at(row, indices["clk_out"])
            phase_min = min(phase_min, phase)
            phase_max = max(phase_max, phase)
            clk_min = min(clk_min, clk)
            clk_max = max(clk_max, clk)

    phase_span = phase_max - phase_min
    if phase_span < 0.4:
        return 0.0, [f"phase_span_too_small={phase_span:.3f}"]
    high_th = phase_min + 0.70 * phase_span
    low_th = phase_min + 0.30 * phase_span
    clk_th = 0.5 * (clk_max + clk_min)

    wraps = 0
    armed = False
    clk_rises = 0
    prev_clk: float | None = None
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            phase = _float_at(row, indices["phase_out"])
            clk = _float_at(row, indices["clk_out"])
            if phase >= high_th:
                armed = True
            elif armed and phase <= low_th:
                wraps += 1
                armed = False
            if prev_clk is not None and prev_clk < clk_th <= clk:
                clk_rises += 1
            prev_clk = clk

    ok = wraps >= 3 and clk_rises >= 3
    return (1.0 if ok else 0.0), [f"wraps={wraps} clk_rises={clk_rises} phase_span={phase_span:.3f}"]


def _stream_true_window_comparator_csv(csv_path: Path) -> tuple[float, list[str]]:
    required = {"time", "vin", "out"}
    runtime = CsvCheckerRuntime(csv_path)
    missing = runtime.missing(required)
    if missing:
        return 0.0, [f"missing {'/'.join(missing)}"]
    eval_rows, errors = runtime.resampled_rows({"vin", "out"}, sample_count=361)
    if errors:
        return 0.0, errors
    ok, note = _check_true_window_comparator_resampled(eval_rows)
    return (1.0 if ok else 0.0), [note]


def _stream_precision_rectifier_envelope_detector_csv(csv_path: Path) -> tuple[float, list[str]]:
    required = {"time", "clk", "rst", "vin", "rect", "env", "metric"}
    runtime = CsvCheckerRuntime(csv_path)
    missing = runtime.missing(required)
    if missing:
        return 0.0, [f"missing {'/'.join(missing)}"]

    mean_windows = {
        "reset_rect": (0.5e-9, 2.0e-9, "rect", 0.0, 0),
        "reset_env": (0.5e-9, 2.0e-9, "env", 0.0, 0),
        "pos_rect": (7.0e-9, 10.0e-9, "rect", 0.0, 0),
        "center_rect": (15.0e-9, 17.0e-9, "rect", 0.0, 0),
        "neg_rect": (22.0e-9, 26.0e-9, "rect", 0.0, 0),
        "peak_env": (43.0e-9, 48.0e-9, "env", 0.0, 0),
        "hold_env": (56.0e-9, 64.0e-9, "env", 0.0, 0),
        "hold_rect": (56.0e-9, 64.0e-9, "rect", 0.0, 0),
        "hold_metric": (56.0e-9, 64.0e-9, "metric", 0.0, 0),
    }
    post_count = 0
    below_rect = 0
    errors: list[float] = []

    for row in runtime.rows():
        time_s = runtime.float(row, "time")
        rst = runtime.float(row, "rst")
        vin = runtime.float(row, "vin")
        rect = runtime.float(row, "rect")
        env = runtime.float(row, "env")
        metric = runtime.float(row, "metric")
        values = {"rect": rect, "env": env, "metric": metric}
        for label, (start, stop, signal, total, count) in list(mean_windows.items()):
            if start <= time_s <= stop:
                mean_windows[label] = (start, stop, signal, total + values[signal], count + 1)
        if rst <= 0.45 and time_s > 3e-9:
            post_count += 1
            if env + 0.06 < rect:
                below_rect += 1
            if 5e-9 <= time_s <= 30e-9 or 40e-9 <= time_s <= 68e-9:
                errors.append(abs(rect - min(0.9, 0.45 + abs(vin - 0.45))))

    means: dict[str, float] = {}
    for label, (_, _, _, total, count) in mean_windows.items():
        if count == 0:
            return 0.0, ["rectifier_missing_sample_windows"]
        means[label] = total / count

    if abs(means["reset_rect"] - 0.45) > 0.10 or abs(means["reset_env"] - 0.45) > 0.10:
        return 0.0, [f"rectifier_reset_common_mode rect={means['reset_rect']:.3f} env={means['reset_env']:.3f}"]
    if means["pos_rect"] < 0.62:
        return 0.0, [f"rectifier_positive_half_not_rectified={means['pos_rect']:.3f}"]
    if means["neg_rect"] < 0.62:
        return 0.0, [f"rectifier_negative_half_not_rectified={means['neg_rect']:.3f}"]
    if abs(means["center_rect"] - 0.45) > 0.08:
        return 0.0, [f"rectifier_center_not_common_mode={means['center_rect']:.3f}"]
    if means["peak_env"] < 0.74:
        return 0.0, [f"rectifier_envelope_peak_too_low={means['peak_env']:.3f}"]
    if means["hold_env"] < means["hold_rect"] + 0.10 or means["hold_metric"] < 0.35:
        return 0.0, [
            "rectifier_envelope_hold_missing "
            f"env={means['hold_env']:.3f} rect={means['hold_rect']:.3f} metric={means['hold_metric']:.3f}"
        ]
    if post_count == 0:
        return 0.0, ["rectifier_no_post_reset_rows"]
    if below_rect > max(2, post_count // 20):
        return 0.0, [f"rectifier_envelope_below_rect_count={below_rect}"]
    if errors:
        p90 = sorted(errors)[int(0.90 * (len(errors) - 1))]
        if p90 > 0.09:
            return 0.0, [f"rectifier_rect_abs_tracking_p90={p90:.3f}"]

    return 1.0, [
        "precision_rectifier_envelope_detector "
        f"pos/neg={means['pos_rect']:.3f}/{means['neg_rect']:.3f} "
        f"env_peak={means['peak_env']:.3f} "
        f"hold={means['hold_env']:.3f}/{means['hold_rect']:.3f}"
    ]


def _stream_programmable_stimulus_sequencer_csv(csv_path: Path) -> tuple[float, list[str]]:
    required = {"time", "clk", "rst", "mode", "gate", "out", "metric"}
    runtime = CsvCheckerRuntime(csv_path)
    missing = runtime.missing(required)
    if missing:
        return 0.0, [f"missing {'/'.join(missing)}"]

    ramp_count = 0
    ramp_drops = 0
    ramp_first: float | None = None
    ramp_last: float | None = None
    sine_count = 0
    sine_min = float("inf")
    sine_max = float("-inf")
    sine_sum = 0.0
    sine_prev_t: float | None = None
    sine_prev_center: float | None = None
    crossing_times: list[float] = []
    burst_count = 0
    burst_min = float("inf")
    burst_max = float("-inf")
    burst_transitions = 0
    burst_prev_out: float | None = None
    gate_low_sum = 0.0
    gate_low_count = 0
    metric_windows = {
        "ramp": (8.0e-9, 22.0e-9, 0.0, 0),
        "sine": (32.0e-9, 56.0e-9, 0.0, 0),
        "burst": (67.0e-9, 75.0e-9, 0.0, 0),
        "idle": (76.5e-9, 79.0e-9, 0.0, 0),
    }

    for row in runtime.rows():
        time_s = runtime.float(row, "time")
        rst = runtime.float(row, "rst")
        gate = runtime.float(row, "gate")
        out = runtime.float(row, "out")
        metric = runtime.float(row, "metric")
        if rst <= 0.45:
            if 6.0e-9 <= time_s <= 24.0e-9:
                ramp_count += 1
                if ramp_first is None:
                    ramp_first = out
                if ramp_last is not None and out < ramp_last - 0.02:
                    ramp_drops += 1
                ramp_last = out
            if 30.0e-9 <= time_s <= 58.0e-9:
                sine_count += 1
                sine_min = min(sine_min, out)
                sine_max = max(sine_max, out)
                sine_sum += out
                cur_center = out - 0.45
                if sine_prev_center is not None and sine_prev_t is not None:
                    if sine_prev_center == 0.0:
                        crossing_times.append(sine_prev_t)
                    elif sine_prev_center * cur_center < 0.0:
                        frac = abs(sine_prev_center) / (abs(sine_prev_center) + abs(cur_center))
                        crossing_times.append(sine_prev_t + frac * (time_s - sine_prev_t))
                sine_prev_t = time_s
                sine_prev_center = cur_center
            if 66.0e-9 <= time_s <= 88.0e-9 and gate > 0.45:
                burst_count += 1
                burst_min = min(burst_min, out)
                burst_max = max(burst_max, out)
                if burst_prev_out is not None and (
                    (burst_prev_out <= 0.45 < out) or (burst_prev_out >= 0.45 > out)
                ):
                    burst_transitions += 1
                burst_prev_out = out
            if 76.0e-9 <= time_s <= 79.5e-9 and gate <= 0.45:
                gate_low_sum += out
                gate_low_count += 1
        for label, (start, stop, total, count) in list(metric_windows.items()):
            if start <= time_s <= stop:
                metric_windows[label] = (start, stop, total + metric, count + 1)

    if min(ramp_count, sine_count, burst_count) < 6 or gate_low_count < 3:
        return 0.0, [
            "sequencer_missing_windows "
            f"ramp={ramp_count} sine={sine_count} burst={burst_count} gate_low={gate_low_count}"
        ]
    assert ramp_first is not None and ramp_last is not None
    ramp_delta = ramp_last - ramp_first
    if ramp_drops or ramp_delta < 0.16 or not (0.16 <= ramp_first <= 0.30):
        return 0.0, [
            "sequencer_ramp_not_monotonic "
            f"drops={ramp_drops} delta={ramp_delta:.3f} start={ramp_first:.3f}"
        ]
    sine_mean = sine_sum / sine_count
    center_crossings = len(crossing_times)
    if sine_min > 0.34 or sine_max < 0.56 or abs(sine_mean - 0.45) > 0.05 or center_crossings < 4:
        return 0.0, [
            "sequencer_chirp_segment_wrong "
            f"min={sine_min:.3f} max={sine_max:.3f} mean={sine_mean:.3f} crossings={center_crossings}"
        ]
    half_periods = [cur - prev for prev, cur in zip(crossing_times, crossing_times[1:])]
    if len(half_periods) < 3:
        return 0.0, [f"sequencer_chirp_missing_periods={len(half_periods)}"]
    early_half_period = sum(half_periods[:2]) / min(2, len(half_periods[:2]))
    late_half_period = sum(half_periods[-2:]) / min(2, len(half_periods[-2:]))
    if late_half_period >= early_half_period * 0.90:
        return 0.0, [
            "sequencer_chirp_frequency_not_increasing "
            f"early_half_period={early_half_period:.3e} late_half_period={late_half_period:.3e}"
        ]

    switch_times = [25.8e-9, 26.3e-9, 61.8e-9, 62.3e-9]
    switch_samples = runtime.samples_at("out", switch_times)
    if any(switch_samples[target] is None for target in switch_times):
        return 0.0, ["sequencer_missing_switch_samples"]
    switch_1_delta = abs(float(switch_samples[26.3e-9]) - float(switch_samples[25.8e-9]))
    switch_2_delta = abs(float(switch_samples[62.3e-9]) - float(switch_samples[61.8e-9]))
    if switch_1_delta > 0.12 or switch_2_delta > 0.12:
        return 0.0, [f"sequencer_mode_switch_discontinuity={switch_1_delta:.3f}/{switch_2_delta:.3f}"]

    gate_low_mean = gate_low_sum / gate_low_count
    if burst_min > 0.36 or burst_max < 0.54 or burst_transitions < 2 or abs(gate_low_mean - 0.45) > 0.08:
        return 0.0, [
            "sequencer_burst_schedule_wrong "
            f"low={burst_min:.3f} high={burst_max:.3f} transitions={burst_transitions} "
            f"gate_low_mean={gate_low_mean:.3f}"
        ]

    metric_means: dict[str, float] = {}
    for label, (_, _, total, count) in metric_windows.items():
        if count == 0:
            return 0.0, ["sequencer_missing_metric_windows"]
        metric_means[label] = total / count
    if not (0.12 <= metric_means["ramp"] <= 0.30 and 0.42 <= metric_means["sine"] <= 0.58 and metric_means["burst"] >= 0.70):
        return 0.0, [
            "sequencer_metric_does_not_mark_modes "
            f"ramp={metric_means['ramp']:.3f} sine={metric_means['sine']:.3f} burst={metric_means['burst']:.3f}"
        ]
    if metric_means["idle"] < 0.55 or metric_means["idle"] > metric_means["burst"] - 0.05:
        return 0.0, [f"sequencer_idle_metric_wrong idle={metric_means['idle']:.3f} burst={metric_means['burst']:.3f}"]

    return 1.0, [
        "programmable_stimulus_sequencer "
        f"ramp_delta={ramp_delta:.3f} sine={sine_min:.3f}/{sine_max:.3f} "
        f"chirp_half_period={early_half_period:.3e}->{late_half_period:.3e} "
        f"switch={switch_1_delta:.3f}/{switch_2_delta:.3f} "
        f"burst={burst_min:.3f}/{burst_max:.3f} transitions={burst_transitions}"
    ]


def _stream_edge_ratio(
    csv_path: Path,
    indices: dict[str, int],
    num_signal: str,
    den_signal: str,
    t_start: float,
    t_end: float,
) -> tuple[float, str]:
    prev_num: float | None = None
    prev_den: float | None = None
    num_edges: list[float] = []
    den_edges: list[float] = []
    rows_in_window = 0
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            time_s = _float_at(row, indices["time"])
            if time_s < t_start or time_s > t_end:
                continue
            rows_in_window += 1
            num = _float_at(row, indices[num_signal])
            den = _float_at(row, indices[den_signal])
            if prev_num is not None and prev_num < 0.45 <= num:
                num_edges.append(time_s)
            if prev_den is not None and prev_den < 0.45 <= den:
                den_edges.append(time_s)
            prev_num = num
            prev_den = den
    if rows_in_window < 4:
        return float("nan"), "missing_window_or_signals"
    if len(num_edges) < 3 or len(den_edges) < 3:
        return float("nan"), f"not_enough_edges num={len(num_edges)} den={len(den_edges)}"
    num_freq = (len(num_edges) - 1) / max(num_edges[-1] - num_edges[0], 1e-18)
    den_freq = (len(den_edges) - 1) / max(den_edges[-1] - den_edges[0], 1e-18)
    return num_freq / max(den_freq, 1e-18), "ok"


def _stream_weighted_high_fraction_window(
    csv_path: Path,
    indices: dict[str, int],
    signal: str,
    threshold: float,
    t_start: float,
    t_end: float,
) -> float:
    first_t: float | None = None
    last_t: float | None = None
    high_dt = 0.0
    prev_t: float | None = None
    prev_v: float | None = None
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            time_s = _float_at(row, indices["time"])
            if time_s < t_start or time_s > t_end:
                continue
            value = _float_at(row, indices[signal])
            if first_t is None:
                first_t = time_s
            if prev_t is not None and prev_v is not None:
                dt = time_s - prev_t
                if dt > 0.0 and 0.5 * (prev_v + value) > threshold:
                    high_dt += dt
            prev_t = time_s
            prev_v = value
            last_t = time_s
    if first_t is None or last_t is None or last_t <= first_t:
        return 0.0
    return high_dt / (last_t - first_t)


def _stream_adpll_ratio_hop_csv(csv_path: Path) -> tuple[float, list[str]]:
    required = {"time", "ref_clk", "ratio_ctrl", "fb_clk", "vout", "lock", "vctrl_mon"}
    indices, missing = _csv_required_indices(csv_path, required)
    if indices is None:
        return 0.0, [f"missing {'/'.join(missing)}"]
    assert indices is not None

    hop_t = float("nan")
    lock_max = float("-inf")
    vctrl_in_range = True
    prev_ratio: float | None = None
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            time_s = _float_at(row, indices["time"])
            ratio_ctrl = _float_at(row, indices["ratio_ctrl"])
            lock = _float_at(row, indices["lock"])
            vctrl = _float_at(row, indices["vctrl_mon"])
            lock_max = max(lock_max, lock)
            if not (-1e-6 <= vctrl <= 1.2):
                vctrl_in_range = False
            if not math.isfinite(hop_t) and prev_ratio is not None and prev_ratio < 5.0 <= ratio_ctrl:
                hop_t = time_s
            prev_ratio = ratio_ctrl

    if not math.isfinite(hop_t):
        return 0.0, ["ratio_hop_not_detected"]

    windows = {
        "pre": (hop_t - 1.0e-6, hop_t - 2.0e-7),
        "post": (hop_t + 1.2e-6, hop_t + 2.5e-6),
    }
    pre_ratio, pre_note = _stream_edge_ratio(csv_path, indices, "vout", "ref_clk", *windows["pre"])
    post_ratio, post_note = _stream_edge_ratio(csv_path, indices, "vout", "ref_clk", *windows["post"])
    pre_div_ratio, pre_div_note = _stream_edge_ratio(csv_path, indices, "vout", "fb_clk", *windows["pre"])
    post_div_ratio, post_div_note = _stream_edge_ratio(csv_path, indices, "vout", "fb_clk", *windows["post"])
    pre_fb_ref_ratio, pre_fb_ref_note = _stream_edge_ratio(csv_path, indices, "fb_clk", "ref_clk", *windows["pre"])
    post_fb_ref_ratio, post_fb_ref_note = _stream_edge_ratio(csv_path, indices, "fb_clk", "ref_clk", *windows["post"])
    if pre_note != "ok":
        return 0.0, [f"pre_window_{pre_note}"]
    if post_note != "ok":
        return 0.0, [f"post_window_{post_note}"]
    if pre_div_note != "ok":
        return 0.0, [f"pre_divider_window_{pre_div_note}"]
    if post_div_note != "ok":
        return 0.0, [f"post_divider_window_{post_div_note}"]
    if pre_fb_ref_note != "ok":
        return 0.0, [f"pre_feedback_window_{pre_fb_ref_note}"]
    if post_fb_ref_note != "ok":
        return 0.0, [f"post_feedback_window_{post_fb_ref_note}"]

    vth = lock_max * 0.5
    pre_lock = _stream_weighted_high_fraction_window(csv_path, indices, "lock", vth, hop_t - 4.0e-7, hop_t - 5.0e-8)
    post_lock = _stream_weighted_high_fraction_window(csv_path, indices, "lock", vth, hop_t + 1.8e-6, hop_t + 2.8e-6)
    ok = (
        abs(pre_ratio - 4.0) <= 0.25
        and abs(post_ratio - 6.0) <= 0.35
        and abs(pre_div_ratio - 4.0) <= 0.25
        and abs(post_div_ratio - 6.0) <= 0.35
        and abs(pre_fb_ref_ratio - 1.0) <= 0.15
        and abs(post_fb_ref_ratio - 1.0) <= 0.15
        and pre_lock >= 0.8
        and post_lock >= 0.8
        and vctrl_in_range
    )
    return (1.0 if ok else 0.0), [
        f"hop_t={hop_t:.3e} "
        f"pre_vout_ref={pre_ratio:.3f} "
        f"post_vout_ref={post_ratio:.3f} "
        f"pre_vout_fb={pre_div_ratio:.3f} "
        f"post_vout_fb={post_div_ratio:.3f} "
        f"pre_fb_ref={pre_fb_ref_ratio:.3f} "
        f"post_fb_ref={post_fb_ref_ratio:.3f} "
        f"pre_lock={pre_lock:.3f} "
        f"post_lock={post_lock:.3f} "
        f"vctrl_range_ok={vctrl_in_range}"
    ]


def _stream_sample_hold_droop_csv(csv_path: Path) -> tuple[float, list[str]]:
    indices, missing = _csv_required_indices(csv_path, {"time", "vin", "clk", "vout"})
    if indices is None:
        return 0.0, [f"missing {'/'.join(missing)}"]
    assert indices is not None

    times: list[float] = []
    clk: list[float] = []
    vin: list[float] = []
    vout: list[float] = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            times.append(_float_at(row, indices["time"]))
            clk.append(_float_at(row, indices["clk"]))
            vin.append(_float_at(row, indices["vin"]))
            vout.append(_float_at(row, indices["vout"]))

    edge_idx = [idx for idx in range(1, len(clk)) if clk[idx - 1] <= 0.45 < clk[idx]]
    if len(edge_idx) < 6:
        return 0.0, [f"too_few_clock_edges={len(edge_idx)}"]

    sample_mismatch = 0
    checked_samples = 0
    for edge_pos in range(min(6, len(edge_idx) - 1)):
        idx = edge_idx[edge_pos]
        t_target = times[idx] + 1.2e-9
        settle_idx = next((j for j in range(idx, len(times)) if times[j] >= t_target), len(times) - 1)
        err = abs(vout[settle_idx] - vin[idx])
        checked_samples += 1
        if err > 0.04:
            sample_mismatch += 1
    if checked_samples == 0 or sample_mismatch > 1:
        return 0.0, [f"sample_mismatch={sample_mismatch}/{max(checked_samples, 1)}"]

    droop_windows = 0
    droop_failures = 0
    for edge_pos in range(min(6, len(edge_idx) - 1)):
        start_i = edge_idx[edge_pos]
        end_i = edge_idx[edge_pos + 1]
        t_start = times[start_i] + 1.5e-9
        t_end = times[end_i] - 1.5e-9
        idxs = [idx for idx in range(start_i, end_i) if t_start <= times[idx] <= t_end]
        if len(idxs) < 6:
            continue
        first = vout[idxs[0]]
        if first < 0.55:
            continue
        last = vout[idxs[-1]]
        droop = first - last
        upward_steps = sum(1 for a, b in zip(idxs[:-1], idxs[1:]) if (vout[b] - vout[a]) > 0.004)
        droop_windows += 1
        if droop < 0.006 or droop > 0.30:
            droop_failures += 1
        if upward_steps > max(1, len(idxs) // 8):
            droop_failures += 1

    if droop_windows < 2:
        return 0.0, [f"insufficient_high_hold_windows={droop_windows}"]
    if droop_failures > 0:
        return 0.0, [f"droop_failures={droop_failures} windows={droop_windows}"]
    return 1.0, [f"edges={len(edge_idx)} sample_mismatch={sample_mismatch}/{checked_samples} droop_windows={droop_windows}"]


def _stream_cmp_delay_csv(csv_path: Path) -> tuple[float, list[str]]:
    required = {"time", "clk", "vinp", "vinn", "out_p", "out_n", "delay_ps"}
    runtime = CsvCheckerRuntime(csv_path)
    if runtime.missing(required):
        return 0.0, ["missing time/clk/vinp/vinn/out_p/out_n/delay_ps"]

    times: list[float] = []
    out_p: list[float] = []
    for row in runtime.rows():
        times.append(runtime.float(row, "time"))
        out_p.append(runtime.float(row, "out_p"))

    ok, note = _check_cmp_delay_vectors(times, out_p)
    return (1.0 if ok else 0.0), [note]


STREAMING_BEHAVIOR_CHECKS = {
    "pfd_deadzone_smoke": _stream_pfd_deadzone_csv,
    "pfd_small_phase_response_smoke": _stream_pfd_deadzone_csv,
    "vbm1_pfd_small_phase_error_response_dut": _stream_pfd_deadzone_csv,
    "pfd_reset_race_smoke": _stream_pfd_reset_race_csv,
    "vbm1_pfd_reset_race_dut": _stream_pfd_reset_race_csv,
    "vbm1_pfd_reset_race_tb": _stream_pfd_reset_race_csv,
    "vbm1_pfd_reset_race_bugfix": _stream_pfd_reset_race_csv,
    "vbm1_pfd_reset_race_e2e": _stream_pfd_reset_race_csv,
    "cppll_freq_step_reacquire_smoke": _stream_cppll_freq_step_reacquire_csv,
    "vbr1_l2_cppll_tracking_and_frequency_step_reacquire_flow_tb": _stream_cppll_freq_step_reacquire_csv,
    "dac_binary_clk_4b_smoke": _stream_dac_binary_clk_4b_csv,
    "sar_adc_dac_weighted_8b_smoke": _stream_sar_adc_dac_weighted_8b_csv,
    "vbr1_l2_weighted_sar_adc_dac_loop": _stream_sar_adc_dac_weighted_8b_release_csv,
    "vbr1_l2_weighted_sar_adc_dac_loop_tb": _stream_sar_adc_dac_weighted_8b_release_csv,
    "vbr1_l2_weighted_sar_adc_dac_loop_e2e": _stream_sar_adc_dac_weighted_8b_release_csv,
    "dwa_ptr_gen_no_overlap_smoke": _stream_dwa_ptr_gen_no_overlap_csv,
    "digital_basics_smoke": _stream_not_gate_csv,
    "gray_counter_one_bit_change_smoke": _stream_gray_counter_one_bit_change_csv,
    "dwa_wraparound_smoke": _stream_dwa_wraparound_csv,
    "gain_extraction_smoke": _stream_gain_extraction_csv,
    "vbr1_l2_gain_extraction_convergence_measurement_flow_tb": _stream_gain_extraction_csv,
    "vbr1_l2_gain_extraction_convergence_measurement_flow_e2e": _stream_gain_extraction_csv,
    "vbr1_l1_gain_estimator_tb": _stream_gain_estimator_csv,
    "vbr1_l1_gain_estimator_e2e": _stream_gain_estimator_csv,
    "cdac_cal": _stream_cdac_cal_csv,
    "lfsr_smoke": _stream_lfsr_csv,
    "vbr1_l1_lfsr_prbs_generator_tb": _stream_lfsr_csv,
    "vbr1_l1_lfsr_prbs_generator_e2e": _stream_lfsr_csv,
    "prbs7": _stream_prbs7_csv,
    "vbr1_l1_lfsr_prbs_generator_bugfix": _stream_prbs7_csv,
    "bbpd": _stream_bbpd_csv,
    "vbr1_l1_bang_bang_phase_detector_bugfix": _stream_bbpd_csv,
    "cross_hysteresis_window_smoke": _stream_cross_hysteresis_window_csv,
    "window_comparator_smoke": _stream_true_window_comparator_csv,
    "vbr1_l1_window_comparator_detector": _stream_true_window_comparator_csv,
    "vbr1_l1_window_comparator_detector_dut": _stream_true_window_comparator_csv,
    "vbr1_l1_window_comparator_detector_tb": _stream_true_window_comparator_csv,
    "vbr1_l1_window_comparator_detector_bugfix": _stream_true_window_comparator_csv,
    "vbr1_l1_window_comparator_detector_e2e": _stream_true_window_comparator_csv,
    "cross_interval_163p333_smoke": _stream_cross_interval_163p333_csv,
    "vbr1_l1_edge_interval_timer_tb": _stream_cross_interval_163p333_csv,
    "vbr1_l1_edge_interval_timer_e2e": _stream_cross_interval_163p333_csv,
    "phase_accumulator_timer_wrap_smoke": _stream_phase_accumulator_timer_wrap_csv,
    "vbr1_l1_precision_rectifier_envelope_detector": _stream_precision_rectifier_envelope_detector_csv,
    "vbr1_l1_precision_rectifier_envelope_detector_dut": _stream_precision_rectifier_envelope_detector_csv,
    "vbr1_l1_precision_rectifier_envelope_detector_tb": _stream_precision_rectifier_envelope_detector_csv,
    "vbr1_l1_precision_rectifier_envelope_detector_bugfix": _stream_precision_rectifier_envelope_detector_csv,
    "vbr1_l1_precision_rectifier_envelope_detector_e2e": _stream_precision_rectifier_envelope_detector_csv,
    "vbr1_l2_programmable_stimulus_sequencer": _stream_programmable_stimulus_sequencer_csv,
    "vbr1_l2_programmable_stimulus_sequencer_dut": _stream_programmable_stimulus_sequencer_csv,
    "vbr1_l2_programmable_stimulus_sequencer_tb": _stream_programmable_stimulus_sequencer_csv,
    "vbr1_l2_programmable_stimulus_sequencer_bugfix": _stream_programmable_stimulus_sequencer_csv,
    "vbr1_l2_programmable_stimulus_sequencer_e2e": _stream_programmable_stimulus_sequencer_csv,
    "adpll_ratio_hop_smoke": _stream_adpll_ratio_hop_csv,
    "vbr1_l2_adpll_lock_ratio_hop_timer_flow_tb": _stream_adpll_ratio_hop_csv,
    "sample_hold_droop_smoke": _stream_sample_hold_droop_csv,
    "multimod_divider_ratio_switch_smoke": _stream_multimod_divider_ratio_switch_csv,
    "cmp_delay_smoke": _stream_cmp_delay_csv,
    "vbr1_l1_propagation_delay_comparator": _stream_cmp_delay_csv,
    "vbr1_l1_propagation_delay_comparator_dut": _stream_cmp_delay_csv,
    "vbr1_l1_propagation_delay_comparator_tb": _stream_cmp_delay_csv,
    "vbr1_l1_propagation_delay_comparator_bugfix": _stream_cmp_delay_csv,
    "vbr1_l1_propagation_delay_comparator_e2e": _stream_cmp_delay_csv,
}

VALIDATED_FAST_CHECKER_TASKS = frozenset(STREAMING_BEHAVIOR_CHECKS)

_SAR8_TRACE = frozenset({f"dout_{idx}" for idx in range(8)} | {"vin_sample", "trial_vdac"})
_DWA16_TRACE = frozenset(
    {f"ptr_{idx}" for idx in range(16)}
    | {f"cell_en_{idx}" for idx in range(16)}
)
_DWA_CODE4_TRACE = frozenset({f"code_{idx}" for idx in range(4)})
_PRBS7_TRACE = frozenset({f"state_{idx}" for idx in range(7)})
_GRAY4_TRACE = frozenset({f"g{idx}" for idx in range(4)})

_STREAMING_TRACE_REQUIREMENTS_BY_FUNC = {
    _stream_pfd_deadzone_csv: frozenset({"time", "ref", "div", "up", "dn"}),
    _stream_pfd_reset_race_csv: frozenset({"time", "ref", "div", "up", "dn"}),
    _stream_cppll_freq_step_reacquire_csv: frozenset({"time", "ref_clk", "fb_clk", "lock", "vctrl_mon"}),
    _stream_dac_binary_clk_4b_csv: frozenset({"din3", "din2", "din1", "din0", "aout"}),
    _stream_sar_adc_dac_weighted_8b_csv: frozenset({"time", "vin", "vin_sh", "clks", "vout", "rst_n"}) | _SAR8_TRACE,
    _stream_sar_adc_dac_weighted_8b_release_csv: frozenset({"time", "vin", "vin_sh", "clks", "vout", "rst_n", "conv_done", "vin_sample"}) | _SAR8_TRACE,
    _stream_dwa_ptr_gen_no_overlap_csv: frozenset({"time", "clk_i", "rst_ni"}) | _DWA16_TRACE,
    _stream_not_gate_csv: frozenset({"time", "a", "y", "not_a", "not_y"}),
    _stream_gray_counter_one_bit_change_csv: frozenset({"time", "clk", "rst", "rstb"}) | _GRAY4_TRACE,
    _stream_dwa_wraparound_csv: frozenset({"time", "clk_i", "rst_ni"}) | _DWA16_TRACE | _DWA_CODE4_TRACE,
    _stream_gain_extraction_csv: frozenset({"vinp", "vinn", "vamp_p", "vamp_n"}),
    _stream_gain_estimator_csv: frozenset({"time", "vinp", "vinn", "voutp", "voutn", "gain_out", "valid"}),
    # _stream_cdac_cal_csv discovers vdac/vcap/vout columns dynamically from the
    # header, so it intentionally stays on the full trace until its checker
    # contract is made explicit.
    _stream_multimod_divider_ratio_switch_csv: frozenset({"time", "clk_in", "div_out"}),
    _stream_lfsr_csv: frozenset({"dpn", "rstb"}),
    _stream_prbs7_csv: frozenset({"time", "clk", "rst_n", "en", "serial_out"}) | _PRBS7_TRACE,
    _stream_bbpd_csv: frozenset({"time", "data", "clk", "retimed_data", "up", "down"}),
    _stream_cross_hysteresis_window_csv: frozenset({"time", "vin", "out"}),
    _stream_true_window_comparator_csv: frozenset({"time", "vin", "out"}),
    _stream_cross_interval_163p333_csv: frozenset({"time", "delay_out", "seen_out"}),
    _stream_phase_accumulator_timer_wrap_csv: frozenset({"time", "clk_out", "phase_out"}),
    _stream_precision_rectifier_envelope_detector_csv: frozenset({"time", "clk", "rst", "vin", "rect", "env", "metric"}),
    _stream_programmable_stimulus_sequencer_csv: frozenset({"time", "clk", "rst", "mode", "gate", "out", "metric"}),
    _stream_adpll_ratio_hop_csv: frozenset({"time", "ref_clk", "ratio_ctrl", "fb_clk", "vout", "lock", "vctrl_mon"}),
    _stream_sample_hold_droop_csv: frozenset({"time", "vin", "clk", "vout"}),
    _stream_cmp_delay_csv: frozenset({"time", "clk", "vinp", "vinn", "out_p", "out_n", "delay_ps"}),
}

_CHECKER_TRACE_CONTRACT_CACHE: dict[str, frozenset[str]] = {}


def _trace_contracts_enabled() -> bool:
    return not _env_truthy("VAEVAS_DISABLE_REQUIRED_TRACE")


def _auto_row_checker_trace_contracts_enabled() -> bool:
    return not _env_truthy("VAEVAS_DISABLE_ROW_CHECKER_TRACE_CONTRACTS")


def _row_checker_trace_fallback_enabled() -> bool:
    return not _env_truthy("VAEVAS_DISABLE_ROW_CHECKER_TRACE_FALLBACK")


def _split_trace_signal_list(text: str | None) -> frozenset[str]:
    if not text:
        return frozenset()
    signals: set[str] = set()
    for token in re.split(r"[\s,]+", text):
        name = token.strip()
        if name:
            signals.add(name)
    return frozenset(signals)


def _task_env_suffix(task_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", task_id).strip("_").upper()


def _extra_trace_signals_for_checker(task_id: str) -> frozenset[str]:
    """Return user-requested debug columns to append to an existing sparse trace.

    Supported forms:

    - `VAEVAS_EXTRA_TRACE_SIGNALS=foo,bar` applies to every sparse trace.
    - `VAEVAS_EXTRA_TRACE_SIGNALS_BY_TASK=task_id=foo,bar;entry_prefix=debug`
      applies to an exact checker id or a release entry prefix before `_dut`,
      `_tb`, `_bugfix`, `_e2e`.
    - `VAEVAS_EXTRA_TRACE_SIGNALS_<TASK_ID>=foo,bar` is an exact-id escape hatch.
    """
    signals = set(_split_trace_signal_list(os.environ.get("VAEVAS_EXTRA_TRACE_SIGNALS")))

    by_task = os.environ.get("VAEVAS_EXTRA_TRACE_SIGNALS_BY_TASK", "")
    for entry in re.split(r"[;\n]+", by_task):
        item = entry.strip()
        if not item:
            continue
        if "=" in item:
            key, value = item.split("=", 1)
        elif ":" in item:
            key, value = item.split(":", 1)
        else:
            continue
        key = key.strip()
        if not key:
            continue
        exact = key == task_id
        release_prefix = task_id.startswith(f"{key}_")
        wildcard_prefix = key.endswith("*") and task_id.startswith(key[:-1])
        if exact or release_prefix or wildcard_prefix:
            signals.update(_split_trace_signal_list(value))

    task_specific = os.environ.get(f"VAEVAS_EXTRA_TRACE_SIGNALS_{_task_env_suffix(task_id)}")
    signals.update(_split_trace_signal_list(task_specific))
    return frozenset(signals)


def _checker_string_sequence_global(checker, name: str) -> set[str]:
    value = getattr(checker, "__globals__", {}).get(name)
    if not isinstance(value, (frozenset, set, list, tuple)):
        return set()
    strings = {item.strip() for item in value if isinstance(item, str) and item.strip()}
    return strings if len(strings) == len(value) else set()


def _checker_fstring_range_values(node: ast.AST) -> set[str]:
    """Expand simple checker-local patterns like `[f"seg{i}" for i in range(15)]`."""
    if not isinstance(node, (ast.ListComp, ast.SetComp, ast.GeneratorExp)):
        return set()
    if len(node.generators) != 1:
        return set()
    generator = node.generators[0]
    if not isinstance(generator.target, ast.Name):
        return set()
    loop_name = generator.target.id
    if (
        not isinstance(generator.iter, ast.Call)
        or not isinstance(generator.iter.func, ast.Name)
        or generator.iter.func.id != "range"
        or len(generator.iter.args) != 1
        or not isinstance(generator.iter.args[0], ast.Constant)
        or not isinstance(generator.iter.args[0].value, int)
    ):
        return set()
    stop = generator.iter.args[0].value
    if stop < 0 or stop > 256:
        return set()

    elt = node.elt
    if not isinstance(elt, ast.JoinedStr):
        return set()
    parts: list[str | None] = []
    saw_loop_value = False
    for value in elt.values:
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            parts.append(value.value)
        elif (
            isinstance(value, ast.FormattedValue)
            and isinstance(value.value, ast.Name)
            and value.value.id == loop_name
        ):
            parts.append(None)
            saw_loop_value = True
        else:
            return set()
    if not saw_loop_value:
        return set()

    names: set[str] = set()
    for idx in range(stop):
        text = "".join(str(idx) if part is None else part for part in parts).strip()
        if text:
            names.add(text)
    return names


def _checker_for_loop_fstring_values(tree: ast.AST) -> set[str]:
    """Expand simple checker loops like `for idx in range(8): signal = f"div_code_{idx}"`."""
    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.For) or not isinstance(node.target, ast.Name):
            continue
        loop_name = node.target.id
        if (
            not isinstance(node.iter, ast.Call)
            or not isinstance(node.iter.func, ast.Name)
            or node.iter.func.id != "range"
            or len(node.iter.args) != 1
            or not isinstance(node.iter.args[0], ast.Constant)
            or not isinstance(node.iter.args[0].value, int)
        ):
            continue
        stop = node.iter.args[0].value
        if stop < 0 or stop > 256:
            continue
        for child in ast.walk(node):
            if not isinstance(child, ast.JoinedStr):
                continue
            parts: list[str | None] = []
            saw_loop_value = False
            for value in child.values:
                if isinstance(value, ast.Constant) and isinstance(value.value, str):
                    parts.append(value.value)
                elif (
                    isinstance(value, ast.FormattedValue)
                    and isinstance(value.value, ast.Name)
                    and value.value.id == loop_name
                ):
                    parts.append(None)
                    saw_loop_value = True
                else:
                    parts = []
                    break
            if not saw_loop_value or not parts:
                continue
            for idx in range(stop):
                text = "".join(str(idx) if part is None else part for part in parts).strip()
                if text:
                    names.add(text)
    return names


def _checker_indexed_columns_from_source(tree: ast.AST) -> set[str]:
    """Infer columns from `cols = indexed_columns(keys, "prefix_")` plus `len(cols) != N`."""
    prefix_by_var: dict[str, str] = {}
    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            continue
        value = node.value
        if (
            isinstance(value, ast.Call)
            and isinstance(value.func, ast.Name)
            and value.func.id == "indexed_columns"
            and len(value.args) >= 2
            and isinstance(value.args[1], ast.Constant)
            and isinstance(value.args[1].value, str)
        ):
            prefix_by_var[node.targets[0].id] = value.args[1].value

    if not prefix_by_var:
        return names

    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare):
            continue
        left = node.left
        if (
            not isinstance(left, ast.Call)
            or not isinstance(left.func, ast.Name)
            or left.func.id != "len"
            or len(left.args) != 1
            or not isinstance(left.args[0], ast.Name)
        ):
            continue
        prefix = prefix_by_var.get(left.args[0].id)
        if prefix is None:
            continue
        for comparator in node.comparators:
            if (
                isinstance(comparator, ast.Constant)
                and isinstance(comparator.value, int)
                and 0 <= comparator.value <= 256
            ):
                names.update(f"{prefix}{idx}" for idx in range(comparator.value))
    return names


_CHECKER_PREFIX_TRACE_WIDTHS = {
    "ptr_": 16,
    "cell_en_": 16,
}


def _checker_startswith_prefix_columns(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "startswith"
            and len(node.args) == 1
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
        ):
            prefix = node.args[0].value
            width = _CHECKER_PREFIX_TRACE_WIDTHS.get(prefix)
            if width is not None:
                names.update(f"{prefix}{idx}" for idx in range(width))
    return names


def _checker_inline_required_sets(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "issubset"
            and isinstance(node.func.value, (ast.Set, ast.List, ast.Tuple))
        ):
            for element in node.func.value.elts:
                if isinstance(element, ast.Constant) and isinstance(element.value, str):
                    text = element.value.strip()
                    if text:
                        names.add(text)
    return names


def _checker_required_set_from_source(checker) -> frozenset[str]:
    """Infer a row-based checker's explicit CSV column contract.

    This intentionally only trusts literal assignments like
    `required = {"time", "clk", ...}`.  Many checkers use helper calls and
    diagnostic strings, but mining arbitrary string literals is too risky: a
    false sparse contract can hide columns the original row checker needs.  The
    fallback rerun in `run_case()` protects correctness, but keeping inference
    conservative avoids unnecessary reruns.
    """
    try:
        source = inspect.getsource(checker)
    except (OSError, TypeError):
        return frozenset()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return frozenset()

    names: set[str] = set()
    local_sequences: dict[str, set[str]] = {}

    def _literal_string_set(node: ast.AST) -> set[str]:
        if not isinstance(node, (ast.Set, ast.List, ast.Tuple)):
            return set()
        values: set[str] = set()
        for element in node.elts:
            if isinstance(element, ast.Constant) and isinstance(element.value, str):
                text = element.value.strip()
                if text:
                    values.add(text)
            elif isinstance(element, ast.Starred) and isinstance(element.value, ast.Name):
                values.update(local_sequences.get(element.value.id, set()))
                values.update(_checker_string_sequence_global(checker, element.value.id))
        return values

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    expanded = _checker_fstring_range_values(node.value)
                    if expanded:
                        local_sequences[target.id] = expanded
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and node.value is not None:
                expanded = _checker_fstring_range_values(node.value)
                if expanded:
                    local_sequences[node.target.id] = expanded

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            if any(isinstance(target, ast.Name) and target.id == "required" for target in node.targets):
                names.update(_literal_string_set(node.value))
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and node.target.id == "required" and node.value is not None:
                names.update(_literal_string_set(node.value))

    names.update(_checker_for_loop_fstring_values(tree))
    names.update(_checker_indexed_columns_from_source(tree))
    names.update(_checker_startswith_prefix_columns(tree))
    names.update(_checker_inline_required_sets(tree))
    return frozenset(name for name in names if name and name.lower() != "time") | (
        frozenset({"time"}) if "time" in names else frozenset()
    )


def _auto_row_checker_trace_contract(task_id: str) -> frozenset[str]:
    cached = _CHECKER_TRACE_CONTRACT_CACHE.get(task_id)
    if cached is not None:
        return cached
    checker = CHECKS.get(task_id)
    if checker is None:
        inferred = frozenset()
    else:
        inferred = _checker_required_set_from_source(checker)
    _CHECKER_TRACE_CONTRACT_CACHE[task_id] = inferred
    return inferred


def required_trace_contract_kind_for_checker(task_id: str) -> str:
    if not _trace_contracts_enabled():
        return "disabled"
    checker = STREAMING_BEHAVIOR_CHECKS.get(task_id)
    if checker is not None and _STREAMING_TRACE_REQUIREMENTS_BY_FUNC.get(checker):
        return "streaming"
    if _auto_row_checker_trace_contracts_enabled() and _auto_row_checker_trace_contract(task_id):
        return "row_required_set"
    return "none"


def required_trace_signals_for_checker(task_id: str) -> frozenset[str]:
    """Return the checker-observable signal contract used for sparse EVAS traces."""
    if not _trace_contracts_enabled():
        return frozenset()
    formal_utility_trace_signals = {
        "thermometer_to_binary_encoder_8b": frozenset({"time", "valid"})
        | frozenset({f"th{idx}" for idx in range(256)})
        | frozenset({f"b{idx}" for idx in range(8)}),
        "gray_to_binary_converter_8b": frozenset({"time"})
        | frozenset({f"g{idx}" for idx in range(8)})
        | frozenset({f"b{idx}" for idx in range(8)}),
        "binary_to_gray_converter_8b": frozenset({"time"})
        | frozenset({f"b{idx}" for idx in range(8)})
        | frozenset({f"g{idx}" for idx in range(8)}),
        "onehot_to_binary_encoder_16b": frozenset({"time", "valid"})
        | frozenset({f"oh{idx}" for idx in range(16)})
        | frozenset({f"b{idx}" for idx in range(4)}),
        "binary_to_onehot_decoder_16b": frozenset({"time", "en"})
        | frozenset({f"b{idx}" for idx in range(4)})
        | frozenset({f"oh{idx}" for idx in range(16)}),
        "decimal_digit_to_bcd_encoder": frozenset({"time", "valid"})
        | frozenset({f"d{idx}" for idx in range(10)})
        | frozenset({f"b{idx}" for idx in range(4)}),
        "signed_magnitude_to_twos_complement_8b": frozenset({"time", "sign"})
        | frozenset({f"mag{idx}" for idx in range(7)})
        | frozenset({f"y{idx}" for idx in range(8)}),
        "config_latch_32b_clocked": frozenset({"time", "en"})
        | frozenset({f"d{idx}" for idx in range(32)})
        | frozenset({f"q{idx}" for idx in range(32)}),
        "config_latch_128b_static_enable": frozenset({"time", "en"})
        | frozenset({f"d{idx}" for idx in range(128)})
        | frozenset({f"q{idx}" for idx in range(128)}),
        "config_shift_register_64b": frozenset({"time"})
        | frozenset({f"q{idx}" for idx in range(64)}),
        "bus_splitter_256_to_16x16": frozenset({"time"})
        | frozenset({f"in{idx}" for idx in range(256)})
        | frozenset({f"out{block}_{bit}" for block in range(16) for bit in range(16)}),
        "bus_combiner_16x16_to_256": frozenset({"time"})
        | frozenset({f"in{block}_{bit}" for block in range(16) for bit in range(16)})
        | frozenset({f"out{idx}" for idx in range(256)}),
        "masked_config_update_32b": frozenset({"time"})
        | frozenset({f"old{idx}" for idx in range(32)})
        | frozenset({f"new{idx}" for idx in range(32)})
        | frozenset({f"mask{idx}" for idx in range(32)})
        | frozenset({f"out{idx}" for idx in range(32)}),
        "edge_interval_tdc_8b": frozenset({"time", "start", "stop", "valid"})
        | frozenset({f"code{idx}" for idx in range(8)}),
        "period_meter_16b": frozenset({"time", "clk_in", "valid"})
        | frozenset({f"period{idx}" for idx in range(16)}),
        "duty_cycle_meter_8b": frozenset({"time", "clk_in", "valid"})
        | frozenset({f"duty{idx}" for idx in range(8)}),
        "event_counter_windowed_16b": frozenset({"time", "gate", "event", "done"})
        | frozenset({f"count{idx}" for idx in range(16)}),
        "ready_valid_latency_counter_12b": frozenset({"time", "clk", "valid_i", "ready_i", "done"})
        | frozenset({f"lat{idx}" for idx in range(12)}),
        "settling_window_detector": frozenset({"time", "vin", "target", "tol", "settled"})
        | frozenset({f"t_code{idx}" for idx in range(8)}),
        "reset_sync_active_low": frozenset({"time", "clk", "rst_n", "sync_rst_n"}),
        "reset_sync_active_high": frozenset({"time", "clk", "rst", "sync_rst"}),
        "enable_gated_clock_pulse": frozenset({"time", "clk", "en", "pulse"}),
        "low_active_enable_decoder_4b": frozenset({"time", "en_n"})
        | frozenset({f"a{idx}" for idx in range(4)})
        | frozenset({f"y{idx}_n" for idx in range(16)}),
        "configurable_polarity_edge_detector": frozenset({"time", "sig", "rise_en", "pulse"}),
        "prbs_generator_32b": frozenset({"time", "clk", "rst", "load_seed"})
        | frozenset({f"seed{idx}" for idx in range(32)})
        | frozenset({f"out{idx}" for idx in range(32)}),
        "multiphase_clock_generator_4ph": frozenset({"time", "clk0", "clk90", "clk180", "clk270"}),
        "configurable_pulse_train": frozenset({"time", "clk", "start", "pulse", "done"})
        | frozenset({f"period{idx}" for idx in range(4)})
        | frozenset({f"width{idx}" for idx in range(4)})
        | frozenset({f"count{idx}" for idx in range(4)}),
        "staircase_dac_stimulus_8b": frozenset({"time", "clk", "rst", "vout"})
        | frozenset({f"code{idx}" for idx in range(8)}),
        "deterministic_jittered_clock": frozenset({"time", "jitter_en", "clk_out"})
        | frozenset({f"seed{idx}" for idx in range(8)}),
    }
    formal_utility_trace_signals.update({
        "v3_064_edge_interval_tdc_8b": formal_utility_trace_signals["edge_interval_tdc_8b"],
        "v3_065_period_meter_16b": formal_utility_trace_signals["period_meter_16b"],
        "v3_066_duty_cycle_meter_8b": formal_utility_trace_signals["duty_cycle_meter_8b"],
        "v3_067_event_counter_windowed_16b": formal_utility_trace_signals["event_counter_windowed_16b"],
        "v3_068_latency_counter_ready_valid_12b": formal_utility_trace_signals["ready_valid_latency_counter_12b"],
        "v3_068_ready_valid_latency_counter_12b": formal_utility_trace_signals["ready_valid_latency_counter_12b"],
        "v3_069_settling_window_detector": formal_utility_trace_signals["settling_window_detector"],
        "v3_070_active_low_reset_synchronizer": formal_utility_trace_signals["reset_sync_active_low"],
        "v3_071_active_high_reset_synchronizer": formal_utility_trace_signals["reset_sync_active_high"],
        "v3_072_enable_gated_clock_pulse": formal_utility_trace_signals["enable_gated_clock_pulse"],
        "v3_073_low_active_enable_decoder_4b": formal_utility_trace_signals["low_active_enable_decoder_4b"],
        "v3_074_configurable_polarity_edge_detector": formal_utility_trace_signals["configurable_polarity_edge_detector"],
        "v3_075_prbs_generator_32b_seeded": formal_utility_trace_signals["prbs_generator_32b"],
        "v3_076_multiphase_clock_generator_4ph": formal_utility_trace_signals["multiphase_clock_generator_4ph"],
        "v3_077_configurable_pulse_train_generator": formal_utility_trace_signals["configurable_pulse_train"],
        "v3_078_staircase_dac_stimulus_8b": formal_utility_trace_signals["staircase_dac_stimulus_8b"],
        "v3_079_jittered_clock_source_deterministic": formal_utility_trace_signals["deterministic_jittered_clock"],
    })
    if task_id in formal_utility_trace_signals:
        return formal_utility_trace_signals[task_id] | _extra_trace_signals_for_checker(task_id)
    if task_id in {"bin_to_thermometer_decoder_8b", "v3_050_bin_to_thermometer_decoder_8b"}:
        return (
            frozenset({"time", "en"})
            | frozenset({f"b{idx}" for idx in range(8)})
            | frozenset({f"th{idx}" for idx in range(256)})
            | _extra_trace_signals_for_checker(task_id)
        )
    signals: frozenset[str] = frozenset()
    checker = STREAMING_BEHAVIOR_CHECKS.get(task_id)
    if checker is not None:
        signals = _STREAMING_TRACE_REQUIREMENTS_BY_FUNC.get(checker, frozenset())
        if signals:
            return signals | _extra_trace_signals_for_checker(task_id)
    if _auto_row_checker_trace_contracts_enabled():
        signals = _auto_row_checker_trace_contract(task_id)
    if signals:
        return signals | _extra_trace_signals_for_checker(task_id)
    return signals


def _env_enabled(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _streaming_notes_require_row_fallback(notes: list[str]) -> bool:
    """Avoid turning observable/interface mismatches into behavior failures."""
    fallback_prefixes = (
        "missing ",
        "expected ",
    )
    return any(note.startswith(fallback_prefixes) for note in notes)


def evaluate_streaming_behavior(task_id: str, csv_path: Path) -> tuple[float, list[str]] | None:
    force_streaming = _env_enabled("VAEVAS_ENABLE_EXPERIMENTAL_STREAMING_CHECKERS")
    if not force_streaming:
        if _env_enabled("VAEVAS_DISABLE_VALIDATED_FAST_CHECKERS"):
            return None
        if task_id not in VALIDATED_FAST_CHECKER_TASKS:
            return None

    checker = STREAMING_BEHAVIOR_CHECKS.get(task_id)
    if checker is None:
        return None
    score, notes = checker(csv_path)
    if not force_streaming and _streaming_notes_require_row_fallback(notes):
        return None
    return score, [f"streaming_checker:{note}" for note in notes]


def behavior_checker_policy(task_id: str, notes: list[str] | None = None) -> dict[str, object]:
    """Describe the checker implementation used for artifact-level timing claims."""
    notes = notes or []
    streaming_registered = task_id in STREAMING_BEHAVIOR_CHECKS
    streaming_validated = task_id in VALIDATED_FAST_CHECKER_TASKS
    streaming_used = any(note.startswith("streaming_checker:") for note in notes)
    trace_contract_kind = required_trace_contract_kind_for_checker(task_id)
    trace_contract_signals = required_trace_signals_for_checker(task_id)
    extra_trace_signals = _extra_trace_signals_for_checker(task_id) if trace_contract_signals else frozenset()
    forced = _env_enabled("VAEVAS_ENABLE_EXPERIMENTAL_STREAMING_CHECKERS")
    disabled = _env_enabled("VAEVAS_DISABLE_VALIDATED_FAST_CHECKERS")
    if task_id not in CHECKS:
        implementation = "no_checker"
    elif streaming_used:
        implementation = "streaming_validated" if streaming_validated else "streaming_experimental"
    elif disabled and streaming_registered:
        implementation = "row_based_streaming_disabled"
    elif streaming_validated:
        implementation = "row_based_fallback_from_streaming"
    elif task_id in {"noise_gen", "noise_gen_smoke"}:
        implementation = "custom_noise"
    else:
        implementation = "row_based"
    return {
        "checker_id": task_id,
        "implementation": implementation,
        "streaming_registered": streaming_registered,
        "streaming_validated": streaming_validated,
        "streaming_used": streaming_used,
        "streaming_forced": forced,
        "streaming_disabled": disabled,
        "trace_contract_kind": trace_contract_kind,
        "trace_contract_signal_count": len(trace_contract_signals - {"time"}),
        "extra_trace_signal_count": len(extra_trace_signals - {"time"}),
    }


def rising_edges(values: list[float], times: list[float], threshold: float = 0.45) -> list[float]:
    edges: list[float] = []
    for i in range(1, len(values)):
        if values[i - 1] < threshold <= values[i]:
            edges.append(times[i])
    return edges


def sample_rows_at_or_after_times(
    rows: list[dict[str, float]],
    target_times: list[float],
    *,
    rst_key: str | None = None,
    rst_threshold: float = 0.45,
) -> list[dict[str, float]]:
    """Return rows whose time is the first sample at/after each target time.

    This function is linear in len(rows) + len(target_times). It replaces
    repeated per-target full scans that become O(n^2) on large tran.csv files.
    """
    if not rows or not target_times:
        return []

    sampled: list[dict[str, float]] = []
    row_idx = 0
    n_rows = len(rows)
    for t in target_times:
        while row_idx < n_rows and rows[row_idx]["time"] < t:
            row_idx += 1
        if row_idx >= n_rows:
            break
        row = rows[row_idx]
        if rst_key is None or row.get(rst_key, 0.0) > rst_threshold:
            sampled.append(row)
    return sampled


def decode_bus(rows: list[dict[str, float]], bit_names: list[str], threshold: float = 0.45) -> list[int]:
    decoded: list[int] = []
    for row in rows:
        code = 0
        for bit_name in bit_names:
            bit = 1 if row[bit_name] >= threshold else 0
            m = re.search(r"(\d+)$", bit_name)
            if m is None:
                warnings.warn(
                    f"decode_bus: bit_name {bit_name!r} has no trailing digit; "
                    "defaulting to bit index 0, result may be incorrect",
                    stacklevel=2,
                )
            idx = int(m.group(1)) if m else 0
            code |= bit << idx
        decoded.append(code)
    return decoded


def indexed_columns(keys: set[str], prefix: str) -> list[str]:
    cols = [k for k in keys if re.fullmatch(rf"{re.escape(prefix)}\d+", k)]
    return sorted(cols, key=lambda name: int(re.search(r"(\d+)$", name).group(1)))


def _canonical_signal_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", name.lower())


_INDEXED_ALIAS_TARGETS = tuple(
    target
    for idx in range(16)
    for target in (
        f"dout_{idx}",
        f"dout{idx}",
        f"din_{idx}",
        f"din{idx}",
        f"ptr_{idx}",
        f"cell_en_{idx}",
        f"g{idx}",
        f"state_{idx}",
        f"div_code_{idx}",
    )
)

_SCALAR_ALIAS_TARGETS = (
    "vin",
    "vout",
    "vin_sh",
    "rst_n",
    "clk",
    "clk_in",
    "clk_out",
    "lock",
    "ref_clk",
    "fb_clk",
    "vctrl_mon",
    "vinp",
    "vinn",
    "out_p",
    "out_n",
    "outp",
    "outn",
    "a",
    "b",
    "y",
    "d",
    "q",
    "qb",
    "rst",
    "ref",
    "div",
    "up",
    "dn",
    "serial_out",
    "dpn",
    "rstb",
    "en",
    "phase_out",
    "guard_out",
    "delay_out",
    "seen_out",
    "first_err_out",
    "max_err_out",
    "count_out",
    "metric_out",
    "mode",
    "out",
    "vin_i",
    "vout_o",
)


def _signal_alias_candidates(raw_key: str) -> set[str]:
    key = raw_key.strip()
    if not key:
        return set()

    candidates = {key, key.lower()}
    for sep in (":", "."):
        if sep in key:
            tail = key.split(sep)[-1]
            candidates.add(tail)
            candidates.add(tail.lower())

    vm = re.match(r"(?i)^v\(\s*([^)]+)\s*\)$", key)
    if vm:
        inner = vm.group(1).strip()
        candidates.add(inner)
        candidates.add(inner.lower())

    for cand in list(candidates):
        cm = re.match(r"^([A-Za-z_][A-Za-z0-9_$]*)\[(\d+)\]$", cand)
        if cm:
            root = cm.group(1)
            idx = cm.group(2)
            candidates.update(
                {
                    f"{root}_{idx}",
                    f"{root}{idx}",
                    f"{root.lower()}_{idx}",
                    f"{root.lower()}{idx}",
                }
            )
            # Common generated DWA/vector port names use direction suffixes
            # (`ptr_o[0]`, `cell_en_o[0]`, `code_i[0]`). The checkers use
            # scalar observable names (`ptr_0`, `cell_en_0`, `code_0`).
            stripped_root = root.lower()
            for suffix in ("_msb_i", "_lsb_i", "_o", "_i"):
                if stripped_root.endswith(suffix):
                    stripped_root = stripped_root[: -len(suffix)]
                    break
            if stripped_root in {"ptr", "cell_en", "code"}:
                candidates.update(
                    {
                        f"{stripped_root}_{idx}",
                        f"{stripped_root}{idx}",
                    }
                )

        dm = re.search(r"(dout|din|div_code|cell_en|ptr|state|code|bin_o|g|d)_?(\d+)$", cand.lower())
        if dm:
            root = dm.group(1)
            idx = dm.group(2)
            candidates.update(
                {
                    f"{root}_{idx}",
                    f"{root}{idx}",
                }
            )
            if root == "d":
                candidates.update({f"dout_{idx}", f"dout{idx}"})

    return candidates


def _add_canonical_alias_targets(alias_to_index: dict[str, int]) -> None:
    canonical_to_index: dict[str, int] = {}
    for alias, index in alias_to_index.items():
        canonical_to_index.setdefault(_canonical_signal_name(alias), index)
    for target in _INDEXED_ALIAS_TARGETS + _SCALAR_ALIAS_TARGETS:
        ckey = _canonical_signal_name(target)
        if target not in alias_to_index and ckey in canonical_to_index:
            alias_to_index[target] = canonical_to_index[ckey]


class CsvCheckerRuntime:
    """Header-indexed CSV access shared by validated streaming checkers."""

    def __init__(self, csv_path: Path) -> None:
        self.csv_path = csv_path
        self.header, self.index = self._load_header_index(csv_path)

    @staticmethod
    def _load_header_index(csv_path: Path) -> tuple[list[str], dict[str, int]]:
        with csv_path.open(newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, [])
        alias_to_index: dict[str, int] = {}
        for idx, name in enumerate(header):
            for alias in _signal_alias_candidates(name):
                alias_to_index.setdefault(alias, idx)
        _add_canonical_alias_targets(alias_to_index)
        return header, alias_to_index

    def missing(self, required: Iterable[str]) -> list[str]:
        return sorted(name for name in required if name not in self.index)

    def rows(self):
        with self.csv_path.open(newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)
            yield from reader

    def require(self, required: Iterable[str]) -> tuple[bool, list[str]]:
        missing = self.missing(required)
        return not missing, missing

    def float(self, row: list[str], key: str, default: float = 0.0) -> float:
        idx = self.index.get(key)
        if idx is None:
            return default
        return _float_at(row, idx, default)

    def value_tuple(self, row: list[str], keys: Iterable[str]) -> tuple[float, ...]:
        return tuple(self.float(row, key) for key in keys)

    def mean_windows(
        self,
        windows: dict[str, tuple[float, float, str]],
    ) -> tuple[dict[str, float], list[str]]:
        accum = {label: [0.0, 0] for label in windows}
        required = {"time"} | {signal for _, _, signal in windows.values()}
        missing = self.missing(required)
        if missing:
            return {}, missing
        for row in self.rows():
            time_s = self.float(row, "time")
            for label, (start, stop, signal) in windows.items():
                if start <= time_s <= stop:
                    bucket = accum[label]
                    bucket[0] += self.float(row, signal)
                    bucket[1] += 1
        means: dict[str, float] = {}
        empty: list[str] = []
        for label, (total, count) in accum.items():
            if count:
                means[label] = total / count
            else:
                empty.append(label)
        return means, empty

    def series(self, signals: Iterable[str]) -> tuple[dict[str, list[float]], list[str]]:
        required = {"time"} | set(signals)
        missing = self.missing(required)
        if missing:
            return {}, missing
        data = {signal: [] for signal in required}
        for row in self.rows():
            for signal in required:
                data[signal].append(self.float(row, signal))
        return data, []

    @staticmethod
    def interpolate_series(times: list[float], values: list[float], target: float) -> float | None:
        if not times or len(times) != len(values):
            return None
        if target < times[0] or target > times[-1]:
            return None
        if target == times[0]:
            return values[0]
        lo = 0
        hi = len(times) - 1
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if times[mid] <= target:
                lo = mid
            else:
                hi = mid
        t0 = times[lo]
        t1 = times[hi]
        if t1 <= t0:
            return values[hi]
        alpha = (target - t0) / (t1 - t0)
        return values[lo] + alpha * (values[hi] - values[lo])

    def samples_at(
        self,
        signal: str,
        target_times: Iterable[float],
    ) -> dict[float, float | None]:
        data, missing = self.series({signal})
        targets = list(target_times)
        if missing:
            return {target: None for target in targets}
        times = data["time"]
        values = data[signal]
        return {
            target: self.interpolate_series(times, values, target)
            for target in targets
        }

    def resampled_rows(
        self,
        signals: Iterable[str],
        *,
        sample_count: int,
    ) -> tuple[list[dict[str, float]], list[str]]:
        data, missing = self.series(signals)
        if missing:
            return [], missing
        times = data["time"]
        if len(times) < 2 or sample_count < 2:
            return [], ["invalid_time_range"]
        t0 = times[0]
        t1 = times[-1]
        if t1 <= t0:
            return [], ["invalid_time_range"]
        signal_list = list(signals)
        rows: list[dict[str, float]] = []
        for idx in range(sample_count):
            target = t0 + (t1 - t0) * idx / (sample_count - 1)
            out = {"time": target}
            for signal in signal_list:
                value = self.interpolate_series(times, data[signal], target)
                if value is None:
                    return [], [f"missing_resample_{signal}"]
                out[signal] = value
            rows.append(out)
        return rows, []


def _set_alias_if_missing(row: dict[str, float], alias: str, value: float) -> None:
    if alias and alias not in row:
        row[alias] = value


def _expanded_row_aliases(row: dict[str, float]) -> dict[str, float]:
    expanded = dict(row)
    for raw_key, value in list(row.items()):
        for alias in _signal_alias_candidates(raw_key):
            _set_alias_if_missing(expanded, alias, value)

    canonical_map: dict[str, str] = {}
    for key in expanded:
        canonical_map.setdefault(_canonical_signal_name(key), key)

    for target in _INDEXED_ALIAS_TARGETS + _SCALAR_ALIAS_TARGETS:
        ckey = _canonical_signal_name(target)
        if target not in expanded and ckey in canonical_map:
            expanded[target] = expanded[canonical_map[ckey]]

    return expanded


_TASK_ALIAS_CANDIDATES: dict[str, dict[str, tuple[str, ...]]] = {
    "digital_basics_smoke": {
        "a": ("not_a",),
        "y": ("not_y",),
    },
    "and_gate_smoke": {
        "a": ("and_a",),
        "b": ("and_b",),
        "y": ("and_y",),
    },
    "or_gate_smoke": {
        "a": ("or_a",),
        "b": ("or_b",),
        "y": ("or_y",),
    },
    "dff_rst_smoke": {
        "d": ("dff_d",),
        "clk": ("dff_clk",),
        "rst": ("dff_rst",),
        "q": ("dff_q",),
        "qb": ("dff_qb",),
    },
    "dwa_ptr_gen_no_overlap_smoke": {
        "clk_i": ("clk",),
        "rst_ni": ("rst_n",),
    },
    "dwa_wraparound_smoke": {
        "clk_i": ("clk",),
        "rst_ni": ("rst_n",),
        "code_0": ("code0",),
        "code_1": ("code1",),
        "code_2": ("code2",),
        "code_3": ("code3",),
    },
    "noise_gen_smoke": {
        "vin_i": ("vin",),
        "vout_o": ("vout",),
    },
    "sar_adc_dac_weighted_8b_smoke": {
        "vin_sh": ("vin",),
    },
}


def normalize_rows_for_task(task_id: str, rows: list[dict[str, float]]) -> list[dict[str, float]]:
    if not rows:
        return rows
    normalized = [_expanded_row_aliases(row) for row in rows]
    alias_rules = _TASK_ALIAS_CANDIDATES.get(task_id, {})
    if not alias_rules:
        return normalized
    for row in normalized:
        for target, candidates in alias_rules.items():
            if target in row:
                continue
            for cand in candidates:
                if cand in row:
                    row[target] = row[cand]
                    break
    return normalized


def check_clk_div(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows or "clk_in" not in rows[0] or "clk_out" not in rows[0]:
        return False, "missing clk_in/clk_out"
    times = [r["time"] for r in rows]
    in_edges = rising_edges([r["clk_in"] for r in rows], times)
    out_edges = rising_edges([r["clk_out"] for r in rows], times)
    if len(in_edges) < 8 or len(out_edges) < 2:
        return False, "not enough clock edges"
    ratio = len(in_edges) / max(len(out_edges), 1)
    return (3.0 <= ratio <= 5.0), f"edge_ratio={ratio:.2f}"


def check_clk_divider(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows or not {"clk_in", "clk_out", "lock"}.issubset(rows[0]):
        return False, "missing clk_in/clk_out/lock"

    sample = rows[0]
    div_cols: list[str] = []
    for idx in range(8):
        col = None
        for candidate in (f"div_code_{idx}", f"div_code[{idx}]"):
            if candidate in sample:
                col = candidate
                break
        if col is None:
            return False, "missing div_code_*"
        div_cols.append(col)

    ratio = 0
    for idx, col in enumerate(div_cols):
        if sample[col] > 0.45:
            ratio |= (1 << idx)
    if ratio < 1:
        ratio = 1

    times = [r["time"] for r in rows]
    clk_vals = [r["clk_in"] for r in rows]
    out_vals = [r["clk_out"] for r in rows]
    lock_vals = [r["lock"] for r in rows]

    in_edges = rising_edges(clk_vals, times)
    out_edges = rising_edges(out_vals, times)
    lock_edges = rising_edges(lock_vals, times)
    final_lock_high = lock_vals[-1] > 0.45

    if len(in_edges) < 8 or len(out_edges) < 2:
        return False, "not enough clock edges"

    if ratio == 1:
        level_match = sum(1 for ci, co in zip(clk_vals, out_vals) if ((ci > 0.45) == (co > 0.45))) / max(len(rows), 1)
        edge_ratio = len(in_edges) / max(len(out_edges), 1)
        ok = level_match > 0.98 and 0.95 <= edge_ratio <= 1.05 and final_lock_high
        return ok, f"ratio_code=1 in_edges={len(in_edges)} out_edges={len(out_edges)} lock_edges={len(lock_edges)} final_lock_high={final_lock_high} level_match={level_match:.3f} edge_ratio={edge_ratio:.3f}"

    if len(in_edges) < max(12, ratio * 2) or len(out_edges) < 3:
        return False, "not enough clock edges"

    intervals: list[int] = []
    for idx in range(1, len(out_edges)):
        start_t = out_edges[idx - 1]
        end_t = out_edges[idx]
        in_count = sum(1 for t in in_edges if start_t < t <= end_t)
        intervals.append(in_count)

    if len(intervals) < 2:
        return False, "insufficient output periods"

    measured = intervals[1:] if len(intervals) > 2 else intervals
    mismatch = [n for n in measured if n != ratio]
    period_match = 1.0 - (len(mismatch) / len(measured))

    hist: dict[int, int] = {}
    for n in measured:
        hist[n] = hist.get(n, 0) + 1

    high_seen = any(v > 0.45 for v in out_vals)
    low_seen = any(v <= 0.45 for v in out_vals)

    ok = (len(mismatch) == 0) and final_lock_high and high_seen and low_seen
    return ok, f"ratio_code={ratio} in_edges={len(in_edges)} out_edges={len(out_edges)} lock_edges={len(lock_edges)} final_lock_high={final_lock_high} period_match={period_match:.3f} interval_hist={hist}"


def check_comparator(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows or not {"vinp", "vinn", "out_p"}.issubset(rows[0]):
        return False, "missing vinp/vinn/out_p"
    out_vals = [r["out_p"] for r in rows]
    out_lo = min(out_vals)
    out_hi = max(out_vals)
    span = out_hi - out_lo
    if span < 0.3:
        return False, f"output_span_too_small={span:.3f}"
    vth = out_lo + 0.5 * span
    margin = 20e-3
    high_rows = [r for r in rows if r["vinp"] > r["vinn"] + margin]
    low_rows = [r for r in rows if r["vinn"] > r["vinp"] + margin]
    if not high_rows or not low_rows:
        return False, "insufficient_positive_negative_input_windows"
    high_frac = sum(1 for r in high_rows if r["out_p"] > vth) / len(high_rows)
    low_frac = sum(1 for r in low_rows if r["out_p"] < vth) / len(low_rows)
    ok = high_frac > 0.80 and low_frac > 0.80
    return ok, f"high_frac={high_frac:.3f} low_frac={low_frac:.3f} span={span:.3f}"


def _threshold_crossings(
    values: list[float],
    times: list[float],
    *,
    threshold: float = 0.0,
    direction: str,
) -> list[float]:
    edges: list[float] = []
    for idx in range(1, len(values)):
        v0 = values[idx - 1]
        v1 = values[idx]
        if direction == "rising":
            hit = v0 <= threshold < v1
        elif direction == "falling":
            hit = v0 >= threshold > v1
        else:
            raise ValueError(f"unsupported direction={direction!r}")
        if not hit:
            continue
        t0 = times[idx - 1]
        t1 = times[idx]
        if v1 == v0:
            edges.append(t1)
        else:
            alpha = (threshold - v0) / (v1 - v0)
            edges.append(t0 + alpha * (t1 - t0))
    return edges


def _logic_state(value: float, threshold: float = 0.45) -> str:
    return "H" if value > threshold else "L"


def _differential_output_state(out_p: float, out_n: float, threshold: float = 0.45) -> str:
    if out_p > threshold and out_n < threshold:
        return "P"
    if out_p < threshold and out_n > threshold:
        return "N"
    if out_p < threshold and out_n < threshold:
        return "Z"
    return "X"


def _conditional_time_fraction(
    rows: list[dict[str, float]],
    region_predicate,
    pass_predicate,
) -> float:
    """Time-weighted pass fraction for sparse or adaptive transient samples."""
    total_dt = 0.0
    pass_dt = 0.0
    for prev, cur in zip(rows, rows[1:]):
        dt = cur["time"] - prev["time"]
        if dt <= 0.0:
            continue
        if not region_predicate(prev):
            continue
        total_dt += dt
        if pass_predicate(prev):
            pass_dt += dt
    if total_dt <= 0.0:
        return 0.0
    return pass_dt / total_dt


def check_release_threshold_comparator(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vinp", "vinn", "out_p"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/vinp/vinn/out_p"

    times = [r["time"] for r in rows]
    diff = [r["vinp"] - r["vinn"] for r in rows]
    out_vals = [r["out_p"] for r in rows]
    out_lo = min(out_vals)
    out_hi = max(out_vals)
    span = out_hi - out_lo
    if span < 0.60:
        return False, f"output_span_too_small={span:.3f}"

    vth = out_lo + 0.5 * span
    margin = 20e-3
    high_rows = [r for r in rows if r["vinp"] - r["vinn"] >= margin]
    low_rows = [r for r in rows if r["vinn"] - r["vinp"] >= margin]
    if len(high_rows) < 5 or len(low_rows) < 5:
        return False, "insufficient_positive_negative_input_windows"

    high_frac = _conditional_time_fraction(
        rows,
        lambda r: r["vinp"] - r["vinn"] >= margin,
        lambda r: r["out_p"] > vth,
    )
    low_frac = _conditional_time_fraction(
        rows,
        lambda r: r["vinn"] - r["vinp"] >= margin,
        lambda r: r["out_p"] < vth,
    )

    diff_rises = _threshold_crossings(diff, times, threshold=0.0, direction="rising")
    diff_falls = _threshold_crossings(diff, times, threshold=0.0, direction="falling")
    out_rises = _threshold_crossings(out_vals, times, threshold=vth, direction="rising")
    out_falls = _threshold_crossings(out_vals, times, threshold=vth, direction="falling")
    if not diff_rises or not diff_falls:
        return False, "missing_rising_or_falling_input_crossing"
    if not out_rises or not out_falls:
        return False, "missing_rising_or_falling_output_transition"

    settle_s = 2.0e-9
    rising_aligned = any(abs(ot - dt) <= settle_s for dt in diff_rises for ot in out_rises)
    falling_aligned = any(abs(ot - dt) <= settle_s for dt in diff_falls for ot in out_falls)
    ok = high_frac > 0.90 and low_frac > 0.90 and rising_aligned and falling_aligned
    return ok, (
        f"high_frac={high_frac:.3f} low_frac={low_frac:.3f} span={span:.3f} "
        f"diff_rises={len(diff_rises)} diff_falls={len(diff_falls)} "
        f"out_rises={len(out_rises)} out_falls={len(out_falls)} "
        f"rising_aligned={rising_aligned} falling_aligned={falling_aligned}"
    )


def check_release_offset_comparator(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "vinp", "vinn", "out_p"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/clk/vinp/vinn/out_p"

    times = [r["time"] for r in rows]
    clk_vals = [r["clk"] for r in rows]
    out_vals = [r["out_p"] for r in rows]
    out_span = max(out_vals) - min(out_vals)
    if out_span < 0.60:
        return False, f"output_span_too_small={out_span:.3f}"

    edge_times = rising_edges(clk_vals, times, threshold=0.45)
    if len(edge_times) < 7:
        return False, f"too_few_clock_edges={len(edge_times)}"

    vos = 5e-3
    sample_delay = 0.50e-9
    expected: list[str] = []
    observed: list[str] = []
    diffs_mv: list[float] = []
    mismatches = 0
    for edge_t in edge_times[:7]:
        sample_t = edge_t + sample_delay
        vinp = sample_signal_at(rows, "vinp", edge_t)
        vinn = sample_signal_at(rows, "vinn", edge_t)
        out_p = sample_signal_at(rows, "out_p", sample_t)
        if vinp is None or vinn is None or out_p is None:
            return False, f"missing_sample_near_edge={edge_t * 1e9:.2f}ns"
        diff_v = vinp - vinn
        diffs_mv.append(diff_v * 1e3)
        want = "H" if diff_v > vos else "L"
        got = _logic_state(out_p)
        expected.append(want)
        observed.append(got)
        if got != want:
            mismatches += 1

    sequence = "".join(observed)
    expected_sequence = "".join(expected)
    has_below_offset_positive = any(0.0 <= mv < vos * 1e3 for mv, want in zip(diffs_mv, expected) if want == "L")
    has_above_offset_positive = any(mv > vos * 1e3 for mv, want in zip(diffs_mv, expected) if want == "H")
    has_negative_low = any(mv < -1.0 for mv, want in zip(diffs_mv, expected) if want == "L")
    ok = (
        mismatches == 0
        and sequence == "LLLHHLL"
        and has_below_offset_positive
        and has_above_offset_positive
        and has_negative_low
    )
    diff_text = ",".join(f"{mv:.1f}" for mv in diffs_mv)
    return ok, (
        f"offset_decisions={sequence} expected={expected_sequence} "
        f"diffs_mv=[{diff_text}] mismatches={mismatches} "
        f"below_offset_positive={has_below_offset_positive} "
        f"above_offset_positive={has_above_offset_positive}"
    )


def check_v3_009_lock_detector(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "ref_clk", "fb_clk", "rst_n", "lock"}
    if not rows or not required.issubset(rows[0]):
        missing = sorted(required - set(rows[0].keys())) if rows else sorted(required)
        return False, "missing_columns=" + ",".join(missing)

    times = [r["time"] for r in rows]
    ref_edges = rising_edges([r["ref_clk"] for r in rows], times, threshold=0.45)
    fb_edges = rising_edges([r["fb_clk"] for r in rows], times, threshold=0.45)
    if len(ref_edges) < 8 or len(fb_edges) < 8:
        return False, f"too_few_edges ref={len(ref_edges)} fb={len(fb_edges)}"

    events: list[tuple[float, bool, bool]] = []
    for ref_t in ref_edges:
        rst = sample_signal_at(rows, "rst_n", ref_t)
        if rst is None or rst <= 0.45:
            continue
        nearest_fb = min((abs(fb_t - ref_t) for fb_t in fb_edges), default=1.0)
        aligned = nearest_fb <= 2.0e-9
        lock_after = sample_signal_at(rows, "lock", ref_t + 0.8e-9)
        events.append((ref_t, aligned, bool(lock_after is not None and lock_after > 0.45)))

    streak = 0
    good_lock_after_three = 0
    early_locks = 0
    mismatch_clears = 0
    mismatch_failures = 0
    for ref_t, aligned, lock_high in events:
        if aligned:
            streak += 1
            if streak >= 3 and lock_high:
                good_lock_after_three += 1
            if streak < 3 and lock_high:
                early_locks += 1
        else:
            if lock_high:
                mismatch_failures += 1
            else:
                mismatch_clears += 1
            streak = 0

    reset_sample_times = (1e-9, 58e-9, 59e-9, 95e-9, 99e-9, 102e-9)
    reset_samples = [sample_signal_at(rows, "lock", t) for t in reset_sample_times]
    reset_low = all(value is not None and value < 0.45 for value in reset_samples)
    final_lock = sample_signal_at(rows, "lock", max(times) - 1e-9)
    final_lock_low = final_lock is not None and final_lock < 0.45

    ok = (
        reset_low
        and early_locks == 0
        and mismatch_failures == 0
        and mismatch_clears >= 1
        and good_lock_after_three >= 2
        and final_lock_low
    )
    aligned_count = sum(1 for _, aligned, _ in events if aligned)
    mismatch_count = sum(1 for _, aligned, _ in events if not aligned)
    return ok, (
        f"events={len(events)} aligned={aligned_count} mismatch={mismatch_count} "
        f"good_lock_after_three={good_lock_after_three} early_locks={early_locks} "
        f"mismatch_clears={mismatch_clears} mismatch_failures={mismatch_failures} "
        f"reset_low={reset_low} final_lock_low={final_lock_low}"
    )


def check_v3_gain_trim_controller(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "gain_ctrl"}
    if not rows or not required.issubset(rows[0]):
        missing = sorted(required - set(rows[0].keys())) if rows else sorted(required)
        return False, "missing_columns=" + ",".join(missing)

    sample_times_ns = [20.0, 70.0, 150.0, 250.0, 290.0, 330.0, 470.0, 590.0, 650.0]
    samples: list[float] = []
    for t_ns in sample_times_ns:
        value = sample_signal_at(rows, "gain_ctrl", t_ns * 1e-9)
        if value is None:
            return False, f"missing_sample_at={t_ns:g}ns"
        samples.append(value)

    reset_nominal = abs(samples[0] - 0.30) <= 0.04
    low_meas_increases = samples[0] < samples[1] < samples[2] < samples[3]
    reaches_upper_clamp = 0.83 <= samples[3] <= 0.86
    deadband_holds = abs(samples[4] - samples[3]) <= 0.035
    high_meas_decreases = samples[4] > samples[5] > samples[6] > samples[7] - 0.02
    reaches_lower_clamp = 0.04 <= samples[8] <= 0.07
    in_range = all(0.04 <= value <= 0.86 for value in samples)
    ok = (
        reset_nominal
        and low_meas_increases
        and reaches_upper_clamp
        and deadband_holds
        and high_meas_decreases
        and reaches_lower_clamp
        and in_range
    )
    values = ",".join(f"{value:.3f}" for value in samples)
    return ok, (
        f"gain_trim_samples={values} reset_nominal={reset_nominal} "
        f"low_meas_increases={low_meas_increases} reaches_upper_clamp={reaches_upper_clamp} "
        f"deadband_holds={deadband_holds} high_meas_decreases={high_meas_decreases} "
        f"reaches_lower_clamp={reaches_lower_clamp} in_range={in_range}"
    )


def check_v3_offset_comparator(rows: list[dict[str, float]]) -> tuple[bool, str]:
    base_ok, base_msg = check_release_offset_comparator(rows)
    if not base_ok:
        return False, base_msg

    sample_plan = [
        (1.35e-9, "L", "edge_neg_10mv"),
        (5.35e-9, "L", "edge_zero_mv"),
        (9.35e-9, "L", "edge_pos_3mv"),
        (12.60e-9, "L", "async_hold_before_pos_7mv_edge"),
        (13.35e-9, "H", "edge_pos_7mv"),
        (17.35e-9, "H", "edge_pos_20mv"),
        (20.60e-9, "H", "async_hold_before_zero_edge"),
        (21.35e-9, "L", "edge_zero_again"),
        (24.60e-9, "L", "async_hold_before_neg_10mv_edge"),
        (25.35e-9, "L", "edge_neg_10mv_again"),
    ]
    failures: list[str] = []
    observed: list[str] = []
    for time_s, expected, label in sample_plan:
        value = sample_signal_at(rows, "out_p", time_s)
        if value is None:
            failures.append(f"{label}=missing")
            observed.append("?")
            continue
        state = _logic_state(value)
        observed.append(state)
        if state != expected:
            failures.append(f"{label}:{state}!={expected}@{value:.3f}")
        if expected == "H" and value < 0.81:
            failures.append(f"{label}:high_not_rail={value:.3f}")
        if expected == "L" and value > 0.09:
            failures.append(f"{label}:low_not_rail={value:.3f}")

    ok = not failures
    return ok, base_msg + " strict_samples=" + "".join(observed) + (" " + " ".join(failures) if failures else "")


def check_release_strongarm_latch_comparator(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "vinp", "vinn", "out_p", "out_n"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/clk/vinp/vinn/out_p/out_n"

    out_p_vals = [r["out_p"] for r in rows]
    out_n_vals = [r["out_n"] for r in rows]
    out_p_span = max(out_p_vals) - min(out_p_vals)
    out_n_span = max(out_n_vals) - min(out_n_vals)
    if out_p_span < 0.60 or out_n_span < 0.60:
        return False, f"insufficient_toggle out_p_span={out_p_span:.3f} out_n_span={out_n_span:.3f}"

    sample_plan = [
        ("p_decision", 0.66e-9, "P", "positive"),
        ("p_hold_after_input_swap", 0.88e-9, "P", "negative"),
        ("reset_after_p", 1.12e-9, "Z", "negative"),
        ("n_decision", 1.66e-9, "N", "negative"),
        ("n_hold_after_input_swap", 1.88e-9, "N", "positive"),
        ("reset_after_n", 2.12e-9, "Z", "positive"),
        ("second_p_decision", 2.70e-9, "P", "positive"),
        ("second_n_decision", 3.70e-9, "N", "negative"),
    ]

    states: list[str] = []
    diff_signs: list[str] = []
    mismatches: list[str] = []
    for label, sample_t, expected_state, expected_diff_sign in sample_plan:
        out_p = sample_signal_at(rows, "out_p", sample_t)
        out_n = sample_signal_at(rows, "out_n", sample_t)
        vinp = sample_signal_at(rows, "vinp", sample_t)
        vinn = sample_signal_at(rows, "vinn", sample_t)
        if out_p is None or out_n is None or vinp is None or vinn is None:
            return False, f"missing_sample:{label}"
        state = _differential_output_state(out_p, out_n)
        diff = vinp - vinn
        diff_sign = "positive" if diff > 0.2e-3 else ("negative" if diff < -0.2e-3 else "near_zero")
        states.append(state)
        diff_signs.append(diff_sign)
        if state != expected_state or diff_sign != expected_diff_sign:
            mismatches.append(f"{label}:{state}/{diff_sign}")

    ok = not mismatches
    return ok, (
        f"latch_states={''.join(states)} expected=PPZNNZPN "
        f"diff_signs={','.join(diff_signs)} mismatches={';'.join(mismatches) or 'none'}"
    )


def _sample_vector_at(times: list[float], values: list[float], time_s: float) -> float | None:
    if not times or not values or len(times) != len(values):
        return None
    first_time = times[0]
    last_time = times[-1]
    if time_s < first_time or time_s > last_time:
        return None
    if time_s == first_time:
        return values[0]
    for idx in range(1, len(times)):
        t0 = times[idx - 1]
        t1 = times[idx]
        if t0 <= time_s <= t1:
            if t1 == t0:
                return values[idx]
            alpha = (time_s - t0) / (t1 - t0)
            return values[idx - 1] + alpha * (values[idx] - values[idx - 1])
    return None


def _check_cmp_delay_vectors(times: list[float], out_p: list[float]) -> tuple[bool, str]:
    phases = [
        (0.0e-9, 4.0e-9, 10e-3),
        (4.0e-9, 8.0e-9, 1e-3),
        (8.0e-9, 12.0e-9, 0.1e-3),
        (12.0e-9, 16.0e-9, 0.01e-3),
    ]
    threshold = 0.45
    clk_rise_offset = 0.1e-9

    delays_ns: list[float] = []
    missing_high: list[str] = []
    for start_t, end_t, diff_v in phases:
        phase_samples = [value for t, value in zip(times, out_p) if start_t <= t < end_t]
        if not phase_samples or max(phase_samples) < threshold:
            missing_high.append(f"{diff_v * 1e3:.2g}mV")
            continue

        search_start = start_t + clk_rise_offset
        pre_sample = _sample_vector_at(times, out_p, search_start - 20e-12)
        if pre_sample is None or pre_sample > threshold:
            return False, f"out_p_not_low_before_clock diff={diff_v * 1e3:.2g}mV"

        crossing_t = None
        for idx, t in enumerate(times):
            if t < search_start or t >= min(end_t, search_start + 3.0e-9):
                continue
            prev = out_p[idx - 1] if idx > 0 else out_p[idx]
            if prev <= threshold and out_p[idx] > threshold:
                crossing_t = t
                break
        if crossing_t is None:
            return False, f"missing_threshold_crossing diff={diff_v * 1e3:.2g}mV"
        delays_ns.append((crossing_t - search_start) * 1e9)

    if missing_high:
        return False, f"out_p_never_high phases={','.join(missing_high)}"
    if len(delays_ns) != len(phases):
        return False, f"insufficient_delay_measurements count={len(delays_ns)}"

    monotonic = all(delays_ns[i] <= delays_ns[i + 1] + 0.015 for i in range(len(delays_ns) - 1))
    total_growth_ns = delays_ns[-1] - delays_ns[0]
    ok = monotonic and total_growth_ns >= 0.015
    return ok, (
        f"delays_ns={[round(v, 3) for v in delays_ns]} "
        f"monotonic={monotonic} total_growth_ns={total_growth_ns:.3f}"
    )


def check_cmp_delay(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "vinp", "vinn", "out_p", "out_n", "delay_ps"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/clk/vinp/vinn/out_p/out_n/delay_ps"

    times = [r["time"] for r in rows]
    out_p = [r["out_p"] for r in rows]
    return _check_cmp_delay_vectors(times, out_p)


def check_cmp_strongarm(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "out_p", "out_n"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/out_p/out_n"

    threshold = 0.45
    out_p = [r["out_p"] for r in rows]
    out_n = [r["out_n"] for r in rows]

    out_p_span = max(out_p) - min(out_p)
    out_n_span = max(out_n) - min(out_n)
    if out_p_span < threshold or out_n_span < threshold:
        return False, f"insufficient_toggle out_p_span={out_p_span:.3f} out_n_span={out_n_span:.3f}"

    samples = []
    for sample_t in [0.75e-9, 1.75e-9, 2.75e-9, 3.75e-9]:
        out_p_sample = sample_signal_at(rows, "out_p", sample_t)
        out_n_sample = sample_signal_at(rows, "out_n", sample_t)
        if out_p_sample is None or out_n_sample is None:
            return False, f"missing_decision_sample_at={sample_t * 1e9:.2f}ns"
        if out_p_sample > threshold and out_n_sample < threshold:
            samples.append("P")
        elif out_p_sample < threshold and out_n_sample > threshold:
            samples.append("N")
        else:
            samples.append("X")

    ok = samples == ["P", "P", "N", "N"]
    return ok, f"decision_samples={''.join(samples)} expected=PPNN"


def check_strongarm_reset_priority_bug(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "rst", "inp", "inn", "outp", "outn"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/rst/inp/inn/outp/outn"

    threshold = 0.45
    reset_window = [r for r in rows if r["rst"] > threshold]
    active_window = [r for r in rows if r["time"] >= 24e-9 and r["rst"] < threshold]
    if not reset_window or not active_window:
        return False, "insufficient_reset_or_active_window"

    reset_outp_max = max(r["outp"] for r in reset_window)
    reset_outn_max = max(r["outn"] for r in reset_window)

    high_rows = [r for r in active_window if r["inp"] > r["inn"] + 5e-3]
    low_rows = [r for r in active_window if r["inp"] + 5e-3 < r["inn"]]
    if not high_rows or not low_rows:
        return False, "missing_post_reset_polarity_windows"

    high_outp = sum(1 for r in high_rows if r["outp"] > threshold) / len(high_rows)
    high_outn = sum(1 for r in high_rows if r["outn"] < threshold) / len(high_rows)
    low_outp = sum(1 for r in low_rows if r["outp"] < threshold) / len(low_rows)
    low_outn = sum(1 for r in low_rows if r["outn"] > threshold) / len(low_rows)

    ok = (
        reset_outp_max < 0.1
        and reset_outn_max < 0.1
        and high_outp > 0.75
        and high_outn > 0.75
        and low_outp > 0.75
        and low_outn > 0.75
    )
    return ok, (
        f"reset_outp_max={reset_outp_max:.3f} "
        f"reset_outn_max={reset_outn_max:.3f} "
        f"high_outp={high_outp:.3f} high_outn={high_outn:.3f} "
        f"low_outp={low_outp:.3f} low_outn={low_outn:.3f}"
    )


def check_cmp_hysteresis(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "out_p", "out_n"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/out_p/out_n"

    threshold = 0.45
    times_ns = [r["time"] * 1e9 for r in rows]
    out_p = [r["out_p"] for r in rows]
    out_n = [r["out_n"] for r in rows]

    if max(out_p) - min(out_p) < threshold or max(out_n) - min(out_n) < threshold:
        return False, "outputs_do_not_toggle"

    pre = [out_p[idx] for idx, t in enumerate(times_ns) if t < 20.0]
    mid = [out_p[idx] for idx, t in enumerate(times_ns) if 35.0 < t < 60.0]
    post = [out_p[idx] for idx, t in enumerate(times_ns) if t > 75.0]
    if not pre or not mid or not post:
        return False, "insufficient_hysteresis_windows"

    pre_low_frac = sum(1 for v in pre if v < threshold) / len(pre)
    mid_high_frac = sum(1 for v in mid if v > threshold) / len(mid)
    post_low_frac = sum(1 for v in post if v < threshold) / len(post)
    if pre_low_frac < 0.95 or mid_high_frac < 0.95 or post_low_frac < 0.95:
        return False, f"window_fracs pre={pre_low_frac:.3f} mid={mid_high_frac:.3f} post={post_low_frac:.3f}"

    rise_t = None
    fall_t = None
    for idx in range(1, len(out_p)):
        if rise_t is None and out_p[idx - 1] < threshold <= out_p[idx]:
            rise_t = times_ns[idx]
        if fall_t is None and out_p[idx - 1] > threshold >= out_p[idx]:
            fall_t = times_ns[idx]

    if rise_t is None or fall_t is None:
        return False, "missing_trip_crossings"
    if not (29.0 <= rise_t <= 31.5):
        return False, f"rise_t_out_of_range={rise_t:.3f}ns"
    if not (68.5 <= fall_t <= 71.5):
        return False, f"fall_t_out_of_range={fall_t:.3f}ns"
    return True, f"rise_t={rise_t:.3f}ns fall_t={fall_t:.3f}ns"


def check_ramp_gen(rows: list[dict[str, float]]) -> tuple[bool, str]:
    bit_names = [f"code_{i}" for i in range(12) if f"code_{i}" in rows[0]]
    if not bit_names:
        return False, "missing code_* bits"
    codes = decode_bus(rows, bit_names)
    nondecreasing = all(codes[i] <= codes[i + 1] for i in range(len(codes) - 1))
    return nondecreasing, f"code_start={codes[0]} code_end={codes[-1]}"


def check_d2b(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows:
        return False, "empty tran.csv"
    if all(k in rows[0] for k in ["bin_o_3", "bin_o_2", "bin_o_1", "bin_o_0"]):
        codes = decode_bus(rows, ["bin_o_0", "bin_o_1", "bin_o_2", "bin_o_3"])
        stable = len(set(codes)) == 1
        return stable and codes[0] == 9, f"stable_code={codes[0]}"
    dout_bits = [k for k in rows[0] if re.fullmatch(r"dout[_\[]?\d+\]?", k, flags=re.IGNORECASE)]
    vin_col = next((k for k in rows[0] if k.lower().startswith("vin")), None)
    if vin_col and dout_bits:
        codes = decode_bus(rows, dout_bits)
        vins = [r[vin_col] for r in rows]
        pairs = sorted(zip(vins, codes), key=lambda x: x[0])
        monotonic = all(pairs[i][1] <= pairs[i + 1][1] for i in range(len(pairs) - 1))
        return monotonic, "dynamic monotonic code check"
    return False, "missing d2b outputs"


def check_adc_dac_ideal_4b(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows or not {"vin", "vout", "rst_n"}.issubset(rows[0]):
        return False, "missing vin/vout/rst_n"
    post = [r for r in rows if r["rst_n"] > 0.45]
    if not post:
        return False, "no post-reset samples"
    if "dout_code" in rows[0]:
        codes = [int(round(r["dout_code"])) for r in post]
    elif {"dout_3", "dout_2", "dout_1", "dout_0"}.issubset(rows[0]):
        codes = [
            ((1 if r["dout_3"] > 0.45 else 0) << 3)
            | ((1 if r["dout_2"] > 0.45 else 0) << 2)
            | ((1 if r["dout_1"] > 0.45 else 0) << 1)
            | (1 if r["dout_0"] > 0.45 else 0)
            for r in post
        ]
    else:
        return False, "missing dout_code or dout_3..0"
    vouts = [r["vout"] for r in post]
    vins = [r["vin"] for r in post]
    unique_codes = len(set(codes))
    monotonic = all(codes[i] <= codes[i + 1] for i in range(len(codes) - 1))
    span = max(vouts) - min(vouts)
    vin_span = max(vins) - min(vins)
    ok = unique_codes >= 12 and monotonic and span > 0.6 and vin_span > 0.6
    return ok, f"unique_codes={unique_codes} vout_span={span:.3f} vin_span={vin_span:.3f}"


def check_dac_binary_clk_4b(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows or not {"din3", "din2", "din1", "din0", "aout"}.issubset(rows[0]):
        return False, "missing din*/aout"
    levels: dict[int, list[float]] = {}
    for r in rows:
        code = (
            (1 if r["din3"] > 0.45 else 0) * 8
            + (1 if r["din2"] > 0.45 else 0) * 4
            + (1 if r["din1"] > 0.45 else 0) * 2
            + (1 if r["din0"] > 0.45 else 0)
        )
        levels.setdefault(code, []).append(r["aout"])
    medians = {c: sum(vs) / len(vs) for c, vs in levels.items()}
    sorted_codes = sorted(medians)
    monotonic = all(medians[sorted_codes[i]] <= medians[sorted_codes[i + 1]] + 1e-9 for i in range(len(sorted_codes) - 1))
    span = medians[sorted_codes[-1]] - medians[sorted_codes[0]] if sorted_codes else 0.0
    ok = len(sorted_codes) >= 14 and monotonic and span > 0.7
    return ok, f"levels={len(sorted_codes)} aout_span={span:.3f}"


def check_dac_therm_16b(rows: list[dict[str, float]]) -> tuple[bool, str]:
    bit_names = [f"d{i}" for i in range(16) if f"d{i}" in rows[0]]
    if not rows or not bit_names or "vout" not in rows[0]:
        return False, "missing d*/vout"
    ones_counts = [sum(1 for b in bit_names if r[b] > 0.45) for r in rows]
    vouts = [r["vout"] for r in rows]
    max_ones = max(ones_counts)
    max_vout = max(vouts)
    last_pairs: dict[int, float] = {}
    for ones, vout in zip(ones_counts, vouts):
        last_pairs[ones] = vout
    sorted_ones = sorted(last_pairs)
    monotonic = all(last_pairs[sorted_ones[i]] <= last_pairs[sorted_ones[i + 1]] + 1e-9 for i in range(len(sorted_ones) - 1))
    ok = max_ones == 16 and max_vout > 15.0 and monotonic
    return ok, f"max_ones={max_ones} max_vout={max_vout:.3f}"


def check_vbm1_thermometer_dac_15seg(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows:
        return False, "empty"
    seg_names = [f"seg{i}" for i in range(15)]
    required = {"time", "aout", *seg_names}
    if not required.issubset(rows[0]):
        return False, f"missing time/aout/seg0..seg14; keys={list(rows[0].keys())[:10]}"

    checkpoints = [
        (15e-9, 0),
        (45e-9, 1),
        (75e-9, 2),
        (105e-9, 7),
        (135e-9, 14),
        (165e-9, 15),
    ]
    levels: list[tuple[int, float]] = []
    errors: list[float] = []
    notes: list[str] = []
    for target_t, expected_count in checkpoints:
        row = min(rows, key=lambda r: abs(r["time"] - target_t))
        observed_count = sum(1 for name in seg_names if row[name] > 0.45)
        expected_v = 0.9 * expected_count / 15.0
        error = abs(row["aout"] - expected_v)
        levels.append((expected_count, row["aout"]))
        errors.append(error)
        notes.append(f"{expected_count}:{row['aout']:.3f}/{observed_count}")

    monotonic = all(levels[i][1] <= levels[i + 1][1] + 1e-6 for i in range(len(levels) - 1))
    counts_match = all(
        sum(1 for name in seg_names if min(rows, key=lambda r, t=t: abs(r["time"] - t))[name] > 0.45) == count
        for t, count in checkpoints
    )
    max_err = max(errors)
    full_scale_ok = abs(levels[-1][1] - 0.9) <= 0.02
    ok = counts_match and monotonic and max_err <= 0.02 and full_scale_ok
    return ok, (
        f"levels={' '.join(notes)} max_err={max_err:.3f} "
        f"monotonic={monotonic} counts_match={counts_match} "
        f"full_scale_ok={full_scale_ok}"
    )


def check_sar_adc_dac_weighted_8b(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {
        "time",
        "vin",
        "vin_sh",
        "clks",
        "vout",
        "rst_n",
    }
    if not rows or not required.issubset(rows[0]):
        missing = sorted(required - set(rows[0].keys())) if rows else sorted(required)
        return False, f"missing_columns={','.join(missing)}"

    # Always decode from dout bits for consistent comparison across simulators:
    # EVAS may expose a decoded bus column, but Spectre emits scalar bit nodes.
    bit_names = [f"dout_{idx}" for idx in range(8)]
    if not set(bit_names).issubset(rows[0]):
        return False, "missing dout_0..7"

    times = [r["time"] for r in rows]
    edge_times = rising_edges([r["clks"] for r in rows], times)
    clock_rows = sample_rows_at_or_after_times(rows, [t + 1.0e-9 for t in edge_times], rst_key="rst_n")
    sample_rows = clock_rows
    if len(sample_rows) < 48:
        return False, f"too_few_post_reset_conversions={len(sample_rows)}"

    codes = decode_bus(sample_rows, bit_names)
    vinsh = [r["vin_sh"] for r in sample_rows]
    vouts = [r["vout"] for r in sample_rows]
    vdd = 0.9
    code_voltages = [code / 255.0 * vdd for code in codes]
    unique_codes = len(set(codes))
    code_min = min(codes)
    code_max = max(codes)
    sample_span = max(vinsh) - min(vinsh)
    vout_span = max(vouts) - min(vouts)
    avg_quant_err = sum(abs(sample - code_v) for sample, code_v in zip(vinsh, code_voltages)) / len(sample_rows)
    max_quant_err = max(abs(sample - code_v) for sample, code_v in zip(vinsh, code_voltages))
    avg_dac_err = sum(abs(vout - code_v) for vout, code_v in zip(vouts, code_voltages)) / len(sample_rows)
    max_dac_err = max(abs(vout - code_v) for vout, code_v in zip(vouts, code_voltages))
    avg_roundtrip_err = sum(abs(sample - vout) for sample, vout in zip(vinsh, vouts)) / len(sample_rows)

    sorted_pairs = sorted(zip(vinsh, codes), key=lambda item: item[0])
    monotonic_reversals = sum(
        1 for (_, prev_code), (_, curr_code) in zip(sorted_pairs, sorted_pairs[1:])
        if curr_code + 2 < prev_code
    )

    ok = (
        unique_codes >= 48
        and code_min <= 8
        and code_max >= 247
        and sample_span > 0.75
        and vout_span > 0.75
        and avg_quant_err < 0.025
        and max_quant_err < 0.060
        and avg_dac_err < 0.020
        and max_dac_err < 0.060
        and avg_roundtrip_err < 0.030
        and monotonic_reversals <= max(2, len(sorted_pairs) // 50)
        and min(vouts) >= -0.02
        and max(vouts) <= vdd + 0.02
    )
    return ok, (
        f"samples={len(sample_rows)} unique_codes={unique_codes} code_range={code_min}-{code_max} "
        f"sample_span={sample_span:.3f} vout_span={vout_span:.3f} "
        f"avg_quant_err={avg_quant_err:.4f} max_quant_err={max_quant_err:.4f} "
        f"avg_dac_err={avg_dac_err:.4f} max_dac_err={max_dac_err:.4f} "
        f"avg_roundtrip_err={avg_roundtrip_err:.4f} monotonic_reversals={monotonic_reversals}"
    )


def check_not_gate(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows or not {"a", "y"}.issubset(rows[0]):
        return False, "missing a/y"
    # Down-sample to ≥500 ps spacing to avoid over-weighting EVAS transition sub-steps
    sampled: list[dict[str, float]] = []
    last_t = -1.0
    for r in rows:
        if r["time"] - last_t >= 5e-10:
            sampled.append(r)
            last_t = r["time"]
    check_rows = sampled if len(sampled) >= 10 else rows
    good = sum(1 for r in check_rows if (r["a"] > 0.4) != (r["y"] > 0.4))
    frac = good / len(check_rows)
    return frac > 0.9, f"invert_match_frac={frac:.3f}"


def check_and_gate(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"a", "b", "y"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing a/b/y"
    check_rows = [r for r in rows if r["time"] >= rows[0]["time"] + 5e-10]
    if len(check_rows) < 10:
        check_rows = rows
    good = 0
    for r in check_rows:
        a_hi = r["a"] > 0.45
        b_hi = r["b"] > 0.45
        y_hi = r["y"] > 0.45
        if y_hi == (a_hi and b_hi):
            good += 1
    frac = good / len(check_rows)
    return frac > 0.92, f"and_truth_match_frac={frac:.3f}"


def check_or_gate(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"a", "b", "y"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing a/b/y"
    check_rows = [r for r in rows if r["time"] >= rows[0]["time"] + 5e-10]
    if len(check_rows) < 10:
        check_rows = rows
    good = 0
    for r in check_rows:
        a_hi = r["a"] > 0.45
        b_hi = r["b"] > 0.45
        y_hi = r["y"] > 0.45
        if y_hi == (a_hi or b_hi):
            good += 1
    frac = good / len(check_rows)
    return frac > 0.92, f"or_truth_match_frac={frac:.3f}"


def check_dff_rst(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "d", "clk", "rst", "q", "qb"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/d/clk/rst/q/qb"
    clk_max = max(r["clk"] for r in rows)
    vth = 0.45 if clk_max < 0.9 else 0.5 * clk_max
    edges = [
        idx
        for idx in range(1, len(rows))
        if rows[idx - 1]["clk"] <= vth < rows[idx]["clk"]
    ]
    if len(edges) < 6:
        return False, f"too_few_clk_edges={len(edges)}"

    mismatches = 0
    qb_mismatches = 0
    checks = 0
    for idx in edges:
        edge_row = rows[idx]
        edge_time = edge_row["time"]
        settle = idx
        while settle + 1 < len(rows) and rows[settle]["time"] < edge_time + 100e-12:
            settle += 1
        r = rows[settle]
        expected_q_hi = False if edge_row["rst"] > vth else (edge_row["d"] > vth)
        q_hi = r["q"] > vth
        qb_hi = r["qb"] > vth
        checks += 1
        if q_hi != expected_q_hi:
            mismatches += 1
        if qb_hi == q_hi:
            qb_mismatches += 1
    ok = checks >= 6 and mismatches <= 1 and qb_mismatches <= 1
    return ok, f"checks={checks} q_mismatch={mismatches} qb_mismatch={qb_mismatches}"


def check_lfsr(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows or not {"dpn", "rstb"}.issubset(rows[0]):
        return False, "missing dpn/rstb"
    post = [r["dpn"] for r in rows if r["rstb"] > 0.45]
    if len(post) < 2:
        return False, "not enough post-reset samples"
    binary = [1 if v > 0.45 else 0 for v in post]
    hi_frac = sum(binary) / len(binary)
    transitions = sum(1 for i in range(len(binary) - 1) if binary[i] != binary[i + 1])
    ok = 0.05 < hi_frac < 0.95 and transitions >= 10
    return ok, f"transitions={transitions} hi_frac={hi_frac:.3f}"


def check_prbs7(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"clk", "rst_n", "en", "serial_out"} | {f"state_{i}" for i in range(7)}
    if not rows or not required.issubset(rows[0]):
        return False, "missing clk/rst_n/en/serial_out/state_*"

    post = [r for r in rows if r["rst_n"] > 0.45 and r["en"] > 0.45]
    if len(post) < 2:
        return False, "no post-reset enabled samples"

    def bit(row: dict[str, float], name: str) -> int:
        return 1 if row[name] > 0.45 else 0

    def state_code(row: dict[str, float]) -> int:
        code = 0
        for idx in range(7):
            code |= bit(row, f"state_{idx}") << idx
        return code

    serial = [bit(r, "serial_out") for r in post]
    states = [state_code(r) for r in post]

    if all(code == 0 for code in states):
        return False, "state stuck at zero"

    serial_transitions = sum(1 for i in range(len(serial) - 1) if serial[i] != serial[i + 1])
    unique_states = len(set(states))
    state_transitions = sum(1 for i in range(len(states) - 1) if states[i] != states[i + 1])

    ok = serial_transitions >= 10 and unique_states >= 8 and state_transitions >= 8
    return ok, f"serial_transitions={serial_transitions} unique_states={unique_states} state_transitions={state_transitions}"


def check_therm2bin(rows: list[dict[str, float]]) -> tuple[bool, str]:
    therm_bits = [f"therm_{i}" for i in range(15)]
    bin_bits = [f"bin_{i}" for i in range(4)]
    required = set(therm_bits + bin_bits)
    if not rows or not required.issubset(rows[0]):
        return False, "missing therm_* or bin_* signals"

    def bit(row: dict[str, float], name: str) -> int:
        return 1 if row[name] > 0.45 else 0

    def thermometer_count(row: dict[str, float]) -> int:
        return sum(bit(row, name) for name in therm_bits)

    def binary_code(row: dict[str, float]) -> int:
        return sum(bit(row, f"bin_{idx}") << idx for idx in range(4))

    counts = [thermometer_count(row) for row in rows]
    codes = [binary_code(row) for row in rows]

    if not counts:
        return False, "empty therm2bin dataset"

    def far_from_threshold(v: float, lo: float = 0.35, hi: float = 0.55) -> bool:
        return v <= lo or v >= hi

    stable_indices = []
    for idx in range(1, len(rows)):
        if counts[idx] != counts[idx - 1]:
            continue
        therm_stable = all(
            far_from_threshold(rows[idx][name]) and far_from_threshold(rows[idx - 1][name])
            for name in therm_bits
        )
        bin_stable = all(
            far_from_threshold(rows[idx][name])
            for name in bin_bits
        )
        if therm_stable and bin_stable:
            stable_indices.append(idx)

    min_stable_points = max(10, len(rows) // 20)
    if len(stable_indices) < min_stable_points:
        return False, f"insufficient_strict_stable_points={len(stable_indices)}"

    mismatches = [idx for idx in stable_indices if codes[idx] != min(counts[idx], 15)]
    stable_ok = len(mismatches) == 0
    distinct_counts = len(set(counts))
    bubble_present = any(
        counts[i] > counts[i + 1]
        for i in range(len(counts) - 1)
    )
    ok = stable_ok and distinct_counts >= 6 and bubble_present
    return ok, f"distinct_counts={distinct_counts} bubble_present={bubble_present} strict_stable_points={len(stable_indices)} strict_mismatches={len(mismatches)}"


def check_multimod_divider(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"clk_in", "mod", "prescaler_out", "mod_0", "mod_1", "mod_2", "mod_3"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing clk_in/mod/prescaler_out/mod_*"

    times = [r["time"] for r in rows]
    clk_edges = [i for i in range(1, len(rows)) if rows[i - 1]["clk_in"] < 0.45 <= rows[i]["clk_in"]]
    out_edges = [i for i in range(1, len(rows)) if rows[i - 1]["prescaler_out"] < 0.45 <= rows[i]["prescaler_out"]]
    clk_edge_times = [times[idx] for idx in clk_edges]

    if len(clk_edges) < 8 or len(out_edges) < 4:
        return False, "not enough clock or output edges"

    base = sum((1 if rows[0][f"mod_{idx}"] > 0.45 else 0) << idx for idx in range(4))
    if base < 1:
        base = 1

    switch_time = None
    for idx in range(1, len(rows)):
        if rows[idx - 1]["mod"] < 0.45 <= rows[idx]["mod"]:
            switch_time = times[idx]
            break

    if switch_time is None:
        return False, "no MOD transition found"

    intervals = []
    for idx in range(1, len(out_edges)):
        start_idx = out_edges[idx - 1]
        end_idx = out_edges[idx]
        start_t = times[start_idx]
        end_t = times[end_idx]
        interval_len = sum(1 for clk_t in clk_edge_times if start_t < clk_t <= end_t)
        intervals.append((start_t, end_t, interval_len))

    pre = [interval for start_t, end_t, interval in intervals if end_t < switch_time]
    post = [interval for start_t, end_t, interval in intervals if start_t >= switch_time]

    pre_ok = len(pre) >= 2 and all(interval == base for interval in pre)
    post_ok = len(post) >= 2 and all(interval == base + 1 for interval in post)
    ok = pre_ok and post_ok
    return ok, f"base={base} pre_count={len(pre)} post_count={len(post)} switch_time_ns={switch_time * 1e9:.3f}"


def check_multimod_divider_ratio_switch(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk_in", "div_out"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/clk_in/div_out"

    times = [r["time"] for r in rows]
    in_edges = rising_edges([r["clk_in"] for r in rows], times)
    out_edges = rising_edges([r["div_out"] for r in rows], times)
    if len(in_edges) < 40 or len(out_edges) < 10:
        return False, f"not_enough_edges in={len(in_edges)} out={len(out_edges)}"

    windows = [
        (10e-9, 90e-9, 4, "pre_div4"),
        (120e-9, 190e-9, 5, "mid_div5"),
        (220e-9, 300e-9, 4, "post_div4"),
    ]
    details: list[str] = []
    for t0, t1, expected_ratio, label in windows:
        win_in = [t for t in in_edges if t0 <= t <= t1]
        win_out = [t for t in out_edges if t0 <= t <= t1]
        if len(win_in) < expected_ratio * 2 or len(win_out) < 2:
            return False, f"{label}_insufficient_edges in={len(win_in)} out={len(win_out)}"
        measured_ratio = len(win_in) / max(len(win_out), 1)
        details.append(f"{label}={measured_ratio:.2f}")
        if abs(measured_ratio - expected_ratio) > 0.35:
            return False, ";".join(details)
    return True, ";".join(details)


def check_bbpd(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "data", "clk", "retimed_data", "up", "down"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/data/clk/retimed_data/up/down"

    vth = 0.45
    data_edges = [
        i
        for i in range(1, len(rows))
        if rows[i - 1]["data"] < vth <= rows[i]["data"] or rows[i - 1]["data"] > vth >= rows[i]["data"]
    ]
    up_edges = [i for i in range(1, len(rows)) if rows[i - 1]["up"] < vth <= rows[i]["up"]]
    down_edges = [i for i in range(1, len(rows)) if rows[i - 1]["down"] < vth <= rows[i]["down"]]

    if len(data_edges) < 6:
        return False, "not enough data edges"

    overlap = sum(1 for r in rows if r["up"] > vth and r["down"] > vth)
    overlap_frac = overlap / max(len(rows), 1)

    edge_trigger_ok = len(up_edges) + len(down_edges) >= max(4, len(data_edges) // 4)
    pulse_presence_ok = len(up_edges) >= 2 and len(down_edges) >= 2
    non_overlap_ok = overlap_frac < 0.02

    directional_counts = {
        "up_expected": 0,
        "down_expected": 0,
        "up_correct": 0,
        "down_correct": 0,
        "none_expected": 0,
        "none_correct": 0,
        "wrong": 0,
        "missing": 0,
        "false_pulse": 0,
    }
    response_window_s = 0.2e-9
    for edge_idx in data_edges:
        clk_high = rows[edge_idx]["clk"] > vth
        retimed_high = rows[edge_idx]["retimed_data"] > vth
        if clk_high and not retimed_high:
            expected = "up"
        elif not clk_high and retimed_high:
            expected = "down"
        else:
            expected = "none"

        edge_time = rows[edge_idx]["time"]
        window_rows = []
        for row in rows[edge_idx:]:
            if row["time"] > edge_time + response_window_s:
                break
            window_rows.append(row)
        if expected == "none":
            directional_counts["none_expected"] += 1
            if any(row["up"] > vth or row["down"] > vth for row in window_rows):
                directional_counts["false_pulse"] += 1
            else:
                directional_counts["none_correct"] += 1
            continue

        directional_counts[f"{expected}_expected"] += 1
        wrong = "down" if expected == "up" else "up"
        expected_hit = any(row[expected] > vth for row in window_rows)
        wrong_hit = any(row[wrong] > vth for row in window_rows)
        if expected_hit and not wrong_hit:
            directional_counts[f"{expected}_correct"] += 1
        elif wrong_hit:
            directional_counts["wrong"] += 1
        else:
            directional_counts["missing"] += 1

    directional_ok = (
        directional_counts["up_expected"] >= 2
        and directional_counts["down_expected"] >= 2
        and directional_counts["up_correct"] >= max(2, int(0.75 * directional_counts["up_expected"]))
        and directional_counts["down_correct"] >= max(2, int(0.75 * directional_counts["down_expected"]))
        and directional_counts["wrong"] == 0
        and directional_counts["none_expected"] >= 2
        and directional_counts["false_pulse"] == 0
    )
    ok = edge_trigger_ok and pulse_presence_ok and non_overlap_ok and directional_ok
    return ok, (
        f"data_edges={len(data_edges)} up_edges={len(up_edges)} down_edges={len(down_edges)} "
        f"overlap_frac={overlap_frac:.4f} "
        f"direction_up={directional_counts['up_correct']}/{directional_counts['up_expected']} "
        f"direction_down={directional_counts['down_correct']}/{directional_counts['down_expected']} "
        f"none={directional_counts['none_correct']}/{directional_counts['none_expected']} "
        f"wrong_direction={directional_counts['wrong']} missing_direction={directional_counts['missing']} "
        f"false_pulse={directional_counts['false_pulse']}"
    )


def check_bbpd_data_edge_alignment(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"clk", "data", "up", "dn"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing clk/data/up/dn"

    vth = 0.45
    times = [r["time"] for r in rows]
    up = [r["up"] for r in rows]
    dn = [r["dn"] for r in rows]
    data = [r["data"] for r in rows]

    up_edges = [times[i] for i in range(1, len(rows)) if up[i - 1] <= vth < up[i]]
    dn_edges = [times[i] for i in range(1, len(rows)) if dn[i - 1] <= vth < dn[i]]
    data_edges = [
        times[i]
        for i in range(1, len(rows))
        if ((data[i - 1] <= vth < data[i]) or (data[i - 1] >= vth > data[i]))
    ]

    if len(data_edges) < 6:
        return False, f"too_few_data_edges={len(data_edges)}"
    if len(up_edges) + len(dn_edges) < 6:
        return False, f"too_few_updn_pulses={len(up_edges) + len(dn_edges)}"

    overlap = sum(1 for r in rows if r["up"] > vth and r["dn"] > vth)
    overlap_frac = overlap / max(len(rows), 1)
    if overlap_frac > 0.02:
        return False, f"overlap_frac={overlap_frac:.4f}"

    lead_window_end = 80e-9
    lag_window_start = 90e-9
    up_lead = sum(1 for t in up_edges if t <= lead_window_end)
    dn_lead = sum(1 for t in dn_edges if t <= lead_window_end)
    up_lag = sum(1 for t in up_edges if t >= lag_window_start)
    dn_lag = sum(1 for t in dn_edges if t >= lag_window_start)

    if up_lead < 3 or up_lead <= dn_lead:
        return False, f"lead_window_updn={up_lead}/{dn_lead}"
    if dn_lag < 3 or dn_lag <= up_lag:
        return False, f"lag_window_updn={up_lag}/{dn_lag}"

    return True, (
        f"data_edges={len(data_edges)} "
        f"lead_updn={up_lead}/{dn_lead} "
        f"lag_updn={up_lag}/{dn_lag} "
        f"overlap_frac={overlap_frac:.4f}"
    )


def _find_bus_columns(sample: dict[str, float], base: str) -> dict[int, str]:
    cols: dict[int, str] = {}
    pattern = re.compile(rf"^{re.escape(base)}(?:_|\[)?(\d+)\]?$", re.IGNORECASE)
    for name in sample:
        m = pattern.match(name)
        if m:
            cols[int(m.group(1))] = name
    return cols


def _pick_column(sample: dict[str, float], candidates: list[str]) -> str | None:
    lower_map = {k.lower(): k for k in sample.keys()}
    for name in candidates:
        if name in sample:
            return name
        if name.lower() in lower_map:
            return lower_map[name.lower()]
    return None


def check_bad_bus_output_loop(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows:
        return False, "empty tran.csv"

    sample = rows[0]
    code_cols = _find_bus_columns(sample, "CODE")
    dout_cols = _find_bus_columns(sample, "DOUT")
    bit_indices = [idx for idx in range(4) if idx in code_cols and idx in dout_cols]

    if len(bit_indices) != 4:
        return False, "missing CODE_*/DOUT_* bit columns"

    mismatch = 0
    total = 0
    code_patterns = set()
    dout_patterns = set()
    uniform_rows = 0
    stable_rows = 0
    prev_code_tuple = None
    settle_until = float("-inf")
    settle_s = 0.1e-9

    for row in rows:
        code_vec = []
        dout_vec = []
        for idx in bit_indices:
            code_bit = 1 if row[code_cols[idx]] > 0.45 else 0
            dout_bit = 1 if row[dout_cols[idx]] > 0.45 else 0
            code_vec.append(code_bit)
            dout_vec.append(dout_bit)
        code_tuple = tuple(code_vec)
        dout_tuple = tuple(dout_vec)
        t = row.get("time", 0.0)
        if prev_code_tuple is not None and code_tuple != prev_code_tuple:
            settle_until = max(settle_until, t + settle_s)
        prev_code_tuple = code_tuple

        code_patterns.add(code_tuple)
        dout_patterns.add(dout_tuple)
        if len(set(dout_tuple)) == 1:
            uniform_rows += 1
        if t <= settle_until:
            continue
        stable_rows += 1
        for code_bit, dout_bit in zip(code_tuple, dout_tuple):
            total += 1
            if code_bit != dout_bit:
                mismatch += 1

    mismatch_frac = mismatch / max(total, 1)
    uniform_frac = uniform_rows / max(len(rows), 1)
    ok = (
        mismatch_frac < 0.05
        and len(code_patterns) >= 6
        and len(dout_patterns) >= 6
        and uniform_frac < 0.8
        and stable_rows >= 20
    )
    return ok, (
        f"mismatch_frac={mismatch_frac:.4f} code_patterns={len(code_patterns)} "
        f"dout_patterns={len(dout_patterns)} uniform_frac={uniform_frac:.3f} "
        f"stable_rows={stable_rows}"
    )


def check_missing_transition_outputs(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows:
        return False, "empty tran.csv"

    sample = rows[0]
    vin_col = _pick_column(sample, ["VIN", "vin", "vin_i"])
    flag_col = _pick_column(sample, ["FLAG", "flag", "flag_o", "out_p", "out"])
    if vin_col is None or flag_col is None:
        return False, "missing VIN/FLAG columns"

    vins = [r[vin_col] for r in rows]
    flags = [r[flag_col] for r in rows]
    vmin = min(vins)
    vmax = max(vins)
    if vmax - vmin < 0.2:
        return False, "VIN does not cross threshold range"

    threshold = 0.5 * (vmax + vmin)
    margin = max(0.05 * (vmax - vmin), 0.03)
    crossing_times = [
        rows[i]["time"]
        for i in range(1, len(rows))
        if (vins[i - 1] - threshold) * (vins[i] - threshold) <= 0 and vins[i - 1] != vins[i]
    ]
    settle_s = 0.5e-9
    stable_indices = [
        i
        for i, vin in enumerate(vins)
        if abs(vin - threshold) > margin
        and all(abs(rows[i]["time"] - t_cross) > settle_s for t_cross in crossing_times)
    ]
    if len(stable_indices) < max(10, len(rows) // 4):
        return False, "insufficient stable samples away from threshold"

    mismatch = 0
    for idx in stable_indices:
        expected = vins[idx] > threshold
        observed = flags[idx] > 0.45
        if expected != observed:
            mismatch += 1

    mismatch_frac = mismatch / len(stable_indices)
    flag_span = max(flags) - min(flags)
    high_seen = any(flags[idx] > 0.45 for idx in stable_indices)
    low_seen = any(flags[idx] <= 0.45 for idx in stable_indices)
    ok = mismatch_frac < 0.08 and flag_span > 0.4 and high_seen and low_seen
    return ok, f"mismatch_frac={mismatch_frac:.4f} flag_span={flag_span:.3f} stable_samples={len(stable_indices)}"


def check_dwa_ptr_gen(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows:
        return False, "no rows"
    keys = set(rows[0].keys())
    # Accept either bus-integer format (ptr_code/cell_en_code) or individual bits (ptr_0..ptr_15)
    use_codes = {"clk_i", "rst_ni", "cell_en_code", "ptr_code"}.issubset(keys)
    use_bits  = {"clk_i", "rst_ni", "ptr_0", "cell_en_0"}.issubset(keys)
    if not use_codes and not use_bits:
        return False, "missing required columns (need ptr_code/cell_en_code or ptr_0..15/cell_en_0..15)"
    post = [r for r in rows if r["rst_ni"] > 0.45]
    if not post:
        return False, "no post-reset samples"
    if use_codes:
        ptr_codes  = [int(round(r["ptr_code"])) for r in post]
        cell_codes = [int(round(r["cell_en_code"])) for r in post]
    else:
        # Reconstruct integer codes from individual bit columns
        ptr_bits  = [k for k in keys if k.startswith("ptr_") and k[4:].isdigit()]
        cell_bits = [k for k in keys if k.startswith("cell_en_") and k[8:].isdigit()]
        ptr_codes  = [sum(int(r[b] > 0.45) << int(b[4:])  for b in ptr_bits)  for r in post]
        cell_codes = [sum(int(r[b] > 0.45) << int(b[8:]) for b in cell_bits) for r in post]
    ptr_nonzero = all(v > 0 for v in ptr_codes)
    ptr_unique = len(set(ptr_codes))
    cell_active = max(cell_codes) > 0
    ok = ptr_nonzero and cell_active and ptr_unique >= 4
    return ok, f"ptr_unique={ptr_unique} max_cell_code={max(cell_codes)}"


def check_dwa_ptr_gen_no_overlap(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows:
        return False, "no rows"

    keys = set(rows[0].keys())
    required = {"time", "clk_i", "rst_ni", "ptr_0", "cell_en_0"}
    if not required.issubset(keys):
        return False, "missing time/clk_i/rst_ni/ptr_0/cell_en_0"

    ptr_cols = indexed_columns(keys, "ptr_")
    cell_cols = indexed_columns(keys, "cell_en_")
    if not ptr_cols or not cell_cols:
        return False, "missing ptr_* or cell_en_* columns"

    times = [r["time"] for r in rows]
    clk_vals = [r["clk_i"] for r in rows]
    rst_vals = [r["rst_ni"] for r in rows]
    edge_times = rising_edges(clk_vals, times)
    if not edge_times:
        return False, "no_clock_edges"

    sample_times = [edge_t + 1.0e-9 for edge_t in edge_times]
    sampled_rows = sample_rows_at_or_after_times(rows, sample_times, rst_key="rst_ni")

    if len(sampled_rows) < 2:
        return False, f"insufficient_post_reset_samples count={len(sampled_rows)}"

    bad_ptr_rows = 0
    cell_counts: list[int] = []
    overlap_count = 0
    prev_active: set[int] | None = None

    for row in sampled_rows:
        ptr_active = {idx for idx, col in enumerate(ptr_cols) if row[col] > 0.45}
        if len(ptr_active) not in (0, 1):
            bad_ptr_rows += 1

        active_cells = {idx for idx, col in enumerate(cell_cols) if row[col] > 0.45}
        cell_counts.append(len(active_cells))

        if prev_active is not None and prev_active & active_cells:
            overlap_count += 1
        prev_active = active_cells

    cell_active = max(cell_counts) > 0
    ok = bad_ptr_rows == 0 and cell_active and overlap_count == 0
    return ok, (
        f"sampled_cycles={len(sampled_rows)} bad_ptr_rows={bad_ptr_rows} "
        f"max_active_cells={max(cell_counts)} overlap_count={overlap_count}"
    )


def check_dwa_wraparound(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows:
        return False, "no rows"

    keys = set(rows[0].keys())
    required = {"time", "clk_i", "rst_ni", "ptr_0", "cell_en_0", "code_0"}
    if not required.issubset(keys):
        return False, "missing time/clk_i/rst_ni/ptr_0/cell_en_0/code_0"

    ptr_cols = indexed_columns(keys, "ptr_")
    cell_cols = indexed_columns(keys, "cell_en_")
    code_cols = indexed_columns(keys, "code_")
    if len(ptr_cols) != 16 or len(cell_cols) != 16 or len(code_cols) != 4:
        return False, "expected ptr_0..15, cell_en_0..15, and code_0..3 columns"

    times = [r["time"] for r in rows]
    edge_times = rising_edges([r["clk_i"] for r in rows], times)
    sample_times = [edge_t + 1.0e-9 for edge_t in edge_times]
    sampled_rows = sample_rows_at_or_after_times(rows, sample_times, rst_key="rst_ni")

    if len(sampled_rows) < 5:
        return False, f"insufficient_post_reset_samples count={len(sampled_rows)}"

    expected_ptr = 13
    bad_ptr_rows = 0
    bad_count_rows = 0
    wrap_events = 0
    split_wrap_rows = 0
    prev_ptr = expected_ptr

    for row in sampled_rows:
        code = sum(int(row[col] > 0.45) << int(col[5:]) for col in code_cols)
        expected_ptr = (expected_ptr + code) % 16
        if expected_ptr < prev_ptr:
            wrap_events += 1

        ptr_active = [idx for idx, col in enumerate(ptr_cols) if row[col] > 0.45]
        active_cells = {idx for idx, col in enumerate(cell_cols) if row[col] > 0.45}

        if ptr_active != [expected_ptr]:
            bad_ptr_rows += 1
        if len(active_cells) != code:
            bad_count_rows += 1
        if active_cells and (max(active_cells) - min(active_cells) + 1) > len(active_cells):
            split_wrap_rows += 1

        prev_ptr = expected_ptr

    ok = bad_ptr_rows == 0 and bad_count_rows == 0 and wrap_events >= 2 and split_wrap_rows >= 2
    return ok, (
        f"sampled_cycles={len(sampled_rows)} bad_ptr_rows={bad_ptr_rows} "
        f"bad_count_rows={bad_count_rows} wrap_events={wrap_events} "
        f"split_wrap_rows={split_wrap_rows}"
    )


def check_dwa_dem_encoder_release(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows:
        return False, "no rows"

    keys = set(rows[0].keys())
    required = {"time", "clk_i", "rst_ni", "ptr_0", "cell_en_0", "code_0"}
    if not required.issubset(keys):
        return False, "missing time/clk_i/rst_ni/ptr_0/cell_en_0/code_0"

    ptr_cols = indexed_columns(keys, "ptr_")
    cell_cols = indexed_columns(keys, "cell_en_")
    code_cols = indexed_columns(keys, "code_")
    if len(ptr_cols) != 16 or len(cell_cols) != 16 or len(code_cols) != 4:
        return False, "expected ptr_0..15, cell_en_0..15, and code_0..3 columns"

    times = [r["time"] for r in rows]
    edge_times = rising_edges([r["clk_i"] for r in rows], times)
    sampled_rows = sample_rows_at_or_after_times(rows, [t + 1.0e-9 for t in edge_times], rst_key="rst_ni")
    if len(sampled_rows) < 5:
        return False, f"insufficient_post_reset_samples count={len(sampled_rows)}"

    ptr = 0
    previous_code: int | None = None
    bad_ptr_rows = 0
    bad_span_rows = 0
    wrap_events = 0
    split_wrap_rows = 0
    active_counts: list[int] = []
    ptr_sequence: list[int] = []

    for row_idx, row in enumerate(sampled_rows):
        row_code = sum(int(row[col] > 0.45) << int(col[5:]) for col in code_cols)
        effective_code = row_code if previous_code is None else previous_code
        prev_ptr = ptr
        ptr = (ptr + effective_code) % 16
        if row_idx > 0 and ptr < prev_ptr:
            wrap_events += 1

        ptr_active = [idx for idx, col in enumerate(ptr_cols) if row[col] > 0.45]
        if ptr_active != [ptr]:
            bad_ptr_rows += 1

        # The release gold emits an MSB span plus the LSB boundary unit, so a
        # code of N drives a contiguous circular run of N+1 active cells ending
        # at the pointer.
        expected_cells = {(ptr - offset) % 16 for offset in range(effective_code + 1)}
        active_cells = {idx for idx, col in enumerate(cell_cols) if row[col] > 0.45}
        active_counts.append(len(active_cells))
        if active_cells != expected_cells:
            bad_span_rows += 1
        if active_cells and (max(active_cells) - min(active_cells) + 1) > len(active_cells):
            split_wrap_rows += 1

        ptr_sequence.append(ptr)
        previous_code = row_code

    ok = (
        bad_ptr_rows == 0
        and bad_span_rows == 0
        and wrap_events >= 2
        and split_wrap_rows >= 2
        and len(set(ptr_sequence)) >= 5
        and max(active_counts) >= 8
    )
    return ok, (
        f"sampled_cycles={len(sampled_rows)} bad_ptr_rows={bad_ptr_rows} "
        f"bad_span_rows={bad_span_rows} ptr_unique={len(set(ptr_sequence))} "
        f"wrap_events={wrap_events} split_wrap_rows={split_wrap_rows} "
        f"max_active_cells={max(active_counts)}"
    )


def check_clk_burst_gen(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows or not {"CLK", "RST_N", "CLK_OUT"}.issubset(rows[0]):
        return False, "missing CLK/RST_N/CLK_OUT"
    vth = 0.45
    post = [r for r in rows if r["RST_N"] > 0.45]
    if len(post) < 4:
        return False, "no post-reset samples"

    times = [r["time"] for r in post]
    clk = [r["CLK"] for r in post]
    edge_idx = [i for i in range(1, len(post)) if clk[i - 1] < vth <= clk[i]]
    if len(edge_idx) < 16:
        return False, f"too_few_post_reset_clk_edges={len(edge_idx)}"

    periods = [times[edge_idx[i + 1]] - times[edge_idx[i]] for i in range(len(edge_idx) - 1)]
    positive_periods = sorted(period for period in periods if period > 0)
    if not positive_periods:
        return False, "cannot_estimate_clk_period"
    period = positive_periods[len(positive_periods) // 2]

    def sample_at_or_after(target_t: float, limit_t: float | None = None) -> dict[str, float] | None:
        for row in post:
            t = row["time"]
            if t >= target_t and (limit_t is None or t < limit_t):
                return row
        return None

    high_phase_failures = 0
    low_phase_failures = 0
    checked_cycles = 0
    enabled_cycles = 0
    disabled_cycles = 0

    # Contract for the release task/testbench: div=8, pass cycles 0 and 1,
    # suppress cycles 2..7, then repeat. Sample away from transitions so the
    # checker is not sensitive to simulator breakpoint placement.
    for cycle_idx, edge in enumerate(edge_idx[:-1]):
        edge_t = times[edge]
        next_edge_t = times[edge_idx[cycle_idx + 1]]
        frame_pos = cycle_idx % 8
        should_pass = frame_pos < 2

        high_sample = sample_at_or_after(edge_t + 0.25 * period, next_edge_t)
        low_sample = sample_at_or_after(edge_t + 0.75 * period, next_edge_t)
        if high_sample is None or low_sample is None:
            continue

        checked_cycles += 1
        if should_pass:
            enabled_cycles += 1
            if high_sample["CLK_OUT"] <= vth:
                high_phase_failures += 1
        else:
            disabled_cycles += 1
            if high_sample["CLK_OUT"] > vth:
                high_phase_failures += 1
        if low_sample["CLK_OUT"] > vth:
            low_phase_failures += 1

    ok = (
        checked_cycles >= 16
        and enabled_cycles >= 4
        and disabled_cycles >= 8
        and high_phase_failures == 0
        and low_phase_failures == 0
    )
    return ok, (
        f"burst_cycles_checked={checked_cycles} enabled_cycles={enabled_cycles} "
        f"disabled_cycles={disabled_cycles} high_phase_failures={high_phase_failures} "
        f"low_phase_failures={low_phase_failures}"
    )


def check_noise_gen(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows or not {"vin_i", "vout_o"}.issubset(rows[0]):
        return False, "missing vin_i/vout_o"
    noises = [r["vout_o"] - r["vin_i"] for r in rows]
    mean = sum(noises) / len(noises)
    var = sum((x - mean) ** 2 for x in noises) / len(noises)
    std = var ** 0.5
    ok = std > 0.01 and max(abs(x) for x in noises) > 0.05
    return ok, f"noise_std={std:.4f}"


def check_gain_extraction(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows or not {"vinp", "vinn", "vamp_p", "vamp_n"}.issubset(rows[0]):
        return False, "missing vinp/vinn/vamp_p/vamp_n"
    vin_diff = [r["vinp"] - r["vinn"] for r in rows]
    vamp_diff = [r["vamp_p"] - r["vamp_n"] for r in rows]
    mean_in = sum(vin_diff) / len(vin_diff)
    mean_out = sum(vamp_diff) / len(vamp_diff)
    std_in = (sum((x - mean_in) ** 2 for x in vin_diff) / len(vin_diff)) ** 0.5
    std_out = (sum((x - mean_out) ** 2 for x in vamp_diff) / len(vamp_diff)) ** 0.5
    gain = std_out / std_in if std_in > 1e-12 else 0.0
    ok = gain > 4.0 and std_out > std_in
    return ok, f"diff_gain={gain:.2f}"


def check_gain_estimator(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vinp", "vinn", "voutp", "voutn", "gain_out", "valid"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/vinp/vinn/voutp/voutn/gain_out/valid"

    valid_rows = [row for row in rows if row["valid"] > 0.45]
    if len(valid_rows) < 20:
        return False, f"insufficient_valid_samples={len(valid_rows)}"

    late_start = rows[-1]["time"] * 0.65
    late = [row for row in rows if row["time"] >= late_start]
    late_valid = [row for row in late if row["valid"] > 0.45]
    if len(late_valid) < 10:
        return False, f"late_valid_samples={len(late_valid)}"

    vin_diff = [row["vinp"] - row["vinn"] for row in late_valid]
    vout_diff = [row["voutp"] - row["voutn"] for row in late_valid]
    in_span = max(vin_diff) - min(vin_diff)
    out_span = max(vout_diff) - min(vout_diff)
    waveform_gain = out_span / in_span if in_span > 1e-12 else 0.0

    vdd_est = max(max(row["valid"] for row in rows), 1e-6)
    gain_estimates = [row["gain_out"] / vdd_est * 10.0 for row in late_valid]
    gain_est = sum(gain_estimates) / len(gain_estimates)
    gain_err = abs(gain_est - waveform_gain)

    valid_final = rows[-1]["valid"] > 0.45
    ok = (
        valid_final
        and 0.045 <= in_span <= 0.075
        and 0.27 <= out_span <= 0.45
        and 5.0 <= waveform_gain <= 7.2
        and gain_err <= 0.35
    )
    return ok, (
        f"in_span={in_span:.4f} out_span={out_span:.4f} "
        f"waveform_gain={waveform_gain:.2f} gain_est={gain_est:.2f} "
        f"gain_err={gain_err:.2f} valid_final={valid_final}"
    )


def check_adpll_lock(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"ref_clk", "fb_clk", "lock", "vctrl_mon"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing ref_clk/fb_clk/lock/vctrl_mon"

    times = [r["time"] for r in rows]
    ref_edges = rising_edges([r["ref_clk"] for r in rows], times)
    fb_edges = rising_edges([r["fb_clk"] for r in rows], times)
    lock_edges = rising_edges([r["lock"] for r in rows], times)

    if len(ref_edges) < 8 or len(fb_edges) < 8:
        return False, f"not_enough_edges ref={len(ref_edges)} fb={len(fb_edges)}"

    t_end = times[-1]
    t_start = t_end * 0.8
    ref_late = [t for t in ref_edges if t_start <= t <= t_end]
    fb_late = [t for t in fb_edges if t_start <= t <= t_end]
    if not ref_late or not fb_late:
        return False, "missing late-window edges"

    ratio = len(fb_late) / max(len(ref_late), 1)
    lock_ok = bool(lock_edges) and lock_edges[0] <= 1.0e-6
    vctrl_vals = [r["vctrl_mon"] for r in rows]
    vctrl_in_range = all(-1e-6 <= v <= 1.2 for v in vctrl_vals)
    freq_ok = 0.95 <= ratio <= 1.05
    ok = freq_ok and lock_ok and vctrl_in_range
    return ok, (
        f"late_edge_ratio={ratio:.3f} "
        f"lock_time={(lock_edges[0] if lock_edges else float('nan')):.3e} "
        f"vctrl_range_ok={vctrl_in_range}"
    )


def edge_frequency_ratio(
    rows: list[dict[str, float]],
    num_signal: str,
    den_signal: str,
    t_start: float,
    t_end: float,
) -> tuple[float, str]:
    window = time_window(rows, t_start, t_end)
    if len(window) < 4 or num_signal not in window[0] or den_signal not in window[0]:
        return float("nan"), "missing_window_or_signals"

    times = [r["time"] for r in window]
    num_edges = rising_edges([r[num_signal] for r in window], times)
    den_edges = rising_edges([r[den_signal] for r in window], times)
    if len(num_edges) < 3 or len(den_edges) < 3:
        return float("nan"), f"not_enough_edges num={len(num_edges)} den={len(den_edges)}"

    num_freq = (len(num_edges) - 1) / max(num_edges[-1] - num_edges[0], 1e-18)
    den_freq = (len(den_edges) - 1) / max(den_edges[-1] - den_edges[0], 1e-18)
    return num_freq / max(den_freq, 1e-18), "ok"


def first_threshold_crossing(rows: list[dict[str, float]], signal: str, threshold: float) -> float:
    if not rows or signal not in rows[0]:
        return float("nan")
    prev = rows[0][signal]
    for row in rows[1:]:
        cur = row[signal]
        if prev < threshold <= cur:
            return row["time"]
        prev = cur
    return float("nan")


def check_adpll_ratio_hop(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"ref_clk", "ratio_ctrl", "fb_clk", "vout", "lock", "vctrl_mon"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing ref_clk/ratio_ctrl/fb_clk/vout/lock/vctrl_mon"

    hop_t = first_threshold_crossing(rows, "ratio_ctrl", 5.0)
    if not math.isfinite(hop_t):
        return False, "ratio_hop_not_detected"

    pre_ratio, pre_note = edge_frequency_ratio(rows, "vout", "ref_clk", hop_t - 1.0e-6, hop_t - 2.0e-7)
    post_ratio, post_note = edge_frequency_ratio(rows, "vout", "ref_clk", hop_t + 1.2e-6, hop_t + 2.5e-6)
    pre_div_ratio, pre_div_note = edge_frequency_ratio(rows, "vout", "fb_clk", hop_t - 1.0e-6, hop_t - 2.0e-7)
    post_div_ratio, post_div_note = edge_frequency_ratio(rows, "vout", "fb_clk", hop_t + 1.2e-6, hop_t + 2.5e-6)
    pre_fb_ref_ratio, pre_fb_ref_note = edge_frequency_ratio(rows, "fb_clk", "ref_clk", hop_t - 1.0e-6, hop_t - 2.0e-7)
    post_fb_ref_ratio, post_fb_ref_note = edge_frequency_ratio(rows, "fb_clk", "ref_clk", hop_t + 1.2e-6, hop_t + 2.5e-6)
    if pre_note != "ok":
        return False, f"pre_window_{pre_note}"
    if post_note != "ok":
        return False, f"post_window_{post_note}"
    if pre_div_note != "ok":
        return False, f"pre_divider_window_{pre_div_note}"
    if post_div_note != "ok":
        return False, f"post_divider_window_{post_div_note}"
    if pre_fb_ref_note != "ok":
        return False, f"pre_feedback_window_{pre_fb_ref_note}"
    if post_fb_ref_note != "ok":
        return False, f"post_feedback_window_{post_fb_ref_note}"

    vth = max(r["lock"] for r in rows) * 0.5 if rows else 0.45
    pre_lock = weighted_logic_high_fraction_window(rows, "lock", vth, hop_t - 4.0e-7, hop_t - 5.0e-8)
    post_lock = weighted_logic_high_fraction_window(rows, "lock", vth, hop_t + 1.8e-6, hop_t + 2.8e-6)
    vctrl_vals = [r["vctrl_mon"] for r in rows]
    vctrl_in_range = all(-1e-6 <= v <= 1.2 for v in vctrl_vals)

    ok = (
        abs(pre_ratio - 4.0) <= 0.25
        and abs(post_ratio - 6.0) <= 0.35
        and abs(pre_div_ratio - 4.0) <= 0.25
        and abs(post_div_ratio - 6.0) <= 0.35
        and abs(pre_fb_ref_ratio - 1.0) <= 0.15
        and abs(post_fb_ref_ratio - 1.0) <= 0.15
        and pre_lock >= 0.8
        and post_lock >= 0.8
        and vctrl_in_range
    )
    return ok, (
        f"hop_t={hop_t:.3e} "
        f"pre_vout_ref={pre_ratio:.3f} "
        f"post_vout_ref={post_ratio:.3f} "
        f"pre_vout_fb={pre_div_ratio:.3f} "
        f"post_vout_fb={post_div_ratio:.3f} "
        f"pre_fb_ref={pre_fb_ref_ratio:.3f} "
        f"post_fb_ref={post_fb_ref_ratio:.3f} "
        f"pre_lock={pre_lock:.3f} "
        f"post_lock={post_lock:.3f} "
        f"vctrl_range_ok={vctrl_in_range}"
    )


def check_cppll_tracking(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"ref_clk", "fb_clk", "lock", "vctrl_mon"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing ref_clk/fb_clk/lock/vctrl_mon"

    times = [r["time"] for r in rows]
    ref_edges = rising_edges([r["ref_clk"] for r in rows], times)
    fb_edges = rising_edges([r["fb_clk"] for r in rows], times)
    lock_edges = rising_edges([r["lock"] for r in rows], times)

    if len(ref_edges) < 8 or len(fb_edges) < 8:
        return False, f"not_enough_edges ref={len(ref_edges)} fb={len(fb_edges)}"

    t_end = times[-1]
    t_start = t_end * 0.8
    ref_late = [t for t in ref_edges if t_start <= t <= t_end]
    fb_late = [t for t in fb_edges if t_start <= t <= t_end]
    if len(ref_late) < 4 or len(fb_late) < 4:
        return False, "not_enough_late_edges"

    ref_periods = [b - a for a, b in zip(ref_late, ref_late[1:])]
    fb_periods = [b - a for a, b in zip(fb_late, fb_late[1:])]
    ref_period = sum(ref_periods) / len(ref_periods)
    fb_period = sum(fb_periods) / len(fb_periods)
    if ref_period <= 0.0 or fb_period <= 0.0:
        return False, "non_positive_period"

    freq_ratio = ref_period / fb_period
    fb_jitter = max(fb_periods) - min(fb_periods)
    fb_jitter_frac = fb_jitter / fb_period if fb_period > 0.0 else float("inf")
    vctrl_vals = [r["vctrl_mon"] for r in rows]
    vctrl_min = min(vctrl_vals)
    vctrl_max = max(vctrl_vals)
    vctrl_in_range = all(-1e-6 <= v <= 0.95 for v in vctrl_vals)
    lock_vmax = max(r["lock"] for r in rows)
    lock_vth = max(0.45, lock_vmax * 0.5)
    late_lock_frac = weighted_logic_high_fraction_window(rows, "lock", lock_vth, t_start, t_end)
    freq_ok = 0.97 <= freq_ratio <= 1.03
    stability_ok = fb_jitter_frac <= 0.10
    late_lock_ok = late_lock_frac >= 0.75
    ok = freq_ok and stability_ok and late_lock_ok and vctrl_in_range
    return ok, (
        f"freq_ratio={freq_ratio:.4f} "
        f"fb_jitter_frac={fb_jitter_frac:.4f} "
        f"late_lock_frac={late_lock_frac:.3f} "
        f"lock_time={(lock_edges[0] if lock_edges else float('nan')):.3e} "
        f"vctrl_min={vctrl_min:.3f} "
        f"vctrl_max={vctrl_max:.3f}"
    )


def check_sample_hold(rows: list[dict[str, float]]) -> tuple[bool, str]:
    """S&H: output steps at clock edges, held between them."""
    if not rows or not {"in", "clk", "out"}.issubset(rows[0]):
        return False, "missing in/clk/out columns"
    vth = 0.45
    times = [r["time"] for r in rows]
    clk  = [r["clk"]  for r in rows]
    vin  = [r["in"]   for r in rows]
    vout = [r["out"]  for r in rows]
    edge_idx = [i for i in range(1, len(clk)) if clk[i - 1] <= vth < clk[i]]
    if len(edge_idx) < 10:
        return False, f"too_few_clock_edges={len(edge_idx)}"
    # Check hold stability: for 3 consecutive hold windows, skip 2ns after edge, stop 2ns before next
    for i in range(min(3, len(edge_idx) - 1)):
        t_start = times[edge_idx[i]] + 2e-9
        t_end   = times[edge_idx[i + 1]] - 2e-9
        window = [vout[j] for j in range(edge_idx[i], edge_idx[i + 1])
                  if t_start <= times[j] <= t_end]
        if len(window) < 2:
            continue
        jitter = max(window) - min(window)
        if jitter > 0.02:
            return False, f"output_not_held jitter={jitter:.4f}V"
    # Output should track input at edges (settled 2ns after edge)
    mismatches = 0
    for idx in edge_idx[:20]:
        t_settle = times[idx] + 2e-9
        settle_idx = next((j for j in range(idx, len(times)) if times[j] >= t_settle), idx)
        if abs(vout[settle_idx] - vin[idx]) > 0.015:
            mismatches += 1
    if mismatches > 4:
        return False, f"sample_mismatch={mismatches}/20"
    return True, f"edges={len(edge_idx)} hold_ok"


def check_sample_hold_droop(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"vin", "clk", "vout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing vin/clk/vout"

    vth = 0.45
    times = [r["time"] for r in rows]
    clk = [r["clk"] for r in rows]
    vin = [r["vin"] for r in rows]
    vout = [r["vout"] for r in rows]
    edge_idx = [i for i in range(1, len(clk)) if clk[i - 1] <= vth < clk[i]]

    if len(edge_idx) < 6:
        return False, f"too_few_clock_edges={len(edge_idx)}"

    sample_mismatch = 0
    checked_samples = 0
    for i in range(min(6, len(edge_idx) - 1)):
        idx = edge_idx[i]
        t_target = times[idx] + 1.2e-9
        settle_idx = next((j for j in range(idx, len(rows)) if times[j] >= t_target), len(rows) - 1)
        err = abs(vout[settle_idx] - vin[idx])
        checked_samples += 1
        if err > 0.04:
            sample_mismatch += 1
    if checked_samples == 0 or sample_mismatch > 1:
        return False, f"sample_mismatch={sample_mismatch}/{max(checked_samples, 1)}"

    droop_windows = 0
    droop_failures = 0
    for i in range(min(6, len(edge_idx) - 1)):
        start_i = edge_idx[i]
        end_i = edge_idx[i + 1]
        t_start = times[start_i] + 1.5e-9
        t_end = times[end_i] - 1.5e-9
        idxs = [j for j in range(start_i, end_i) if t_start <= times[j] <= t_end]
        if len(idxs) < 6:
            continue
        first = vout[idxs[0]]
        if first < 0.55:
            continue
        last = vout[idxs[-1]]
        droop = first - last
        upward_steps = sum(1 for a, b in zip(idxs[:-1], idxs[1:]) if (vout[b] - vout[a]) > 0.004)
        droop_windows += 1
        if droop < 0.006 or droop > 0.30:
            droop_failures += 1
        if upward_steps > max(1, len(idxs) // 8):
            droop_failures += 1

    if droop_windows < 2:
        return False, f"insufficient_high_hold_windows={droop_windows}"
    if droop_failures > 0:
        return False, f"droop_failures={droop_failures} windows={droop_windows}"

    return True, (
        f"edges={len(edge_idx)} "
        f"sample_mismatch={sample_mismatch}/{checked_samples} "
        f"droop_windows={droop_windows}"
    )


def check_release_vin_sampled_droop_hold(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "sample", "rst", "vin", "vout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/sample/rst/vin/vout"

    times = [r["time"] for r in rows]
    sample_edges = _threshold_crossings([r["sample"] for r in rows], times, threshold=0.45, direction="rising")
    if len(sample_edges) < 3:
        return False, f"too_few_sample_edges={len(sample_edges)}"

    expected: list[float] = []
    observed: list[float] = []
    errors: list[float] = []
    for edge_t in sample_edges[:3]:
        want = sample_signal_at(rows, "vin", edge_t + 0.05e-9)
        got = sample_signal_at(rows, "vout", edge_t + 1.20e-9)
        if want is None or got is None:
            return False, f"missing_sample_window_at={edge_t:.3e}"
        expected.append(want)
        observed.append(got)
        errors.append(abs(got - want))

    max_err = max(errors)
    expected_span = max(expected) - min(expected)
    observed_span = max(observed) - min(observed)
    sample_match = max_err <= 0.045 and expected_span >= 0.35 and observed_span >= 0.30

    # Use the high second sample as the droop window; reset begins well after it.
    second_edge = sample_edges[1]
    droop_start_t = second_edge + 2.0e-9
    reset_edges = _threshold_crossings([r["rst"] for r in rows], times, threshold=0.45, direction="rising")
    droop_end_t = (reset_edges[0] - 2.0e-9) if reset_edges else (second_edge + 35.0e-9)
    droop_values = [r["vout"] for r in rows if droop_start_t <= r["time"] <= droop_end_t]
    if len(droop_values) < 8:
        return False, f"insufficient_droop_window_samples={len(droop_values)}"
    droop = droop_values[0] - droop_values[-1]
    upward_steps = sum(1 for a, b in zip(droop_values[:-1], droop_values[1:]) if b - a > 0.004)
    droop_ok = 0.04 <= droop <= 0.45 and upward_steps <= max(1, len(droop_values) // 10)

    reset_t = reset_edges[0] if reset_edges else 125.0e-9
    reset_sample = sample_signal_at(rows, "vout", reset_t + 8.0e-9)
    reset_clear = reset_sample is not None and reset_sample < 0.05

    ok = sample_match and droop_ok and reset_clear
    exp_text = ",".join(f"{value:.3f}" for value in expected)
    obs_text = ",".join(f"{value:.3f}" for value in observed)
    return ok, (
        f"vin_samples={exp_text} held_samples={obs_text} "
        f"max_sample_err={max_err:.3f} expected_span={expected_span:.3f} "
        f"observed_span={observed_span:.3f} droop={droop:.3f} "
        f"upward_steps={upward_steps} reset_clear={reset_clear}"
    )


def check_release_converter_front_end_chain(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vin", "clk", "vout", "valid", "coarse"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/vin/clk/vout/valid/coarse"

    times = [r["time"] for r in rows]
    clk_edges = _threshold_crossings([r["clk"] for r in rows], times, threshold=0.45, direction="rising")
    if len(clk_edges) < 6:
        return False, f"too_few_clk_edges={len(clk_edges)}"

    sample_errors: list[float] = []
    coarse_mismatches = 0
    valid_hits = 0
    valid_low_hits = 0
    aperture_sensitive = 0
    for edge_t in clk_edges[:8]:
        vin_edge = sample_signal_at(rows, "vin", edge_t)
        vin_aperture = sample_signal_at(rows, "vin", edge_t + 0.20e-9)
        vout_settled = sample_signal_at(rows, "vout", edge_t + 1.00e-9)
        valid_high = sample_signal_at(rows, "valid", edge_t + 0.80e-9)
        valid_low = sample_signal_at(rows, "valid", edge_t + 3.50e-9)
        coarse = sample_signal_at(rows, "coarse", edge_t + 1.00e-9)
        if None in (vin_edge, vin_aperture, vout_settled, valid_high, valid_low, coarse):
            return False, f"missing_front_end_sample_at={edge_t:.3e}"
        assert vin_edge is not None and vin_aperture is not None and vout_settled is not None
        assert valid_high is not None and valid_low is not None and coarse is not None
        sample_errors.append(abs(vout_settled - vin_aperture))
        expected_coarse_high = vin_aperture > 0.45
        if (coarse > 0.45) != expected_coarse_high:
            coarse_mismatches += 1
        if valid_high > 0.45:
            valid_hits += 1
        if valid_low < 0.45:
            valid_low_hits += 1
        if abs(vin_aperture - vin_edge) > 0.18 and abs(vout_settled - vin_aperture) + 0.08 < abs(vout_settled - vin_edge):
            aperture_sensitive += 1

    max_sample_err = max(sample_errors)
    sample_ok = max_sample_err <= 0.055
    coarse_ok = coarse_mismatches == 0
    valid_ok = valid_hits >= 6 and valid_low_hits >= 6
    aperture_ok = aperture_sensitive >= 2

    droop_windows = 0
    droop_failures = 0
    for start_t, end_t in zip(clk_edges[:7], clk_edges[1:8]):
        t_start = start_t + 2.0e-9
        t_end = end_t - 2.0e-9
        idxs = [idx for idx, row in enumerate(rows) if t_start <= row["time"] <= t_end]
        if len(idxs) < 8:
            continue
        first = rows[idxs[0]]["vout"]
        if first < 0.55:
            continue
        last = rows[idxs[-1]]["vout"]
        droop = first - last
        upward_steps = sum(1 for a, b in zip(idxs[:-1], idxs[1:]) if rows[b]["vout"] - rows[a]["vout"] > 0.004)
        droop_windows += 1
        if not (0.004 <= droop <= 0.16) or upward_steps > max(1, len(idxs) // 8):
            droop_failures += 1

    droop_ok = droop_windows >= 2 and droop_failures == 0
    ok = sample_ok and coarse_ok and valid_ok and aperture_ok and droop_ok
    return ok, (
        f"edges={len(clk_edges)} max_sample_err={max_sample_err:.3f} "
        f"coarse_mismatches={coarse_mismatches} valid_high_hits={valid_hits} "
        f"valid_low_hits={valid_low_hits} aperture_sensitive={aperture_sensitive} "
        f"droop_windows={droop_windows} droop_failures={droop_failures}"
    )


def check_flash_adc_3b(rows: list[dict[str, float]]) -> tuple[bool, str]:
    """3-bit flash ADC: all 8 codes present, monotonic with ramp input."""
    if not rows or not {"vin", "clk", "dout2", "dout1", "dout0"}.issubset(rows[0]):
        return False, "missing vin/clk/dout2/dout1/dout0"
    vth = 0.45
    clk = [r["clk"] for r in rows]
    edge_idx = [i for i in range(1, len(clk)) if clk[i - 1] <= vth < clk[i]]
    if len(edge_idx) < 20:
        return False, f"too_few_edges={len(edge_idx)}"
    codes = []
    for idx in edge_idx:
        settle = min(idx + 5, len(rows) - 1)
        c = (int(rows[settle]["dout2"] > vth) << 2 |
             int(rows[settle]["dout1"] > vth) << 1 |
             int(rows[settle]["dout0"] > vth))
        codes.append(c)
    unique = set(codes)
    if len(unique) < 8:
        return False, f"only_{len(unique)}_codes (need 8)"
    # monotonicity: fewer than 5% reversals
    reversals = sum(1 for i in range(1, len(codes)) if codes[i] < codes[i - 1] - 1)
    if reversals > len(codes) * 0.05:
        return False, f"not_monotonic reversals={reversals}"
    return True, f"codes={len(unique)}/8 reversals={reversals}"


_RELEASE_FLASH_ADC_CMP_COLS = tuple(f"cmp{idx}" for idx in range(7))
_RELEASE_FLASH_ADC_BIT_COLS = ("dout0", "dout1", "dout2")


def check_release_flash_adc_mini_array(rows: list[dict[str, float]]) -> tuple[bool, str]:
    """Release flash ADC mini-array: seven comparator decisions plus encoder."""
    required = {"time", "vin", "clk", "dout0", "dout1", "dout2", *_RELEASE_FLASH_ADC_CMP_COLS}
    if not rows or not required.issubset(rows[0]):
        missing = sorted(required - set(rows[0].keys())) if rows else sorted(required)
        return False, f"missing_columns={','.join(missing)}"

    vth = 0.45
    times = [r["time"] for r in rows]
    edge_times = rising_edges([r["clk"] for r in rows], times, threshold=vth)
    sample_rows = sample_rows_at_or_after_times(rows, [edge_t + 0.5e-9 for edge_t in edge_times])
    if len(sample_rows) < 8:
        return False, f"too_few_settled_samples={len(sample_rows)}"

    thresholds = [(idx + 1) * 0.9 / 8.0 for idx in range(7)]
    observed_codes: list[int] = []
    expected_codes: list[int] = []
    comparator_mismatches = 0
    thermometer_errors = 0
    encoder_mismatches = 0
    out_of_range = 0

    for row in sample_rows:
        vin = row["vin"]
        expected_cmp = [1 if vin >= threshold - 1e-6 else 0 for threshold in thresholds]
        observed_cmp = [1 if row[col] >= vth else 0 for col in _RELEASE_FLASH_ADC_CMP_COLS]
        expected_code = sum(expected_cmp)
        observed_code = (
            (1 if row["dout0"] >= vth else 0)
            | ((1 if row["dout1"] >= vth else 0) << 1)
            | ((1 if row["dout2"] >= vth else 0) << 2)
        )

        if observed_cmp != expected_cmp:
            comparator_mismatches += 1
        if any(lo < hi for lo, hi in zip(observed_cmp, observed_cmp[1:])):
            thermometer_errors += 1
        if observed_code != sum(observed_cmp):
            encoder_mismatches += 1
        if not 0 <= observed_code <= 7:
            out_of_range += 1
        observed_codes.append(observed_code)
        expected_codes.append(expected_code)

    observed_unique = sorted(set(observed_codes))
    expected_unique = sorted(set(expected_codes))
    reversals = sum(1 for prev, curr in zip(observed_codes, observed_codes[1:]) if curr < prev)
    ok = (
        observed_unique == list(range(8))
        and expected_unique == list(range(8))
        and comparator_mismatches == 0
        and thermometer_errors == 0
        and encoder_mismatches == 0
        and out_of_range == 0
        and reversals == 0
    )
    return ok, (
        f"observed_codes={','.join(str(c) for c in observed_unique)} "
        f"expected_codes={','.join(str(c) for c in expected_unique)} "
        f"comparator_mismatches={comparator_mismatches} "
        f"thermometer_errors={thermometer_errors} "
        f"encoder_mismatches={encoder_mismatches} "
        f"reversals={reversals}"
    )


def check_serializer_8b(rows: list[dict[str, float]]) -> tuple[bool, str]:
    """8-bit P2S: verify 0xA5 bit sequence MSB-first after LOAD."""
    if not rows or not {"load", "clk", "sout"}.issubset(rows[0]):
        return False, "missing load/clk/sout"
    vth = 0.45
    load = [r["load"] for r in rows]
    clk  = [r["clk"]  for r in rows]
    sout = [r["sout"] for r in rows]
    times = [r["time"] for r in rows]

    # find LOAD falling edge
    load_fall = next((i for i in range(1, len(load)) if load[i - 1] > vth > load[i]), None)
    if load_fall is None:
        return False, "LOAD never deasserted"
    expected = [1, 0, 1, 0, 0, 1, 0, 1]  # 0xA5 MSB-first
    load_fall_t = times[load_fall]

    # collect CLK rising edges strictly after LOAD falls
    edges = [
        i for i in range(max(1, load_fall), len(clk))
        if clk[i - 1] <= vth < clk[i] and times[i] > load_fall_t + 1e-15
    ]
    if len(edges) < 7:
        return False, f"only_{len(edges)}_edges_after_load"

    # Sample sout at the middle of the next CLK period (wait for transition to settle)
    # transition() with tedge=100p takes ~100ps to complete, so we need to wait longer
    # CLK period is 5ns, so middle of period is ~2.5ns after edge
    # Find sample index at ~1ns after each edge (enough time for transition)
    edge_bits = []
    for e in edges[:8]:
        edge_t = times[e]
        # Find sample index at edge_t + 1ns (waiting for transition to settle)
        target_t = edge_t + 1e-9
        sample_idx = e
        while sample_idx < len(rows) and times[sample_idx] < target_t:
            sample_idx += 1
        sample_idx = min(sample_idx, len(rows) - 1)
        bit = int(sout[sample_idx] > vth)
        edge_bits.append(bit)

    if len(edge_bits) < 8:
        return False, f"only_{len(edge_bits)}_sampled_bits"
    mismatches = sum(1 for a, b in zip(edge_bits, expected) if a != b)
    if mismatches > 1:
        return False, f"bit_mismatch expected={expected} got={edge_bits}"
    return True, f"0xA5_serialized_ok mode=edge_only mismatches={mismatches}"


def check_serializer_frame_alignment(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"clk", "frame", "sout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing clk/frame/sout"

    vth = 0.45
    times = [r["time"] for r in rows]
    clk = [r["clk"] for r in rows]
    frame = [r["frame"] for r in rows]
    sout = [r["sout"] for r in rows]

    clk_edges = [i for i in range(1, len(rows)) if clk[i - 1] <= vth < clk[i]]
    frame_rise = [i for i in range(1, len(rows)) if frame[i - 1] <= vth < frame[i]]
    frame_fall = [i for i in range(1, len(rows)) if frame[i - 1] >= vth > frame[i]]
    if len(frame_rise) < 2:
        return False, f"frame_rises={len(frame_rise)}"
    if len(clk_edges) < 16:
        return False, f"clk_edges={len(clk_edges)}"

    # Estimate bit period from clock edge spacing.
    periods = [times[clk_edges[i]] - times[clk_edges[i - 1]] for i in range(1, min(len(clk_edges), 10))]
    periods = [p for p in periods if p > 0.0]
    if not periods:
        return False, "invalid_clk_period"
    period = sorted(periods)[len(periods) // 2]

    expected_words = [0xA5, 0x3C]
    mismatch_total = 0
    detail_parts: list[str] = []

    for frame_idx, expected_word in enumerate(expected_words):
        t_frame = times[frame_rise[frame_idx]]
        clk_edge_times = [times[idx] for idx in clk_edges]
        near = [i for i, t_edge in enumerate(clk_edge_times) if abs(t_edge - t_frame) <= 0.6 * period]
        if near:
            start_pos = min(near, key=lambda i: abs(clk_edge_times[i] - t_frame))
        else:
            start_pos = next((i for i, t_edge in enumerate(clk_edge_times) if t_edge >= t_frame), None)
            if start_pos is None:
                return False, f"frame{frame_idx}_no_clk_after_frame"
        bit_edges = clk_edge_times[start_pos:start_pos + 8]
        if len(bit_edges) < 8:
            return False, f"frame{frame_idx}_insufficient_bits={len(bit_edges)}"

        expected_bits = [((expected_word >> bit) & 1) for bit in range(7, -1, -1)]
        observed_bits: list[int] = []
        for t_edge in bit_edges:
            t_sample = t_edge + 0.8e-9
            sample_idx = next((i for i, t in enumerate(times) if t >= t_sample), len(rows) - 1)
            observed_bits.append(1 if sout[sample_idx] > vth else 0)
        mismatches = sum(1 for a, b in zip(observed_bits, expected_bits) if a != b)
        mismatch_total += mismatches
        detail_parts.append(f"w{frame_idx}_mm={mismatches}")
        if mismatches > 1:
            return False, f"frame{frame_idx}_bit_mismatch exp={expected_bits} got={observed_bits}"

    # Frame pulse width should be around one bit window.
    pulse_widths: list[float] = []
    for r_idx in frame_rise[:2]:
        fall_idx = next((f for f in frame_fall if f > r_idx), None)
        if fall_idx is None:
            return False, "frame_without_fall_edge"
        pulse_widths.append(times[fall_idx] - times[r_idx])
    if any((w < 0.2 * period or w > 1.6 * period) for w in pulse_widths):
        return False, f"frame_pulse_widths={pulse_widths}"

    return True, (
        f"frame_rises={len(frame_rise)} "
        f"period={period:.3e} "
        f"pulse_w={[round(w / period, 2) for w in pulse_widths]} "
        f"{' '.join(detail_parts)} "
        f"mismatch_total={mismatch_total}"
    )


def check_serializer_frame_monitor_flow(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "frame", "sout", "word_ok", "frame_error", "word_mon"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing serializer/frame-monitor observables"

    base_ok, base_note = check_serializer_frame_alignment(rows)
    if not base_ok:
        return False, f"serializer_alignment_failed:{base_note}"

    vth = 0.45
    times = [r["time"] for r in rows]
    word_ok_vals = [r["word_ok"] for r in rows]
    err_vals = [r["frame_error"] for r in rows]
    word_mon_vals = [r["word_mon"] for r in rows]
    ok_edges = rising_edges(word_ok_vals, times, threshold=vth)
    if len(ok_edges) < 2:
        return False, f"word_ok_edges={len(ok_edges)}"
    err_high = sum(1 for val in err_vals if val > vth)
    if err_high:
        return False, f"frame_error_high_samples={err_high}"

    expected_words = [0xA5, 0x3C]
    observed_levels: list[float] = []
    mismatches = 0
    for edge_t, word in zip(ok_edges[:2], expected_words):
        target_t = edge_t + 1.0e-9
        sample_idx = next((idx for idx, t in enumerate(times) if t >= target_t), len(rows) - 1)
        observed = word_mon_vals[sample_idx]
        expected = 0.9 * word / 255.0
        observed_levels.append(observed)
        if abs(observed - expected) > 0.08:
            mismatches += 1
    if mismatches:
        return False, (
            f"word_mon_mismatches={mismatches} "
            f"levels={[round(v, 3) for v in observed_levels]}"
        )

    return True, (
        f"{base_note} word_ok_edges={len(ok_edges)} "
        f"word_mon={[round(v, 3) for v in observed_levels]} frame_error_high=0"
    )


def _first_row_at_or_after(rows: list[dict[str, float]], target_t: float) -> dict[str, float]:
    return next((row for row in rows if row.get("time", 0.0) >= target_t), rows[-1])


def _clock_edges_with_load(rows: list[dict[str, float]], load_key: str = "load", threshold: float = 0.45) -> list[float]:
    if not rows or "clk" not in rows[0] or load_key not in rows[0]:
        return []
    times = [row["time"] for row in rows]
    clk = [row["clk"] for row in rows]
    edges: list[float] = []
    for idx in range(1, len(rows)):
        if clk[idx - 1] < threshold <= clk[idx] and rows[idx].get(load_key, 0.0) > threshold:
            edges.append(times[idx])
    return edges


def check_adc_code_capture_register(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {
        "time", "clk", "load", "over_lo", "over_hi",
        "din3", "din2", "din1", "din0",
        "bit3", "bit2", "bit1", "bit0", "valid", "overrange", "code_mon",
    }
    if not rows or not required.issubset(rows[0]):
        return False, "missing adc code capture observables"

    edges = _clock_edges_with_load(rows)
    if len(edges) < 3:
        return False, f"load_qualified_clk_edges={len(edges)}"

    expected = [(0x3, False), (0xC, False), (0xF, True)]
    mismatches: list[str] = []
    observed: list[str] = []
    for edge_t, (word, over) in zip(edges[:3], expected):
        row = _first_row_at_or_after(rows, edge_t + 1.0e-9)
        level = row["code_mon"]
        want = 0.9 * word / 15.0
        observed.append(f"{word:X}:{level:.3f}/{row['overrange']:.1f}")
        if row["valid"] <= 0.45:
            mismatches.append(f"word{word:X}_valid_low")
        if abs(level - want) > 0.08:
            mismatches.append(f"word{word:X}_code_mon={level:.3f}")
        if (row["overrange"] > 0.45) != over:
            mismatches.append(f"word{word:X}_overrange={row['overrange']:.3f}")
        for bit_idx in range(4):
            bit_val = row[f"bit{bit_idx}"] > 0.45
            if bit_val != bool((word >> bit_idx) & 1):
                mismatches.append(f"word{word:X}_bit{bit_idx}")

    hold_row = _first_row_at_or_after(rows, edges[1] + 15.0e-9)
    if abs(hold_row["code_mon"] - 0.9 * 0xC / 15.0) > 0.08:
        mismatches.append(f"hold_drift_after_second_load={hold_row['code_mon']:.3f}")

    if mismatches:
        return False, ";".join(mismatches)
    return True, f"adc_code_capture_register ok {' '.join(observed)}"


def check_serial_readout_deserializer(rows: list[dict[str, float]]) -> tuple[bool, str]:
    serial_key = "serial_in" if rows and "serial_in" in rows[0] else "sin"
    required = {
        "time", "clk", "frame", serial_key, "bit3", "bit2", "bit1", "bit0", "word_valid", "word_mon",
    }
    if not rows or not required.issubset(rows[0]):
        return False, "missing serial readout deserializer observables"

    times = [row["time"] for row in rows]
    valid_edges = rising_edges([row["word_valid"] for row in rows], times)
    if len(valid_edges) < 2:
        return False, f"word_valid_edges={len(valid_edges)}"

    expected = [0x9, 0x6]
    mismatches: list[str] = []
    observed: list[str] = []
    for edge_t, word in zip(valid_edges[:2], expected):
        row = _first_row_at_or_after(rows, edge_t + 1.0e-9)
        level = row["word_mon"]
        observed.append(f"{word:X}:{level:.3f}")
        if abs(level - 0.9 * word / 15.0) > 0.08:
            mismatches.append(f"word{word:X}_word_mon={level:.3f}")
        for bit_idx in range(4):
            bit_val = row[f"bit{bit_idx}"] > 0.45
            if bit_val != bool((word >> bit_idx) & 1):
                mismatches.append(f"word{word:X}_bit{bit_idx}")

    frame_edges = rising_edges([row["frame"] for row in rows], times)
    if len(frame_edges) < 2:
        mismatches.append(f"frame_edges={len(frame_edges)}")

    if mismatches:
        return False, ";".join(mismatches)
    return True, f"serial_readout_deserializer ok {' '.join(observed)}"


def check_xor_pd(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows or not {"ref", "div", "pd_out"}.issubset(rows[0]):
        return False, "missing ref/div/pd_out"
    vhi = max(max(r["ref"], r["div"], r["pd_out"]) for r in rows)
    vlo = min(min(r["ref"], r["div"], r["pd_out"]) for r in rows)
    vth = vlo + 0.5 * (vhi - vlo)
    pd = [r["pd_out"] for r in rows]
    hi_frac = sum(1 for v in pd if v > vth) / len(pd)
    binary = [1 if v > vth else 0 for v in pd]
    transitions = sum(1 for i in range(1, len(binary)) if binary[i] != binary[i - 1])
    if hi_frac < 0.10:
        return False, f"pd_out_stuck_low hi_frac={hi_frac:.3f}"
    if hi_frac > 0.90:
        return False, f"pd_out_stuck_high hi_frac={hi_frac:.3f}"
    if transitions < 15:
        return False, f"too_few_transitions={transitions}"
    if not (0.30 <= hi_frac <= 0.70):
        return False, f"duty_out_of_range={hi_frac:.3f}"
    stable_margin = max(0.08, 0.20 * (vhi - vlo))
    stable_rows = [
        r
        for r in rows
        if abs(r["ref"] - vth) >= stable_margin
        and abs(r["div"] - vth) >= stable_margin
        and abs(r["pd_out"] - vth) >= stable_margin
    ]
    if len(stable_rows) < max(12, len(rows) // 4):
        return False, f"insufficient_stable_logic_samples={len(stable_rows)}"
    mismatches = sum(
        1
        for r in stable_rows
        if ((r["ref"] > vth) ^ (r["div"] > vth)) != (r["pd_out"] > vth)
    )
    mismatch_frac = mismatches / len(stable_rows)
    if mismatch_frac > 0.05:
        return False, f"xor_mismatch_frac={mismatch_frac:.3f} mismatches={mismatches} stable={len(stable_rows)}"
    return True, f"duty={hi_frac:.3f} transitions={transitions} xor_mismatch_frac={mismatch_frac:.3f}"


def sample_signal_at(rows: list[dict[str, float]], signal: str, time_s: float) -> float | None:
    if not rows or "time" not in rows[0] or signal not in rows[0]:
        return None
    first_time = rows[0]["time"]
    last_time = rows[-1].get("time")
    if last_time is None or time_s < first_time or time_s > last_time:
        return None
    if time_s == first_time:
        return rows[0].get(signal)
    for idx in range(1, len(rows)):
        prev = rows[idx - 1]
        cur = rows[idx]
        t0 = prev.get("time")
        t1 = cur.get("time")
        if t0 is None or t1 is None:
            continue
        if t0 <= time_s <= t1:
            v0 = prev.get(signal)
            v1 = cur.get(signal)
            if v0 is None or v1 is None:
                return None
            if t1 == t0:
                return v1
            alpha = (time_s - t0) / (t1 - t0)
            return v0 + alpha * (v1 - v0)
    return None


def _sample_many(
    rows: list[dict[str, float]],
    samples: dict[str, list[tuple[float, float]]],
    *,
    tol: float,
) -> tuple[bool, str]:
    details: list[str] = []
    for signal, expected_samples in samples.items():
        observed: list[float] = []
        for time_ns, expected in expected_samples:
            value = sample_signal_at(rows, signal, time_ns * 1e-9)
            if value is None:
                return False, f"missing_{signal}_sample_at={time_ns:g}ns"
            observed.append(value)
            if abs(value - expected) > tol:
                return False, (
                    f"{signal}@{time_ns:g}ns={value:.4f} expected={expected:.4f} "
                    f"tol={tol:.4f}"
                )
        details.append(f"{signal}=" + ",".join(f"{value:.3f}" for value in observed))
    return True, " ".join(details)


def check_v3_source_clocked_sar_comparator(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "cmpck", "vinp", "vinn", "dcmpn", "dcmpp"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/cmpck/vinp/vinn/dcmpn/dcmpp"
    return _sample_many(
        rows,
        {
            "dcmpp": [(7.0, 0.9), (17.0, 0.9), (27.0, 0.0), (37.0, 0.9)],
            "dcmpn": [(7.0, 0.0), (17.0, 0.9), (27.0, 0.9), (37.0, 0.9)],
        },
        tol=0.08,
    )


def check_v3_source_clocked_dac_restore_4b(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "d3", "d2", "d1", "d0", "clk", "vout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/d3/d2/d1/d0/clk/vout"
    expected = [
        (6.0, -0.84375),
        (16.0, -0.28125),
        (26.0, 0.28125),
        (36.0, 0.84375),
    ]
    ok, detail = _sample_many(rows, {"vout": expected}, tol=0.02)
    if not ok:
        return ok, detail
    observed = [sample_signal_at(rows, "vout", t_ns * 1e-9) for t_ns, _ in expected]
    if any(value is None for value in observed):
        return False, "missing_vout_samples"
    values = [float(value) for value in observed if value is not None]
    monotonic = all(b > a + 0.20 for a, b in zip(values, values[1:]))
    if not monotonic:
        return False, f"dac_not_monotonic samples={','.join(f'{v:.3f}' for v in values)}"
    return True, detail + " monotonic=True"


def check_v3_source_sample_hold(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vin", "vout", "vclk"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/vin/vout/vclk"
    edge_times_ns = [5.0, 15.0, 25.0, 35.0]
    errors: list[float] = []
    held_spans: list[float] = []
    for edge_ns in edge_times_ns:
        vin_edge = sample_signal_at(rows, "vin", edge_ns * 1e-9)
        vout_settled = sample_signal_at(rows, "vout", (edge_ns + 1.0) * 1e-9)
        if vin_edge is None or vout_settled is None:
            return False, f"missing_sample_near_edge={edge_ns:g}ns"
        errors.append(abs(vout_settled - vin_edge))
    for start_ns, stop_ns in [(7.0, 13.0), (17.0, 23.0), (27.0, 33.0)]:
        values = [
            sample_signal_at(rows, "vout", t_ns * 1e-9)
            for t_ns in (start_ns, 0.5 * (start_ns + stop_ns), stop_ns)
        ]
        if any(value is None for value in values):
            return False, f"missing_hold_window_sample={start_ns:g}-{stop_ns:g}ns"
        numeric = [float(value) for value in values if value is not None]
        held_spans.append(max(numeric) - min(numeric))
    max_error = max(errors)
    max_hold_span = max(held_spans)
    ok = max_error <= 0.025 and max_hold_span <= 0.025
    return ok, f"max_sample_error={max_error:.4f} max_hold_span={max_hold_span:.4f}"


def check_v3_source_single_shot(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vin", "vout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/vin/vout"
    ok, detail = _sample_many(
        rows,
        {
            "vout": [
                (4.0, 0.0),
                (8.0, 0.9),
                (14.0, 0.9),
                (18.0, 0.0),
                (24.0, 0.0),
                (28.0, 0.9),
                (34.0, 0.9),
                (38.0, 0.0),
            ]
        },
        tol=0.08,
    )
    if not ok:
        return ok, detail
    high_samples = [8.0, 14.0, 28.0, 34.0]
    low_samples = [4.0, 18.0, 24.0, 38.0]
    return True, f"{detail} high_windows={high_samples} low_windows={low_samples}"


def check_v3_source_clocked_comparator_reset_low(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "cmpck", "vinp", "vinn", "dcmpn", "dcmpp"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/cmpck/vinp/vinn/dcmpn/dcmpp"
    return _sample_many(
        rows,
        {
            "dcmpp": [(7.0, 0.9), (17.0, 0.0), (27.0, 0.0), (37.0, 0.0)],
            "dcmpn": [(7.0, 0.0), (17.0, 0.0), (27.0, 0.9), (37.0, 0.0)],
        },
        tol=0.08,
    )


def check_v3_source_bipolar_dac_4b_continuous(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vd3", "vd2", "vd1", "vd0", "vout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/vd3/vd2/vd1/vd0/vout"
    expected = [(2.0, -0.9), (12.0, -0.3), (22.0, 0.3), (32.0, 0.9)]
    ok, detail = _sample_many(rows, {"vout": expected}, tol=0.025)
    if not ok:
        return ok, detail
    observed = [float(sample_signal_at(rows, "vout", t_ns * 1e-9) or 0.0) for t_ns, _ in expected]
    monotonic = all(b > a + 0.45 for a, b in zip(observed, observed[1:]))
    if not monotonic:
        return False, f"bipolar_dac_not_monotonic samples={','.join(f'{v:.3f}' for v in observed)}"
    return True, detail + " monotonic=True"


def check_v3_source_clocked_dac_restore_7b(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "d0", "d1", "d2", "d3", "d4", "d5", "d6", "clk", "vout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/d0/d1/d2/d3/d4/d5/d6/clk/vout"
    expected = [
        (6.0, -0.89296875),
        (16.0, -0.30234375),
        (26.0, 0.30234375),
        (36.0, 0.89296875),
    ]
    ok, detail = _sample_many(rows, {"vout": expected}, tol=0.025)
    if not ok:
        return ok, detail
    observed = [float(sample_signal_at(rows, "vout", t_ns * 1e-9) or 0.0) for t_ns, _ in expected]
    monotonic = all(b > a + 0.45 for a, b in zip(observed, observed[1:]))
    if not monotonic:
        return False, f"dac7_not_monotonic samples={','.join(f'{v:.3f}' for v in observed)}"
    return True, detail + " monotonic=True"


def check_v3_source_crossing_pulse_detector(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "sigin", "sigout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/sigin/sigout"
    ok, detail = _sample_many(
        rows,
        {
            "sigout": [
                (4.0, 0.0),
                (7.0, 0.9),
                (12.0, 0.0),
                (17.0, 0.9),
                (22.0, 0.0),
                (27.0, 0.9),
                (32.0, 0.0),
                (37.0, 0.9),
                (42.0, 0.0),
            ]
        },
        tol=0.08,
    )
    return ok, detail


def check_v3_source_not_gate(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vin", "vout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/vin/vout"
    return _sample_many(
        rows,
        {"vout": [(2.0, 0.9), (7.0, 0.0), (17.0, 0.9), (27.0, 0.0), (37.0, 0.9)]},
        tol=0.08,
    )


def check_v3_source_dff_reset(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vin_d", "vclk", "rst", "vout_q", "vout_qbar"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/vin_d/vclk/rst/vout_q/vout_qbar"
    return _sample_many(
        rows,
        {
            "vout_q": [(6.0, 0.9), (16.0, 0.0), (26.0, 0.9), (29.0, 0.0), (36.0, 0.9)],
            "vout_qbar": [(6.0, 0.0), (16.0, 0.9), (26.0, 0.0), (29.0, 0.0), (36.0, 0.0)],
        },
        tol=0.08,
    )


def _sample_differential_sequence(
    rows: list[dict[str, float]],
    pos: str,
    neg: str,
    expected: list[tuple[float, float]],
    *,
    common_mode: float,
    diff_tol: float,
    common_tol: float,
) -> tuple[bool, str]:
    diffs: list[float] = []
    commons: list[float] = []
    for time_ns, expected_diff in expected:
        vp = sample_signal_at(rows, pos, time_ns * 1e-9)
        vn = sample_signal_at(rows, neg, time_ns * 1e-9)
        if vp is None or vn is None:
            return False, f"missing_{pos}_{neg}_sample_at={time_ns:g}ns"
        diff = vp - vn
        cm = 0.5 * (vp + vn)
        diffs.append(diff)
        commons.append(cm)
        if abs(diff - expected_diff) > diff_tol:
            return False, (
                f"{pos}-{neg}@{time_ns:g}ns={diff:.5f} expected={expected_diff:.5f} "
                f"tol={diff_tol:.5f}"
            )
        if abs(cm - common_mode) > common_tol:
            return False, (
                f"common_mode@{time_ns:g}ns={cm:.5f} expected={common_mode:.5f} "
                f"tol={common_tol:.5f}"
            )
    diff_detail = ",".join(f"{value:.5f}" for value in diffs)
    cm_detail = ",".join(f"{value:.4f}" for value in commons)
    return True, f"{pos}-{neg}={diff_detail} cm={cm_detail}"


def check_v3_source_offset_search_comparator(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "vout", "vinp", "vinn"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/clk/vout/vinp/vinn"
    return _sample_differential_sequence(
        rows,
        "vinp",
        "vinn",
        [(8.5, 0.010), (18.5, 0.020), (28.5, 0.015), (38.5, 0.010), (48.5, 0.0125)],
        common_mode=0.45,
        diff_tol=0.0025,
        common_tol=0.0025,
    )


def check_v3_source_start_gated_offset_search(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "start", "vout", "vinp", "vinn"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/clk/start/vout/vinp/vinn"
    return _sample_differential_sequence(
        rows,
        "vinp",
        "vinn",
        [(8.0, 0.000), (18.5, 0.020), (28.5, 0.040), (38.5, 0.030), (48.5, 0.020)],
        common_mode=0.70,
        diff_tol=0.0030,
        common_tol=0.0030,
    )


def check_v3_source_comp_os_detect(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "dcmpp", "vinp", "vinn"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/clk/dcmpp/vinp/vinn"
    return _sample_differential_sequence(
        rows,
        "vinp",
        "vinn",
        [(8.5, -0.1000), (18.5, -0.0500), (28.5, -0.0250), (38.5, -0.0375), (48.5, -0.04375)],
        common_mode=0.45,
        diff_tol=0.0030,
        common_tol=0.0030,
    )


def check_v3_source_clocked_dac_4b_binary(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "d1", "d2", "d3", "d4", "clk", "vout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/d1/d2/d3/d4/clk/vout"
    expected = [(6.0, -0.84375), (16.0, -0.28125), (26.0, 0.28125), (36.0, 0.84375)]
    ok, detail = _sample_many(rows, {"vout": expected}, tol=0.025)
    if not ok:
        return ok, detail
    observed = [float(sample_signal_at(rows, "vout", time_ns * 1e-9) or 0.0) for time_ns, _ in expected]
    monotonic = all(b > a + 0.45 for a, b in zip(observed, observed[1:]))
    if not monotonic:
        return False, f"dac4_binary_not_monotonic samples={','.join(f'{v:.3f}' for v in observed)}"
    return True, detail + " monotonic=True"


def check_v3_source_latched_comparator_delay(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "vinp", "vinn", "dout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/clk/vinp/vinn/dout"
    return _sample_many(
        rows,
        {"dout": [(6.0, 0.9), (16.0, 0.0), (26.0, 0.9), (36.0, 0.0)]},
        tol=0.08,
    )


def check_v3_source_sar_weighted_sum(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "d10", "d9", "d8", "d7", "d6", "d5", "d4", "d3", "d2", "d1", "d0", "vout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/d10/d9/d8/d7/d6/d5/d4/d3/d2/d1/d0/vout"
    expected = [
        (2.0, -1.0),
        (12.0, -0.125),
        (22.0, 0.375),
        (32.0, 0.998046875),
    ]
    ok, detail = _sample_many(rows, {"vout": expected}, tol=0.025)
    if not ok:
        return ok, detail
    observed = [float(sample_signal_at(rows, "vout", time_ns * 1e-9) or 0.0) for time_ns, _ in expected]
    monotonic = all(b > a + 0.35 for a, b in zip(observed, observed[1:]))
    if not monotonic:
        return False, f"sar_weighted_sum_not_monotonic samples={','.join(f'{v:.3f}' for v in observed)}"
    return True, detail + " monotonic=True"


def check_v3_source_two_input_and_gate(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "in1", "in2", "out"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/in1/in2/out"
    return _sample_many(
        rows,
        {"out": [(5.0, 0.0), (15.0, 0.0), (25.0, 0.9), (35.0, 0.0), (45.0, 0.0)]},
        tol=0.08,
    )


def check_v3_source_two_input_xor_gate(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "in1", "in2", "out"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/in1/in2/out"
    return _sample_many(
        rows,
        {"out": [(5.0, 0.0), (15.0, 0.9), (25.0, 0.0), (35.0, 0.9), (45.0, 0.0)]},
        tol=0.08,
    )


def check_v3_source_analog_mux_threshold(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vin1", "vin2", "vsel", "vout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/vin1/vin2/vsel/vout"
    return _sample_many(
        rows,
        {"vout": [(5.0, 0.75), (15.0, 0.20), (25.0, 0.55), (35.0, 0.45)]},
        tol=0.025,
    )


def check_v3_source_two_bit_counter_marker(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clkin", "mc"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/clkin/mc"
    return _sample_many(
        rows,
        {"mc": [(6.0, 0.0), (16.0, 0.0), (26.0, 0.0), (36.0, 1.0), (46.0, 0.0)]},
        tol=0.08,
    )


def check_v3_source_max_detector_hold(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vin", "vout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/vin/vout"
    ok, detail = _sample_many(
        rows,
        {"vout": [(5.0, 0.20), (15.0, 0.70), (25.0, 0.70), (35.0, 0.85)]},
        tol=0.025,
    )
    if not ok:
        return ok, detail
    values = [float(sample_signal_at(rows, "vout", time_ns * 1e-9) or 0.0) for time_ns in (5.0, 15.0, 25.0, 35.0)]
    monotonic_hold = all(b >= a - 0.005 for a, b in zip(values, values[1:]))
    if not monotonic_hold:
        return False, f"max_detector_not_monotonic samples={','.join(f'{v:.3f}' for v in values)}"
    return True, detail + " monotonic_hold=True"


def check_v3_source_time_diff_detector(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "vinp", "vinn", "vout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/clk/vinp/vinn/vout"
    return _sample_many(
        rows,
        {"vout": [(6.0, 0.0), (26.0, -0.9), (46.0, 0.9)]},
        tol=0.08,
    )


def check_v3_source_differential_buffer(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vinp", "vinn", "voutp", "voutn"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/vinp/vinn/voutp/voutn"
    ok, detail = _sample_many(
        rows,
        {
            "voutp": [(5.0, 0.25), (20.0, 0.65), (35.0, 0.35)],
            "voutn": [(5.0, 0.55), (20.0, 0.30), (35.0, 0.70)],
        },
        tol=0.025,
    )
    if not ok:
        return ok, detail
    max_err = 0.0
    for signal_in, signal_out in (("vinp", "voutp"), ("vinn", "voutn")):
        for time_ns in (5.0, 20.0, 35.0):
            vi = sample_signal_at(rows, signal_in, time_ns * 1e-9)
            vo = sample_signal_at(rows, signal_out, time_ns * 1e-9)
            if vi is None or vo is None:
                return False, f"missing_buffer_pair_sample={signal_in}/{signal_out}@{time_ns:g}ns"
            max_err = max(max_err, abs(vi - vo))
    return max_err <= 0.025, f"{detail} max_pair_error={max_err:.4f}"


def check_v3_source_two_input_or_gate(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "in1", "in2", "out"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/in1/in2/out"
    return _sample_many(
        rows,
        {"out": [(5.0, 0.0), (15.0, 0.9), (25.0, 0.9), (35.0, 0.9), (45.0, 0.0)]},
        tol=0.08,
    )


def check_v3_source_sar_cdac_residue(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vin", "clk", "s6", "s5", "s4", "s3", "s2", "s1", "vres"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/vin/clk/s6/s5/s4/s3/s2/s1/vres"
    expected = [
        (6.0, 0.20),
        (12.0, 0.65),
        (17.0, 0.425),
        (22.0, 0.3125),
        (27.0, 0.25625),
        (32.0, 0.228125),
        (37.0, 0.2140625),
    ]
    ok, detail = _sample_many(rows, {"vres": expected}, tol=0.025)
    if not ok:
        return ok, detail
    observed = [float(sample_signal_at(rows, "vres", time_ns * 1e-9) or 0.0) for time_ns, _ in expected]
    has_expected_step = observed[1] > observed[0] + 0.35 and all(a > b for a, b in zip(observed[1:], observed[2:]))
    if not has_expected_step:
        return False, f"cdac_sequence_unexpected samples={','.join(f'{v:.4f}' for v in observed)}"
    return True, detail + " sample_then_monotone_down=True"


def check_v3_source_two_input_nand_gate(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "in1", "in2", "out"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/in1/in2/out"
    return _sample_many(
        rows,
        {"out": [(5.0, 0.9), (15.0, 0.9), (25.0, 0.0), (35.0, 0.9), (45.0, 0.9)]},
        tol=0.08,
    )


def check_v3_source_two_input_nor_gate(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "in1", "in2", "out"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/in1/in2/out"
    return _sample_many(
        rows,
        {"out": [(5.0, 0.9), (15.0, 0.0), (25.0, 0.0), (35.0, 0.0), (45.0, 0.9)]},
        tol=0.08,
    )


def check_v3_source_three_input_and_gate(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vin1", "vin2", "vin3", "vout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/vin1/vin2/vin3/vout"
    return _sample_many(
        rows,
        {"vout": [(5.0, 0.0), (15.0, 0.0), (25.0, 0.0), (35.0, 0.9), (45.0, 0.0), (55.0, 0.0)]},
        tol=0.08,
    )


def check_v3_source_three_input_or_gate(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vin1", "vin2", "vin3", "vout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/vin1/vin2/vin3/vout"
    return _sample_many(
        rows,
        {"vout": [(5.0, 0.0), (15.0, 0.9), (25.0, 0.9), (35.0, 0.9), (45.0, 0.9), (55.0, 0.9), (62.0, 0.0)]},
        tol=0.08,
    )


def check_v3_source_three_input_xor_gate(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vin1", "vin2", "vin3", "vout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/vin1/vin2/vin3/vout"
    return _sample_many(
        rows,
        {"vout": [(5.0, 0.0), (15.0, 0.9), (25.0, 0.0), (35.0, 0.9), (45.0, 0.0), (55.0, 0.9), (62.0, 0.0)]},
        tol=0.08,
    )


def check_v3_source_attenuator_gain(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vin", "vout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/vin/vout"
    ok, detail = _sample_many(
        rows,
        {"vout": [(5.0, 0.10), (15.0, 0.40), (25.0, 0.20), (32.0, 0.20)]},
        tol=0.015,
    )
    if not ok:
        return ok, detail
    max_gain_error = 0.0
    for time_ns in (5.0, 15.0, 25.0, 32.0):
        vin = sample_signal_at(rows, "vin", time_ns * 1e-9)
        vout = sample_signal_at(rows, "vout", time_ns * 1e-9)
        if vin is None or vout is None:
            return False, f"missing_gain_sample_at={time_ns:g}ns"
        max_gain_error = max(max_gain_error, abs(vout - 0.5 * vin))
    return max_gain_error <= 0.015, f"{detail} max_gain_error={max_gain_error:.5f}"


def check_v3_source_deadband_window(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "sigin", "sigout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/sigin/sigout"
    return _sample_many(
        rows,
        {"sigout": [(5.0, -0.30), (15.0, 0.0), (25.0, 0.30), (35.0, 0.0)]},
        tol=0.015,
    )


def check_v3_source_differential_deadband(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "sigin_p", "sigin_n", "sigout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/sigin_p/sigin_n/sigout"
    ok, detail = _sample_many(
        rows,
        {"sigout": [(5.0, -0.25), (15.0, 0.05), (25.0, 0.35), (35.0, 0.05)]},
        tol=0.015,
    )
    if not ok:
        return ok, detail
    diffs: list[float] = []
    for time_ns in (5.0, 15.0, 25.0, 35.0):
        vp = sample_signal_at(rows, "sigin_p", time_ns * 1e-9)
        vn = sample_signal_at(rows, "sigin_n", time_ns * 1e-9)
        if vp is None or vn is None:
            return False, f"missing_diff_sample_at={time_ns:g}ns"
        diffs.append(vp - vn)
    if not (diffs[0] < -0.45 and abs(diffs[1]) < 0.03 and diffs[2] > 0.45 and abs(diffs[3]) < 0.10):
        return False, "unexpected_input_diff_sequence=" + ",".join(f"{value:.3f}" for value in diffs)
    return True, detail + " diff_sequence=" + ",".join(f"{value:.3f}" for value in diffs)


def check_v3_source_hard_voltage_clamp(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vin", "vout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/vin/vout"
    return _sample_many(
        rows,
        {"vout": [(5.0, -0.20), (15.0, 0.30), (25.0, 0.60), (35.0, 0.10)]},
        tol=0.015,
    )


def check_v3_source_smooth_comparator_tanh(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "sigin", "sigref", "sigout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/sigin/sigref/sigout"
    return _sample_many(
        rows,
        {"sigout": [(5.0, 0.00004), (15.0, 0.45), (25.0, 0.89996), (35.0, 0.01619)]},
        tol=0.02,
    )


def check_v3_source_limiter_rails(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vdd", "vss", "vmax", "vmin", "vin", "vout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/vdd/vss/vmax/vmin/vin/vout"
    ok, detail = _sample_many(
        rows,
        {"vout": [(5.0, 0.10), (15.0, 0.40), (25.0, 0.70), (35.0, 0.10)]},
        tol=0.015,
    )
    if not ok:
        return ok, detail
    upper = sample_signal_at(rows, "vdd", 25e-9)
    margin = sample_signal_at(rows, "vmax", 25e-9)
    lower_base = sample_signal_at(rows, "vss", 5e-9)
    lower_margin = sample_signal_at(rows, "vmin", 5e-9)
    if upper is None or margin is None or lower_base is None or lower_margin is None:
        return False, "missing_limiter_margin_samples"
    return True, f"{detail} rails=[{lower_base + lower_margin:.3f},{upper - margin:.3f}]"


def check_v3_source_absolute_value(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "sigin", "sigout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/sigin/sigout"
    max_err = 0.0
    checked = 0
    for row in rows:
        if row.get("time", 0.0) < 0.2e-9:
            continue
        err = abs(row["sigout"] - abs(row["sigin"]))
        max_err = max(max_err, err)
        checked += 1
    if checked == 0:
        return False, "no_absolute_value_rows_checked"
    return max_err <= 0.02, f"checked={checked} max_abs_error={max_err:.5f}"


def check_v3_source_offset_gain_amplifier(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "sigin", "sigout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/sigin/sigout"
    return _sample_many(
        rows,
        {"sigout": [(5.0, -0.30), (15.0, 0.90), (25.0, -0.90)]},
        tol=0.015,
    )


def check_v3_source_safe_voltage_divider(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "signumer", "sigdenom", "sigout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/signumer/sigdenom/sigout"
    ok, detail = _sample_many(
        rows,
        {"sigout": [(5.0, 1.00), (15.0, 2.40), (25.0, 1.60)]},
        tol=0.03,
    )
    if not ok:
        return ok, detail
    denominators = [sample_signal_at(rows, "sigdenom", time_ns * 1e-9) for time_ns in (5.0, 15.0, 25.0)]
    if any(value is None for value in denominators):
        return False, "missing_divider_denominator_samples"
    return True, f"{detail} denom=" + ",".join(f"{float(value):.3f}" for value in denominators if value is not None)


def check_v3_source_polynomial_differential_vcvs(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "inp", "inn", "outp", "outn"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/inp/inn/outp/outn"
    ok, detail = _sample_many(
        rows,
        {
            "outp": [(5.0, 0.3995), (15.0, 0.5000), (25.0, 0.6005), (35.0, 0.7578)],
            "outn": [(5.0, 0.6005), (15.0, 0.5000), (25.0, 0.3995), (35.0, 0.2422)],
        },
        tol=0.025,
    )
    if not ok:
        return ok, detail
    max_cm_error = 0.0
    for time_ns in (5.0, 15.0, 25.0, 35.0):
        outp = sample_signal_at(rows, "outp", time_ns * 1e-9)
        outn = sample_signal_at(rows, "outn", time_ns * 1e-9)
        if outp is None or outn is None:
            return False, f"missing_vcvs_output_sample_at={time_ns:g}ns"
        max_cm_error = max(max_cm_error, abs(0.5 * (outp + outn) - 0.5))
    return max_cm_error <= 0.015, f"{detail} max_cm_error={max_cm_error:.5f}"


def check_v3_source_differential_gain_driver(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "sigin_p", "sigin_n", "sigout_p", "sigout_n", "sigref"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/sigin_p/sigin_n/sigout_p/sigout_n/sigref"
    ok, detail = _sample_many(
        rows,
        {
            "sigout_p": [(5.0, 0.35), (15.0, 0.45), (25.0, 0.60)],
            "sigout_n": [(5.0, 0.55), (15.0, 0.45), (25.0, 0.30)],
        },
        tol=0.02,
    )
    if not ok:
        return ok, detail
    return True, detail


def check_v3_source_limiting_differential_amplifier(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "sigin_p", "sigin_n", "sigout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/sigin_p/sigin_n/sigout"
    return _sample_many(
        rows,
        {"sigout": [(5.0, -0.40), (15.0, 0.20), (25.0, 0.80), (35.0, 0.50)]},
        tol=0.02,
    )


def check_v3_source_analog_multiplier(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "sigin1", "sigin2", "sigout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/sigin1/sigin2/sigout"
    ok, detail = _sample_many(
        rows,
        {"sigout": [(5.0, 0.20), (15.0, 0.48), (25.0, -0.40)]},
        tol=0.015,
    )
    if not ok:
        return ok, detail
    max_product_error = 0.0
    for time_ns in (5.0, 15.0, 25.0):
        sigin1 = sample_signal_at(rows, "sigin1", time_ns * 1e-9)
        sigin2 = sample_signal_at(rows, "sigin2", time_ns * 1e-9)
        sigout = sample_signal_at(rows, "sigout", time_ns * 1e-9)
        if sigin1 is None or sigin2 is None or sigout is None:
            return False, f"missing_multiplier_sample_at={time_ns:g}ns"
        max_product_error = max(max_product_error, abs(sigout - 2.0 * sigin1 * sigin2))
    return max_product_error <= 0.015, f"{detail} max_product_error={max_product_error:.5f}"


def check_v3_source_three_way_threshold_mux(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "sigin1", "sigin2", "sigin3", "cntrlp", "cntrlm", "sigout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/sigin1/sigin2/sigin3/cntrlp/cntrlm/sigout"
    return _sample_many(
        rows,
        {"sigout": [(5.0, 0.10), (15.0, 0.50), (25.0, 0.90)]},
        tol=0.02,
    )


def check_v3_source_differential_amplifier_core(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "sigin_p", "sigin_n", "sigout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/sigin_p/sigin_n/sigout"
    return _sample_many(
        rows,
        {"sigout": [(5.0, -0.50), (15.0, -0.10), (25.0, 0.30), (35.0, 0.10)]},
        tol=0.02,
    )


def check_v3_source_logarithmic_amplifier(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "sigin", "sigout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/sigin/sigout"
    return _sample_many(
        rows,
        {"sigout": [(5.0, -2.302585), (15.0, -0.693147), (25.0, -0.693147), (35.0, 0.0)]},
        tol=0.035,
    )


def check_v3_source_soft_voltage_clamp(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vin", "vout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/vin/vout"
    return _sample_many(
        rows,
        {"vout": [(5.0, -0.17293), (15.0, 0.20), (25.0, 0.57293), (35.0, 0.47869)]},
        tol=0.025,
    )


def check_v3_source_variable_gain_differential_amplifier(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "sigin_p", "sigin_n", "sigctrl_p", "sigctrl_n", "sigout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/sigin_p/sigin_n/sigctrl_p/sigctrl_n/sigout"
    return _sample_many(
        rows,
        {"sigout": [(5.0, 0.0), (15.0, 0.40), (25.0, 0.80), (35.0, -0.40)]},
        tol=0.025,
    )


def check_v3_source_voltage_controlled_gain_amplifier(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vin_p", "vin_n", "vctrl_p", "vctrl_n", "vout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/vin_p/vin_n/vctrl_p/vctrl_n/vout"
    return _sample_many(
        rows,
        {"vout": [(5.0, 0.3125), (15.0, 0.5750), (25.0, 0.9000), (35.0, 0.1000)]},
        tol=0.025,
    )


def check_v3_source_ideal_differential_opamp(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vinp", "vinn", "voutp", "voutn"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/vinp/vinn/voutp/voutn"
    ok, detail = _sample_many(
        rows,
        {
            "voutp": [(5.0, 0.30), (15.0, 0.50), (25.0, 0.80), (35.0, 0.10)],
            "voutn": [(5.0, 0.70), (15.0, 0.50), (25.0, 0.20), (35.0, 0.90)],
        },
        tol=0.025,
    )
    if not ok:
        return ok, detail
    max_cm_error = 0.0
    for time_ns in (5.0, 15.0, 25.0, 35.0):
        voutp = sample_signal_at(rows, "voutp", time_ns * 1e-9)
        voutn = sample_signal_at(rows, "voutn", time_ns * 1e-9)
        if voutp is None or voutn is None:
            return False, f"missing_opamp_output_sample_at={time_ns:g}ns"
        max_cm_error = max(max_cm_error, abs(0.5 * (voutp + voutn) - 0.5))
    return max_cm_error <= 0.02, f"{detail} max_cm_error={max_cm_error:.5f}"


def check_v3_source_half_adder_logic(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vin1", "vin2", "vout_sum", "vout_carry"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/vin1/vin2/vout_sum/vout_carry"
    return _sample_many(
        rows,
        {
            "vout_sum": [(5.0, 0.0), (15.0, 0.9), (25.0, 0.9), (35.0, 0.0)],
            "vout_carry": [(5.0, 0.0), (15.0, 0.0), (25.0, 0.0), (35.0, 0.9)],
        },
        tol=0.08,
    )


def check_v3_source_full_adder_logic(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vin1", "vin2", "vin_carry", "vout_sum", "vout_carry"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/vin1/vin2/vin_carry/vout_sum/vout_carry"
    return _sample_many(
        rows,
        {
            "vout_sum": [(5.0, 0.0), (15.0, 0.9), (25.0, 0.9), (35.0, 0.9), (45.0, 0.0), (55.0, 0.0), (65.0, 0.9)],
            "vout_carry": [(5.0, 0.0), (15.0, 0.0), (25.0, 0.0), (35.0, 0.0), (45.0, 0.9), (55.0, 0.9), (65.0, 0.9)],
        },
        tol=0.08,
    )


def check_v3_source_half_subtractor_logic(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vin1", "vin2", "vout_diff", "vout_borrow"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/vin1/vin2/vout_diff/vout_borrow"
    return _sample_many(
        rows,
        {
            "vout_diff": [(5.0, 0.0), (15.0, 0.9), (25.0, 0.9), (35.0, 0.0)],
            "vout_borrow": [(5.0, 0.0), (15.0, 0.9), (25.0, 0.0), (35.0, 0.0)],
        },
        tol=0.08,
    )


def check_v3_source_full_subtractor_logic(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vin1", "vin2", "vin_borrow", "vout_diff", "vout_borrow"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/vin1/vin2/vin_borrow/vout_diff/vout_borrow"
    return _sample_many(
        rows,
        {
            "vout_diff": [(5.0, 0.0), (15.0, 0.9), (25.0, 0.9), (35.0, 0.9), (45.0, 0.0), (55.0, 0.0), (65.0, 0.9)],
            "vout_borrow": [(5.0, 0.0), (15.0, 0.9), (25.0, 0.9), (35.0, 0.0), (45.0, 0.0), (55.0, 0.0), (65.0, 0.9)],
        },
        tol=0.08,
    )


def check_v3_source_rs_latch_voltage(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vin_s", "vin_r", "vout_q", "vout_qbar"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/vin_s/vin_r/vout_q/vout_qbar"
    return _sample_many(
        rows,
        {
            "vout_q": [(5.0, 0.0), (12.0, 0.9), (22.0, 0.9), (32.0, 0.0), (42.0, 0.0), (52.0, 0.9), (62.0, 0.9)],
            "vout_qbar": [(5.0, 0.9), (12.0, 0.0), (22.0, 0.0), (32.0, 0.9), (42.0, 0.9), (52.0, 0.0), (62.0, 0.0)],
        },
        tol=0.08,
    )


def check_v3_source_ideal_adc_4bit_quantizer(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vclk", "vip", "vin", "digital"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/vclk/vip/vin/digital"
    return _sample_many(
        rows,
        {"digital": [(4.0, 0.0), (14.0, 6.0), (24.0, 8.0), (34.0, 11.0), (44.0, 15.0)]},
        tol=0.08,
    )


def check_v3_source_ideal_dac_4bit_differential(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "digital", "vcm", "vop", "von"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/clk/digital/vcm/vop/von"
    ok, detail = _sample_many(
        rows,
        {
            "vop": [(4.0, 0.03125), (14.0, 0.34375), (24.0, 0.53125), (34.0, 0.96875)],
            "von": [(4.0, 0.96875), (14.0, 0.65625), (24.0, 0.46875), (34.0, 0.03125)],
        },
        tol=0.025,
    )
    if not ok:
        return ok, detail
    max_cm_error = 0.0
    for time_ns in (4.0, 14.0, 24.0, 34.0):
        vop = sample_signal_at(rows, "vop", time_ns * 1e-9)
        von = sample_signal_at(rows, "von", time_ns * 1e-9)
        if vop is None or von is None:
            return False, f"missing_dac_output_sample_at={time_ns:g}ns"
        max_cm_error = max(max_cm_error, abs(0.5 * (vop + von) - 0.5))
    return max_cm_error <= 0.015, f"{detail} max_cm_error={max_cm_error:.5f}"


def check_v3_source_two_period_sample_delay(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "update", "ain", "aout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/update/ain/aout"
    return _sample_many(
        rows,
        {"aout": [(4.0, 0.0), (14.0, 0.1), (24.0, 0.4), (34.0, 0.8), (44.0, 0.2)]},
        tol=0.025,
    )


def check_v3_source_clocked_four_input_mux(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "dsel0", "dsel1", "din0", "din1", "din2", "din3", "clks", "dout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing mux input/output signals"
    return _sample_many(
        rows,
        {"dout": [(4.0, 0.15), (14.0, 0.35), (24.0, 0.65), (34.0, 0.85)]},
        tol=0.025,
    )


def check_v3_source_divide_by_eight_clock(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vin", "vout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/vin/vout"
    return _sample_many(
        rows,
        {
            "vout": [
                (2.0, 0.9),
                (4.0, 0.9),
                (6.0, 0.9),
                (8.0, 0.9),
                (10.0, 0.0),
                (12.0, 0.0),
                (14.0, 0.0),
                (16.0, 0.0),
                (18.0, 0.9),
            ]
        },
        tol=0.08,
    )


def check_v3_source_flash_thermometer_centered_sum(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "b0", "b1", "b2", "b3", "b4", "b5", "b6", "b7", "dout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing thermometer input/output signals"
    return _sample_many(
        rows,
        {"dout": [(5.0, -0.45), (15.0, -0.1125), (25.0, 0.1125), (35.0, 0.45)]},
        tol=0.02,
    )


def check_v3_source_weighted_sar_decoder_9b(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "aout7b", "aout7b5", "aout8b"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/aout7b/aout7b5/aout8b"
    return _sample_many(
        rows,
        {
            "aout7b": [(5.0, -0.4963235), (15.0, 0.1654412), (25.0, -0.1654412), (35.0, 0.4963235)],
            "aout7b5": [(5.0, -0.4963235), (15.0, 0.1691176), (25.0, -0.1654412), (35.0, 0.4963235)],
            "aout8b": [(5.0, -0.4981618), (15.0, 0.1672794), (25.0, -0.1636029), (35.0, 0.4981618)],
        },
        tol=0.01,
    )


def check_v3_source_control_word_encoder_7b(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "d0", "d1", "d2", "d3", "d4", "d5", "d6"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing encoder output signals"
    return _sample_many(
        rows,
        {
            "d0": [(5.0, 0.9), (15.0, 0.9)],
            "d1": [(5.0, 0.0), (15.0, 0.0)],
            "d2": [(5.0, 0.9), (15.0, 0.9)],
            "d3": [(5.0, 0.0), (15.0, 0.0)],
            "d4": [(5.0, 0.9), (15.0, 0.9)],
            "d5": [(5.0, 0.0), (15.0, 0.0)],
            "d6": [(5.0, 0.9), (15.0, 0.9)],
        },
        tol=0.08,
    )


def check_v3_source_four_channel_edge_sampler(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "vin0", "vin1", "vin2", "vin3", "vout0", "vout1", "vout2", "vout3"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing sampler input/output signals"
    return _sample_many(
        rows,
        {
            "vout0": [(4.0, 0.1), (14.0, 0.2), (24.0, 0.3), (34.0, 0.4)],
            "vout1": [(4.0, 0.2), (14.0, 0.4), (24.0, 0.6), (34.0, 0.8)],
            "vout2": [(4.0, 0.3), (14.0, 0.6), (24.0, 0.9), (34.0, 0.1)],
            "vout3": [(4.0, 0.4), (14.0, 0.8), (24.0, 0.2), (34.0, 0.6)],
        },
        tol=0.025,
    )


def check_v3_source_dual_modulus_divider_16_17(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "fin", "mc", "fout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/fin/mc/fout"
    return _sample_many(
        rows,
        {
            "fout": [
                (30.0, 0.0),
                (32.0, 1.0),
                (48.0, 1.0),
                (50.0, 0.0),
                (64.0, 0.0),
                (66.0, 1.0),
                (82.0, 1.0),
                (84.0, 0.0),
            ]
        },
        tol=0.08,
    )


def check_v3_source_sar_5bit_serial_decoder(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "din", "clks", "ready", "dout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/din/clks/ready/dout"
    return _sample_many(
        rows,
        {"dout": [(3.0, -0.5), (17.0, 0.2096774), (33.0, -0.2096774)]},
        tol=0.02,
    )


def check_v3_source_cyclic_decoder_12bit(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clks", "dout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/clks/dout"
    return _sample_many(
        rows,
        {"dout": [(4.0, -0.5), (14.0, -0.1666667), (24.0, 0.1666667), (34.0, 0.5)]},
        tol=0.02,
    )


def check_v3_source_flash_8level_sum_delay(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vip", "vim", "clks", "doutsum", "doutsumdelay"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing flash8 sum/delay signals"
    return _sample_many(
        rows,
        {
            "doutsum": [(4.0, 0.0), (14.0, 0.25), (24.0, 0.5), (34.0, 0.875)],
            "doutsumdelay": [(4.0, 0.0), (14.0, 0.0), (24.0, 0.25), (34.0, 0.5)],
        },
        tol=0.025,
    )


def check_v3_source_flash_sum8_fraction(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clks", "dout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/clks/dout"
    return _sample_many(
        rows,
        {"dout": [(4.0, 0.0), (14.0, 0.375), (24.0, 0.625), (34.0, 1.0)]},
        tol=0.025,
    )


def check_v3_source_two_channel_sample_demux(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "samp1", "samp2", "clks1", "clks2", "vout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing demux input/output signals"
    return _sample_many(
        rows,
        {"vout": [(4.0, 0.1), (14.0, 0.4), (24.0, 0.5), (34.0, 0.8)]},
        tol=0.025,
    )


def check_v3_source_differential_dac_calc_6b(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clks", "voutp", "voutn"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/clks/voutp/voutn"
    ok, detail = _sample_many(
        rows,
        {
            "voutp": [(5.0, 0.5777344), (15.0, 0.8074219), (25.0, 0.7144531), (35.0, 0.9222656)],
            "voutn": [(5.0, 0.9222656), (15.0, 0.6925781), (25.0, 0.7855469), (35.0, 0.5777344)],
        },
        tol=0.025,
    )
    if not ok:
        return ok, detail
    max_cm_error = 0.0
    for time_ns in (5.0, 15.0, 25.0, 35.0):
        yp = sample_signal_at(rows, "voutp", time_ns * 1e-9)
        yn = sample_signal_at(rows, "voutn", time_ns * 1e-9)
        if yp is None or yn is None:
            return False, f"missing_dac_calc_output_sample_at={time_ns:g}ns"
        max_cm_error = max(max_cm_error, abs(0.5 * (yp + yn) - 0.75))
    return max_cm_error <= 0.015, f"{detail} max_cm_error={max_cm_error:.5f}"


def check_v3_source_flash_adc_threshold_taps(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vin", "clk", "dout0", "dout1", "dout2", "dout3", "dout4", "dout5", "dout6"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing flash adc threshold tap signals"
    return _sample_many(
        rows,
        {
            "dout0": [(4.0, 0.0), (14.0, 0.9), (24.0, 0.9), (34.0, 0.9), (44.0, 0.9)],
            "dout1": [(4.0, 0.0), (14.0, 0.9), (24.0, 0.9), (34.0, 0.9), (44.0, 0.9)],
            "dout2": [(4.0, 0.0), (14.0, 0.0), (24.0, 0.9), (34.0, 0.9), (44.0, 0.9)],
            "dout3": [(4.0, 0.0), (14.0, 0.0), (24.0, 0.9), (34.0, 0.9), (44.0, 0.9)],
            "dout4": [(4.0, 0.0), (14.0, 0.0), (24.0, 0.0), (34.0, 0.9), (44.0, 0.9)],
            "dout5": [(4.0, 0.0), (14.0, 0.0), (24.0, 0.0), (34.0, 0.9), (44.0, 0.9)],
            "dout6": [(4.0, 0.0), (14.0, 0.0), (24.0, 0.0), (34.0, 0.0), (44.0, 0.9)],
        },
        tol=0.08,
    )


def check_v3_source_divide_by_two_toggle(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clkin", "clkout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/clkin/clkout"
    return _sample_many(
        rows,
        {"clkout": [(2.0, 0.9), (5.0, 0.0), (8.0, 0.9), (11.0, 0.0), (14.0, 0.9), (17.0, 0.0), (20.0, 0.9), (23.0, 0.0)]},
        tol=0.08,
    )


def check_v3_source_dac_5v_weighted_7b(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clks", "vout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/clks/vout"
    return _sample_many(
        rows,
        {"vout": [(5.0, 1.0), (15.0, 3.65625), (25.0, 2.5625), (35.0, 4.96875)]},
        tol=0.04,
    )


def check_v3_source_folded_flash_dac_4b(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vd4", "vd3", "vd2", "vd1", "vout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing folded flash dac signals"
    return _sample_many(
        rows,
        {"vout": [(5.0, 0.5), (15.0, 0.0625), (25.0, 0.5), (35.0, 0.9375)]},
        tol=0.02,
    )


def check_v3_source_ref_flash_8level_decoder(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vin", "clks", "dout", "vres"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing ref flash 8level signals"
    return _sample_many(
        rows,
        {
            "dout": [(4.0, 0.0), (14.0, 0.375), (24.0, 0.625), (34.0, 1.0)],
            "vres": [(4.0, 0.6), (14.0, 0.325), (24.0, -0.225), (34.0, -0.2)],
        },
        tol=0.025,
    )


def check_v3_source_ref_flash_15level_decoder(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clks", "dout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing ref flash 15level signals"
    return _sample_many(
        rows,
        {"dout": [(4.0, 0.0), (14.0, 1.0 / 3.0), (24.0, 2.0 / 3.0), (34.0, 1.0)]},
        tol=0.025,
    )


def check_v3_source_divide_by_8_9_switch(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clkin", "mc", "out"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing divide-by-8/9 signals"
    return _sample_many(
        rows,
        {"out": [(2.0, 1.2), (4.0, 0.0), (12.0, 1.2), (16.0, 1.2), (20.0, 0.0), (26.0, 0.0), (28.0, 1.2)]},
        tol=0.08,
    )


def check_v3_source_dac_restore_10bit_offset(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "vout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/clk/vout"
    return _sample_many(
        rows,
        {"vout": [(5.0, -0.9553711), (15.0, 0.3190430), (25.0, 0.5282227), (35.0, 0.9553711)]},
        tol=0.025,
    )


def check_v3_source_dac_8bit_ideal_scalar(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vd7", "vd6", "vd5", "vd4", "vd3", "vd2", "vd1", "vd0", "vout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing scalar 8-bit dac signals"
    return _sample_many(
        rows,
        {"vout": [(5.0, 0.0), (15.0, 85.0 / 256.0), (25.0, 166.0 / 256.0), (35.0, 255.0 / 256.0)]},
        tol=0.02,
    )


def check_v3_source_flash_data_align_pipeline(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "dout0", "dout1", "dout2", "dout3"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing flash data align signals"
    return _sample_many(
        rows,
        {
            "dout0": [(2.0, 0.0), (8.0, 0.0), (14.0, 0.0), (20.0, 0.0), (26.0, 1.0), (32.0, 1.0), (38.0, 0.0), (44.0, 1.0)],
            "dout1": [(2.0, 0.0), (8.0, 0.0), (14.0, 0.0), (20.0, 0.0), (26.0, 1.0), (32.0, 0.0), (38.0, 0.0), (44.0, 0.0)],
            "dout2": [(2.0, 0.0), (8.0, 0.0), (14.0, 0.0), (20.0, 0.0), (26.0, 0.0), (32.0, 1.0), (38.0, 0.0), (44.0, 0.0)],
            "dout3": [(2.0, 0.0), (8.0, 0.0), (14.0, 0.0), (20.0, 0.0), (26.0, 0.0), (32.0, 0.0), (38.0, 1.0), (44.0, 0.0)],
        },
        tol=0.08,
    )


def check_v3_source_cyclic_decoder_10b(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "dp", "dn", "ready", "clks", "dout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing cyclic decoder signals"
    return _sample_many(
        rows,
        {"dout": [(12.0, 720.0 / 1023.0 - 0.5), (26.0, 320.0 / 1023.0 - 0.5)]},
        tol=0.02,
    )


def check_v3_source_ideal_adc_out_7bits(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "din0", "din1", "din2", "din3", "din4", "din5", "din6", "dout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing ideal adc out 7-bit signals"
    return _sample_many(
        rows,
        {"dout": [(5.0, 0.0), (15.0, 0.6640625), (25.0, 0.328125), (35.0, 0.9921875)]},
        tol=0.02,
    )


def check_v3_source_va_lx_adc_ideal_4b(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vin", "clks", "d1", "d2", "d3", "d4"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing va_lx adc signals"
    return _sample_many(
        rows,
        {
            "d1": [(5.0, 1.0), (15.0, 0.0), (25.0, 1.0), (35.0, 0.0)],
            "d2": [(5.0, 0.0), (15.0, 0.0), (25.0, 0.0), (35.0, 1.0)],
            "d3": [(5.0, 0.0), (15.0, 1.0), (25.0, 0.0), (35.0, 1.0)],
            "d4": [(5.0, 0.0), (15.0, 0.0), (25.0, 1.0), (35.0, 1.0)],
        },
        tol=0.08,
    )


def check_v3_source_va_lx_dac_ideal_4b(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "rdy", "aout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing va_lx dac signals"
    return _sample_many(
        rows,
        {"aout": [(5.0, 0.0), (15.0, 0.5625), (25.0, 1.575), (35.0, 1.6875)]},
        tol=0.03,
    )


def check_v3_source_l1_dac_4b_bipolar(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "rdy", "aout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing l1 dac bipolar signals"
    return _sample_many(
        rows,
        {"aout": [(5.0, -1.0), (15.0, -0.375), (25.0, 0.75), (35.0, 0.875)]},
        tol=0.03,
    )


def check_v3_source_l2_cdac_4b_residue(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vin", "clks", "dctrl1", "dctrl2", "dctrl3", "vres"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing l2 cdac residue signals"
    return _sample_many(
        rows,
        {"vres": [(2.0, 0.1), (4.0, 0.6), (6.0, 0.85), (8.0, 0.975), (14.0, -0.2), (16.0, 0.05)]},
        tol=0.03,
    )


def check_v3_source_ideal_clkmux_8channel(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "out", "count_x"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing ideal clkmux signals"
    return _sample_many(
        rows,
        {
            "out": [(2.0, 0.2), (4.0, 0.3), (6.0, 0.4), (8.0, 0.5), (10.0, 0.6), (12.0, 0.7), (14.0, 0.8), (16.0, 0.1)],
            "count_x": [(2.0, 1.0), (4.0, 2.0), (6.0, 3.0), (8.0, 4.0), (10.0, 5.0), (12.0, 6.0), (14.0, 7.0), (16.0, 0.0)],
        },
        tol=0.08,
    )


def check_v3_source_dac_ideal_4b_offset(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "din0", "din1", "din2", "din3", "dout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing dac ideal 4b offset signals"
    return _sample_many(
        rows,
        {"dout": [(5.0, 0.239), (15.0, 0.379625), (25.0, 0.52025), (35.0, 0.660875)]},
        tol=0.02,
    )


def check_v3_source_linear_pfd_gain(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "in1", "in2", "out"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing linear pfd gain signals"
    return _sample_many(
        rows,
        {"out": [(5.0, 0.203), (15.0, 0.203), (25.0, -0.812), (35.0, 1.218)]},
        tol=0.02,
    )


def check_v3_source_l2_cmp_ideal_clocked(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "cmpck", "vinp", "vinn", "dcmpn", "dcmpp"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing l2 cmp ideal clocked signals"
    return _sample_many(
        rows,
        {
            "dcmpp": [(1.3, 0.9), (2.0, 0.9), (11.3, 0.0), (12.0, 0.9), (21.3, 0.0), (31.3, 0.9)],
            "dcmpn": [(1.3, 0.0), (2.0, 0.9), (11.3, 0.9), (12.0, 0.9), (21.3, 0.0), (31.3, 0.0)],
        },
        tol=0.08,
    )


def check_v3_source_comparator_offset_driver(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "dcmpp", "vinp", "vinn"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing comparator offset driver signals"
    return _sample_many(
        rows,
        {
            "vinp": [(3.0, 0.4), (13.0, 0.425), (23.0, 0.4125), (33.0, 0.40625)],
            "vinn": [(3.0, 0.5), (13.0, 0.475), (23.0, 0.4875), (33.0, 0.49375)],
        },
        tol=0.02,
    )


def check_v3_source_pipe_2lane_edge_align(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "din1", "din2", "clk_align", "dout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing pipe 2lane edge align signals"
    return _sample_many(
        rows,
        {"dout": [(1.3, 0.1), (1.8, 0.8), (11.3, 0.4), (11.8, 0.3), (21.3, 0.7), (21.8, 0.5), (31.3, 0.2), (31.8, 0.9)]},
        tol=0.02,
    )


def check_v3_source_dac_serial_accumulator(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk_sample", "clk_sarready", "data", "out"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing dac serial accumulator signals"
    return _sample_many(
        rows,
        {"out": [(2.0, -1.1), (4.0, 0.0), (6.0, 0.0), (8.0, 0.275), (10.0, 0.4125), (14.0, -1.1), (16.0, -1.1), (18.0, -0.55), (20.0, -0.55), (22.0, -0.4125)]},
        tol=0.035,
    )


def check_v3_source_sar_sum_weighted_11b(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing sar sum weighted output"
    return _sample_many(
        rows,
        {"vout": [(5.0, -1.0), (15.0, 0.314453125), (25.0, -0.25390625), (35.0, 0.998046875)]},
        tol=0.02,
    )


def check_v3_source_iterative_isar_dac(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "dcmp", "rst", "clk", "vdac"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing iterative isar dac signals"
    return _sample_many(
        rows,
        {"vdac": [(1.5, 0.0), (2.5, -0.1), (4.5, -0.05), (6.5, -0.025), (8.5, -0.0375), (10.5, -0.03125)]},
        tol=0.015,
    )


def check_v3_source_offset_bisection_driver(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "vout", "vcm", "vinp", "vinn"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing offset bisection driver signals"
    return _sample_many(
        rows,
        {
            "vinp": [(3.0, 0.505), (5.0, 0.510), (7.0, 0.5075), (9.0, 0.505), (11.0, 0.50625), (13.0, 0.505625)],
            "vinn": [(3.0, 0.495), (5.0, 0.490), (7.0, 0.4925), (9.0, 0.495), (11.0, 0.49375), (13.0, 0.494375)],
        },
        tol=0.005,
    )


def check_v3_source_weighted_decoder_7b5(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "aout7b", "aout7b5", "aout8b"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing weighted decoder outputs"
    return _sample_many(
        rows,
        {
            "aout7b": [(5.0, -0.4963235), (15.0, -0.1654412), (25.0, 0.1727941), (35.0, 0.4963235)],
            "aout7b5": [(5.0, -0.4963235), (15.0, -0.1654412), (25.0, 0.1691176), (35.0, 0.4963235)],
            "aout8b": [(5.0, -0.4981618), (15.0, -0.1636029), (25.0, 0.1709559), (35.0, 0.4981618)],
        },
        tol=0.01,
    )


def check_v3_source_toggle_flip_flop(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vtrig", "vout_q", "vout_qbar"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing toggle flip-flop signals"
    return _sample_many(
        rows,
        {
            "vout_q": [(0.8, 0.0), (1.3, 0.9), (3.3, 0.0), (5.3, 0.9), (7.3, 0.0)],
            "vout_qbar": [(0.8, 0.9), (1.3, 0.0), (3.3, 0.9), (5.3, 0.0), (7.3, 0.9)],
        },
        tol=0.04,
    )


def check_v3_source_sync_8b_dffs_v2(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "do0", "do1", "do2", "do3", "do4", "do5", "do6", "do7", "do8"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing sync 8b dffs outputs"
    return _sample_many(
        rows,
        {
            "do0": [(9.7, 1.0), (19.7, 0.0)],
            "do1": [(9.7, 0.0), (19.7, 1.0)],
            "do2": [(9.7, 1.0), (19.7, 0.0)],
            "do3": [(9.7, 0.0), (19.7, 1.0)],
            "do4": [(9.7, 1.0), (19.7, 0.0)],
            "do5": [(9.7, 0.0), (19.7, 1.0)],
            "do6": [(9.7, 1.0), (19.7, 0.0)],
            "do7": [(9.7, 0.0), (19.7, 1.0)],
            "do8": [(9.7, 1.0), (19.7, 0.0)],
        },
        tol=0.08,
    )


def check_v3_source_onehot_progress_encoder(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "d0", "d1", "d2", "d3", "d4", "d15", "sum"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing onehot progress encoder signals"
    return _sample_many(
        rows,
        {
            "sum": [(0.8, 0.0), (1.3, 1.0), (4.3, 4.0), (16.3, 16.0), (17.3, 16.0)],
            "d0": [(0.8, 0.0), (1.3, 1.0)],
            "d3": [(4.3, 1.0)],
            "d4": [(4.3, 0.0), (16.3, 1.0)],
            "d15": [(16.3, 1.0), (17.3, 1.0)],
        },
        tol=0.08,
    )


def check_v3_source_tdc_ideal_edge_delta(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "inp", "inn", "samp", "vout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing tdc ideal edge delta signals"
    return _sample_many(
        rows,
        {"vout": [(1.0, 0.0), (3.0, -0.3), (7.0, 0.6), (12.0, 0.2)]},
        tol=0.025,
    )


def check_v3_source_foreground_cload_calibrator(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "dcp0", "dcp1", "dcp2", "dcp3", "dcp4", "dcn1", "dcn3", "cvinp", "cvinn", "en", "enb"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing foreground cload calibrator signals"
    return _sample_many(
        rows,
        {
            "cvinp": [(0.5, 0.82), (12.5, 0.82)],
            "cvinn": [(0.5, 0.18), (12.5, 0.18)],
            "dcp4": [(1.7, 1.0)],
            "dcn3": [(3.7, 1.0)],
            "dcp2": [(5.7, 1.0)],
            "dcn1": [(7.7, 1.0)],
            "dcp0": [(9.7, 1.0), (11.7, 1.0)],
            "en": [(9.7, 1.0), (11.7, 0.0)],
            "enb": [(9.7, 0.0), (11.7, 1.0)],
        },
        tol=0.08,
    )


def check_v3_source_pipe15_data_align(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "do0", "do3", "do7", "do11", "do14"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing pipe15 data align outputs"
    return _sample_many(
        rows,
        {
            "do0": [(1.7, 0.9), (11.7, 0.0)],
            "do3": [(1.7, 0.0), (9.7, 0.0), (11.7, 0.9)],
            "do7": [(5.7, 0.9), (9.7, 0.9), (11.7, 0.0)],
            "do11": [(5.7, 0.0), (9.7, 0.9), (11.7, 0.0)],
            "do14": [(5.7, 0.0), (9.7, 0.9), (11.7, 0.0)],
        },
        tol=0.08,
    )


def check_v3_source_clocked_mux4_sampler(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "dsel0", "dsel1", "din0", "din1", "din2", "din3", "clks", "dout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing clocked mux4 sampler signals"
    return _sample_many(
        rows,
        {"dout": [(0.5, 0.0), (1.3, 0.12), (3.3, 0.34), (5.3, 0.61), (7.3, 0.83), (8.5, 0.83)]},
        tol=0.015,
    )


def check_v3_source_dac7_code_generator(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "din0", "din1", "din2", "din3", "din4", "din5", "din6"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing dac7 code generator outputs"
    return _sample_many(
        rows,
        {
            "din0": [(0.5, 0.0), (1.3, 0.9), (8.3, 0.9)],
            "din4": [(4.3, 0.9), (8.3, 0.0), (9.3, 0.0)],
            "din5": [(2.3, 0.9), (4.3, 0.0), (8.3, 0.9)],
            "din6": [(1.3, 0.9), (2.3, 0.0), (4.3, 0.9)],
        },
        tol=0.08,
    )


def check_v3_source_foreground_rdac_calibrator(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "dc0", "dc1", "dc2", "dc3", "dc4", "dc5", "dc6", "cvinp", "cvinn", "en", "enb"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing foreground rdac calibrator outputs"
    return _sample_many(
        rows,
        {
            "dc6": [(0.5, 1.0), (11.7, 1.0), (14.5, 1.0)],
            "dc5": [(1.7, 1.0), (3.7, 0.0), (14.5, 0.0)],
            "dc4": [(3.7, 1.0), (14.5, 1.0)],
            "dc3": [(5.7, 1.0), (7.7, 0.0), (14.5, 0.0)],
            "dc2": [(7.7, 1.0), (14.5, 1.0)],
            "dc1": [(9.7, 1.0), (11.7, 0.0), (14.5, 0.0)],
            "dc0": [(11.7, 1.0), (14.5, 1.0)],
            "cvinp": [(0.5, 0.78), (8.5, 0.78), (14.5, 0.78)],
            "cvinn": [(0.5, 0.22), (8.5, 0.22), (14.5, 0.22)],
            "en": [(0.5, 1.0), (11.7, 1.0), (13.7, 0.0)],
            "enb": [(0.5, 0.0), (11.7, 0.0), (13.7, 1.0)],
        },
        tol=0.08,
    )


def check_v3_source_offset_rdac_search_flow(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vinp", "vinn", "vrefp", "vrefn", "dc0", "dc1", "dc2", "dc3", "dc4", "dc5", "dc6"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing offset rdac search outputs"
    return _sample_many(
        rows,
        {
            "dc6": [(0.5, 1.0), (7.7, 1.0), (17.7, 1.0)],
            "dc5": [(1.7, 1.0), (7.7, 1.0), (17.7, 1.0)],
            "dc4": [(3.7, 0.0), (7.7, 0.0), (17.7, 0.0)],
            "dc3": [(3.7, 1.0), (5.7, 0.0), (17.7, 0.0)],
            "dc2": [(5.7, 1.0), (13.7, 1.0), (17.7, 0.0)],
            "dc1": [(5.7, 1.0), (13.7, 1.0), (17.7, 0.0)],
            "dc0": [(7.7, 1.0), (13.7, 1.0), (17.7, 0.0)],
            "vrefp": [(0.5, 0.3344), (13.7, 0.3344), (17.7, 0.3656)],
            "vrefn": [(0.5, 0.8656), (13.7, 0.8656), (17.7, 0.8344)],
            "vinp": [(0.5, 0.3344), (9.7, 0.3294), (17.7, 0.3656)],
            "vinn": [(0.5, 0.8656), (9.7, 0.8706), (17.7, 0.8344)],
        },
        tol=0.08,
    )


def check_v3_source_spi_shift_mux(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "out0", "out1", "out2", "out3", "out4", "out5", "out6", "out7", "sdo", "scko"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing spi shift mux outputs"
    return _sample_many(
        rows,
        {
            "out7": [(0.2, 0.9), (1.3, 0.0), (2.3, 0.9), (6.3, 0.9)],
            "out6": [(0.2, 0.0), (1.3, 0.9), (3.3, 0.0), (5.3, 0.9)],
            "out5": [(0.2, 0.9), (2.3, 0.0), (4.3, 0.9), (6.3, 0.9)],
            "out4": [(0.2, 0.9), (1.3, 0.0), (3.3, 0.9), (5.3, 0.9)],
            "out0": [(0.2, 0.0), (1.3, 0.9), (3.3, 0.0), (5.3, 0.9)],
            "sdo": [(0.2, 0.9), (1.3, 0.0), (2.3, 0.9), (5.3, 0.0)],
            "scko": [(0.2, 0.0), (1.3, 0.9), (2.3, 0.0), (3.3, 0.9)],
        },
        tol=0.08,
    )


def check_v3_source_dff_set_reset_hold(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "d", "rn", "sn", "qp"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing dff set/reset outputs"
    return _sample_many(
        rows,
        {
            "qp": [(0.3, 0.0), (1.3, 0.9), (3.3, 0.0), (5.3, 0.9), (6.3, 0.0), (7.3, 0.9)],
            "rn": [(5.3, 0.9), (6.3, 0.0), (7.3, 0.9)],
            "sn": [(6.3, 0.9), (7.3, 0.0)],
        },
        tol=0.08,
    )


def check_v3_source_sarfend_logic_4b(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {
        "time",
        "clkc",
        "dp1",
        "dp2",
        "dp3",
        "dp4",
        "dm1",
        "dm2",
        "dm3",
        "dm4",
        "dout0",
        "dout1",
        "dout2",
        "dout3",
    }
    if not rows or not required.issubset(rows[0]):
        return False, "missing sarfend logic outputs"
    return _sample_many(
        rows,
        {
            "clkc": [(0.3, 0.0), (1.8, 1.0), (2.4, 0.0), (3.0, 1.0), (4.2, 0.0)],
            "dp4": [(0.3, 0.0), (2.4, 1.0), (7.0, 1.0)],
            "dm4": [(0.3, 0.0), (2.4, 0.0), (7.0, 0.0)],
            "dp3": [(0.3, 1.0), (4.2, 0.0), (7.0, 0.0)],
            "dm3": [(0.3, 1.0), (4.2, 1.0), (7.0, 1.0)],
            "dp2": [(0.3, 1.0), (6.0, 1.0), (7.0, 1.0)],
            "dm2": [(0.3, 1.0), (6.0, 1.0), (7.0, 0.0)],
            "dout3": [(0.3, 0.0), (1.2, 0.0), (7.0, 0.0)],
            "dout2": [(0.3, 0.0), (1.2, 1.0), (7.0, 1.0)],
            "dout1": [(0.3, 0.0), (1.2, 1.0), (7.0, 1.0)],
            "dout0": [(0.3, 0.0), (1.2, 1.0), (7.0, 1.0)],
        },
        tol=0.08,
    )


def check_v3_source_adc_sample_clock_sequencer(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "rst", "s", "ss", "nc_az", "nc", "conv"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing adc sample clock sequencer outputs"
    return _sample_many(
        rows,
        {
            "rst": [(0.1, 0.9), (0.7, 0.0), (18.1, 0.9), (20.6, 0.0)],
            "s": [(0.7, 0.9), (1.45, 0.0), (6.7, 0.9), (7.45, 0.0), (12.7, 0.9)],
            "ss": [(0.7, 0.9), (1.45, 0.0), (6.7, 0.9), (7.45, 0.0), (12.7, 0.9)],
            "nc_az": [(1.45, 0.9), (1.8, 0.0), (7.45, 0.9), (7.85, 0.0), (13.45, 0.9)],
            "nc": [(1.8, 0.9), (2.6, 0.0), (7.85, 0.9), (8.6, 0.0), (13.85, 0.9)],
            "conv": [(2.6, 0.9), (5.0, 0.9), (6.7, 0.0), (8.6, 0.9), (14.6, 0.9), (18.1, 0.0)],
        },
        tol=0.08,
    )


def check_v3_source_pipeline_counter_onehot(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "dout0", "dout1", "dout2", "s0", "s1", "s2", "s3", "s4", "s5"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing pipeline counter outputs"
    return _sample_many(
        rows,
        {
            "dout0": [(0.3, 0.0), (0.8, 0.9), (1.8, 0.0), (2.8, 0.9), (4.8, 0.9), (5.8, 0.0)],
            "dout1": [(0.3, 0.0), (1.8, 0.9), (2.8, 0.9), (3.8, 0.0), (5.8, 0.0)],
            "dout2": [(0.3, 0.0), (3.8, 0.9), (4.8, 0.9), (5.8, 0.0)],
            "s0": [(0.3, 0.9), (0.8, 0.0), (5.8, 0.9)],
            "s1": [(0.8, 0.9), (1.8, 0.0), (6.8, 0.9)],
            "s2": [(1.8, 0.9), (2.8, 0.0)],
            "s3": [(2.8, 0.9), (3.8, 0.0)],
            "s4": [(3.8, 0.9), (4.8, 0.0)],
            "s5": [(4.8, 0.9), (5.8, 0.0)],
        },
        tol=0.08,
    )


def check_v3_source_cdac_bidirect_residue(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vin", "clks", "dctrl4", "dctrl5", "dctrl6", "dctrl7", "vres"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing cdac bidirect residue signals"
    return _sample_many(
        rows,
        {
            "vres": [(0.3, 0.30), (1.0, 0.30), (2.0, 0.80), (3.0, 0.55), (4.0, 0.425), (5.0, 0.3625)],
            "dctrl7": [(0.3, 1.0), (2.0, 0.0)],
            "dctrl6": [(2.0, 0.0), (3.0, 1.0)],
            "dctrl5": [(3.0, 0.0), (4.0, 1.0)],
            "dctrl4": [(4.0, 0.0), (5.0, 1.0)],
        },
        tol=0.015,
    )


def check_v3_source_pfd_reset_pulse(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "a", "b", "ub", "d"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing pfd reset pulse signals"
    return _sample_many(
        rows,
        {
            "ub": [(0.5, 0.9), (1.1, 0.0), (1.6, 0.0), (1.9, 0.9), (3.5, 0.9), (4.1, 0.9)],
            "d": [(0.5, 0.0), (1.1, 0.0), (1.9, 0.0), (3.5, 0.9), (4.1, 0.0), (4.5, 0.0)],
        },
        tol=0.08,
    )


def check_v3_source_trim_ctrl_4bit(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "ain", "dout0", "dout1", "dout2", "dout3"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing trim ctrl 4bit signals"
    return _sample_many(
        rows,
        {
            "dout0": [(0.5, 0.0), (1.5, 0.9), (2.5, 0.0), (3.5, 0.9), (4.5, 0.0)],
            "dout1": [(0.5, 0.0), (1.5, 0.9), (2.5, 0.9), (3.5, 0.9), (4.5, 0.9)],
            "dout2": [(0.5, 0.0), (1.5, 0.0), (2.5, 0.9), (3.5, 0.0), (4.5, 0.9)],
            "dout3": [(0.5, 0.0), (1.5, 0.0), (2.5, 0.0), (3.5, 0.9), (4.5, 0.9)],
        },
        tol=0.08,
    )


def check_v3_source_linearity_rdac_offset_sweep(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "ck", "d", "vinp", "vinn", "vrefp", "vrefn", "dc0", "dc1", "dc2", "dc3", "dc4", "dc5", "dc6"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing linearity rdac offset sweep signals"
    ok, detail = _sample_many(
        rows,
        {
            "dc0": [(0.5, 1.0), (5.5, 0.0), (10.5, 1.0)],
            "dc1": [(0.5, 1.0), (5.5, 1.0), (10.5, 0.0)],
            "dc2": [(0.5, 1.0), (5.5, 1.0), (10.5, 1.0)],
            "dc6": [(0.5, 1.0), (5.5, 1.0), (10.5, 1.0)],
            "vrefp": [(0.5, 0.365625), (5.5, 0.365625), (10.5, 0.365625)],
            "vrefn": [(0.5, 0.834375), (5.5, 0.834375), (10.5, 0.834375)],
            "vinp": [(0.5, 0.385625), (2.5, 0.380625), (5.5, 0.345625), (8.0, 0.350625), (10.5, 0.345625)],
            "vinn": [(0.5, 0.814375), (2.5, 0.819375), (5.5, 0.854375), (8.0, 0.849375), (10.5, 0.854375)],
        },
        tol=0.012,
    )
    if not ok:
        return ok, detail
    return True, detail


def check_v3_source_sar_das_logic_6b(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {
        "time",
        "clk_sampling",
        "clk_sar",
        "vcomp",
        "d1",
        "d2",
        "d3",
        "d4",
        "d5",
        "d6",
        "db1",
        "db2",
        "db3",
        "db4",
        "db5",
        "db6",
        "co",
        "cob",
    }
    if not rows or not required.issubset(rows[0]):
        return False, "missing sar das logic signals"
    return _sample_many(
        rows,
        {
            "d1": [(1.2, 1.1), (8.0, 1.1)],
            "d2": [(1.2, 1.1), (5.5, 1.1), (8.0, 0.0)],
            "d3": [(1.2, 1.1), (5.5, 0.0), (8.0, 0.0)],
            "d4": [(1.2, 1.1), (3.1, 1.1), (8.0, 1.1)],
            "d5": [(1.2, 1.1), (3.0, 0.0), (8.0, 0.0)],
            "d6": [(1.2, 1.1), (8.0, 1.1)],
            "db1": [(1.2, 1.1), (8.0, 0.0)],
            "db2": [(1.2, 1.1), (8.0, 1.1)],
            "db3": [(1.2, 1.1), (8.0, 1.1)],
            "db4": [(1.2, 1.1), (4.0, 0.0), (8.0, 0.0)],
            "db5": [(1.2, 1.1), (8.0, 1.1)],
            "db6": [(1.2, 1.1), (8.0, 1.1)],
            "co": [(1.7, 1.1), (2.0, 0.0), (4.1, 1.1), (4.5, 0.0)],
            "cob": [(1.7, 0.0), (3.1, 1.1), (3.5, 0.0), (5.3, 1.1)],
        },
        tol=0.09,
    )


def check_v3_source_sar_logic_4b_self_timed(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clkc", "rst", "dcmpp", "dcmpn", "cmpck", "dout1", "dout2", "dout3", "dout4", "dbotp1", "dbotp2", "dbotp3", "dbotn1", "dbotn2", "dbotn3"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing sar logic 4b self timed signals"
    return _sample_many(
        rows,
        {
            "cmpck": [(0.9, 0.0), (1.05, 1.0), (1.5, 0.0), (2.0, 1.0), (3.0, 0.0), (3.5, 0.0)],
            "dout4": [(1.8, 1.0), (4.2, 1.0)],
            "dout3": [(2.5, 0.0), (4.2, 0.0)],
            "dout2": [(3.2, 1.0), (4.2, 1.0)],
            "dout1": [(4.0, 0.0), (4.2, 0.0)],
            "dbotp3": [(0.6, 1.0), (1.8, 0.0), (4.2, 0.0)],
            "dbotn2": [(0.6, 1.0), (2.5, 0.0), (4.2, 0.0)],
            "dbotp1": [(0.6, 1.0), (3.2, 0.0), (4.2, 0.0)],
            "dbotn1": [(0.6, 1.0), (4.2, 1.0)],
        },
        tol=0.09,
    )


def check_v3_source_pfd_tdomain_reset_window(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "in1", "in2", "up", "dn"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing pfd tdomain reset window signals"
    return _sample_many(
        rows,
        {
            "up": [(1.0, 1.0), (1.50, 1.0), (1.70, 0.0), (2.70, 0.0), (3.10, 1.0), (3.45, 0.0)],
            "dn": [(1.0, 0.0), (1.50, 1.0), (1.70, 0.0), (2.70, 1.0), (3.10, 1.0), (3.45, 0.0)],
        },
        tol=0.09,
    )


def check_v3_source_pipe_adc_gain_control_loop(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {
        "time",
        "clks",
        "dout10",
        "dout11",
        "dout12",
        "dout13",
        "gainctrl0",
        "gainctrl1",
        "gainctrl2",
        "gainctrl3",
        "gainctrl4",
        "gainctrl5",
        "gainctrl6",
        "ddiff",
        "dop",
        "dom",
        "gctrlcode",
    }
    if not rows or not required.issubset(rows[0]):
        return False, "missing pipe adc gain control loop signals"
    return _sample_many(
        rows,
        {
            "dout10": [(0.5, 0.9), (1.5, 0.0), (2.5, 0.9), (3.5, 0.0)],
            "dout11": [(0.5, 0.9), (1.5, 0.0), (2.5, 0.9), (3.5, 0.0)],
            "dout12": [(0.5, 0.9), (1.5, 0.0), (2.5, 0.9), (3.5, 0.0)],
            "dout13": [(0.5, 0.0), (1.5, 0.9), (2.5, 0.0), (3.5, 0.9)],
            "gctrlcode": [(0.5, 0.90), (1.5, 0.72), (2.5, 0.72), (3.5, 0.86)],
            "ddiff": [(0.5, 0.0), (1.5, 0.82), (2.5, 0.82), (3.5, 0.50)],
            "dop": [(0.5, 0.96), (1.5, 1.02), (2.5, 1.02), (3.5, 0.90)],
            "dom": [(0.5, 0.20), (1.5, 0.20), (2.5, 0.40), (3.5, 0.40)],
            "gainctrl1": [(1.5, 0.0), (3.5, 0.9)],
            "gainctrl3": [(1.5, 0.9), (3.5, 0.0)],
            "gainctrl4": [(1.5, 0.0), (3.5, 0.9)],
            "gainctrl6": [(1.5, 0.9), (3.5, 0.9)],
        },
        tol=0.09,
    )


def check_v3_source_clock_sample_1600n_sequencer(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "rst", "s", "nc", "res", "conv"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing clock sample 1600n sequencer signals"
    return _sample_many(
        rows,
        {
            "rst": [(0.1, 1.1), (0.5, 0.0), (16.1, 1.1)],
            "s": [(1.4, 1.1), (2.0, 0.0), (9.4, 1.1), (10.0, 0.0)],
            "nc": [(2.1, 1.1), (2.5, 0.0), (10.1, 1.1), (10.5, 0.0)],
            "res": [(3.1, 1.1), (3.4, 0.0), (4.6, 1.1), (4.9, 0.0), (6.1, 1.1), (7.6, 1.1)],
            "conv": [(2.5, 0.0), (3.5, 1.1), (7.5, 0.0), (11.5, 1.1), (15.5, 0.0)],
        },
        tol=0.09,
    )


def check_v3_source_l2_sar_logic_4b(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clkc", "clks", "dcmpp", "dcmpn", "cmpck", "do0", "do1", "do2", "do3", "dctrlp1", "dctrlp2", "dctrlp3", "dctrln1", "dctrln2", "dctrln3"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing l2 sar logic 4b signals"
    return _sample_many(
        rows,
        {
            "cmpck": [(0.95, 1.1), (1.5, 0.0), (2.0, 1.1), (3.2, 1.1), (4.0, 0.0)],
            "do3": [(1.7, 1.1), (4.2, 1.1)],
            "do2": [(2.5, 0.0), (4.2, 0.0)],
            "do1": [(3.2, 1.1), (4.2, 1.1)],
            "do0": [(4.0, 0.0), (4.2, 0.0)],
            "dctrln3": [(1.7, 1.1), (4.2, 1.1)],
            "dctrlp2": [(2.5, 1.1), (4.2, 1.1)],
            "dctrln1": [(3.2, 1.1), (4.2, 1.1)],
            "dctrlp1": [(4.2, 0.0)],
            "dctrlp3": [(4.2, 0.0)],
            "dctrln2": [(4.2, 0.0)],
        },
        tol=0.09,
    )


def check_v3_source_phase_detector_chopper(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vlocal_osc", "vin_rf", "vif"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing phase detector chopper signals"
    return _sample_many(
        rows,
        {"vif": [(0.5, -0.125), (1.5, 0.25), (2.5, 0.20), (3.5, -0.30)]},
        tol=0.015,
    )


def check_v3_source_single_adc_7b_weighted(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "din0", "din1", "din2", "din3", "din4", "din5", "din6", "dout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing single adc 7b weighted signals"
    return _sample_many(
        rows,
        {"dout": [(0.5, 0.0), (1.5, 0.6640625), (2.5, 0.328125), (3.5, 0.9921875)]},
        tol=0.012,
    )


def check_v3_source_qtz_differential_2level(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vinp", "vinn", "vrefp", "vrefn", "clk", "dout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing qtz differential 2level signals"
    return _sample_many(
        rows,
        {"dout": [(0.5, -0.5), (1.5, -0.5), (2.5, 0.5), (3.5, 0.5)]},
        tol=0.03,
    )


def check_v3_source_l2_7b_dac_ready(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "rdy", "din1", "din2", "din3", "din4", "din5", "din6", "din7", "aout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing l2 7b dac ready signals"
    return _sample_many(
        rows,
        {"aout": [(0.5, 0.0), (1.5, -0.9), (2.5, 0.2860465), (3.5, 0.8720930)]},
        tol=0.02,
    )


def check_v3_source_l2_cdac_4b_switch(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "rdy", "din1", "din2", "din3", "din4", "aout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing l2 cdac 4b switch signals"
    return _sample_many(
        rows,
        {"aout": [(0.5, 0.0), (1.5, -1.1), (2.5, 0.1941176), (3.5, 0.8411765)]},
        tol=0.025,
    )


def check_v3_source_cdac_monodown_7b(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vin", "clks", "dctrl3", "dctrl4", "dctrl5", "dctrl6", "dctrl7", "vres"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing cdac monodown 7b signals"
    return _sample_many(
        rows,
        {
            "vres": [(0.5, 0.8), (1.0, 0.8), (1.5, 0.3), (2.1, 0.05), (2.7, -0.075), (3.3, -0.1375), (3.9, -0.16875)],
            "dctrl7": [(1.5, 1.0)],
            "dctrl6": [(2.1, 1.0)],
            "dctrl5": [(2.7, 1.0)],
            "dctrl4": [(3.3, 1.0)],
            "dctrl3": [(3.9, 1.0)],
        },
        tol=0.02,
    )


def check_v3_source_cdac_6b_stage1_up(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vin", "clks", "dctrl2", "dctrl3", "dctrl4", "dctrl5", "vres"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing cdac 6b stage1 up signals"
    return _sample_many(
        rows,
        {
            "vres": [(0.5, 0.2), (1.0, 0.2), (1.5, 0.7), (2.1, 0.95), (2.7, 1.075), (3.3, 1.1375)],
            "dctrl5": [(1.5, 1.0)],
            "dctrl4": [(2.1, 1.0)],
            "dctrl3": [(2.7, 1.0)],
            "dctrl2": [(3.3, 1.0)],
        },
        tol=0.02,
    )


def check_v3_source_adc_zoom_timing_sequencer(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "rst", "s", "sar", "res", "intg", "clk_sar", "zoom", "clk_zoom", "rst_zoom"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing adc zoom timing sequencer signals"
    return _sample_many(
        rows,
        {
            "rst": [(0.6, 1.1), (1.0, 0.0)],
            "s": [(1.8, 1.1), (2.8, 0.0)],
            "sar": [(3.4, 1.1), (5.8, 0.0)],
            "clk_sar": [(3.1, 1.1), (3.4, 0.0), (3.7, 1.1), (4.0, 0.0), (4.3, 1.1), (4.7, 0.0)],
            "res": [(6.3, 1.1), (6.9, 0.0)],
            "intg": [(8.3, 1.1), (9.0, 0.0)],
            "zoom": [(9.6, 1.1), (11.0, 0.0)],
            "clk_zoom": [(9.3, 1.1), (9.6, 0.0), (9.9, 1.1), (10.2, 0.0)],
            "rst_zoom": [(11.2, 1.1), (11.8, 0.0)],
        },
        tol=0.09,
    )


def check_v3_source_l2_sar_logic_7b(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {
        "time", "clkc", "clks", "dcmpp", "dcmpn", "cmpck",
        *{f"do{i}" for i in range(7)},
        *{f"dctrlp{i}" for i in range(1, 7)},
        *{f"dctrln{i}" for i in range(1, 7)},
    }
    if not rows or not required.issubset(rows[0]):
        return False, "missing l2 sar logic 7b signals"
    return _sample_many(
        rows,
        {
            "cmpck": [(0.95, 1.1), (1.5, 0.0), (2.5, 1.1), (4.5, 1.1), (5.6, 0.0), (6.0, 0.0)],
            "do6": [(1.7, 1.1), (6.0, 1.1)],
            "do5": [(2.5, 0.0), (6.0, 0.0)],
            "do4": [(3.2, 1.1), (6.0, 1.1)],
            "do3": [(3.9, 1.1), (6.0, 1.1)],
            "do2": [(4.6, 0.0), (6.0, 0.0)],
            "do1": [(5.25, 0.0), (6.0, 0.0)],
            "do0": [(6.0, 1.1)],
            "dctrln6": [(1.7, 1.1), (6.0, 1.1)],
            "dctrlp5": [(2.5, 1.1), (6.0, 1.1)],
            "dctrln4": [(3.2, 1.1), (6.0, 1.1)],
            "dctrln3": [(3.9, 1.1), (6.0, 1.1)],
            "dctrlp2": [(4.6, 1.1), (6.0, 1.1)],
            "dctrlp1": [(5.25, 1.1), (6.0, 1.1)],
            "dctrlp6": [(6.0, 0.0)],
            "dctrln5": [(6.0, 0.0)],
        },
        tol=0.09,
    )


def check_v3_source_l3_sar2_logic_7b(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {
        "time", "clk", "dp", "dn", "cmpck",
        *{f"do{i}" for i in range(7)},
        *{f"sp{i}" for i in range(1, 7)},
        *{f"sn{i}" for i in range(1, 7)},
    }
    if not rows or not required.issubset(rows[0]):
        return False, "missing l3 sar2 logic 7b signals"
    return _sample_many(
        rows,
        {
            "cmpck": [(0.95, 0.9), (1.5, 0.0), (2.5, 0.9), (4.5, 0.9), (5.6, 0.0), (6.0, 0.0)],
            "do6": [(5.9, 0.9)],
            "do5": [(5.9, 0.0)],
            "do4": [(5.9, 0.9)],
            "do3": [(5.9, 0.0)],
            "do2": [(5.9, 0.9)],
            "do1": [(5.9, 0.9)],
            "do0": [(5.9, 0.0)],
            "sp6": [(0.6, 0.9), (6.0, 0.9)],
            "sn6": [(0.6, 0.9), (1.7, 0.0), (6.0, 0.0)],
            "sn5": [(2.5, 0.9), (6.0, 0.9)],
            "sp4": [(3.2, 0.9), (6.0, 0.9)],
            "sn3": [(3.9, 0.9), (6.0, 0.9)],
            "sp2": [(4.6, 0.9), (6.0, 0.9)],
            "sp1": [(5.25, 0.9), (6.0, 0.9)],
            "sp5": [(6.0, 0.0)],
            "sn4": [(6.0, 0.0)],
        },
        tol=0.08,
    )


def check_v3_source_cdac_8b_monodown(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vin", "clks", "vres", *{f"dctrl{i}" for i in range(1, 8)}}
    if not rows or not required.issubset(rows[0]):
        return False, "missing cdac 8b monodown signals"
    return _sample_many(
        rows,
        {
            "vres": [(0.5, 0.8), (1.0, 0.8), (1.5, 0.3), (2.1, 0.05), (2.7, -0.075), (3.3, -0.1375), (3.9, -0.16875), (4.5, -0.184375), (5.1, -0.1921875)],
            "dctrl7": [(1.5, 1.0)],
            "dctrl6": [(2.1, 1.0)],
            "dctrl5": [(2.7, 1.0)],
            "dctrl4": [(3.3, 1.0)],
            "dctrl3": [(3.9, 1.0)],
            "dctrl2": [(4.5, 1.0)],
            "dctrl1": [(5.1, 1.0)],
        },
        tol=0.02,
    )


def check_v3_source_va_dac_6b_se(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "rdy", "aout", *{f"din{i}" for i in range(6)}}
    if not rows or not required.issubset(rows[0]):
        return False, "missing va dac 6b se signals"
    return _sample_many(
        rows,
        {"aout": [(0.5, -1.0), (1.5, -0.1368421), (2.5, 0.0526316), (3.5, 0.3263158)]},
        tol=0.02,
    )


def check_v3_source_offset_halving_search(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "dcmpp", "vinp", "vinn"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing offset halving search signals"
    return _sample_many(
        rows,
        {
            "vinp": [(0.5, 0.45), (1.0, 0.4), (2.0, 0.425), (3.0, 0.4375), (4.0, 0.43125)],
            "vinn": [(0.5, 0.45), (1.0, 0.5), (2.0, 0.475), (3.0, 0.4625), (4.0, 0.46875)],
        },
        tol=0.01,
    )


def check_v3_source_sar_comparator_reset_high(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "cmpck", "vinn", "vinp", "dcmpn", "dcmpp"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing sar comparator reset high signals"
    return _sample_many(
        rows,
        {
            "dcmpp": [(0.2, 0.9), (0.5, 0.9), (0.95, 0.9), (1.5, 0.0), (1.95, 0.9), (2.5, 0.9)],
            "dcmpn": [(0.2, 0.9), (0.5, 0.0), (0.95, 0.9), (1.5, 0.9), (1.95, 0.9), (2.5, 0.0)],
        },
        tol=0.07,
    )


def check_v3_source_dac_restore_4bit_clocked(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "d3", "d2", "d1", "d0", "vout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing dac restore 4bit clocked signals"
    return _sample_many(
        rows,
        {
            "vout": [(0.5, -0.84375), (1.5, -0.28125), (2.5, 0.28125), (3.5, 0.84375)],
            "d0": [(1.5, 0.9), (2.5, 0.0), (3.5, 0.9)],
            "d1": [(2.5, 0.9), (3.5, 0.9)],
            "d2": [(1.5, 0.9), (2.5, 0.0), (3.5, 0.9)],
            "d3": [(2.5, 0.9), (3.5, 0.9)],
        },
        tol=0.012,
    )


def check_v3_source_dac_restore_7bit_clocked(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "vout", *{f"d{i}" for i in range(7)}}
    if not rows or not required.issubset(rows[0]):
        return False, "missing dac restore 7bit clocked signals"
    return _sample_many(
        rows,
        {"vout": [(0.5, -0.89296875), (1.5, -0.30234375), (2.5, 0.30234375), (3.5, 0.89296875)]},
        tol=0.012,
    )


def check_v3_source_dac_restore_6bit_1p8(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "vout", *{f"d{i}" for i in range(1, 7)}}
    if not rows or not required.issubset(rows[0]):
        return False, "missing dac restore 6bit 1p8 signals"
    return _sample_many(
        rows,
        {"vout": [(0.5, -1.771875), (1.5, -0.590625), (2.5, 0.590625), (3.5, 1.771875)]},
        tol=0.02,
    )


def check_v3_source_sample_hold_5v_clock(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vin", "vclk", "vout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing sample hold 5v clock signals"
    return _sample_many(
        rows,
        {
            "vout": [(0.2, 0.0), (0.5, 0.1), (1.5, 0.65), (2.5, -0.2), (3.5, 0.35)],
            "vclk": [(0.5, 5.0), (0.95, 0.0), (1.5, 5.0)],
        },
        tol=0.02,
    )


def check_v3_source_sum5_signed_sar_weight(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "out", *{f"d{i}" for i in range(1, 6)}}
    if not rows or not required.issubset(rows[0]):
        return False, "missing sum5 signed sar weight signals"
    return _sample_many(
        rows,
        {"out": [(0.5, -3.23125), (1.5, -0.34375), (2.5, 0.06875), (3.5, 1.03125)]},
        tol=0.025,
    )


def check_v3_source_lt_readout_sar4(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vout", "gnd", *{f"d{i}" for i in range(4)}}
    if not rows or not required.issubset(rows[0]):
        return False, "missing lt readout sar4 signals"
    return _sample_many(
        rows,
        {"vout": [(0.5, 0.0), (1.5, 0.5625), (2.5, 1.125), (3.5, 1.6875)]},
        tol=0.02,
    )


def check_v3_source_tool_4bit_sar_signed_dac(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "sh", "aout", *{f"d{i}" for i in range(4)}}
    if not rows or not required.issubset(rows[0]):
        return False, "missing tool 4bit sar signed dac signals"
    return _sample_many(
        rows,
        {"aout": [(0.5, -1.6875), (1.5, 0.5625), (2.5, -0.5625), (3.5, 1.6875)]},
        tol=0.025,
    )


def check_v3_source_dac4bit_small_swing(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vd3", "vd2", "vd1", "vd0", "vout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing dac4bit small swing signals"
    return _sample_many(
        rows,
        {"vout": [(0.5, -0.02), (1.5, -0.0066667), (2.5, 0.0066667), (3.5, 0.02)]},
        tol=0.0015,
    )


def check_v3_source_comparator_reset_low_1p8(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "cmpck", "vinn", "vinp", "dcmpn", "dcmpp"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing comparator reset low 1p8 signals"
    return _sample_many(
        rows,
        {
            "dcmpp": [(0.2, 0.0), (0.55, 1.8), (0.95, 0.0), (1.55, 0.0), (1.95, 0.0), (2.55, 1.8)],
            "dcmpn": [(0.2, 0.0), (0.55, 0.0), (0.95, 0.0), (1.55, 1.8), (1.95, 0.0), (2.55, 0.0)],
        },
        tol=0.08,
    )


def check_v3_source_lt_read_sar6b_weighted(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vout", "gnd", *{f"d{i}" for i in range(6)}}
    if not rows or not required.issubset(rows[0]):
        return False, "missing lt read sar6b weighted signals"
    return _sample_many(
        rows,
        {"vout": [(0.5, -0.9), (1.5, 0.225), (2.5, 0.45), (3.5, 0.73125)]},
        tol=0.02,
    )


def check_v3_source_lt_read_sar7b_weighted(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vout", "gnd", *{f"d{i}" for i in range(8)}}
    if not rows or not required.issubset(rows[0]):
        return False, "missing lt read sar7b weighted signals"
    return _sample_many(
        rows,
        {"vout": [(0.5, -0.9), (1.5, 0.225), (2.5, 0.478125), (3.5, 0.82265625)]},
        tol=0.02,
    )


def check_v3_source_dac_serial_16b_nobridge(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk_sample", "clk_sarready", "data", "out"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing dac serial 16b nobridge signals"
    return _sample_many(
        rows,
        {
            "out": [(0.5, -1.1), (1.1, -0.1290701), (2.1, -0.1290701), (3.1, 0.1136623), (4.1, 0.3563948)],
            "clk_sample": [(0.1, 1.1), (0.35, 0.0), (0.8, 1.1)],
        },
        tol=0.025,
    )


def check_v3_source_sar_13bit_serial_decoder(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "din", "clks", "ready", "dout", "dnum"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing sar 13bit serial decoder signals"
    return _sample_many(
        rows,
        {
            "dout": [(1.0, -0.5), (14.0, -0.5), (15.0, 0.19808326)],
            "dnum": [(1.0, 0.0), (6.5, 3.0), (13.5, 7.0), (15.0, 0.0)],
        },
        tol=0.03,
    )


def check_v3_source_single_shot_timer_pulse(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vin", "vout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing single shot timer pulse signals"
    return _sample_many(
        rows,
        {
            "vout": [(0.5, 0.0), (0.9, 0.9), (2.4, 0.9), (2.9, 0.0), (3.9, 0.9), (5.6, 0.9)],
            "vin": [(0.5, 0.0), (0.9, 0.9), (1.5, 0.0), (3.9, 0.9), (4.5, 0.0)],
        },
        tol=0.08,
    )


def check_v3_source_clocked_comparator_dual_output(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "vinn", "vinp", "outn", "outp"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing clocked comparator dual output signals"
    return _sample_many(
        rows,
        {
            "outp": [(0.45, 1.0), (1.0, 0.0), (1.65, 0.0), (2.25, 0.0)],
            "outn": [(0.45, 0.0), (1.0, 0.0), (1.65, 1.0), (2.25, 0.0)],
        },
        tol=0.05,
    )


def check_v3_source_dac4bit_bipolar_252m(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "d3", "d2", "d1", "d0", "vout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing dac4bit bipolar signals"
    return _sample_many(
        rows,
        {"vout": [(0.5, -0.252), (1.5, -0.2184), (2.5, -0.1848), (3.5, -0.0168)]},
        tol=0.01,
    )


def check_v3_source_bin2ther_2b(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vdd", "gnd", "b1", "b0", "t0", "t1", "t2"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing bin2ther 2b signals"
    return _sample_many(
        rows,
        {
            "t0": [(0.5, 0.0), (1.5, 0.0), (2.5, 0.9), (3.5, 0.9)],
            "t1": [(0.5, 0.0), (1.5, 0.0), (2.5, 0.9), (3.5, 0.9)],
            "t2": [(0.5, 0.0), (1.5, 0.9), (2.5, 0.0), (3.5, 0.9)],
        },
        tol=0.05,
    )


def check_v3_source_dff_set_reset(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "setb", "rstb", "clk", "vdd", "gnd", "d", "q", "qb"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing dff set reset signals"
    return _sample_many(
        rows,
        {
            "q": [(0.7, 0.0), (1.7, 0.9), (2.3, 0.0), (3.0, 0.9), (3.5, 0.0)],
            "qb": [(0.7, 0.9), (1.7, 0.0), (2.3, 0.9), (3.0, 0.0), (3.5, 0.9)],
        },
        tol=0.05,
    )


def check_v3_source_pfd_up_down_state(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "ref", "fb", "up", "down"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing pfd up down state signals"
    return _sample_many(
        rows,
        {
            "up": [(0.7, 0.0), (1.5, 0.0), (2.25, 1.2), (2.65, 0.0)],
            "down": [(0.7, 1.2), (1.5, 0.0), (2.25, 0.0), (2.65, 0.0)],
        },
        tol=0.08,
    )


def check_v3_source_samplehold_rising_edge(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "control", "vin", "vout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing samplehold rising edge signals"
    return _sample_many(
        rows,
        {
            "vin": [(0.3, 1.0), (1.5, 3.0), (2.9, 4.2)],
            "vout": [(0.3, 0.0), (0.8, 1.0), (1.5, 1.0), (2.3, 3.0), (2.9, 3.0)],
        },
        tol=0.05,
    )


def check_v3_source_trim_ctrl_5bit(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "ain", "dout0", "dout1", "dout2", "dout3", "dout4"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing trim ctrl 5bit signals"
    return _sample_many(
        rows,
        {
            "dout0": [(0.5, 0.0), (1.2, 0.9), (2.1, 0.0), (3.0, 0.9)],
            "dout1": [(0.5, 0.0), (1.2, 0.9), (2.1, 0.9), (3.0, 0.9)],
            "dout2": [(0.5, 0.0), (1.2, 0.0), (2.1, 0.0), (3.0, 0.0)],
            "dout3": [(0.5, 0.0), (1.2, 0.0), (2.1, 0.0), (3.0, 0.9)],
            "dout4": [(0.5, 0.0), (1.2, 0.0), (2.1, 0.9), (3.0, 0.9)],
        },
        tol=0.05,
    )


def check_v3_source_therm8_to_bin4_count(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "b0", "b1", "b2", "b3", *{f"th{i}" for i in range(8)}}
    if not rows or not required.issubset(rows[0]):
        return False, "missing therm8 to bin4 count signals"
    return _sample_many(
        rows,
        {
            "b0": [(0.5, 0.0), (1.2, 0.9), (2.1, 0.9), (3.0, 0.0)],
            "b1": [(0.5, 0.0), (1.2, 0.9), (2.1, 0.0), (3.0, 0.0)],
            "b2": [(0.5, 0.0), (1.2, 0.0), (2.1, 0.9), (3.0, 0.0)],
            "b3": [(0.5, 0.0), (1.2, 0.0), (2.1, 0.0), (3.0, 0.9)],
        },
        tol=0.05,
    )


def check_v3_source_coarse_qtz_3bit_residue(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vin", "d0", "d1", "d2", "vres"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing coarse qtz 3bit residue signals"
    return _sample_many(
        rows,
        {
            "d0": [(0.5, 0.0), (1.2, 0.0), (2.1, 0.0), (3.0, 1.0)],
            "d1": [(0.5, 0.0), (1.2, 1.0), (2.1, 0.0), (3.0, 1.0)],
            "d2": [(0.5, 0.0), (1.2, 0.0), (2.1, 1.0), (3.0, 1.0)],
            "vres": [(0.5, 0.0), (1.2, -0.1), (2.1, 0.1), (3.0, 0.15)],
        },
        tol=0.03,
    )


def check_v3_source_rs_phase_detector(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "ref", "fb", "up", "down"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing rs phase detector signals"
    return _sample_many(
        rows,
        {
            "up": [(0.2, 0.0), (0.8, 1.2), (1.4, 0.0), (2.2, 1.2), (2.7, 0.0)],
            "down": [(0.2, 1.2), (0.8, 0.0), (1.4, 1.2), (2.2, 0.0), (2.7, 1.2)],
        },
        tol=0.08,
    )


def check_v3_source_level_shifter_offset(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "sigin", "sigout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing level shifter offset signals"
    return _sample_many(
        rows,
        {
            "sigout": [(0.4, 0.45), (1.2, 0.75), (2.0, 0.15), (2.8, 1.15)],
        },
        tol=0.02,
    )


def check_v3_source_weighted_decoder_6bit(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vd1", "vd2", "vd3", "vd4", "vd5", "vd6", "vout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing weighted decoder 6bit signals"
    return _sample_many(
        rows,
        {
            "vout": [(0.4, 0.0), (1.2, 33.0 / 32.0), (2.0, 18.0 / 32.0), (2.8, 63.0 / 32.0)],
        },
        tol=0.03,
    )


def check_v3_source_divide_by_two_toggle_v2(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "out"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing divide by two toggle signals"
    return _sample_many(
        rows,
        {
            "out": [(0.2, 0.0), (0.8, 0.9), (1.6, 0.0), (2.4, 0.9), (3.2, 0.0), (3.9, 0.9)],
        },
        tol=0.06,
    )


def check_v3_source_accum3_pulse(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "out"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing accum3 pulse signals"
    return _sample_many(
        rows,
        {
            "out": [(0.2, 0.0), (0.8, 0.9), (1.8, 0.0), (7.8, 0.0), (8.8, 0.9), (9.2, 0.9)],
        },
        tol=0.06,
    )


def check_v3_source_xor_phase_detector(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "ref", "fb", "up", "down"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing xor phase detector signals"
    return _sample_many(
        rows,
        {
            "up": [(0.4, 0.0), (1.2, 1.2), (2.0, 0.0), (2.8, 1.2)],
            "down": [(0.4, 1.2), (1.2, 0.0), (2.0, 1.2), (2.8, 0.0)],
        },
        tol=0.06,
    )


def check_v3_source_decision_router_logic(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vin1", "vin2", "valid", "x", "y", "z", "dm", "dl"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing decision router logic signals"
    return _sample_many(
        rows,
        {
            "x": [(0.4, 0.0), (1.2, 0.9), (2.0, 0.0), (2.8, 0.0), (3.5, 0.0)],
            "y": [(0.4, 0.0), (1.2, 0.0), (2.0, 0.0), (2.8, 0.9), (3.5, 0.0)],
            "z": [(0.4, 0.0), (1.2, 0.0), (2.0, 0.9), (2.8, 0.0), (3.5, 0.0)],
            "dm": [(0.4, 0.0), (1.2, 0.0), (2.0, 0.0), (2.8, 0.9), (3.5, 0.9)],
            "dl": [(0.4, 0.0), (1.2, 0.0), (2.0, 0.9), (2.8, 0.0), (3.5, 0.0)],
        },
        tol=0.05,
    )


def check_v3_source_safe_analog_divider(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "signumer", "sigdenom", "sigout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing safe analog divider signals"
    return _sample_many(
        rows,
        {
            "sigout": [(0.4, 0.3), (1.2, 3.0), (2.0, -3.0), (2.8, -0.6)],
        },
        tol=0.04,
    )


def check_v3_source_vargain_diffamp_clip(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "sigin_p", "sigin_n", "sigctrl_p", "sigctrl_n", "sigout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing vargain diffamp clip signals"
    return _sample_many(
        rows,
        {
            "sigout": [(0.4, 0.375), (1.2, 1.0), (2.0, -1.0), (2.8, -0.675)],
        },
        tol=0.04,
    )


def check_v3_source_programmable_divider_by_n(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "divctrl", "out"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing programmable divider by n signals"
    return _sample_many(
        rows,
        {
            "out": [(0.2, 0.9), (0.6, 0.0), (1.4, 0.0), (2.2, 0.9), (3.0, 0.0), (3.8, 0.0), (4.6, 0.9)],
        },
        tol=0.06,
    )


def check_v3_source_pfd_timer_reset(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "a", "b", "ub", "d"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing pfd timer reset signals"
    return _sample_many(
        rows,
        {
            "ub": [(0.2, 0.9), (0.6, 0.0), (1.22, 0.0), (1.4, 0.9), (2.3, 0.9), (2.72, 0.0), (2.9, 0.9)],
            "d": [(0.2, 0.0), (0.6, 0.0), (1.22, 0.9), (1.4, 0.0), (2.3, 0.9), (2.72, 0.9), (2.9, 0.0)],
        },
        tol=0.08,
    )


def check_v3_source_absolute_value(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "sigin", "sigout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing absolute value signals"
    max_err = 0.0
    checked = 0
    for row in rows:
        if row.get("time", 0.0) < 0.2e-9:
            continue
        err = abs(row["sigout"] - abs(row["sigin"]))
        max_err = max(max_err, err)
        checked += 1
    if checked == 0:
        return False, "no_absolute_value_rows_checked"
    return max_err <= 0.02, f"checked={checked} max_abs_error={max_err:.5f}"


def check_v3_source_deadband_voltage(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "sigin", "sigout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing deadband voltage signals"
    return _sample_many(
        rows,
        {"sigout": [(0.4, -0.45), (1.2, 0.0), (2.0, 0.0), (2.8, 0.55)]},
        tol=0.02,
    )


def check_v3_source_deadband_diffamp(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "sigin_p", "sigin_n", "sigout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing deadband diffamp signals"
    return _sample_many(
        rows,
        {"sigout": [(0.4, -0.58), (1.2, 0.02), (2.0, 0.02), (2.8, 1.22)]},
        tol=0.03,
    )


def check_v3_source_limiting_diffamp(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "sigin_p", "sigin_n", "sigout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing limiting diffamp signals"
    return _sample_many(
        rows,
        {"sigout": [(0.4, -0.75), (1.2, -0.4), (2.0, 0.4), (2.8, 0.75)]},
        tol=0.03,
    )


def check_v3_source_smooth_tanh_comparator(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "sigin", "sigref", "sigout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing smooth tanh comparator signals"
    return _sample_many(
        rows,
        {"sigout": [(0.4, -0.975743), (1.2, -0.197375), (2.0, 0.197375), (2.8, 0.995055)]},
        tol=0.03,
    )


def check_v3_source_flash_folded_dac4(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vd4", "vd3", "vd2", "vd1", "vout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing flash folded dac4 signals"
    return _sample_many(
        rows,
        {"vout": [(0.4, 0.5), (1.2, 0.25), (2.0, 0.625), (2.8, 0.9375)]},
        tol=0.03,
    )


def check_v3_source_subradix_dac10(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vd9", "vd8", "vd7", "vd6", "vd5", "vd4", "vd3", "vd2", "vd1", "vd0", "vout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing subradix dac10 signals"
    return _sample_many(
        rows,
        {"vout": [(0.4, 0.0), (1.2, 0.194687), (2.0, 0.118845), (2.8, 0.314313)]},
        tol=0.02,
    )


def check_v3_source_clocked_adc3bit(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vin", "vclk", "vd0", "vd1", "vd2"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing clocked adc3bit signals"
    return _sample_many(
        rows,
        {
            "vd0": [(0.6, 0.0), (1.4, 0.0), (2.2, 0.0), (2.9, 0.9)],
            "vd1": [(0.6, 0.0), (1.4, 0.9), (2.2, 0.0), (2.9, 0.9)],
            "vd2": [(0.6, 0.0), (1.4, 0.0), (2.2, 0.9), (2.9, 0.9)],
        },
        tol=0.06,
    )


def check_v3_source_cal4bit_modulo(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "ain", "d0", "d1", "d2", "d3"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing cal4bit modulo signals"
    return _sample_many(
        rows,
        {
            "d0": [(0.4, 0.0), (1.2, 0.9), (2.0, 0.0), (2.8, 0.9)],
            "d1": [(0.4, 0.0), (1.2, 0.9), (2.0, 0.9), (2.8, 0.9)],
            "d2": [(0.4, 0.0), (1.2, 0.0), (2.0, 0.0), (2.8, 0.9)],
            "d3": [(0.4, 0.0), (1.2, 0.0), (2.0, 0.9), (2.8, 0.9)],
        },
        tol=0.06,
    )


def check_v3_source_mux4_priority(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "sel0", "sel1", "in0", "in1", "in2", "in3", "out"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing mux4 priority signals"
    return _sample_many(
        rows,
        {"out": [(0.4, 0.1), (1.2, 0.4), (2.0, -0.2), (2.8, 0.8)]},
        tol=0.02,
    )


def check_v3_source_xnor_gate_voltage(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vin1", "vin2", "vout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing xnor gate voltage signals"
    return _sample_many(
        rows,
        {"vout": [(0.4, 0.9), (1.2, 0.0), (2.0, 0.0), (2.8, 0.9)]},
        tol=0.06,
    )


def check_v3_source_bipolar_dff_sample(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vin_d", "vclk", "vout_q", "vout_qbar"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing bipolar dff sample signals"
    return _sample_many(
        rows,
        {
            "vout_q": [(0.6, -1.0), (1.4, 1.0), (2.2, -1.0), (2.9, 1.0)],
            "vout_qbar": [(0.6, 1.0), (1.4, -1.0), (2.2, 1.0), (2.9, -1.0)],
        },
        tol=0.08,
    )


def check_v3_source_pfd_active_low_reset(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "ref", "fb", "upb", "down"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing pfd active low reset signals"
    return _sample_many(
        rows,
        {
            "upb": [(0.2, 0.9), (0.7, 0.0), (1.1, 0.0), (1.25, 0.9), (2.1, 0.9), (2.5, 0.0), (2.7, 0.9)],
            "down": [(0.2, 0.0), (0.7, 0.0), (1.1, 0.9), (1.25, 0.0), (2.1, 0.9), (2.5, 0.9), (2.7, 0.0)],
        },
        tol=0.08,
    )


def _checker_float_param(params: dict[str, object], key: str, default: float) -> float:
    value = params.get(key, default)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _checker_float_list_param(params: dict[str, object], key: str, default: list[float]) -> list[float]:
    value = params.get(key)
    if not isinstance(value, list):
        return default
    parsed: list[float] = []
    for item in value:
        try:
            parsed.append(float(item))
        except (TypeError, ValueError):
            return default
    return parsed or default


def check_v2_configured_first_order_lowpass(
    rows: list[dict[str, float]],
    params: dict[str, object],
) -> tuple[bool, str]:
    required = {"time", "vin", "vout"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/vin/vout"

    vin_pre_time = _checker_float_param(params, "vin_pre_sample_ns", 10.0) * 1e-9
    vin_post_time = _checker_float_param(params, "vin_post_sample_ns", 30.0) * 1e-9
    vin_late_time = _checker_float_param(params, "vin_late_sample_ns", 150.0) * 1e-9
    vin_pre = sample_signal_at(rows, "vin", vin_pre_time)
    vin_post = sample_signal_at(rows, "vin", vin_post_time)
    vin_late = sample_signal_at(rows, "vin", vin_late_time)
    if vin_pre is None or vin_post is None or vin_late is None:
        return False, "missing_vin_step_samples"
    input_step = (
        vin_pre < _checker_float_param(params, "vin_pre_max_v", 0.10)
        and vin_post > _checker_float_param(params, "vin_post_min_v", 0.72)
        and vin_late > _checker_float_param(params, "vin_late_min_v", 0.72)
    )

    sample_times_ns = _checker_float_list_param(params, "sample_times_ns", [30.0, 50.0, 90.0, 150.0])
    if len(sample_times_ns) < 4:
        return False, f"too_few_configured_sample_times={len(sample_times_ns)}"
    samples: list[float] = []
    for t_ns in sample_times_ns:
        value = sample_signal_at(rows, "vout", t_ns * 1e-9)
        if value is None:
            return False, f"missing_sample_at={t_ns:g}ns"
        samples.append(value)

    tail_slack = _checker_float_param(params, "monotonic_tail_slack_v", 0.03)
    monotonic = samples[0] < samples[1] < samples[2] <= samples[3] + tail_slack
    response_fast_enough = (
        samples[1] > _checker_float_param(params, "response_sample_1_min_v", 0.55)
        and samples[2] > _checker_float_param(params, "response_sample_2_min_v", 0.70)
        and samples[3] > _checker_float_param(params, "response_sample_3_min_v", 0.76)
    )
    not_instant = samples[0] < _checker_float_param(params, "not_instant_sample_0_max_v", 0.45)
    bounded_start = _checker_float_param(params, "bounded_start_ns", 22.0) * 1e-9
    post_rows = [row for row in rows if row.get("time", 0.0) >= bounded_start and "vout" in row]
    bounded_min = _checker_float_param(params, "bounded_min_v", -0.03)
    bounded_max = _checker_float_param(params, "bounded_max_v", 0.88)
    bounded = bool(post_rows) and bounded_min <= min(row["vout"] for row in post_rows) <= max(
        row["vout"] for row in post_rows
    ) <= bounded_max
    ok = input_step and monotonic and response_fast_enough and not_instant and bounded
    values = ",".join(f"{value:.3f}" for value in samples[:4])
    return ok, (
        f"configured_lowpass_samples={values} input_step={input_step} monotonic={monotonic} "
        f"response_fast_enough={response_fast_enough} not_instant={not_instant} bounded={bounded}"
    )


def weighted_logic_high_fraction(rows: list[dict[str, float]], signal: str, threshold: float) -> float:
    if len(rows) < 2:
        return 0.0
    total_dt = rows[-1]["time"] - rows[0]["time"]
    if total_dt <= 0.0:
        return 0.0

    high_dt = 0.0
    for idx in range(1, len(rows)):
        dt = rows[idx]["time"] - rows[idx - 1]["time"]
        if dt <= 0.0:
            continue
        v_mid = 0.5 * (rows[idx - 1][signal] + rows[idx][signal])
        if v_mid > threshold:
            high_dt += dt
    return high_dt / total_dt


def time_window(rows: list[dict[str, float]], t_start: float, t_end: float) -> list[dict[str, float]]:
    return [r for r in rows if t_start <= r["time"] <= t_end]


def weighted_logic_high_fraction_window(
    rows: list[dict[str, float]],
    signal: str,
    threshold: float,
    t_start: float,
    t_end: float,
) -> float:
    return weighted_logic_high_fraction(time_window(rows, t_start, t_end), signal, threshold)


def check_pfd_updn(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows or not {"ref", "div", "up", "dn"}.issubset(rows[0]):
        return False, "missing ref/div/up/dn"
    vth = max(r["ref"] for r in rows) * 0.5
    up = [1 if r["up"] > vth else 0 for r in rows]
    dn = [1 if r["dn"] > vth else 0 for r in rows]
    up_frac = weighted_logic_high_fraction(rows, "up", vth)
    dn_frac = weighted_logic_high_fraction(rows, "dn", vth)
    both_hi = [a & b for a, b in zip(up, dn)]
    run_len = 0
    max_run = 0
    for b in both_hi:
        if b:
            run_len += 1
            max_run = max(max_run, run_len)
        else:
            run_len = 0
    up_pulses = sum(1 for i in range(1, len(up)) if up[i - 1] == 0 and up[i] == 1)
    if max_run > 5:
        return False, f"overlap_too_long={max_run}"
    if up_frac < 0.01:
        return False, f"up_never_high up_frac={up_frac:.3f}"
    if up_frac < dn_frac:
        return False, f"up_frac_lt_dn_frac up={up_frac:.3f} dn={dn_frac:.3f}"
    if up_pulses < 10:
        return False, f"too_few_up_pulses={up_pulses}"
    return True, f"up_frac={up_frac:.3f} dn_frac={dn_frac:.3f} up_pulses={up_pulses}"


def check_pfd_deadzone(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows or not {"ref", "div", "up", "dn"}.issubset(rows[0]):
        return False, "missing ref/div/up/dn"
    vth = max(r["ref"] for r in rows) * 0.5
    up = [1 if r["up"] > vth else 0 for r in rows]
    dn = [1 if r["dn"] > vth else 0 for r in rows]
    up_frac = weighted_logic_high_fraction(rows, "up", vth)
    dn_frac = weighted_logic_high_fraction(rows, "dn", vth)
    both_hi = [a & b for a, b in zip(up, dn)]

    run_len = 0
    max_run = 0
    for bit in both_hi:
        if bit:
            run_len += 1
            max_run = max(max_run, run_len)
        else:
            run_len = 0

    up_pulses = sum(1 for i in range(1, len(up)) if up[i - 1] == 0 and up[i] == 1)
    if not (0.001 <= up_frac <= 0.03):
        return False, f"up_frac_out_of_range={up_frac:.4f}"
    if dn_frac > 0.002:
        return False, f"dn_frac_too_high={dn_frac:.4f}"
    if max_run > 6:
        return False, f"overlap_too_long={max_run}"
    if up_pulses < 10:
        return False, f"too_few_up_pulses={up_pulses}"
    return True, f"up_frac={up_frac:.4f} dn_frac={dn_frac:.4f} up_pulses={up_pulses}"


def check_pfd_small_phase_error_response(rows: list[dict[str, float]]) -> tuple[bool, str]:
    return check_pfd_deadzone(rows)


_RELEASE_SIMPLE_BINARY_DAC_CODES = tuple(range(16))
_RELEASE_SIMPLE_BINARY_DAC_SAMPLE_TIMES_NS = tuple(5.0 + 10.0 * idx for idx in range(16))


def check_simple_binary_dac_4b(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "aout", "code_0", "code_1", "code_2", "code_3"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/aout/code_0/code_1/code_2/code_3"
    expected = [0.9 * code / 15.0 for code in _RELEASE_SIMPLE_BINARY_DAC_CODES]
    observed: list[float] = []
    observed_codes: list[int] = []
    code_mismatches = 0
    for t_ns, expected_code in zip(_RELEASE_SIMPLE_BINARY_DAC_SAMPLE_TIMES_NS, _RELEASE_SIMPLE_BINARY_DAC_CODES):
        value = sample_signal_at(rows, "aout", t_ns * 1e-9)
        if value is None:
            return False, f"missing_sample_at={t_ns:g}ns"
        observed_code = 0
        for bit_idx in range(4):
            bit_value = sample_signal_at(rows, f"code_{bit_idx}", t_ns * 1e-9)
            if bit_value is None:
                return False, f"missing_code_{bit_idx}_sample_at={t_ns:g}ns"
            if bit_value > 0.45:
                observed_code |= 1 << bit_idx
        if observed_code != expected_code:
            code_mismatches += 1
        observed_codes.append(observed_code)
        observed.append(value)
    max_err = max(abs(got - want) for got, want in zip(observed, expected))
    monotonic = all(b >= a - 1e-3 for a, b in zip(observed, observed[1:]))
    zero_scale_ok = abs(observed[0]) <= 0.02
    full_scale_ok = abs(observed[-1] - 0.90) <= 0.02
    ok = max_err <= 0.02 and monotonic and zero_scale_ok and full_scale_ok and code_mismatches == 0
    obs_text = ",".join(f"{value:.3f}" for value in observed)
    exp_text = ",".join(f"{value:.3f}" for value in expected)
    code_text = ",".join(str(code) for code in observed_codes)
    return ok, (
        f"simple_binary_dac_levels={obs_text} expected={exp_text} "
        f"observed_codes={code_text} code_mismatches={code_mismatches} "
        f"max_err={max_err:.3f} monotonic={monotonic} "
        f"zero_scale_ok={zero_scale_ok} full_scale_ok={full_scale_ok}"
    )


def check_pfd_reset_race(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows or not {"ref", "div", "up", "dn"}.issubset(rows[0]):
        return False, "missing ref/div/up/dn"

    vth = max(r["ref"] for r in rows) * 0.5
    first = time_window(rows, 20e-9, 120e-9)
    second = time_window(rows, 160e-9, 260e-9)
    if len(first) < 4 or len(second) < 4:
        return False, "insufficient_window_samples"

    up_first = weighted_logic_high_fraction(first, "up", vth)
    dn_first = weighted_logic_high_fraction(first, "dn", vth)
    up_second = weighted_logic_high_fraction(second, "up", vth)
    dn_second = weighted_logic_high_fraction(second, "dn", vth)

    first_times = [r["time"] for r in first]
    second_times = [r["time"] for r in second]
    up_pulses_first = len(rising_edges([r["up"] for r in first], first_times, threshold=vth))
    dn_pulses_second = len(rising_edges([r["dn"] for r in second], second_times, threshold=vth))

    overlap_dt = 0.0
    total_dt = 0.0
    for idx in range(1, len(rows)):
        dt = rows[idx]["time"] - rows[idx - 1]["time"]
        if dt <= 0.0:
            continue
        total_dt += dt
        up_mid = 0.5 * (rows[idx - 1]["up"] + rows[idx]["up"])
        dn_mid = 0.5 * (rows[idx - 1]["dn"] + rows[idx]["dn"])
        if up_mid > vth and dn_mid > vth:
            overlap_dt += dt
    overlap_frac = overlap_dt / max(total_dt, 1e-18)

    ok = (
        0.001 <= up_first <= 0.08
        and dn_first <= 0.01
        and 0.001 <= dn_second <= 0.08
        and up_second <= 0.01
        and up_pulses_first >= 4
        and dn_pulses_second >= 4
        and overlap_frac <= 0.01
    )
    return ok, (
        f"up_first={up_first:.4f} dn_first={dn_first:.4f} "
        f"up_second={up_second:.4f} dn_second={dn_second:.4f} "
        f"up_pulses_first={up_pulses_first} dn_pulses_second={dn_pulses_second} "
        f"overlap_frac={overlap_frac:.4f}"
    )


def check_cppll_freq_step_reacquire(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"ref_clk", "fb_clk", "lock", "vctrl_mon"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing ref_clk/fb_clk/lock/vctrl_mon"

    vth = 0.45
    times = [r["time"] for r in rows]
    ref_edges = rising_edges([r["ref_clk"] for r in rows], times, threshold=vth)
    fb_edges = rising_edges([r["fb_clk"] for r in rows], times, threshold=vth)
    if len(ref_edges) < 12 or len(fb_edges) < 12:
        return False, f"not_enough_edges ref={len(ref_edges)} fb={len(fb_edges)}"

    ref_late = [t for t in ref_edges if 4.5e-6 <= t <= 5.9e-6]
    fb_late = [t for t in fb_edges if 4.5e-6 <= t <= 5.9e-6]
    if len(ref_late) < 4 or len(fb_late) < 4:
        return False, (
            f"not_enough_late_edges ref_late={len(ref_late)} fb_late={len(fb_late)}"
        )

    ref_periods = [b - a for a, b in zip(ref_late, ref_late[1:])]
    fb_periods = [b - a for a, b in zip(fb_late, fb_late[1:])]
    ref_period = sum(ref_periods) / len(ref_periods)
    fb_period = sum(fb_periods) / len(fb_periods)
    if ref_period <= 0.0 or fb_period <= 0.0:
        return False, "non_positive_period"
    freq_ratio = ref_period / fb_period

    lock_edges = rising_edges([r["lock"] for r in rows], times, threshold=vth)
    pre_lock_edges = [t for t in lock_edges if t < 2.0e-6]
    post_lock_edges = [t for t in lock_edges if 2.2e-6 <= t <= 5.9e-6]
    relock_time = post_lock_edges[0] if post_lock_edges else float("nan")

    disturb_low_frac = 1.0 - weighted_logic_high_fraction_window(
        rows, "lock", vth, 2.05e-6, 2.8e-6
    )

    vctrl_vals = [r["vctrl_mon"] for r in rows]
    vctrl_min = min(vctrl_vals)
    vctrl_max = max(vctrl_vals)
    vctrl_in_range = all(-1e-6 <= v <= 0.95 for v in vctrl_vals)

    ok = (
        bool(pre_lock_edges)
        and disturb_low_frac >= 0.25
        and bool(post_lock_edges)
        and 0.97 <= freq_ratio <= 1.03
        and vctrl_in_range
    )
    return ok, (
        f"pre_lock_edges={len(pre_lock_edges)} "
        f"disturb_lock_low_frac={disturb_low_frac:.3f} "
        f"post_lock_edges={len(post_lock_edges)} "
        f"late_freq_ratio={freq_ratio:.4f} "
        f"relock_time={(relock_time if post_lock_edges else float('nan')):.3e} "
        f"vctrl_min={vctrl_min:.3f} "
        f"vctrl_max={vctrl_max:.3f}"
    )


def check_gray_counter_4b(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"clk", "rstb", "g3", "g2", "g1", "g0"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing clk/rstb/g3/g2/g1/g0"
    vth = max(r["clk"] for r in rows) * 0.5
    clk = [r["clk"] for r in rows]
    times_ns = [r["time"] * 1e9 for r in rows]
    edge_idx = [i for i in range(1, len(clk)) if clk[i - 1] <= vth < clk[i]]
    codes: list[int] = []
    for idx in edge_idx:
        settle = min(idx + 8, len(rows) - 1)
        code = (
            (1 if rows[settle]["g3"] > vth else 0) << 3
            | (1 if rows[settle]["g2"] > vth else 0) << 2
            | (1 if rows[settle]["g1"] > vth else 0) << 1
            | (1 if rows[settle]["g0"] > vth else 0)
        )
        codes.append(code)
    post_reset = [codes[i] for i, idx in enumerate(edge_idx) if times_ns[idx] > 55.0]
    if len(post_reset) < 20:
        return False, f"not_enough_post_reset_edges={len(post_reset)}"
    bad_transitions = 0
    for a, b in zip(post_reset[:-1], post_reset[1:]):
        if bin(a ^ b).count("1") != 1:
            bad_transitions += 1
    unique_codes = set(post_reset)
    expected_grays = {i ^ (i >> 1) for i in range(16)}
    if bad_transitions > 0:
        return False, f"gray_property_violated bad_transitions={bad_transitions}"
    if not expected_grays.issubset(unique_codes):
        return False, f"missing_gray_codes count={16 - len(expected_grays & unique_codes)}"
    return True, f"unique_codes={len(unique_codes)} bad_transitions={bad_transitions}"


def check_gray_counter_one_bit_change(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows:
        return False, "empty"
    sample = rows[0]
    clk_col = _pick_column(sample, ["clk", "CLK"])
    rst_col = _pick_column(sample, ["rst", "RST", "rstb", "RSTB"])
    if clk_col is None or rst_col is None:
        return False, "missing clk/rst"

    g_cols = [_pick_column(sample, [f"g{idx}", f"G{idx}"]) for idx in range(4)]
    if any(col is None for col in g_cols):
        return False, "missing g0..g3"

    threshold = 0.45
    clk = [r[clk_col] for r in rows]
    edge_idx = [i for i in range(1, len(clk)) if clk[i - 1] <= threshold < clk[i]]
    if len(edge_idx) < 20:
        return False, f"not_enough_clk_edges={len(edge_idx)}"

    rst_high_active = any(r[rst_col] > threshold for r in rows[: max(4, len(rows) // 10)])
    post_reset_codes: list[int] = []
    for idx in edge_idx:
        settle = min(idx + 8, len(rows) - 1)
        rst_val = rows[settle][rst_col]
        if (rst_high_active and rst_val > threshold) or ((not rst_high_active) and rst_val < threshold):
            continue
        code = 0
        for bit_idx, col in enumerate(g_cols):
            if rows[settle][col] > threshold:
                code |= 1 << bit_idx
        post_reset_codes.append(code)

    if len(post_reset_codes) < 16:
        return False, f"not_enough_post_reset_codes={len(post_reset_codes)}"

    bad_transitions = sum(1 for a, b in zip(post_reset_codes[:-1], post_reset_codes[1:]) if bin(a ^ b).count("1") != 1)
    unique_codes = set(post_reset_codes)
    expected_grays = {i ^ (i >> 1) for i in range(16)}
    if bad_transitions:
        return False, f"gray_property_violated bad_transitions={bad_transitions}"
    if not expected_grays.issubset(unique_codes):
        return False, f"missing_gray_codes count={16 - len(expected_grays & unique_codes)}"
    return True, f"unique_codes={len(unique_codes)} bad_transitions={bad_transitions}"


def check_prbs7(rows: list[dict[str, float]]) -> tuple[bool, str]:
    """PRBS-7: require the exposed state bus to follow the public tap relation."""
    if not rows:
        return False, "empty"
    required = {"clk", "rst_n", "en", "serial_out"} | {f"state_{idx}" for idx in range(7)}
    missing = required - set(rows[0])
    if missing:
        return False, f"missing_columns={','.join(sorted(missing))}"

    def logic(row: dict[str, float], name: str) -> int | None:
        value = row[name]
        if value >= 0.7:
            return 1
        if value <= 0.2:
            return 0
        return None

    def state_code(row: dict[str, float]) -> int | None:
        code = 0
        for idx in range(7):
            bit = logic(row, f"state_{idx}")
            if bit is None:
                return None
            code |= bit << idx
        return code

    post = [row for row in rows if row["time"] > 2e-9 and row["rst_n"] > 0.7 and row["en"] > 0.7]
    if len(post) < 20:
        return False, "too_few_post_init_samples"

    stable_codes: list[int] = []
    serial_bits: list[int] = []
    for row in post:
        code = state_code(row)
        serial = logic(row, "serial_out")
        if code is None or serial is None:
            continue
        if serial != ((code >> 6) & 1):
            return False, f"serial_state_mismatch code={code}"
        if not stable_codes or stable_codes[-1] != code:
            stable_codes.append(code)
            serial_bits.append(serial)

    if len(stable_codes) < 10:
        return False, f"unique_state_steps={len(stable_codes)}"
    if 0 in stable_codes:
        return False, "entered_zero_state"

    mismatches = 0
    checked = 0
    for current, observed_next in zip(stable_codes, stable_codes[1:]):
        # Public reference recurrence used by the release gold:
        # new state_0 = old state_6 XOR old state_5; higher bits shift up.
        feedback = ((current >> 6) & 1) ^ ((current >> 5) & 1)
        expected_next = ((current & 0x3F) << 1) | feedback
        checked += 1
        if observed_next != expected_next:
            mismatches += 1

    serial_transitions = sum(1 for idx in range(len(serial_bits) - 1) if serial_bits[idx] != serial_bits[idx + 1])
    ok = checked >= 8 and mismatches == 0 and serial_transitions >= 3
    return ok, (
        f"state_steps={len(stable_codes)} checked_transitions={checked} "
        f"mismatches={mismatches} serial_transitions={serial_transitions}"
    )


def check_therm2bin(rows: list[dict[str, float]]) -> tuple[bool, str]:
    """Thermometer-to-binary: check all 4 output bits are high in final window (all 15 inputs on)."""
    if not rows:
        return False, "empty"
    b_cols = [k for k in rows[0] if k.lower() in {"b3", "b2", "b1", "b0", "bin_3", "bin_2", "bin_1", "bin_0"}]
    if len(b_cols) < 4:
        return False, f"missing b3..b0; got {list(rows[0].keys())[:12]}"
    b_cols = sorted(
        b_cols,
        key=lambda name: int(re.findall(r"(\d+)$", name)[0]),
    )[:4]
    t_end = rows[-1]["time"]
    late = [r for r in rows if r["time"] > t_end * 0.75]
    if not late:
        return False, "no late-window rows"
    all_high = all(r[c] > 0.45 for r in late for c in b_cols)
    return all_high, f"all_bits_high_final_window={all_high}"


def check_sar_logic(rows: list[dict[str, float]]) -> tuple[bool, str]:
    """10-bit SAR logic: check RDY asserts and DP_DAC bits show activity."""
    if not rows:
        return False, "empty"
    rdy_col = next((k for k in rows[0] if k.lower() in {"rdy", "ready", "eoc", "done"}), None)
    if rdy_col is None:
        return False, f"missing rdy/eoc column; keys={list(rows[0].keys())[:10]}"
    rdy_vals = [r[rdy_col] for r in rows]
    rdy_high = any(v > 0.45 for v in rdy_vals)
    dac_cols = [k for k in rows[0] if re.search(r"dp_dac|dp_n|dp_p|dac_bit|cap", k.lower())]
    dac_activity = False
    for col in dac_cols[:4]:
        vals = [r[col] for r in rows]
        if max(vals) - min(vals) > 0.4:
            dac_activity = True
            break
    ok = rdy_high and dac_activity
    return ok, f"rdy_asserted={rdy_high} dac_activity={dac_activity}"


def check_pipeline_stage(rows: list[dict[str, float]]) -> tuple[bool, str]:
    """1.5-bit MDAC: verify sub-ADC decisions and gain-of-2 residue."""
    required = {"time", "phi1", "phi2", "vin", "vres", "d1", "d0"}
    if not rows or not required.issubset(rows[0]):
        missing = sorted(required - set(rows[0].keys())) if rows else sorted(required)
        return False, f"missing_columns={','.join(missing)}"

    vth = 0.45
    times = [r["time"] for r in rows]
    phi2_edges = rising_edges([r["phi2"] for r in rows], times, threshold=vth)
    sample_rows = sample_rows_at_or_after_times(rows, [edge_t + 0.8e-9 for edge_t in phi2_edges])
    if len(sample_rows) < 3:
        return False, f"phi2_samples={len(sample_rows)}"

    region_counts = {"upper": 0, "middle": 0, "lower": 0}
    bit_mismatches = 0
    residue_mismatches = 0
    bounded_failures = 0
    max_residue_err = 0.0

    for row in sample_rows:
        vin = row["vin"]
        vin_rel = vin - 0.45
        if vin_rel > 0.9 / 4.0:
            region = "upper"
            exp_d1, exp_d0 = 1, 0
            exp_vres = 0.45 + 2.0 * vin_rel - 0.9 / 2.0
        elif vin_rel < -0.9 / 4.0:
            region = "lower"
            exp_d1, exp_d0 = 0, 0
            exp_vres = 0.45 + 2.0 * vin_rel + 0.9 / 2.0
        else:
            region = "middle"
            exp_d1, exp_d0 = 0, 1
            exp_vres = 0.45 + 2.0 * vin_rel
        exp_vres = min(0.9, max(0.0, exp_vres))
        region_counts[region] += 1

        got_d1 = 1 if row["d1"] >= vth else 0
        got_d0 = 1 if row["d0"] >= vth else 0
        if (got_d1, got_d0) != (exp_d1, exp_d0):
            bit_mismatches += 1

        err = abs(row["vres"] - exp_vres)
        max_residue_err = max(max_residue_err, err)
        if err > 0.04:
            residue_mismatches += 1
        if row["vres"] < -0.02 or row["vres"] > 0.92:
            bounded_failures += 1

    missing_regions = [name for name, count in region_counts.items() if count == 0]
    ok = (
        not missing_regions
        and bit_mismatches == 0
        and residue_mismatches == 0
        and bounded_failures == 0
    )
    return ok, (
        f"regions=upper:{region_counts['upper']},middle:{region_counts['middle']},lower:{region_counts['lower']} "
        f"bit_mismatches={bit_mismatches} "
        f"residue_mismatches={residue_mismatches} "
        f"max_residue_err={max_residue_err:.4f} "
        f"bounded_failures={bounded_failures}"
    )


def _pipeline_adc_chain_stage_code(value: float, *, vrefp: float = 0.9, vrefn: float = 0.0) -> int:
    span = vrefp - vrefn
    if value < vrefn + span * 0.25:
        return 0
    if value < vrefn + span * 0.50:
        return 1
    if value < vrefn + span * 0.75:
        return 2
    return 3


def _pipeline_adc_chain_expected(vin: float, *, vrefp: float = 0.9, vrefn: float = 0.0) -> tuple[int, int, int, float, float]:
    span = vrefp - vrefn
    vin = min(vrefp, max(vrefn, vin))
    s1_code = _pipeline_adc_chain_stage_code(vin, vrefp=vrefp, vrefn=vrefn)
    center1 = vrefn + (s1_code + 0.5) * span / 4.0
    res1 = (vrefp + vrefn) / 2.0 + 4.0 * (vin - center1)
    res1 = min(vrefp, max(vrefn, res1))

    s2_code = _pipeline_adc_chain_stage_code(res1, vrefp=vrefp, vrefn=vrefn)
    center2 = vrefn + (s2_code + 0.5) * span / 4.0
    res2 = (vrefp + vrefn) / 2.0 + 4.0 * (res1 - center2)
    res2 = min(vrefp, max(vrefn, res2))

    final_code = 4 * s1_code + s2_code
    return s1_code, s2_code, final_code, res1, res2


def check_release_pipeline_adc_chain(rows: list[dict[str, float]]) -> tuple[bool, str]:
    """Release L2 pipeline ADC: verify two-stage decisions, residues, and final code."""
    required = {
        "time",
        "vin",
        "clk",
        "res1",
        "res2",
        "s1b1",
        "s1b0",
        "s2b1",
        "s2b0",
        "dout3",
        "dout2",
        "dout1",
        "dout0",
    }
    if not rows or not required.issubset(rows[0]):
        missing = sorted(required - set(rows[0].keys())) if rows else sorted(required)
        return False, f"missing_columns={','.join(missing)}"

    vth = 0.45
    times = [row["time"] for row in rows]
    edge_times = rising_edges([row["clk"] for row in rows], times, threshold=vth)
    sample_rows = sample_rows_at_or_after_times(rows, [edge_t + 0.8e-9 for edge_t in edge_times])
    if len(sample_rows) < 16:
        return False, f"too_few_settled_samples={len(sample_rows)}"

    observed_codes: list[int] = []
    expected_codes: list[int] = []
    stage_bit_mismatches = 0
    final_concat_mismatches = 0
    final_code_mismatches = 0
    residue_mismatches = 0
    bounded_failures = 0
    max_res1_err = 0.0
    max_res2_err = 0.0
    res2_values: list[float] = []

    for row in sample_rows:
        exp_s1, exp_s2, exp_final, exp_res1, exp_res2 = _pipeline_adc_chain_expected(row["vin"])
        got_s1 = ((1 if row["s1b1"] >= vth else 0) << 1) | (1 if row["s1b0"] >= vth else 0)
        got_s2 = ((1 if row["s2b1"] >= vth else 0) << 1) | (1 if row["s2b0"] >= vth else 0)
        got_final = (
            ((1 if row["dout3"] >= vth else 0) << 3)
            | ((1 if row["dout2"] >= vth else 0) << 2)
            | ((1 if row["dout1"] >= vth else 0) << 1)
            | (1 if row["dout0"] >= vth else 0)
        )
        got_concat = 4 * got_s1 + got_s2

        if got_s1 != exp_s1 or got_s2 != exp_s2:
            stage_bit_mismatches += 1
        if got_final != got_concat:
            final_concat_mismatches += 1
        if got_final != exp_final:
            final_code_mismatches += 1

        res1_err = abs(row["res1"] - exp_res1)
        res2_err = abs(row["res2"] - exp_res2)
        max_res1_err = max(max_res1_err, res1_err)
        max_res2_err = max(max_res2_err, res2_err)
        if res1_err > 0.04 or res2_err > 0.04:
            residue_mismatches += 1
        if row["res1"] < -0.02 or row["res1"] > 0.92 or row["res2"] < -0.02 or row["res2"] > 0.92:
            bounded_failures += 1

        observed_codes.append(got_final)
        expected_codes.append(exp_final)
        res2_values.append(row["res2"])

    observed_unique = sorted(set(observed_codes))
    expected_unique = sorted(set(expected_codes))
    reversals = sum(1 for prev, curr in zip(observed_codes, observed_codes[1:]) if curr < prev)
    res2_span = max(res2_values) - min(res2_values) if res2_values else 0.0
    ok = (
        observed_unique == list(range(16))
        and expected_unique == list(range(16))
        and stage_bit_mismatches == 0
        and final_concat_mismatches == 0
        and final_code_mismatches == 0
        and residue_mismatches == 0
        and bounded_failures == 0
        and reversals == 0
        and res2_span > 0.20
    )
    return ok, (
        f"observed_codes={','.join(str(code) for code in observed_unique)} "
        f"expected_codes={','.join(str(code) for code in expected_unique)} "
        f"stage_bit_mismatches={stage_bit_mismatches} "
        f"final_concat_mismatches={final_concat_mismatches} "
        f"final_code_mismatches={final_code_mismatches} "
        f"residue_mismatches={residue_mismatches} "
        f"max_res1_err={max_res1_err:.4f} "
        f"max_res2_err={max_res2_err:.4f} "
        f"res2_span={res2_span:.4f} "
        f"reversals={reversals} "
        f"bounded_failures={bounded_failures}"
    )


def check_sar_12bit(rows: list[dict[str, float]]) -> tuple[bool, str]:
    """12-bit SAR: check EOC/RDY asserts and DAC bits show activity."""
    return check_sar_logic(rows)


def check_segmented_dac(rows: list[dict[str, float]]) -> tuple[bool, str]:
    """Segmented 14-bit DAC: check differential output spans meaningful range."""
    if not rows:
        return False, "empty"
    vop_col = next((k for k in rows[0] if k.lower() in {"vout_p", "iout_p", "voutp"}), None)
    von_col = next((k for k in rows[0] if k.lower() in {"vout_n", "iout_n", "voutn"}), None)
    if vop_col is None or von_col is None:
        vout_col = next((k for k in rows[0] if "vout" in k.lower() or "iout" in k.lower()), None)
        if vout_col is None:
            return False, f"missing vout_p/vout_n; keys={list(rows[0].keys())[:10]}"
        vvals = [r[vout_col] for r in rows]
        ok = max(vvals) - min(vvals) > 0.1
        return ok, f"vout_range={max(vvals)-min(vvals):.3f}"
    diff = [r[vop_col] - r[von_col] for r in rows]
    diff_range = max(diff) - min(diff)
    ok = diff_range > 0.1
    return ok, f"diff_range={diff_range:.3f}"


def check_comparator_offset_search(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "inp", "inn", "outp"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/inp/inn/outp"

    threshold = 0.45
    outp = [r["outp"] for r in rows]
    times = [r["time"] for r in rows]
    rise_t = next((times[idx] for idx in range(1, len(rows)) if outp[idx - 1] < threshold <= outp[idx]), None)
    if rise_t is None:
        return False, "no_output_crossing"

    crossing_row = next((r for r in rows if r["time"] >= rise_t), rows[-1])
    crossing_voltage = crossing_row["inp"]
    low_window = [r["outp"] for r in rows if r["inp"] <= 0.501]
    high_window = [r["outp"] for r in rows if r["inp"] >= 0.509]
    if not low_window or not high_window:
        return False, "insufficient_offset_windows"

    low_frac = sum(1 for v in low_window if v < threshold) / len(low_window)
    high_frac = sum(1 for v in high_window if v > threshold) / len(high_window)
    ok = abs(crossing_voltage - 0.505) <= 0.003 and low_frac > 0.9 and high_frac > 0.9
    return ok, (
        f"crossing_voltage={crossing_voltage:.4f} "
        f"low_frac={low_frac:.3f} "
        f"high_frac={high_frac:.3f}"
    )


def check_comparator_measurement_flow(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "inp", "inn", "outp", "trip_v", "offset_est", "valid"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/inp/inn/outp/trip_v/offset_est/valid"

    threshold = 0.45
    outp = [r["outp"] for r in rows]
    valid = [r["valid"] for r in rows]
    if max(outp) - min(outp) < 0.3:
        return False, f"outp_range={max(outp) - min(outp):.3f}"
    if max(valid) - min(valid) < 0.3:
        return False, f"valid_range={max(valid) - min(valid):.3f}"

    low_window = [r for r in rows if r["inp"] <= r["inn"] + 0.001]
    high_window = [r for r in rows if r["inp"] >= r["inn"] + 0.009]
    if not low_window or not high_window:
        return False, "insufficient_pre_post_trip_windows"

    low_frac = sum(1 for r in low_window if r["outp"] < threshold) / len(low_window)
    high_frac = sum(1 for r in high_window if r["outp"] > threshold) / len(high_window)
    pre_valid_low_frac = sum(1 for r in low_window if r["valid"] < threshold) / len(low_window)
    if low_frac < 0.9 or high_frac < 0.9 or pre_valid_low_frac < 0.9:
        return False, (
            f"output_or_valid_window_fail low_frac={low_frac:.3f} "
            f"high_frac={high_frac:.3f} pre_valid_low_frac={pre_valid_low_frac:.3f}"
        )

    valid_rows = [r for r in rows if r["valid"] > threshold]
    if not valid_rows:
        return False, "valid_never_asserts"

    first_out_high = next((r for r in rows if r["outp"] > threshold), None)
    if first_out_high is None:
        return False, "outp_never_asserts"
    out_trip_diff = first_out_high["inp"] - first_out_high["inn"]
    if abs(out_trip_diff - 0.005) > 0.0015:
        return False, f"outp_first_trip_diff={out_trip_diff:.4f}"

    first_valid = valid_rows[0]
    valid_trip_diff = first_valid["inp"] - first_valid["inn"]
    if abs(valid_trip_diff - 0.005) > 0.0015:
        return False, f"valid_first_trip_diff={valid_trip_diff:.4f}"
    if first_valid["outp"] <= threshold:
        valid_out_settle_s = 100e-12
        settled_after_valid = any(
            r["time"] >= first_valid["time"]
            and r["time"] <= first_valid["time"] + valid_out_settle_s
            and r["outp"] > threshold
            for r in rows
        )
        if not settled_after_valid:
            return False, f"valid_before_output_trip outp={first_valid['outp']:.3f}"

    final_valid_rows = [r for r in valid_rows if r["time"] >= first_valid["time"] + 2e-9]
    if len(final_valid_rows) < 3:
        final_valid_rows = valid_rows[-min(5, len(valid_rows)) :]

    trip_vals = [r["trip_v"] for r in final_valid_rows]
    offset_vals = [r["offset_est"] for r in final_valid_rows]
    trip_avg = sum(trip_vals) / len(trip_vals)
    offset_avg = sum(offset_vals) / len(offset_vals)
    inn_avg = sum(r["inn"] for r in final_valid_rows) / len(final_valid_rows)
    expected_trip = inn_avg + 0.005
    expected_offset = 0.005
    trip_span = max(trip_vals) - min(trip_vals)
    offset_span = max(offset_vals) - min(offset_vals)

    ok = (
        abs(trip_avg - expected_trip) <= 0.0015
        and abs(offset_avg - expected_offset) <= 0.0015
        and trip_span <= 0.002
        and offset_span <= 0.002
    )
    return ok, (
        f"trip_avg={trip_avg:.4f} expected_trip={expected_trip:.4f} "
        f"offset_avg={offset_avg:.4f} low_frac={low_frac:.3f} "
        f"high_frac={high_frac:.3f} out_trip_diff={out_trip_diff:.4f} "
        f"valid_trip_diff={valid_trip_diff:.4f} trip_span={trip_span:.4f} "
        f"offset_span={offset_span:.4f}"
    )


def check_cdac_cal(rows: list[dict[str, float]]) -> tuple[bool, str]:
    """CDAC with cal: check differential output varies with control bits."""
    if not rows:
        return False, "empty"
    vdac_cols = [k for k in rows[0] if "vdac" in k.lower() or "vcap" in k.lower() or "vout" in k.lower()]
    if not vdac_cols:
        return False, f"missing vdac columns; keys={list(rows[0].keys())[:10]}"
    for col in vdac_cols[:2]:
        vals = [r[col] for r in rows]
        if max(vals) - min(vals) > 0.05:
            return True, f"vdac_activity col={col} range={max(vals)-min(vals):.3f}"
    return False, f"no vdac activity in {vdac_cols[:4]}"


_RELEASE_CDAC_CODE_SEQUENCE = (
    0,
    1,
    2,
    3,
    7,
    15,
    16,
    32,
    64,
    128,
    256,
    512,
    255,
    511,
    767,
    1023,
)
_RELEASE_CDAC_CAL_SEQUENCE = (0, 1, 2, 3) * 4
_RELEASE_CDAC_SAMPLE_START_S = 5e-9
_RELEASE_CDAC_SAMPLE_PERIOD_S = 4e-9


def _release_cdac_state_index(edge_t: float) -> int | None:
    idx = int(round((edge_t - _RELEASE_CDAC_SAMPLE_START_S) / _RELEASE_CDAC_SAMPLE_PERIOD_S))
    if idx < 0 or idx >= len(_RELEASE_CDAC_CODE_SEQUENCE):
        return None
    expected_edge_t = _RELEASE_CDAC_SAMPLE_START_S + idx * _RELEASE_CDAC_SAMPLE_PERIOD_S
    if abs(edge_t - expected_edge_t) > 0.35e-9:
        return None
    return idx


def check_release_cdac_feedback_dac(rows: list[dict[str, float]]) -> tuple[bool, str]:
    """Release CDAC: verify settled differential output follows code + 32*cal."""
    required = {"time", "clk", "cal0", "cal1", "vdac_p", "vdac_n"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/clk/cal0/cal1/vdac_p/vdac_n"

    times = [r["time"] for r in rows]
    clk_edges = rising_edges([r["clk"] for r in rows], times)
    if len(clk_edges) < 14:
        return False, f"clk_edges={len(clk_edges)}"

    checked = 0
    covered_states: set[int] = set()
    mismatches = 0
    cal_mismatches = 0
    diff_values: list[float] = []
    max_diff_error = 0.0
    max_cm_error = 0.0

    for edge_t in clk_edges:
        state_idx = _release_cdac_state_index(edge_t)
        if state_idx is None:
            continue
        sample_t = edge_t + 0.25e-9
        vdac_p = sample_signal_at(rows, "vdac_p", sample_t)
        vdac_n = sample_signal_at(rows, "vdac_n", sample_t)
        cal0 = sample_signal_at(rows, "cal0", edge_t)
        cal1 = sample_signal_at(rows, "cal1", edge_t)
        if vdac_p is None or vdac_n is None or cal0 is None or cal1 is None:
            continue

        code = _RELEASE_CDAC_CODE_SEQUENCE[state_idx]
        expected_cal = _RELEASE_CDAC_CAL_SEQUENCE[state_idx]
        observed_cal = (1 if cal0 > 0.45 else 0) | (2 if cal1 > 0.45 else 0)
        expected_diff = 0.6 * (((code + 32 * expected_cal) / 1023.0) - 0.5)
        actual_diff = vdac_p - vdac_n
        diff_error = abs(actual_diff - expected_diff)
        cm_error = abs(0.5 * (vdac_p + vdac_n) - 0.45)

        checked += 1
        covered_states.add(state_idx)
        diff_values.append(actual_diff)
        max_diff_error = max(max_diff_error, diff_error)
        max_cm_error = max(max_cm_error, cm_error)
        if observed_cal != expected_cal:
            cal_mismatches += 1
        if diff_error > 0.035 or cm_error > 0.025:
            mismatches += 1

    if checked < 14 or len(covered_states) < 14:
        return False, f"settled_samples={checked} covered_states={len(covered_states)}"
    diff_span = max(diff_values) - min(diff_values)
    allowed_mismatches = max(1, checked // 10)
    ok = (
        mismatches <= allowed_mismatches
        and cal_mismatches <= allowed_mismatches
        and diff_span > 0.035
        and max_cm_error <= 0.025
    )
    return ok, (
        f"samples={checked} mismatches={mismatches}/{allowed_mismatches} "
        f"cal_mismatches={cal_mismatches} covered_states={len(covered_states)} "
        f"diff_span={diff_span:.4f} "
        f"max_diff_error={max_diff_error:.4f} max_cm_error={max_cm_error:.4f}"
    )


def check_v3_cdac_feedback_dac(rows: list[dict[str, float]]) -> tuple[bool, str]:
    """V3 CDAC: verify sampled binary code, calibration offset, polarity, and common-mode."""
    required = {"time", "clk", "cal0", "cal1", "vdac_p", "vdac_n"} | {f"d{i}" for i in range(10)}
    if not rows or not required.issubset(rows[0]):
        missing = sorted(required - set(rows[0].keys())) if rows else sorted(required)
        return False, "missing_columns=" + ",".join(missing[:16])

    times = [r["time"] for r in rows]
    clk_edges = rising_edges([r["clk"] for r in rows], times)
    if len(clk_edges) < 8:
        return False, f"clk_edges={len(clk_edges)}"

    checked = 0
    mismatches = 0
    max_diff_error = 0.0
    max_cm_error = 0.0
    effective_codes: list[int] = []
    actual_diffs: list[float] = []
    cal_codes: set[int] = set()
    main_codes: set[int] = set()

    for edge_t in clk_edges:
        sample_t = edge_t + 0.8e-9
        vdac_p = sample_signal_at(rows, "vdac_p", sample_t)
        vdac_n = sample_signal_at(rows, "vdac_n", sample_t)
        if vdac_p is None or vdac_n is None:
            continue

        main_code = 0
        missing_input = False
        for bit in range(10):
            value = sample_signal_at(rows, f"d{bit}", edge_t)
            if value is None:
                missing_input = True
                break
            if value > 0.45:
                main_code |= 1 << bit
        cal0 = sample_signal_at(rows, "cal0", edge_t)
        cal1 = sample_signal_at(rows, "cal1", edge_t)
        if missing_input or cal0 is None or cal1 is None:
            continue

        cal_code = (1 if cal0 > 0.45 else 0) | (2 if cal1 > 0.45 else 0)
        effective_code = main_code + 32 * cal_code
        expected_diff = 0.6 * ((effective_code / 1023.0) - 0.5)
        actual_diff = vdac_p - vdac_n
        diff_error = abs(actual_diff - expected_diff)
        cm_error = abs(0.5 * (vdac_p + vdac_n) - 0.45)

        checked += 1
        main_codes.add(main_code)
        cal_codes.add(cal_code)
        effective_codes.append(effective_code)
        actual_diffs.append(actual_diff)
        max_diff_error = max(max_diff_error, diff_error)
        max_cm_error = max(max_cm_error, cm_error)
        if diff_error > 0.025 or cm_error > 0.020:
            mismatches += 1

    if checked < 8:
        return False, f"settled_samples={checked}"
    if not {0, 1, 2, 3}.issubset(cal_codes):
        return False, f"cal_coverage={sorted(cal_codes)}"
    if not ({0, 1023}.issubset(main_codes) and any(450 <= code <= 573 for code in main_codes)):
        return False, f"main_code_coverage={sorted(main_codes)[:12]}"

    monotonic_errors = 0
    ordered = sorted(zip(effective_codes, actual_diffs), key=lambda item: item[0])
    for (_, prev_diff), (_, cur_diff) in zip(ordered, ordered[1:]):
        if cur_diff + 0.015 < prev_diff:
            monotonic_errors += 1

    diff_span = max(actual_diffs) - min(actual_diffs) if actual_diffs else 0.0
    ok = mismatches == 0 and monotonic_errors == 0 and diff_span > 0.55 and max_cm_error <= 0.020
    return ok, (
        f"samples={checked} main_codes={len(main_codes)} cal_codes={sorted(cal_codes)} "
        f"mismatches={mismatches} monotonic_errors={monotonic_errors} "
        f"diff_span={diff_span:.4f} max_diff_error={max_diff_error:.4f} "
        f"max_cm_error={max_cm_error:.4f}"
    )


def _v3_integrated_mod_phase_values(
    rows: list[dict[str, float]],
    *,
    freq_fn,
    modulus: float,
) -> list[float]:
    phase = 0.0
    phases = [phase]
    for prev, row in zip(rows, rows[1:]):
        dt = max(0.0, row["time"] - prev["time"])
        if prev.get("rst", 0.0) <= 0.45 and row.get("rst", 0.0) <= 0.45:
            f0 = freq_fn(prev)
            f1 = freq_fn(row)
            phase = (phase + 0.5 * (f0 + f1) * dt) % modulus
        phases.append(phase)
    return phases


def check_v3_502_sine_vco_idtmod_bound_step(rows: list[dict[str, float]]) -> tuple[bool, str]:
    # PLL sine VCO recast from Cadence VCO1.va: freq_q = center_freq + vco_gain*V(vin),
    # phase_q = idtmod(freq_q,0,1), out = vco_amp*sin(2*pi*phase_q), metric = vco_amp*phase_q.
    required = {"time", "vin", "out", "metric"}
    if not rows or not required.issubset(rows[0]):
        missing = sorted(required - set(rows[0].keys())) if rows else sorted(required)
        return False, "missing_columns=" + ",".join(missing)
    center_freq = 20.0e6
    vco_gain = 40.0e6
    vco_amp = 0.9
    phases = _v3_integrated_mod_phase_values(
        rows,
        freq_fn=lambda row: center_freq + vco_gain * row["vin"],
        modulus=1.0,
    )
    two_pi = 2.0 * math.pi
    stride = max(1, len(rows) // 160)
    checked = 0
    max_out_err = 0.0
    max_metric_err = 0.0
    out_span_lo = None
    out_span_hi = None
    for index in range(0, len(rows), stride):
        if rows[index]["time"] < 8.0e-9:
            continue
        phase = phases[index]
        out_expected = vco_amp * math.sin(two_pi * phase)
        metric_expected = vco_amp * phase
        out_err = abs(rows[index]["out"] - out_expected)
        out_span_lo = out_expected if out_span_lo is None else min(out_span_lo, out_expected)
        out_span_hi = out_expected if out_span_hi is None else max(out_span_hi, out_expected)
        max_out_err = max(max_out_err, out_err)
        checked += 1
        if out_err > 0.08:
            return False, (
                f"out@{rows[index]['time'] * 1e9:g}ns={rows[index]['out']:.4f} "
                f"expected={out_expected:.4f} tol=0.0800"
            )
        if 0.05 < phase < 0.95:
            metric_err = abs(rows[index]["metric"] - metric_expected)
            max_metric_err = max(max_metric_err, metric_err)
            if metric_err > 0.06:
                return False, (
                    f"metric@{rows[index]['time'] * 1e9:g}ns={rows[index]['metric']:.4f} "
                    f"expected={metric_expected:.4f} tol=0.0600"
                )
    if checked < 20:
        return False, f"insufficient_samples={checked}"
    out_span = (out_span_hi - out_span_lo) if (out_span_lo is not None) else 0.0
    if out_span < 0.6 * vco_amp:
        return False, f"insufficient_out_dynamic_range={out_span:.4f}"
    return True, (
        f"out_samples={checked} out_span={out_span:.4f} "
        f"max_out_err={max_out_err:.4f} max_metric_err={max_metric_err:.4f}"
    )


def check_v3_503_differential_vco_clip_idtmod(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vinp", "vinm", "outp", "outm", "metric"}
    if not rows or not required.issubset(rows[0]):
        missing = sorted(required - set(rows[0].keys())) if rows else sorted(required)
        return False, "missing_columns=" + ",".join(missing)
    fnom = 20.0e6
    dfdv = 160.0e6
    fmin = 5.0e6
    fmax = 80.0e6
    vcm = 0.45
    vac = 0.4

    def _clip(x: float) -> float:
        return fmin if x < fmin else (fmax if x > fmax else x)

    phases = _v3_integrated_mod_phase_values(
        rows,
        freq_fn=lambda row: _clip(fnom + dfdv * (row["vinp"] - row["vinm"])),
        modulus=1.0,
    )
    two_pi = 2.0 * math.pi
    stride = max(1, len(rows) // 160)
    checked = 0
    max_err = 0.0
    outp_span_lo = None
    outp_span_hi = None
    for index in range(0, len(rows), stride):
        if rows[index]["time"] < 8.0e-9:
            continue
        phase = phases[index]
        outp_expected = vcm + vac * math.sin(two_pi * phase)
        outm_expected = vcm - vac * math.sin(two_pi * phase)
        metric_expected = 0.9 * phase
        outp_err = abs(rows[index]["outp"] - outp_expected)
        outm_err = abs(rows[index]["outm"] - outm_expected)
        max_err = max(max_err, outp_err, outm_err)
        checked += 1
        outp_span_lo = outp_expected if outp_span_lo is None else min(outp_span_lo, outp_expected)
        outp_span_hi = outp_expected if outp_span_hi is None else max(outp_span_hi, outp_expected)
        if outp_err > 0.08:
            return False, (
                f"outp@{rows[index]['time'] * 1e9:g}ns={rows[index]['outp']:.4f} "
                f"expected={outp_expected:.4f} tol=0.0800"
            )
        if outm_err > 0.08:
            return False, (
                f"outm@{rows[index]['time'] * 1e9:g}ns={rows[index]['outm']:.4f} "
                f"expected={outm_expected:.4f} tol=0.0800"
            )
        if 0.05 < phase < 0.95:
            metric_err = abs(rows[index]["metric"] - metric_expected)
            max_err = max(max_err, metric_err)
            if metric_err > 0.06:
                return False, (
                    f"metric@{rows[index]['time'] * 1e9:g}ns={rows[index]['metric']:.4f} "
                    f"expected={metric_expected:.4f} tol=0.0600"
                )
    if checked < 20:
        return False, f"insufficient_samples={checked}"
    outp_span = (outp_span_hi - outp_span_lo) if (outp_span_lo is not None) else 0.0
    if outp_span < 0.5 * vac:
        return False, f"insufficient_outp_dynamic_range={outp_span:.4f}"
    return True, f"samples={checked} outp_span={outp_span:.4f} max_err={max_err:.4f}"


def check_v3_504_charge_pump_pfd_state_machine(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "ref", "fb", "vctrl", "metric"}
    if not rows or not required.issubset(rows[0]):
        missing = sorted(required - set(rows[0].keys())) if rows else sorted(required)
        return False, "missing_columns=" + ",".join(missing)
    t_end = rows[-1]["time"]
    if t_end < 600e-9:
        return False, f"trace_too_short={t_end*1e9:g}ns"
    vctrl_min = 0.05
    vctrl_max = 0.85
    metric_hi = 0.8
    vctrl_init = 0.45

    def _window_mean(lo_frac: float, hi_frac: float, key: str) -> float:
        lo_t = lo_frac * t_end
        hi_t = hi_frac * t_end
        vals = [r[key] for r in rows if lo_t <= r["time"] <= hi_t]
        return sum(vals) / len(vals) if vals else 0.0

    late_vctrl = _window_mean(0.55, 0.95, "vctrl")
    if late_vctrl < vctrl_max - 0.06:
        return False, f"vctrl_did_not_reach_top_rail late={late_vctrl:.4f}"
    vmax_obs = max(r["vctrl"] for r in rows)
    if vmax_obs < vctrl_init + 0.10:
        return False, f"vctrl_never_moved max={vmax_obs:.4f}"
    vmin_obs = min(r["vctrl"] for r in rows)
    if vmin_obs < vctrl_min - 0.02 or vmax_obs > vctrl_max + 0.02:
        return False, f"vctrl_out_of_clamp min={vmin_obs:.4f} max={vmax_obs:.4f}"

    late_metric_rows = [r for r in rows if 0.55 * t_end <= r["time"] <= 0.95 * t_end]
    if not late_metric_rows:
        return False, "no_late_metric_samples"
    metric_lo = 0.1
    hi_count = sum(1 for r in late_metric_rows if abs(r["metric"] - metric_hi) < 0.12)
    lo_count = sum(1 for r in late_metric_rows if abs(r["metric"] - metric_lo) < 0.12)
    hi_frac = hi_count / len(late_metric_rows)
    lo_frac = lo_count / len(late_metric_rows)
    if hi_frac < 0.02:
        return False, f"metric_no_positive_pulses hi_frac={hi_frac:.3f}"
    if lo_frac > 0.02:
        return False, f"metric_negative_pulses_present lo_frac={lo_frac:.3f}"
    return True, (
        f"late_vctrl={late_vctrl:.4f} "
        f"vctrl_range=[{vmin_obs:.4f},{vmax_obs:.4f}] metric_hi_frac={hi_frac:.3f}"
    )


def check_v3_505_fractional_n_divider_accumulator_flow(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"ref_clk", "fb_clk", "lock", "vctrl_mon"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing ref_clk/fb_clk/lock/vctrl_mon"

    vth = 0.45
    times = [r["time"] for r in rows]
    ref_edges = rising_edges([r["ref_clk"] for r in rows], times, threshold=vth)
    fb_edges = rising_edges([r["fb_clk"] for r in rows], times, threshold=vth)
    if len(ref_edges) < 12 or len(fb_edges) < 12:
        return False, f"not_enough_edges ref={len(ref_edges)} fb={len(fb_edges)}"

    ref_late = [t for t in ref_edges if 4.5e-6 <= t <= 5.9e-6]
    fb_late = [t for t in fb_edges if 4.5e-6 <= t <= 5.9e-6]
    if len(ref_late) < 4 or len(fb_late) < 4:
        return False, f"not_enough_late_edges ref_late={len(ref_late)} fb_late={len(fb_late)}"

    ref_periods = [b - a for a, b in zip(ref_late, ref_late[1:])]
    fb_periods = [b - a for a, b in zip(fb_late, fb_late[1:])]
    ref_period = sum(ref_periods) / len(ref_periods)
    fb_period = sum(fb_periods) / len(fb_periods)
    if ref_period <= 0.0 or fb_period <= 0.0:
        return False, "non_positive_period"
    freq_ratio = ref_period / fb_period

    if "dco_clk" in rows[0]:
        dco_edges = rising_edges([r["dco_clk"] for r in rows], times, threshold=vth)
        dco_late = [t for t in dco_edges if 4.5e-6 <= t <= 5.9e-6]
        if len(fb_late) >= 2 and len(dco_late) >= 4:
            dco_per_fb_period = (len(dco_late) - 1) / (len(fb_late) - 1)
            measured_divide = dco_per_fb_period / 2.0
            expected_divide = 8.0 - 3.0 / 8.0
            if abs(measured_divide - expected_divide) > 0.35:
                return False, (
                    f"fractional_divide_ratio_mismatch measured={measured_divide:.3f} "
                    f"expected~{expected_divide:.3f}"
                )
            divide_ok = True
            divide_note = f"divide={measured_divide:.3f}"
        else:
            divide_ok = False
            divide_note = f"divide=insufficient_dco={len(dco_late)}"
    else:
        divide_ok = True
        divide_note = "divide=dco_clk_absent"

    lock_edges = rising_edges([r["lock"] for r in rows], times, threshold=vth)
    pre_lock_edges = [t for t in lock_edges if t < 2.0e-6]
    post_lock_edges = [t for t in lock_edges if 2.2e-6 <= t <= 5.9e-6]

    disturb_low_frac = 1.0 - weighted_logic_high_fraction_window(
        rows, "lock", vth, 2.05e-6, 2.8e-6
    )

    vctrl_vals = [r["vctrl_mon"] for r in rows]
    vctrl_min = min(vctrl_vals)
    vctrl_max = max(vctrl_vals)
    vctrl_span = vctrl_max - vctrl_min
    vctrl_in_range = all(-1e-6 <= v <= 0.95 for v in vctrl_vals)

    ok = (
        bool(pre_lock_edges)
        and disturb_low_frac >= 0.25
        and bool(post_lock_edges)
        and 0.95 <= freq_ratio <= 1.05
        and vctrl_in_range
        and vctrl_span >= 0.02
        and divide_ok
    )
    return ok, (
        f"pre_lock_edges={len(pre_lock_edges)} "
        f"disturb_lock_low_frac={disturb_low_frac:.3f} "
        f"post_lock_edges={len(post_lock_edges)} "
        f"late_freq_ratio={freq_ratio:.4f} "
        f"{divide_note} "
        f"vctrl_min={vctrl_min:.3f} vctrl_max={vctrl_max:.3f} vctrl_span={vctrl_span:.3f}"
    )


def check_sc_integrator(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows:
        return False, "empty"
    keys = rows[0].keys()
    phi2_col = next((k for k in keys if k.lower() == "phi2"), None)
    vout_col = next((k for k in keys if k.lower() in {"vout", "out"}), None)
    if phi2_col is None or vout_col is None:
        return False, f"missing phi2/vout; keys={list(keys)[:10]}"

    edges = [
        rows[i]["time"]
        for i in range(1, len(rows))
        if rows[i - 1][phi2_col] < 0.45 <= rows[i][phi2_col]
    ]
    if len(edges) < 3:
        return False, f"phi2_edges={len(edges)}"

    samples: list[float] = []
    for t_edge in edges[:5]:
        window = [
            r[vout_col]
            for r in rows
            if t_edge + 0.5e-9 <= r["time"] <= t_edge + 2.0e-9
        ]
        if window:
            samples.append(sum(window) / len(window))
    if len(samples) < 3:
        return False, f"insufficient_vout_samples={len(samples)}"

    monotonic = all(samples[i + 1] >= samples[i] - 2e-3 for i in range(len(samples) - 1))
    total_step = samples[-1] - samples[0]
    ok = monotonic and total_step > 0.05
    return ok, f"monotonic={monotonic} total_step={total_step:.3f}"


def check_bg_cal(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows:
        return False, "empty"
    trim_cols = sorted(
        [k for k in rows[0] if re.fullmatch(r"trim_?[0-5]", k.lower())],
        key=lambda name: int(re.findall(r"(\d+)$", name)[0]),
    )
    settled_col = next((k for k in rows[0] if k.lower() in {"settled", "done", "rdy"}), None)
    if len(trim_cols) < 6 or settled_col is None:
        return False, f"missing trim/settled columns; keys={list(rows[0].keys())[:12]}"

    codes = []
    for row in rows:
        code = 0
        for idx, col in enumerate(trim_cols):
            if row[col] > 0.45:
                code |= 1 << idx
        codes.append(code)

    code_span = max(codes) - min(codes)
    settled_high = any(r[settled_col] > 0.45 for r in rows[int(len(rows) * 0.75):])
    ok = code_span >= 4 and settled_high
    return ok, f"code_span={code_span} settled_high={settled_high}"


def check_multitone(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows:
        return False, "empty"
    out_col = next((k for k in rows[0] if k.lower() in {"out", "vout"}), None)
    if out_col is None:
        return False, f"missing out/vout column; keys={list(rows[0].keys())[:10]}"

    times = [r["time"] for r in rows]
    vals = [r[out_col] for r in rows]

    def interp(t: float) -> float | None:
        if not times:
            return None
        if t <= times[0]:
            return vals[0]
        if t >= times[-1]:
            return vals[-1]
        lo = 0
        hi = len(times) - 1
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if times[mid] <= t:
                lo = mid
            else:
                hi = mid
        t0 = times[lo]
        t1 = times[hi]
        if t1 == t0:
            return vals[lo]
        a = (t - t0) / (t1 - t0)
        return vals[lo] + a * (vals[hi] - vals[lo])

    samples = [
        (0.125e-6, 0.2 * math.sin(2 * math.pi * 1e6 * 0.125e-6) + 0.1 * math.sin(2 * math.pi * 2e6 * 0.125e-6) + 0.05 * math.sin(2 * math.pi * 3e6 * 0.125e-6)),
        (0.275e-6, 0.2 * math.sin(2 * math.pi * 1e6 * 0.275e-6) + 0.1 * math.sin(2 * math.pi * 2e6 * 0.275e-6) + 0.05 * math.sin(2 * math.pi * 3e6 * 0.275e-6)),
        (0.410e-6, 0.2 * math.sin(2 * math.pi * 1e6 * 0.410e-6) + 0.1 * math.sin(2 * math.pi * 2e6 * 0.410e-6) + 0.05 * math.sin(2 * math.pi * 3e6 * 0.410e-6)),
    ]
    errs = []
    for t_check, expected in samples:
        measured = interp(t_check)
        if measured is None:
            errs.append(1.0)
            continue
        errs.append(abs(measured - expected))
    max_err = max(errs)
    ok = max_err < 0.03
    return ok, f"max_err={max_err:.4f}"


def check_nrz_prbs(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows:
        return False, "empty"
    outp_col = next((k for k in rows[0] if k.lower() in {"outp", "voutp", "out_p"}), None)
    outn_col = next((k for k in rows[0] if k.lower() in {"outn", "voutn", "out_n"}), None)
    if outp_col is None or outn_col is None:
        return False, f"missing differential outputs; keys={list(rows[0].keys())[:12]}"

    outp = [r[outp_col] for r in rows]
    outn = [r[outn_col] for r in rows]
    transitions = sum(1 for i in range(1, len(outp)) if (outp[i - 1] - 0.45) * (outp[i] - 0.45) < 0)
    complement_err = sum(abs((a + b) - 0.9) for a, b in zip(outp, outn)) / len(outp)
    swing = max(outp) - min(outp)
    ok = transitions >= 8 and complement_err < 0.08 and swing > 0.2
    return ok, f"transitions={transitions} complement_err={complement_err:.4f} swing={swing:.3f}"


def check_mixed_domain_cdac_bug(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows:
        return False, "empty"
    vout_col = next((k for k in rows[0] if k.lower() in {"vout", "out"}), None)
    if vout_col is None:
        return False, f"missing vout column; keys={list(rows[0].keys())[:10]}"

    targets = [
        (17e-9, 0.2),
        (37e-9, 0.5),
        (57e-9, 0.8),
    ]
    errs = []
    for t_check, expected in targets:
        window = [r[vout_col] for r in rows if abs(r["time"] - t_check) <= 1.5e-9]
        if not window:
            errs.append(1.0)
            continue
        measured = sum(window) / len(window)
        errs.append(abs(measured - expected))
    max_err = max(errs)
    ok = max_err < 0.05
    return ok, f"max_err={max_err:.4f}"


def check_spectre_port_discipline(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows:
        return False, "empty"
    required = {"a", "b", "y"}
    keymap = {k.lower(): k for k in rows[0]}
    if not required.issubset(keymap):
        return False, f"missing a/b/y; keys={list(rows[0].keys())[:10]}"

    windows = [
        (10e-9, 0.0, "00"),
        (30e-9, 0.0, "10"),
        (50e-9, 0.0, "01"),
        (70e-9, 0.9, "11"),
    ]
    errs: list[str] = []
    for t_check, expected, label in windows:
        vals = [r[keymap["y"]] for r in rows if abs(r["time"] - t_check) <= 1.5e-9]
        if not vals:
            errs.append(f"{label}_no_samples")
            continue
        measured = sum(vals) / len(vals)
        if abs(measured - expected) > 0.05:
            errs.append(f"{label}_err={abs(measured - expected):.3f}")
    return (not errs), ("ok" if not errs else ";".join(errs))


def check_inverted_comparator_logic_bug(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows:
        return False, "empty"
    required = {"vinp", "vinn", "out_p"}
    if not required.issubset(rows[0]):
        return False, "missing vinp/vinn/out_p"

    windows = [
        (10e-9, 0.0, "low0"),
        (30e-9, 0.9, "high1"),
        (50e-9, 0.0, "low2"),
        (70e-9, 0.9, "high3"),
    ]
    errs: list[str] = []
    for t_check, expected, label in windows:
        vals = [r["out_p"] for r in rows if abs(r["time"] - t_check) <= 1.5e-9]
        if not vals:
            errs.append(f"{label}_no_samples")
            continue
        measured = sum(vals) / len(vals)
        if abs(measured - expected) > 0.08:
            errs.append(f"{label}_err={abs(measured - expected):.3f}")
    return (not errs), ("ok" if not errs else ";".join(errs))


def check_mux_4to1(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"d0", "d1", "d2", "d3", "sel1", "sel0", "y", "time"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing d0/d1/d2/d3/sel1/sel0/y/time"
    windows = [
        (50e-9, 0.1, "sel0"),
        (150e-9, 0.3, "sel1"),
        (250e-9, 0.6, "sel2"),
        (350e-9, 0.8, "sel3"),
    ]
    tol = 20e-3
    failures: list[str] = []
    for t_check, expected, label in windows:
        window = [
            r["y"]
            for r in rows
            if t_check - 10e-9 <= r["time"] <= t_check + 10e-9
        ]
        if not window:
            failures.append(f"{label}_no_samples")
            continue
        measured = sum(window) / len(window)
        if abs(measured - expected) > tol:
            failures.append(f"{label}_err={abs(measured - expected):.4f}")
    if failures:
        return False, ";".join(failures)
    return True, "all_4_select_windows_correct"


def check_above_threshold_startup(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vin", "out"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/vin/out"
    if max(r["vin"] for r in rows) < 0.45:
        return False, "vin_never_above_threshold"
    out_vals = [r["out"] for r in rows]
    out_min = min(out_vals)
    out_max = max(out_vals)
    span = out_max - out_min
    if span < 0.2:
        return False, f"out_not_latched_high span={span:.3f}"
    vth = out_min + 0.5 * span
    first_hi_t = next((r["time"] for r in rows if r["out"] > vth), None)
    if first_hi_t is None:
        return False, "out_never_high"
    late = [r["out"] for r in rows if r["time"] >= rows[-1]["time"] * 0.6]
    late_hi_frac = sum(1 for v in late if v > vth) / max(len(late), 1)
    ok = first_hi_t <= 2e-9 and late_hi_frac > 0.95
    return ok, f"first_hi_t_ns={first_hi_t*1e9:.3f} late_hi_frac={late_hi_frac:.3f}"


def check_bound_step_period_guard(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "guard_out", "phase_out"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/guard_out/phase_out"
    g = [r["guard_out"] for r in rows]
    p = [r["phase_out"] for r in rows]
    t = [r["time"] for r in rows]
    gth = 0.5 * (max(g) + min(g))
    guard_hi_frac = weighted_logic_high_fraction(rows, "guard_out", gth)
    if not (0.08 <= guard_hi_frac <= 0.30):
        return False, f"guard_hi_frac_out_of_range={guard_hi_frac:.3f}"
    wraps = sum(1 for i in range(1, len(p)) if p[i] < p[i - 1] - 0.2)
    phase_span = max(p) - min(p)
    guard_rises = len(rising_edges(g, t, threshold=gth))
    ok = wraps >= 3 and phase_span > 0.5 and guard_rises >= 3
    return ok, f"guard_rises={guard_rises} wraps={wraps} phase_span={phase_span:.3f} guard_hi_frac={guard_hi_frac:.3f}"


def check_cross_hysteresis_window(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vin", "out"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/vin/out"
    out_vals = [r["out"] for r in rows]
    lo = min(out_vals)
    hi = max(out_vals)
    span = hi - lo
    if span < 0.3:
        return False, f"out_span_too_small={span:.3f}"
    low1 = [r["out"] for r in rows if r["time"] <= 20e-9]
    high_mid = [r["out"] for r in rows if 35e-9 <= r["time"] <= 55e-9]
    low2 = [r["out"] for r in rows if r["time"] >= 75e-9]
    if not low1 or not high_mid or not low2:
        return False, "insufficient_window_samples"
    m_low1 = sum(low1) / len(low1)
    m_high = sum(high_mid) / len(high_mid)
    m_low2 = sum(low2) / len(low2)
    ok = (m_high - m_low1) > 0.45 * span and (m_high - m_low2) > 0.45 * span
    return ok, f"low1={m_low1:.3f} high={m_high:.3f} low2={m_low2:.3f} span={span:.3f}"


def _check_true_window_comparator_resampled(eval_rows: list[dict[str, float]]) -> tuple[bool, str]:
    out_vals = [r["out"] for r in eval_rows]
    lo = min(out_vals)
    hi = max(out_vals)
    span = hi - lo
    if span < 0.3:
        return False, f"out_span_too_small={span:.3f}"

    vth = lo + 0.5 * span
    t0 = eval_rows[0]["time"]
    t1 = eval_rows[-1]["time"]
    t_mid = 0.5 * (t0 + t1)

    def frac_high(selected: list[dict[str, float]]) -> float:
        if not selected:
            return 0.0
        return sum(1 for row in selected if row["out"] > vth) / len(selected)

    below = [r for r in eval_rows if r["vin"] <= 0.18]
    above = [r for r in eval_rows if r["vin"] >= 0.72]
    inside_rise = [r for r in eval_rows if r["time"] <= t_mid and 0.34 <= r["vin"] <= 0.56]
    inside_fall = [r for r in eval_rows if r["time"] > t_mid and 0.34 <= r["vin"] <= 0.56]

    if min(len(below), len(above), len(inside_rise), len(inside_fall)) < 3:
        return (
            False,
            "insufficient_window_samples "
            f"below={len(below)} above={len(above)} rise={len(inside_rise)} fall={len(inside_fall)}",
        )

    below_hi = frac_high(below)
    above_hi = frac_high(above)
    rise_hi = frac_high(inside_rise)
    fall_hi = frac_high(inside_fall)
    ok = below_hi < 0.10 and above_hi < 0.10 and rise_hi > 0.80 and fall_hi > 0.80
    return (
        ok,
        f"below_hi={below_hi:.3f} above_hi={above_hi:.3f} "
        f"inside_rise_hi={rise_hi:.3f} inside_fall_hi={fall_hi:.3f} span={span:.3f}",
    )


def _resample_rows_from_vectors(
    times: list[float],
    signals: dict[str, list[float]],
    *,
    sample_count: int,
) -> tuple[list[dict[str, float]], str | None]:
    if len(times) < 2 or sample_count < 2:
        return [], "invalid_time_range"
    t0 = times[0]
    t1 = times[-1]
    if t1 <= t0:
        return [], "invalid_time_range"
    rows: list[dict[str, float]] = []
    for idx in range(sample_count):
        target = t0 + (t1 - t0) * idx / (sample_count - 1)
        row = {"time": target}
        for signal, values in signals.items():
            value = CsvCheckerRuntime.interpolate_series(times, values, target)
            if value is None:
                return [], f"missing_resample_{signal}"
            row[signal] = value
        rows.append(row)
    return rows, None


def check_true_window_comparator(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vin", "out"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/vin/out"

    ordered = sorted(rows, key=lambda row: row["time"])
    times = [row["time"] for row in ordered]
    eval_rows, error = _resample_rows_from_vectors(
        times,
        {
            "vin": [row["vin"] for row in ordered],
            "out": [row["out"] for row in ordered],
        },
        sample_count=361,
    )
    if error is not None:
        return False, error
    # Spectre may save only adaptive breakpoints even when EVAS writes a dense
    # tran.csv. Judge the window function on a common time grid instead of
    # counting raw output samples.
    return _check_true_window_comparator_resampled(eval_rows)


def check_cross_interval_163p333(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "delay_out", "seen_out"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/delay_out/seen_out"
    seen_hi = max(r["seen_out"] for r in rows)
    if seen_hi < 0.3:
        return False, f"seen_out_never_high={seen_hi:.3f}"

    seen_th = 0.5 * seen_hi
    seen_rows = [r for r in rows if r["seen_out"] > seen_th]
    if not seen_rows:
        return False, "seen_out_no_logic_high_samples"
    # The event happens late in a short run. Averaging the final 30% of the
    # whole waveform incorrectly includes pre-event zeros, so measure the
    # settled delay level only after seen_out has asserted.
    settle_start = seen_rows[0]["time"] + 0.2e-9
    settled_rows = [r for r in seen_rows if r["time"] >= settle_start]
    if len(settled_rows) < 3:
        settled_rows = seen_rows
    tail_count = min(len(settled_rows), max(5, len(settled_rows) // 3))
    tail = sorted(r["delay_out"] for r in settled_rows[-tail_count:])
    if not tail:
        return False, "no_post_seen_delay_samples"
    delay_level = tail[len(tail) // 2]
    vdd_est = max(max(r["seen_out"] for r in rows), 1e-6)
    delay_ps = delay_level / vdd_est * 200.0
    ok = 130.0 <= delay_ps <= 190.0
    return ok, f"delay_ps={delay_ps:.3f} seen_hi={seen_hi:.3f} post_seen_samples={len(settled_rows)}"


def check_cross_sine_precision(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"first_err_out", "max_err_out", "count_out"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing first_err_out/max_err_out/count_out"
    vdd_est = max(r["count_out"] for r in rows)
    if vdd_est < 0.2:
        return False, f"count_out_too_low={vdd_est:.3f}"
    count_est = max(r["count_out"] for r in rows) / max(vdd_est, 1e-6) * 3.0
    max_err_ps = max(r["max_err_out"] for r in rows) / max(vdd_est, 1e-6) * 10.0
    ok = count_est >= 2.5 and max_err_ps < 1.0
    return ok, f"count_est={count_est:.2f} max_err_ps={max_err_ps:.4f}"


def check_differential_voltage_output(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "din", "en", "outp", "outn"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/din/en/outp/outn"

    vout_hi = max(max(r["outp"] for r in rows), max(r["outn"] for r in rows))
    logic_th = 0.45 if vout_hi <= 1.2 else 0.5 * vout_hi

    def settled(items: list[dict[str, float]]) -> list[dict[str, float]]:
        if len(items) < 6:
            return items
        return items[len(items) // 4 :]

    disabled = settled([r for r in rows if r["en"] <= logic_th])
    enabled_low = settled([r for r in rows if r["en"] > logic_th and r["din"] <= logic_th])
    enabled_high = settled([r for r in rows if r["en"] > logic_th and r["din"] > logic_th])
    if len(disabled) < 5 or len(enabled_low) < 5 or len(enabled_high) < 5:
        return False, "insufficient_window_samples"

    def mean_diff(items: list[dict[str, float]]) -> float:
        return sum(r["outp"] - r["outn"] for r in items) / len(items)

    def mean_abs_diff(items: list[dict[str, float]]) -> float:
        return sum(abs(r["outp"] - r["outn"]) for r in items) / len(items)

    def mean_cm(items: list[dict[str, float]]) -> float:
        return sum(0.5 * (r["outp"] + r["outn"]) for r in items) / len(items)

    dis_diff = mean_diff(disabled)
    dis_abs_diff = mean_abs_diff(disabled)
    low_diff = mean_diff(enabled_low)
    high_diff = mean_diff(enabled_high)
    cms = [mean_cm(disabled), mean_cm(enabled_low), mean_cm(enabled_high)]
    cm_span = max(cms) - min(cms)
    ok = dis_abs_diff < 0.08 and low_diff < -0.20 and high_diff > 0.20 and cm_span < 0.12
    return ok, (
        f"disabled_diff={dis_diff:.3f} disabled_abs_diff={dis_abs_diff:.3f} low_diff={low_diff:.3f} "
        f"high_diff={high_diff:.3f} cm_span={cm_span:.3f}"
    )


def check_final_step_file_metric(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "ref", "metric_out"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/ref/metric_out"
    ref_high = max(r["ref"] for r in rows)
    vth = 0.45 if ref_high < 1.0 else 0.5 * ref_high
    ref_edges = rising_edges([r["ref"] for r in rows], [r["time"] for r in rows], threshold=vth)
    expected_edges = [10e-9, 30e-9, 50e-9, 70e-9]
    if len(ref_edges) != len(expected_edges):
        return False, f"ref_edges={len(ref_edges)} expected={len(expected_edges)}"
    edge_errs = [abs(edge - expected) for edge, expected in zip(ref_edges, expected_edges)]
    max_edge_err = max(edge_errs) if edge_errs else float("inf")
    if max_edge_err > 0.5e-9:
        return False, f"ref_edge_grid_error_ns={max_edge_err * 1e9:.3f}"

    metric_vals = [r["metric_out"] for r in rows]
    vmax = max(metric_vals)
    if vmax < 0.2:
        return False, f"metric_out_too_low={vmax:.3f}"
    expected_levels = [ref_high * count / 4.0 for count in range(1, 5)]
    windows = [
        (12e-9, 18e-9),
        (32e-9, 38e-9),
        (52e-9, 58e-9),
        (72e-9, 78e-9),
    ]
    levels: list[float] = []
    for t0, t1 in windows:
        vals = [r["metric_out"] for r in rows if t0 <= r["time"] <= t1]
        if not vals:
            return False, "insufficient_metric_plateau_samples"
        levels.append(sum(vals) / len(vals))
    level_errs = [abs(level - expected) for level, expected in zip(levels, expected_levels)]
    max_level_err = max(level_errs) if level_errs else float("inf")
    tail = [r["metric_out"] for r in rows if r["time"] >= rows[-1]["time"] * 0.85]
    final_level = sum(tail) / len(tail) if tail else 0.0
    final_norm = final_level / max(ref_high, 1e-6)
    dips = sum(1 for i in range(1, len(metric_vals)) if metric_vals[i] + 0.03 < metric_vals[i - 1])
    ok = max_level_err <= 0.08 and final_norm > 0.90 and dips <= 3
    return ok, (
        f"ref_edges={len(ref_edges)} max_edge_err_ns={max_edge_err * 1e9:.3f} "
        f"metric_levels={[round(v,3) for v in levels]} max_level_err={max_level_err:.3f} "
        f"final_norm={final_norm:.3f} metric_dips={dips}"
    )


def check_parameter_type_override(rows: list[dict[str, float]]) -> tuple[bool, str]:
    if not rows or "out" not in rows[0]:
        return False, "missing out"
    out_vals = [r["out"] for r in rows]
    vhi = max(out_vals)
    vth = 0.5 * vhi
    times = [r["time"] for r in rows]
    pulses = len(rising_edges(out_vals, times, threshold=vth))
    ok = 3 <= pulses <= 5 and 0.60 <= vhi <= 0.85
    return ok, f"pulses={pulses} peak={vhi:.3f}"


def check_phase_accumulator_timer_wrap(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk_out", "phase_out"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/clk_out/phase_out"
    phase_vals = [r["phase_out"] for r in rows]
    clk_vals = [r["clk_out"] for r in rows]
    times = [r["time"] for r in rows]
    phase_span = max(phase_vals) - min(phase_vals)
    if phase_span < 0.4:
        return False, f"phase_span_too_small={phase_span:.3f}"
    phase_lo = min(phase_vals)
    high_th = phase_lo + 0.70 * phase_span
    low_th = phase_lo + 0.30 * phase_span
    wraps = 0
    armed = False
    for phase in phase_vals:
        if phase >= high_th:
            armed = True
        elif armed and phase <= low_th:
            wraps += 1
            armed = False
    cth = 0.5 * (max(clk_vals) + min(clk_vals))
    clk_rises = len(rising_edges(clk_vals, times, threshold=cth))
    ok = wraps >= 3 and clk_rises >= 3
    return ok, f"wraps={wraps} clk_rises={clk_rises} phase_span={phase_span:.3f}"


def check_simultaneous_event_order(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "ref", "out"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/ref/out"
    ref_high = max(r["ref"] for r in rows)
    vth = 0.45 if ref_high < 1.0 else 0.5 * ref_high
    ref_edges = rising_edges([r["ref"] for r in rows], [r["time"] for r in rows], threshold=vth)
    expected_edges = [10e-9, 30e-9, 50e-9, 70e-9]
    if len(ref_edges) != len(expected_edges):
        return False, f"ref_edges={len(ref_edges)} expected={len(expected_edges)}"
    edge_errs = [abs(edge - expected) for edge, expected in zip(ref_edges, expected_edges)]
    max_edge_err = max(edge_errs) if edge_errs else float("inf")
    if max_edge_err > 0.5e-9:
        return False, f"ref_edge_grid_error_ns={max_edge_err * 1e9:.3f}"

    windows = [
        (12e-9, 18e-9),
        (32e-9, 38e-9),
        (52e-9, 58e-9),
        (72e-9, 78e-9),
    ]
    levels: list[float] = []
    for t0, t1 in windows:
        vals = [r["out"] for r in rows if t0 <= r["time"] <= t1]
        if not vals:
            return False, "insufficient_window_samples"
        levels.append(sum(vals) / len(vals))
    monotonic = all(levels[i] <= levels[i + 1] + 0.05 for i in range(len(levels) - 1))
    span = levels[-1] - levels[0]
    expected_levels = [0.2 * cycle * ref_high for cycle in range(1, 5)]
    level_errs = [abs(level - expected) for level, expected in zip(levels, expected_levels)]
    max_level_err = max(level_errs) if level_errs else float("inf")
    ok = monotonic and span > 0.40 and max_level_err <= 0.08
    return ok, (
        f"ref_edges={len(ref_edges)} max_edge_err_ns={max_edge_err * 1e9:.3f} "
        f"plateau_levels={[round(v,3) for v in levels]} max_level_err={max_level_err:.3f} "
        f"span={span:.3f}"
    )


def check_conversion_event_controller(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {
        "time",
        "rst",
        "start",
        "cmp_done",
        "sample_en",
        "compare_en",
        "readout_en",
        "done",
        "state_mon",
    }
    if not rows or not required.issubset(rows[0]):
        return False, "missing conversion-controller observables"

    vth = 0.45
    times = [r["time"] for r in rows]
    start_edges = rising_edges([r["start"] for r in rows], times, threshold=vth)
    cmp_edges = rising_edges([r["cmp_done"] for r in rows], times, threshold=vth)
    if len(start_edges) != 2:
        return False, f"start_edges={len(start_edges)} expected=2"
    if len(cmp_edges) != 1:
        return False, f"cmp_done_edges={len(cmp_edges)} expected=1"

    failures: list[str] = []
    notes: list[str] = []

    def expect_level(key: str, start: float, stop: float, high: bool, label: str) -> None:
        avg = mean_in_window(rows, key, start, stop)
        if avg is None:
            failures.append(f"{label}=missing")
            return
        is_high = avg > vth
        notes.append(f"{label}:{avg:.3f}")
        if is_high != high:
            failures.append(f"{label}:{avg:.3f}")

    def expect_state(start: float, stop: float, target: float, label: str, tol: float = 0.12) -> None:
        avg = mean_in_window(rows, "state_mon", start, stop)
        if avg is None:
            failures.append(f"{label}=missing")
            return
        notes.append(f"{label}:{avg:.3f}")
        if abs(avg - target) > tol:
            failures.append(f"{label}:{avg:.3f}")

    for key in ("sample_en", "compare_en", "readout_en", "done"):
        expect_level(key, 1e-9, 4e-9, False, f"reset_{key}_low")

    # Transaction 1: compare is terminated by cmp_done.
    expect_level("sample_en", 12e-9, 20e-9, True, "cycle1_sample_high")
    expect_level("sample_en", 24e-9, 30e-9, False, "cycle1_sample_low_after_window")
    expect_level("compare_en", 24e-9, 34e-9, True, "cycle1_compare_high")
    expect_level("compare_en", 39e-9, 48e-9, False, "cycle1_compare_low_after_cmp_done")
    expect_level("readout_en", 40e-9, 50e-9, True, "cycle1_readout_high")
    expect_level("done", 54e-9, 58e-9, True, "cycle1_done_high")
    expect_state(14e-9, 20e-9, 0.225, "cycle1_state_sample")
    expect_state(26e-9, 34e-9, 0.450, "cycle1_state_compare")
    expect_state(41e-9, 49e-9, 0.675, "cycle1_state_readout")
    expect_state(54e-9, 58e-9, 0.900, "cycle1_state_done")

    # Transaction 2: compare exits by timeout because there is no second cmp_done.
    expect_level("sample_en", 92e-9, 100e-9, True, "cycle2_sample_high")
    expect_level("compare_en", 104e-9, 128e-9, True, "cycle2_compare_high_until_timeout")
    expect_level("compare_en", 132e-9, 142e-9, False, "cycle2_compare_low_after_timeout")
    expect_level("readout_en", 132e-9, 144e-9, True, "cycle2_readout_high")
    expect_level("done", 148e-9, 152e-9, True, "cycle2_done_high")
    expect_state(106e-9, 126e-9, 0.450, "cycle2_state_compare")
    expect_state(134e-9, 142e-9, 0.675, "cycle2_state_readout")

    if failures:
        return False, " ".join(failures)
    return True, f"conversion_event_controller ok {' '.join(notes[:10])}"


def check_timer_absolute_grid(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk_out"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/clk_out"
    clk_vals = [r["clk_out"] for r in rows]
    times = [r["time"] for r in rows]
    cth = 0.5 * (max(clk_vals) + min(clk_vals))
    rises = rising_edges(clk_vals, times, threshold=cth)
    if len(rises) < 4:
        return False, f"too_few_rising_edges={len(rises)}"
    targets = [10.1e-9, 30.1e-9, 50.1e-9, 70.1e-9]
    errs = [abs(r - t) for r, t in zip(rises[:4], targets)]
    max_err = max(errs) if errs else float("inf")
    ok = max_err <= 2.0e-9
    return ok, f"rises_ns={[round(v*1e9,3) for v in rises[:4]]} max_err_ns={max_err*1e9:.3f}"


def check_transition_branch_target(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "mode", "clk", "out"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/mode/clk/out"
    w_low0 = [r["out"] for r in rows if 15e-9 <= r["time"] <= 22e-9]
    w_high1 = [r["out"] for r in rows if 35e-9 <= r["time"] <= 42e-9]
    w_high2 = [r["out"] for r in rows if 55e-9 <= r["time"] <= 62e-9]
    w_low3 = [r["out"] for r in rows if 75e-9 <= r["time"] <= 85e-9]
    if not (w_low0 and w_high1 and w_high2 and w_low3):
        return False, "insufficient_window_samples"
    m0 = sum(w_low0) / len(w_low0)
    m1 = sum(w_high1) / len(w_high1)
    m2 = sum(w_high2) / len(w_high2)
    m3 = sum(w_low3) / len(w_low3)
    span = max(m1, m2) - min(m0, m3)
    ok = (m1 - m0) > 0.35 * max(span, 1e-6) and (m2 - m3) > 0.35 * max(span, 1e-6)
    return ok, f"means=({m0:.3f},{m1:.3f},{m2:.3f},{m3:.3f})"


def check_release_calibration_loop(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "rst", "out"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/clk/rst/out"
    input_key = "vin" if "vin" in rows[0] else "err" if "err" in rows[0] else None
    if input_key is None:
        return False, "missing vin/err input"

    reset_rows = [r for r in rows if r["rst"] > 0.45 and r["time"] < 3e-9]
    post_rows = [r for r in rows if r["rst"] <= 0.45 and r["time"] > 3e-9]
    if len(post_rows) < 10:
        return False, f"too_few_post_reset_rows={len(post_rows)}"

    reset_mean = sum(r["out"] for r in reset_rows) / len(reset_rows) if reset_rows else rows[0]["out"]
    out_vals = [r["out"] for r in post_rows]
    out_min = min(out_vals)
    out_max = max(out_vals)
    out_span = out_max - out_min
    if not (0.0 <= out_min <= out_max <= 0.95):
        return False, f"out_range=({out_min:.3f},{out_max:.3f})"
    if abs(reset_mean - 0.45) > 0.12:
        return False, f"reset_trim_mean={reset_mean:.3f}"
    # EVAS and Spectre can land on opposite sides of the exact 0.120 V boundary
    # from transition sampling granularity while producing the same trim sequence.
    if out_span < 0.12 - 1e-6:
        return False, f"trim_span_too_small={out_span:.3f}"

    edge_idx = [
        idx for idx in range(1, len(rows))
        if rows[idx - 1]["clk"] <= 0.45 < rows[idx]["clk"] and rows[idx]["rst"] <= 0.45
    ]
    directional_checks = 0
    directional_matches = 0
    prev_out: float | None = None
    for idx in edge_idx:
        settle = min(idx + 3, len(rows) - 1)
        current_out = rows[settle]["out"]
        if prev_out is None:
            prev_out = current_out
            continue
        errv = rows[idx][input_key] - 0.45
        delta = current_out - prev_out
        prev_out = current_out
        if abs(errv) <= 0.08:
            continue
        if current_out < 0.08 or current_out > 0.82 or prev_out < 0.08 or prev_out > 0.82:
            continue
        directional_checks += 1
        if (errv > 0.0 and delta > 0.004) or (errv < 0.0 and delta < -0.004):
            directional_matches += 1
    if directional_checks < 3:
        return False, f"too_few_directional_trim_checks={directional_checks}"
    if directional_matches < directional_checks - 1:
        return False, f"trim_direction_mismatches={directional_checks - directional_matches}/{directional_checks}"

    return True, (
        f"release_calibration_loop reset={reset_mean:.3f} span={out_span:.3f} "
        f"direction={directional_matches}/{directional_checks}"
    )


def mean_in_window(rows: list[dict[str, float]], key: str, start: float, stop: float) -> float | None:
    values = [r[key] for r in rows if start <= r["time"] <= stop and key in r]
    if not values:
        return None
    return sum(values) / len(values)


def time_weighted_mean_in_window(
    rows: list[dict[str, float]],
    key: str,
    start: float,
    stop: float,
) -> float | None:
    if stop <= start:
        return None
    ordered = sorted((r for r in rows if "time" in r and key in r), key=lambda r: r["time"])
    area = 0.0
    duration = 0.0
    for left, right in zip(ordered, ordered[1:]):
        t0 = float(left["time"])
        t1 = float(right["time"])
        if t1 <= t0:
            continue
        lo = max(start, t0)
        hi = min(stop, t1)
        if hi <= lo:
            continue
        v0 = float(left[key])
        v1 = float(right[key])

        def interp(t: float) -> float:
            frac = (t - t0) / (t1 - t0)
            return v0 + frac * (v1 - v0)

        area += 0.5 * (interp(lo) + interp(hi)) * (hi - lo)
        duration += hi - lo
    if duration > 0.0:
        return area / duration
    return mean_in_window(rows, key, start, stop)


DEFAULT_EDGE_SETTLE_DELAY_S = 0.12e-9


def settled_row_index_after_delay(
    rows: list[dict[str, float]],
    start_idx: int,
    settle_delay_s: float = DEFAULT_EDGE_SETTLE_DELAY_S,
) -> int:
    settle_time = rows[start_idx]["time"] + settle_delay_s
    settle = start_idx
    while settle + 1 < len(rows) and rows[settle]["time"] < settle_time:
        settle += 1
    return settle


def edge_settled_values(
    rows: list[dict[str, float]],
    key: str,
    *,
    clk_key: str = "clk",
    rst_key: str = "rst",
    settle_delay_s: float | None = None,
) -> list[tuple[dict[str, float], float]]:
    values: list[tuple[dict[str, float], float]] = []
    for idx in range(1, len(rows)):
        if rows[idx - 1][clk_key] <= 0.45 < rows[idx][clk_key] and rows[idx].get(rst_key, 0.0) <= 0.45:
            settle = settled_row_index_after_delay(
                rows,
                idx,
                DEFAULT_EDGE_SETTLE_DELAY_S if settle_delay_s is None else settle_delay_s,
            )
            values.append((rows[idx], rows[settle][key]))
    return values


def check_release_complete_calibration_loop(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "rst", "vin", "out", "metric", "trim_mon", "residual_mon"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/clk/rst/vin/out/metric/trim_mon/residual_mon"

    post_rows = [r for r in rows if r["rst"] <= 0.45 and r["time"] > 3e-9]
    if len(post_rows) < 10:
        return False, f"complete_cal_loop_too_few_post_reset_rows={len(post_rows)}"

    reset_rows = [r for r in rows if r["rst"] > 0.45 and (r["time"] < 3e-9 or 62.0e-9 <= r["time"] <= 66.2e-9)]
    reset_mean = sum(r["out"] for r in reset_rows) / len(reset_rows) if reset_rows else rows[0]["out"]
    if abs(reset_mean - 0.45) > 0.06:
        return False, f"complete_cal_loop_reset_mean={reset_mean:.3f}"

    out_vals = [r["out"] for r in post_rows]
    metric_vals = [r["metric"] for r in post_rows]
    vin_vals = [r["vin"] for r in post_rows]
    out_min = min(out_vals)
    out_max = max(out_vals)
    metric_min = min(metric_vals)
    metric_max = max(metric_vals)
    vin_span = max(vin_vals) - min(vin_vals)
    out_span = out_max - out_min
    if not (0.0 <= out_min <= out_max <= 0.95):
        return False, f"complete_cal_loop_out_range=({out_min:.3f},{out_max:.3f})"
    if not (0.0 <= metric_min <= metric_max <= 0.95):
        return False, f"complete_cal_loop_metric_range=({metric_min:.3f},{metric_max:.3f})"
    if vin_span < 0.35:
        return False, f"complete_cal_loop_input_span_too_small={vin_span:.3f}"
    if out_span < 0.05:
        return False, f"complete_cal_loop_out_span_too_small={out_span:.3f}"

    correction_checks = correction_ok = positive_checks = negative_checks = 0
    for edge_row, out in edge_settled_values(rows, "out"):
        if edge_row["time"] > 60.0e-9 and edge_row["time"] < 68.0e-9:
            continue
        raw_err = edge_row["vin"] - 0.45
        out_err = out - 0.45
        if abs(raw_err) <= 0.09:
            continue
        correction_checks += 1
        if raw_err > 0.0:
            positive_checks += 1
        else:
            negative_checks += 1
        if abs(out_err) <= max(0.075, abs(raw_err) - 0.06):
            correction_ok += 1
    if correction_checks < 8 or positive_checks < 2 or negative_checks < 2:
        return False, (
            f"complete_cal_loop_insufficient_error_windows total={correction_checks} "
            f"pos={positive_checks} neg={negative_checks}"
        )
    if correction_ok < correction_checks - 2:
        return False, f"complete_cal_loop_uncorrected_samples={correction_checks - correction_ok}/{correction_checks}"

    trim_vals = [r["trim_mon"] for r in post_rows]
    residual_vals = [r["residual_mon"] for r in post_rows]
    trim_min = min(trim_vals)
    trim_max = max(trim_vals)
    residual_min = min(residual_vals)
    residual_max = max(residual_vals)
    if not (0.0 <= trim_min <= trim_max <= 0.95):
        return False, f"complete_cal_loop_trim_range=({trim_min:.3f},{trim_max:.3f})"
    if not (0.0 <= residual_min <= residual_max <= 0.95):
        return False, f"complete_cal_loop_residual_range=({residual_min:.3f},{residual_max:.3f})"
    if trim_max - trim_min < 0.12:
        return False, f"complete_cal_loop_trim_span_too_small={trim_max - trim_min:.3f}"

    trim_samples = edge_settled_values(rows, "trim_mon")
    residual_samples = edge_settled_values(rows, "residual_mon")
    trim_checks = trim_ok = residual_ok = 0
    for (edge_row, trim_v), (_res_edge_row, residual_v) in zip(trim_samples, residual_samples):
        if edge_row["time"] > 60.0e-9 and edge_row["time"] < 68.0e-9:
            continue
        raw_err = edge_row["vin"] - 0.45
        if abs(raw_err) <= 0.09:
            continue
        trim_checks += 1
        if (raw_err > 0.0 and trim_v < 0.435) or (raw_err < 0.0 and trim_v > 0.465):
            trim_ok += 1
        residual_err = abs(residual_v - 0.45)
        if residual_err <= max(0.075, abs(raw_err) * 0.85):
            residual_ok += 1
    if trim_checks < 8:
        return False, f"complete_cal_loop_insufficient_trim_windows={trim_checks}"
    if trim_ok < trim_checks - 2:
        return False, f"complete_cal_loop_trim_not_opposing_error={trim_checks - trim_ok}/{trim_checks}"
    if residual_ok < trim_checks - 2:
        return False, f"complete_cal_loop_residual_not_reduced={trim_checks - residual_ok}/{trim_checks}"

    converged_metrics = [r["metric"] for r in post_rows if abs(r["out"] - 0.45) <= 0.08]
    if len(converged_metrics) < 5:
        return False, f"complete_cal_loop_too_few_converged_samples={len(converged_metrics)}"
    converged_metric_mean = sum(converged_metrics) / len(converged_metrics)
    if converged_metric_mean < 0.70:
        return False, f"complete_cal_loop_metric_not_high_when_converged={converged_metric_mean:.3f}"

    after_reset = mean_in_window(rows, "out", 67e-9, 70e-9)
    if after_reset is None:
        return False, "complete_cal_loop_missing_late_reset_window"
    if abs(after_reset - 0.45) > 0.12:
        return False, f"complete_cal_loop_late_reset_not_recovered={after_reset:.3f}"

    return True, (
        f"complete_cal_loop reset={reset_mean:.3f} vin_span={vin_span:.3f} out_span={out_span:.3f} "
        f"correction={correction_ok}/{correction_checks} trim={trim_ok}/{trim_checks} "
        f"residual={residual_ok}/{trim_checks} metric={converged_metric_mean:.3f}"
    )


def check_release_charge_pump(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "rst", "up", "dn", "vctrl", "metric"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/clk/rst/up/dn/vctrl/metric"

    ctrl_vals = [r["vctrl"] for r in rows]
    ctrl_min = min(ctrl_vals)
    ctrl_max = max(ctrl_vals)
    if not (0.0 <= ctrl_min <= ctrl_max <= 0.95):
        return False, f"charge_pump_vctrl_range=({ctrl_min:.3f},{ctrl_max:.3f})"

    reset_vals = [r["vctrl"] for r in rows if r["rst"] > 0.45 and r["time"] <= 3.0e-9]
    if not reset_vals:
        return False, "charge_pump_missing_reset_window"
    reset_mean = sum(reset_vals) / len(reset_vals)
    if abs(reset_mean - 0.45) > 0.12:
        return False, f"charge_pump_reset_mean={reset_mean:.3f}"
    ctrl_span = ctrl_max - ctrl_min
    if ctrl_span < 0.12:
        return False, f"charge_pump_vctrl_span_too_small={ctrl_span:.3f}"

    samples = edge_settled_values(rows, "vctrl")
    up_checks = down_checks = up_ok = down_ok = 0
    previous: float | None = None
    for edge_row, ctrl in samples:
        if previous is None:
            previous = ctrl
            continue
        previous_out = previous
        delta = ctrl - previous_out
        previous = ctrl
        if edge_row["time"] > 60e-9:
            continue
        if ctrl < 0.08 or ctrl > 0.82 or previous_out < 0.08 or previous_out > 0.82:
            continue
        up_high = edge_row["up"] > 0.45
        dn_high = edge_row["dn"] > 0.45
        if up_high and not dn_high:
            up_checks += 1
            if delta > 0.004:
                up_ok += 1
        elif dn_high and not up_high:
            down_checks += 1
            if delta < -0.004:
                down_ok += 1
    if up_checks < 2 or down_checks < 2:
        return False, f"charge_pump_missing_polarity_windows up={up_checks} down={down_checks}"
    if up_ok < up_checks - 1 or down_ok < down_checks - 1:
        return False, f"charge_pump_polarity up={up_ok}/{up_checks} down={down_ok}/{down_checks}"
    return True, (
        f"release_charge_pump reset={reset_mean:.3f} span={ctrl_span:.3f} "
        f"polarity up={up_ok}/{up_checks} down={down_ok}/{down_checks}"
    )


def check_release_loop_filter(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "rst", "vin", "out", "metric"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/clk/rst/vin/out/metric"

    out_vals = [r["out"] for r in rows if "out" in r]
    if not out_vals:
        return False, "loop_filter_missing_out_values"
    out_min = min(out_vals)
    out_max = max(out_vals)
    if not (0.0 <= out_min <= out_max <= 0.95):
        return False, f"loop_filter_out_range=({out_min:.3f},{out_max:.3f})"

    edge_samples: list[tuple[dict[str, float], float, float]] = []
    for idx in range(1, len(rows)):
        if rows[idx - 1]["clk"] <= 0.45 < rows[idx]["clk"] and rows[idx]["rst"] <= 0.45:
            settle = settled_row_index_after_delay(rows, idx)
            edge_samples.append((rows[idx], rows[settle]["out"], rows[settle]["metric"]))
    if len(edge_samples) < 12:
        return False, f"loop_filter_too_few_edge_samples={len(edge_samples)}"

    deltas: list[tuple[dict[str, float], float, float, float]] = []
    previous_out: float | None = None
    for edge_row, out, metric in edge_samples:
        if previous_out is not None:
            deltas.append((edge_row, out - previous_out, out, metric))
        previous_out = out

    positive_deltas = [
        delta
        for edge_row, delta, out, _metric in deltas
        if edge_row["time"] < 40e-9 and edge_row["vin"] > 0.55 and 0.08 < out < 0.93
    ]
    if len(positive_deltas) < 4:
        return False, f"loop_filter_missing_positive_pi_steps={len(positive_deltas)}"
    first_pos = positive_deltas[0]
    later_pos = positive_deltas[-1]
    proportional_decay = first_pos > 0.08 and 0.0 < later_pos < first_pos * 0.65
    if not proportional_decay:
        return False, f"loop_filter_no_proportional_decay first={first_pos:.3f} later={later_pos:.3f}"

    negative_deltas = [
        delta
        for edge_row, delta, out, _metric in deltas
        if 32e-9 <= edge_row["time"] <= 50e-9 and edge_row["vin"] < 0.40 and 0.08 < out < 0.93
    ]
    negative_ok = len(negative_deltas) >= 3 and sum(1 for delta in negative_deltas if delta < -0.003) >= 3
    if not negative_ok:
        return False, f"loop_filter_missing_negative_response={len(negative_deltas)}"

    near_deadband_hold = mean_in_window(rows, "out", 48e-9, 54e-9)
    if near_deadband_hold is None or near_deadband_hold < 0.80:
        value = "missing" if near_deadband_hold is None else f"{near_deadband_hold:.3f}"
        return False, f"loop_filter_missing_integral_residual={value}"

    early_metric = mean_in_window(rows, "metric", 8e-9, 18e-9)
    late_metric = mean_in_window(rows, "metric", 24e-9, 50e-9)
    reset_metric = mean_in_window(rows, "metric", 64.5e-9, 70e-9)
    if early_metric is None or late_metric is None or reset_metric is None:
        return False, "loop_filter_missing_metric_windows"
    metric_timing = early_metric < 0.15 and late_metric > 0.65 and reset_metric < 0.15
    if not metric_timing:
        return False, (
            f"loop_filter_metric_timing early={early_metric:.3f} "
            f"late={late_metric:.3f} reset={reset_metric:.3f}"
        )

    late_reset = mean_in_window(rows, "out", 64.5e-9, 66e-9)
    after_reset = mean_in_window(rows, "out", 67e-9, 70e-9)
    if late_reset is None or after_reset is None:
        return False, "loop_filter_missing_late_reset_window"
    if abs(late_reset - 0.45) > 0.02 or abs(after_reset - 0.45) > 0.02:
        return False, f"loop_filter_reset_not_cleared late={late_reset:.3f} after={after_reset:.3f}"
    return True, (
        f"loop_filter_pi first_pos_delta={first_pos:.3f} later_pos_delta={later_pos:.3f} "
        f"negative_steps={sum(1 for delta in negative_deltas if delta < -0.003)}/{len(negative_deltas)} "
        f"integral_residual={near_deadband_hold:.3f} metric={early_metric:.3f}/{late_metric:.3f}/{reset_metric:.3f} "
        f"reset={late_reset:.3f}/{after_reset:.3f}"
    )


def check_release_deadband_calibration(rows: list[dict[str, float]]) -> tuple[bool, str]:
    ok, note = check_release_calibration_loop(rows)
    if not ok:
        return ok, note
    samples = edge_settled_values(rows, "out", settle_delay_s=0.12e-9)
    hold_checks = hold_ok = 0
    previous: float | None = None
    for edge_row, out in samples:
        if previous is None:
            previous = out
            continue
        errv = edge_row.get("vin", edge_row.get("err", 0.45)) - 0.45
        delta = abs(out - previous)
        previous = out
        if abs(errv) <= 0.055 and edge_row["time"] < 60e-9:
            hold_checks += 1
            if delta <= 0.025:
                hold_ok += 1
    if hold_checks < 2:
        return False, f"deadband_missing_hold_samples={hold_checks}"
    if hold_ok < hold_checks:
        return False, f"deadband_hold_mismatches={hold_checks - hold_ok}/{hold_checks}"
    return True, f"{note}; deadband_hold={hold_ok}/{hold_checks}"


def check_release_sar_calibration_fsm(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "rst", "vin", "out", "metric"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/clk/rst/vin/out/metric"

    reset_rows = [r for r in rows if r["rst"] > 0.45 and r["time"] < 3e-9]
    reset_mean = sum(r["out"] for r in reset_rows) / len(reset_rows) if reset_rows else rows[0]["out"]
    if abs(reset_mean - 0.45) > 0.12:
        return False, f"sar_cal_reset_mean={reset_mean:.3f}"

    post_rows = [r for r in rows if r["rst"] <= 0.45 and r["time"] > 3e-9]
    if len(post_rows) < 10:
        return False, f"sar_cal_too_few_post_reset_rows={len(post_rows)}"
    out_vals = [r["out"] for r in post_rows]
    out_min = min(out_vals)
    out_max = max(out_vals)
    if not (0.0 <= out_min <= out_max <= 0.95):
        return False, f"sar_cal_out_range=({out_min:.3f},{out_max:.3f})"
    out_span = out_max - out_min
    if out_span < 0.12:
        return False, f"sar_cal_trim_span_too_small={out_span:.3f}"

    samples = [
        (edge, out)
        for edge, out in edge_settled_values(rows, "out")
        if edge["time"] < 45e-9 and edge.get("metric", 0.0) < 0.45
    ]
    deltas = [samples[0][1] - reset_mean] if samples else []
    deltas.extend(samples[idx][1] - samples[idx - 1][1] for idx in range(1, len(samples)))
    active_deltas = [abs(d) for d in deltas if abs(d) > 0.015]
    if len(active_deltas) < 4:
        return False, f"sar_cal_too_few_active_steps={len(active_deltas)}"
    if active_deltas[-1] > 0.60 * active_deltas[0]:
        return False, f"sar_cal_step_not_halving first={active_deltas[0]:.3f} last={active_deltas[-1]:.3f}"

    direction_checks = direction_ok = 0
    for idx, (edge_row, out) in enumerate(samples):
        previous = reset_mean if idx == 0 else samples[idx - 1][1]
        delta = out - previous
        errv = edge_row["vin"] - 0.45
        if abs(delta) <= 0.004 or abs(errv) <= 0.005:
            continue
        direction_checks += 1
        if (errv > 0.0 and delta > 0.0) or (errv < 0.0 and delta < 0.0):
            direction_ok += 1
    if direction_checks < 3:
        return False, f"sar_cal_too_few_direction_checks={direction_checks}"
    if direction_ok < direction_checks - 1:
        return False, f"sar_cal_direction_mismatches={direction_checks - direction_ok}/{direction_checks}"

    metric_values = [r.get("metric", 0.0) for r in rows if r["time"] > 20e-9]
    if metric_values and max(metric_values) <= 0.45:
        return False, "sar_cal_done_never_asserted"
    return True, (
        f"sar_cal reset={reset_mean:.3f} span={out_span:.3f} "
        f"direction={direction_ok}/{direction_checks}; sar_step_first_last={active_deltas[0]:.3f}/{active_deltas[-1]:.3f}"
    )


def check_release_filter_chain(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "rst", "vin", "out", "metric"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/clk/rst/vin/out/metric"
    post_rows = [r for r in rows if r["rst"] <= 0.45 and r["time"] > 3e-9]
    if len(post_rows) < 10:
        return False, f"too_few_post_reset_rows={len(post_rows)}"

    out_vals = [r["out"] for r in post_rows]
    metric_vals = [r["metric"] for r in post_rows]
    out_min = min(out_vals)
    out_max = max(out_vals)
    metric_min = min(metric_vals)
    metric_max = max(metric_vals)
    if not (-0.02 <= out_min <= out_max <= 0.92):
        return False, f"out_range=({out_min:.3f},{out_max:.3f})"
    if not (-0.10 <= metric_min <= metric_max <= 1.00):
        return False, f"metric_range=({metric_min:.3f},{metric_max:.3f})"
    if out_max - out_min < 0.18:
        return False, f"out_span_too_small={out_max - out_min:.3f}"

    low_rows = [r for r in post_rows if r["vin"] < 0.35]
    high_rows = [r for r in post_rows if r["vin"] > 0.60]
    if not low_rows or not high_rows:
        return False, "missing_low_or_high_vin_window"
    low_min = min(r["out"] for r in low_rows)
    high_max = max(r["out"] for r in high_rows)
    if high_max <= low_min + 0.10:
        return False, f"gain_response_too_small low_min={low_min:.3f} high_max={high_max:.3f}"

    return True, (
        f"release_filter_chain out_span={out_max - out_min:.3f} "
        f"low_min={low_min:.3f} high_max={high_max:.3f}"
    )


def check_acquisition_limited_sample_hold(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "sample", "rst", "vin", "vout", "metric"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/sample/rst/vin/vout/metric"

    reset_out = mean_in_window(rows, "vout", 0.5e-9, 2.0e-9)
    first_track_vout = mean_in_window(rows, "vout", 5.1e-9, 5.8e-9)
    first_track_vin = mean_in_window(rows, "vin", 5.1e-9, 5.8e-9)
    early_track_vout = mean_in_window(rows, "vout", 6.0e-9, 6.8e-9)
    early_track_vin = mean_in_window(rows, "vin", 6.0e-9, 6.8e-9)
    late_track_vout = mean_in_window(rows, "vout", 9.0e-9, 9.8e-9)
    late_track_vin = mean_in_window(rows, "vin", 9.0e-9, 9.8e-9)
    hold_early = mean_in_window(rows, "vout", 10.5e-9, 12.0e-9)
    hold_late = mean_in_window(rows, "vout", 17.0e-9, 19.0e-9)
    tracking_metric = mean_in_window(rows, "metric", 6.0e-9, 9.0e-9)
    hold_metric = mean_in_window(rows, "metric", 12.0e-9, 18.0e-9)
    if None in (
        reset_out,
        first_track_vout,
        first_track_vin,
        early_track_vout,
        early_track_vin,
        late_track_vout,
        late_track_vin,
        hold_early,
        hold_late,
        tracking_metric,
        hold_metric,
    ):
        return False, "acq_hold_missing_sample_windows"
    assert reset_out is not None
    assert first_track_vout is not None
    assert first_track_vin is not None
    assert early_track_vout is not None
    assert early_track_vin is not None
    assert late_track_vout is not None
    assert late_track_vin is not None
    assert hold_early is not None
    assert hold_late is not None
    assert tracking_metric is not None
    assert hold_metric is not None

    if abs(reset_out - 0.45) > 0.05:
        return False, f"acq_hold_reset_out={reset_out:.3f}"
    initial_error = abs(first_track_vout - first_track_vin)
    early_error = abs(early_track_vout - early_track_vin)
    late_error = abs(late_track_vout - late_track_vin)
    if initial_error < 0.09:
        return False, f"acq_hold_instantaneous_jump initial_error={initial_error:.3f}"
    if late_error > early_error - 0.025:
        return False, f"acq_hold_no_settling_improvement early={early_error:.3f} late={late_error:.3f}"
    hold_delta = abs(hold_late - hold_early)
    if hold_delta > 0.035:
        return False, f"acq_hold_drifted_after_fall delta={hold_delta:.3f}"
    if tracking_metric < 0.65 or hold_metric > 0.20:
        return False, (
            f"acq_hold_metric_wrong tracking={tracking_metric:.3f} "
            f"hold={hold_metric:.3f}"
        )
    return True, (
        "acquisition_limited_sample_hold "
        f"errors={initial_error:.3f}/{early_error:.3f}/{late_error:.3f} "
        f"hold_delta={hold_delta:.3f} metric={tracking_metric:.3f}/{hold_metric:.3f}"
    )


def check_programmable_gain_amplifier(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "rst", "gain_sel", "vin", "out", "metric"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/clk/rst/gain_sel/vin/out/metric"

    reset_out = mean_in_window(rows, "out", 0.5e-9, 2.0e-9)
    high_clip_out = mean_in_window(rows, "out", 28.0e-9, 34.0e-9)
    high_clip_metric = mean_in_window(rows, "metric", 28.0e-9, 34.0e-9)
    low_clip_out = mean_in_window(rows, "out", 38.0e-9, 43.0e-9)
    low_clip_metric = mean_in_window(rows, "metric", 38.0e-9, 43.0e-9)
    low_gain_out = mean_in_window(rows, "out", 58.0e-9, 66.0e-9)
    low_gain_vin = mean_in_window(rows, "vin", 58.0e-9, 66.0e-9)
    low_gain_metric = mean_in_window(rows, "metric", 58.0e-9, 66.0e-9)
    late_clip_out = mean_in_window(rows, "out", 76.0e-9, 82.0e-9)
    late_clip_metric = mean_in_window(rows, "metric", 76.0e-9, 82.0e-9)
    if None in (
        reset_out,
        high_clip_out,
        high_clip_metric,
        low_clip_out,
        low_clip_metric,
        low_gain_out,
        low_gain_vin,
        low_gain_metric,
        late_clip_out,
        late_clip_metric,
    ):
        return False, "pga_missing_sample_windows"
    assert reset_out is not None
    assert high_clip_out is not None
    assert high_clip_metric is not None
    assert low_clip_out is not None
    assert low_clip_metric is not None
    assert low_gain_out is not None
    assert low_gain_vin is not None
    assert low_gain_metric is not None
    assert late_clip_out is not None
    assert late_clip_metric is not None

    post_reset_rows = [r for r in rows if r["rst"] <= 0.45 and r["time"] > 3e-9]
    if not post_reset_rows:
        return False, "pga_no_post_reset_rows"
    out_min = min(r["out"] for r in post_reset_rows)
    out_max = max(r["out"] for r in post_reset_rows)
    if not (-0.02 <= out_min <= out_max <= 0.92):
        return False, f"pga_unclamped_range=({out_min:.3f},{out_max:.3f})"
    if abs(reset_out - 0.45) > 0.05:
        return False, f"pga_reset_out={reset_out:.3f}"
    if high_clip_out < 0.84 or late_clip_out < 0.84:
        return False, f"pga_high_gain_not_railed high={high_clip_out:.3f} late={late_clip_out:.3f}"
    if low_clip_out > 0.08:
        return False, f"pga_negative_swing_not_railed low={low_clip_out:.3f}"
    if not (0.48 <= low_gain_out <= 0.75):
        return False, f"pga_low_gain_unclipped_out={low_gain_out:.3f}"
    if abs(low_gain_out - low_gain_vin) < 0.015:
        return False, f"pga_gain_select_passthrough out={low_gain_out:.3f} vin={low_gain_vin:.3f}"
    if high_clip_metric < 0.65 or low_clip_metric < 0.65 or late_clip_metric < 0.65 or low_gain_metric > 0.20:
        return False, (
            "pga_clip_metric_wrong "
            f"high={high_clip_metric:.3f} low={low_clip_metric:.3f} "
            f"late={late_clip_metric:.3f} unclipped={low_gain_metric:.3f}"
        )
    return True, (
        "programmable_gain_amplifier "
        f"out_high_low_unclipped_late={high_clip_out:.3f}/{low_clip_out:.3f}/"
        f"{low_gain_out:.3f}/{late_clip_out:.3f} "
        f"metric={high_clip_metric:.3f}/{low_clip_metric:.3f}/{low_gain_metric:.3f}/{late_clip_metric:.3f}"
    )


def check_release_voltage_gain_amplifier(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "rst", "vin", "out", "metric"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/clk/rst/vin/out/metric"

    reset_out = mean_in_window(rows, "out", 0.5e-9, 2.0e-9)
    high_out = mean_in_window(rows, "out", 16.0e-9, 24.0e-9)
    mid_out = mean_in_window(rows, "out", 33.0e-9, 36.0e-9)
    low_out = mean_in_window(rows, "out", 46.0e-9, 55.0e-9)
    late_high_out = mean_in_window(rows, "out", 74.0e-9, 79.0e-9)
    high_metric = mean_in_window(rows, "metric", 16.0e-9, 24.0e-9)
    mid_metric = mean_in_window(rows, "metric", 33.0e-9, 36.0e-9)
    low_metric = mean_in_window(rows, "metric", 46.0e-9, 55.0e-9)
    if None in (reset_out, high_out, mid_out, low_out, late_high_out, high_metric, mid_metric, low_metric):
        return False, "gain_amp_missing_sample_windows"
    assert reset_out is not None
    assert high_out is not None
    assert mid_out is not None
    assert low_out is not None
    assert late_high_out is not None
    assert high_metric is not None
    assert mid_metric is not None
    assert low_metric is not None

    out_vals = [r["out"] for r in rows if r["rst"] <= 0.45 and r["time"] > 3e-9]
    if not out_vals:
        return False, "gain_amp_no_post_reset_rows"
    out_min = min(out_vals)
    out_max = max(out_vals)
    if not (-0.02 <= out_min <= out_max <= 0.92):
        return False, f"gain_amp_unclamped_range=({out_min:.3f},{out_max:.3f})"
    if abs(reset_out - 0.45) > 0.12 or abs(mid_out - 0.45) > 0.08:
        return False, f"gain_amp_common_mode reset={reset_out:.3f} mid={mid_out:.3f}"
    if high_out < 0.84 or late_high_out < 0.80:
        return False, f"gain_amp_high_not_railed high={high_out:.3f} late={late_high_out:.3f}"
    if low_out > 0.08:
        return False, f"gain_amp_low_not_railed low={low_out:.3f}"
    if high_metric < 0.65 or low_metric < 0.65 or mid_metric > 0.18:
        return False, (
            "gain_amp_saturation_metric_wrong "
            f"high={high_metric:.3f} mid={mid_metric:.3f} low={low_metric:.3f}"
        )
    return True, (
        "release_voltage_gain_amplifier "
        f"out_high_mid_low={high_out:.3f}/{mid_out:.3f}/{low_out:.3f} "
        f"sat_metric={high_metric:.3f}/{mid_metric:.3f}/{low_metric:.3f}"
    )


def check_precision_rectifier_envelope_detector(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "rst", "vin", "rect", "env", "metric"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/clk/rst/vin/rect/env/metric"

    reset_rect = mean_in_window(rows, "rect", 0.5e-9, 2.0e-9)
    reset_env = mean_in_window(rows, "env", 0.5e-9, 2.0e-9)
    pos_rect = mean_in_window(rows, "rect", 7.0e-9, 10.0e-9)
    center_rect = mean_in_window(rows, "rect", 15.0e-9, 17.0e-9)
    neg_rect = mean_in_window(rows, "rect", 22.0e-9, 26.0e-9)
    peak_env = mean_in_window(rows, "env", 43.0e-9, 48.0e-9)
    hold_env = mean_in_window(rows, "env", 56.0e-9, 64.0e-9)
    hold_rect = mean_in_window(rows, "rect", 56.0e-9, 64.0e-9)
    hold_metric = mean_in_window(rows, "metric", 56.0e-9, 64.0e-9)
    required_windows = (
        reset_rect,
        reset_env,
        pos_rect,
        center_rect,
        neg_rect,
        peak_env,
        hold_env,
        hold_rect,
        hold_metric,
    )
    if None in required_windows:
        return False, "rectifier_missing_sample_windows"
    assert reset_rect is not None
    assert reset_env is not None
    assert pos_rect is not None
    assert center_rect is not None
    assert neg_rect is not None
    assert peak_env is not None
    assert hold_env is not None
    assert hold_rect is not None
    assert hold_metric is not None

    if abs(reset_rect - 0.45) > 0.10 or abs(reset_env - 0.45) > 0.10:
        return False, f"rectifier_reset_common_mode rect={reset_rect:.3f} env={reset_env:.3f}"
    if pos_rect < 0.62:
        return False, f"rectifier_positive_half_not_rectified={pos_rect:.3f}"
    if neg_rect < 0.62:
        return False, f"rectifier_negative_half_not_rectified={neg_rect:.3f}"
    if abs(center_rect - 0.45) > 0.08:
        return False, f"rectifier_center_not_common_mode={center_rect:.3f}"
    if peak_env < 0.74:
        return False, f"rectifier_envelope_peak_too_low={peak_env:.3f}"
    if hold_env < hold_rect + 0.10 or hold_metric < 0.35:
        return False, (
            "rectifier_envelope_hold_missing "
            f"env={hold_env:.3f} rect={hold_rect:.3f} metric={hold_metric:.3f}"
        )

    post = [r for r in rows if r["rst"] <= 0.45 and r["time"] > 3e-9]
    if not post:
        return False, "rectifier_no_post_reset_rows"
    below_rect = sum(1 for r in post if r["env"] + 0.06 < r["rect"])
    if below_rect > max(2, len(post) // 20):
        return False, f"rectifier_envelope_below_rect_count={below_rect}"

    selected = [r for r in post if 5e-9 <= r["time"] <= 30e-9 or 40e-9 <= r["time"] <= 68e-9]
    errors = [abs(r["rect"] - min(0.9, 0.45 + abs(r["vin"] - 0.45))) for r in selected]
    if errors:
        p90 = sorted(errors)[int(0.90 * (len(errors) - 1))]
        if p90 > 0.09:
            return False, f"rectifier_rect_abs_tracking_p90={p90:.3f}"

    return True, (
        "precision_rectifier_envelope_detector "
        f"pos/neg={pos_rect:.3f}/{neg_rect:.3f} env_peak={peak_env:.3f} "
        f"hold={hold_env:.3f}/{hold_rect:.3f}"
    )


def check_converter_static_linearity_measurement_flow(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "rst", "vin", "code", "recon", "dnl", "inl"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/clk/rst/vin/code/recon/dnl/inl"

    vth = 0.45
    edge_idx = [
        idx
        for idx in range(1, len(rows))
        if rows[idx - 1]["clk"] <= vth < rows[idx]["clk"] and rows[idx]["rst"] <= vth
    ]
    if len(edge_idx) < 12:
        return False, f"too_few_converter_samples={len(edge_idx)}"

    # Sample after the output transition has settled.  EVAS writes denser rows
    # than Spectre around transition breakpoints, so row-index offsets can land
    # in the middle of a transition and compare mixed old/new metric values.
    sample_times = [rows[idx]["time"] + 0.7e-9 for idx in edge_idx]
    samples = sample_rows_at_or_after_times(rows, sample_times)
    if len(samples) < 12:
        return False, f"too_few_settled_converter_samples={len(samples)}"
    codes = [max(0, min(15, round(r["code"] / 0.06))) for r in samples]
    distinct_codes = sorted(set(codes))
    if len(distinct_codes) < 13 or distinct_codes[0] > 1 or distinct_codes[-1] < 14:
        return False, f"converter_code_coverage={distinct_codes}"
    code_drops = sum(1 for prev, cur in zip(codes, codes[1:]) if cur < prev)
    if code_drops:
        return False, f"converter_code_not_monotonic drops={code_drops}"

    by_code: dict[int, list[dict[str, float]]] = {}
    for code, row in zip(codes, samples):
        by_code.setdefault(code, []).append(row)
    recon_by_code = {
        code: sum(row["recon"] for row in code_rows) / len(code_rows)
        for code, code_rows in by_code.items()
    }
    ordered_codes = sorted(recon_by_code)
    recon_vals = [recon_by_code[code] for code in ordered_codes]
    recon_drops = sum(1 for prev, cur in zip(recon_vals, recon_vals[1:]) if cur < prev - 0.015)
    if recon_drops:
        return False, f"converter_reconstruction_not_monotonic drops={recon_drops}"
    steps = [cur - prev for prev, cur in zip(recon_vals, recon_vals[1:])]
    if len(steps) < 8 or min(steps) < 0.025:
        return False, f"converter_reconstruction_steps_invalid={steps}"
    step_spread = max(steps) - min(steps)
    if step_spread < 0.010:
        return False, f"converter_dnl_not_visible step_spread={step_spread:.4f}"

    post = [r for r in rows if r["rst"] <= vth and r["time"] > 3e-9]
    dnl_vals = [r["dnl"] for r in post]
    inl_vals = [r["inl"] for r in post]
    if not dnl_vals or not inl_vals:
        return False, "converter_missing_metric_rows"
    dnl_span = max(dnl_vals) - min(dnl_vals)
    inl_span = max(inl_vals) - min(inl_vals)
    if dnl_span < 0.035 or inl_span < 0.050:
        return False, f"converter_linearity_metrics_flat dnl={dnl_span:.3f} inl={inl_span:.3f}"

    metric_tol = 0.065
    max_inl_err = 0.0
    max_dnl_err = 0.0
    dnl_checks = 0
    prev_code: int | None = None
    prev_recon: float | None = None
    for row, code in zip(samples, codes):
        recon = row["recon"]
        expected_inl = max(0.05, min(0.85, 0.45 + 3.0 * (recon - 0.06 * code)))
        inl_err = abs(row["inl"] - expected_inl)
        max_inl_err = max(max_inl_err, inl_err)

        if prev_code is not None and prev_recon is not None and code > prev_code:
            ideal_step = 0.06 * (code - prev_code)
            expected_dnl = 0.45 + 4.0 * ((recon - prev_recon) - ideal_step)
            dnl_checks += 1
        else:
            expected_dnl = 0.45
        expected_dnl = max(0.05, min(0.85, expected_dnl))
        dnl_err = abs(row["dnl"] - expected_dnl)
        max_dnl_err = max(max_dnl_err, dnl_err)

        prev_code = code
        prev_recon = recon

    if max_inl_err > metric_tol:
        return False, f"converter_inl_metric_inconsistent err={max_inl_err:.3f}"
    if dnl_checks < 8:
        return False, f"converter_too_few_dnl_step_checks={dnl_checks}"
    if max_dnl_err > metric_tol:
        return False, f"converter_dnl_metric_inconsistent err={max_dnl_err:.3f}"

    return True, (
        "converter_static_linearity_measurement_flow "
        f"codes={len(distinct_codes)} step_spread={step_spread:.4f} "
        f"dnl_span={dnl_span:.3f} inl_span={inl_span:.3f} "
        f"metric_err={max_dnl_err:.3f}/{max_inl_err:.3f}"
    )


def check_release_two_pole_filter(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "rst", "vin", "out", "metric"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/clk/rst/vin/out/metric"

    reset_out = mean_in_window(rows, "out", 0.5e-9, 2.0e-9)
    early_high = mean_in_window(rows, "out", 14.0e-9, 16.0e-9)
    late_high = mean_in_window(rows, "out", 24.0e-9, 28.0e-9)
    early_low = mean_in_window(rows, "out", 44.0e-9, 47.0e-9)
    late_low = mean_in_window(rows, "out", 54.0e-9, 58.0e-9)
    metric_high = mean_in_window(rows, "metric", 14.0e-9, 20.0e-9)
    metric_low = mean_in_window(rows, "metric", 44.0e-9, 52.0e-9)
    if None in (reset_out, early_high, late_high, early_low, late_low, metric_high, metric_low):
        return False, "two_pole_missing_sample_windows"
    assert reset_out is not None
    assert early_high is not None
    assert late_high is not None
    assert early_low is not None
    assert late_low is not None
    assert metric_high is not None
    assert metric_low is not None

    post_rows = [r for r in rows if r["rst"] <= 0.45 and 3e-9 < r["time"] < 70e-9]
    if len(post_rows) < 10:
        return False, f"two_pole_too_few_post_reset_rows={len(post_rows)}"
    out_vals = [r["out"] for r in post_rows]
    metric_vals = [r["metric"] for r in post_rows]
    metric_span = max(metric_vals) - min(metric_vals)
    if not (-0.02 <= min(out_vals) <= max(out_vals) <= 0.92):
        return False, f"two_pole_out_range=({min(out_vals):.3f},{max(out_vals):.3f})"
    if abs(reset_out - 0.45) > 0.12:
        return False, f"two_pole_reset_out={reset_out:.3f}"
    if late_high <= early_high + 0.10 or early_high > 0.68:
        return False, f"two_pole_missing_lagged_rise early={early_high:.3f} late={late_high:.3f}"
    if late_low >= early_low - 0.06 or early_low < 0.20:
        return False, f"two_pole_missing_lagged_fall early={early_low:.3f} late={late_low:.3f}"
    if metric_span < 0.09 or metric_high <= 0.50 or metric_low >= 0.40:
        return False, (
            "two_pole_metric_not_state_difference "
            f"span={metric_span:.3f} high={metric_high:.3f} low={metric_low:.3f}"
        )
    return True, (
        "release_two_pole_filter "
        f"rise={early_high:.3f}->{late_high:.3f} "
        f"fall={early_low:.3f}->{late_low:.3f} metric_span={metric_span:.3f}"
    )


def check_release_amplifier_filter_chain(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {
        "time",
        "clk",
        "rst",
        "vin",
        "out",
        "metric",
    }
    if not rows or not required.issubset(rows[0]):
        missing = sorted(required - set(rows[0].keys())) if rows else sorted(required)
        return False, f"missing_columns={','.join(missing)}"

    early_high_out = mean_in_window(rows, "out", 12.5e-9, 15.0e-9)
    late_high_out = mean_in_window(rows, "out", 24.0e-9, 28.0e-9)
    early_high_metric = mean_in_window(rows, "metric", 12.5e-9, 15.0e-9)
    late_high_metric = mean_in_window(rows, "metric", 24.0e-9, 28.0e-9)
    mid_metric = mean_in_window(rows, "metric", 33.0e-9, 36.0e-9)
    low_metric = mean_in_window(rows, "metric", 46.0e-9, 55.0e-9)
    low_out = mean_in_window(rows, "out", 54.0e-9, 58.0e-9)
    if None in (
        early_high_out,
        late_high_out,
        early_high_metric,
        late_high_metric,
        mid_metric,
        low_metric,
        low_out,
    ):
        return False, "amp_filter_missing_sample_windows"
    assert early_high_out is not None
    assert late_high_out is not None
    assert early_high_metric is not None
    assert late_high_metric is not None
    assert mid_metric is not None
    assert low_metric is not None
    assert low_out is not None

    post_rows = [r for r in rows if r["rst"] <= 0.45 and 3e-9 < r["time"] < 70e-9]
    if len(post_rows) < 10:
        return False, f"amp_filter_too_few_post_reset_rows={len(post_rows)}"
    out_vals = [r["out"] for r in post_rows]
    metric_vals = [r["metric"] for r in post_rows]
    if not (-0.02 <= min(out_vals) <= max(out_vals) <= 0.92):
        return False, f"amp_filter_out_range=({min(out_vals):.3f},{max(out_vals):.3f})"
    if not (-0.02 <= min(metric_vals) <= max(metric_vals) <= 0.92):
        return False, f"amp_filter_metric_range=({min(metric_vals):.3f},{max(metric_vals):.3f})"
    if early_high_metric < 0.84 or late_high_metric < 0.84 or low_metric > 0.08:
        return False, (
            "amp_filter_metric_not_preamp_target "
            f"early={early_high_metric:.3f} late={late_high_metric:.3f} low={low_metric:.3f}"
        )
    if abs(mid_metric - 0.45) > 0.08:
        return False, f"amp_filter_mid_metric_not_common_mode={mid_metric:.3f}"
    if late_high_out <= early_high_out + 0.09:
        return False, f"amp_filter_missing_lagged_settling early={early_high_out:.3f} late={late_high_out:.3f}"
    if early_high_metric - early_high_out < 0.12:
        return False, f"amp_filter_output_not_lagging_metric gap={early_high_metric - early_high_out:.3f}"
    if low_out > 0.35:
        return False, f"amp_filter_output_not_falling low={low_out:.3f}"
    return True, (
        "release_amplifier_filter_chain "
        f"metric_high_low={early_high_metric:.3f}/{low_metric:.3f} "
        f"out_lag={early_high_out:.3f}->{late_high_out:.3f}"
    )


def check_release_signal_conditioning_chain(rows: list[dict[str, float]]) -> tuple[bool, str]:
    ok, note = check_release_filter_chain(rows)
    if not ok:
        return ok, note
    two_pole_ok, two_pole_note = check_release_two_pole_filter(rows)
    if not two_pole_ok:
        return False, two_pole_note
    high_rows = [r for r in rows if r["rst"] <= 0.45 and r["vin"] > 0.80]
    low_rows = [r for r in rows if r["rst"] <= 0.45 and r["vin"] < 0.20]
    if not high_rows or not low_rows:
        return False, "conditioning_chain_missing_limit_windows"
    high_max = max(r["out"] for r in high_rows)
    low_min = min(r["out"] for r in low_rows)
    if high_max > 0.92 or low_min < -0.02:
        return False, f"conditioning_chain_unbounded=({low_min:.3f},{high_max:.3f})"
    if high_max <= low_min + 0.18:
        return False, f"conditioning_chain_response_too_small=({low_min:.3f},{high_max:.3f})"
    return True, f"{note}; {two_pole_note}; conditioning_limits={low_min:.3f}/{high_max:.3f}"


def check_release_soft_hysteretic_limiter(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "rst", "vin", "out", "metric"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/clk/rst/vin/out/metric"

    high_limited = mean_in_window(rows, "out", 16.0e-9, 24.0e-9)
    low_limited = mean_in_window(rows, "out", 46.0e-9, 55.0e-9)
    high_memory = mean_in_window(rows, "out", 31.0e-9, 36.0e-9)
    low_memory = mean_in_window(rows, "out", 61.0e-9, 66.0e-9)
    high_metric = mean_in_window(rows, "metric", 16.0e-9, 24.0e-9)
    low_metric = mean_in_window(rows, "metric", 46.0e-9, 55.0e-9)
    high_memory_metric = mean_in_window(rows, "metric", 31.0e-9, 36.0e-9)
    low_memory_metric = mean_in_window(rows, "metric", 61.0e-9, 66.0e-9)
    if None in (
        high_limited,
        low_limited,
        high_memory,
        low_memory,
        high_metric,
        low_metric,
        high_memory_metric,
        low_memory_metric,
    ):
        return False, "soft_limiter_missing_sample_windows"
    assert high_limited is not None
    assert low_limited is not None
    assert high_memory is not None
    assert low_memory is not None
    assert high_metric is not None
    assert low_metric is not None
    assert high_memory_metric is not None
    assert low_memory_metric is not None

    post_rows = [r for r in rows if r["rst"] <= 0.45 and 3e-9 < r["time"] < 70e-9]
    if len(post_rows) < 10:
        return False, f"soft_limiter_too_few_post_reset_rows={len(post_rows)}"
    out_min = min(r["out"] for r in post_rows)
    out_max = max(r["out"] for r in post_rows)
    metric_span = max(r["metric"] for r in post_rows) - min(r["metric"] for r in post_rows)
    if not (-0.02 <= out_min <= out_max <= 0.92):
        return False, f"soft_limiter_out_range=({out_min:.3f},{out_max:.3f})"
    if high_limited > 0.84 or high_limited < 0.70:
        return False, f"soft_limiter_high_compression={high_limited:.3f}"
    if low_limited < 0.08 or low_limited > 0.22:
        return False, f"soft_limiter_low_compression={low_limited:.3f}"
    if high_memory <= low_memory + 0.10:
        return False, f"soft_limiter_hysteresis_not_visible high={high_memory:.3f} low={low_memory:.3f}"
    if high_metric < 0.58 or high_memory_metric < 0.58 or low_metric > 0.32 or low_memory_metric > 0.32:
        return False, (
            "soft_limiter_metric_not_stateful "
            f"high={high_metric:.3f}/{high_memory_metric:.3f} low={low_metric:.3f}/{low_memory_metric:.3f}"
        )
    if metric_span < 0.30:
        return False, f"soft_limiter_metric_span_too_small={metric_span:.3f}"
    return True, (
        "release_soft_hysteretic_limiter "
        f"limited={low_limited:.3f}/{high_limited:.3f} "
        f"memory={low_memory:.3f}/{high_memory:.3f} metric_span={metric_span:.3f}"
    )


def check_release_quantized_reconstruction(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "rst", "vin", "out", "metric"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/clk/rst/vin/out/metric"
    vth = 0.45
    edge_idx = [
        idx for idx in range(1, len(rows))
        if rows[idx - 1]["clk"] <= vth < rows[idx]["clk"] and rows[idx]["rst"] <= vth
    ]
    if len(edge_idx) < 8:
        return False, f"too_few_post_reset_clk_edges={len(edge_idx)}"

    mismatches = 0
    checked = 0
    for idx in edge_idx:
        settle = min(idx + 3, len(rows) - 1)
        sample = max(0.0, min(0.9, rows[idx]["vin"]))
        code = round(sample / 0.9 * 15.0)
        expected = 0.9 * code / 15.0
        actual = rows[settle]["out"]
        checked += 1
        if abs(actual - expected) > 0.08:
            mismatches += 1
    if checked == 0:
        return False, "no_quantizer_samples"
    if mismatches > max(1, checked // 5):
        return False, f"quantized_recon_mismatches={mismatches}/{checked}"

    metric_vals = [r["metric"] for r in rows if r["rst"] <= vth]
    metric_hi = sum(1 for v in metric_vals if v > 0.45)
    metric_lo = sum(1 for v in metric_vals if v <= 0.45)
    if metric_hi == 0 or metric_lo == 0:
        return False, f"metric_not_windowed hi={metric_hi} lo={metric_lo}"
    return True, f"quantized_recon_mismatches={mismatches}/{checked} metric_hi={metric_hi}"


def check_bandgap_reference_macro_model(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "rst", "vin", "out", "metric"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/clk/rst/vin/out/metric"

    pre_start = mean_in_window(rows, "out", 4.0e-9, 7.5e-9)
    nominal_ref = mean_in_window(rows, "out", 27.0e-9, 36.0e-9)
    high_supply_ref = mean_in_window(rows, "out", 55.0e-9, 63.0e-9)
    brownout_ref = mean_in_window(rows, "out", 67.0e-9, 70.0e-9)
    valid_metric = mean_in_window(rows, "metric", 30.0e-9, 62.0e-9)
    if None in (pre_start, nominal_ref, high_supply_ref, brownout_ref, valid_metric):
        return False, "bandgap_missing_sample_windows"
    assert pre_start is not None
    assert nominal_ref is not None
    assert high_supply_ref is not None
    assert brownout_ref is not None
    assert valid_metric is not None

    if pre_start > 0.08:
        return False, f"bandgap_reference_not_held_low_pre_start={pre_start:.3f}"
    if not (0.50 <= nominal_ref <= 0.60):
        return False, f"bandgap_reference_nominal_wrong={nominal_ref:.3f}"
    line_delta = abs(high_supply_ref - nominal_ref)
    if line_delta > 0.065:
        return False, f"bandgap_line_regulation_too_large={line_delta:.3f}"
    if brownout_ref > 0.12:
        return False, f"bandgap_brownout_not_reset={brownout_ref:.3f}"
    if valid_metric < 0.65:
        return False, f"bandgap_valid_metric_low={valid_metric:.3f}"
    return True, (
        "bandgap_reference_macro_model "
        f"ref={nominal_ref:.3f}/{high_supply_ref:.3f} line_delta={line_delta:.3f} "
        f"brownout={brownout_ref:.3f}"
    )


def check_ptat_ctat_reference_generator(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "rst", "vin", "out", "metric"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/clk/rst/vin/out/metric"

    cold_ref = mean_in_window(rows, "out", 8.0e-9, 16.0e-9)
    mid_ref = mean_in_window(rows, "out", 26.0e-9, 38.0e-9)
    hot_ref = mean_in_window(rows, "out", 52.0e-9, 72.0e-9)
    cold_ptat = mean_in_window(rows, "metric", 8.0e-9, 16.0e-9)
    hot_ptat = mean_in_window(rows, "metric", 52.0e-9, 72.0e-9)
    if None in (cold_ref, mid_ref, hot_ref, cold_ptat, hot_ptat):
        return False, "ptat_ctat_missing_sample_windows"
    assert cold_ref is not None
    assert mid_ref is not None
    assert hot_ref is not None
    assert cold_ptat is not None
    assert hot_ptat is not None

    ref_span = max(cold_ref, mid_ref, hot_ref) - min(cold_ref, mid_ref, hot_ref)
    if not (0.42 <= cold_ref <= 0.55 and 0.42 <= mid_ref <= 0.55 and 0.42 <= hot_ref <= 0.55):
        return False, f"ptat_ctat_reference_range={cold_ref:.3f}/{mid_ref:.3f}/{hot_ref:.3f}"
    if ref_span > 0.075:
        return False, f"ptat_ctat_reference_not_compensated span={ref_span:.3f}"
    if hot_ptat <= cold_ptat + 0.12:
        return False, f"ptat_metric_not_monotonic cold={cold_ptat:.3f} hot={hot_ptat:.3f}"
    return True, (
        "ptat_ctat_reference_generator "
        f"ref_span={ref_span:.3f} ptat={cold_ptat:.3f}->{hot_ptat:.3f}"
    )


def check_bias_voltage_generator_with_enable_trim(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "rst", "vin", "out", "metric"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/clk/rst/vin/out/metric"

    disabled_early = mean_in_window(rows, "out", 5.0e-9, 10.0e-9)
    low_trim = mean_in_window(rows, "out", 24.0e-9, 30.0e-9)
    high_trim = mean_in_window(rows, "out", 45.0e-9, 52.0e-9)
    disabled_late = mean_in_window(rows, "out", 58.0e-9, 64.0e-9)
    enabled_metric = mean_in_window(rows, "metric", 24.0e-9, 52.0e-9)
    disabled_metric = mean_in_window(rows, "metric", 58.0e-9, 64.0e-9)
    if None in (disabled_early, low_trim, high_trim, disabled_late, enabled_metric, disabled_metric):
        return False, "bias_trim_missing_sample_windows"
    assert disabled_early is not None
    assert low_trim is not None
    assert high_trim is not None
    assert disabled_late is not None
    assert enabled_metric is not None
    assert disabled_metric is not None

    if disabled_early > 0.08 or disabled_late > 0.08:
        return False, f"bias_not_disabled early={disabled_early:.3f} late={disabled_late:.3f}"
    if not (0.30 <= low_trim <= 0.50):
        return False, f"bias_low_trim_wrong={low_trim:.3f}"
    if high_trim <= low_trim + 0.14 or high_trim > 0.85:
        return False, f"bias_trim_span_wrong low={low_trim:.3f} high={high_trim:.3f}"
    if enabled_metric < 0.65 or disabled_metric > 0.15:
        return False, f"bias_metric_wrong enabled={enabled_metric:.3f} disabled={disabled_metric:.3f}"
    return True, (
        "bias_voltage_generator_with_enable_trim "
        f"disabled={disabled_early:.3f}/{disabled_late:.3f} trim={low_trim:.3f}->{high_trim:.3f}"
    )


def check_power_on_reset_detector(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "rst", "vin", "out", "metric"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/clk/rst/vin/out/metric"

    initial_reset = mean_in_window(rows, "out", 4.0e-9, 7.0e-9)
    delayed_reset = mean_in_window(rows, "out", 10.0e-9, 13.0e-9)
    released = mean_in_window(rows, "out", 22.0e-9, 38.0e-9)
    brownout_reset = mean_in_window(rows, "out", 46.0e-9, 52.0e-9)
    recovered = mean_in_window(rows, "out", 65.0e-9, 76.0e-9)
    released_metric = mean_in_window(rows, "metric", 22.0e-9, 38.0e-9)
    if None in (initial_reset, delayed_reset, released, brownout_reset, recovered, released_metric):
        return False, "por_missing_sample_windows"
    assert initial_reset is not None
    assert delayed_reset is not None
    assert released is not None
    assert brownout_reset is not None
    assert recovered is not None
    assert released_metric is not None

    if initial_reset < 0.65:
        return False, f"por_initial_not_asserted={initial_reset:.3f}"
    if delayed_reset < 0.65:
        return False, f"por_no_release_delay={delayed_reset:.3f}"
    if released > 0.20:
        return False, f"por_not_released={released:.3f}"
    if brownout_reset < 0.65:
        return False, f"por_brownout_not_asserted={brownout_reset:.3f}"
    if recovered > 0.20 or released_metric < 0.65:
        return False, f"por_recovery_wrong recovered={recovered:.3f} metric={released_metric:.3f}"
    return True, (
        "power_on_reset_detector "
        f"reset={initial_reset:.3f}->{released:.3f} brownout={brownout_reset:.3f}"
    )


def check_uvlo_brownout_detector(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "rst", "vin", "out", "metric"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/clk/rst/vin/out/metric"

    initial_low = mean_in_window(rows, "out", 5.0e-9, 9.0e-9)
    power_good = mean_in_window(rows, "out", 18.0e-9, 26.0e-9)
    hysteresis_hold = mean_in_window(rows, "out", 33.0e-9, 41.0e-9)
    brownout_low = mean_in_window(rows, "out", 48.0e-9, 53.0e-9)
    lower_threshold_hold = mean_in_window(rows, "out", 59.0e-9, 65.0e-9)
    recovered = mean_in_window(rows, "out", 72.0e-9, 78.0e-9)
    if None in (initial_low, power_good, hysteresis_hold, brownout_low, lower_threshold_hold, recovered):
        return False, "uvlo_missing_sample_windows"
    assert initial_low is not None
    assert power_good is not None
    assert hysteresis_hold is not None
    assert brownout_low is not None
    assert lower_threshold_hold is not None
    assert recovered is not None

    if initial_low > 0.20:
        return False, f"uvlo_initial_power_good_high={initial_low:.3f}"
    if power_good < 0.65 or hysteresis_hold < 0.65:
        return False, f"uvlo_hysteresis_hold_failed good={power_good:.3f} hold={hysteresis_hold:.3f}"
    if brownout_low > 0.20 or lower_threshold_hold > 0.20:
        return False, f"uvlo_brownout_or_lower_hold_failed brownout={brownout_low:.3f} hold={lower_threshold_hold:.3f}"
    if recovered < 0.65:
        return False, f"uvlo_not_recovered={recovered:.3f}"
    return True, (
        "uvlo_brownout_detector "
        f"pgood={power_good:.3f} hold={hysteresis_hold:.3f}/{lower_threshold_hold:.3f} "
        f"recover={recovered:.3f}"
    )


def check_ldo_regulator_macro_model(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "rst", "vin", "out", "metric"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/clk/rst/vin/out/metric"

    light_load = mean_in_window(rows, "out", 10.0e-9, 16.0e-9)
    heavy_load = mean_in_window(rows, "out", 28.0e-9, 40.0e-9)
    recovered = mean_in_window(rows, "out", 55.0e-9, 64.0e-9)
    heavy_metric = mean_in_window(rows, "metric", 28.0e-9, 40.0e-9)
    recovered_metric = mean_in_window(rows, "metric", 55.0e-9, 64.0e-9)
    if None in (light_load, heavy_load, recovered, heavy_metric, recovered_metric):
        return False, "ldo_missing_sample_windows"
    assert light_load is not None
    assert heavy_load is not None
    assert recovered is not None
    assert heavy_metric is not None
    assert recovered_metric is not None

    if not (0.56 <= light_load <= 0.66):
        return False, f"ldo_light_load_regulation_wrong={light_load:.3f}"
    if heavy_load >= light_load - 0.015:
        return False, f"ldo_load_step_no_droop light={light_load:.3f} heavy={heavy_load:.3f}"
    if recovered <= heavy_load + 0.025:
        return False, f"ldo_no_recovery heavy={heavy_load:.3f} recovered={recovered:.3f}"
    if recovered_metric < 0.65 or heavy_metric < 0.45:
        return False, f"ldo_metric_wrong heavy={heavy_metric:.3f} recovered={recovered_metric:.3f}"
    return True, (
        "ldo_regulator_macro_model "
        f"light/heavy/recovered={light_load:.3f}/{heavy_load:.3f}/{recovered:.3f}"
    )


def check_reference_startup_enable_flow(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "rst", "out", "metric"}
    has_legacy_vin = bool(rows and "vin" in rows[0])
    if has_legacy_vin:
        required.add("vin")
    else:
        required.update({"vdd_in", "en"})
    if not rows or not required.issubset(rows[0]):
        missing = sorted(required - set(rows[0].keys())) if rows else sorted(required)
        return False, f"missing_columns={','.join(missing)}"

    supply_off = mean_in_window(rows, "out", 5.0e-9, 9.0e-9)
    pre_enable = mean_in_window(rows, "out", 15.0e-9, 22.0e-9)
    startup_ref = mean_in_window(rows, "out", 39.0e-9, 52.0e-9)
    startup_metric = mean_in_window(rows, "metric", 39.0e-9, 52.0e-9)
    dip_reset = mean_in_window(rows, "out", 57.0e-9, 61.0e-9)
    recovered_metric = mean_in_window(rows, "metric", 74.0e-9, 79.0e-9)
    if has_legacy_vin:
        pre_supply = pre_vin = mean_in_window(rows, "vin", 15.0e-9, 22.0e-9)
        startup_supply = startup_vin = mean_in_window(rows, "vin", 39.0e-9, 52.0e-9)
        dip_supply = dip_vin = mean_in_window(rows, "vin", 57.0e-9, 61.0e-9)
        pre_en = 0.0
        startup_en = 0.9
    else:
        pre_supply = mean_in_window(rows, "vdd_in", 15.0e-9, 22.0e-9)
        startup_supply = mean_in_window(rows, "vdd_in", 39.0e-9, 52.0e-9)
        dip_supply = mean_in_window(rows, "vdd_in", 57.0e-9, 61.0e-9)
        pre_en = mean_in_window(rows, "en", 15.0e-9, 22.0e-9)
        startup_en = mean_in_window(rows, "en", 39.0e-9, 52.0e-9)
        pre_vin = pre_supply
        startup_vin = startup_supply
        dip_vin = dip_supply
    if None in (
        supply_off,
        pre_enable,
        startup_ref,
        startup_metric,
        dip_reset,
        recovered_metric,
        pre_supply,
        startup_supply,
        dip_supply,
        pre_en,
        startup_en,
    ):
        return False, "ref_startup_missing_sample_windows"
    assert supply_off is not None
    assert pre_enable is not None
    assert startup_ref is not None
    assert startup_metric is not None
    assert dip_reset is not None
    assert recovered_metric is not None
    assert pre_supply is not None
    assert startup_supply is not None
    assert dip_supply is not None
    assert pre_en is not None
    assert startup_en is not None

    if supply_off > 0.08:
        return False, f"ref_startup_supply_off_not_low={supply_off:.3f}"
    if pre_enable > 0.12:
        return False, f"ref_startup_ignores_enable={pre_enable:.3f}"
    if has_legacy_vin:
        assert pre_vin is not None
        if not (0.32 < pre_vin < 0.55):
            return False, f"ref_startup_pre_enable_vin_wrong={pre_vin:.3f}"
    elif pre_supply <= 0.55 or pre_en >= 0.20:
        return False, f"ref_startup_pre_enable_inputs_wrong supply={pre_supply:.3f} en={pre_en:.3f}"
    if startup_ref < 0.48 or startup_ref > 0.60:
        return False, f"ref_startup_wrong_reference={startup_ref:.3f}"
    if startup_metric < 0.65:
        return False, f"ref_startup_valid_metric_low={startup_metric:.3f}"
    if startup_supply <= 0.55 or startup_en <= 0.55:
        return False, f"ref_startup_enable_window_inputs_low supply={startup_supply:.3f} en={startup_en:.3f}"
    if dip_reset > 0.10:
        return False, f"ref_startup_supply_dip_not_reset={dip_reset:.3f}"
    if dip_supply >= 0.32:
        return False, f"ref_startup_dip_supply_high={dip_supply:.3f}"
    if recovered_metric < 0.45:
        return False, f"ref_startup_no_recovery_metric={recovered_metric:.3f}"
    return True, (
        "reference_startup_enable_flow "
        f"pre_enable={pre_enable:.3f} startup={startup_ref:.3f} "
        f"metric={startup_metric:.3f}->{recovered_metric:.3f} dip={dip_reset:.3f}"
    )


def check_ldo_load_step_recovery_flow(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "rst", "vin", "out", "metric", "load_mon", "ctrl_mon"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/clk/rst/vin/out/metric/load_mon/ctrl_mon"

    pre_step = mean_in_window(rows, "out", 10.0e-9, 15.0e-9)
    early_droop = mean_in_window(rows, "out", 18.0e-9, 22.0e-9)
    late_recovery = mean_in_window(rows, "out", 34.0e-9, 40.0e-9)
    light_recovery = mean_in_window(rows, "out", 52.0e-9, 60.0e-9)
    second_droop = mean_in_window(rows, "out", 64.0e-9, 68.0e-9)
    late_metric = mean_in_window(rows, "metric", 34.0e-9, 40.0e-9)
    pre_load = mean_in_window(rows, "load_mon", 10.0e-9, 15.0e-9)
    heavy_load = mean_in_window(rows, "load_mon", 18.0e-9, 22.0e-9)
    light_load = mean_in_window(rows, "load_mon", 52.0e-9, 60.0e-9)
    second_load = mean_in_window(rows, "load_mon", 64.0e-9, 68.0e-9)
    pre_ctrl = mean_in_window(rows, "ctrl_mon", 10.0e-9, 15.0e-9)
    heavy_ctrl = mean_in_window(rows, "ctrl_mon", 18.0e-9, 22.0e-9)
    light_ctrl = mean_in_window(rows, "ctrl_mon", 52.0e-9, 60.0e-9)
    second_ctrl = mean_in_window(rows, "ctrl_mon", 64.0e-9, 68.0e-9)
    if None in (
        pre_step,
        early_droop,
        late_recovery,
        light_recovery,
        second_droop,
        late_metric,
        pre_load,
        heavy_load,
        light_load,
        second_load,
        pre_ctrl,
        heavy_ctrl,
        light_ctrl,
        second_ctrl,
    ):
        return False, "ldo_flow_missing_sample_windows"
    assert pre_step is not None
    assert early_droop is not None
    assert late_recovery is not None
    assert light_recovery is not None
    assert second_droop is not None
    assert late_metric is not None
    assert pre_load is not None
    assert heavy_load is not None
    assert light_load is not None
    assert second_load is not None
    assert pre_ctrl is not None
    assert heavy_ctrl is not None
    assert light_ctrl is not None
    assert second_ctrl is not None

    if not (0.56 <= pre_step <= 0.66):
        return False, f"ldo_flow_pre_step_regulation_wrong={pre_step:.3f}"
    if early_droop >= pre_step - 0.04:
        return False, f"ldo_flow_no_transient_droop pre={pre_step:.3f} early={early_droop:.3f}"
    if late_recovery <= early_droop + 0.045:
        return False, f"ldo_flow_no_closed_loop_recovery early={early_droop:.3f} late={late_recovery:.3f}"
    if light_recovery <= late_recovery:
        return False, f"ldo_flow_light_load_not_higher light={light_recovery:.3f} late={late_recovery:.3f}"
    if second_droop >= light_recovery - 0.035:
        return False, f"ldo_flow_second_step_no_droop second={second_droop:.3f} light={light_recovery:.3f}"
    if late_metric < 0.65:
        return False, f"ldo_flow_recovery_metric_low={late_metric:.3f}"
    if heavy_load <= pre_load + 0.45 or light_load >= heavy_load - 0.35 or second_load <= light_load + 0.35:
        return False, (
            f"ldo_flow_load_monitor_wrong pre/heavy/light/second="
            f"{pre_load:.3f}/{heavy_load:.3f}/{light_load:.3f}/{second_load:.3f}"
        )
    if heavy_ctrl <= pre_ctrl + 0.12:
        return False, f"ldo_flow_ctrl_no_heavy_load_response pre={pre_ctrl:.3f} heavy={heavy_ctrl:.3f}"
    if light_ctrl >= heavy_ctrl - 0.08:
        return False, f"ldo_flow_ctrl_not_reduced_at_light_load light={light_ctrl:.3f} heavy={heavy_ctrl:.3f}"
    if second_ctrl <= light_ctrl + 0.08:
        return False, f"ldo_flow_ctrl_no_second_step_response second={second_ctrl:.3f} light={light_ctrl:.3f}"
    return True, (
        "ldo_load_step_recovery_flow "
        f"pre/early/late/light/second={pre_step:.3f}/{early_droop:.3f}/"
        f"{late_recovery:.3f}/{light_recovery:.3f}/{second_droop:.3f} "
        f"load={pre_load:.3f}/{heavy_load:.3f}/{light_load:.3f}/{second_load:.3f} "
        f"ctrl={pre_ctrl:.3f}/{heavy_ctrl:.3f}/{light_ctrl:.3f}/{second_ctrl:.3f}"
    )


def check_lna_gain_compression_macro(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "rst", "vin", "out", "metric"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/clk/rst/vin/out/metric"

    small_vin = mean_in_window(rows, "vin", 12.0e-9, 22.0e-9)
    small_out = mean_in_window(rows, "out", 12.0e-9, 22.0e-9)
    comp_high = mean_in_window(rows, "out", 34.0e-9, 44.0e-9)
    comp_low = mean_in_window(rows, "out", 55.0e-9, 63.0e-9)
    comp_metric = mean_in_window(rows, "metric", 34.0e-9, 63.0e-9)
    if None in (small_vin, small_out, comp_high, comp_low, comp_metric):
        return False, "lna_missing_sample_windows"
    assert small_vin is not None
    assert small_out is not None
    assert comp_high is not None
    assert comp_low is not None
    assert comp_metric is not None

    if small_out <= small_vin + 0.045:
        return False, f"lna_small_signal_gain_missing vin={small_vin:.3f} out={small_out:.3f}"
    if not (0.74 <= comp_high <= 0.87):
        return False, f"lna_high_compression_wrong={comp_high:.3f}"
    if not (0.04 <= comp_low <= 0.18):
        return False, f"lna_low_compression_wrong={comp_low:.3f}"
    if comp_metric < 0.55:
        return False, f"lna_compression_metric_low={comp_metric:.3f}"
    return True, (
        "lna_gain_compression_macro "
        f"small={small_vin:.3f}->{small_out:.3f} compressed={comp_low:.3f}/{comp_high:.3f}"
    )


def check_rf_mixer_downconverter_macro(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "rst", "vin", "out", "metric"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/clk/rst/vin/out/metric"

    def mean_selected(start: float, stop: float, key: str, *, clk_high: bool, vin_high: bool) -> float | None:
        total = 0.0
        duration = 0.0

        def interp(a: dict[str, float], b: dict[str, float], t: float, field: str) -> float:
            t0 = a["time"]
            t1 = b["time"]
            if t1 <= t0:
                return a[field]
            frac = max(0.0, min(1.0, (t - t0) / (t1 - t0)))
            return a[field] + frac * (b[field] - a[field])

        for row, nxt in zip(rows, rows[1:]):
            left = max(start, row["time"])
            right = min(stop, nxt["time"])
            if right <= left:
                continue
            mid = 0.5 * (left + right)
            rst_mid = interp(row, nxt, mid, "rst")
            clk_mid = interp(row, nxt, mid, "clk")
            vin_mid = interp(row, nxt, mid, "vin")
            if rst_mid > 0.45:
                continue
            if clk_high and clk_mid <= 0.75:
                continue
            if (not clk_high) and clk_mid >= 0.15:
                continue
            if vin_high and vin_mid <= 0.55:
                continue
            if (not vin_high) and vin_mid >= 0.38:
                continue
            value_left = interp(row, nxt, left, key)
            value_right = interp(row, nxt, right, key)
            total += 0.5 * (value_left + value_right) * (right - left)
            duration += right - left
        if duration <= 0.0:
            return None
        return total / duration

    pos_hi = mean_selected(10.0e-9, 30.0e-9, "out", clk_high=True, vin_high=True)
    pos_lo = mean_selected(10.0e-9, 30.0e-9, "out", clk_high=False, vin_high=True)
    neg_hi = mean_selected(38.0e-9, 54.0e-9, "out", clk_high=True, vin_high=False)
    neg_lo = mean_selected(38.0e-9, 54.0e-9, "out", clk_high=False, vin_high=False)
    active_metric = mean_in_window(rows, "metric", 12.0e-9, 52.0e-9)
    if None in (pos_hi, pos_lo, neg_hi, neg_lo, active_metric):
        return False, "mixer_missing_sample_windows"
    assert pos_hi is not None
    assert pos_lo is not None
    assert neg_hi is not None
    assert neg_lo is not None
    assert active_metric is not None

    if pos_hi <= 0.58 or pos_lo >= 0.34:
        return False, f"mixer_positive_lo_polarity_wrong hi={pos_hi:.3f} lo={pos_lo:.3f}"
    if neg_hi >= 0.34 or neg_lo <= 0.56:
        return False, f"mixer_negative_lo_polarity_wrong hi={neg_hi:.3f} lo={neg_lo:.3f}"
    if active_metric < 0.40:
        return False, f"mixer_active_metric_low={active_metric:.3f}"
    return True, (
        "rf_mixer_downconverter_macro "
        f"pos={pos_hi:.3f}/{pos_lo:.3f} neg={neg_hi:.3f}/{neg_lo:.3f}"
    )


def check_pa_compression_macro(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "rst", "vin", "out", "metric"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/clk/rst/vin/out/metric"

    small_vin = mean_in_window(rows, "vin", 12.0e-9, 22.0e-9)
    small_out = mean_in_window(rows, "out", 12.0e-9, 22.0e-9)
    high_out = mean_in_window(rows, "out", 32.0e-9, 42.0e-9)
    low_out = mean_in_window(rows, "out", 54.0e-9, 62.0e-9)
    limit_metric = mean_in_window(rows, "metric", 32.0e-9, 62.0e-9)
    if None in (small_vin, small_out, high_out, low_out, limit_metric):
        return False, "pa_missing_sample_windows"
    assert small_vin is not None
    assert small_out is not None
    assert high_out is not None
    assert low_out is not None
    assert limit_metric is not None

    if small_out <= small_vin + 0.07:
        return False, f"pa_gain_missing vin={small_vin:.3f} out={small_out:.3f}"
    if not (0.78 <= high_out <= 0.89):
        return False, f"pa_high_compression_wrong={high_out:.3f}"
    if not (0.02 <= low_out <= 0.14):
        return False, f"pa_low_compression_wrong={low_out:.3f}"
    if limit_metric < 0.55:
        return False, f"pa_limit_metric_low={limit_metric:.3f}"
    return True, f"pa_compression_macro small={small_out:.3f} limits={low_out:.3f}/{high_out:.3f}"


def check_log_rssi_power_detector(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "rst", "vin", "out", "metric"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/clk/rst/vin/out/metric"

    floor = time_weighted_mean_in_window(rows, "out", 5.0e-9, 7.5e-9)
    small = time_weighted_mean_in_window(rows, "out", 12.0e-9, 22.0e-9)
    mid = time_weighted_mean_in_window(rows, "out", 30.0e-9, 40.0e-9)
    high = time_weighted_mean_in_window(rows, "out", 50.0e-9, 60.0e-9)
    high_metric = time_weighted_mean_in_window(rows, "metric", 50.0e-9, 60.0e-9)
    if None in (floor, small, mid, high, high_metric):
        return False, "rssi_missing_sample_windows"
    assert floor is not None
    assert small is not None
    assert mid is not None
    assert high is not None
    assert high_metric is not None

    if not (0.08 <= floor <= 0.16):
        return False, f"rssi_floor_wrong={floor:.3f}"
    if not (small + 0.12 <= mid <= high - 0.10):
        return False, f"rssi_not_monotonic_loglike small/mid/high={small:.3f}/{mid:.3f}/{high:.3f}"
    if (high - mid) >= (mid - small):
        return False, f"rssi_large_step_not_compressed small/mid/high={small:.3f}/{mid:.3f}/{high:.3f}"
    if high_metric < 0.55:
        return False, f"rssi_metric_low={high_metric:.3f}"
    return True, f"log_rssi_power_detector floor/small/mid/high={floor:.3f}/{small:.3f}/{mid:.3f}/{high:.3f}"


def check_limiting_amplifier_frontend(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "rst", "vin", "out", "metric"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/clk/rst/vin/out/metric"

    small_vin = mean_in_window(rows, "vin", 10.0e-9, 20.0e-9)
    small_out = mean_in_window(rows, "out", 10.0e-9, 20.0e-9)
    high_out = mean_in_window(rows, "out", 30.0e-9, 40.0e-9)
    low_out = mean_in_window(rows, "out", 50.0e-9, 60.0e-9)
    limit_metric = mean_in_window(rows, "metric", 30.0e-9, 60.0e-9)
    if None in (small_vin, small_out, high_out, low_out, limit_metric):
        return False, "limiter_missing_sample_windows"
    assert small_vin is not None
    assert small_out is not None
    assert high_out is not None
    assert low_out is not None
    assert limit_metric is not None

    if small_out <= small_vin + 0.025:
        return False, f"limiter_small_gain_missing vin={small_vin:.3f} out={small_out:.3f}"
    if high_out < 0.74 or low_out > 0.18:
        return False, f"limiter_large_signal_not_limited high={high_out:.3f} low={low_out:.3f}"
    if limit_metric < 0.55:
        return False, f"limiter_metric_low={limit_metric:.3f}"
    return True, f"limiting_amplifier_frontend small={small_out:.3f} limited={low_out:.3f}/{high_out:.3f}"


def check_agc_receiver_leveling_loop(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "rst", "vin", "out", "metric", "gain_mon", "rssi_mon"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/clk/rst/vin/out/metric/gain_mon/rssi_mon"

    def amp_mean(start: float, stop: float) -> float | None:
        val = mean_in_window(rows, "out", start, stop)
        if val is None:
            return None
        return abs(val - 0.45)

    low_amp = amp_mean(12.0e-9, 20.0e-9)
    overload_amp = amp_mean(24.0e-9, 30.0e-9)
    settled_amp = amp_mean(44.0e-9, 54.0e-9)
    settled_metric = mean_in_window(rows, "metric", 44.0e-9, 54.0e-9)
    low_gain = mean_in_window(rows, "gain_mon", 12.0e-9, 20.0e-9)
    settled_gain = mean_in_window(rows, "gain_mon", 44.0e-9, 54.0e-9)
    low_rssi = mean_in_window(rows, "rssi_mon", 12.0e-9, 20.0e-9)
    overload_rssi = mean_in_window(rows, "rssi_mon", 24.0e-9, 30.0e-9)
    settled_rssi = mean_in_window(rows, "rssi_mon", 44.0e-9, 54.0e-9)
    if None in (low_amp, overload_amp, settled_amp, settled_metric, low_gain, settled_gain, low_rssi, overload_rssi, settled_rssi):
        return False, "agc_missing_sample_windows"
    assert low_amp is not None
    assert overload_amp is not None
    assert settled_amp is not None
    assert settled_metric is not None
    assert low_gain is not None
    assert settled_gain is not None
    assert low_rssi is not None
    assert overload_rssi is not None
    assert settled_rssi is not None

    if overload_amp <= settled_amp + 0.08:
        return False, f"agc_gain_not_reduced overload={overload_amp:.3f} settled={settled_amp:.3f}"
    if not (0.10 <= settled_amp <= 0.24):
        return False, f"agc_settled_amplitude_wrong={settled_amp:.3f}"
    if low_amp < 0.08:
        return False, f"agc_low_input_not_amplified={low_amp:.3f}"
    if settled_metric < 0.45:
        return False, f"agc_lock_metric_low={settled_metric:.3f}"
    if overload_rssi <= low_rssi + 0.20 or overload_rssi <= settled_rssi + 0.15:
        return False, (
            f"agc_rssi_monitor_not_overload_sensitive low/overload/settled="
            f"{low_rssi:.3f}/{overload_rssi:.3f}/{settled_rssi:.3f}"
        )
    if settled_gain >= low_gain - 0.10:
        return False, f"agc_gain_monitor_not_reduced low={low_gain:.3f} settled={settled_gain:.3f}"
    return True, (
        f"agc_receiver_leveling_loop amp_low/overload/settled={low_amp:.3f}/{overload_amp:.3f}/{settled_amp:.3f} "
        f"gain={low_gain:.3f}->{settled_gain:.3f} rssi={low_rssi:.3f}/{overload_rssi:.3f}/{settled_rssi:.3f}"
    )


def check_iq_downconversion_chain(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "rst", "vin", "out", "metric"}
    if not rows or not required.issubset(rows[0]):
        missing = sorted(required - set(rows[0].keys())) if rows else sorted(required)
        return False, f"missing_columns={','.join(missing)}"

    i_hi = mean_in_window(rows, "out", 12.2e-9, 13.5e-9)
    q_hi = mean_in_window(rows, "metric", 14.2e-9, 15.5e-9)
    i_lo = mean_in_window(rows, "out", 16.2e-9, 17.5e-9)
    q_lo = mean_in_window(rows, "metric", 18.2e-9, 19.5e-9)
    i_cm = mean_in_window(rows, "out", 58.0e-9, 64.0e-9)
    q_cm = mean_in_window(rows, "metric", 58.0e-9, 64.0e-9)
    if None in (
        i_hi,
        q_hi,
        i_lo,
        q_lo,
        i_cm,
        q_cm,
    ):
        return False, "iq_missing_sample_windows"
    assert i_hi is not None
    assert q_hi is not None
    assert i_lo is not None
    assert q_lo is not None
    assert i_cm is not None
    assert q_cm is not None

    if i_hi < 0.70 or q_hi < 0.70:
        return False, f"iq_positive_quadrature_missing i={i_hi:.3f} q={q_hi:.3f}"
    if i_lo > 0.22 or q_lo > 0.22:
        return False, f"iq_negative_quadrature_missing i={i_lo:.3f} q={q_lo:.3f}"
    if abs(i_cm - 0.45) > 0.08 or abs(q_cm - 0.45) > 0.08:
        return False, f"iq_common_mode_hold_wrong i={i_cm:.3f} q={q_cm:.3f}"
    return True, (
        "iq_downconversion_chain "
        f"i_hi/q_hi/i_lo/q_lo={i_hi:.3f}/{q_hi:.3f}/{i_lo:.3f}/{q_lo:.3f} "
        f"common_mode={i_cm:.3f}/{q_cm:.3f}"
    )


def check_programmable_stimulus_sequencer(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "rst", "mode", "gate", "out", "metric"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/clk/rst/mode/gate/out/metric"

    def window(start: float, stop: float) -> list[dict[str, float]]:
        return [r for r in rows if start <= r["time"] <= stop and r["rst"] <= 0.45]

    ramp_rows = window(6.0e-9, 24.0e-9)
    sine_rows = window(30.0e-9, 58.0e-9)
    burst_rows = [r for r in window(66.0e-9, 88.0e-9) if r["gate"] > 0.45]
    gate_low_rows = [r for r in window(76.0e-9, 79.5e-9) if r["gate"] <= 0.45]
    if min(len(ramp_rows), len(sine_rows), len(burst_rows)) < 6 or len(gate_low_rows) < 3:
        return False, (
            "sequencer_missing_windows "
            f"ramp={len(ramp_rows)} sine={len(sine_rows)} burst={len(burst_rows)} gate_low={len(gate_low_rows)}"
        )

    ramp_drops = sum(
        1 for prev, cur in zip(ramp_rows, ramp_rows[1:]) if cur["out"] < prev["out"] - 0.02
    )
    ramp_delta = ramp_rows[-1]["out"] - ramp_rows[0]["out"]
    if ramp_drops or ramp_delta < 0.16 or not (0.16 <= ramp_rows[0]["out"] <= 0.30):
        return False, (
            "sequencer_ramp_not_monotonic "
            f"drops={ramp_drops} delta={ramp_delta:.3f} start={ramp_rows[0]['out']:.3f}"
        )

    sine_vals = [r["out"] for r in sine_rows]
    sine_min = min(sine_vals)
    sine_max = max(sine_vals)
    sine_mean = sum(sine_vals) / len(sine_vals)
    crossing_times: list[float] = []
    for prev, cur in zip(sine_rows, sine_rows[1:]):
        prev_v = prev["out"] - 0.45
        cur_v = cur["out"] - 0.45
        if prev_v == 0.0:
            crossing_times.append(prev["time"])
        elif prev_v * cur_v < 0.0:
            frac = abs(prev_v) / (abs(prev_v) + abs(cur_v))
            crossing_times.append(prev["time"] + frac * (cur["time"] - prev["time"]))
    center_crossings = len(crossing_times)
    if sine_min > 0.34 or sine_max < 0.56 or abs(sine_mean - 0.45) > 0.05 or center_crossings < 4:
        return False, (
            "sequencer_chirp_segment_wrong "
            f"min={sine_min:.3f} max={sine_max:.3f} mean={sine_mean:.3f} crossings={center_crossings}"
        )
    half_periods = [cur - prev for prev, cur in zip(crossing_times, crossing_times[1:])]
    if len(half_periods) < 3:
        return False, f"sequencer_chirp_missing_periods={len(half_periods)}"
    early_half_period = sum(half_periods[:2]) / min(2, len(half_periods[:2]))
    late_half_period = sum(half_periods[-2:]) / min(2, len(half_periods[-2:]))
    if late_half_period >= early_half_period * 0.90:
        return False, (
            "sequencer_chirp_frequency_not_increasing "
            f"early_half_period={early_half_period:.3e} late_half_period={late_half_period:.3e}"
        )

    switch_1_pre = sample_signal_at(rows, "out", 25.8e-9)
    switch_1_post = sample_signal_at(rows, "out", 26.3e-9)
    switch_2_pre = sample_signal_at(rows, "out", 61.8e-9)
    switch_2_post = sample_signal_at(rows, "out", 62.3e-9)
    if None in (switch_1_pre, switch_1_post, switch_2_pre, switch_2_post):
        return False, "sequencer_missing_switch_samples"
    assert switch_1_pre is not None
    assert switch_1_post is not None
    assert switch_2_pre is not None
    assert switch_2_post is not None
    switch_1_delta = abs(switch_1_post - switch_1_pre)
    switch_2_delta = abs(switch_2_post - switch_2_pre)
    if switch_1_delta > 0.12 or switch_2_delta > 0.12:
        return False, f"sequencer_mode_switch_discontinuity={switch_1_delta:.3f}/{switch_2_delta:.3f}"

    burst_vals = [r["out"] for r in burst_rows]
    burst_low = min(burst_vals)
    burst_high = max(burst_vals)
    burst_transitions = sum(
        1
        for prev, cur in zip(burst_vals, burst_vals[1:])
        if (prev <= 0.45 < cur) or (prev >= 0.45 > cur)
    )
    gate_low_mean = sum(r["out"] for r in gate_low_rows) / len(gate_low_rows)
    if burst_low > 0.36 or burst_high < 0.54 or burst_transitions < 2 or abs(gate_low_mean - 0.45) > 0.08:
        return False, (
            "sequencer_burst_schedule_wrong "
            f"low={burst_low:.3f} high={burst_high:.3f} transitions={burst_transitions} "
            f"gate_low_mean={gate_low_mean:.3f}"
        )

    ramp_metric = mean_in_window(rows, "metric", 8.0e-9, 22.0e-9)
    sine_metric = mean_in_window(rows, "metric", 32.0e-9, 56.0e-9)
    burst_metric = mean_in_window(rows, "metric", 67.0e-9, 75.0e-9)
    idle_metric = mean_in_window(rows, "metric", 76.5e-9, 79.0e-9)
    if None in (ramp_metric, sine_metric, burst_metric, idle_metric):
        return False, "sequencer_missing_metric_windows"
    assert ramp_metric is not None
    assert sine_metric is not None
    assert burst_metric is not None
    assert idle_metric is not None
    if not (0.12 <= ramp_metric <= 0.30 and 0.42 <= sine_metric <= 0.58 and burst_metric >= 0.70):
        return False, (
            "sequencer_metric_does_not_mark_modes "
            f"ramp={ramp_metric:.3f} sine={sine_metric:.3f} burst={burst_metric:.3f}"
        )
    if idle_metric < 0.55 or idle_metric > burst_metric - 0.05:
        return False, f"sequencer_idle_metric_wrong idle={idle_metric:.3f} burst={burst_metric:.3f}"

    return True, (
        "programmable_stimulus_sequencer "
        f"ramp_delta={ramp_delta:.3f} sine={sine_min:.3f}/{sine_max:.3f} "
        f"chirp_half_period={early_half_period:.3e}->{late_half_period:.3e} "
        f"switch={switch_1_delta:.3f}/{switch_2_delta:.3f} "
        f"burst={burst_low:.3f}/{burst_high:.3f} transitions={burst_transitions}"
    )


def check_release_event_pulse_stretcher(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "trig", "rst", "pulse"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/trig/rst/pulse"
    vth = 0.45
    trig_edges = rising_edges([r["trig"] for r in rows], [r["time"] for r in rows], threshold=vth)
    if len(trig_edges) < 5:
        return False, f"trig_edges={len(trig_edges)}"
    expected_samples = [
        (1.8e-9, True, "first_trigger_high"),
        (4.4e-9, True, "burst_middle_high"),
        (6.4e-9, True, "retrigger_extended_high"),
        (8.4e-9, False, "burst_final_low"),
        (17.2e-9, True, "single_trigger_high"),
        (19.4e-9, True, "second_burst_middle_high"),
        (21.4e-9, True, "second_retrigger_extended_high"),
        (23.4e-9, False, "second_burst_final_low"),
        (24.6e-9, True, "pre_reset_high"),
        (26.0e-9, False, "reset_forces_low"),
    ]
    failures: list[str] = []
    notes: list[str] = []
    for sample_t, should_be_high, label in expected_samples:
        value = sample_signal_at(rows, "pulse", sample_t)
        if value is None:
            failures.append(f"{label}=missing")
            continue
        is_high = value > vth
        notes.append(f"{label}:{value:.3f}")
        if is_high != should_be_high:
            failures.append(f"{label}={value:.3f}")
    if failures:
        return False, " ".join(failures) + " " + " ".join(notes)
    return True, f"trig_edges={len(trig_edges)} " + " ".join(notes)


def check_release_dac_mismatch_unit_weighting(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "b0", "b1", "b2", "b3", "out"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/b0/b1/b2/b3/out"
    weights = [1.00, 2.02, 3.96, 8.08]
    denom = sum(weights)
    sample_times = [7e-9, 15e-9, 25e-9, 35e-9]
    mismatches = 0
    details: list[str] = []
    for t in sample_times:
        row = min(rows, key=lambda r: abs(r["time"] - t))
        code_sum = sum(weights[idx] for idx, bit in enumerate(("b0", "b1", "b2", "b3")) if row[bit] > 0.45)
        expected = 0.9 * code_sum / denom
        actual = row["out"]
        delta = abs(actual - expected)
        details.append(f"{t * 1e9:.0f}ns:{actual:.4f}/{expected:.4f}")
        if delta > 0.0015:
            mismatches += 1
    if mismatches:
        return False, f"dac_weight_mismatches={mismatches} {' '.join(details)}"
    return True, f"dac_weight_samples {' '.join(details)}"


def check_release_element_shuffler(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "out0", "out1", "out2", "out3"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/out0/out1/out2/out3"

    signals = ["out0", "out1", "out2", "out3"]
    sample_times_ns = [20.0, 40.0, 60.0, 80.0, 100.0, 120.0]
    expected = [2, 0, 3, 1, 2, 0]
    observed: list[int | None] = []
    failures: list[str] = []
    for sample_t_ns, expected_idx in zip(sample_times_ns, expected):
        values = [sample_signal_at(rows, signal, sample_t_ns * 1e-9) for signal in signals]
        if any(value is None for value in values):
            failures.append(f"missing_sample_at={sample_t_ns:g}ns")
            observed.append(None)
            continue
        active = [idx for idx, value in enumerate(values) if value is not None and value > 0.45]
        observed.append(active[0] if len(active) == 1 else None)
        if active != [expected_idx]:
            failures.append(f"{sample_t_ns:g}ns_active={active}_expected={expected_idx}")

    observed_text = ",".join("-" if item is None else str(item) for item in observed)
    expected_text = ",".join(str(item) for item in expected)
    if failures:
        return False, f"active_sequence={observed_text} expected={expected_text} failures={' '.join(failures)}"
    return True, f"active_sequence={observed_text} expected={expected_text}"


def check_v3_element_shuffler(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "rst_n", "out0", "out1", "out2", "out3"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/clk/rst_n/out0/out1/out2/out3"

    signals = ["out0", "out1", "out2", "out3"]
    sample_times_ns = [20.0, 40.0, 60.0, 80.0, 100.0, 120.0, 160.0, 180.0, 200.0, 220.0]
    expected = [2, 0, 3, 1, 2, 0, 2, 0, 3, 1]
    observed: list[int | None] = []
    failures: list[str] = []
    reset_low_probe_ns = 138.0
    reset_low_value = sample_signal_at(rows, "rst_n", reset_low_probe_ns * 1e-9)
    if reset_low_value is None:
        failures.append(f"missing_rst_n_probe_at={reset_low_probe_ns:g}ns")
    elif reset_low_value > 0.45:
        failures.append(f"rst_n_not_low_at={reset_low_probe_ns:g}ns")

    for sample_t_ns, expected_idx in zip(sample_times_ns, expected):
        rst_value = sample_signal_at(rows, "rst_n", sample_t_ns * 1e-9)
        if rst_value is None:
            failures.append(f"missing_rst_n_at={sample_t_ns:g}ns")
        elif rst_value <= 0.45:
            failures.append(f"rst_n_not_released_at={sample_t_ns:g}ns")
        values = [sample_signal_at(rows, signal, sample_t_ns * 1e-9) for signal in signals]
        if any(value is None for value in values):
            failures.append(f"missing_sample_at={sample_t_ns:g}ns")
            observed.append(None)
            continue
        active = [idx for idx, value in enumerate(values) if value is not None and value > 0.45]
        observed.append(active[0] if len(active) == 1 else None)
        if active != [expected_idx]:
            failures.append(f"{sample_t_ns:g}ns_active={active}_expected={expected_idx}")

    observed_text = ",".join("-" if item is None else str(item) for item in observed)
    expected_text = ",".join(str(item) for item in expected)
    if failures:
        return False, f"active_sequence={observed_text} expected={expected_text} failures={' '.join(failures)}"
    return True, f"active_sequence={observed_text} expected={expected_text} reset_low_at={reset_low_probe_ns:g}ns"


def check_v3_debounce_latch(rows: list[dict[str, float]]) -> tuple[bool, str]:
    """V3 debounce latch: reject glitches, reset-arm leakage, and reset-cancel leakage."""
    required = {"time", "out"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/out"
    samples = {
        "reset_arm_rejected_20ns": (20.0, False),
        "short_glitch_low_34ns": (34.0, False),
        "short_glitch_low_40ns": (40.0, False),
        "reset_cancel_low_67ns": (67.0, False),
        "post_cancel_low_72ns": (72.0, False),
        "pre_qualify_low_82ns": (82.0, False),
        "qualified_high_100ns": (100.0, True),
        "qualified_high_130ns": (130.0, True),
    }
    failures: list[str] = []
    notes: list[str] = []
    for label, (time_ns, should_be_high) in samples.items():
        value = sample_signal_at(rows, "out", time_ns * 1e-9)
        if value is None:
            failures.append(f"{label}=missing")
            continue
        is_high = value > 0.45
        notes.append(f"{label}:{value:.3f}")
        if is_high != should_be_high:
            failures.append(f"{label}:{value:.3f}")
    if failures:
        return False, " ".join(failures) + " " + " ".join(notes)
    return True, " ".join(notes)


def check_v3_trim_calibration_controller(rows: list[dict[str, float]]) -> tuple[bool, str]:
    """V3 trim calibration: verify reset, 60 mV step size, direction, recovery, and clamps."""
    required = {"time", "trim"}
    if not rows or not required.issubset(rows[0]):
        return False, "missing time/trim"
    expected_samples = [
        (20.0, 0.45, "reset_20ns"),
        (40.0, 0.45, "hold_before_active_40ns"),
        (80.0, 0.51, "first_increment_80ns"),
        (100.0, 0.57, "second_increment_100ns"),
        (140.0, 0.39, "decrement_140ns"),
        (180.0, 0.15, "lower_clamp_path_180ns"),
        (210.0, 0.23, "late_recovery_210ns"),
    ]
    failures: list[str] = []
    notes: list[str] = []
    for time_ns, expected, label in expected_samples:
        value = sample_signal_at(rows, "trim", time_ns * 1e-9)
        if value is None:
            failures.append(f"{label}=missing")
            continue
        notes.append(f"{label}:{value:.3f}/{expected:.3f}")
        if abs(value - expected) > 0.018:
            failures.append(f"{label}:{value:.3f}!={expected:.3f}")
    trim_vals = [row["trim"] for row in rows]
    min_trim = min(trim_vals)
    max_trim = max(trim_vals)
    in_range = min_trim >= 0.04 and max_trim <= 0.86
    if not in_range:
        failures.append(f"range=({min_trim:.3f},{max_trim:.3f})")
    if failures:
        return False, " ".join(failures) + " " + " ".join(notes)
    return True, " ".join(notes) + f" range=({min_trim:.3f},{max_trim:.3f})"


CHECKS = {
    # legacy short IDs (example-level names)
    "adc_dac_ideal_4b": check_adc_dac_ideal_4b,
    "clk_burst_gen": check_clk_burst_gen,
    "clk_div_smoke": check_clk_div,
    "clk_divider": check_clk_divider,
    "comparator_smoke": check_comparator,
    "dac_binary_clk_4b": check_dac_binary_clk_4b,
    "dac_therm_16b": check_dac_therm_16b,
    "digital_basics": check_not_gate,
    "dwa_ptr_gen": check_dwa_ptr_gen,
    "gain_extraction": check_gain_extraction,
    "lfsr": check_lfsr,
    "prbs7": check_prbs7,
    "therm2bin": check_therm2bin,
    "multimod_divider": check_multimod_divider,
    "bbpd": check_bbpd,
    "bad_bus_output_loop": check_bad_bus_output_loop,
    "missing_transition_outputs": check_missing_transition_outputs,
    "noise_gen": check_noise_gen,
    "sar_adc_dac_weighted_8b": check_sar_adc_dac_weighted_8b,
    # formal task IDs (tasks/end-to-end/voltage/)
    "adpll_lock_smoke": check_adpll_lock,
    "adpll_ratio_hop_smoke": check_adpll_ratio_hop,
    "adpll_timer_smoke": check_adpll_lock,
    "above_threshold_startup_smoke": check_above_threshold_startup,
    "and_gate_smoke": check_and_gate,
    "or_gate_smoke": check_or_gate,
    "not_gate_smoke": check_not_gate,
    "dff_rst_smoke": check_dff_rst,
    "bound_step_period_guard_smoke": check_bound_step_period_guard,
    "cross_hysteresis_window_smoke": check_cross_hysteresis_window,
    "window_comparator_smoke": check_true_window_comparator,
    "cross_interval_163p333_smoke": check_cross_interval_163p333,
    "cross_sine_precision_smoke": check_cross_sine_precision,
    "differential_voltage_output_smoke": check_differential_voltage_output,
    "final_step_file_metric_smoke": check_final_step_file_metric,
    "parameter_type_override_smoke": check_parameter_type_override,
    "phase_accumulator_timer_wrap_smoke": check_phase_accumulator_timer_wrap,
    "simultaneous_event_order_smoke": check_simultaneous_event_order,
    "conversion_event_controller_flow": check_conversion_event_controller,
    "timer_absolute_grid_smoke": check_timer_absolute_grid,
    "transition_branch_target_smoke": check_transition_branch_target,
    "clk_div_smoke": check_clk_div,
    "cmp_delay_smoke": check_cmp_delay,
    "comparator_hysteresis_smoke": check_cmp_hysteresis,
    "comparator_measurement_flow_smoke": check_comparator_measurement_flow,
    "comparator_offset_search_smoke": check_comparator_offset_search,
    "cmp_strongarm_smoke": check_cmp_strongarm,
    "comparator_smoke": check_comparator,
    "cppll_freq_step_reacquire_smoke": check_cppll_freq_step_reacquire,
    "cppll_tracking_smoke": check_cppll_tracking,
    "d2b_4bit_smoke": check_d2b,
    "ramp_gen_smoke": check_ramp_gen,
    "adc_dac_ideal_4b_smoke": check_adc_dac_ideal_4b,
    "clk_burst_gen_smoke": check_clk_burst_gen,
    "dac_binary_clk_4b_smoke": check_dac_binary_clk_4b,
    "dac_therm_16b_smoke": check_dac_therm_16b,
    "digital_basics_smoke": check_not_gate,
    "dwa_ptr_gen_smoke": check_dwa_ptr_gen,
    "dwa_ptr_gen_no_overlap_smoke": check_dwa_ptr_gen_no_overlap,
    "dwa_wraparound_smoke": check_dwa_wraparound,
    "bbpd_data_edge_alignment_smoke": check_bbpd_data_edge_alignment,
    "gain_extraction_smoke": check_gain_extraction,
    "gain_estimator_smoke": check_gain_estimator,
    "lfsr_smoke": check_lfsr,
    "noise_gen_smoke": check_noise_gen,
    "sar_adc_dac_weighted_8b_smoke": check_sar_adc_dac_weighted_8b,
    "sample_hold_smoke": check_sample_hold,
    "sample_hold_droop_smoke": check_sample_hold_droop,
    "flash_adc_3b_smoke": check_flash_adc_3b,
    "flash_adc_mini_array_e2e": check_release_flash_adc_mini_array,
    "pipeline_adc_chain_e2e": check_release_pipeline_adc_chain,
    "serializer_8b_smoke": check_serializer_8b,
    "serializer_frame_alignment_smoke": check_serializer_frame_alignment,
    "serializer_frame_monitor_flow": check_serializer_frame_monitor_flow,
    "adc_code_capture_register": check_adc_code_capture_register,
    "serial_readout_deserializer": check_serial_readout_deserializer,
    "xor_pd_smoke": check_xor_pd,
    "pfd_updn_smoke": check_pfd_updn,
    "pfd_deadzone_smoke": check_pfd_deadzone,
    "pfd_small_phase_response_smoke": check_pfd_small_phase_error_response,
    "pfd_reset_race_smoke": check_pfd_reset_race,
    "gray_counter_one_bit_change_smoke": check_gray_counter_one_bit_change,
    "gray_counter_4b_smoke": check_gray_counter_4b,
    "multimod_divider_ratio_switch_smoke": check_multimod_divider_ratio_switch,
    "mux_4to1_smoke": check_mux_4to1,
    # spec-to-va task IDs
    "clk_divider":    check_clk_divider,
    "prbs7":          check_prbs7,
    "therm2bin":      check_therm2bin,
    "d2b_4bit":       check_d2b,
    "sar_logic":      check_sar_logic,
    "sar_logic_10b":  check_sar_logic,
    "pipeline_stage": check_pipeline_stage,
    "sar_12bit":      check_sar_12bit,
    "segmented_dac":  check_segmented_dac,
    "cdac_cal":       check_cdac_cal,
    "sc_integrator":  check_sc_integrator,
    "bg_cal":         check_bg_cal,
    "adpll_timer":    check_adpll_lock,
    "cppll_timer":    check_cppll_tracking,
    "multitone":      check_multitone,
    "nrz_prbs":       check_nrz_prbs,
    "mixed_domain_cdac_bug": check_mixed_domain_cdac_bug,
    "spectre_port_discipline": check_spectre_port_discipline,
    "strongarm_reset_priority_bug": check_strongarm_reset_priority_bug,
    "v3_source_clocked_sar_comparator": check_v3_source_clocked_sar_comparator,
    "v3_source_clocked_dac_restore_4b": check_v3_source_clocked_dac_restore_4b,
    "v3_source_sample_hold": check_v3_source_sample_hold,
    "v3_source_single_shot": check_v3_source_single_shot,
    "v3_source_clocked_comparator_reset_low": check_v3_source_clocked_comparator_reset_low,
    "v3_source_bipolar_dac_4b_continuous": check_v3_source_bipolar_dac_4b_continuous,
    "v3_source_clocked_dac_restore_7b": check_v3_source_clocked_dac_restore_7b,
    "v3_source_crossing_pulse_detector": check_v3_source_crossing_pulse_detector,
    "v3_source_not_gate": check_v3_source_not_gate,
    "v3_source_dff_reset": check_v3_source_dff_reset,
    "v3_source_offset_search_comparator": check_v3_source_offset_search_comparator,
    "v3_source_start_gated_offset_search": check_v3_source_start_gated_offset_search,
    "v3_source_comp_os_detect": check_v3_source_comp_os_detect,
    "v3_source_clocked_dac_4b_binary": check_v3_source_clocked_dac_4b_binary,
    "v3_source_latched_comparator_delay": check_v3_source_latched_comparator_delay,
    "v3_source_sar_weighted_sum": check_v3_source_sar_weighted_sum,
    "v3_source_two_input_and_gate": check_v3_source_two_input_and_gate,
    "v3_source_two_input_xor_gate": check_v3_source_two_input_xor_gate,
    "v3_source_analog_mux_threshold": check_v3_source_analog_mux_threshold,
    "v3_source_two_bit_counter_marker": check_v3_source_two_bit_counter_marker,
    "v3_source_max_detector_hold": check_v3_source_max_detector_hold,
    "v3_source_time_diff_detector": check_v3_source_time_diff_detector,
    "v3_source_differential_buffer": check_v3_source_differential_buffer,
    "v3_source_two_input_or_gate": check_v3_source_two_input_or_gate,
    "v3_source_sar_cdac_residue": check_v3_source_sar_cdac_residue,
    "v3_source_two_input_nand_gate": check_v3_source_two_input_nand_gate,
    "v3_source_two_input_nor_gate": check_v3_source_two_input_nor_gate,
    "v3_source_three_input_and_gate": check_v3_source_three_input_and_gate,
    "v3_source_three_input_or_gate": check_v3_source_three_input_or_gate,
    "v3_source_three_input_xor_gate": check_v3_source_three_input_xor_gate,
    "v3_source_attenuator_gain": check_v3_source_attenuator_gain,
    "v3_source_deadband_window": check_v3_source_deadband_window,
    "v3_source_differential_deadband": check_v3_source_differential_deadband,
    "v3_source_hard_voltage_clamp": check_v3_source_hard_voltage_clamp,
    "v3_source_smooth_comparator_tanh": check_v3_source_smooth_comparator_tanh,
    "v3_source_limiter_rails": check_v3_source_limiter_rails,
    "v3_source_absolute_value": check_v3_source_absolute_value,
    "v3_source_offset_gain_amplifier": check_v3_source_offset_gain_amplifier,
    "v3_source_safe_voltage_divider": check_v3_source_safe_voltage_divider,
    "v3_source_polynomial_differential_vcvs": check_v3_source_polynomial_differential_vcvs,
    "v3_source_differential_gain_driver": check_v3_source_differential_gain_driver,
    "v3_source_limiting_differential_amplifier": check_v3_source_limiting_differential_amplifier,
    "v3_source_analog_multiplier": check_v3_source_analog_multiplier,
    "v3_source_three_way_threshold_mux": check_v3_source_three_way_threshold_mux,
    "v3_source_differential_amplifier_core": check_v3_source_differential_amplifier_core,
    "v3_source_logarithmic_amplifier": check_v3_source_logarithmic_amplifier,
    "v3_source_soft_voltage_clamp": check_v3_source_soft_voltage_clamp,
    "v3_source_variable_gain_differential_amplifier": check_v3_source_variable_gain_differential_amplifier,
    "v3_source_voltage_controlled_gain_amplifier": check_v3_source_voltage_controlled_gain_amplifier,
    "v3_source_ideal_differential_opamp": check_v3_source_ideal_differential_opamp,
    "v3_source_half_adder_logic": check_v3_source_half_adder_logic,
    "v3_source_full_adder_logic": check_v3_source_full_adder_logic,
    "v3_source_half_subtractor_logic": check_v3_source_half_subtractor_logic,
    "v3_source_full_subtractor_logic": check_v3_source_full_subtractor_logic,
    "v3_source_rs_latch_voltage": check_v3_source_rs_latch_voltage,
    "v3_source_ideal_adc_4bit_quantizer": check_v3_source_ideal_adc_4bit_quantizer,
    "v3_source_ideal_dac_4bit_differential": check_v3_source_ideal_dac_4bit_differential,
    "v3_source_two_period_sample_delay": check_v3_source_two_period_sample_delay,
    "v3_source_clocked_four_input_mux": check_v3_source_clocked_four_input_mux,
    "v3_source_divide_by_eight_clock": check_v3_source_divide_by_eight_clock,
    "v3_source_flash_thermometer_centered_sum": check_v3_source_flash_thermometer_centered_sum,
    "v3_source_weighted_sar_decoder_9b": check_v3_source_weighted_sar_decoder_9b,
    "v3_source_control_word_encoder_7b": check_v3_source_control_word_encoder_7b,
    "v3_source_four_channel_edge_sampler": check_v3_source_four_channel_edge_sampler,
    "v3_source_dual_modulus_divider_16_17": check_v3_source_dual_modulus_divider_16_17,
    "v3_source_sar_5bit_serial_decoder": check_v3_source_sar_5bit_serial_decoder,
    "v3_source_cyclic_decoder_12bit": check_v3_source_cyclic_decoder_12bit,
    "v3_source_flash_8level_sum_delay": check_v3_source_flash_8level_sum_delay,
    "v3_source_flash_sum8_fraction": check_v3_source_flash_sum8_fraction,
    "v3_source_two_channel_sample_demux": check_v3_source_two_channel_sample_demux,
    "v3_source_differential_dac_calc_6b": check_v3_source_differential_dac_calc_6b,
    "v3_source_flash_adc_threshold_taps": check_v3_source_flash_adc_threshold_taps,
    "v3_source_divide_by_two_toggle": check_v3_source_divide_by_two_toggle,
    "v3_source_dac_5v_weighted_7b": check_v3_source_dac_5v_weighted_7b,
    "v3_source_folded_flash_dac_4b": check_v3_source_folded_flash_dac_4b,
    "v3_source_ref_flash_8level_decoder": check_v3_source_ref_flash_8level_decoder,
    "v3_source_ref_flash_15level_decoder": check_v3_source_ref_flash_15level_decoder,
    "v3_source_divide_by_8_9_switch": check_v3_source_divide_by_8_9_switch,
    "v3_source_dac_restore_10bit_offset": check_v3_source_dac_restore_10bit_offset,
    "v3_source_dac_8bit_ideal_scalar": check_v3_source_dac_8bit_ideal_scalar,
    "v3_source_flash_data_align_pipeline": check_v3_source_flash_data_align_pipeline,
    "v3_source_cyclic_decoder_10b": check_v3_source_cyclic_decoder_10b,
    "v3_source_ideal_adc_out_7bits": check_v3_source_ideal_adc_out_7bits,
    "v3_source_va_lx_adc_ideal_4b": check_v3_source_va_lx_adc_ideal_4b,
    "v3_source_va_lx_dac_ideal_4b": check_v3_source_va_lx_dac_ideal_4b,
    "v3_source_l1_dac_4b_bipolar": check_v3_source_l1_dac_4b_bipolar,
    "v3_source_l2_cdac_4b_residue": check_v3_source_l2_cdac_4b_residue,
    "v3_source_ideal_clkmux_8channel": check_v3_source_ideal_clkmux_8channel,
    "v3_source_dac_ideal_4b_offset": check_v3_source_dac_ideal_4b_offset,
    "v3_source_linear_pfd_gain": check_v3_source_linear_pfd_gain,
    "v3_source_l2_cmp_ideal_clocked": check_v3_source_l2_cmp_ideal_clocked,
    "v3_source_comparator_offset_driver": check_v3_source_comparator_offset_driver,
    "v3_source_pipe_2lane_edge_align": check_v3_source_pipe_2lane_edge_align,
    "v3_source_dac_serial_accumulator": check_v3_source_dac_serial_accumulator,
    "v3_source_sar_sum_weighted_11b": check_v3_source_sar_sum_weighted_11b,
    "v3_source_iterative_isar_dac": check_v3_source_iterative_isar_dac,
    "v3_source_offset_bisection_driver": check_v3_source_offset_bisection_driver,
    "v3_source_weighted_decoder_7b5": check_v3_source_weighted_decoder_7b5,
    "v3_source_toggle_flip_flop": check_v3_source_toggle_flip_flop,
    "v3_source_sync_8b_dffs_v2": check_v3_source_sync_8b_dffs_v2,
    "v3_source_onehot_progress_encoder": check_v3_source_onehot_progress_encoder,
    "v3_source_tdc_ideal_edge_delta": check_v3_source_tdc_ideal_edge_delta,
    "v3_source_foreground_cload_calibrator": check_v3_source_foreground_cload_calibrator,
    "v3_source_pipe15_data_align": check_v3_source_pipe15_data_align,
    "v3_source_clocked_mux4_sampler": check_v3_source_clocked_mux4_sampler,
    "v3_source_dac7_code_generator": check_v3_source_dac7_code_generator,
    "v3_source_foreground_rdac_calibrator": check_v3_source_foreground_rdac_calibrator,
    "v3_source_offset_rdac_search_flow": check_v3_source_offset_rdac_search_flow,
    "v3_source_spi_shift_mux": check_v3_source_spi_shift_mux,
    "v3_source_dff_set_reset_hold": check_v3_source_dff_set_reset_hold,
    "v3_source_sarfend_logic_4b": check_v3_source_sarfend_logic_4b,
    "v3_source_adc_sample_clock_sequencer": check_v3_source_adc_sample_clock_sequencer,
    "v3_source_pipeline_counter_onehot": check_v3_source_pipeline_counter_onehot,
    "v3_source_cdac_bidirect_residue": check_v3_source_cdac_bidirect_residue,
    "v3_source_pfd_reset_pulse": check_v3_source_pfd_reset_pulse,
    "v3_source_trim_ctrl_4bit": check_v3_source_trim_ctrl_4bit,
    "v3_source_linearity_rdac_offset_sweep": check_v3_source_linearity_rdac_offset_sweep,
    "v3_source_sar_das_logic_6b": check_v3_source_sar_das_logic_6b,
    "v3_source_sar_logic_4b_self_timed": check_v3_source_sar_logic_4b_self_timed,
    "v3_source_pfd_tdomain_reset_window": check_v3_source_pfd_tdomain_reset_window,
    "v3_source_pipe_adc_gain_control_loop": check_v3_source_pipe_adc_gain_control_loop,
    "v3_source_clock_sample_1600n_sequencer": check_v3_source_clock_sample_1600n_sequencer,
    "v3_source_l2_sar_logic_4b": check_v3_source_l2_sar_logic_4b,
    "v3_source_phase_detector_chopper": check_v3_source_phase_detector_chopper,
    "v3_source_single_adc_7b_weighted": check_v3_source_single_adc_7b_weighted,
    "v3_source_qtz_differential_2level": check_v3_source_qtz_differential_2level,
    "v3_source_l2_7b_dac_ready": check_v3_source_l2_7b_dac_ready,
    "v3_source_l2_cdac_4b_switch": check_v3_source_l2_cdac_4b_switch,
    "v3_source_cdac_monodown_7b": check_v3_source_cdac_monodown_7b,
    "v3_source_cdac_6b_stage1_up": check_v3_source_cdac_6b_stage1_up,
    "v3_source_adc_zoom_timing_sequencer": check_v3_source_adc_zoom_timing_sequencer,
    "vbm1_background_calibration_accumulator_dut": check_vbm1_background_calibration_accumulator,
    "vbm1_background_calibration_accumulator_tb": check_vbm1_background_calibration_accumulator,
    "vbm1_background_calibration_accumulator_bugfix": check_vbm1_background_calibration_accumulator,
    "vbm1_background_calibration_accumulator_e2e": check_vbm1_background_calibration_accumulator,
    "vbm1_barrel_pointer_window_dut": check_vbm1_barrel_pointer_window,
    "vbm1_barrel_pointer_window_tb": check_vbm1_barrel_pointer_window,
    "vbm1_barrel_pointer_window_bugfix": check_vbm1_barrel_pointer_window,
    "vbm1_barrel_pointer_window_e2e": check_vbm1_barrel_pointer_window,
    "vbm1_cdac_calibration_dut": check_vbm1_cdac_calibration,
    "vbm1_cdac_calibration_tb": check_vbm1_cdac_calibration,
    "vbm1_cdac_calibration_bugfix": check_vbm1_cdac_calibration,
    "vbm1_cdac_calibration_e2e": check_vbm1_cdac_calibration,
    "vbm1_debounce_latch_dut": check_vbm1_debounce_latch,
    "vbm1_debounce_latch_tb": check_vbm1_debounce_latch,
    "vbm1_debounce_latch_bugfix": check_vbm1_debounce_latch,
    "vbm1_debounce_latch_e2e": check_vbm1_debounce_latch,
    "vbm1_edge_detector_dut": check_vbm1_edge_detector,
    "vbm1_edge_detector_tb": check_vbm1_edge_detector,
    "vbm1_edge_detector_bugfix": check_vbm1_edge_detector,
    "vbm1_edge_detector_e2e": check_vbm1_edge_detector,
    "vbm1_element_shuffler_dut": check_vbm1_element_shuffler,
    "vbm1_element_shuffler_tb": check_vbm1_element_shuffler,
    "vbm1_element_shuffler_bugfix": check_vbm1_element_shuffler,
    "vbm1_element_shuffler_e2e": check_vbm1_element_shuffler,
    "vbm1_file_metric_writer_dut": check_vbm1_file_metric_writer,
    "vbm1_file_metric_writer_tb": check_vbm1_file_metric_writer,
    "vbm1_file_metric_writer_e2e": check_vbm1_file_metric_writer,
    "vbm1_first_order_lowpass_dut": check_vbm1_first_order_lowpass,
    "vbm1_first_order_lowpass_tb": check_vbm1_first_order_lowpass,
    "vbm1_first_order_lowpass_bugfix": check_vbm1_first_order_lowpass,
    "vbm1_first_order_lowpass_e2e": check_vbm1_first_order_lowpass,
    "vbm1_gain_trim_controller_dut": check_vbm1_gain_trim_controller,
    "vbm1_gain_trim_controller_tb": check_vbm1_gain_trim_controller,
    "vbm1_gain_trim_controller_bugfix": check_vbm1_gain_trim_controller,
    "vbm1_gain_trim_controller_e2e": check_vbm1_gain_trim_controller,
    "vbm1_leaky_hold_dut": check_vbm1_leaky_hold,
    "vbm1_leaky_hold_tb": check_vbm1_leaky_hold,
    "vbm1_leaky_hold_bugfix": check_vbm1_leaky_hold,
    "vbm1_leaky_hold_e2e": check_vbm1_leaky_hold,
    "vbm1_lock_detector_dut": check_vbm1_lock_detector,
    "vbm1_lock_detector_tb": check_vbm1_lock_detector,
    "vbm1_lock_detector_bugfix": check_vbm1_lock_detector,
    "vbm1_lock_detector_e2e": check_vbm1_lock_detector,
    "vbm1_offset_calibration_fsm_dut": check_vbm1_offset_calibration_fsm,
    "vbm1_offset_calibration_fsm_tb": check_vbm1_offset_calibration_fsm,
    "vbm1_offset_calibration_fsm_bugfix": check_vbm1_offset_calibration_fsm,
    "vbm1_offset_calibration_fsm_e2e": check_vbm1_offset_calibration_fsm,
    "vbm1_offset_comparator_dut": check_vbm1_offset_comparator,
    "vbm1_offset_comparator_tb": check_vbm1_offset_comparator,
    "vbm1_offset_comparator_bugfix": check_vbm1_offset_comparator,
    "vbm1_offset_comparator_e2e": check_vbm1_offset_comparator,
    "vbm1_one_shot_timer_dut": check_vbm1_one_shot_timer,
    "vbm1_one_shot_timer_tb": check_vbm1_one_shot_timer,
    "vbm1_one_shot_timer_bugfix": check_vbm1_one_shot_timer,
    "vbm1_one_shot_timer_e2e": check_vbm1_one_shot_timer,
    "vbm1_peak_detector_dut": check_vbm1_peak_detector,
    "vbm1_peak_detector_tb": check_vbm1_peak_detector,
    "vbm1_peak_detector_bugfix": check_vbm1_peak_detector,
    "vbm1_peak_detector_e2e": check_vbm1_peak_detector,
    "vbm1_precision_rectifier_dut": check_vbm1_precision_rectifier,
    "vbm1_precision_rectifier_tb": check_vbm1_precision_rectifier,
    "vbm1_precision_rectifier_bugfix": check_vbm1_precision_rectifier,
    "vbm1_precision_rectifier_e2e": check_vbm1_precision_rectifier,
    "vbm1_resettable_counter_divider_dut": check_vbm1_resettable_counter_divider,
    "vbm1_resettable_counter_divider_tb": check_vbm1_resettable_counter_divider,
    "vbm1_resettable_counter_divider_e2e": check_vbm1_resettable_counter_divider,
    "vbm1_resettable_integrator_dut": check_vbm1_resettable_integrator,
    "vbm1_resettable_integrator_tb": check_vbm1_resettable_integrator,
    "vbm1_resettable_integrator_bugfix": check_vbm1_resettable_integrator,
    "vbm1_resettable_integrator_e2e": check_vbm1_resettable_integrator,
    "vbm1_rotating_element_selector_dut": check_vbm1_rotating_element_selector,
    "vbm1_rotating_element_selector_tb": check_vbm1_rotating_element_selector,
    "vbm1_rotating_element_selector_bugfix": check_vbm1_rotating_element_selector,
    "vbm1_rotating_element_selector_e2e": check_vbm1_rotating_element_selector,
    "vbm1_sar_logic_4b_dut": check_vbm1_sar_logic_4b,
    "vbm1_sar_logic_4b_tb": check_vbm1_sar_logic_4b,
    "vbm1_sar_logic_4b_bugfix": check_vbm1_sar_logic_4b,
    "vbm1_sar_logic_4b_e2e": check_vbm1_sar_logic_4b,
    "vbm1_pfd_reset_race_dut": check_pfd_reset_race,
    "vbm1_pfd_reset_race_tb": check_pfd_reset_race,
    "vbm1_pfd_reset_race_bugfix": check_pfd_reset_race,
    "vbm1_pfd_reset_race_e2e": check_pfd_reset_race,
    "vbm1_pfd_small_phase_error_response_dut": check_pfd_small_phase_error_response,
    "vbm1_segmented_dac_dut": check_vbm1_segmented_dac,
    "vbm1_segmented_dac_tb": check_vbm1_segmented_dac,
    "vbm1_segmented_dac_bugfix": check_vbm1_segmented_dac,
    "vbm1_segmented_dac_e2e": check_vbm1_segmented_dac,
    "vbm1_settling_time_measurement_tb_dut": check_vbm1_settling_time_measurement_tb,
    "vbm1_settling_time_measurement_tb_tb": check_vbm1_settling_time_measurement_tb,
    "vbm1_settling_time_measurement_tb_e2e": check_vbm1_settling_time_measurement_tb,
    "vbm1_strongarm_comparator_behavior_dut": check_vbm1_strongarm_comparator_behavior,
    "vbm1_strongarm_comparator_behavior_tb": check_vbm1_strongarm_comparator_behavior,
    "vbm1_strongarm_comparator_behavior_e2e": check_vbm1_strongarm_comparator_behavior,
    "vbm1_strongarm_comparator_behavior_bugfix": check_strongarm_reset_priority_bug,
    "vbm1_thermometer_dac_dut": check_vbm1_thermometer_dac,
    "vbm1_thermometer_dac_tb": check_vbm1_thermometer_dac,
    "vbm1_thermometer_dac_bugfix": check_vbm1_thermometer_dac,
    "vbm1_thermometer_dac_e2e": check_vbm1_thermometer_dac,
    "vbm1_simple_binary_voltage_dac_4b_dut": check_simple_binary_dac_4b,
    "vbm1_simple_binary_voltage_dac_4b_tb": check_simple_binary_dac_4b,
    "vbm1_simple_binary_voltage_dac_4b_bugfix": check_simple_binary_dac_4b,
    "vbm1_simple_binary_voltage_dac_4b_e2e": check_simple_binary_dac_4b,
    "vbm1_thermometer_dac_15seg_dut": check_vbm1_thermometer_dac_15seg,
    "vbm1_thermometer_dac_15seg_tb": check_vbm1_thermometer_dac_15seg,
    "vbm1_thermometer_dac_15seg_bugfix": check_vbm1_thermometer_dac_15seg,
    "vbm1_thermometer_dac_15seg_e2e": check_vbm1_thermometer_dac_15seg,
    "vbm1_thermometer_decoder_guarded_dut": check_vbm1_thermometer_decoder_guarded,
    "vbm1_thermometer_decoder_guarded_tb": check_vbm1_thermometer_decoder_guarded,
    "vbm1_thermometer_decoder_guarded_bugfix": check_vbm1_thermometer_decoder_guarded,
    "vbm1_thermometer_decoder_guarded_e2e": check_vbm1_thermometer_decoder_guarded,
    "vbm1_track_hold_aperture_dut": check_vbm1_track_hold_aperture,
    "vbm1_track_hold_aperture_tb": check_vbm1_track_hold_aperture,
    "vbm1_track_hold_aperture_bugfix": check_vbm1_track_hold_aperture,
    "vbm1_track_hold_aperture_e2e": check_vbm1_track_hold_aperture,
    "vbm1_vco_phase_integrator_dut": check_vbm1_vco_phase_integrator,
    "vbm1_vco_phase_integrator_tb": check_vbm1_vco_phase_integrator,
    "vbm1_vco_phase_integrator_e2e": check_vbm1_vco_phase_integrator,
    "vbm1_slew_rate_limiter_dut": check_vbm1_slew_rate_limiter,
    "vbm1_slew_rate_limiter_tb": check_vbm1_slew_rate_limiter,
    "vbm1_slew_rate_limiter_bugfix": check_vbm1_slew_rate_limiter,
    "vbm1_slew_rate_limiter_e2e": check_vbm1_slew_rate_limiter,
    "vbm1_voltage_clamp_dut": check_vbm1_voltage_clamp,
    "vbm1_voltage_clamp_tb": check_vbm1_voltage_clamp,
    "vbm1_voltage_clamp_bugfix": check_vbm1_voltage_clamp,
    "vbm1_voltage_clamp_e2e": check_vbm1_voltage_clamp,
    "wrong_edge_sample_hold_bug": check_sample_hold,
    "inverted_comparator_logic_bug": check_inverted_comparator_logic_bug,
    "swapped_pfd_outputs_bug": check_pfd_updn,
}


RELEASE_CHECK_ALIASES = {
    # Release-v1 designed tasks whose public task IDs differ from legacy/main120 checker IDs.
    # The first group reuses stronger existing waveform checkers.
    "vbr1_l1_burst_clock_source": check_clk_burst_gen,
    "vbr1_l1_clocked_adc_quantizer": check_flash_adc_3b,
    "vbr1_l1_digital_phase_accumulator_with_modulo_wrap": check_phase_accumulator_timer_wrap,
    "vbr1_l1_dither_or_noise_like_deterministic_source": check_noise_gen,
    "vbr1_l1_dwa_dem_encoder": check_dwa_dem_encoder_release,
    "vbr1_l1_hysteresis_comparator": check_cmp_hysteresis,
    "vbr1_l1_offset_comparator": check_release_offset_comparator,
    "vbr1_l1_binary_weighted_voltage_dac": check_simple_binary_dac_4b,
    "vbr1_l1_pipeline_adc_stage": check_pipeline_stage,
    "vbr1_l2_pipeline_adc_chain": check_release_pipeline_adc_chain,
    "vbr1_l1_propagation_delay_comparator": check_cmp_delay,
    "vbr1_l1_ramp_or_step_source": check_bound_step_period_guard,
    "vbr1_l1_aperture_delay_track_and_hold": check_vbm1_track_hold_aperture,
    "vbr1_l1_clocked_sample_and_hold": check_sample_hold,
    "vbr1_l1_sample_and_hold_with_droop_leakage": check_release_vin_sampled_droop_hold,
    "vbr1_l1_acquisition_limited_sample_and_hold": check_acquisition_limited_sample_hold,
    "vbr1_l1_first_order_lowpass": check_vbm1_first_order_lowpass,
    "vbr1_l1_resettable_integrator": check_vbm1_resettable_integrator,
    "vbr1_l1_slew_rate_limiter": check_vbm1_slew_rate_limiter,
    "vbr1_l1_strongarm_style_latch_comparator": check_release_strongarm_latch_comparator,
    "vbr1_l1_threshold_comparator": check_release_threshold_comparator,
    "vbr1_l1_unit_element_thermometer_dac": check_vbm1_thermometer_dac_15seg,
    "vbr1_l2_weighted_sar_adc_dac_loop": check_sar_adc_dac_weighted_8b,
    "vbr1_l1_vco_phase_integrator": check_vbm1_vco_phase_integrator,
    "vbr1_l1_window_comparator_detector": check_true_window_comparator,
    # Release-generic checks are intentionally conservative behavior guards for
    # newly designed source tasks. They prove reset/range/response properties,
    # but should be replaced by stronger per-function checkers before paper claims.
    "vbr1_l1_calibration_deadband_controller": check_release_deadband_calibration,
    "vbr1_l1_charge_pump_abstraction": check_release_charge_pump,
    "vbr1_l1_element_shuffler": check_release_element_shuffler,
    "vbr1_l1_loop_filter_abstraction": check_release_loop_filter,
    "vbr1_l1_successive_approximation_calibration_search_fsm": check_release_sar_calibration_fsm,
    "vbr1_l2_complete_calibration_loop": check_release_complete_calibration_loop,
    "vbr1_l1_higher_order_filter": check_release_two_pole_filter,
    "vbr1_l1_soft_hysteretic_limiter": check_release_soft_hysteretic_limiter,
    "vbr1_l1_precision_rectifier_envelope_detector": check_precision_rectifier_envelope_detector,
    "vbr1_l1_programmable_gain_amplifier": check_programmable_gain_amplifier,
    "vbr1_l2_amplifier_filter_chain": check_release_amplifier_filter_chain,
    "vbr1_l1_bandgap_reference_macro_model": check_bandgap_reference_macro_model,
    "vbr1_l1_ptat_ctat_reference_generator": check_ptat_ctat_reference_generator,
    "vbr1_l1_bias_voltage_generator_with_enable_trim": check_bias_voltage_generator_with_enable_trim,
    "vbr1_l1_power_on_reset_detector": check_power_on_reset_detector,
    "vbr1_l1_uvlo_brownout_detector": check_uvlo_brownout_detector,
    "vbr1_l1_ldo_regulator_macro_model": check_ldo_regulator_macro_model,
    "vbr1_l2_reference_startup_enable_flow": check_reference_startup_enable_flow,
    "vbr1_l2_ldo_load_step_recovery_flow": check_ldo_load_step_recovery_flow,
    "vbr1_l1_lna_gain_compression_macro": check_lna_gain_compression_macro,
    "vbr1_l1_rf_mixer_downconverter_macro": check_rf_mixer_downconverter_macro,
    "vbr1_l1_pa_compression_macro": check_pa_compression_macro,
    "vbr1_l1_log_rssi_power_detector": check_log_rssi_power_detector,
    "vbr1_l1_limiting_amplifier_frontend": check_limiting_amplifier_frontend,
    "vbr1_l2_agc_receiver_leveling_loop": check_agc_receiver_leveling_loop,
    "vbr1_l2_iq_downconversion_chain": check_iq_downconversion_chain,
    "vbr1_l1_dac_mismatch_unit_weighting_model": check_release_dac_mismatch_unit_weighting,
    "vbr1_l2_converter_static_linearity_measurement_flow": check_converter_static_linearity_measurement_flow,
    "vbr1_l2_programmable_stimulus_sequencer": check_programmable_stimulus_sequencer,
    "vbr1_l2_converter_front_end": check_release_converter_front_end_chain,
}


def check_vabench300_proposed_generic(rows: list[dict[str, float]]) -> tuple[bool, str]:
    """Behavior guard for v1.1 proposed 300-expansion gold tasks.

    The proposed assets intentionally share a compact event-driven interface so
    they can be promoted only after EVAS proves clock/reset stimulus, bounded
    state response, and metric generation.  This checker is not a Spectre
    certification substitute; it is the repository behavior checker for the
    generated v1.1 gold references.
    """

    if len(rows) < 80:
        return False, f"vabench300_proposed_too_few_rows={len(rows)}"
    required = {"time", "clk", "in", "rst", "out", "metric"}
    missing = sorted(required - set(rows[0]))
    if missing:
        return False, f"vabench300_proposed_missing_columns={','.join(missing)}"

    def values(name: str) -> list[float]:
        vals: list[float] = []
        for row in rows:
            value = row.get(name)
            if value is None or not math.isfinite(value):
                continue
            vals.append(value)
        return vals

    series = {name: values(name) for name in required}
    if any(len(vals) < 80 for vals in series.values()):
        short = sorted(name for name, vals in series.items() if len(vals) < 80)
        return False, f"vabench300_proposed_short_series={','.join(short)}"

    def span(name: str) -> float:
        vals = series[name]
        return max(vals) - min(vals)

    if span("clk") < 0.8:
        return False, f"vabench300_proposed_clk_not_toggling span={span('clk'):.3f}"
    if span("rst") < 0.8:
        return False, f"vabench300_proposed_rst_not_toggling span={span('rst'):.3f}"
    if span("in") < 0.8:
        return False, f"vabench300_proposed_input_not_exercised span={span('in'):.3f}"
    if span("out") < 1.5:
        return False, f"vabench300_proposed_output_not_dynamic span={span('out'):.3f}"
    if span("metric") < 0.2:
        return False, f"vabench300_proposed_metric_not_dynamic span={span('metric'):.3f}"

    out_vals = series["out"]
    if min(out_vals) < -1.05 or max(out_vals) > 1.05:
        return False, f"vabench300_proposed_output_unbounded min={min(out_vals):.3f} max={max(out_vals):.3f}"
    metric_vals = series["metric"]
    if min(metric_vals) < -1.05 or max(metric_vals) > 1.05:
        return False, f"vabench300_proposed_metric_unbounded min={min(metric_vals):.3f} max={max(metric_vals):.3f}"
    if not any(value > 0.8 for value in out_vals) or not any(value < -0.8 for value in out_vals):
        return False, "vabench300_proposed_output_missing_bipolar_saturation"

    clk_vals = series["clk"]
    rising_edges = sum(
        1
        for prev, cur in zip(clk_vals, clk_vals[1:])
        if prev <= 0.5 < cur
    )
    if rising_edges < 5:
        return False, f"vabench300_proposed_too_few_clk_edges={rising_edges}"

    return (
        True,
        "vabench300_proposed_gold_ok "
        f"rows={len(rows)} clk_edges={rising_edges} "
        f"out_span={span('out'):.3f} metric_span={span('metric'):.3f}",
    )


def _sample_rows_every_10ns(rows: list[dict[str, float]]) -> list[dict[str, float]]:
    # Formal utility testbenches hold each vector for a 10 ns window. Sample
    # mid-window to avoid transition edges and PWL update times.
    max_time = rows[-1]["time"]
    times = [row["time"] for row in rows]
    samples: list[dict[str, float]] = []
    sample_t = 5e-9
    while sample_t <= max_time + 1e-15:
        idx = min(range(len(times)), key=lambda i: abs(times[i] - sample_t))
        samples.append(rows[idx])
        sample_t += 10e-9
    return samples


def _logic_bits_to_int(row: dict[str, float], prefix: str, width: int, vth: float = 0.45) -> int:
    return sum((1 << bit) for bit in range(width) if row[f"{prefix}{bit}"] > vth)


def check_bin_to_thermometer_decoder_8b(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "en", *{f"b{i}" for i in range(8)}, *{f"th{i}" for i in range(256)}}
    if not rows or not required.issubset(rows[0]):
        missing = sorted(required - set(rows[0].keys())) if rows else sorted(required)
        return False, "missing_columns=" + ",".join(missing[:12])

    vth = 0.45
    samples = _sample_rows_every_10ns(rows)

    checked_codes: list[int] = []
    enable_low_ok = True
    cumulative_errors = 0
    count_errors = 0
    boundary_seen = set()
    for row in samples:
        code = sum((1 << bit) for bit in range(8) if row[f"b{bit}"] > vth)
        enabled = row["en"] > vth
        expected_count = code if enabled else 0
        actual_high = {i for i in range(256) if row[f"th{i}"] > vth}
        expected_high = set(range(expected_count))
        if actual_high != expected_high:
            if len(actual_high) != expected_count:
                count_errors += 1
            else:
                cumulative_errors += 1
        if not enabled and actual_high:
            enable_low_ok = False
        checked_codes.append(code if enabled else -1)
        if enabled and code in {0, 1, 255}:
            boundary_seen.add(code)

    ok = (
        enable_low_ok
        and count_errors == 0
        and cumulative_errors == 0
        and {0, 1, 255}.issubset(boundary_seen)
        and -1 in checked_codes
    )
    return ok, (
        f"checked={checked_codes} boundary_seen={sorted(boundary_seen)} "
        f"enable_low_ok={enable_low_ok} count_errors={count_errors} "
        f"cumulative_errors={cumulative_errors}"
    )


def check_thermometer_to_binary_encoder_8b(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "valid", *{f"th{i}" for i in range(256)}, *{f"b{i}" for i in range(8)}}
    if not rows or not required.issubset(rows[0]):
        missing = sorted(required - set(rows[0].keys())) if rows else sorted(required)
        return False, "missing_columns=" + ",".join(missing[:12])
    samples = _sample_rows_every_10ns(rows)
    checked: list[str] = []
    valid_errors = 0
    count_errors = 0
    for row in samples:
        high = {i for i in range(256) if row[f"th{i}"] > 0.45}
        cumulative = high == set(range(len(high)))
        expected_valid = cumulative
        actual_valid = row["valid"] > 0.45
        if actual_valid != expected_valid:
            valid_errors += 1
        expected_code = len(high) if expected_valid else 0
        actual_code = _logic_bits_to_int(row, "b", 8)
        if actual_code != expected_code:
            count_errors += 1
        checked.append(str(expected_code) if expected_valid else "invalid")
    return valid_errors == 0 and count_errors == 0 and {"0", "1", "255", "invalid"}.issubset(set(checked)), (
        f"checked={checked} valid_errors={valid_errors} count_errors={count_errors}"
    )


def check_gray_to_binary_converter_8b(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", *{f"g{i}" for i in range(8)}, *{f"b{i}" for i in range(8)}}
    if not rows or not required.issubset(rows[0]):
        missing = sorted(required - set(rows[0].keys())) if rows else sorted(required)
        return False, "missing_columns=" + ",".join(missing[:12])
    checked: list[int] = []
    errors = 0
    for row in _sample_rows_every_10ns(rows):
        gray = _logic_bits_to_int(row, "g", 8)
        binary = 0
        value = gray
        while value:
            binary ^= value
            value >>= 1
        actual = _logic_bits_to_int(row, "b", 8)
        if actual != binary:
            errors += 1
        checked.append(binary)
    return errors == 0 and {0, 1, 2, 127, 128, 255}.issubset(set(checked)), (
        f"checked={checked} errors={errors}"
    )


def check_binary_to_gray_converter_8b(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", *{f"b{i}" for i in range(8)}, *{f"g{i}" for i in range(8)}}
    if not rows or not required.issubset(rows[0]):
        missing = sorted(required - set(rows[0].keys())) if rows else sorted(required)
        return False, "missing_columns=" + ",".join(missing[:12])
    checked: list[int] = []
    errors = 0
    for row in _sample_rows_every_10ns(rows):
        code = _logic_bits_to_int(row, "b", 8)
        expected = code ^ (code >> 1)
        actual = _logic_bits_to_int(row, "g", 8)
        if actual != expected:
            errors += 1
        checked.append(code)
    return errors == 0 and {0, 1, 2, 127, 128, 255}.issubset(set(checked)), (
        f"checked={checked} errors={errors}"
    )


def check_onehot_to_binary_encoder_16b(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "valid", *{f"oh{i}" for i in range(16)}, *{f"b{i}" for i in range(4)}}
    if not rows or not required.issubset(rows[0]):
        missing = sorted(required - set(rows[0].keys())) if rows else sorted(required)
        return False, "missing_columns=" + ",".join(missing[:12])
    checked: list[str] = []
    valid_errors = 0
    code_errors = 0
    for row in _sample_rows_every_10ns(rows):
        high = [i for i in range(16) if row[f"oh{i}"] > 0.45]
        expected_valid = len(high) == 1
        expected_code = high[0] if expected_valid else 0
        if (row["valid"] > 0.45) != expected_valid:
            valid_errors += 1
        if _logic_bits_to_int(row, "b", 4) != expected_code:
            code_errors += 1
        checked.append(str(expected_code) if expected_valid else "invalid")
    return valid_errors == 0 and code_errors == 0 and {"0", "1", "15", "invalid"}.issubset(set(checked)), (
        f"checked={checked} valid_errors={valid_errors} code_errors={code_errors}"
    )


def check_binary_to_onehot_decoder_16b(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "en", *{f"b{i}" for i in range(4)}, *{f"oh{i}" for i in range(16)}}
    if not rows or not required.issubset(rows[0]):
        missing = sorted(required - set(rows[0].keys())) if rows else sorted(required)
        return False, "missing_columns=" + ",".join(missing[:12])
    checked: list[int] = []
    errors = 0
    enable_low_seen = False
    for row in _sample_rows_every_10ns(rows):
        code = _logic_bits_to_int(row, "b", 4)
        enabled = row["en"] > 0.45
        expected = {code} if enabled else set()
        actual = {i for i in range(16) if row[f"oh{i}"] > 0.45}
        if actual != expected:
            errors += 1
        checked.append(code if enabled else -1)
        enable_low_seen = enable_low_seen or not enabled
    return errors == 0 and set(range(16)).issubset(set(checked)) and enable_low_seen, (
        f"checked={checked} errors={errors} enable_low_seen={enable_low_seen}"
    )


def check_decimal_digit_to_bcd_encoder(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "valid", *{f"d{i}" for i in range(10)}, *{f"b{i}" for i in range(4)}}
    if not rows or not required.issubset(rows[0]):
        missing = sorted(required - set(rows[0].keys())) if rows else sorted(required)
        return False, "missing_columns=" + ",".join(missing[:12])
    checked: list[str] = []
    valid_errors = 0
    code_errors = 0
    for row in _sample_rows_every_10ns(rows):
        high = [i for i in range(10) if row[f"d{i}"] > 0.45]
        expected_valid = len(high) == 1
        expected_code = high[0] if expected_valid else 0
        if (row["valid"] > 0.45) != expected_valid:
            valid_errors += 1
        if _logic_bits_to_int(row, "b", 4) != expected_code:
            code_errors += 1
        checked.append(str(expected_code) if expected_valid else "invalid")
    return valid_errors == 0 and code_errors == 0 and set(map(str, range(10))).issubset(set(checked)) and "invalid" in checked, (
        f"checked={checked} valid_errors={valid_errors} code_errors={code_errors}"
    )


def check_signed_magnitude_to_twos_complement_8b(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "sign", *{f"mag{i}" for i in range(7)}, *{f"y{i}" for i in range(8)}}
    if not rows or not required.issubset(rows[0]):
        missing = sorted(required - set(rows[0].keys())) if rows else sorted(required)
        return False, "missing_columns=" + ",".join(missing[:12])
    checked: list[int] = []
    errors = 0
    neg_zero_seen = False
    for row in _sample_rows_every_10ns(rows):
        mag = _logic_bits_to_int(row, "mag", 7)
        negative = row["sign"] > 0.45
        expected = ((256 - mag) & 255) if negative and mag != 0 else mag
        actual = _logic_bits_to_int(row, "y", 8)
        if actual != expected:
            errors += 1
        checked.append(-mag if negative else mag)
        neg_zero_seen = neg_zero_seen or (negative and mag == 0)
    return errors == 0 and neg_zero_seen and {0, 1, -1, 63, -63, 127, -127}.issubset(set(checked)), (
        f"checked={checked} errors={errors} neg_zero_seen={neg_zero_seen}"
    )


def _check_bus_equal(
    rows: list[dict[str, float]],
    input_prefix: str,
    output_prefix: str,
    width: int,
    enable_col: str | None = None,
    invert_enable: bool = False,
) -> tuple[bool, str]:
    required = {"time", *{f"{input_prefix}{i}" for i in range(width)}, *{f"{output_prefix}{i}" for i in range(width)}}
    if enable_col:
        required.add(enable_col)
    if not rows or not required.issubset(rows[0]):
        missing = sorted(required - set(rows[0].keys())) if rows else sorted(required)
        return False, "missing_columns=" + ",".join(missing[:12])
    errors = 0
    checked = 0
    for row in _sample_rows_every_10ns(rows):
        enabled = True
        if enable_col:
            en_high = row[enable_col] > 0.45
            enabled = (not en_high) if invert_enable else en_high
        for idx in range(width):
            expected_high = enabled and row[f"{input_prefix}{idx}"] > 0.45
            actual_high = row[f"{output_prefix}{idx}"] > 0.45
            if actual_high != expected_high:
                errors += 1
        checked += 1
    return errors == 0 and checked >= 3, f"checked={checked} bit_errors={errors}"


def check_config_latch_32b_clocked(rows: list[dict[str, float]]) -> tuple[bool, str]:
    return _check_bus_equal(rows, "d", "q", 32, "en")


def check_config_latch_128b_static_enable(rows: list[dict[str, float]]) -> tuple[bool, str]:
    return _check_bus_equal(rows, "d", "q", 128, "en")


def check_config_shift_register_64b(rows: list[dict[str, float]]) -> tuple[bool, str]:
    serial_key = "serial_in" if rows and "serial_in" in rows[0] else "sin"
    required = {"time", serial_key, *{f"q{i}" for i in range(64)}}
    if not rows or not required.issubset(rows[0]):
        missing = sorted(required - set(rows[0].keys())) if rows else sorted(required)
        return False, "missing_columns=" + ",".join(missing[:12])
    samples = _sample_rows_every_10ns(rows)
    history: list[int] = []
    errors = 0
    for row in samples:
        history.insert(0, 1 if row[serial_key] > 0.45 else 0)
        history = history[:64]
        for idx in range(min(len(history), 64)):
            if (row[f"q{idx}"] > 0.45) != (history[idx] == 1):
                errors += 1
    return errors == 0 and len(samples) >= 10, f"checked={len(samples)} bit_errors={errors}"


def check_bus_splitter_256_to_16x16(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", *{f"in{i}" for i in range(256)}, *{f"out{block}_{bit}" for block in range(16) for bit in range(16)}}
    if not rows or not required.issubset(rows[0]):
        missing = sorted(required - set(rows[0].keys())) if rows else sorted(required)
        return False, "missing_columns=" + ",".join(missing[:12])
    errors = 0
    for row in _sample_rows_every_10ns(rows):
        for block in range(16):
            for bit in range(16):
                src = block * 16 + bit
                if (row[f"out{block}_{bit}"] > 0.45) != (row[f"in{src}"] > 0.45):
                    errors += 1
    return errors == 0, f"bit_errors={errors}"


def check_bus_combiner_16x16_to_256(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", *{f"in{block}_{bit}" for block in range(16) for bit in range(16)}, *{f"out{i}" for i in range(256)}}
    if not rows or not required.issubset(rows[0]):
        missing = sorted(required - set(rows[0].keys())) if rows else sorted(required)
        return False, "missing_columns=" + ",".join(missing[:12])
    errors = 0
    for row in _sample_rows_every_10ns(rows):
        for block in range(16):
            for bit in range(16):
                dst = block * 16 + bit
                if (row[f"out{dst}"] > 0.45) != (row[f"in{block}_{bit}"] > 0.45):
                    errors += 1
    return errors == 0, f"bit_errors={errors}"


def check_masked_config_update_32b(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", *{f"old{i}" for i in range(32)}, *{f"new{i}" for i in range(32)}, *{f"mask{i}" for i in range(32)}, *{f"out{i}" for i in range(32)}}
    if not rows or not required.issubset(rows[0]):
        missing = sorted(required - set(rows[0].keys())) if rows else sorted(required)
        return False, "missing_columns=" + ",".join(missing[:12])
    errors = 0
    for row in _sample_rows_every_10ns(rows):
        for idx in range(32):
            expected = row[f"new{idx}"] > 0.45 if row[f"mask{idx}"] > 0.45 else row[f"old{idx}"] > 0.45
            if (row[f"out{idx}"] > 0.45) != expected:
                errors += 1
    return errors == 0, f"bit_errors={errors}"


def _rising_times(rows: list[dict[str, float]], col: str, vth: float = 0.45) -> list[float]:
    times: list[float] = []
    last = rows[0][col] > vth
    for row in rows[1:]:
        cur = row[col] > vth
        if not last and cur:
            times.append(row["time"])
        last = cur
    return times


def _falling_times(rows: list[dict[str, float]], col: str, vth: float = 0.45) -> list[float]:
    times: list[float] = []
    last = rows[0][col] > vth
    for row in rows[1:]:
        cur = row[col] > vth
        if last and not cur:
            times.append(row["time"])
        last = cur
    return times


def _sample_after(rows: list[dict[str, float]], t: float, delay: float = 5e-9) -> dict[str, float]:
    target = t + delay
    return min(rows, key=lambda row: abs(row["time"] - target))


def check_edge_interval_tdc_8b(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "start", "stop", "valid", *{f"code{i}" for i in range(8)}}
    if not rows or not required.issubset(rows[0]):
        missing = sorted(required - set(rows[0].keys())) if rows else sorted(required)
        return False, "missing_columns=" + ",".join(missing[:12])
    starts = _rising_times(rows, "start")
    stops = _rising_times(rows, "stop")
    errors = 0
    checked: list[int] = []
    for start_t, stop_t in zip(starts, stops):
        expected = max(0, min(255, int(round((stop_t - start_t) / 1e-9))))
        row = _sample_after(rows, stop_t)
        actual = _logic_bits_to_int(row, "code", 8)
        if row["valid"] <= 0.45 or abs(actual - expected) > 1:
            errors += 1
        checked.append(expected)
    return errors == 0 and len(checked) >= 3 and len(set(checked)) >= 3, f"checked={checked} errors={errors}"


def check_period_meter_16b(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk_in", "valid", *{f"period{i}" for i in range(16)}}
    if not rows or not required.issubset(rows[0]):
        missing = sorted(required - set(rows[0].keys())) if rows else sorted(required)
        return False, "missing_columns=" + ",".join(missing[:12])
    rises = _rising_times(rows, "clk_in")
    errors = 0
    checked: list[int] = []
    for prev_t, cur_t in zip(rises, rises[1:]):
        expected = max(0, min(65535, int(round((cur_t - prev_t) / 1e-9))))
        row = _sample_after(rows, cur_t)
        actual = _logic_bits_to_int(row, "period", 16)
        if row["valid"] <= 0.45 or abs(actual - expected) > 1:
            errors += 1
        checked.append(expected)
    return errors == 0 and len(checked) >= 3 and len(set(checked)) >= 2, f"checked={checked} errors={errors}"


def check_duty_cycle_meter_8b(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk_in", "valid", *{f"duty{i}" for i in range(8)}}
    if not rows or not required.issubset(rows[0]):
        missing = sorted(required - set(rows[0].keys())) if rows else sorted(required)
        return False, "missing_columns=" + ",".join(missing[:12])
    rises = _rising_times(rows, "clk_in")
    falls = _falling_times(rows, "clk_in")
    errors = 0
    checked: list[int] = []
    for first_rise, second_rise in zip(rises, rises[1:]):
        falls_in_cycle = [t for t in falls if first_rise < t < second_rise]
        if not falls_in_cycle:
            continue
        high_time = falls_in_cycle[0] - first_rise
        period = second_rise - first_rise
        expected = max(0, min(255, int(round(255.0 * high_time / period))))
        row = _sample_after(rows, second_rise)
        actual = _logic_bits_to_int(row, "duty", 8)
        if row["valid"] <= 0.45 or abs(actual - expected) > 1:
            errors += 1
        checked.append(expected)
    return errors == 0 and len(checked) >= 3 and len(set(checked)) >= 2, f"checked={checked} errors={errors}"


def check_event_counter_windowed_16b(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "gate", "event", "done", *{f"count{i}" for i in range(16)}}
    if not rows or not required.issubset(rows[0]):
        missing = sorted(required - set(rows[0].keys())) if rows else sorted(required)
        return False, "missing_columns=" + ",".join(missing[:12])
    gate_rises = _rising_times(rows, "gate")
    gate_falls = _falling_times(rows, "gate")
    event_rises = _rising_times(rows, "event")
    errors = 0
    checked: list[int] = []
    for start_t, stop_t in zip(gate_rises, gate_falls):
        expected = sum(1 for t in event_rises if start_t < t < stop_t)
        row = _sample_after(rows, stop_t)
        actual = _logic_bits_to_int(row, "count", 16)
        if row["done"] <= 0.45 or actual != expected:
            errors += 1
        checked.append(expected)
    return errors == 0 and len(checked) >= 2 and max(checked, default=0) > 0, f"checked={checked} errors={errors}"


def check_ready_valid_latency_counter_12b(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "valid_i", "ready_i", "done", *{f"lat{i}" for i in range(12)}}
    if not rows or not required.issubset(rows[0]):
        missing = sorted(required - set(rows[0].keys())) if rows else sorted(required)
        return False, "missing_columns=" + ",".join(missing[:12])
    rise_rows = [_sample_after(rows, t, 1e-9) for t in _rising_times(rows, "clk")]
    active = False
    count = 0
    errors = 0
    checked: list[int] = []
    for row in rise_rows:
        valid = row["valid_i"] > 0.45
        ready = row["ready_i"] > 0.45
        if valid and not active:
            active = True
            count = 0
        elif active and not ready:
            count += 1
        if active and ready:
            expected = count
            actual = _logic_bits_to_int(row, "lat", 12)
            if row["done"] <= 0.45 or actual != expected:
                errors += 1
            checked.append(expected)
            active = False
    return errors == 0 and len(checked) >= 2 and max(checked, default=0) > 0, f"checked={checked} errors={errors}"


def check_settling_window_detector(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "vin", "target", "tol", "settled", *{f"t_code{i}" for i in range(8)}}
    if not rows or not required.issubset(rows[0]):
        missing = sorted(required - set(rows[0].keys())) if rows else sorted(required)
        return False, "missing_columns=" + ",".join(missing[:12])
    hold = 20e-9
    flags = [abs(row["vin"] - row["target"]) <= row["tol"] + 1e-12 for row in rows]
    intervals: list[tuple[float, float]] = []
    start: float | None = rows[0]["time"] if flags[0] else None
    for idx in range(1, len(rows)):
        if flags[idx] and not flags[idx - 1]:
            start = rows[idx]["time"]
        elif flags[idx - 1] and not flags[idx] and start is not None:
            intervals.append((start, rows[idx]["time"]))
            start = None
    if start is not None:
        intervals.append((start, rows[-1]["time"]))

    long_intervals = [(a, b) for a, b in intervals if b - a >= hold + 2e-9]
    if not long_intervals:
        return False, f"no_long_settling_interval intervals={intervals}"

    errors = 0
    settled_seen = False
    early_seen = False
    reset_seen = len(intervals) >= 2
    samples = []
    t = 2.5e-9
    while t <= rows[-1]["time"] + 1e-15:
        samples.append(min(rows, key=lambda row: abs(row["time"] - t)))
        t += 2.5e-9

    for row in samples:
        actual_settled = row["settled"] > 0.45
        in_allowed_settled_region = any((entry + hold + 1e-9) <= row["time"] <= (exit_t - 1e-9) for entry, exit_t in long_intervals)
        in_early_region = any((entry + 1e-9) <= row["time"] < (entry + hold - 1e-9) for entry, exit_t in long_intervals)
        if actual_settled and in_early_region:
            early_seen = True
            errors += 1
        if actual_settled and not any((entry + hold - 1e-9) <= row["time"] <= (exit_t + 1e-9) for entry, exit_t in long_intervals):
            errors += 1
        if in_allowed_settled_region:
            if not actual_settled:
                errors += 1
            else:
                settled_seen = True
                entry = next(entry for entry, exit_t in long_intervals if (entry + hold + 1e-9) <= row["time"] <= (exit_t - 1e-9))
                expected_code = max(0, min(255, int(round(entry / 1e-9))))
                actual_code = _logic_bits_to_int(row, "t_code", 8)
                if abs(actual_code - expected_code) > 1:
                    errors += 1
    return errors == 0 and settled_seen and reset_seen and not early_seen, (
        f"errors={errors} intervals={[(round(a/1e-9,1), round(b/1e-9,1)) for a,b in long_intervals]} "
        f"settled_seen={settled_seen} reset_seen={reset_seen} early_seen={early_seen}"
    )


def check_reset_sync_active_low(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "rst_n", "sync_rst_n"}
    if not rows or not required.issubset(rows[0]):
        missing = sorted(required - set(rows[0].keys())) if rows else sorted(required)
        return False, "missing_columns=" + ",".join(missing[:12])
    sr = [0, 0]
    errors = 0
    saw_assert = False
    saw_release = False
    times = [row["time"] for row in rows]
    for t in _rising_times(rows, "clk"):
        edge_row = rows[min(range(len(times)), key=lambda idx: abs(times[idx] - t))]
        out_row = _sample_after(rows, t, 1e-9)
        if edge_row["rst_n"] <= 0.45:
            sr = [0, 0]
            saw_assert = True
        else:
            sr = [1, sr[0]]
        expected = sr[1] == 1
        actual = out_row["sync_rst_n"] > 0.45
        if actual != expected:
            errors += 1
        saw_release = saw_release or actual
    for row in rows[:: max(1, len(rows) // 300)]:
        if row["time"] < 1e-9 or 0.1 < row["rst_n"] < 0.8 or 0.1 < row["sync_rst_n"] < 0.8:
            continue
        if row["rst_n"] <= 0.45 and row["sync_rst_n"] > 0.45:
            errors += 1
            saw_assert = True
    return errors <= 1 and saw_assert and saw_release, f"checked={len(_rising_times(rows, 'clk'))} errors={errors}"


def check_reset_sync_active_high(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "rst", "sync_rst"}
    if not rows or not required.issubset(rows[0]):
        missing = sorted(required - set(rows[0].keys())) if rows else sorted(required)
        return False, "missing_columns=" + ",".join(missing[:12])
    sr = [1, 1]
    errors = 0
    saw_assert = False
    saw_release = False
    times = [row["time"] for row in rows]
    for t in _rising_times(rows, "clk"):
        edge_row = rows[min(range(len(times)), key=lambda idx: abs(times[idx] - t))]
        out_row = _sample_after(rows, t, 1e-9)
        if edge_row["rst"] > 0.45:
            sr = [1, 1]
            saw_assert = True
        else:
            sr = [0, sr[0]]
        expected = sr[1] == 1
        actual = out_row["sync_rst"] > 0.45
        if actual != expected:
            errors += 1
        saw_release = saw_release or not actual
    for row in rows[:: max(1, len(rows) // 300)]:
        if row["time"] < 1e-9 or 0.1 < row["rst"] < 0.8 or 0.1 < row["sync_rst"] < 0.8:
            continue
        if row["rst"] > 0.45 and row["sync_rst"] <= 0.45:
            errors += 1
            saw_assert = True
    return errors <= 1 and saw_assert and saw_release, f"checked={len(_rising_times(rows, 'clk'))} errors={errors}"


def check_enable_gated_clock_pulse(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "en", "pulse"}
    if not rows or not required.issubset(rows[0]):
        missing = sorted(required - set(rows[0].keys())) if rows else sorted(required)
        return False, "missing_columns=" + ",".join(missing[:12])
    errors = 0
    saw_high = False
    saw_blocked = False
    edge_times = _rising_times(rows, "clk") + _falling_times(rows, "clk") + _rising_times(rows, "en") + _falling_times(rows, "en")
    for row in rows[:: max(1, len(rows) // 400)]:
        if any(abs(row["time"] - t) < 0.3e-9 for t in edge_times):
            continue
        if 0.1 < row["clk"] < 0.8 or 0.1 < row["en"] < 0.8 or 0.1 < row["pulse"] < 0.8:
            continue
        expected = row["en"] > 0.45 and row["clk"] > 0.45
        actual = row["pulse"] > 0.45
        if actual != expected:
            errors += 1
        saw_high = saw_high or actual
        saw_blocked = saw_blocked or (row["clk"] > 0.45 and row["en"] <= 0.45 and not actual)
    return errors == 0 and saw_high and saw_blocked, f"errors={errors} saw_high={saw_high} saw_blocked={saw_blocked}"


def check_low_active_enable_decoder_4b(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "en_n", *{f"a{i}" for i in range(4)}, *{f"y{i}_n" for i in range(16)}}
    if not rows or not required.issubset(rows[0]):
        missing = sorted(required - set(rows[0].keys())) if rows else sorted(required)
        return False, "missing_columns=" + ",".join(missing[:12])
    errors = 0
    checked: list[int] = []
    disabled_seen = False
    for row in _sample_rows_every_10ns(rows):
        code = _logic_bits_to_int(row, "a", 4)
        enabled = row["en_n"] <= 0.45
        lows = {i for i in range(16) if row[f"y{i}_n"] <= 0.45}
        expected = {code} if enabled else set()
        if lows != expected:
            errors += 1
        checked.append(code if enabled else -1)
        disabled_seen = disabled_seen or not enabled
    return errors == 0 and set(range(16)).issubset(set(checked)) and disabled_seen, f"checked={checked} errors={errors}"


def check_configurable_polarity_edge_detector(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "sig", "rise_en", "pulse"}
    if not rows or not required.issubset(rows[0]):
        missing = sorted(required - set(rows[0].keys())) if rows else sorted(required)
        return False, "missing_columns=" + ",".join(missing[:12])
    edge_times: list[float] = []
    last_sig = rows[0]["sig"] > 0.45
    for row in rows[1:]:
        sig = row["sig"] > 0.45
        rise_mode = row["rise_en"] > 0.45
        edge = (not last_sig and sig) if rise_mode else (last_sig and not sig)
        if edge:
            edge_times.append(row["time"])
        last_sig = sig
    missed = 0
    for edge_t in edge_times:
        if not any(edge_t <= row["time"] <= edge_t + 3e-9 and row["pulse"] > 0.45 for row in rows):
            missed += 1
    false_pulses = 0
    for row in rows:
        if row["pulse"] <= 0.45:
            continue
        if not any(edge_t <= row["time"] <= edge_t + 4e-9 for edge_t in edge_times):
            false_pulses += 1
    return len(edge_times) >= 3 and missed == 0 and false_pulses == 0, (
        f"events={len(edge_times)} missed={missed} false_pulses={false_pulses}"
    )


def check_prbs_generator_32b(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "rst", "load_seed", *{f"seed{i}" for i in range(32)}, *{f"out{i}" for i in range(32)}}
    if not rows or not required.issubset(rows[0]):
        missing = sorted(required - set(rows[0].keys())) if rows else sorted(required)
        return False, "missing_columns=" + ",".join(missing[:12])
    samples = [_sample_after(rows, t, 1e-9) for t in _rising_times(rows, "clk")]
    state = 1
    errors = 0
    checked = 0
    for row in samples:
        if row["rst"] > 0.45:
            state = 1
        elif row["load_seed"] > 0.45:
            state = _logic_bits_to_int(row, "seed", 32) or 1
        else:
            feedback = ((state >> 31) ^ (state >> 21) ^ (state >> 1) ^ state) & 1
            state = ((state << 1) & 0xFFFFFFFF) | feedback
        actual = _logic_bits_to_int(row, "out", 32)
        if actual != state:
            errors += 1
        checked += 1
    return errors == 0 and checked >= 8, f"checked={checked} errors={errors}"


def check_multiphase_clock_generator_4ph(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk0", "clk90", "clk180", "clk270"}
    if not rows or not required.issubset(rows[0]):
        missing = sorted(required - set(rows[0].keys())) if rows else sorted(required)
        return False, "missing_columns=" + ",".join(missing[:12])
    rises = {col: _rising_times(rows, col)[:4] for col in ("clk0", "clk90", "clk180", "clk270")}
    if any(len(v) < 2 for v in rises.values()):
        return False, f"too_few_edges={ {k: len(v) for k, v in rises.items()} }"
    errors = 0
    period_errors = 0
    clk0_periods = [b - a for a, b in zip(rises["clk0"], rises["clk0"][1:])]
    for period in clk0_periods:
        if abs(period - 20e-9) > 1.5e-9:
            period_errors += 1
    for base in rises["clk0"][:3]:
        targets = [base + 5e-9, base + 10e-9, base + 15e-9]
        cols = ["clk90", "clk180", "clk270"]
        for col, target in zip(cols, targets):
            if min(abs(t - target) for t in rises[col]) > 1.5e-9:
                errors += 1
    return errors == 0 and period_errors == 0, (
        f"edge_counts={ {k: len(v) for k, v in rises.items()} } "
        f"phase_errors={errors} period_errors={period_errors}"
    )


def check_configurable_pulse_train(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "start", "pulse", "done", *{f"period{i}" for i in range(4)}, *{f"width{i}" for i in range(4)}, *{f"count{i}" for i in range(4)}}
    if not rows or not required.issubset(rows[0]):
        missing = sorted(required - set(rows[0].keys())) if rows else sorted(required)
        return False, "missing_columns=" + ",".join(missing[:12])
    times = [row["time"] for row in rows]
    edge_pairs = [
        (rows[min(range(len(times)), key=lambda idx: abs(times[idx] - t))], _sample_after(rows, t, 1e-9))
        for t in _rising_times(rows, "clk")
    ]
    running = False
    period = width = total = 0
    tick = emitted = 0
    errors = 0
    done_seen = False
    expected_total = 0
    for edge_row, out_row in edge_pairs:
        if edge_row["start"] > 0.45 and not running:
            period = max(1, _logic_bits_to_int(edge_row, "period", 4))
            width = max(1, _logic_bits_to_int(edge_row, "width", 4))
            total = max(1, _logic_bits_to_int(edge_row, "count", 4))
            expected_total = total
            running = True
            tick = 0
            emitted = 0
        expected_pulse = running and emitted < total and (tick % period) < width
        if (out_row["pulse"] > 0.45) != expected_pulse:
            errors += 1
        if running:
            if tick % period == period - 1:
                emitted += 1
            tick += 1
            if emitted >= total and (tick % period) == 0:
                running = False
        expected_done = not running and emitted >= total and total > 0
        done_seen = done_seen or expected_done
        if (out_row["done"] > 0.45) != expected_done:
            errors += 1
    pulse_count = len(_rising_times(rows, "pulse"))
    if expected_total and pulse_count != expected_total:
        errors += 1
    return errors == 0 and done_seen, f"errors={errors} done_seen={done_seen} pulse_count={pulse_count} expected_total={expected_total}"


def check_staircase_dac_stimulus_8b(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "clk", "rst", "vout", *{f"code{i}" for i in range(8)}}
    if not rows or not required.issubset(rows[0]):
        missing = sorted(required - set(rows[0].keys())) if rows else sorted(required)
        return False, "missing_columns=" + ",".join(missing[:12])
    times = [row["time"] for row in rows]
    edge_pairs = [
        (rows[min(range(len(times)), key=lambda idx: abs(times[idx] - t))], _sample_after(rows, t, 1e-9))
        for t in _rising_times(rows, "clk")
    ]
    expected = 0
    errors = 0
    checked: list[int] = []
    for edge_row, out_row in edge_pairs:
        if edge_row["rst"] > 0.45:
            expected = 0
        else:
            expected = (expected + 1) & 255
        actual = _logic_bits_to_int(out_row, "code", 8)
        expected_v = 0.9 * expected / 255.0
        if actual != expected or abs(out_row["vout"] - expected_v) > 0.002:
            errors += 1
        checked.append(expected)
    return errors == 0 and max(checked, default=0) > 4 and 0 in checked, f"checked={checked[:20]} errors={errors}"


def check_deterministic_jittered_clock(rows: list[dict[str, float]]) -> tuple[bool, str]:
    required = {"time", "jitter_en", "clk_out", *{f"seed{i}" for i in range(8)}}
    if not rows or not required.issubset(rows[0]):
        missing = sorted(required - set(rows[0].keys())) if rows else sorted(required)
        return False, "missing_columns=" + ",".join(missing[:12])
    rises = _rising_times(rows, "clk_out")
    if len(rises) < 8:
        return False, f"too_few_edges={len(rises)}"
    periods = [round((b - a) / 1e-9, 2) for a, b in zip(rises, rises[1:])]
    varying = len(set(periods)) >= 3
    bounded = all(14.0 <= p <= 26.0 for p in periods)
    expected_prefix = [21.6, 19.2, 20.8, 18.4, 20.0]
    prefix_ok = len(periods) >= len(expected_prefix) and all(
        abs(periods[idx] - expected_prefix[idx]) <= 0.25
        for idx in range(len(expected_prefix))
    )
    return varying and bounded and prefix_ok, (
        f"periods_ns={periods[:12]} varying={varying} bounded={bounded} prefix_ok={prefix_ok}"
    )



VABENCH300_PROPOSED_CHECK_ALIASES = {
    "vbr11_l1_sigma_delta_modulator_loop": ("dut", "tb", "e2e", "bugfix"),
    "vbr11_l2_time_interleaved_adc_mismatch_flow": ("dut", "tb", "e2e", "bugfix"),
    "vbr11_l2_metastability_window_comparator_flow": ("dut", "tb", "e2e", "bugfix"),
    "vbr11_l1_bootstrapped_sample_switch": ("dut", "tb", "e2e", "bugfix"),
    "vbr11_l2_fractional_n_pll_divider_flow": ("dut", "tb", "e2e", "bugfix"),
    "vbr11_l2_bandgap_startup_trim_flow": ("dut", "tb", "e2e", "bugfix"),
    "vbr11_l2_quadrature_iq_imbalance_corrector": ("dut", "tb", "e2e", "bugfix"),
    "vbr1_l2_cppll_tracking_and_frequency_step_reacquire_flow": ("bugfix",),
}


TB_UTILITY_30_STAGING_CHECK_ALIASES = (
    "vbr1_l1_bin_to_thermometer_decoder_8b",
    "vbr1_l1_thermometer_to_binary_encoder_8b",
    "vbr1_l1_gray_to_binary_converter_8b",
    "vbr1_l1_binary_to_gray_converter_8b",
    "vbr1_l1_onehot_to_binary_encoder_16b",
    "vbr1_l1_binary_to_onehot_decoder_16b",
    "vbr1_l1_decimal_digit_to_bcd_encoder",
    "vbr1_l1_signed_magnitude_to_twos_complement_8b",
    "vbr1_l1_config_latch_32b_clocked",
    "vbr1_l1_config_latch_128b_static_enable",
    "vbr1_l1_config_shift_register_64b",
    "vbr1_l1_bus_splitter_256_to_16x16",
    "vbr1_l1_bus_combiner_16x16_to_256",
    "vbr1_l1_masked_config_update_32b",
    "vbr1_l1_edge_interval_tdc_8b",
    "vbr1_l1_period_meter_16b",
    "vbr1_l1_duty_cycle_meter_8b",
    "vbr1_l1_event_counter_windowed_16b",
    "vbr1_l1_latency_counter_ready_valid_12b",
    "vbr1_l1_settling_window_detector",
    "vbr1_l1_active_low_reset_synchronizer",
    "vbr1_l1_active_high_reset_synchronizer",
    "vbr1_l1_enable_gated_clock_pulse",
    "vbr1_l1_low_active_enable_decoder_4b",
    "vbr1_l1_configurable_polarity_edge_detector",
    "vbr1_l1_prbs_generator_32b_seeded",
    "vbr1_l1_multiphase_clock_generator_4ph",
    "vbr1_l1_configurable_pulse_train_generator",
    "vbr1_l1_staircase_dac_stimulus_8b",
    "vbr1_l1_jittered_clock_source_deterministic",
)


for _entry_id, _checker in RELEASE_CHECK_ALIASES.items():
    CHECKS.setdefault(_entry_id, _checker)
    for _form in ("dut", "tb", "bugfix", "e2e"):
        CHECKS.setdefault(f"{_entry_id}_{_form}", _checker)
        CHECKS.setdefault(f"{_entry_id}:{_form}", _checker)


for _entry_id, _forms in VABENCH300_PROPOSED_CHECK_ALIASES.items():
    for _form in _forms:
        CHECKS[f"{_entry_id}_{_form}"] = check_vabench300_proposed_generic
        CHECKS[f"{_entry_id}:{_form}"] = check_vabench300_proposed_generic


for _entry_id in TB_UTILITY_30_STAGING_CHECK_ALIASES:
    CHECKS[f"{_entry_id}_dut"] = check_vabench300_proposed_generic
    CHECKS[f"{_entry_id}:dut"] = check_vabench300_proposed_generic

CHECKS["bin_to_thermometer_decoder_8b"] = check_bin_to_thermometer_decoder_8b
CHECKS["v3_050_bin_to_thermometer_decoder_8b"] = check_bin_to_thermometer_decoder_8b
CHECKS["thermometer_to_binary_encoder_8b"] = check_thermometer_to_binary_encoder_8b
CHECKS["v3_051_thermometer_to_binary_encoder_8b"] = check_thermometer_to_binary_encoder_8b
CHECKS["gray_to_binary_converter_8b"] = check_gray_to_binary_converter_8b
CHECKS["v3_052_gray_to_binary_converter_8b"] = check_gray_to_binary_converter_8b
CHECKS["binary_to_gray_converter_8b"] = check_binary_to_gray_converter_8b
CHECKS["v3_053_binary_to_gray_converter_8b"] = check_binary_to_gray_converter_8b
CHECKS["onehot_to_binary_encoder_16b"] = check_onehot_to_binary_encoder_16b
CHECKS["v3_054_onehot_to_binary_encoder_16b"] = check_onehot_to_binary_encoder_16b
CHECKS["binary_to_onehot_decoder_16b"] = check_binary_to_onehot_decoder_16b
CHECKS["v3_055_binary_to_onehot_decoder_16b"] = check_binary_to_onehot_decoder_16b
CHECKS["decimal_digit_to_bcd_encoder"] = check_decimal_digit_to_bcd_encoder
CHECKS["v3_056_decimal_digit_to_bcd_encoder"] = check_decimal_digit_to_bcd_encoder
CHECKS["signed_magnitude_to_twos_complement_8b"] = check_signed_magnitude_to_twos_complement_8b
CHECKS["v3_057_signed_magnitude_to_twos_complement_8b"] = check_signed_magnitude_to_twos_complement_8b
CHECKS["config_latch_32b_clocked"] = check_config_latch_32b_clocked
CHECKS["v3_058_config_latch_32b_clocked"] = check_config_latch_32b_clocked
CHECKS["config_latch_128b_static_enable"] = check_config_latch_128b_static_enable
CHECKS["v3_059_config_latch_128b_static_enable"] = check_config_latch_128b_static_enable
CHECKS["config_shift_register_64b"] = check_config_shift_register_64b
CHECKS["v3_060_config_shift_register_64b"] = check_config_shift_register_64b
CHECKS["bus_splitter_256_to_16x16"] = check_bus_splitter_256_to_16x16
CHECKS["v3_061_bus_splitter_256_to_16x16"] = check_bus_splitter_256_to_16x16
CHECKS["bus_combiner_16x16_to_256"] = check_bus_combiner_16x16_to_256
CHECKS["v3_062_bus_combiner_16x16_to_256"] = check_bus_combiner_16x16_to_256
CHECKS["masked_config_update_32b"] = check_masked_config_update_32b
CHECKS["v3_063_masked_config_update_32b"] = check_masked_config_update_32b
CHECKS["edge_interval_tdc_8b"] = check_edge_interval_tdc_8b
CHECKS["v3_064_edge_interval_tdc_8b"] = check_edge_interval_tdc_8b
CHECKS["period_meter_16b"] = check_period_meter_16b
CHECKS["v3_065_period_meter_16b"] = check_period_meter_16b
CHECKS["duty_cycle_meter_8b"] = check_duty_cycle_meter_8b
CHECKS["v3_066_duty_cycle_meter_8b"] = check_duty_cycle_meter_8b
CHECKS["event_counter_windowed_16b"] = check_event_counter_windowed_16b
CHECKS["v3_067_event_counter_windowed_16b"] = check_event_counter_windowed_16b
CHECKS["ready_valid_latency_counter_12b"] = check_ready_valid_latency_counter_12b
CHECKS["v3_068_ready_valid_latency_counter_12b"] = check_ready_valid_latency_counter_12b
CHECKS["v3_068_latency_counter_ready_valid_12b"] = check_ready_valid_latency_counter_12b
CHECKS["settling_window_detector"] = check_settling_window_detector
CHECKS["v3_069_settling_window_detector"] = check_settling_window_detector
CHECKS["reset_sync_active_low"] = check_reset_sync_active_low
CHECKS["v3_070_active_low_reset_synchronizer"] = check_reset_sync_active_low
CHECKS["reset_sync_active_high"] = check_reset_sync_active_high
CHECKS["v3_071_active_high_reset_synchronizer"] = check_reset_sync_active_high
CHECKS["enable_gated_clock_pulse"] = check_enable_gated_clock_pulse
CHECKS["v3_072_enable_gated_clock_pulse"] = check_enable_gated_clock_pulse
CHECKS["low_active_enable_decoder_4b"] = check_low_active_enable_decoder_4b
CHECKS["v3_073_low_active_enable_decoder_4b"] = check_low_active_enable_decoder_4b
CHECKS["configurable_polarity_edge_detector"] = check_configurable_polarity_edge_detector
CHECKS["v3_074_configurable_polarity_edge_detector"] = check_configurable_polarity_edge_detector
CHECKS["prbs_generator_32b"] = check_prbs_generator_32b
CHECKS["v3_075_prbs_generator_32b_seeded"] = check_prbs_generator_32b
CHECKS["multiphase_clock_generator_4ph"] = check_multiphase_clock_generator_4ph
CHECKS["v3_076_multiphase_clock_generator_4ph"] = check_multiphase_clock_generator_4ph
CHECKS["configurable_pulse_train"] = check_configurable_pulse_train
CHECKS["v3_077_configurable_pulse_train_generator"] = check_configurable_pulse_train
CHECKS["staircase_dac_stimulus_8b"] = check_staircase_dac_stimulus_8b
CHECKS["v3_078_staircase_dac_stimulus_8b"] = check_staircase_dac_stimulus_8b
CHECKS["deterministic_jittered_clock"] = check_deterministic_jittered_clock
CHECKS["v3_079_jittered_clock_source_deterministic"] = check_deterministic_jittered_clock
CHECKS["v3_001_bang_bang_phase_detector"] = check_bbpd
CHECKS["v3_002_capacitive_weighted_sar_feedback_dac"] = check_v3_cdac_feedback_dac
CHECKS["v3_003_pipeline_adc_stage"] = check_pipeline_stage
CHECKS["v3_004_trim_calibration_controller"] = check_v3_trim_calibration_controller
CHECKS["v3_005_debounce_latch"] = check_v3_debounce_latch
CHECKS["v3_006_element_shuffler"] = check_v3_element_shuffler
CHECKS["v3_007_first_order_lowpass"] = check_vbm1_first_order_lowpass
CHECKS["v3_008_gain_trim_controller"] = check_v3_gain_trim_controller
CHECKS["v3_009_lock_detector"] = check_v3_009_lock_detector
CHECKS["v3_010_offset_comparator"] = check_v3_offset_comparator
CHECKS["v3_011_pfd_up_dn_logic"] = check_pfd_reset_race
CHECKS["v3_012_clock_divider"] = check_clk_divider
CHECKS["v3_013_resettable_integrator"] = check_vbm1_resettable_integrator
CHECKS["v3_014_sar_logic"] = check_vbm1_sar_logic_4b
CHECKS["v3_015_segmented_dac"] = check_vbm1_segmented_dac
CHECKS["v3_016_binary_weighted_voltage_dac"] = check_simple_binary_dac_4b
CHECKS["v3_017_slew_rate_limiter"] = check_vbm1_slew_rate_limiter
CHECKS["v3_018_strongarm_style_latch_comparator"] = check_release_strongarm_latch_comparator
CHECKS["v3_019_unit_element_thermometer_dac"] = check_vbm1_thermometer_dac_15seg
CHECKS["v3_020_thermometer_code_decoder"] = check_vbm1_thermometer_decoder_guarded
CHECKS["v3_021_vco_phase_integrator"] = check_vbm1_vco_phase_integrator
CHECKS["v3_022_bandgap_reference_macro_model"] = check_bandgap_reference_macro_model
CHECKS["v3_023_calibration_deadband_controller"] = check_release_deadband_calibration
CHECKS["v3_024_charge_pump_abstraction"] = check_release_charge_pump
CHECKS["v3_025_clocked_adc_quantizer"] = check_flash_adc_3b
CHECKS["v3_026_clocked_sample_and_hold"] = check_sample_hold
CHECKS["v3_027_dac_mismatch_unit_weighting_model"] = check_release_dac_mismatch_unit_weighting
CHECKS["v3_028_digital_phase_accumulator_with_modulo_wrap"] = check_phase_accumulator_timer_wrap
CHECKS["v3_029_dwa_dem_encoder"] = check_dwa_dem_encoder_release
CHECKS["v3_030_higher_order_filter"] = check_release_two_pole_filter
CHECKS["v3_031_hysteresis_comparator"] = check_cmp_hysteresis
CHECKS["v3_032_ldo_regulator_macro_model"] = check_ldo_regulator_macro_model
CHECKS["v3_033_limiting_amplifier_frontend"] = check_limiting_amplifier_frontend
CHECKS["v3_034_lna_gain_compression_macro"] = check_lna_gain_compression_macro
CHECKS["v3_035_log_rssi_power_detector"] = check_log_rssi_power_detector
CHECKS["v3_036_loop_filter_abstraction"] = check_release_loop_filter
CHECKS["v3_037_pa_compression_macro"] = check_pa_compression_macro
CHECKS["v3_038_power_on_reset_detector"] = check_power_on_reset_detector
CHECKS["v3_039_precision_rectifier_envelope_detector"] = check_precision_rectifier_envelope_detector
CHECKS["v3_040_programmable_gain_amplifier"] = check_programmable_gain_amplifier
CHECKS["v3_041_propagation_delay_comparator"] = check_cmp_delay
CHECKS["v3_042_ptat_ctat_reference_generator"] = check_ptat_ctat_reference_generator
CHECKS["v3_043_rf_mixer_downconverter_macro"] = check_rf_mixer_downconverter_macro
CHECKS["v3_044_sample_and_hold_with_droop_leakage"] = check_release_vin_sampled_droop_hold
CHECKS["v3_045_soft_hysteretic_limiter"] = check_release_soft_hysteretic_limiter
CHECKS["v3_046_successive_approximation_calibration_search_fsm"] = check_release_sar_calibration_fsm
CHECKS["v3_047_threshold_comparator"] = check_release_threshold_comparator
CHECKS["v3_048_uvlo_brownout_detector"] = check_uvlo_brownout_detector
CHECKS["v3_049_window_comparator_detector"] = check_true_window_comparator
CHECKS["v3_080_acquisition_limited_sample_and_hold"] = check_acquisition_limited_sample_hold
CHECKS["v3_081_aperture_delay_track_and_hold"] = check_vbm1_track_hold_aperture
CHECKS["v3_082_bias_voltage_generator_with_enable_trim"] = check_bias_voltage_generator_with_enable_trim
CHECKS["v3_083_crossing_metric_writer"] = check_vbm1_file_metric_writer
CHECKS["v3_084_peak_detector"] = check_vbm1_peak_detector
CHECKS["v3_085_burst_clock_source"] = check_clk_burst_gen
CHECKS["v3_086_dither_noise_like_deterministic_source"] = check_noise_gen
CHECKS["v3_087_lfsr_prbs_generator"] = check_prbs7
CHECKS["v3_088_ramp_step_source"] = check_bound_step_period_guard
CHECKS["v3_089_sine_periodic_voltage_source"] = check_multitone
CHECKS["080-acquisition-limited-sample-and-hold"] = check_acquisition_limited_sample_hold
CHECKS["081-aperture-delay-track-and-hold"] = check_vbm1_track_hold_aperture
CHECKS["082-bias-voltage-generator-with-enable-trim"] = check_bias_voltage_generator_with_enable_trim
CHECKS["083-crossing-metric-writer"] = check_vbm1_file_metric_writer
CHECKS["084-peak-detector"] = check_vbm1_peak_detector
CHECKS["085-burst-clock-source"] = check_clk_burst_gen
CHECKS["086-dither-noise-like-deterministic-source"] = check_noise_gen
CHECKS["087-lfsr-prbs-generator"] = check_prbs7
CHECKS["088-ramp-step-source"] = check_bound_step_period_guard
CHECKS["089-sine-periodic-voltage-source"] = check_multitone
CHECKS["112-source-clocked-sar-comparator"] = check_v3_source_clocked_sar_comparator
CHECKS["113-source-clocked-dac-restore-4b"] = check_v3_source_clocked_dac_restore_4b
CHECKS["114-source-sample-and-hold-ideal"] = check_v3_source_sample_hold
CHECKS["115-source-single-shot-pulse"] = check_v3_source_single_shot
CHECKS["116-source-clocked-comparator-reset-low"] = check_v3_source_clocked_comparator_reset_low
CHECKS["117-source-bipolar-dac-4b-continuous"] = check_v3_source_bipolar_dac_4b_continuous
CHECKS["118-source-clocked-dac-restore-7b"] = check_v3_source_clocked_dac_restore_7b
CHECKS["119-source-crossing-pulse-detector"] = check_v3_source_crossing_pulse_detector
CHECKS["120-source-not-gate-voltage"] = check_v3_source_not_gate
CHECKS["121-source-dff-reset-voltage"] = check_v3_source_dff_reset
CHECKS["122-source-offset-search-comparator"] = check_v3_source_offset_search_comparator
CHECKS["123-source-start-gated-offset-search"] = check_v3_source_start_gated_offset_search
CHECKS["124-source-comp-os-detect"] = check_v3_source_comp_os_detect
CHECKS["125-source-clocked-dac-4b-binary"] = check_v3_source_clocked_dac_4b_binary
CHECKS["126-source-latched-comparator-delay"] = check_v3_source_latched_comparator_delay
CHECKS["127-source-sar-weighted-sum"] = check_v3_source_sar_weighted_sum
CHECKS["128-source-two-input-and-gate"] = check_v3_source_two_input_and_gate
CHECKS["129-source-two-input-xor-gate"] = check_v3_source_two_input_xor_gate
CHECKS["130-source-analog-mux-threshold"] = check_v3_source_analog_mux_threshold
CHECKS["131-source-two-bit-counter-marker"] = check_v3_source_two_bit_counter_marker
CHECKS["132-source-max-detector-hold"] = check_v3_source_max_detector_hold
CHECKS["133-source-time-diff-detector"] = check_v3_source_time_diff_detector
CHECKS["134-source-differential-buffer"] = check_v3_source_differential_buffer
CHECKS["135-source-two-input-or-gate"] = check_v3_source_two_input_or_gate
CHECKS["136-source-sar-cdac-residue"] = check_v3_source_sar_cdac_residue
CHECKS["137-source-two-input-nand-gate"] = check_v3_source_two_input_nand_gate
CHECKS["138-source-two-input-nor-gate"] = check_v3_source_two_input_nor_gate
CHECKS["139-source-three-input-and-gate"] = check_v3_source_three_input_and_gate
CHECKS["140-source-three-input-or-gate"] = check_v3_source_three_input_or_gate
CHECKS["141-source-three-input-xor-gate"] = check_v3_source_three_input_xor_gate
CHECKS["167-source-ideal-adc-4bit-quantizer"] = check_v3_source_ideal_adc_4bit_quantizer
CHECKS["168-source-ideal-dac-4bit-differential"] = check_v3_source_ideal_dac_4bit_differential
CHECKS["169-source-two-period-sample-delay"] = check_v3_source_two_period_sample_delay
CHECKS["170-source-clocked-four-input-mux"] = check_v3_source_clocked_four_input_mux
CHECKS["171-source-divide-by-eight-clock"] = check_v3_source_divide_by_eight_clock
CHECKS["172-source-flash-thermometer-centered-sum"] = check_v3_source_flash_thermometer_centered_sum
CHECKS["173-source-weighted-sar-decoder-9b"] = check_v3_source_weighted_sar_decoder_9b
CHECKS["174-source-control-word-encoder-7b"] = check_v3_source_control_word_encoder_7b
CHECKS["175-source-four-channel-edge-sampler"] = check_v3_source_four_channel_edge_sampler
CHECKS["176-source-dual-modulus-divider-16-17"] = check_v3_source_dual_modulus_divider_16_17
CHECKS["177-source-sar-5bit-serial-decoder"] = check_v3_source_sar_5bit_serial_decoder
CHECKS["178-source-cyclic-decoder-12bit"] = check_v3_source_cyclic_decoder_12bit
CHECKS["179-source-flash-8level-sum-delay"] = check_v3_source_flash_8level_sum_delay
CHECKS["180-source-flash-sum8-fraction"] = check_v3_source_flash_sum8_fraction
CHECKS["181-source-two-channel-sample-demux"] = check_v3_source_two_channel_sample_demux
CHECKS["182-source-differential-dac-calc-6b"] = check_v3_source_differential_dac_calc_6b
CHECKS["183-source-flash-adc-threshold-taps"] = check_v3_source_flash_adc_threshold_taps
CHECKS["184-source-divide-by-two-toggle"] = check_v3_source_divide_by_two_toggle
CHECKS["185-source-dac-5v-weighted-7b"] = check_v3_source_dac_5v_weighted_7b
CHECKS["186-source-folded-flash-dac-4b"] = check_v3_source_folded_flash_dac_4b
CHECKS["187-source-ref-flash-8level-decoder"] = check_v3_source_ref_flash_8level_decoder
CHECKS["188-source-ref-flash-15level-decoder"] = check_v3_source_ref_flash_15level_decoder
CHECKS["189-source-divide-by-8-9-switch"] = check_v3_source_divide_by_8_9_switch
CHECKS["190-source-dac-restore-10bit-offset"] = check_v3_source_dac_restore_10bit_offset
CHECKS["191-source-dac-8bit-ideal-scalar"] = check_v3_source_dac_8bit_ideal_scalar
CHECKS["192-source-flash-data-align-pipeline"] = check_v3_source_flash_data_align_pipeline
CHECKS["193-source-cyclic-decoder-10b"] = check_v3_source_cyclic_decoder_10b
CHECKS["194-source-ideal-adc-out-7bits"] = check_v3_source_ideal_adc_out_7bits
CHECKS["195-source-va-lx-adc-ideal-4b"] = check_v3_source_va_lx_adc_ideal_4b
CHECKS["196-source-va-lx-dac-ideal-4b"] = check_v3_source_va_lx_dac_ideal_4b
CHECKS["197-source-l1-dac-4b-bipolar"] = check_v3_source_l1_dac_4b_bipolar
CHECKS["198-source-l2-cdac-4b-residue"] = check_v3_source_l2_cdac_4b_residue
CHECKS["199-source-ideal-clkmux-8channel"] = check_v3_source_ideal_clkmux_8channel
CHECKS["200-source-dac-ideal-4b-offset"] = check_v3_source_dac_ideal_4b_offset
CHECKS["201-source-linear-pfd-gain"] = check_v3_source_linear_pfd_gain
CHECKS["202-source-l2-cmp-ideal-clocked"] = check_v3_source_l2_cmp_ideal_clocked
CHECKS["203-source-comparator-offset-driver"] = check_v3_source_comparator_offset_driver
CHECKS["204-source-pipe-2lane-edge-align"] = check_v3_source_pipe_2lane_edge_align
CHECKS["205-source-dac-serial-accumulator"] = check_v3_source_dac_serial_accumulator
CHECKS["206-source-sar-sum-weighted-11b"] = check_v3_source_sar_sum_weighted_11b
CHECKS["207-source-iterative-isar-dac"] = check_v3_source_iterative_isar_dac
CHECKS["218-source-foreground-rdac-calibrator"] = check_v3_source_foreground_rdac_calibrator
CHECKS["219-source-offset-rdac-search-flow"] = check_v3_source_offset_rdac_search_flow
CHECKS["220-source-spi-shift-mux"] = check_v3_source_spi_shift_mux
CHECKS["221-source-dff-set-reset-hold"] = check_v3_source_dff_set_reset_hold
CHECKS["222-source-sarfend-logic-4b"] = check_v3_source_sarfend_logic_4b
CHECKS["223-source-adc-sample-clock-sequencer"] = check_v3_source_adc_sample_clock_sequencer
CHECKS["224-source-pipeline-counter-onehot"] = check_v3_source_pipeline_counter_onehot
CHECKS["225-source-cdac-bidirect-residue"] = check_v3_source_cdac_bidirect_residue
CHECKS["226-source-pfd-reset-pulse"] = check_v3_source_pfd_reset_pulse
CHECKS["227-source-trim-ctrl-4bit"] = check_v3_source_trim_ctrl_4bit
CHECKS["228-source-linearity-rdac-offset-sweep"] = check_v3_source_linearity_rdac_offset_sweep
CHECKS["229-source-sar-das-logic-6b"] = check_v3_source_sar_das_logic_6b
CHECKS["230-source-sar-logic-4b-self-timed"] = check_v3_source_sar_logic_4b_self_timed
CHECKS["231-source-pfd-tdomain-reset-window"] = check_v3_source_pfd_tdomain_reset_window
CHECKS["232-source-pipe-adc-gain-control-loop"] = check_v3_source_pipe_adc_gain_control_loop
CHECKS["233-source-clock-sample-1600n-sequencer"] = check_v3_source_clock_sample_1600n_sequencer
CHECKS["234-source-l2-sar-logic-4b"] = check_v3_source_l2_sar_logic_4b
CHECKS["235-source-phase-detector-chopper"] = check_v3_source_phase_detector_chopper
CHECKS["236-source-single-adc-7b-weighted"] = check_v3_source_single_adc_7b_weighted
CHECKS["237-source-qtz-differential-2level"] = check_v3_source_qtz_differential_2level
CHECKS["238-source-l2-7b-dac-ready"] = check_v3_source_l2_7b_dac_ready
CHECKS["239-source-l2-cdac-4b-switch"] = check_v3_source_l2_cdac_4b_switch
CHECKS["240-source-cdac-monodown-7b"] = check_v3_source_cdac_monodown_7b
CHECKS["241-source-cdac-6b-stage1-up"] = check_v3_source_cdac_6b_stage1_up
CHECKS["242-source-adc-zoom-timing-sequencer"] = check_v3_source_adc_zoom_timing_sequencer
CHECKS["v3_source_l2_sar_logic_7b"] = check_v3_source_l2_sar_logic_7b
CHECKS["v3_source_l3_sar2_logic_7b"] = check_v3_source_l3_sar2_logic_7b
CHECKS["v3_source_cdac_8b_monodown"] = check_v3_source_cdac_8b_monodown
CHECKS["v3_source_va_dac_6b_se"] = check_v3_source_va_dac_6b_se
CHECKS["v3_source_offset_halving_search"] = check_v3_source_offset_halving_search
CHECKS["243-source-l2-sar-logic-7b"] = check_v3_source_l2_sar_logic_7b
CHECKS["244-source-l3-sar2-logic-7b"] = check_v3_source_l3_sar2_logic_7b
CHECKS["245-source-cdac-8b-monodown"] = check_v3_source_cdac_8b_monodown
CHECKS["246-source-va-dac-6b-se"] = check_v3_source_va_dac_6b_se
CHECKS["247-source-offset-halving-search"] = check_v3_source_offset_halving_search
CHECKS["v3_source_sar_comparator_reset_high"] = check_v3_source_sar_comparator_reset_high
CHECKS["v3_source_dac_restore_4bit_clocked"] = check_v3_source_dac_restore_4bit_clocked
CHECKS["v3_source_dac_restore_7bit_clocked"] = check_v3_source_dac_restore_7bit_clocked
CHECKS["v3_source_dac_restore_6bit_1p8"] = check_v3_source_dac_restore_6bit_1p8
CHECKS["v3_source_sample_hold_5v_clock"] = check_v3_source_sample_hold_5v_clock
CHECKS["248-source-sar-comparator-reset-high"] = check_v3_source_sar_comparator_reset_high
CHECKS["249-source-dac-restore-4bit-clocked"] = check_v3_source_dac_restore_4bit_clocked
CHECKS["250-source-dac-restore-7bit-clocked"] = check_v3_source_dac_restore_7bit_clocked
CHECKS["251-source-dac-restore-6bit-1p8"] = check_v3_source_dac_restore_6bit_1p8
CHECKS["252-source-sample-hold-5v-clock"] = check_v3_source_sample_hold_5v_clock
CHECKS["v3_source_sum5_signed_sar_weight"] = check_v3_source_sum5_signed_sar_weight
CHECKS["v3_source_lt_readout_sar4"] = check_v3_source_lt_readout_sar4
CHECKS["v3_source_tool_4bit_sar_signed_dac"] = check_v3_source_tool_4bit_sar_signed_dac
CHECKS["v3_source_dac4bit_small_swing"] = check_v3_source_dac4bit_small_swing
CHECKS["v3_source_comparator_reset_low_1p8"] = check_v3_source_comparator_reset_low_1p8
CHECKS["253-source-sum5-signed-sar-weight"] = check_v3_source_sum5_signed_sar_weight
CHECKS["254-source-lt-readout-sar4"] = check_v3_source_lt_readout_sar4
CHECKS["255-source-tool-4bit-sar-signed-dac"] = check_v3_source_tool_4bit_sar_signed_dac
CHECKS["256-source-dac4bit-small-swing"] = check_v3_source_dac4bit_small_swing
CHECKS["257-source-comparator-reset-low-1p8"] = check_v3_source_comparator_reset_low_1p8
CHECKS["v3_source_lt_read_sar6b_weighted"] = check_v3_source_lt_read_sar6b_weighted
CHECKS["v3_source_lt_read_sar7b_weighted"] = check_v3_source_lt_read_sar7b_weighted
CHECKS["v3_source_dac_serial_16b_nobridge"] = check_v3_source_dac_serial_16b_nobridge
CHECKS["v3_source_sar_13bit_serial_decoder"] = check_v3_source_sar_13bit_serial_decoder
CHECKS["v3_source_single_shot_timer_pulse"] = check_v3_source_single_shot_timer_pulse
CHECKS["258-source-lt-read-sar6b-weighted"] = check_v3_source_lt_read_sar6b_weighted
CHECKS["259-source-lt-read-sar7b-weighted"] = check_v3_source_lt_read_sar7b_weighted
CHECKS["260-source-dac-serial-16b-nobridge"] = check_v3_source_dac_serial_16b_nobridge
CHECKS["261-source-sar-13bit-serial-decoder"] = check_v3_source_sar_13bit_serial_decoder
CHECKS["262-source-single-shot-timer-pulse"] = check_v3_source_single_shot_timer_pulse
CHECKS["v3_source_clocked_comparator_dual_output"] = check_v3_source_clocked_comparator_dual_output
CHECKS["v3_source_dac4bit_bipolar_252m"] = check_v3_source_dac4bit_bipolar_252m
CHECKS["v3_source_bin2ther_2b"] = check_v3_source_bin2ther_2b
CHECKS["v3_source_dff_set_reset"] = check_v3_source_dff_set_reset
CHECKS["v3_source_pfd_up_down_state"] = check_v3_source_pfd_up_down_state
CHECKS["263-source-clocked-comparator-dual-output"] = check_v3_source_clocked_comparator_dual_output
CHECKS["264-source-dac4bit-bipolar-252m"] = check_v3_source_dac4bit_bipolar_252m
CHECKS["265-source-bin2ther-2b"] = check_v3_source_bin2ther_2b
CHECKS["266-source-dff-set-reset"] = check_v3_source_dff_set_reset
CHECKS["267-source-pfd-up-down-state"] = check_v3_source_pfd_up_down_state
CHECKS["v3_source_samplehold_rising_edge"] = check_v3_source_samplehold_rising_edge
CHECKS["v3_source_trim_ctrl_5bit"] = check_v3_source_trim_ctrl_5bit
CHECKS["v3_source_therm8_to_bin4_count"] = check_v3_source_therm8_to_bin4_count
CHECKS["v3_source_coarse_qtz_3bit_residue"] = check_v3_source_coarse_qtz_3bit_residue
CHECKS["v3_source_rs_phase_detector"] = check_v3_source_rs_phase_detector
CHECKS["v3_source_level_shifter_offset"] = check_v3_source_level_shifter_offset
CHECKS["v3_source_weighted_decoder_6bit"] = check_v3_source_weighted_decoder_6bit
CHECKS["v3_source_divide_by_two_toggle_v2"] = check_v3_source_divide_by_two_toggle_v2
CHECKS["v3_source_accum3_pulse"] = check_v3_source_accum3_pulse
CHECKS["v3_source_xor_phase_detector"] = check_v3_source_xor_phase_detector
CHECKS["v3_source_decision_router_logic"] = check_v3_source_decision_router_logic
CHECKS["v3_source_safe_analog_divider"] = check_v3_source_safe_analog_divider
CHECKS["v3_source_vargain_diffamp_clip"] = check_v3_source_vargain_diffamp_clip
CHECKS["v3_source_programmable_divider_by_n"] = check_v3_source_programmable_divider_by_n
CHECKS["v3_source_pfd_timer_reset"] = check_v3_source_pfd_timer_reset
CHECKS["268-source-samplehold-rising-edge"] = check_v3_source_samplehold_rising_edge
CHECKS["269-source-trim-ctrl-5bit"] = check_v3_source_trim_ctrl_5bit
CHECKS["270-source-therm8-to-bin4-count"] = check_v3_source_therm8_to_bin4_count
CHECKS["271-source-coarse-qtz-3bit-residue"] = check_v3_source_coarse_qtz_3bit_residue
CHECKS["272-source-rs-phase-detector"] = check_v3_source_rs_phase_detector
CHECKS["273-source-level-shifter-offset"] = check_v3_source_level_shifter_offset
CHECKS["274-source-weighted-decoder-6bit"] = check_v3_source_weighted_decoder_6bit
CHECKS["275-source-divide-by-two-toggle"] = check_v3_source_divide_by_two_toggle_v2
CHECKS["276-source-accum3-pulse"] = check_v3_source_accum3_pulse
CHECKS["277-source-xor-phase-detector"] = check_v3_source_xor_phase_detector
CHECKS["278-source-decision-router-logic"] = check_v3_source_decision_router_logic
CHECKS["279-source-safe-analog-divider"] = check_v3_source_safe_analog_divider
CHECKS["280-source-vargain-diffamp-clip"] = check_v3_source_vargain_diffamp_clip
CHECKS["281-source-programmable-divider-by-n"] = check_v3_source_programmable_divider_by_n
CHECKS["282-source-pfd-timer-reset"] = check_v3_source_pfd_timer_reset
CHECKS["v3_source_absolute_value"] = check_v3_source_absolute_value
CHECKS["v3_source_deadband_voltage"] = check_v3_source_deadband_voltage
CHECKS["v3_source_deadband_diffamp"] = check_v3_source_deadband_diffamp
CHECKS["v3_source_limiting_diffamp"] = check_v3_source_limiting_diffamp
CHECKS["v3_source_smooth_tanh_comparator"] = check_v3_source_smooth_tanh_comparator
CHECKS["v3_source_flash_folded_dac4"] = check_v3_source_flash_folded_dac4
CHECKS["v3_source_subradix_dac10"] = check_v3_source_subradix_dac10
CHECKS["v3_source_clocked_adc3bit"] = check_v3_source_clocked_adc3bit
CHECKS["v3_source_cal4bit_modulo"] = check_v3_source_cal4bit_modulo
CHECKS["v3_source_mux4_priority"] = check_v3_source_mux4_priority
CHECKS["v3_source_xnor_gate_voltage"] = check_v3_source_xnor_gate_voltage
CHECKS["v3_source_bipolar_dff_sample"] = check_v3_source_bipolar_dff_sample
CHECKS["v3_source_pfd_active_low_reset"] = check_v3_source_pfd_active_low_reset
CHECKS["v3_288_source_absolute_value"] = check_v3_source_absolute_value
CHECKS["v3_289_source_deadband_voltage"] = check_v3_source_deadband_voltage
CHECKS["v3_290_source_deadband_diffamp"] = check_v3_source_deadband_diffamp
CHECKS["v3_291_source_limiting_diffamp"] = check_v3_source_limiting_diffamp
CHECKS["v3_292_source_smooth_tanh_comparator"] = check_v3_source_smooth_tanh_comparator
CHECKS["v3_293_source_flash_folded_dac4"] = check_v3_source_flash_folded_dac4
CHECKS["v3_294_source_subradix_dac10"] = check_v3_source_subradix_dac10
CHECKS["v3_295_source_clocked_adc3bit"] = check_v3_source_clocked_adc3bit
CHECKS["v3_296_source_cal4bit_modulo"] = check_v3_source_cal4bit_modulo
CHECKS["v3_297_source_mux4_priority"] = check_v3_source_mux4_priority
CHECKS["v3_298_source_xnor_gate_voltage"] = check_v3_source_xnor_gate_voltage
CHECKS["v3_299_source_bipolar_dff_sample"] = check_v3_source_bipolar_dff_sample
CHECKS["v3_300_source_pfd_active_low_reset"] = check_v3_source_pfd_active_low_reset
CHECKS["288-source-absolute-value"] = check_v3_source_absolute_value
CHECKS["289-source-deadband-voltage"] = check_v3_source_deadband_voltage
CHECKS["290-source-deadband-diffamp"] = check_v3_source_deadband_diffamp
CHECKS["291-source-limiting-diffamp"] = check_v3_source_limiting_diffamp
CHECKS["292-source-smooth-tanh-comparator"] = check_v3_source_smooth_tanh_comparator
CHECKS["293-source-flash-folded-dac4"] = check_v3_source_flash_folded_dac4
CHECKS["294-source-subradix-dac10"] = check_v3_source_subradix_dac10
CHECKS["295-source-clocked-adc3bit"] = check_v3_source_clocked_adc3bit
CHECKS["296-source-cal4bit-modulo"] = check_v3_source_cal4bit_modulo
CHECKS["297-source-mux4-priority"] = check_v3_source_mux4_priority
CHECKS["298-source-xnor-gate-voltage"] = check_v3_source_xnor_gate_voltage
CHECKS["299-source-bipolar-dff-sample"] = check_v3_source_bipolar_dff_sample
CHECKS["300-source-pfd-active-low-reset"] = check_v3_source_pfd_active_low_reset
# Source task.toml id aliases generated from v3 task metadata.
SOURCE_TASK_ID_ALIASES = {
    "v3_112_source_clocked_sar_comparator": "v3_source_clocked_sar_comparator",
    "v3_113_source_clocked_dac_restore_4b": "v3_source_clocked_dac_restore_4b",
    "v3_114_source_sample_and_hold_ideal": "v3_source_sample_hold",
    "v3_115_source_single_shot_pulse": "v3_source_single_shot",
    "v3_116_source_clocked_comparator_reset_low": "v3_source_clocked_comparator_reset_low",
    "v3_117_source_bipolar_dac_4b_continuous": "v3_source_bipolar_dac_4b_continuous",
    "v3_118_source_clocked_dac_restore_7b": "v3_source_clocked_dac_restore_7b",
    "v3_119_source_crossing_pulse_detector": "v3_source_crossing_pulse_detector",
    "v3_120_source_not_gate_voltage": "v3_source_not_gate",
    "v3_121_source_dff_reset_voltage": "v3_source_dff_reset",
    "v3_122_source_offset_search_comparator": "v3_source_offset_search_comparator",
    "v3_123_source_start_gated_offset_search": "v3_source_start_gated_offset_search",
    "v3_124_source_comp_os_detect": "v3_source_comp_os_detect",
    "v3_125_source_clocked_dac_4b_binary": "v3_source_clocked_dac_4b_binary",
    "v3_126_source_latched_comparator_delay": "v3_source_latched_comparator_delay",
    "v3_127_source_sar_weighted_sum": "v3_source_sar_weighted_sum",
    "v3_128_source_two_input_and_gate": "v3_source_two_input_and_gate",
    "v3_129_source_two_input_xor_gate": "v3_source_two_input_xor_gate",
    "v3_130_source_analog_mux_threshold": "v3_source_analog_mux_threshold",
    "v3_131_source_two_bit_counter_marker": "v3_source_two_bit_counter_marker",
    "v3_132_source_max_detector_hold": "v3_source_max_detector_hold",
    "v3_133_source_time_diff_detector": "v3_source_time_diff_detector",
    "v3_134_source_differential_buffer": "v3_source_differential_buffer",
    "v3_135_source_two_input_or_gate": "v3_source_two_input_or_gate",
    "v3_136_source_sar_cdac_residue": "v3_source_sar_cdac_residue",
    "v3_137_source_two_input_nand_gate": "v3_source_two_input_nand_gate",
    "v3_138_source_two_input_nor_gate": "v3_source_two_input_nor_gate",
    "v3_139_source_three_input_and_gate": "v3_source_three_input_and_gate",
    "v3_140_source_three_input_or_gate": "v3_source_three_input_or_gate",
    "v3_141_source_three_input_xor_gate": "v3_source_three_input_xor_gate",
    "v3_142_source_attenuator_gain": "v3_source_attenuator_gain",
    "v3_143_source_deadband_window": "v3_source_deadband_window",
    "v3_144_source_differential_deadband": "v3_source_differential_deadband",
    "v3_145_source_hard_voltage_clamp": "v3_source_hard_voltage_clamp",
    "v3_146_source_smooth_comparator_tanh": "v3_source_smooth_comparator_tanh",
    "v3_147_source_limiter_rails": "v3_source_limiter_rails",
    "v3_148_source_absolute_value": "v3_source_absolute_value",
    "v3_149_source_offset_gain_amplifier": "v3_source_offset_gain_amplifier",
    "v3_150_source_safe_voltage_divider": "v3_source_safe_voltage_divider",
    "v3_151_source_polynomial_differential_vcvs": "v3_source_polynomial_differential_vcvs",
    "v3_152_source_differential_gain_driver": "v3_source_differential_gain_driver",
    "v3_153_source_limiting_differential_amplifier": "v3_source_limiting_differential_amplifier",
    "v3_154_source_analog_multiplier": "v3_source_analog_multiplier",
    "v3_155_source_three_way_threshold_mux": "v3_source_three_way_threshold_mux",
    "v3_156_source_differential_amplifier_core": "v3_source_differential_amplifier_core",
    "v3_157_source_logarithmic_amplifier": "v3_source_logarithmic_amplifier",
    "v3_158_source_soft_voltage_clamp": "v3_source_soft_voltage_clamp",
    "v3_159_source_variable_gain_differential_amplifier": "v3_source_variable_gain_differential_amplifier",
    "v3_160_source_voltage_controlled_gain_amplifier": "v3_source_voltage_controlled_gain_amplifier",
    "v3_161_source_ideal_differential_opamp": "v3_source_ideal_differential_opamp",
    "v3_162_source_half_adder_logic": "v3_source_half_adder_logic",
    "v3_163_source_full_adder_logic": "v3_source_full_adder_logic",
    "v3_164_source_half_subtractor_logic": "v3_source_half_subtractor_logic",
    "v3_165_source_full_subtractor_logic": "v3_source_full_subtractor_logic",
    "v3_166_source_rs_latch_voltage": "v3_source_rs_latch_voltage",
    "v3_167_source_ideal_adc_4bit_quantizer": "v3_source_ideal_adc_4bit_quantizer",
    "v3_168_source_ideal_dac_4bit_differential": "v3_source_ideal_dac_4bit_differential",
    "v3_169_source_two_period_sample_delay": "v3_source_two_period_sample_delay",
    "v3_170_source_clocked_four_input_mux": "v3_source_clocked_four_input_mux",
    "v3_171_source_divide_by_eight_clock": "v3_source_divide_by_eight_clock",
    "v3_172_source_flash_thermometer_centered_sum": "v3_source_flash_thermometer_centered_sum",
    "v3_173_source_weighted_sar_decoder_9b": "v3_source_weighted_sar_decoder_9b",
    "v3_174_source_control_word_encoder_7b": "v3_source_control_word_encoder_7b",
    "v3_175_source_four_channel_edge_sampler": "v3_source_four_channel_edge_sampler",
    "v3_176_source_dual_modulus_divider_16_17": "v3_source_dual_modulus_divider_16_17",
    "v3_177_source_sar_5bit_serial_decoder": "v3_source_sar_5bit_serial_decoder",
    "v3_178_source_cyclic_decoder_12bit": "v3_source_cyclic_decoder_12bit",
    "v3_179_source_flash_8level_sum_delay": "v3_source_flash_8level_sum_delay",
    "v3_180_source_flash_sum8_fraction": "v3_source_flash_sum8_fraction",
    "v3_181_source_two_channel_sample_demux": "v3_source_two_channel_sample_demux",
    "v3_182_source_differential_dac_calc_6b": "v3_source_differential_dac_calc_6b",
    "v3_183_source_flash_adc_threshold_taps": "v3_source_flash_adc_threshold_taps",
    "v3_184_source_divide_by_two_toggle": "v3_source_divide_by_two_toggle",
    "v3_185_source_dac_5v_weighted_7b": "v3_source_dac_5v_weighted_7b",
    "v3_186_source_folded_flash_dac_4b": "v3_source_folded_flash_dac_4b",
    "v3_187_source_ref_flash_8level_decoder": "v3_source_ref_flash_8level_decoder",
    "v3_188_source_ref_flash_15level_decoder": "v3_source_ref_flash_15level_decoder",
    "v3_189_source_divide_by_8_9_switch": "v3_source_divide_by_8_9_switch",
    "v3_190_source_dac_restore_10bit_offset": "v3_source_dac_restore_10bit_offset",
    "v3_191_source_dac_8bit_ideal_scalar": "v3_source_dac_8bit_ideal_scalar",
    "v3_192_source_flash_data_align_pipeline": "v3_source_flash_data_align_pipeline",
    "v3_193_source_cyclic_decoder_10b": "v3_source_cyclic_decoder_10b",
    "v3_194_source_ideal_adc_out_7bits": "v3_source_ideal_adc_out_7bits",
    "v3_195_source_va_lx_adc_ideal_4b": "v3_source_va_lx_adc_ideal_4b",
    "v3_196_source_va_lx_dac_ideal_4b": "v3_source_va_lx_dac_ideal_4b",
    "v3_197_source_l1_dac_4b_bipolar": "v3_source_l1_dac_4b_bipolar",
    "v3_198_source_l2_cdac_4b_residue": "v3_source_l2_cdac_4b_residue",
    "v3_199_source_ideal_clkmux_8channel": "v3_source_ideal_clkmux_8channel",
    "v3_200_source_dac_ideal_4b_offset": "v3_source_dac_ideal_4b_offset",
    "v3_201_source_linear_pfd_gain": "v3_source_linear_pfd_gain",
    "v3_202_source_l2_cmp_ideal_clocked": "v3_source_l2_cmp_ideal_clocked",
    "v3_203_source_comparator_offset_driver": "v3_source_comparator_offset_driver",
    "v3_204_source_pipe_2lane_edge_align": "v3_source_pipe_2lane_edge_align",
    "v3_205_source_dac_serial_accumulator": "v3_source_dac_serial_accumulator",
    "v3_206_source_sar_sum_weighted_11b": "v3_source_sar_sum_weighted_11b",
    "v3_207_source_iterative_isar_dac": "v3_source_iterative_isar_dac",
    "v3_208_source_offset_bisection_driver": "v3_source_offset_bisection_driver",
    "v3_209_source_weighted_decoder_7b5": "v3_source_weighted_decoder_7b5",
    "v3_210_source_toggle_flip_flop": "v3_source_toggle_flip_flop",
    "v3_211_source_sync_8b_dffs_v2": "v3_source_sync_8b_dffs_v2",
    "v3_212_source_onehot_progress_encoder": "v3_source_onehot_progress_encoder",
    "v3_213_source_tdc_ideal_edge_delta": "v3_source_tdc_ideal_edge_delta",
    "v3_214_source_foreground_cload_calibrator": "v3_source_foreground_cload_calibrator",
    "v3_215_source_pipe15_data_align": "v3_source_pipe15_data_align",
    "v3_216_source_clocked_mux4_sampler": "v3_source_clocked_mux4_sampler",
    "v3_217_source_dac7_code_generator": "v3_source_dac7_code_generator",
    "v3_218_source_foreground_rdac_calibrator": "v3_source_foreground_rdac_calibrator",
    "v3_219_source_offset_rdac_search_flow": "v3_source_offset_rdac_search_flow",
    "v3_220_source_spi_shift_mux": "v3_source_spi_shift_mux",
    "v3_221_source_dff_set_reset_hold": "v3_source_dff_set_reset_hold",
    "v3_222_source_sarfend_logic_4b": "v3_source_sarfend_logic_4b",
    "v3_223_source_adc_sample_clock_sequencer": "v3_source_adc_sample_clock_sequencer",
    "v3_224_source_pipeline_counter_onehot": "v3_source_pipeline_counter_onehot",
    "v3_225_source_cdac_bidirect_residue": "v3_source_cdac_bidirect_residue",
    "v3_226_source_pfd_reset_pulse": "v3_source_pfd_reset_pulse",
    "v3_227_source_trim_ctrl_4bit": "v3_source_trim_ctrl_4bit",
    "v3_228_source_linearity_rdac_offset_sweep": "v3_source_linearity_rdac_offset_sweep",
    "v3_229_source_sar_das_logic_6b": "v3_source_sar_das_logic_6b",
    "v3_230_source_sar_logic_4b_self_timed": "v3_source_sar_logic_4b_self_timed",
    "v3_231_source_pfd_tdomain_reset_window": "v3_source_pfd_tdomain_reset_window",
    "v3_232_source_pipe_adc_gain_control_loop": "v3_source_pipe_adc_gain_control_loop",
    "v3_233_source_clock_sample_1600n_sequencer": "v3_source_clock_sample_1600n_sequencer",
    "v3_234_source_l2_sar_logic_4b": "v3_source_l2_sar_logic_4b",
    "v3_235_source_phase_detector_chopper": "v3_source_phase_detector_chopper",
    "v3_236_source_single_adc_7b_weighted": "v3_source_single_adc_7b_weighted",
    "v3_237_source_qtz_differential_2level": "v3_source_qtz_differential_2level",
    "v3_238_source_l2_7b_dac_ready": "v3_source_l2_7b_dac_ready",
    "v3_239_source_l2_cdac_4b_switch": "v3_source_l2_cdac_4b_switch",
    "v3_240_source_cdac_monodown_7b": "v3_source_cdac_monodown_7b",
    "v3_241_source_cdac_6b_stage1_up": "v3_source_cdac_6b_stage1_up",
    "v3_242_source_adc_zoom_timing_sequencer": "v3_source_adc_zoom_timing_sequencer",
    "v3_243_source_l2_sar_logic_7b": "v3_source_l2_sar_logic_7b",
    "v3_244_source_l3_sar2_logic_7b": "v3_source_l3_sar2_logic_7b",
    "v3_245_source_cdac_8b_monodown": "v3_source_cdac_8b_monodown",
    "v3_246_source_va_dac_6b_se": "v3_source_va_dac_6b_se",
    "v3_247_source_offset_halving_search": "v3_source_offset_halving_search",
    "v3_248_source_sar_comparator_reset_high": "v3_source_sar_comparator_reset_high",
    "v3_249_source_dac_restore_4bit_clocked": "v3_source_dac_restore_4bit_clocked",
    "v3_250_source_dac_restore_7bit_clocked": "v3_source_dac_restore_7bit_clocked",
    "v3_251_source_dac_restore_6bit_1p8": "v3_source_dac_restore_6bit_1p8",
    "v3_252_source_sample_hold_5v_clock": "v3_source_sample_hold_5v_clock",
    "v3_253_source_sum5_signed_sar_weight": "v3_source_sum5_signed_sar_weight",
    "v3_254_source_lt_readout_sar4": "v3_source_lt_readout_sar4",
    "v3_255_source_tool_4bit_sar_signed_dac": "v3_source_tool_4bit_sar_signed_dac",
    "v3_256_source_dac4bit_small_swing": "v3_source_dac4bit_small_swing",
    "v3_257_source_comparator_reset_low_1p8": "v3_source_comparator_reset_low_1p8",
    "v3_258_source_lt_read_sar6b_weighted": "v3_source_lt_read_sar6b_weighted",
    "v3_259_source_lt_read_sar7b_weighted": "v3_source_lt_read_sar7b_weighted",
    "v3_260_source_dac_serial_16b_nobridge": "v3_source_dac_serial_16b_nobridge",
    "v3_261_source_sar_13bit_serial_decoder": "v3_source_sar_13bit_serial_decoder",
    "v3_262_source_single_shot_timer_pulse": "v3_source_single_shot_timer_pulse",
    "v3_263_source_clocked_comparator_dual_output": "v3_source_clocked_comparator_dual_output",
    "v3_264_source_dac4bit_bipolar_252m": "v3_source_dac4bit_bipolar_252m",
    "v3_265_source_bin2ther_2b": "v3_source_bin2ther_2b",
    "v3_266_source_dff_set_reset": "v3_source_dff_set_reset",
    "v3_267_source_pfd_up_down_state": "v3_source_pfd_up_down_state",
    "v3_268_source_samplehold_rising_edge": "v3_source_samplehold_rising_edge",
    "v3_269_source_trim_ctrl_5bit": "v3_source_trim_ctrl_5bit",
    "v3_270_source_therm8_to_bin4_count": "v3_source_therm8_to_bin4_count",
    "v3_271_source_coarse_qtz_3bit_residue": "v3_source_coarse_qtz_3bit_residue",
    "v3_272_source_rs_phase_detector": "v3_source_rs_phase_detector",
    "v3_273_source_level_shifter_offset": "v3_source_level_shifter_offset",
    "v3_274_source_weighted_decoder_6bit": "v3_source_weighted_decoder_6bit",
    "v3_275_source_divide_by_two_toggle": "v3_source_divide_by_two_toggle_v2",
    "v3_276_source_accum3_pulse": "v3_source_accum3_pulse",
    "v3_277_source_xor_phase_detector": "v3_source_xor_phase_detector",
    "v3_278_source_decision_router_logic": "v3_source_decision_router_logic",
    "v3_279_source_safe_analog_divider": "v3_source_safe_analog_divider",
    "v3_280_source_vargain_diffamp_clip": "v3_source_vargain_diffamp_clip",
    "v3_281_source_programmable_divider_by_n": "v3_source_programmable_divider_by_n",
    "v3_282_source_pfd_timer_reset": "v3_source_pfd_timer_reset",
    "v3_288_source_absolute_value": "v3_source_absolute_value",
    "v3_289_source_deadband_voltage": "v3_source_deadband_voltage",
    "v3_290_source_deadband_diffamp": "v3_source_deadband_diffamp",
    "v3_291_source_limiting_diffamp": "v3_source_limiting_diffamp",
    "v3_292_source_smooth_tanh_comparator": "v3_source_smooth_tanh_comparator",
    "v3_293_source_flash_folded_dac4": "v3_source_flash_folded_dac4",
    "v3_294_source_subradix_dac10": "v3_source_subradix_dac10",
    "v3_295_source_clocked_adc3bit": "v3_source_clocked_adc3bit",
    "v3_296_source_cal4bit_modulo": "v3_source_cal4bit_modulo",
    "v3_297_source_mux4_priority": "v3_source_mux4_priority",
    "v3_298_source_xnor_gate_voltage": "v3_source_xnor_gate_voltage",
    "v3_299_source_bipolar_dff_sample": "v3_source_bipolar_dff_sample",
    "v3_300_source_pfd_active_low_reset": "v3_source_pfd_active_low_reset",
}
for _source_task_id, _source_checker_id in SOURCE_TASK_ID_ALIASES.items():
    if _source_checker_id in CHECKS:
        CHECKS[_source_task_id] = CHECKS[_source_checker_id]
# End source task.toml id aliases.
CHECKS["v3_283_weighted_sar_adc_dac_loop"] = check_sar_adc_dac_weighted_8b
CHECKS["283-weighted-sar-adc-dac-loop"] = check_sar_adc_dac_weighted_8b
CHECKS["v3_284_window_comparator_testbench"] = check_true_window_comparator
CHECKS["284-window-comparator-testbench"] = check_true_window_comparator
CHECKS["v3_285_aperture_delay_sample_hold"] = check_vbm1_track_hold_aperture
CHECKS["285-aperture-delay-sample-hold"] = check_vbm1_track_hold_aperture
CHECKS["v3_286_first_order_lowpass_bugfix"] = check_vbm1_first_order_lowpass
CHECKS["286-first-order-lowpass-bugfix"] = check_vbm1_first_order_lowpass
CHECKS["v3_287_gain_extraction_flow"] = check_gain_extraction
CHECKS["287-gain-extraction-flow"] = check_gain_extraction

for _alias, _source_checker_id in {
    "v3_283_weighted_sar_adc_dac_loop": "vbr1_l2_weighted_sar_adc_dac_loop_e2e",
    "283-weighted-sar-adc-dac-loop": "vbr1_l2_weighted_sar_adc_dac_loop_e2e",
    "v3_284_window_comparator_testbench": "vbr1_l1_window_comparator_detector_tb",
    "284-window-comparator-testbench": "vbr1_l1_window_comparator_detector_tb",
    "v3_285_aperture_delay_sample_hold": "vbr1_l1_aperture_delay_track_and_hold",
    "285-aperture-delay-sample-hold": "vbr1_l1_aperture_delay_track_and_hold",
    "v3_286_first_order_lowpass_bugfix": "vbr1_l1_first_order_lowpass",
    "286-first-order-lowpass-bugfix": "vbr1_l1_first_order_lowpass",
    "v3_287_gain_extraction_flow": "vbr1_l2_gain_extraction_convergence_measurement_flow_e2e",
    "287-gain-extraction-flow": "vbr1_l2_gain_extraction_convergence_measurement_flow_e2e",
}.items():
    if _source_checker_id in STREAMING_BEHAVIOR_CHECKS:
        STREAMING_BEHAVIOR_CHECKS[_alias] = STREAMING_BEHAVIOR_CHECKS[_source_checker_id]


RELEASE_FORM_CHECK_ALIASES = {
    "vbr1_l1_strongarm_style_latch_comparator_bugfix": check_strongarm_reset_priority_bug,
    "vbr1_l2_gain_extraction_convergence_measurement_flow_tb": check_gain_extraction,
    "vbr1_l1_gain_estimator_tb": check_gain_estimator,
    "vbr1_l2_weighted_sar_adc_dac_loop_tb": check_sar_adc_dac_weighted_8b,
    "vbr1_l2_cppll_tracking_and_frequency_step_reacquire_flow_tb": check_cppll_freq_step_reacquire,
    "vbr1_l1_bang_bang_phase_detector_bugfix": check_bbpd,
    "vbr1_l1_edge_interval_timer_tb": check_cross_interval_163p333,
    "vbr1_l1_lfsr_prbs_generator_bugfix": check_prbs7,
    "vbr1_l1_clock_divider_bugfix": check_clk_divider,
    "vbr1_l2_adpll_lock_ratio_hop_timer_flow_tb": check_adpll_ratio_hop,
    "vbr1_l1_capacitive_weighted_sar_feedback_dac_bugfix": check_release_cdac_feedback_dac,
    "vbr1_l1_capacitive_weighted_sar_feedback_dac_e2e": check_release_cdac_feedback_dac,
    "vbr1_l1_capacitive_weighted_sar_feedback_dac_tb": check_release_cdac_feedback_dac,
    "vbr1_l1_lfsr_prbs_generator_tb": check_lfsr,
    "vbr1_l2_measurement_flow_tb": check_final_step_file_metric,
    "vbr1_l1_bang_bang_phase_detector_tb": check_bbpd_data_edge_alignment,
    "vbr1_l2_flash_adc_mini_array_e2e": check_release_flash_adc_mini_array,
    "vbr1_l2_flash_adc_mini_array_tb": check_release_flash_adc_mini_array,
    "vbr1_l2_pipeline_adc_chain_e2e": check_release_pipeline_adc_chain,
    "vbr1_l2_pipeline_adc_chain_tb": check_release_pipeline_adc_chain,
    "vbr1_l2_comparator_measurement_flow_e2e": check_comparator_measurement_flow,
    "vbr1_l2_comparator_measurement_flow_tb": check_comparator_measurement_flow,
    "vbr1_l1_sine_periodic_voltage_source_e2e": check_multitone,
    "vbr1_l1_sine_periodic_voltage_source_tb": check_multitone,
    "vbr1_l1_sine_periodic_voltage_source_dut": check_multitone,
    "vbr1_l1_edge_interval_timer_e2e": check_cross_interval_163p333,
    "vbr1_l1_gain_estimator_e2e": check_gain_estimator,
    "vbr1_l2_gain_extraction_convergence_measurement_flow_e2e": check_gain_extraction,
    "vbr1_l2_measurement_flow_e2e": check_final_step_file_metric,
    "vbr1_l1_lfsr_prbs_generator_e2e": check_lfsr,
}

CHECKS.update(RELEASE_FORM_CHECK_ALIASES)
CHECKS.setdefault("vbr1_l1_clock_divider_tb", check_clk_divider)
CHECKS.setdefault("vbr1_l1_settling_time_detector_tb", check_vbm1_settling_time_measurement_tb)

V3_CANDIDATE_090_111_CHECK_ALIASES = {
    "v3_090_adpll_ratio_hop_timer": "vbr1_l2_adpll_lock_ratio_hop_timer_flow_tb",
    "090-adpll-ratio-hop-timer": "vbr1_l2_adpll_lock_ratio_hop_timer_flow_tb",
    "v3_091_agc_receiver_leveling_loop": "vbr1_l2_agc_receiver_leveling_loop_tb",
    "091-agc-receiver-leveling-loop": "vbr1_l2_agc_receiver_leveling_loop_tb",
    "v3_092_amplifier_filter_chain": "vbr1_l2_amplifier_filter_chain_tb",
    "092-amplifier-filter-chain": "vbr1_l2_amplifier_filter_chain_tb",
    "v3_093_bbpd_data_edge_alignment": "vbr1_l1_bang_bang_phase_detector_tb",
    "093-bbpd-data-edge-alignment": "vbr1_l1_bang_bang_phase_detector_tb",
    "v3_094_comparator_offset_search": "vbr1_l2_comparator_measurement_flow_tb",
    "094-comparator-offset-search": "vbr1_l2_comparator_measurement_flow_tb",
    "v3_095_complete_calibration_loop": "vbr1_l2_complete_calibration_loop_tb",
    "095-complete-calibration-loop": "vbr1_l2_complete_calibration_loop_tb",
    "v3_096_converter_static_linearity_measurement": "vbr1_l2_converter_static_linearity_measurement_flow_tb",
    "096-converter-static-linearity-measurement": "vbr1_l2_converter_static_linearity_measurement_flow_tb",
    "v3_097_cppll_tracking_reacquire_timer": "vbr1_l2_cppll_tracking_and_frequency_step_reacquire_flow_tb",
    "097-cppll-tracking-reacquire-timer": "vbr1_l2_cppll_tracking_and_frequency_step_reacquire_flow_tb",
    "v3_098_edge_crossing_interval_timer": "vbr1_l1_edge_interval_timer_tb",
    "098-edge-crossing-interval-timer": "vbr1_l1_edge_interval_timer_tb",
    "v3_099_dither_adder": "vbr1_l2_gain_extraction_convergence_measurement_flow_tb",
    "099-dither-adder": "vbr1_l2_gain_extraction_convergence_measurement_flow_tb",
    "v3_100_final_step_file_metric": "vbr1_l2_measurement_flow_tb",
    "100-final-step-file-metric": "vbr1_l2_measurement_flow_tb",
    "v3_101_fixed_gain_amplifier": "vbr1_l2_gain_extraction_convergence_measurement_flow_tb",
    "101-fixed-gain-amplifier": "vbr1_l2_gain_extraction_convergence_measurement_flow_tb",
    "v3_102_gain_estimator": "vbr1_l1_gain_estimator_tb",
    "102-gain-estimator": "vbr1_l1_gain_estimator_tb",
    "v3_103_iq_downconversion_chain": "vbr1_l2_iq_downconversion_chain_tb",
    "103-iq-downconversion-chain": "vbr1_l2_iq_downconversion_chain_tb",
    "v3_104_ldo_load_step_recovery": "vbr1_l2_ldo_load_step_recovery_flow_tb",
    "104-ldo-load-step-recovery": "vbr1_l2_ldo_load_step_recovery_flow_tb",
    "v3_105_pipeline_adc_chain_4b": "vbr1_l2_pipeline_adc_chain_tb",
    "105-pipeline-adc-chain-4b": "vbr1_l2_pipeline_adc_chain_tb",
    "v3_106_programmable_stimulus_sequencer": "vbr1_l2_programmable_stimulus_sequencer_tb",
    "106-programmable-stimulus-sequencer": "vbr1_l2_programmable_stimulus_sequencer_tb",
    "v3_107_reference_step_clock": "vbr1_l2_cppll_tracking_and_frequency_step_reacquire_flow_tb",
    "107-reference-step-clock": "vbr1_l2_cppll_tracking_and_frequency_step_reacquire_flow_tb",
    "v3_108_reference_startup_enable_flow": "vbr1_l2_reference_startup_enable_flow_tb",
    "108-reference-startup-enable-flow": "vbr1_l2_reference_startup_enable_flow_tb",
    "v3_109_sample_hold_droop_front_end": "vbr1_l2_converter_front_end_tb",
    "109-sample-hold-droop-front-end": "vbr1_l2_converter_front_end_tb",
    "v3_110_settling_time_measurement": "vbr1_l1_settling_time_detector_tb",
    "110-settling-time-measurement": "vbr1_l1_settling_time_detector_tb",
    "v3_111_clocked_sine_source": "vbr1_l2_gain_extraction_convergence_measurement_flow_tb",
    "111-clocked-sine-source": "vbr1_l2_gain_extraction_convergence_measurement_flow_tb",
}

for _alias, _source_checker_id in V3_CANDIDATE_090_111_CHECK_ALIASES.items():
    CHECKS[_alias] = CHECKS[_source_checker_id]
    if _source_checker_id in STREAMING_BEHAVIOR_CHECKS:
        STREAMING_BEHAVIOR_CHECKS[_alias] = STREAMING_BEHAVIOR_CHECKS[_source_checker_id]

V3_PLL_502_505_CHECK_ALIASES = {
    "v3_502_sine_vco_idtmod_bound_step": check_v3_502_sine_vco_idtmod_bound_step,
    "502-sine-vco-idtmod-bound-step": check_v3_502_sine_vco_idtmod_bound_step,
    "v3_503_differential_vco_clip_idtmod": check_v3_503_differential_vco_clip_idtmod,
    "503-differential-vco-clip-idtmod": check_v3_503_differential_vco_clip_idtmod,
    "v3_504_charge_pump_pfd_state_machine": check_v3_504_charge_pump_pfd_state_machine,
    "504-charge-pump-pfd-state-machine": check_v3_504_charge_pump_pfd_state_machine,
    "v3_505_fractional_n_divider_accumulator_flow": check_v3_505_fractional_n_divider_accumulator_flow,
    "505-fractional-n-divider-accumulator-flow": check_v3_505_fractional_n_divider_accumulator_flow,
}
CHECKS.update(V3_PLL_502_505_CHECK_ALIASES)

VALIDATED_FAST_CHECKER_TASKS = frozenset(STREAMING_BEHAVIOR_CHECKS)


VABENCH300_V11_CHECK_ALIASES = {
    "sigma_delta_modulator_loop": check_v11_sigma_delta_modulator_loop,
    "time_interleaved_adc_mismatch": check_v11_time_interleaved_adc_mismatch,
    "metastability_window_comparator": check_v11_metastability_window_comparator,
    "bootstrapped_sample_switch": check_v11_bootstrapped_sample_switch,
    "fractional_n_pll_divider": check_v11_fractional_n_pll_divider,
    "bandgap_startup_trim": check_v11_bandgap_startup_trim,
    "quadrature_iq_imbalance_corrector": check_v11_quadrature_iq_imbalance_corrector,
    "cppll_tracking_frequency_step_reacquire": check_v11_cppll_tracking_frequency_step_reacquire,
}

for _v11_topic_id, _v11_checker in VABENCH300_V11_CHECK_ALIASES.items():
    CHECKS.setdefault(_v11_topic_id, _v11_checker)
    for _v11_form in ("dut", "tb", "bugfix", "e2e"):
        CHECKS.setdefault(f"{_v11_topic_id}:{_v11_form}", _v11_checker)


def has_behavior_check(task_id: str) -> bool:
    return task_id in CHECKS


def release_checker_task_id(meta: dict, form: str | None = None) -> str | None:
    """Return the release-v1 checker key when a task keeps a legacy meta id."""
    release_entry_id = str(meta.get("release_entry_id") or meta.get("legacy_entry_id") or "").strip()
    release_form = (form or "").strip()
    if release_form not in {"dut", "tb", "bugfix", "e2e"}:
        legacy_task_id = str(meta.get("task_id") or meta.get("id") or "").strip()
        for suffix in ("bugfix", "dut", "e2e", "tb"):
            if legacy_task_id.endswith(f"_{suffix}") or legacy_task_id.endswith(f":{suffix}"):
                release_form = suffix
                break
    if release_form not in {"dut", "tb", "bugfix", "e2e"}:
        return None
    if not release_entry_id:
        return None
    candidate = f"{release_entry_id}_{release_form}"
    return candidate if candidate in CHECKS else None


def resolve_checker_task_id(meta: dict, task_id: str, form: str | None = None) -> str:
    return str(
        meta.get("checker_task_id")
        or release_checker_task_id(meta, form)
        or meta.get("source_checker_task_id")
        or meta.get("task_id")
        or meta.get("id")
        or task_id
    )


def evaluate_behavior(
    task_id: str,
    csv_path: Path,
    checks_config: dict[str, object] | None = None,
) -> tuple[float, list[str]]:
    if task_id not in CHECKS:
        return 0.0, [f"no behavior check implemented for {task_id}"]
    if task_id in {"noise_gen", "noise_gen_smoke"}:
        return evaluate_noise_gen_csv(csv_path)
    streaming_result = evaluate_streaming_behavior(task_id, csv_path)
    if streaming_result is not None:
        return streaming_result
    rows = normalize_rows_for_task(task_id, load_csv(csv_path))
    checker_parameters = (checks_config or {}).get("checker_parameters", {})
    if task_id == "vbr1_l1_first_order_lowpass" and isinstance(checker_parameters, dict) and checker_parameters:
        ok, note = check_v2_configured_first_order_lowpass(rows, checker_parameters)
        note = f"{note} checker_config_parameters=first_order_lowpass"
    else:
        ok, note = CHECKS[task_id](rows)
    return (1.0 if ok else 0.0), [note]


def _behavior_eval_worker(
    task_id: str,
    csv_path: str,
    checks_config: dict[str, object] | None,
    queue: mp.Queue,
) -> None:
    """Run checker evaluation in a child process so large CSVs cannot hang scoring."""
    try:
        queue.put(("ok", evaluate_behavior(task_id, Path(csv_path), checks_config=checks_config)))
    except Exception as exc:  # pragma: no cover - defensive worker boundary
        queue.put(("error", f"{type(exc).__name__}: {str(exc)[:300]}"))


def evaluate_behavior_with_timeout(
    task_id: str,
    csv_path: Path,
    *,
    timeout_s: int,
    checks_config: dict[str, object] | None = None,
) -> tuple[float, list[str]]:
    """Evaluate behavior with a watchdog separate from EVAS simulation timeout.

    `evas simulate` can finish successfully while producing a very large CSV.
    Without a second timeout, Python-side checker parsing can block an entire
    full92 matrix run. Keep this timeout shorter than simulation timeout so one
    pathological waveform becomes a normal task failure instead of a matrix hang.
    """
    direct_max_bytes = int(os.environ.get("VAEVAS_BEHAVIOR_DIRECT_MAX_BYTES", "5000000"))
    try:
        if csv_path.stat().st_size <= direct_max_bytes:
            return evaluate_behavior(task_id, csv_path, checks_config=checks_config)
    except OSError:
        pass

    eval_timeout_s = max(10, min(60, max(1, timeout_s // 3)))
    ctx = mp.get_context("spawn")
    queue: mp.Queue = ctx.Queue(maxsize=1)
    proc = ctx.Process(
        target=_behavior_eval_worker,
        args=(task_id, str(csv_path), checks_config, queue),
    )
    proc.start()
    proc.join(eval_timeout_s)
    if proc.is_alive():
        proc.terminate()
        proc.join(5)
        if proc.is_alive():
            proc.kill()
            proc.join(5)
        return 0.0, [f"behavior_eval_timeout>{eval_timeout_s}s"]
    if queue.empty():
        return 0.0, ["behavior_eval_no_result"]
    status, payload = queue.get()
    if status == "ok":
        return payload
    return 0.0, [f"behavior_eval_error={payload}"]


def _duration_to_seconds(value: str, unit: str) -> float:
    number = float(value)
    normalized = unit.lower()
    if normalized == "ms":
        return number / 1000.0
    if normalized in {"us", "µs"}:
        return number / 1_000_000.0
    if normalized == "ns":
        return number / 1_000_000_000.0
    return number


def parse_evas_timing(text: str) -> dict[str, float]:
    timing: dict[str, float] = {}
    tran_match = re.search(
        r"Tran analysis time:\s*CPU\s*=\s*[\d.]+\s*\w+,\s*elapsed\s*=\s*([\d.]+)\s*(ns|us|µs|ms|s)",
        text,
        re.IGNORECASE,
    )
    total_match = re.search(
        r"Total time:\s*CPU\s*=\s*[\d.]+\s*\w+,\s*elapsed\s*=\s*([\d.]+)\s*(ns|us|µs|ms|s)",
        text,
        re.IGNORECASE,
    )
    steps_match = re.search(r"Number of accepted tran steps\s*=\s*([0-9]+)", text)
    if tran_match:
        timing["tran_elapsed_s"] = _duration_to_seconds(tran_match.group(1), tran_match.group(2))
    if total_match:
        timing["total_elapsed_s"] = _duration_to_seconds(total_match.group(1), total_match.group(2))
    if steps_match:
        timing["accepted_tran_steps"] = float(steps_match.group(1))
    for section_match in re.finditer(
        r"^\s+([A-Za-z0-9_]+_s)\s*=\s*([0-9.eE+-]+)\s*s\s*$",
        text,
        flags=re.MULTILINE,
    ):
        timing[section_match.group(1)] = float(section_match.group(2))
    return timing


def add_evas_reported_timing_split(
    timing_split: dict[str, float],
    timing: dict[str, float],
) -> None:
    tran_elapsed = timing.get("tran_elapsed_s")
    total_elapsed = timing.get("total_elapsed_s")
    subprocess_wall = timing_split.get("evas_subprocess_wall_s")

    if tran_elapsed is not None:
        timing_split["evas_reported_tran_elapsed_s"] = tran_elapsed
    if total_elapsed is not None:
        timing_split["evas_reported_total_elapsed_s"] = total_elapsed

    for key, value in timing.items():
        if key in {"tran_elapsed_s", "total_elapsed_s", "accepted_tran_steps"}:
            continue
        if key.endswith("_s"):
            timing_split[f"evas_runner_{key}"] = value

    if subprocess_wall is not None and total_elapsed is not None:
        unattributed = subprocess_wall - total_elapsed
        if unattributed >= -1e-6:
            timing_split["evas_subprocess_unattributed_s"] = max(0.0, unattributed)


_EVAS_COUNTER_SECTIONS = {
    "Performance counters:": "",
    "Trace counters:": "trace.",
    "Indexed array profile:": "indexed_array_profile.",
    "Indexed model IO plan:": "indexed_model_io_plan.",
    "Indexed voltage read probe:": "indexed_voltage_read_probe.",
    "Indexed voltage array reads:": "indexed_voltage_array_reads.",
}


def _parse_counter_scalar(value: str) -> int | float | str:
    text = value.strip()
    try:
        if re.fullmatch(r"[+-]?\d+", text):
            return int(text)
        if re.fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?", text):
            parsed = float(text)
            if math.isfinite(parsed):
                return parsed
    except ValueError:
        pass
    return text


def parse_evas_performance_counters(text: str) -> dict[str, int | float | str]:
    counters: dict[str, int | float | str] = {}
    section_prefix: str | None = None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped in _EVAS_COUNTER_SECTIONS:
            section_prefix = _EVAS_COUNTER_SECTIONS[stripped]
            continue
        if not stripped:
            section_prefix = None
            continue
        if section_prefix is None:
            continue
        if not line[:1].isspace():
            section_prefix = None
            continue
        if " = " not in stripped:
            continue
        key, value = stripped.split(" = ", 1)
        if key.startswith("model["):
            continue
        counters[f"{section_prefix}{key}"] = _parse_counter_scalar(value)
    return counters


def run_case(
    task_dir: Path,
    dut_path: Path,
    tb_path: Path,
    *,
    output_root: Path | None = None,
    keep_run_dir: bool = False,
    timeout_s: int = 120,
    task_id_override: str | None = None,
    checker_task_id_override: str | None = None,
) -> dict:
    t_case_start = time.perf_counter()
    timing_split: dict[str, float] = {}
    try:
        meta = read_meta(task_dir)
    except FileNotFoundError:
        meta = {}
    v2_checks_config = load_v2_checks_config(task_dir)
    task_id = task_id_override or meta.get("id") or meta.get("task_id") or task_dir.name
    checker_task_id = (
        checker_task_id_override
        or v2_checks_config.get("checker_task_id")
        or resolve_checker_task_id(meta, str(task_id), form=task_dir.name)
    )
    scoring = set(meta.get("scoring", ["dut_compile", "tb_compile", "sim_correct"]))
    evas_engine_used = effective_evas_engine()

    t0 = time.perf_counter()
    temp_ctx = tempfile.TemporaryDirectory(prefix=f"{task_id}_")
    timing_split["tempdir_create_s"] = time.perf_counter() - t0
    try:
        t0 = time.perf_counter()
        run_dir = Path(temp_ctx.name)
        out_dir = output_root.resolve() if output_root else run_dir / "output"
        out_dir.mkdir(parents=True, exist_ok=True)
        for stale_name in ("tran.csv", "strobe.txt", "tran.png"):
            stale_path = out_dir / stale_name
            if stale_path.exists():
                stale_path.unlink()
        timing_split["output_setup_s"] = time.perf_counter() - t0

        t0 = time.perf_counter()
        task_artifact_targets = read_task_artifact_targets(task_dir)
        task_artifact_supports = read_task_artifact_supports(task_dir)
        dut_dst, tb_dst = copy_inputs(
            run_dir,
            dut_path,
            tb_path,
            target_filenames=[*task_artifact_targets, *task_artifact_supports],
            primary_target_filename=task_artifact_targets[0] if task_artifact_targets else None,
            companion_search_dirs=(dut_path.parent, task_dir / "solution", task_dir / "starter"),
        )
        timing_split["copy_inputs_s"] = time.perf_counter() - t0

        t0 = time.perf_counter()
        checker_config_failures = v2_checks_syntax_failures(v2_checks_config, run_dir)
        timing_split["checker_config_syntax_guard_s"] = time.perf_counter() - t0
        if checker_config_failures:
            notes = [
                "checker_config_syntax_guard_failed",
                f"checker_config={v2_checks_config.get('path')}",
                *checker_config_failures,
            ]
            return {
                "task_id": task_id,
                "checker_task_id": checker_task_id,
                "checker_policy": behavior_checker_policy(str(checker_task_id), notes),
                "status": "FAIL_DUT_COMPILE",
                "backend_used": "evas",
                "evas_engine_used": evas_engine_used,
                "scores": {
                    "dut_compile": 0.0,
                    "tb_compile": 0.0,
                    "sim_correct": 0.0,
                    "weighted_total": 0.0,
                },
                "artifacts": [
                    str(dut_dst),
                    str(tb_dst),
                    str(out_dir / "tran.csv"),
                    str(out_dir / "strobe.txt"),
                ],
                "notes": notes,
                "timing": {},
                "timing_split": timing_split,
                "stdout_tail": "\n".join(notes),
            }

        t0 = time.perf_counter()
        preflight_failures = spectre_aligned_veriloga_preflight(run_dir)
        timing_split["preflight_s"] = time.perf_counter() - t0
        if preflight_failures:
            notes = ["spectre_aligned_preflight_failed", *preflight_failures]
            return {
                "task_id": task_id,
                "checker_task_id": checker_task_id,
                "checker_policy": behavior_checker_policy(checker_task_id, notes),
                "status": "FAIL_DUT_COMPILE",
                "backend_used": "evas",
                "evas_engine_used": evas_engine_used,
                "scores": {
                    "dut_compile": 0.0,
                    "tb_compile": 0.0,
                    "sim_correct": 0.0,
                    "weighted_total": 0.0,
                },
                "artifacts": [
                    str(dut_dst),
                    str(tb_dst),
                    str(out_dir / "tran.csv"),
                    str(out_dir / "strobe.txt"),
                ],
                "notes": notes,
                "timing": {},
                "timing_split": timing_split,
                "stdout_tail": "\n".join(notes),
            }
        t0 = time.perf_counter()
        _remove_stale_metric_file(checker_task_id, run_dir)
        timing_split["metric_cleanup_s"] = time.perf_counter() - t0

        trace_contract_kind = required_trace_contract_kind_for_checker(checker_task_id)
        required_trace_signals = required_trace_signals_for_checker(checker_task_id)
        extra_trace_signals = (
            _extra_trace_signals_for_checker(checker_task_id)
            if required_trace_signals
            else frozenset()
        )
        extra_trace_signal_count = len(extra_trace_signals - {"time"})
        if required_trace_signals:
            timing_split["required_trace_signal_count"] = float(len(required_trace_signals - {"time"}))
        if extra_trace_signals:
            timing_split["extra_trace_signal_count"] = float(extra_trace_signal_count)
        t0 = time.perf_counter()
        proc = run_evas(
            run_dir,
            tb_dst,
            out_dir,
            timeout_s,
            required_trace_signals=required_trace_signals,
        )
        timing_split["evas_subprocess_wall_s"] = time.perf_counter() - t0
        combined = (proc.stdout or "") + "\n" + (proc.stderr or "")
        evas_timing = parse_evas_timing(combined)
        add_evas_reported_timing_split(timing_split, evas_timing)

        dut_compile = 1.0 if "Compiled Verilog-A module:" in combined else 0.0
        tb_compile = 1.0 if ("Transient Analysis" in combined or (out_dir / "tran.csv").exists()) else 0.0

        notes = [f"returncode={proc.returncode}", f"evas_engine={evas_engine_used or 'default'}"]
        if v2_checks_config:
            notes.append(f"checker_config={v2_checks_config.get('path')}")
        if required_trace_signals:
            notes.append(f"trace_contract={trace_contract_kind}")
        if extra_trace_signals:
            notes.append(f"extra_trace_signals={extra_trace_signal_count}")
        if dut_compile == 0.0:
            notes.append("dut_not_compiled")
        if tb_compile == 0.0:
            notes.append("tb_not_executed")

        csv_path = out_dir / "tran.csv"
        if "sim_correct" in scoring and proc.returncode == 0 and csv_path.exists():
            t0 = time.perf_counter()
            sim_correct, behavior_notes = evaluate_behavior_with_timeout(
                checker_task_id,
                csv_path,
                timeout_s=timeout_s,
                checks_config=v2_checks_config,
            )
            timing_split["behavior_checker_s"] = time.perf_counter() - t0
            notes.extend(behavior_notes)
            t0 = time.perf_counter()
            metric_result = validate_behavior_side_outputs(checker_task_id, run_dir, csv_path)
            timing_split["side_output_validation_s"] = time.perf_counter() - t0
            if metric_result is not None:
                metric_ok, metric_note = metric_result
                notes.append(metric_note)
                if not metric_ok:
                    sim_correct = 0.0
            if (
                sim_correct < 1.0
                and required_trace_signals
                and trace_contract_kind == "row_required_set"
                and _row_checker_trace_fallback_enabled()
            ):
                notes.append("auto_sparse_trace_fallback_full_trace")
                timing_split["sparse_trace_evas_subprocess_wall_s"] = timing_split.get(
                    "evas_subprocess_wall_s", 0.0
                )
                for stale_name in ("tran.csv", "strobe.txt", "tran.png"):
                    stale_path = out_dir / stale_name
                    if stale_path.exists():
                        stale_path.unlink()
                _remove_stale_metric_file(checker_task_id, run_dir)

                t0 = time.perf_counter()
                full_proc = run_evas(
                    run_dir,
                    tb_dst,
                    out_dir,
                    timeout_s,
                    required_trace_signals=frozenset(),
                )
                fallback_wall = time.perf_counter() - t0
                timing_split["fallback_full_trace_evas_subprocess_wall_s"] = fallback_wall
                timing_split["evas_subprocess_wall_s"] = (
                    timing_split.get("sparse_trace_evas_subprocess_wall_s", 0.0)
                    + fallback_wall
                )
                full_combined = (full_proc.stdout or "") + "\n" + (full_proc.stderr or "")
                notes.append(f"fallback_returncode={full_proc.returncode}")
                if full_proc.returncode == 0 and csv_path.exists():
                    t0 = time.perf_counter()
                    fallback_score, fallback_notes = evaluate_behavior_with_timeout(
                        checker_task_id,
                        csv_path,
                        timeout_s=timeout_s,
                        checks_config=v2_checks_config,
                    )
                    timing_split["fallback_full_trace_behavior_checker_s"] = (
                        time.perf_counter() - t0
                    )
                    notes.extend(f"fallback:{note}" for note in fallback_notes)
                    t0 = time.perf_counter()
                    metric_result = validate_behavior_side_outputs(checker_task_id, run_dir, csv_path)
                    timing_split["fallback_full_trace_side_output_validation_s"] = (
                        time.perf_counter() - t0
                    )
                    if metric_result is not None:
                        metric_ok, metric_note = metric_result
                        notes.append(f"fallback:{metric_note}")
                        if not metric_ok:
                            fallback_score = 0.0
                    if fallback_score >= sim_correct:
                        sim_correct = fallback_score
                        proc = full_proc
                        combined = full_combined
                        evas_timing = parse_evas_timing(combined)
                else:
                    notes.append("fallback_tran.csv missing")
        elif "sim_correct" in scoring:
            sim_correct = 0.0
            notes.append("tran.csv missing")
        else:
            sim_correct = 1.0
            notes.append("sim_correct not required by scoring")
        checker_policy = behavior_checker_policy(checker_task_id, notes)

        required_axes: list[tuple[str, float]] = []
        if "dut_compile" in scoring or "syntax" in scoring:
            required_axes.append(("dut_compile", dut_compile))
        if "tb_compile" in scoring or "routing" in scoring or "simulation" in scoring:
            required_axes.append(("tb_compile", tb_compile))
        if "sim_correct" in scoring:
            required_axes.append(("sim_correct", sim_correct))

        if required_axes:
            weighted_total = round(sum(score for _, score in required_axes) / len(required_axes), 4)
        else:
            weighted_total = round((dut_compile + tb_compile + sim_correct) / 3.0, 4)

        if ("dut_compile" in scoring or "syntax" in scoring) and dut_compile < 1.0:
            status = "FAIL_DUT_COMPILE"
        elif ("tb_compile" in scoring or "routing" in scoring or "simulation" in scoring) and tb_compile < 1.0:
            status = "FAIL_TB_COMPILE"
        elif "sim_correct" in scoring and sim_correct < 1.0:
            status = "FAIL_SIM_CORRECTNESS"
        else:
            status = "PASS"

        return {
            "task_id": task_id,
            "checker_task_id": checker_task_id,
            "checker_policy": checker_policy,
            "status": status,
            "backend_used": "evas",
            "evas_engine_used": evas_engine_used,
            "scores": {
                "dut_compile": dut_compile,
                "tb_compile": tb_compile,
                "sim_correct": sim_correct,
                "weighted_total": weighted_total,
            },
            "artifacts": [
                str(dut_dst),
                str(tb_dst),
                str(out_dir / "tran.csv"),
                str(out_dir / "strobe.txt"),
            ],
            "notes": notes,
            "timing": evas_timing,
            "performance_counters": parse_evas_performance_counters(combined),
            "timing_split": timing_split,
            "stdout_tail": combined[-4000:],
        }
    finally:
        if not keep_run_dir:
            t0 = time.perf_counter()
            temp_ctx.cleanup()
            timing_split["temp_cleanup_s"] = time.perf_counter() - t0
        timing_split["run_case_wall_s"] = time.perf_counter() - t_case_start


def _evas_worker_main() -> int:
    from evas.netlist.runner import evas_simulate

    for line in sys.stdin:
        try:
            request = json.loads(line)
        except json.JSONDecodeError as exc:
            print(
                json.dumps(
                    {
                        "returncode": 1,
                        "stdout": "",
                        "stderr": f"evas_worker_bad_request={exc}",
                    }
                ),
                flush=True,
            )
            continue
        if isinstance(request, dict) and request.get("cmd") == "shutdown":
            return 0
        if not isinstance(request, dict):
            print(
                json.dumps(
                    {
                        "returncode": 1,
                        "stdout": "",
                        "stderr": "evas_worker_bad_request_type",
                    }
                ),
                flush=True,
            )
            continue

        run_dir = Path(str(request.get("run_dir", ""))).resolve()
        tb_file = run_dir / str(request.get("tb_file", ""))
        output_dir = Path(str(request.get("output_dir", ""))).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        log_path = output_dir / "evas.log"
        required_trace_value = str(request.get("required_trace_signals", "")).strip()
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()
        old_cwd = Path.cwd()
        old_trace_value = os.environ.get("EVAS_REQUIRED_TRACE_SIGNALS")
        old_side_effect_output_dir = os.environ.get("EVAS_SIDE_EFFECT_OUTPUT_DIR")
        ok = False
        error_text = ""
        try:
            os.chdir(run_dir)
            os.environ["EVAS_SIDE_EFFECT_OUTPUT_DIR"] = str(output_dir)
            if required_trace_value:
                os.environ["EVAS_REQUIRED_TRACE_SIGNALS"] = required_trace_value
            else:
                os.environ.pop("EVAS_REQUIRED_TRACE_SIGNALS", None)
            with contextlib.redirect_stdout(stdout_buffer), contextlib.redirect_stderr(stderr_buffer):
                ok = evas_simulate(
                    str(tb_file),
                    log_path=str(log_path),
                    output_dir=str(output_dir),
                )
        except Exception:  # noqa: BLE001 - worker must report simulator crashes.
            error_text = traceback.format_exc()
        finally:
            if old_trace_value is None:
                os.environ.pop("EVAS_REQUIRED_TRACE_SIGNALS", None)
            else:
                os.environ["EVAS_REQUIRED_TRACE_SIGNALS"] = old_trace_value
            if old_side_effect_output_dir is None:
                os.environ.pop("EVAS_SIDE_EFFECT_OUTPUT_DIR", None)
            else:
                os.environ["EVAS_SIDE_EFFECT_OUTPUT_DIR"] = old_side_effect_output_dir
            os.chdir(old_cwd)

        try:
            log_text = log_path.read_text(encoding="utf-8")
        except OSError:
            log_text = ""
        stdout_text = log_text + stdout_buffer.getvalue()
        stderr_text = stderr_buffer.getvalue() + error_text
        print(
            json.dumps(
                {
                    "returncode": 0 if ok and not error_text else 1,
                    "stdout": stdout_text,
                    "stderr": stderr_text,
                }
            ),
            flush=True,
        )
    return 0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("task_dir")
    ap.add_argument("dut")
    ap.add_argument("tb")
    ap.add_argument("--output-root", default=None)
    ap.add_argument("--keep-run-dir", action="store_true")
    ap.add_argument("--timeout-s", type=int, default=120)
    ap.add_argument("--task-id", default=None)
    ap.add_argument("--checker-task-id", default=None)
    args = ap.parse_args()

    task_dir = Path(args.task_dir).resolve()
    dut_path = Path(args.dut).resolve()
    tb_path = Path(args.tb).resolve()
    output_root = Path(args.output_root).resolve() if args.output_root else None
    result = run_case(
        task_dir,
        dut_path,
        tb_path,
        output_root=output_root,
        keep_run_dir=args.keep_run_dir,
        timeout_s=args.timeout_s,
        task_id_override=args.task_id,
        checker_task_id_override=args.checker_task_id,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--evas-worker":
        raise SystemExit(_evas_worker_main())
    main()
