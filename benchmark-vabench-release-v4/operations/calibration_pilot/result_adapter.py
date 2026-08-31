#!/usr/bin/env python3
"""Read verified native results for external reporting, never run an evaluation."""

from __future__ import annotations

import hashlib
import json
import argparse
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
import time
import uuid

from result_ledger import build_native_campaign_ledger
from score_campaign import read_native_campaign_rows

INSPECT_VERSION = "0.3.261"


def read_campaign_ledger(campaign_path: Path, run_root: Path, *, workers: int = 1) -> dict:
    """Reuse the score reader and safe ledger; missing evidence fails closed."""
    for path in (campaign_path, run_root):
        if any(part.is_symlink() for part in (path, *path.parents)):
            raise ValueError("source paths must not use symlinks")
    source = campaign_path.read_bytes()
    campaign = json.loads(source)
    digest = hashlib.sha256(source).hexdigest()
    rows = read_native_campaign_rows(
        campaign, run_root, campaign_file_sha256=digest, workers=workers,
    )
    if campaign_path.read_bytes() != source:
        raise ValueError("campaign changed during readback")
    return build_native_campaign_ledger(campaign, rows, campaign_file_sha256=digest)


def build_inspect_log(ledger: dict):
    """Project a reader-produced safe ledger; never synthesize solver events.

    This is an import, not an Inspect evaluation run. Inspect's NaN unscored
    sentinel is confined to its Score objects; source nulls remain in metadata.
    """
    if version("inspect-ai") != INSPECT_VERSION:
        raise ValueError(f"Inspect export requires inspect-ai=={INSPECT_VERSION}")
    from inspect_ai.log import (
        EvalConfig, EvalDataset, EvalLog, EvalMetric, EvalResults, EvalSample,
        EvalScore, EvalSpec, EvalStats,
    )
    from inspect_ai.scorer import Score

    created = datetime.now(timezone.utc).isoformat()
    samples = []
    for record in ledger["records"]:
        score = (
            Score(value=record["actual_score"])
            if record["actual_score_eligible"]
            else Score.unscored(reason=record["actual_score_ineligible_reason"] or "not_eligible")
        )
        identity = record["identity"]
        samples.append(EvalSample(
            id=identity["cell_id"], epoch=1, input=identity["task_id"], target="",
            scores={"vaevas_final": score}, metadata={"vaevas": record},
        ))
    metrics = {}
    # Preserve separate conditions; a pooled headline would conflate estimands.
    for arm, summary in ledger["paired_summary"]["arms"].items():
        for name in ("planned", "observed", "score_eligible", "passed", "pass_rate"):
            value = summary[name]
            if value is not None:
                key = f"{arm}/{name}"
                metrics[key] = EvalMetric(name=key, value=value, metadata={
                    "condition": arm, "denominator_policy": "passed / score_eligible",
                    "ineligible_reasons": summary["ineligible_reasons"],
                    "scheduled": summary["planned"], "eligible": summary["score_eligible"],
                })
    eligible = ledger["denominator"]["eligible_actual_score_cells"]
    return EvalLog(
        status="success",
        eval=EvalSpec(
            eval_id=str(uuid.uuid4()), run_id=str(uuid.uuid4()), created=created,
            task="vaevas_readonly_import", task_id=ledger["ledger_sha256"],
            task_version="native-ledger-v1", model="vaevas-readonly-import",
            dataset=EvalDataset(name="vaEVAS imported native results", samples=len(samples),
                                sample_ids=[sample.id for sample in samples], shuffled=False),
            config=EvalConfig(epochs=1, log_samples=True),
            metadata={
                "adapter_schema": "vaevas-inspect-import-v1",
                "execution_performed": False, "readonly_import": True,
                "claim_scope": "result_interoperability_only",
                "timing_scope": "import_only_not_model_or_evaluation_latency",
                "transcript_scope": "not_exported",
                "model_usage_scope": "source_usage_in_ledger_not_inspect_execution",
                "vaevas_ledger": ledger,
            },
        ),
        results=EvalResults(
            total_samples=len(samples), completed_samples=len(samples),
            scores=[EvalScore(name="vaevas_final", scorer="vaevas_final",
                              scored_samples=eligible, unscored_samples=len(samples) - eligible,
                              metrics=metrics)],
        ),
        samples=samples, stats=EvalStats(started_at=created, completed_at=created),
    )


def export_inspect(
    campaign_path: Path, run_root: Path, output_dir: Path, *, workers: int = 1,
) -> dict:
    """Write a new local export directory; inputs are never modified/rejudged."""
    if any(part.is_symlink() for part in (output_dir, *output_dir.parents)):
        raise ValueError("output paths must not use symlinks")
    destination = output_dir.resolve()
    source_root = run_root.resolve()
    if (destination == source_root or source_root in destination.parents
            or destination == campaign_path.resolve()
            or destination in campaign_path.resolve().parents):
        raise ValueError("export must be outside source evidence")
    if output_dir.exists():
        raise FileExistsError(output_dir)
    started = time.perf_counter()
    ledger = read_campaign_ledger(campaign_path, run_root, workers=workers)
    read_elapsed_s = time.perf_counter() - started
    log = build_inspect_log(ledger)
    from inspect_ai.log import write_eval_log
    from native_episode import _write_once

    # Exclusive directory creation prevents both overwrite and competing exports.
    # An interrupted export remains visibly incomplete; it is never adopted.
    output_dir.mkdir(parents=True, exist_ok=False)
    _write_once(output_dir / "ledger.json", ledger)
    write_eval_log(log, output_dir / "results.eval", format="eval")
    receipt = {
        "schema_version": "vaevas-inspect-export-receipt-v1",
        "inspect_version": INSPECT_VERSION, "ledger_sha256": ledger["ledger_sha256"],
        "scheduled_cells": ledger["denominator"]["scheduled_cells"],
        "read_workers": workers, "read_elapsed_s": read_elapsed_s,
        "execution_performed": False, "claim_scope": "result_interoperability_only",
        "files": {name: hashlib.sha256((output_dir / name).read_bytes()).hexdigest()
                  for name in ("ledger.json", "results.eval")},
    }
    _write_once(output_dir / "receipt.json", receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=1, help="Parallel evidence readers, not model workers")
    args = parser.parse_args()
    print(json.dumps(export_inspect(args.campaign, args.run_root, args.output_dir, workers=args.workers),
                     sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
