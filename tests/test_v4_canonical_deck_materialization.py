from __future__ import annotations

import hashlib
import importlib.util
import json
from functools import cache
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = (
    ROOT
    / "benchmark-vabench-release-v4"
    / "provenance"
    / "dut-base-v3-exact-five-hash-bound-v2"
)
RENDERER = (
    ROOT / "benchmark-vabench-release-v4" / "scripts" / "render_v4_harness.py"
)


@cache
def load_renderer():
    spec = importlib.util.spec_from_file_location("render_v4_harness", RENDERER)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def semantic_deck(text: str) -> str:
    lines = []
    save_signals = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("simulatorOptions options "):
            continue
        if stripped.startswith("save "):
            save_signals.extend(stripped.split()[1:])
            continue
        lines.append(stripped)
    if save_signals:
        lines.append(f"save {' '.join(save_signals)}")
    return "\n".join(lines)


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assert_materialized_decks_match_canonical_spec(
    family: int, expected_stimulus: str,
) -> None:
    renderer = load_renderer()
    task = next(SOURCE_ROOT.glob(f"{family:03d}-*"))
    spec = json.loads(
        (task / "evaluator" / "harness_spec.json").read_text(encoding="utf-8")
    )
    spec_sha = file_sha256(task / "evaluator" / "harness_spec.json")

    renderer.validate_profile_semantic_parity(spec)
    feedback = renderer.render_scs(
        spec, renderer.build_profile(spec, "feedback", spec_sha)
    )
    score = renderer.render_scs(
        spec, renderer.build_profile(spec, "score", spec_sha)
    )
    materialized_feedback = (
        task / "public" / "task" / "feedback_tb.scs"
    ).read_text(encoding="utf-8")
    materialized_score = (task / "evaluator" / "score_tb.scs").read_text(
        encoding="utf-8"
    )
    materialized_feedback_profile = json.loads(
        (task / "evaluator" / "profiles" / "feedback.json").read_text(
            encoding="utf-8"
        )
    )
    materialized_score_profile = json.loads(
        (task / "evaluator" / "profiles" / "score.json").read_text(
            encoding="utf-8"
        )
    )
    task_record_path = task / "evaluator" / "task_record.json"
    task_record = json.loads(task_record_path.read_text(encoding="utf-8"))
    registry = json.loads(
        (SOURCE_ROOT / "score_denominator_registry" / f"{family:03d}.json").read_text(
            encoding="utf-8"
        )
    )["task"]

    assert expected_stimulus in feedback, task.name
    assert materialized_feedback_profile == renderer.build_profile(
        spec, "feedback", spec_sha
    ), task.name
    assert materialized_score_profile == renderer.build_profile(
        spec, "score", spec_sha
    ), task.name
    assert semantic_deck(materialized_feedback) == semantic_deck(feedback), task.name
    assert semantic_deck(materialized_score) == semantic_deck(score), task.name
    for relative, expected_sha in task_record["evaluator_hashes"].items():
        path = task / "evaluator" / relative
        if path.is_file():
            assert file_sha256(path) == expected_sha, task.name
    for relative, expected_sha in task_record["public_hashes"].items():
        path = task / "public" / "task" / relative
        assert file_sha256(path) == expected_sha, task.name
    assert registry["hashes"]["task_record_sha256"] == file_sha256(
        task_record_path
    ), task.name
    assert registry["hashes"]["score_deck_sha256"] == file_sha256(
        task / "evaluator" / "score_tb.scs"
    ), task.name
    assert registry["hashes"]["mutation_catalog_sha256"] == file_sha256(
        task / "evaluator" / "mutation_catalog.json"
    ), task.name


def test_family206_materialized_decks_match_equal_input_canonical_spec() -> None:
    assert_materialized_decks_match_canonical_spec(
        206, "2.05n 0.45 3.2n 0.45",
    )


def test_family214_materialized_decks_match_equal_input_canonical_spec() -> None:
    assert_materialized_decks_match_canonical_spec(
        214, "2.05n 0.9 3.2n 0.9",
    )


def test_family353_materialized_decks_match_midrun_reset_canonical_spec() -> None:
    assert_materialized_decks_match_canonical_spec(
        353, "48n 0 48.1n 0.9 52n 0.9 52.1n 0",
    )


def test_family184_materialized_decks_match_foreground_direction_spec() -> None:
    assert_materialized_decks_match_canonical_spec(
        184, "4.9n 0 5.8n 0 5.9n 1 6.8n 1 6.9n 0",
    )


def test_family392_materialized_decks_match_varying_input_spec() -> None:
    assert_materialized_decks_match_canonical_spec(
        392, "28n 0 28.2n 0.9 38n 0.9 38.2n 0",
    )


def test_family393_materialized_decks_match_midframe_alignment_spec() -> None:
    assert_materialized_decks_match_canonical_spec(
        393, "35n 0 35.2n 0.9 36n 0.9 36.2n 0",
    )


def test_all_materialized_decks_match_canonical_specs() -> None:
    tasks = sorted(SOURCE_ROOT.glob("[0-9][0-9][0-9]-*"))
    assert len(tasks) == 400
    for task in tasks:
        assert_materialized_decks_match_canonical_spec(int(task.name[:3]), "")
