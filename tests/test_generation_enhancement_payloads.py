from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runners"))

from generate import detect_provider  # noqa: E402


def test_detect_provider_supports_mimo_models() -> None:
    assert detect_provider("mimo-v2.5-pro") == "mimo"
    assert detect_provider("xiaomi/mimo-v2.5-pro") == "mimo"

import generate  # noqa: E402


def _balanced_task_dirs() -> list[Path]:
    return sorted((ROOT / "benchmark-balanced" / "tasks").glob("*/meta.json"))


def test_gi_enhancement_payloads_cover_balanced_143() -> None:
    task_meta_paths = _balanced_task_dirs()
    assert len(task_meta_paths) == 143

    for mode in ("mechanism", "functional-ir"):
        missing: list[str] = []
        for meta_path in task_meta_paths:
            task_dir = meta_path.parent
            payload = generate.build_enhancement_payload(task_dir, mode)
            if not payload.get("text") or payload.get("status") == "not_requested":
                missing.append(task_dir.name)
        assert not missing, f"{mode} payload missing for: {missing[:10]}"


def test_enhancement_payloads_do_not_include_teacher_artifact_paths() -> None:
    banned = ("source_root", "generated_root", "result_json", "checker.py")

    for meta_path in _balanced_task_dirs()[:20]:
        task_dir = meta_path.parent
        for mode in ("mechanism", "functional-ir"):
            text = generate.build_enhancement_payload(task_dir, mode)["text"]
            lowered = text.lower()
            assert not any(token in lowered for token in banned)


def test_mechanism_retrieval_ignores_task_identity(tmp_path: Path) -> None:
    prompt = """Write a voltage-domain threshold detector.

Ports:
- `vin`: input voltage
- `out`: output voltage

Required public waveform columns:
- `vin`
- `out`

The output should assert when `vin` crosses a public threshold and should be
held through a transition-smoothed voltage target.
"""

    def make_task(dirname: str, task_id: str, task_name: str) -> Path:
        task_dir = tmp_path / dirname
        task_dir.mkdir()
        (task_dir / "prompt.md").write_text(prompt, encoding="utf-8")
        (task_dir / "meta.json").write_text(
            json.dumps(
                {
                    "task_id": task_id,
                    "task_name": task_name,
                    "category": "threshold-detector",
                    "family": "spec-to-va",
                }
            ),
            encoding="utf-8",
        )
        return task_dir

    poisoned_a = make_task(
        "dwa_ptr_gen_smoke",
        "dwa_ptr_gen_smoke",
        "DWA Pointer Rotation Generator Smoke Test",
    )
    poisoned_b = make_task(
        "pll_feedback_cadence_smoke",
        "pll_feedback_cadence_smoke",
        "PLL Feedback Divider Lock Cadence Smoke Test",
    )

    payload_a = generate.build_enhancement_payload(poisoned_a, "mechanism")
    payload_b = generate.build_enhancement_payload(poisoned_b, "mechanism")

    assert payload_a["ids"] == payload_b["ids"]
    assert "dwa_pointer_window" not in payload_a["ids"]
    assert "pll_feedback_cadence" not in payload_a["ids"]
