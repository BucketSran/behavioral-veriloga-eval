#!/usr/bin/env python3
"""Calibrate OpenAI-compatible provider concurrency with streaming telemetry.

The probe intentionally uses no benchmark-private inputs. It measures the
provider/network path separately from vaBench agent and simulator work.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import http.client
import json
import math
import os
from pathlib import Path
import socket
import statistics
import threading
import time
from typing import Any
from urllib.parse import urlparse


SCHEMA_VERSION = "vabench-provider-concurrency-calibration-v1"
DEFAULT_PROMPT = (
    "Return exactly one line containing the word READY followed by a short "
    "integer checksum of the ASCII string VABENCH. Do not explain."
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_key(path: str | None, env_name: str) -> str:
    value = os.environ.get(env_name, "").strip()
    if value:
        return value
    if path:
        value = Path(path).expanduser().read_text(encoding="utf-8").strip()
        if value:
            return value
    raise SystemExit(f"missing credential: set {env_name} or use --api-key-file")


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil(q * len(ordered)) - 1))
    return ordered[index]


def metric_summary(values: list[float]) -> dict[str, float | int | None]:
    return {
        "count": len(values),
        "min": min(values) if values else None,
        "median": statistics.median(values) if values else None,
        "p90": percentile(values, 0.90),
        "p95": percentile(values, 0.95),
        "max": max(values) if values else None,
    }


@dataclass
class ProbeResult:
    request_id: str
    concurrency: int
    wave: int
    slot: int
    status: str
    http_status: int | None
    started_at: str
    response_headers_s: float | None
    first_sse_data_s: float | None
    stream_after_first_data_s: float | None
    total_s: float
    chunk_count: int
    completion_tokens: int | None
    reasoning_tokens: int | None
    finish_reason: str | None
    response_id: str | None
    error_type: str | None
    error: str | None


def endpoint_parts(base_url: str) -> tuple[str, int | None, str]:
    parsed = urlparse(base_url.rstrip("/"))
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("calibration requires an https OpenAI-compatible base URL")
    path = parsed.path.rstrip("/")
    if not path.endswith("/chat/completions"):
        path += "/chat/completions" if path.endswith("/v1") else "/v1/chat/completions"
    return parsed.hostname, parsed.port, path


def run_probe(
    *,
    base_url: str,
    api_key: str,
    model: str,
    prompt: str,
    max_tokens: int,
    temperature: float,
    concurrency: int,
    wave: int,
    slot: int,
    barrier: threading.Barrier,
    connect_timeout_s: float,
    idle_timeout_s: float,
    total_timeout_s: float,
) -> ProbeResult:
    request_id = f"c{concurrency}-w{wave}-s{slot}"
    host, port, path = endpoint_parts(base_url)
    payload = json.dumps(
        {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }
    ).encode("utf-8")
    barrier.wait()
    started_wall = now()
    started = time.monotonic()
    headers_elapsed: float | None = None
    first_data_elapsed: float | None = None
    chunks = 0
    usage: dict[str, Any] = {}
    finish_reason: str | None = None
    response_id: str | None = None
    status_code: int | None = None
    connection: http.client.HTTPSConnection | None = None
    try:
        connection = http.client.HTTPSConnection(
            host, port=port, timeout=connect_timeout_s
        )
        connection.request(
            "POST",
            path,
            body=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "text/event-stream",
                "Accept-Encoding": "identity",
            },
        )
        response = connection.getresponse()
        status_code = response.status
        headers_elapsed = time.monotonic() - started
        if connection.sock is not None:
            connection.sock.settimeout(idle_timeout_s)
        if response.status != 200:
            detail = response.read(4000).decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {response.status}: {detail}")
        while True:
            if time.monotonic() - started > total_timeout_s:
                raise TimeoutError(
                    f"request exceeded total timeout {total_timeout_s:.1f}s"
                )
            raw = response.readline()
            if not raw:
                break
            line = raw.decode("utf-8", errors="replace").strip()
            if not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if data == "[DONE]":
                break
            if first_data_elapsed is None:
                first_data_elapsed = time.monotonic() - started
            chunks += 1
            chunk = json.loads(data)
            response_id = str(chunk.get("id") or response_id or "") or None
            if chunk.get("usage"):
                usage = dict(chunk["usage"])
            choices = chunk.get("choices") or []
            if choices and choices[0].get("finish_reason") is not None:
                finish_reason = str(choices[0]["finish_reason"])
        total = time.monotonic() - started
        details = usage.get("completion_tokens_details") or {}
        return ProbeResult(
            request_id=request_id,
            concurrency=concurrency,
            wave=wave,
            slot=slot,
            status="ok",
            http_status=status_code,
            started_at=started_wall,
            response_headers_s=headers_elapsed,
            first_sse_data_s=first_data_elapsed,
            stream_after_first_data_s=(
                total - first_data_elapsed
                if first_data_elapsed is not None
                else None
            ),
            total_s=total,
            chunk_count=chunks,
            completion_tokens=usage.get("completion_tokens"),
            reasoning_tokens=details.get("reasoning_tokens"),
            finish_reason=finish_reason,
            response_id=response_id,
            error_type=None,
            error=None,
        )
    except (TimeoutError, socket.timeout) as exc:
        status = "timeout"
        error_type = type(exc).__name__
        error = str(exc)
    except Exception as exc:
        status = "error"
        error_type = type(exc).__name__
        error = str(exc)[:2000]
    finally:
        if connection is not None:
            connection.close()
    total = time.monotonic() - started
    return ProbeResult(
        request_id=request_id,
        concurrency=concurrency,
        wave=wave,
        slot=slot,
        status=status,
        http_status=status_code,
        started_at=started_wall,
        response_headers_s=headers_elapsed,
        first_sse_data_s=first_data_elapsed,
        stream_after_first_data_s=(
            total - first_data_elapsed if first_data_elapsed is not None else None
        ),
        total_s=total,
        chunk_count=chunks,
        completion_tokens=usage.get("completion_tokens"),
        reasoning_tokens=(usage.get("completion_tokens_details") or {}).get(
            "reasoning_tokens"
        ),
        finish_reason=finish_reason,
        response_id=response_id,
        error_type=error_type,
        error=error,
    )


def summarize_level(
    concurrency: int, rows: list[ProbeResult], wall_s: float
) -> dict[str, Any]:
    successful = [row for row in rows if row.status == "ok"]

    def floats(name: str) -> list[float]:
        return [
            float(value)
            for row in successful
            if (value := getattr(row, name)) is not None
        ]

    token_rates = [
        float(row.completion_tokens) / float(row.stream_after_first_data_s)
        for row in successful
        if row.completion_tokens is not None
        and row.stream_after_first_data_s is not None
        and row.stream_after_first_data_s > 0
    ]
    return {
        "concurrency": concurrency,
        "requests": len(rows),
        "successful": len(successful),
        "timeouts": sum(row.status == "timeout" for row in rows),
        "errors": sum(row.status == "error" for row in rows),
        "wall_s": wall_s,
        "successful_requests_per_second": (
            len(successful) / wall_s if wall_s > 0 else None
        ),
        "response_headers_s": metric_summary(floats("response_headers_s")),
        "first_sse_data_s": metric_summary(floats("first_sse_data_s")),
        "stream_after_first_data_s": metric_summary(
            floats("stream_after_first_data_s")
        ),
        "total_s": metric_summary(floats("total_s")),
        "completion_tokens_per_stream_second": metric_summary(token_rates),
    }


def recommend_concurrency(levels: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = sorted(levels, key=lambda row: int(row["concurrency"]))
    baseline = ordered[0]
    baseline_first_p90 = baseline["first_sse_data_s"]["p90"]
    baseline_rate = baseline["completion_tokens_per_stream_second"]["median"]
    first_data_limit = (
        max(1.0, 2.0 * float(baseline_first_p90))
        if baseline_first_p90 is not None
        else None
    )
    rate_floor = 0.90 * float(baseline_rate) if baseline_rate is not None else None
    accepted: list[int] = []
    evaluations: list[dict[str, Any]] = []
    for level in ordered:
        reasons: list[str] = []
        if level["successful"] != level["requests"]:
            reasons.append("nonzero_request_failures")
        first_p90 = level["first_sse_data_s"]["p90"]
        if (
            first_data_limit is not None
            and first_p90 is not None
            and float(first_p90) > first_data_limit
        ):
            reasons.append("first_sse_data_p90_regression")
        rate = level["completion_tokens_per_stream_second"]["median"]
        if rate_floor is not None and rate is not None and float(rate) < rate_floor:
            reasons.append("token_rate_below_90pct_baseline")
        concurrency = int(level["concurrency"])
        if not reasons:
            accepted.append(concurrency)
        evaluations.append(
            {
                "concurrency": concurrency,
                "accepted": not reasons,
                "reasons": reasons,
            }
        )
    return {
        "policy": "largest_level_with_zero_failures_stable_first_data_and_90pct_token_rate",
        "baseline_concurrency": int(baseline["concurrency"]),
        "first_sse_data_p90_limit_s": first_data_limit,
        "completion_token_rate_floor": rate_floor,
        "recommended_max_concurrency": max(accepted) if accepted else None,
        "evaluations": evaluations,
        "sample_strength": (
            "formal" if min(level["requests"] for level in ordered) >= 30 else "pilot"
        ),
    }


def calibrate(args: argparse.Namespace) -> dict[str, Any]:
    key = load_key(args.api_key_file, args.api_key_env)
    prompt = (
        Path(args.prompt_file).read_text(encoding="utf-8")
        if args.prompt_file
        else DEFAULT_PROMPT
    )
    raw: list[ProbeResult] = []
    summaries: list[dict[str, Any]] = []
    for concurrency in args.concurrency:
        if args.requests_per_level % concurrency:
            raise SystemExit(
                "--requests-per-level must be divisible by every concurrency level"
            )
        level_started = time.monotonic()
        level_rows: list[ProbeResult] = []
        waves = args.requests_per_level // concurrency
        for wave in range(waves):
            barrier = threading.Barrier(concurrency + 1)
            with ThreadPoolExecutor(max_workers=concurrency) as pool:
                futures = [
                    pool.submit(
                        run_probe,
                        base_url=args.base_url,
                        api_key=key,
                        model=args.model,
                        prompt=prompt,
                        max_tokens=args.max_tokens,
                        temperature=args.temperature,
                        concurrency=concurrency,
                        wave=wave,
                        slot=slot,
                        barrier=barrier,
                        connect_timeout_s=args.connect_timeout_s,
                        idle_timeout_s=args.idle_timeout_s,
                        total_timeout_s=args.total_timeout_s,
                    )
                    for slot in range(concurrency)
                ]
                barrier.wait()
                level_rows.extend(future.result() for future in futures)
        level_wall = time.monotonic() - level_started
        raw.extend(level_rows)
        summaries.append(summarize_level(concurrency, level_rows, level_wall))
    return {
        "schema_version": SCHEMA_VERSION,
        "started_at": args.started_at,
        "finished_at": now(),
        "provider": {
            "base_url": args.base_url,
            "model": args.model,
        },
        "request": {
            "prompt_sha256": __import__("hashlib").sha256(
                prompt.encode("utf-8")
            ).hexdigest(),
            "prompt_chars": len(prompt),
            "max_tokens": args.max_tokens,
            "temperature": args.temperature,
            "stream": True,
            "connect_timeout_s": args.connect_timeout_s,
            "idle_timeout_s": args.idle_timeout_s,
            "total_timeout_s": args.total_timeout_s,
            "requests_per_level": args.requests_per_level,
        },
        "levels": summaries,
        "recommendation": recommend_concurrency(summaries),
        "requests": [asdict(row) for row in raw],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--api-key-env", default="VAEVAS_API_KEY")
    parser.add_argument("--api-key-file")
    parser.add_argument("--prompt-file")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--concurrency", type=int, nargs="+", default=[1, 5, 10])
    parser.add_argument("--requests-per-level", type=int, default=10)
    parser.add_argument("--max-tokens", type=int, default=128)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--connect-timeout-s", type=float, default=120.0)
    parser.add_argument("--idle-timeout-s", type=float, default=120.0)
    parser.add_argument("--total-timeout-s", type=float, default=900.0)
    args = parser.parse_args()
    if not args.concurrency or any(level < 1 for level in args.concurrency):
        raise SystemExit("concurrency levels must be positive")
    if args.requests_per_level < max(args.concurrency):
        raise SystemExit("requests per level must cover the largest concurrency")
    args.started_at = now()
    result = calibrate(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    for level in result["levels"]:
        total = level["total_s"]
        print(
            f"concurrency={level['concurrency']} ok={level['successful']}/"
            f"{level['requests']} timeout={level['timeouts']} "
            f"p50={total['median']!s}s p90={total['p90']!s}s "
            f"throughput={level['successful_requests_per_second']!s} req/s"
        )
    recommendation = result["recommendation"]
    print(
        "recommended_max_concurrency="
        f"{recommendation['recommended_max_concurrency']} "
        f"sample_strength={recommendation['sample_strength']}"
    )
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
