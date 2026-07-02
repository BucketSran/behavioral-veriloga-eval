"""Agent — top-level orchestrator for the vaEvas closed loop.

Merged from the standalone vaEvas-Agent. Key integration changes vs the
standalone repo:
  - The fragile ``sys.path`` heuristic + ``from score import score_one_task``
    is replaced by a direct sibling import (the agent now lives in runners/).
  - v3 tasks no longer take a divergent low-fidelity path: both v1 and v3
    go through ``score.score_one_task`` so behavior checkers actually run.
  - R1+ repair prompts are delegated to ``build_repair_prompt.py`` via
    ``prompt_modes.build_repair_prompt_for_mode`` (config-driven mode).
  - Optional layered repair (``config.loop.layered_repair``) freezes the
    gold harness and restricts the LLM to one editable layer per round.
  - ``model_slug`` is threaded through so output layout matches
    ``<model>/<task>/round_N/sample_0/``.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

from .config import AgentConfig, load_config
from .display import (
    bold, box_footer, box_header, box_line, dim, green,
    round_header, scores_line, status_icon, transition_label, yellow,
)
from .llm.client import LLMError, call_llm
from .loop.controller import LoopController
from .loop.state import LoopState, RoundResult, TaskContext
from .prompts.pipeline import (
    _resolve_gold_path,
    build_system_prompt,
)
from .skills.manager import SkillManager

# ─── Integration with sibling runners/ modules ───────────────
# These imports assume runners/ is on sys.path (the agent subpackage is
# imported either as ``runners.agent`` or via the flat ``sys.path.insert``
# idiom used by every other runner script). score_one_task and the repair
# prompt builders are the only contract.


def _import_score_one_task():
    """Lazily import score.score_one_task, tolerating both import styles."""
    try:
        from score import score_one_task  # type: ignore
        return score_one_task
    except ImportError:
        pass
    try:
        from runners.score import score_one_task  # type: ignore
        return score_one_task
    except ImportError as e:
        raise ImportError(
            "Could not import score.score_one_task. Ensure runners/ is on sys.path."
        ) from e


class Agent:
    """The vaEvas Agent — runs the full closed loop for a Verilog-A benchmark task."""

    def __init__(self, config: AgentConfig | None = None):
        self.config = config or load_config()
        self.skills = SkillManager(
            skills_root=self.config.resolve_path(self.config.paths.veriloga_skills),
            max_chars=self.config.skills.max_chars,
        )
        self.loop = LoopController(
            max_rounds=self.config.loop.max_rounds,
            stall_limit=self.config.loop.stall_limit,
            regress_limit=self.config.loop.regress_limit,
        )
        self._total_tokens = 0
        self._start_time = 0.0

    def run(self, task_id: str, task_dir: Path | str) -> list[RoundResult]:
        """Run the full generate→evaluate→repair loop for one task."""
        task_dir = Path(task_dir)
        self._total_tokens = 0
        self._start_time = time.time()

        context = _build_task_context(task_id, task_dir)
        output_root = self.config.resolve_path(self.config.output.dir)
        model_slug = _model_slug(self.config.llm.model)

        self._print_task_header(context)

        # Effective max_rounds: single-shot modes run exactly 1 round.
        from .prompt_modes import SINGLE_SHOT_MODES
        if self.config.loop.prompt_mode in SINGLE_SHOT_MODES:
            # Temporarily lower max_rounds so the terminator stops after R0.
            self.loop.terminator.max_rounds = 1

        history = self.loop.run(
            context=context,
            output_root=output_root,
            model_slug=model_slug,
            generate_fn=self._generate,
            evaluate_fn=self._evaluate,
            repair_fn=self._build_repair_prompt,
            on_round_start=self._on_round_start,
            on_round_end=self._on_round_end,
        )

        self._print_result(history, output_root / task_id)
        return history

    # ─── Callbacks for LoopController ───────────────────────

    def _on_round_start(self, round_idx: int, stage: str) -> None:
        if stage == "generating":
            temp = self.config.llm.temperature if round_idx == 0 else self.config.llm.repair_temperature
            sys.stdout.write(
                round_header(round_idx,
                    f"{'Generating' if round_idx == 0 else 'Repairing'} "
                    f"with {self.config.llm.model} (T={temp}) ... ")
            )
            sys.stdout.flush()
        elif stage == "evaluating":
            sys.stdout.write("EVAS scoring ... ")
            sys.stdout.flush()

    def _on_round_end(self, result: RoundResult) -> None:
        print(status_icon(result.status), " ", scores_line(result.scores))
        if result.failure_subtype:
            print(f"           {transition_label(result.failure_subtype)}")
            if result.metrics:
                preview = ", ".join(f"{k}={v}" for k, v in list(result.metrics.items())[:4])
                print(f"           {dim('metrics: ' + preview)}")
        sys.stdout.write("\n")
        sys.stdout.flush()

    # ─── Core steps ─────────────────────────────────────────

    def _generate(
        self,
        round_idx: int,
        context: TaskContext,
        iteration_context: dict,
    ) -> dict:
        temp = self.config.llm.temperature if round_idx == 0 else self.config.llm.repair_temperature

        skill_context = ""
        if self.config.skills.enabled:
            skill_context = self.skills.build_skill_context(context.task_id)
            # Optional skill bundle override (mirrors legacy evas_loop --skill-bundle).
            # When set, the bundle file's content is appended to the keyword-matched
            # category reference, giving the user a way to inject a custom/frozen
            # skill bundle regardless of the task's circuit category.
            bundle_path = self.config.skills.bundle_override_path
            if bundle_path:
                resolved = self.config.resolve_path(bundle_path)
                if resolved.exists():
                    try:
                        bundle_text = resolved.read_text(encoding="utf-8", errors="ignore")
                        if bundle_text.strip():
                            skill_context += (
                                "\n\n## Skill Bundle Override"
                                f" ({resolved.name})\n\n{bundle_text}\n"
                            )
                    except OSError:
                        pass

        system = build_system_prompt(skill_context=skill_context)

        if round_idx == 0:
            # Build R0 prompt via the mode dispatcher.
            from .prompt_modes import build_round0_prompt
            user = build_round0_prompt(
                self.config.loop.prompt_mode,
                context.task_dir,
                skill_bundle_text=skill_context,
                include_skill=self.config.loop.include_skill,
            )
        else:
            user = iteration_context.get("repair_prompt", "")

        try:
            response = call_llm(self.config.llm, system, user, temperature=temp)
        except LLMError as e:
            return {
                "response_text": "",
                "input_tokens": 0,
                "output_tokens": 0,
                "elapsed_ms": 0,
                "error": str(e),
            }

        self._total_tokens += response.input_tokens + response.output_tokens

        text = (response.text or "").strip()
        if not text or not _has_va_or_scs_blocks(text):
            return {
                "response_text": "",
                "input_tokens": response.input_tokens,
                "output_tokens": response.output_tokens,
                "elapsed_ms": response.elapsed_ms,
                "error": "empty_response",
            }

        return {
            "response_text": text,
            "input_tokens": response.input_tokens,
            "output_tokens": response.output_tokens,
            "elapsed_ms": response.elapsed_ms,
        }

    def _evaluate(self, sample_dir: Path, context: TaskContext) -> dict:
        """Run EVAS scoring via score.score_one_task (handles both v1 and v3)."""
        try:
            return _run_evas_score(sample_dir, context, timeout_s=self.config.llm.timeout)
        except Exception as e:
            return {
                "status": "FAIL_INFRA",
                "scores": {"dut_compile": 0.0, "tb_compile": 0.0,
                          "sim_correct": 0.0, "weighted_total": 0.0},
                "evas_notes": [f"score error: {e}"],
            }

    def _build_repair_prompt(
        self,
        task_dir: Path,
        sample_dir: Path,
        evas_result: dict,
        history: list[dict],
    ) -> str:
        from .prompt_modes import build_repair_prompt_for_mode

        # Augment compile failures with stdout error lines (absorbed from evas_loop).
        augmented = _augment_notes_with_stdout(evas_result)

        skill_context = ""
        if self.config.skills.enabled:
            task_id = Path(task_dir).name
            skill_context = self.skills.build_skill_context(task_id)

        prompt = build_repair_prompt_for_mode(
            self.config.loop.prompt_mode,
            task_dir,
            sample_dir,
            augmented,
            history=history,
            include_skill=self.config.loop.include_skill,
            skill_bundle_text=skill_context,
        )

        # Optional layered repair policy (absorbed from run_adaptive_repair).
        if self.config.loop.layered_repair:
            from .layered_repair import classify_repair_layer, layer_policy_section, freeze_gold_harness
            layer = classify_repair_layer(augmented)
            prompt += layer_policy_section(layer, task_dir)
            # For behavior layer: freeze the gold harness so only the DUT is judged.
            if layer == "behavior":
                freeze_gold_harness(task_dir, sample_dir)

        return prompt

    # ─── Display ────────────────────────────────────────────

    def _print_task_header(self, context: TaskContext) -> None:
        print()
        print(box_header(f"Task: {context.task_id}"))
        print(box_line(f"Family: {context.family:<14s} Category: {context.category}"))
        if self.skills.available:
            matched = self.skills.match(context.task_id)
            label = matched.name if matched else "none"
            print(box_line(f"Skill:  {label}"))
        mode = self.config.loop.prompt_mode
        if self.config.loop.layered_repair:
            mode += " +layered"
        print(box_line(f"Mode:   {mode}"))
        print(box_footer())
        print()

    def _print_result(self, history: list[RoundResult], output_dir: Path) -> None:
        rounds = len(history)
        last = history[-1] if history else None
        status = last.status if last else "?"
        elapsed = time.time() - self._start_time
        print(box_header(f"Result: {status}"))
        print(box_line(f"Rounds: {rounds}    Total tokens: {self._total_tokens:,}    "
                       f"Total time: {elapsed:.1f}s"))
        print(box_line(f"Output: {output_dir}"))
        print(box_footer())


# ─── Helpers ─────────────────────────────────────────────────


def _model_slug(model: str) -> str:
    return model.replace("/", "_")


def _build_task_context(task_id: str, task_dir: Path) -> TaskContext:
    import json
    meta_path = task_dir / "meta.json"
    meta = {}
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError, UnicodeDecodeError):
            meta = {}

    family = meta.get("family", "end-to-end")
    category = meta.get("category", "unknown")
    required_axes = meta.get("scoring", ["dut_compile", "tb_compile", "sim_correct"])
    gold_dir = _resolve_gold_path(task_dir)

    # v3 task: read task.toml for metadata.
    if not meta_path.exists():
        toml_path = task_dir / "task.toml"
        if toml_path.exists():
            v3_meta = _read_v3_toml_meta(toml_path)
            family = v3_meta.get("family", family)
            category = v3_meta.get("category", category)
            required_axes = v3_meta.get("scoring", required_axes)
            if gold_dir is None:
                sol_dir = task_dir / "solution"
                if sol_dir.is_dir():
                    gold_dir = sol_dir

    return TaskContext(
        task_id=task_id,
        task_dir=task_dir,
        meta=meta,
        family=family,
        category=category,
        required_axes=required_axes,
        gold_dir=gold_dir,
    )


def _read_v3_toml_meta(toml_path: Path) -> dict:
    meta: dict = {}
    form_map = {"dut": "spec-to-va", "bugfix": "bugfix",
                "tb": "tb-generation", "e2e": "end-to-end"}
    try:
        for line in toml_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            s = line.strip()
            if not s or s.startswith("#") or s.startswith("["):
                continue
            if "=" not in s:
                continue
            k, _, v = s.partition("=")
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k == "form":
                meta["family"] = form_map.get(v, "spec-to-va")
            elif k == "category":
                meta["category"] = v
            elif k == "difficulty":
                meta["difficulty"] = v
    except (OSError, UnicodeDecodeError):
        pass
    return meta


def _run_evas_score(sample_dir: Path, context: TaskContext, *, timeout_s: int = 180) -> dict:
    """Run EVAS evaluation via score.score_one_task (works for both v1 and v3).

    The standalone agent had a divergent _run_v3_evas_score that bypassed the
    behavior checkers and only did a binary sim pass/fail. That's deleted —
    score_one_task already handles staging + checkers for both formats.

    timeout_s is forwarded to score_one_task (and onward to run_case) so the
    --timeout-s CLI flag actually controls the simulation timeout.
    """
    score_one_task = _import_score_one_task()
    return score_one_task(
        task_id=context.task_id,
        task_dir=context.task_dir,
        sample_dir=sample_dir,
        output_dir=sample_dir / "evas_output",
        model="agent",
        sample_idx=0,
        temperature=0.0,
        top_p=1.0,
        timeout_s=timeout_s,
    )


def _augment_notes_with_stdout(evas_result: dict) -> dict:
    """For compile failures, prepend key error lines from stdout_tail into notes.

    Absorbed from evas_loop._augment_notes_with_stdout. The repair prompt is
    much more useful when it can see the actual compiler error messages.
    """
    status = evas_result.get("status", "")
    stdout_tail = evas_result.get("stdout_tail", "")
    if status not in ("FAIL_DUT_COMPILE", "FAIL_TB_COMPILE") or not stdout_tail:
        return evas_result

    lines = stdout_tail.splitlines()
    error_lines: list[str] = []
    for i, line in enumerate(lines):
        if any(kw in line for kw in ("Error", "error", "ParseError", "SyntaxError",
                                      "Traceback", "Exception", "FAILED", "fatal",
                                      "Warning", "warning")):
            start = max(0, i - 1)
            end = min(len(lines), i + 3)
            error_lines.extend(lines[start:end])
            if len(error_lines) >= 25:
                break

    if error_lines:
        deduped = list(dict.fromkeys(error_lines))
        compile_note = "compile_log: " + " | ".join(deduped[:20])
        existing = list(evas_result.get("evas_notes", []))
        return {**evas_result, "evas_notes": [compile_note] + existing}
    return evas_result


def _has_va_or_scs_blocks(text: str) -> bool:
    import re
    return bool(re.search(r"```(?:verilog-a|verilog|spectre|sp)\s*\n", text, re.IGNORECASE))
