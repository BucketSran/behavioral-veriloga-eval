"""Loop state types — TaskContext, RoundResult, LoopState.

Unchanged from the standalone vaEvas-Agent. The ``_result_rank`` tie-breaker
is generic (operates on weighted_total + compile axes + sim_correct) — it does
not hardcode task-specific metrics like the legacy run_adaptive_repair did.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class TaskContext:
    """Immutable context for a single benchmark task."""
    task_id: str
    task_dir: Path
    meta: dict
    family: str                     # end-to-end | spec-to-va | bugfix | tb-generation
    category: str
    required_axes: list[str]        # e.g., ["dut_compile", "tb_compile", "sim_correct"]
    gold_dir: Path | None


@dataclass
class RoundResult:
    """Result of a single agent round (generate + evaluate)."""
    round_idx: int
    sample_dir: Path
    status: str                     # PASS / FAIL_DUT_COMPILE / FAIL_TB_COMPILE / FAIL_SIM_CORRECTNESS / FAIL_INFRA
    scores: dict
    evas_notes: list[str]
    metrics: dict = field(default_factory=dict)
    failure_subtype: str = ""
    transition: str = ""            # improved / regressed / stalled / lateral
    comparison: str = ""
    generation_meta: dict = field(default_factory=dict)
    evas_timing: dict = field(default_factory=dict)
    # stdout_tail from the EVAS run — lets _augment_notes_with_stdout recover
    # compiler errors when this round is used as the basis for the next repair
    # prompt (e.g. after a resume from disk).
    stdout_tail: str = ""


@dataclass
class LoopState:
    """Full state of a repair loop for one task."""
    task_context: TaskContext
    history: list[RoundResult] = field(default_factory=list)
    best_result: RoundResult | None = None
    current_round: int = 0

    def last_result(self) -> RoundResult | None:
        return self.history[-1] if self.history else None

    def is_pass(self) -> bool:
        if self.best_result is None:
            return False
        return self.best_result.status == "PASS"

    def add_result(self, result: RoundResult) -> None:
        self.history.append(result)
        self.current_round = len(self.history)

        if self.best_result is None:
            self.best_result = result
            result.transition = "initial"
        elif _result_rank(result) > _result_rank(self.best_result):
            result.transition = "improved"
            result.comparison = _compare_results(result, self.best_result)
            self.best_result = result
        elif _result_rank(result) == _result_rank(self.best_result):
            result.transition = "lateral"
            result.comparison = "same weighted score, different failure surface"
        else:
            result.transition = "regressed"
            result.comparison = _compare_results(self.best_result, result)


def _safe_float(v: object, default: float = 0.0) -> float:
    try:
        return float(v)  # type: ignore[arg-type]
    except (ValueError, TypeError):
        return default


def _result_rank(r: RoundResult) -> tuple:
    """Generic progress rank — no task-specific metric hardcoding.

    The legacy run_adaptive_repair._progress_rank hardcoded DWA-specific metric
    keys (max_active_cells, overlap_count, etc.). Here we use only the
    universally-available score axes. Layered repair / experiment modes that
    need finer-grained ranking can layer on a failure_phase_score separately.
    """
    return (
        1 if r.status == "PASS" else 0,
        _safe_float(r.scores.get("weighted_total", 0.0)),
        _safe_float(r.scores.get("sim_correct", 0.0)),
        _safe_float(r.scores.get("tb_compile", 0.0)),
        _safe_float(r.scores.get("dut_compile", 0.0)),
    )


def _compare_results(better: RoundResult, worse: RoundResult) -> str:
    b_wt = better.scores.get("weighted_total", 0.0)
    w_wt = worse.scores.get("weighted_total", 0.0)
    return f"weighted_total {w_wt:.3f} → {b_wt:.3f}"
