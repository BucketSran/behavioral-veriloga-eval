from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


def find_repo_root(path: Path) -> Path:
    for parent in [path, *path.parents]:
        if (parent / "runners" / "simulate_evas.py").exists():
            return parent
    env_root = os.environ.get("VABENCH_ROOT")
    if env_root and (Path(env_root) / "runners" / "simulate_evas.py").exists():
        return Path(env_root)
    raise SystemExit("cannot find behavioral-veriloga-eval repo root; set VABENCH_ROOT")


def _candidate_source_dir(env_name: str) -> Path:
    override = os.environ.get(env_name)
    if override:
        return Path(override).expanduser().resolve()
    legacy = os.environ.get("VABENCH_VISIBLE_SOURCE_DIR")
    if legacy and env_name == "VABENCH_FEEDBACK_SOURCE_DIR":
        return Path(legacy).expanduser().resolve()
    raise SystemExit(
        f"missing candidate source directory; set {env_name}=<candidate-dir>. "
        "The v4 oracle runner does not fall back to starter files."
    )


def _oracle_timeout(default_timeout_s: int) -> int:
    configured = os.environ.get("VABENCH_ORACLE_TIMEOUT_S")
    if not configured:
        return default_timeout_s
    try:
        timeout_s = int(configured)
    except ValueError as exc:
        raise SystemExit("VABENCH_ORACLE_TIMEOUT_S must be a positive integer") from exc
    if timeout_s <= 0:
        raise SystemExit("VABENCH_ORACLE_TIMEOUT_S must be a positive integer")
    return timeout_s


def _task_wrapper_may_select_python(force_python_engine: bool) -> bool:
    """Use the compatibility default only when the caller did not select an engine."""
    return force_python_engine and not os.environ.get("EVAS_ENGINE")


def _standalone_rust_frontend() -> tuple[Path, str] | None:
    implementation = os.environ.get("VABENCH_EVAS_IMPLEMENTATION", "python-rust-hybrid")
    if implementation == "python-rust-hybrid":
        return None
    if implementation != "standalone-rust":
        raise SystemExit(f"unsupported VABENCH_EVAS_IMPLEMENTATION={implementation!r}")

    raw_path = os.environ.get("VABENCH_EVAS_RUST_FRONTEND")
    expected_sha256 = os.environ.get("VABENCH_EVAS_RUST_FRONTEND_SHA256")
    if not raw_path:
        raise SystemExit(
            "standalone-rust requires VABENCH_EVAS_RUST_FRONTEND=<evas_rust_frontend>"
        )
    if not expected_sha256 or not re.fullmatch(r"[a-f0-9]{64}", expected_sha256):
        raise SystemExit(
            "standalone-rust requires VABENCH_EVAS_RUST_FRONTEND_SHA256=<64 hex chars>"
        )
    binary = Path(raw_path).expanduser().resolve()
    if not binary.is_file():
        raise SystemExit(f"standalone Rust EVAS binary is missing: {binary}")
    observed_sha256 = hashlib.sha256(binary.read_bytes()).hexdigest()
    if observed_sha256 != expected_sha256:
        raise SystemExit(
            "standalone Rust EVAS binary hash mismatch: "
            f"expected={expected_sha256} observed={observed_sha256}"
        )
    return binary, observed_sha256


def _run_standalone_rust_frontend(
    binary: Path,
    run_dir: Path,
    tb_path: Path,
    output_dir: Path,
    *,
    timeout_s: int,
) -> subprocess.CompletedProcess[str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    command = [
        str(binary),
        "--scs",
        str(tb_path),
        "--output",
        str(output_dir / "tran.csv"),
        "--include-dir",
        str(run_dir),
        "--include-dir",
        str(run_dir / "dut"),
        "--include-dir",
        str(run_dir / "support"),
    ]
    try:
        return subprocess.run(
            command,
            cwd=run_dir,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_s,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode() if isinstance(exc.stdout, bytes) else str(exc.stdout or "")
        stderr = exc.stderr.decode() if isinstance(exc.stderr, bytes) else str(exc.stderr or "")
        return subprocess.CompletedProcess(command, 124, stdout, stderr + "\nTIMEOUT")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _legacy_tb_path(task_dir: Path, profile_name: str) -> Path:
    if profile_name == "feedback":
        return task_dir / "test_feedback" / "public_tb.scs"
    if profile_name == "score":
        return task_dir / "evaluator" / "score_tb.scs"
    raise SystemExit(f"unsupported oracle profile name: {profile_name}")


def _load_tb_text(task_dir: Path, profile_name: str) -> tuple[str, bool]:
    harness_spec = task_dir / "evaluator" / "harness_spec.json"
    if harness_spec.is_file():
        package_root = task_dir.parents[1]
        scripts_dir = package_root / "scripts"
        if str(scripts_dir) not in sys.path:
            sys.path.insert(0, str(scripts_dir))
        from render_v4_harness import build_profile, load_spec, render_scs

        spec, spec_hash = load_spec(harness_spec)
        profile = build_profile(spec, profile_name, spec_hash)
        recorded_path = task_dir / "evaluator" / "profiles" / f"{profile_name}.json"
        if not recorded_path.is_file():
            raise SystemExit(f"missing generated harness profile: {recorded_path}")
        recorded = _read_json(recorded_path)
        if recorded != profile:
            raise SystemExit(
                f"stale generated harness profile: {recorded_path}; regenerate from {harness_spec}"
            )
        return render_scs(spec, profile), True

    path = _legacy_tb_path(task_dir, profile_name)
    if not path.exists():
        raise SystemExit(f"missing oracle testbench deck: {path}")
    return path.read_text(encoding="utf-8"), False


def _load_checker_profile(task_dir: Path) -> dict[str, Any]:
    profile_path = task_dir / "evaluator" / "checker_profile.json"
    if not profile_path.exists():
        raise SystemExit(f"missing checker profile: {profile_path}")
    return _read_json(profile_path)


def _trace_rising_crossings(csv_path: Path, signal: str, threshold: float) -> list[float]:
    crossings: list[float] = []
    previous: tuple[float, float] | None = None
    with csv_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            try:
                time = float(row["time"])
                value = float(row[signal])
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(f"trace missing numeric time/{signal}") from exc
            if previous is not None and previous[1] < threshold <= value:
                previous_time, previous_value = previous
                if value == previous_value:
                    crossings.append(time)
                else:
                    fraction = (threshold - previous_value) / (value - previous_value)
                    crossings.append(previous_time + fraction * (time - previous_time))
            previous = (time, value)
    return crossings


def _validate_side_effect_contract(
    checker_profile: dict[str, Any], csv_path: Path, output_dir: Path
) -> tuple[bool, list[str]]:
    contract = checker_profile.get("side_effect_contract") or {}
    files = contract.get("files") or []
    if not files:
        return True, []
    notes: list[str] = []
    ok = True
    expected_paths: set[Path] = set()
    for item in files:
        relative = Path(str(item.get("path") or ""))
        if not relative.parts or relative.is_absolute() or ".." in relative.parts:
            return False, [f"side_effect_contract_invalid_path={relative}"]
        expected_paths.add(relative)
        path = output_dir / relative
        if not path.is_file():
            ok = False
            notes.append(f"side_effect_missing path={relative.as_posix()}")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        validator = str(item.get("validator") or "regex")
        pattern = str(item.get("record_pattern") or "")
        match = re.fullmatch(pattern, text) if pattern else None
        if pattern and match is None:
            ok = False
            notes.append(
                f"side_effect_format_mismatch path={relative.as_posix()} observed={text!r}"
            )
            continue
        if validator == "regex":
            notes.append(f"side_effect_format_ok path={relative.as_posix()}")
            continue

        signal = str(item["signal"])
        threshold = float(item["threshold"])
        crossings = _trace_rising_crossings(csv_path, signal, threshold)
        if validator == "first_rising_crossing_time":
            if not crossings:
                ok = False
                notes.append(f"side_effect_no_rising_crossing signal={signal}")
                continue
            assert match is not None
            observed = float(match.group(str(item.get("time_group") or "time")))
            expected = crossings[0]
            tolerance = float(item.get("tolerance_s") or 0.0)
            gap = abs(observed - expected)
            passed = gap <= tolerance
            ok = ok and passed
            notes.append(
                "side_effect_crossing_time "
                f"expected={expected:.12g} observed={observed:.12g} "
                f"gap={gap:.3g} tolerance={tolerance:.3g} pass={str(passed).lower()}"
            )
        elif validator == "rising_edge_count_metric":
            assert match is not None
            observed_count = int(match.group(str(item.get("count_group") or "count")))
            observed_metric = float(match.group(str(item.get("metric_group") or "metric")))
            expected_count = len(crossings)
            divisor = float(item["metric_divisor"])
            expected_metric = expected_count / divisor
            tolerance = float(item.get("metric_tolerance") or 0.0)
            metric_gap = abs(observed_metric - expected_metric)
            passed = observed_count == expected_count and metric_gap <= tolerance
            ok = ok and passed
            notes.append(
                "side_effect_count_metric "
                f"expected_count={expected_count} observed_count={observed_count} "
                f"expected_metric={expected_metric:.6g} observed_metric={observed_metric:.6g} "
                f"metric_gap={metric_gap:.3g} tolerance={tolerance:.3g} "
                f"pass={str(passed).lower()}"
            )
        else:
            return False, [f"side_effect_unknown_validator={validator}"]

    if contract.get("exclusive_suffix"):
        suffix = str(contract["exclusive_suffix"])
        observed_paths = {
            path.relative_to(output_dir)
            for path in output_dir.rglob(f"*{suffix}")
            if path.is_file()
        }
        extra = sorted(path.as_posix() for path in observed_paths - expected_paths)
        if extra:
            ok = False
            notes.append(f"side_effect_unexpected_files={','.join(extra)}")
    return ok, notes


def _copy_candidate_sources(
    source_dir: Path,
    run_dir: Path,
    expected_files: list[str],
    *,
    generated_harness: bool,
) -> None:
    missing = [filename for filename in expected_files if not (source_dir / filename).exists()]
    if missing:
        raise SystemExit(f"candidate source directory is missing target artifact(s): {', '.join(missing)}")
    destination = run_dir / "dut" if generated_harness else run_dir
    destination.mkdir(parents=True, exist_ok=True)
    for filename in expected_files:
        source_file = source_dir / filename
        destination_file = destination / filename
        destination_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file, destination_file)


def _safe_va_path(raw: str, *, label: str) -> Path:
    path = Path(raw.replace("\\", "/"))
    if not path.parts or path.is_absolute() or ".." in path.parts or path.suffix != ".va":
        raise SystemExit(f"unsafe {label} path: {raw!r}")
    return path


def _module_names(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    return set(re.findall(r"(?m)^\s*module\s+([A-Za-z_]\w*)", text))


def _copy_public_support(
    task_dir: Path,
    source_dir: Path,
    run_dir: Path,
    expected_candidate_files: list[str],
) -> None:
    family = _read_json(task_dir / "family_spec.json")
    support_contract = family.get("support_contract") or {}
    family_files = list(support_contract.get("files") or [])
    harness_path = task_dir / "evaluator" / "harness_spec.json"
    harness = _read_json(harness_path) if harness_path.is_file() else {}
    harness_support = harness.get("support") or {}
    harness_paths = [str(item) for item in harness_support.get("artifact_paths") or []]
    family_paths = [str(item.get("path") or "") for item in family_files]
    if not family_files and not harness_paths:
        return
    if not family_files or harness_paths != family_paths:
        raise SystemExit(
            "family support_contract and harness support artifact_paths must match exactly"
        )
    if support_contract.get("visibility") != "public_readonly":
        raise SystemExit("support_contract visibility must be public_readonly")
    if support_contract.get("source_root") != "public_support":
        raise SystemExit("support_contract source_root must be public_support")
    if support_contract.get("mount_root") != "support":
        raise SystemExit("support_contract mount_root must be support")
    if harness_support.get("source_root") != "./support":
        raise SystemExit("harness support source_root must be ./support")

    candidate_modules: set[str] = set()
    for raw in expected_candidate_files:
        candidate_modules.update(_module_names(source_dir / _safe_va_path(raw, label="candidate")))

    observed_support_modules: set[str] = set()
    for item in family_files:
        relative = _safe_va_path(str(item.get("path") or ""), label="public support")
        source = task_dir / "public_support" / relative
        if not source.is_file() or source.is_symlink():
            raise SystemExit(f"missing declared public support artifact: {relative.as_posix()}")
        observed_hash = hashlib.sha256(source.read_bytes()).hexdigest()
        if observed_hash != item.get("sha256"):
            raise SystemExit(
                f"public support hash mismatch for {relative.as_posix()}: "
                f"declared={item.get('sha256')} observed={observed_hash}"
            )
        declared_modules = set(str(name) for name in item.get("modules") or [])
        actual_modules = _module_names(source)
        if actual_modules != declared_modules:
            raise SystemExit(
                f"public support module declaration mismatch for {relative.as_posix()}: "
                f"declared={sorted(declared_modules)} observed={sorted(actual_modules)}"
            )
        duplicate_support = observed_support_modules & actual_modules
        if duplicate_support:
            raise SystemExit(
                f"duplicate public support module(s): {', '.join(sorted(duplicate_support))}"
            )
        observed_support_modules.update(actual_modules)
        destination = run_dir / "support" / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)

    collisions = candidate_modules & observed_support_modules
    if collisions:
        raise SystemExit(
            "candidate collides with evaluator-supplied public support module(s): "
            + ", ".join(sorted(collisions))
        )


def _run_oracle(
    script_file: str | Path,
    *,
    profile_name: str,
    source_env: str,
    result_prefix: str,
    checker_task_id: str | None = None,
    timeout_s: int = 60,
    extra_trace_signals: set[str] | frozenset[str] | None = None,
    force_python_engine: bool = False,
) -> int:
    timeout_s = _oracle_timeout(timeout_s)
    script_path = Path(script_file).resolve()
    task_dir = script_path.parents[1] if script_path.parent.name == "test_feedback" else script_path.parents[1]
    contract = _read_json(task_dir / "public_contract.json")
    checker_profile = _load_checker_profile(task_dir)
    effective_checker_task_id = checker_task_id or str(checker_profile.get("checker_task_id") or "")
    source_dir = _candidate_source_dir(source_env)
    expected_files = [str(item) for item in contract.get("target_artifacts") or []]

    repo_root = find_repo_root(task_dir)
    runners_dir = str(repo_root / "runners")
    if runners_dir not in sys.path:
        sys.path.insert(0, runners_dir)
    from simulate_evas import (
        evaluate_behavior,
        required_trace_signals_for_checker,
        run_evas,
        spectre_aligned_veriloga_preflight,
    )

    with tempfile.TemporaryDirectory(prefix=f"v4_{profile_name}_oracle_") as td:
        run_dir = Path(td)
        tb_text, generated_harness = _load_tb_text(task_dir, profile_name)
        _copy_candidate_sources(
            source_dir,
            run_dir,
            expected_files,
            generated_harness=generated_harness,
        )
        _copy_public_support(task_dir, source_dir, run_dir, expected_files)
        tb_dst = run_dir / f"tb_{profile_name}.scs"
        tb_dst.write_text(tb_text, encoding="utf-8")

        preflight = spectre_aligned_veriloga_preflight(run_dir)
        if preflight:
            print(f"{result_prefix}_PREFLIGHT_FAIL")
            for item in preflight:
                print(item)
            return 1

        required_signals = set(extra_trace_signals or ())
        # Preserve the exact scalar/bus expansion selected by the generated
        # harness. A high-level trace contract may spell a bus as b[7:0],
        # while the deck deliberately saves b0..b7 for a checker.
        for line in tb_text.splitlines():
            if line.strip().startswith("save "):
                required_signals.update(line.split()[1:])
        trace_contract = checker_profile.get("trace_contract") or {}
        # The v4 task contract, rather than a legacy checker alias, defines
        # the minimum trace that every oracle run must retain.
        required_signals.update(str(signal) for signal in trace_contract.get("required_signals") or [])
        required_signals.update(str(signal) for signal in trace_contract.get("extra_trace_signals") or [])
        if effective_checker_task_id:
            required_signals.update(required_trace_signals_for_checker(effective_checker_task_id))

        output_dir = run_dir / "out"
        standalone_rust = _standalone_rust_frontend()
        if standalone_rust is not None:
            binary, binary_sha256 = standalone_rust
            result = _run_standalone_rust_frontend(
                binary,
                run_dir,
                tb_dst,
                output_dir,
                timeout_s=timeout_s,
            )
            execution_backend = "standalone-rust"
        else:
            old_engine = os.environ.get("EVAS_ENGINE")
            select_python = _task_wrapper_may_select_python(force_python_engine)
            if select_python:
                os.environ["EVAS_ENGINE"] = "python"
            try:
                result = run_evas(
                    run_dir,
                    tb_dst,
                    output_dir,
                    timeout_s=timeout_s,
                    required_trace_signals=required_signals or None,
                )
            finally:
                if select_python:
                    if old_engine is None:
                        os.environ.pop("EVAS_ENGINE", None)
                    else:
                        os.environ["EVAS_ENGINE"] = old_engine
            execution_backend = "python-rust-hybrid"
            binary_sha256 = ""

        combined = (result.stdout or "") + "\n" + (result.stderr or "")
        if result.returncode != 0:
            print(f"{result_prefix}_EVAS_FAIL")
            print(combined[-4000:])
            return 1
        if execution_backend == "standalone-rust":
            if not result.stdout.startswith("PASS "):
                print(f"{result_prefix}_NO_STANDALONE_PASS_MARKER")
                print(combined[-4000:])
                return 1
            print(
                f"{result_prefix}_EVAS_BACKEND implementation=standalone-rust "
                f"binary_sha256={binary_sha256}"
            )
        else:
            if "Compiled Verilog-A module:" not in combined:
                print(f"{result_prefix}_NO_COMPILE_MARKER")
                print(combined[-4000:])
                return 1
            if "Transient Analysis" not in combined:
                print(f"{result_prefix}_NO_TRAN_MARKER")
                print(combined[-4000:])
                return 1

        if effective_checker_task_id:
            csv_path = output_dir / "tran.csv"
            if not csv_path.exists():
                print(f"{result_prefix}_BEHAVIOR_NO_TRACE")
                print(combined[-4000:])
                return 1
            score, notes = evaluate_behavior(effective_checker_task_id, csv_path)
            if score < 1.0:
                print(f"{result_prefix}_BEHAVIOR_FAIL")
                for note in notes:
                    print(note)
                return 1
            print(f"{result_prefix}_BEHAVIOR_PASS")
            for note in notes:
                print(note)

        csv_path = output_dir / "tran.csv"
        side_effect_ok, side_effect_notes = _validate_side_effect_contract(
            checker_profile, csv_path, output_dir
        )
        if not side_effect_ok:
            print(f"{result_prefix}_SIDE_EFFECT_FAIL")
            for note in side_effect_notes:
                print(note)
            return 1
        for note in side_effect_notes:
            print(note)

        print(f"{result_prefix}_PASS")
        return 0


def run_feedback(
    script_file: str | Path,
    *,
    checker_task_id: str | None = None,
    timeout_s: int = 60,
    extra_trace_signals: set[str] | frozenset[str] | None = None,
    force_python_engine: bool = False,
) -> int:
    return _run_oracle(
        script_file,
        profile_name="feedback",
        source_env="VABENCH_FEEDBACK_SOURCE_DIR",
        result_prefix="FEEDBACK",
        checker_task_id=checker_task_id,
        timeout_s=timeout_s,
        extra_trace_signals=extra_trace_signals,
        force_python_engine=force_python_engine,
    )


def run_score(
    script_file: str | Path,
    *,
    checker_task_id: str | None = None,
    timeout_s: int = 60,
    extra_trace_signals: set[str] | frozenset[str] | None = None,
    force_python_engine: bool = False,
) -> int:
    return _run_oracle(
        script_file,
        profile_name="score",
        source_env="VABENCH_SCORE_SOURCE_DIR",
        result_prefix="SCORE",
        checker_task_id=checker_task_id,
        timeout_s=timeout_s,
        extra_trace_signals=extra_trace_signals,
        force_python_engine=force_python_engine,
    )
