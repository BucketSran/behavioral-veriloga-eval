from __future__ import annotations

import csv
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from pathlib import PurePosixPath
from typing import Any


REQUIRED_EVAS_VERSION = "0.8.4"


class CaseOutcome(str, Enum):
    REFERENCE_PASS = "reference_pass"
    REFERENCE_FAIL = "reference_fail"
    KILLED_BEHAVIORALLY = "killed_behaviorally"
    SURVIVED = "survived"
    INVALID_RUN = "invalid_run"


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    role: str
    outcome: CaseOutcome
    notes: tuple[str, ...]

    @property
    def counts_as_kill(self) -> bool:
        return self.role == "negative" and self.outcome is CaseOutcome.KILLED_BEHAVIORALLY


@dataclass(frozen=True)
class TestbenchResult:
    reference: CaseResult
    negatives: tuple[CaseResult, ...]
    expected_negative_count: int = 5

    @property
    def killed_count(self) -> int:
        return sum(result.counts_as_kill for result in self.negatives)

    @property
    def invalid_count(self) -> int:
        return sum(result.outcome is CaseOutcome.INVALID_RUN for result in self.negatives)

    @property
    def survived_count(self) -> int:
        return sum(result.outcome is CaseOutcome.SURVIVED for result in self.negatives)

    @property
    def passed(self) -> bool:
        return (
            self.reference.outcome is CaseOutcome.REFERENCE_PASS
            and len(self.negatives) == self.expected_negative_count
            and self.killed_count == self.expected_negative_count
        )


def _find_repo_root(package_root: Path) -> Path:
    for parent in [package_root, *package_root.parents]:
        if (parent / "runners" / "simulate_evas.py").exists():
            return parent
    raise SystemExit("cannot find behavioral-veriloga-eval repo root")


def _module_names(source: Path) -> list[str]:
    text = source.read_text(encoding="utf-8", errors="ignore")
    return re.findall(r"\bmodule\s+([A-Za-z_][A-Za-z0-9_$]*)", text)


def _target_name_for_negative(negative_source: Path, target_artifacts: list[str]) -> str:
    if len(target_artifacts) == 1:
        return target_artifacts[0]
    module_names = set(_module_names(negative_source))
    for artifact in target_artifacts:
        if Path(artifact).stem in module_names:
            return artifact
    raise SystemExit(
        f"cannot map negative {negative_source} to one of target artifacts: {', '.join(target_artifacts)}"
    )


def _negative_bundle_sources(negative_bundle: Path, target_artifacts: list[str]) -> dict[str, Path]:
    if negative_bundle.is_file():
        return {_target_name_for_negative(negative_bundle, target_artifacts): negative_bundle}
    if not negative_bundle.is_dir():
        raise ValueError(f"negative bundle is missing: {negative_bundle}")
    candidates = sorted(negative_bundle.rglob("*.va"))
    if not candidates:
        raise ValueError(f"negative bundle has no Verilog-A source: {negative_bundle}")
    by_basename: dict[str, list[str]] = {}
    for artifact in target_artifacts:
        by_basename.setdefault(Path(artifact).name, []).append(artifact)
    mapped: dict[str, Path] = {}
    deferred: list[Path] = []
    for source in candidates:
        relative = source.relative_to(negative_bundle).as_posix()
        if relative in target_artifacts:
            target = relative
        else:
            matches = by_basename.get(source.name) or []
            if len(matches) == 1:
                target = matches[0]
            else:
                deferred.append(source)
                continue
        if target in mapped:
            raise ValueError(f"negative bundle maps multiple files to {target}")
        mapped[target] = source
    for source in deferred:
        target = _target_name_for_negative(source, target_artifacts)
        if target not in mapped:
            mapped[target] = source
    if not mapped:
        raise ValueError("negative bundle does not map to a declared DUT artifact")
    return mapped


def _prepare_dut_sources(
    *,
    package_root: Path,
    source_formal: Path,
    run_dir: Path,
    target_artifacts: list[str],
    negative_bundle: Path | None = None,
    dut_subdir: str | None = None,
    public_contract: dict[str, Any] | None = None,
) -> None:
    supplied = (public_contract or {}).get("supplied_inputs") or {}
    include_by_artifact = {
        str(item.get("public_input_path") or "").removeprefix("supplied_dut/"): str(
            item.get("testbench_include_path") or ""
        )
        for item in supplied.get("read_only_dut_artifacts") or []
    }

    def include_target(include_path: str) -> Path:
        logical = PurePosixPath(include_path)
        if logical.is_absolute() or ".." in logical.parts:
            raise ValueError(f"invalid logical include path: {include_path}")
        return run_dir.joinpath(*[part for part in logical.parts if part != "."])

    target_root = run_dir / dut_subdir if dut_subdir else run_dir
    for artifact in target_artifacts:
        source = source_formal / "solution" / artifact
        if not source.is_file():
            source = source_formal / "trusted_solution" / artifact
        if not source.exists():
            raise SystemExit(f"missing gold DUT artifact: {source}")
        include_path = include_by_artifact.get(artifact)
        target = include_target(include_path) if include_path else target_root / artifact
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    if negative_bundle is not None:
        for target_name, source in _negative_bundle_sources(negative_bundle, target_artifacts).items():
            include_path = include_by_artifact.get(target_name)
            target = include_target(include_path) if include_path else target_root / target_name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    support_root = source_formal / "public_support"
    for item in supplied.get("read_only_support_artifacts") or []:
        public_path = str(item.get("public_input_path") or "")
        relative = public_path.removeprefix("public_support/")
        source = support_root / relative
        if not source.is_file():
            raise SystemExit(f"missing public support artifact: {source}")
        target = include_target(str(item.get("testbench_include_path") or ""))
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    for public_path in (public_contract or {}).get("supplied_support_artifacts") or []:
        relative = str(public_path).removeprefix("supplied_dut/")
        source = source_formal / "solution" / relative
        if not source.is_file():
            source = source_formal / "trusted_solution" / relative
        if not source.is_file():
            raise SystemExit(f"missing public support artifact: {source}")
        target = run_dir / "dut" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def _trace_is_valid(csv_path: Path, required_signals: set[str]) -> tuple[bool, list[str]]:
    try:
        with csv_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.reader(handle)
            header = next(reader, [])
            first_row = next(reader, None)
    except (OSError, csv.Error, UnicodeError) as exc:
        return False, [f"trace read failed: {type(exc).__name__}"]
    def expand(name: str) -> set[str]:
        match = re.fullmatch(r"(.+)\[(\d+):(\d+)\]", name)
        if match is None:
            return {name.lower()}
        base, first, last = match.groups()
        start = int(first)
        stop = int(last)
        step = -1 if start > stop else 1
        return {f"{base}{index}".lower() for index in range(start, stop + step, step)}

    required = {value for item in required_signals for value in expand(str(item))}
    present = {value for item in header for value in expand(str(item))}
    missing = sorted(required - present)
    if missing:
        return False, ["missing required trace signals: " + ", ".join(missing)]
    if first_row is None:
        return False, ["transient trace contains no data rows"]
    return True, []


def _case_result(
    *,
    label: str,
    role: str,
    valid: bool,
    behavior_pass: bool | None,
    notes: list[str],
) -> CaseResult:
    if not valid:
        outcome = CaseOutcome.INVALID_RUN
    elif role == "reference":
        outcome = CaseOutcome.REFERENCE_PASS if behavior_pass else CaseOutcome.REFERENCE_FAIL
    else:
        outcome = CaseOutcome.SURVIVED if behavior_pass else CaseOutcome.KILLED_BEHAVIORALLY
    return CaseResult(label, role, outcome, tuple(notes))


def _evas_engine_value(text: str, key: str) -> str | None:
    match = re.search(
        rf"^\s*{re.escape(key)}\s*=\s*([^\s]+)",
        text,
        flags=re.MULTILINE,
    )
    return match.group(1).strip() if match else None


def _validate_required_evas_engine(
    combined: str,
    required_engine: str | None,
) -> tuple[bool, str]:
    """Validate the requested engine and simulator's reported backend."""
    requested = os.environ.get("EVAS_ENGINE", "").strip().lower()
    default = os.environ.get("VAEVAS_DEFAULT_EVAS_ENGINE", "").strip().lower()
    effective = requested or default
    if required_engine is None:
        return True, f"evas_engine={effective or 'unspecified'}"
    required = required_engine.strip().lower()
    if requested != required or default != required or effective != required:
        return (
            False,
            "engine_policy_violation="
            f"required={required} EVAS_ENGINE={requested or '<unset>'} "
            f"VAEVAS_DEFAULT_EVAS_ENGINE={default or '<unset>'}",
        )
    if required != "evas2":
        return True, f"evas_engine={effective} evas_engine_used={effective}"

    version_match = re.search(r"^Version\s+([^\s]+)", combined, flags=re.MULTILINE)
    observed_version = version_match.group(1) if version_match else None
    reported_engine = _evas_engine_value(combined, "evas_engine")
    rust_required = _evas_engine_value(combined, "evas_rust_required")
    rust_full_model_required = _evas_engine_value(
        combined, "evas_rust_full_model_required"
    )
    failures = _evas_engine_value(combined, "rust_full_model_required_failures")
    if observed_version != REQUIRED_EVAS_VERSION:
        return False, f"engine_validation_failed=version observed={observed_version!r}"
    if reported_engine != "evas-rust":
        return False, f"engine_validation_failed=backend observed={reported_engine!r}"
    if rust_required != "true" or rust_full_model_required != "true":
        return (
            False,
            "engine_validation_failed=rust_required "
            f"evas_rust_required={rust_required!r} "
            f"evas_rust_full_model_required={rust_full_model_required!r}",
        )
    if failures not in {None, "0", "0.0"}:
        return False, f"engine_validation_failed=rust_required_failures observed={failures}"
    return (
        True,
        f"evas_engine=evas2 evas_engine_used=evas2 evas_version={REQUIRED_EVAS_VERSION} "
        "evas_backend=rust evas_reported_engine=evas-rust",
    )


def _simulation_failure_excerpt(combined: str, *, limit: int = 4000) -> str:
    """Preserve root-cause lines even when EVAS appends long counter reports."""
    diagnostic = re.compile(
        r"\b(error|errors|fatal|failed|failure|invalid|unsupported|unknown|"
        r"unrecognized|unexpected|cannot|exception|traceback|parse|syntax)\b|"
        r"no such file|not found|can't\s",
        flags=re.IGNORECASE,
    )
    lines = [line.strip() for line in combined.splitlines() if line.strip()]
    selected: list[str] = []
    for index, line in enumerate(lines):
        if diagnostic.search(line) is None:
            continue
        for nearby in lines[max(0, index - 1) : min(len(lines), index + 2)]:
            if nearby not in selected:
                selected.append(nearby)
    if not selected:
        selected = lines[:6] + lines[-6:]
    return "\n".join(selected)[:limit]


def _run_case(
    *,
    package_root: Path,
    tb_source: Path,
    source_formal: Path,
    target_artifacts: list[str],
    negative_bundle: Path | None,
    checker_task_id: str,
    required_signals: set[str],
    label: str,
    dut_subdir: str | None = None,
    public_contract: dict[str, Any] | None = None,
    required_evas_engine: str | None = None,
) -> CaseResult:
    repo_root = _find_repo_root(package_root)
    runners_dir = str(repo_root / "runners")
    if runners_dir not in sys.path:
        sys.path.insert(0, runners_dir)
    from simulate_evas import evaluate_behavior, run_evas

    role = "reference" if negative_bundle is None else "negative"
    with tempfile.TemporaryDirectory(prefix=f"v4_tb_feedback_{label}_") as td:
        run_dir = Path(td)
        tb_dst = run_dir / "tb_candidate.scs"
        shutil.copy2(tb_source, tb_dst)
        try:
            _prepare_dut_sources(
                package_root=package_root,
                source_formal=source_formal,
                run_dir=run_dir,
                target_artifacts=target_artifacts,
                negative_bundle=negative_bundle,
                dut_subdir=dut_subdir,
                public_contract=public_contract,
            )
        except (OSError, SystemExit, ValueError) as exc:
            return _case_result(
                label=label,
                role=role,
                valid=False,
                behavior_pass=None,
                notes=[f"{label}: DUT staging failed: {str(exc)[:300]}"],
            )
        output_dir = run_dir / "out"
        try:
            result = run_evas(
                run_dir,
                tb_dst,
                output_dir,
                timeout_s=60,
                required_trace_signals=required_signals,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return _case_result(
                label=label,
                role=role,
                valid=False,
                behavior_pass=None,
                notes=[f"{label}: simulation invocation failed: {type(exc).__name__}"],
            )
        combined = (result.stdout or "") + "\n" + (result.stderr or "")
        engine_ok, engine_note = _validate_required_evas_engine(
            combined, required_evas_engine
        )
        if not engine_ok:
            return _case_result(
                label=label,
                role=role,
                valid=False,
                behavior_pass=None,
                notes=[f"{label}: {engine_note}"],
            )
        if result.returncode != 0:
            return _case_result(
                label=label,
                role=role,
                valid=False,
                behavior_pass=None,
                notes=[
                    f"{label}: {engine_note}",
                    f"{label}: simulation failed",
                    _simulation_failure_excerpt(combined),
                ],
            )
        csv_path = output_dir / "tran.csv"
        if not csv_path.exists():
            return _case_result(
                label=label,
                role=role,
                valid=False,
                behavior_pass=None,
                notes=[f"{label}: {engine_note}", f"{label}: no transient trace produced"],
            )
        trace_valid, trace_notes = _trace_is_valid(csv_path, required_signals)
        if not trace_valid:
            return _case_result(
                label=label,
                role=role,
                valid=False,
                behavior_pass=None,
                notes=[f"{label}: {engine_note}"] + [f"{label}: {note}" for note in trace_notes],
            )
        try:
            score, notes = evaluate_behavior(checker_task_id, csv_path)
        except Exception as exc:  # Checker exceptions are evaluator-invalid, not behavioral kills.
            return _case_result(
                label=label,
                role=role,
                valid=False,
                behavior_pass=None,
                notes=[f"{label}: {engine_note}", f"{label}: checker failed: {type(exc).__name__}: {str(exc)[:300]}"],
            )
        return _case_result(
            label=label,
            role=role,
            valid=True,
            behavior_pass=score >= 1.0,
            notes=[f"{label}: {engine_note}"] + [f"{label}: " + note for note in notes],
        )
