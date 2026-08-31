"""Opt-in, single-process spending guard for the named DeepSeek pilot.

This is not a benchmark stopping rule or an account-wide provider spending cap.
The normal CLI does not instantiate it. Share one budget across every pilot
cell, keep its private journal, and never resume by creating a new budget.
"""

from decimal import Decimal, InvalidOperation
import hashlib
import json
import math
import os
from pathlib import Path
import re
from threading import RLock

from run_campaign import OpenAICompatible, parse_openai_sse_response


MODEL = "deepseek-v4-flash"
CONTEXT_TOKEN_BOUND = 1_048_576  # Conservative interpretation of documented 1M.
MAX_OUTPUT_TOKENS = 4096
RATES = {
    "CNY": (Decimal("3.00"), Decimal("9.00"), Decimal("5.00")),
    "USD": (Decimal("0.44"), Decimal("1.32"), Decimal("0.70")),
}


class PilotBudgetStop(RuntimeError):
    """Operational censoring: not a model failure or an ordinary r53 score."""


class DeepSeekPilotBudget:
    def __init__(self, journal: Path, *, cell_ids: list[str], currency="CNY", cap=None,
                 model_call_limit=8):
        if model_call_limit is not None and (type(model_call_limit) is not int or model_call_limit <= 0):
            raise ValueError("pilot model-call limit must be a positive integer or None")
        self.model_call_limit = model_call_limit
        if currency not in RATES:
            raise ValueError("pilot currency must be CNY or USD")
        self.input_rate, self.output_rate, maximum = RATES[currency]
        try:
            self.cap = Decimal(str(cap)) if cap is not None else maximum
        except InvalidOperation:
            raise ValueError("invalid pilot cap") from None
        if not self.cap.is_finite() or not 0 < self.cap <= maximum:
            raise ValueError("cap exceeds authorized pilot ceiling or is invalid")
        if (not cell_ids or len(cell_ids) > 6
                or any(not isinstance(cell, str) or not re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}", cell)
                       for cell in cell_ids)
                or len(set(cell_ids)) != len(cell_ids)):
            raise ValueError("freeze one to six distinct pilot cells")
        self.cell_ids = tuple(cell_ids)
        self.model_calls = dict.fromkeys(self.cell_ids, 0)
        self.currency = currency
        self.committed = Decimal(0)
        self.stopped = False
        self.lock = RLock()
        fd = os.open(journal, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        self.journal = os.fdopen(fd, "w", encoding="utf-8")
        try:
            self._record("opened", cell_ids=cell_ids, currency=currency, cap=str(self.cap),
                         input_miss_peak_per_million=str(self.input_rate),
                         output_peak_per_million=str(self.output_rate),
                         context_token_bound=CONTEXT_TOKEN_BOUND, model=MODEL,
                         model_call_limit_per_cell=model_call_limit, max_output_tokens=MAX_OUTPUT_TOKENS,
                         pricing_date="2026-08-30", may_enter_model_memory=False)
        except BaseException:
            self.journal.close()
            raise

    def _record(self, event, **fields):
        try:
            self.journal.write(json.dumps({
                "event": event, "committed_upper_bound": str(self.committed), **fields,
            }, sort_keys=True) + "\n")
            self.journal.flush()
            os.fsync(self.journal.fileno())
        except BaseException:
            self.stopped = True
            raise

    def _check_active_cell(self, cell_id):
        if self.stopped or self.journal.closed:
            raise PilotBudgetStop("pilot budget is stopped or closed")
        if cell_id not in self.cell_ids:
            raise ValueError("cell is not in the frozen pilot schedule")

    def begin_call(self, cell_id):
        with self.lock:
            self._check_active_cell(cell_id)
            if self.model_call_limit is not None and self.model_calls[cell_id] >= self.model_call_limit:
                self._record("cell_stopped", reason="model_call_limit", cell_id=cell_id)
                raise PilotBudgetStop("pilot model-call ceiling reached for this cell")
            self.model_calls[cell_id] += 1
            self._record("model_call", cell_id=cell_id, model_call=self.model_calls[cell_id])

    def request(self, *, cell_id, max_tokens, send):
        with self.lock:
            self._check_active_cell(cell_id)
            if type(max_tokens) is not int or not 0 < max_tokens <= MAX_OUTPUT_TOKENS:
                raise ValueError("invalid pilot output cap")
            reservation = (CONTEXT_TOKEN_BOUND * self.input_rate
                           + max_tokens * self.output_rate) / 1_000_000
            if self.committed + reservation > self.cap:
                self.stopped = True
                self._record("stopped", reason="insufficient_reservation", cell_id=cell_id)
                raise PilotBudgetStop("insufficient reservation for another HTTP attempt")
            self.committed += reservation
            self._record("reserved", cell_id=cell_id, reservation=str(reservation),
                         model_call=self.model_calls[cell_id], max_tokens=max_tokens)
            try:
                completed = send()
                measured = self._usage_bound(completed, max_tokens)
            except BaseException:
                self.stopped = True
                self._record("stopped", reason="unknown_request_cost", cell_id=cell_id)
                raise
            if measured is None:
                self.stopped = True
                self._record("stopped", reason="unknown_request_cost", cell_id=cell_id)
                raise PilotBudgetStop("unknown request cost; full reservation retained")
            self.committed -= reservation - measured
            self._record("reconciled", cell_id=cell_id, request_upper_bound=str(measured),
                         response_sha256=hashlib.sha256(completed.stdout.encode()).hexdigest())
            return completed

    def _usage_bound(self, completed, max_tokens):
        if completed.returncode != 0:
            return None
        try:
            chunks = [line.strip()[5:].strip() for line in completed.stdout.splitlines()
                      if line.strip().startswith("data:")]
            if len(chunks) < 2 or chunks[-1] != "[DONE]" or chunks.count("[DONE]") != 1:
                return None
            response = parse_openai_sse_response(completed.stdout)
            if response.get("model") not in {MODEL, "DeepSeek-V4-Flash-0731"}:
                return None
            choice = response["choices"][0]
            if not choice.get("finish_reason") or choice["message"].get("reasoning_content"):
                return None
            # Only the final completed stream chunk may release a reservation.
            usage = json.loads(chunks[-2])["usage"]
            prompt, output, total = (usage[key] for key in (
                "prompt_tokens", "completion_tokens", "total_tokens"))
            if any(type(value) is not int or value < 0 for value in (prompt, output, total)):
                return None
            if prompt > CONTEXT_TOKEN_BOUND or output > max_tokens or total != prompt + output:
                return None
            if "prompt_cache_hit_tokens" in usage or "prompt_cache_miss_tokens" in usage:
                hit, miss = usage["prompt_cache_hit_tokens"], usage["prompt_cache_miss_tokens"]
                if (any(type(value) is not int or value < 0 for value in (hit, miss))
                        or hit + miss != prompt):
                    return None
            if usage.get("completion_tokens_details", {}).get("reasoning_tokens", 0) != 0:
                return None
            return (prompt * self.input_rate + output * self.output_rate) / 1_000_000
        except (KeyError, TypeError, ValueError, RuntimeError, IndexError, AttributeError):
            return None

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.journal.close()


class BudgetedDeepSeekClient(OpenAICompatible):
    """Reuse the existing SSE transport/capture; keep pilot knobs out of defaults."""

    def __init__(self, *, budget: DeepSeekPilotBudget, cell_id: str, api_key: str, timeout_s=120):
        try:
            valid_timeout = (type(timeout_s) in (int, float)
                             and math.isfinite(timeout_s) and timeout_s > 0)
        except OverflowError:
            valid_timeout = False
        if not valid_timeout:
            raise ValueError("request timeout must be a finite positive number")
        super().__init__(base_url="https://api.deepseek.com", model=MODEL,
                         api_key=api_key, timeout_s=timeout_s, temperature=0, stream=True)
        self.budget = budget
        self.cell_id = cell_id
        self._call_lock = RLock()

    def complete(self, messages, max_tokens, tools, *, timeout_s=None, transport_observer=None):
        if type(max_tokens) is not int or not 0 < max_tokens <= MAX_OUTPUT_TOKENS:
            raise ValueError("pilot output cap must be an integer from 1 to 4096")
        with self._call_lock:
            if self.endpoint != "https://api.deepseek.com/v1/chat/completions" or self.model != MODEL:
                raise ValueError("pilot model/endpoint differs from the frozen provider contract")
            self.budget.begin_call(self.cell_id)
            self._max_tokens = max_tokens
            payload = {
                "model": MODEL, "messages": messages, "max_tokens": max_tokens,
                "temperature": 0, "thinking": {"type": "disabled"},
                "stream": True, "stream_options": {"include_usage": True},
            }
            if tools:
                payload.update(tools=tools, tool_choice="auto")
            return self._complete_stream(payload, timeout_s=timeout_s or self.timeout_s,
                                         transport_observer=transport_observer)

    def _capture_transport(self, execute, *, attempt, observer):
        return self.budget.request(
            cell_id=self.cell_id, max_tokens=self._max_tokens,
            send=lambda: super(BudgetedDeepSeekClient, self)._capture_transport(
                execute, attempt=attempt, observer=observer,
            ),
        )
