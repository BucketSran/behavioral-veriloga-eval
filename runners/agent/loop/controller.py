"""Loop controller — state machine driving generate → evaluate → diagnose → repair.

Absorbs the resume + per-round JSON persistence from the legacy
``runners/evas_loop.py`` so a crashed/aborted loop can be continued without
re-scoring earlier rounds.

Output layout (aligned with the evas_loop convention that score.py expects):
    <output_root>/<model_slug>/<task_id>/round_<N>/sample_0/{*.va, *.scs}
    <output_root>/<task_id>/round_<N>_result.json
    <output_root>/<task_id>/final_result.json
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

from .state import LoopState, RoundResult, TaskContext
from .terminator import Terminator


class LoopController:
    """Orchestrates the agent's generate→evaluate→repair cycle.

    Does NOT own LLM, skills, or config — those are injected by Agent.
    """

    def __init__(self, max_rounds: int = 3, stall_limit: int = 2, regress_limit: int = 2):
        self.terminator = Terminator(max_rounds, stall_limit, regress_limit)
        self._output_root: Path | None = None
        self._model_slug: str = "agent"
        self._task_results_root: Path | None = None

    def run(
        self,
        context: TaskContext,
        *,
        output_root: Path,
        model_slug: str = "agent",
        generate_fn,            # callable(round_idx, task_context, iteration_context) -> dict
        evaluate_fn,            # callable(sample_dir, task_context) -> dict (evas_result)
        repair_fn,              # callable(task_dir, sample_dir, evas_result, history) -> str
        on_round_start=None,    # optional callback(round_idx, stage)
        on_round_end=None,      # optional callback(result: RoundResult)
        force: bool = False,    # ignore existing final_result.json and re-run
    ) -> list[RoundResult]:
        """Run the full loop. Returns complete history of all rounds."""
        self._output_root = output_root
        self._model_slug = model_slug
        gen_root = output_root / model_slug / context.task_id
        self._task_results_root = output_root / context.task_id
        self._task_results_root.mkdir(parents=True, exist_ok=True)

        state = LoopState(task_context=context)
        iteration_context: dict = {}

        # ── Resume: load prior rounds if not forced ───────────
        start_round = 0
        if not force:
            start_round, resumed = self._resume_from_disk(state, gen_root)
            if resumed and state.is_pass():
                return state.history

        while True:
            round_idx = start_round + len(state.history) if start_round and not state.history else state.current_round
            stopped, reason = self.terminator.should_stop(state)
            if stopped:
                break

            if on_round_start:
                on_round_start(round_idx, "generating")

            sample_dir = self._make_sample_dir(context.task_id, round_idx)

            try:
                if round_idx == 0:
                    result = generate_fn(round_idx, context, iteration_context)
                else:
                    last = state.last_result()
                    if last is None:
                        break
                    evas_result = {
                        "status": last.status,
                        "scores": last.scores,
                        "evas_notes": last.evas_notes,
                        # Carry stdout_tail so the agent's _augment_notes_with_stdout
                        # can recover compiler errors when building the repair prompt.
                        "stdout_tail": last.stdout_tail,
                    }
                    history_dicts = [
                        {"round": r.round_idx, "status": r.status,
                         "scores": r.scores, "transition": r.transition,
                         "failure_subtype": r.failure_subtype}
                        for r in state.history
                    ]
                    repair_prompt = repair_fn(context.task_dir, last.sample_dir,
                                             evas_result, history_dicts)
                    iteration_context["repair_prompt"] = repair_prompt
                    result = generate_fn(round_idx, context, iteration_context)
            except Exception as e:
                result = {
                    "response_text": "",
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "elapsed_ms": 0,
                    "error": f"generate callback failed: {e}",
                }

            _save_generated_files(result, sample_dir)

            if on_round_start:
                on_round_start(round_idx, "evaluating")

            try:
                evas_result = evaluate_fn(sample_dir, context)
            except Exception as e:
                evas_result = {
                    "status": "FAIL_INFRA",
                    "scores": {"dut_compile": 0.0, "tb_compile": 0.0,
                              "sim_correct": 0.0, "weighted_total": 0.0},
                    "evas_notes": [f"evaluate callback failed: {e}"],
                }

            round_result = _build_round_result(round_idx, sample_dir, evas_result, result)
            state.add_result(round_result)

            # Persist per-round result (resume support).
            self._save_round_result(round_result)

            if on_round_end:
                on_round_end(round_result)

            iteration_context["history"] = state.history
            iteration_context["last_result"] = round_result

        # Persist final result.
        self._save_final_result(state)
        return state.history

    def _make_sample_dir(self, task_id: str, round_idx: int) -> Path:
        # Aligned with evas_loop: <model>/<task>/round_N/sample_0/
        d = self._output_root / self._model_slug / task_id / f"round_{round_idx}" / "sample_0"
        d.mkdir(parents=True, exist_ok=True)
        return d

    # ── Resume + persistence (absorbed from evas_loop) ─────────

    def _resume_from_disk(self, state: LoopState, gen_root: Path) -> tuple[int, bool]:
        """Load any existing round_N_result.json files into *state*.

        Returns (start_round, resumed_any). If final_result.json exists and
        represents a pass, the loop will short-circuit.
        """
        final_path = self._task_results_root / "final_result.json"
        if final_path.exists():
            return 0, True  # caller checks state.is_pass()

        resumed_any = False
        start_round = 0
        for r in range(64):  # safety cap
            rpath = self._task_results_root / f"round_{r}_result.json"
            if not rpath.exists():
                break
            try:
                rdata = json.loads(rpath.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                break
            sample_dir = gen_root / f"round_{r}" / "sample_0"
            round_result = RoundResult(
                round_idx=r,
                sample_dir=sample_dir,
                status=rdata.get("status", "FAIL_INFRA"),
                scores=rdata.get("scores", {}),
                evas_notes=rdata.get("evas_notes", []),
                failure_subtype=rdata.get("failure_subtype", ""),
                transition=rdata.get("transition", ""),
                generation_meta=rdata.get("generation_meta", {}),
                stdout_tail=rdata.get("stdout_tail", ""),
            )
            state.history.append(round_result)
            state.best_result = round_result  # last loaded is provisional best
            state.current_round = len(state.history)
            start_round = r + 1
            resumed_any = True
            if round_result.status == "PASS":
                break
        # Re-evaluate best from the full loaded history.
        if state.history:
            state.best_result = max(state.history, key=lambda r: _rank_tuple(r))
        return start_round, resumed_any

    def _save_round_result(self, result: RoundResult) -> None:
        payload = {
            "round": result.round_idx,
            "status": result.status,
            "scores": result.scores,
            "evas_notes": result.evas_notes[:20],
            "failure_subtype": result.failure_subtype,
            "transition": result.transition,
            "metrics": {k: v for k, v in list(result.metrics.items())[:20]},
            "generation_meta": result.generation_meta,
            # Persist stdout_tail so a resumed round can feed compiler errors
            # back into the repair prompt without re-scoring.
            "stdout_tail": result.stdout_tail,
        }
        path = self._task_results_root / f"round_{result.round_idx}_result.json"
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _save_final_result(self, state: LoopState) -> None:
        if not state.history:
            return
        last = state.history[-1]
        passed_round = next(
            (r.round_idx for r in state.history if r.status == "PASS"), None
        )
        payload = {
            "task_id": state.task_context.task_id,
            "status": last.status,
            "scores": last.scores,
            "passed_round": passed_round,
            "total_rounds_run": len(state.history),
            "max_rounds": self.terminator.max_rounds,
            "stop_reason": self.terminator.summary(state),
        }
        path = self._task_results_root / "final_result.json"
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _rank_tuple(r: RoundResult) -> tuple:
    # Local mirror of state._result_rank for resume-time best selection.
    def sf(v, d=0.0):
        try:
            return float(v)
        except (ValueError, TypeError):
            return d
    return (
        1 if r.status == "PASS" else 0,
        sf(r.scores.get("weighted_total", 0.0)),
        sf(r.scores.get("sim_correct", 0.0)),
        sf(r.scores.get("tb_compile", 0.0)),
        sf(r.scores.get("dut_compile", 0.0)),
    )


def _save_generated_files(result, sample_dir: Path) -> None:
    """Extract and save generated .va and .scs files from LLM response."""
    text = result.get("response_text", "") if isinstance(result, dict) else getattr(result, "response_text", "")
    if not text:
        return

    va_blocks = _extract_code_blocks(text, "verilog-a")
    scs_blocks = _extract_code_blocks(text, "spectre")

    for i, code in enumerate(va_blocks):
        module_name = _infer_module_name(code) or f"module_{i}"
        try:
            (sample_dir / f"{module_name}.va").write_text(code, encoding="utf-8")
        except OSError:
            pass

    for i, code in enumerate(scs_blocks):
        tb_name = _infer_tb_name(code) or f"tb_generated_{i}"
        try:
            (sample_dir / f"{tb_name}.scs").write_text(code, encoding="utf-8")
        except OSError:
            pass


def _extract_code_blocks(text: str, lang: str) -> list[str]:
    pattern = rf"```(?:{lang}|{'verilog' if lang == 'verilog-a' else lang})\s*\n(.*?)```"
    return [m.group(1).strip() for m in re.finditer(pattern, text, re.DOTALL | re.IGNORECASE)]


def _infer_module_name(va_code: str) -> str | None:
    m = re.search(r"\bmodule\s+(\w+)", va_code)
    return m.group(1) if m else None


def _infer_tb_name(scs_code: str) -> str | None:
    m = re.search(r"Cell name:\s*(\S+)", scs_code)
    if m:
        return m.group(1)
    m = re.search(r"(tb_\w+)", scs_code)
    return m.group(1) if m else None


def _build_round_result(
    round_idx: int,
    sample_dir: Path,
    evas_result: dict,
    generation_meta: dict,
) -> RoundResult:
    notes = evas_result.get("evas_notes") or evas_result.get("notes") or []
    scores = evas_result.get("scores", {})
    status = evas_result.get("status", "FAIL_INFRA")

    note_text = " ".join(str(n) for n in notes).lower()
    if any(m in note_text for m in ("missing ", "tran.csv missing", "too_few_", "insufficient_")):
        subtype = "observability_contract"
    elif any(m in note_text for m in ("timeout", "evas_timeout", "tb_not_executed")):
        subtype = "simulation_artifact"
    else:
        subtype = "behavior_semantic"

    metrics = {}
    for note in notes:
        for match in re.finditer(r"([A-Za-z_][A-Za-z0-9_]*)=([^\s,;]+)", str(note)):
            key, val = match.group(1), match.group(2)
            try:
                metrics[key] = float(val)
            except ValueError:
                metrics[key] = val

    return RoundResult(
        round_idx=round_idx,
        sample_dir=sample_dir,
        status=status,
        scores=scores,
        evas_notes=[str(n)[:200] for n in notes],
        metrics=metrics,
        failure_subtype=subtype,
        generation_meta=generation_meta,
        evas_timing=evas_result.get("timing", {}),
        stdout_tail=evas_result.get("stdout_tail", ""),
    )
