from __future__ import annotations

import sys
from importlib import import_module
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
RUNNERS = ROOT / "runners"
if str(RUNNERS) not in sys.path:
    sys.path.insert(0, str(RUNNERS))

TASK_IDS = (350, 351, 354, 355, 356, 357, 359)
TASK_MODULES = tuple(import_module(f"checkers.v4.task_{task_id}") for task_id in TASK_IDS)


def _legacy_representative_clear_rows(
    rows: list[dict[str, float]],
    *,
    has_enable: bool,
    settle_s: float = 0.6e-9,
    minimum_spacing_s: float = 1e-9,
) -> list[dict[str, float]]:
    def high(row: dict[str, float], signal: str) -> bool:
        return float(row.get(signal, 0.0)) > 0.45

    def before(time_s: float) -> dict[str, float]:
        candidate = rows[0]
        for row in rows:
            if float(row["time"]) >= time_s:
                break
            candidate = row
        return candidate

    selected: list[dict[str, float]] = []
    last_selected = -1e99
    for row in rows:
        clear = high(row, "rst") or (has_enable and not high(row, "enable"))
        time_s = float(row["time"])
        settled = before(time_s - settle_s)
        settled_clear = high(settled, "rst") or (
            has_enable and not high(settled, "enable")
        )
        if clear and settled_clear and time_s - last_selected >= minimum_spacing_s:
            selected.append(row)
            last_selected = time_s
    return selected


def _edge_case_rows() -> list[dict[str, float]]:
    return [
        {"time": 0.0, "rst": 0.9, "enable": 0.9, "marker": 0.0},
        {"time": 0.0, "rst": 0.0, "enable": 0.9, "marker": 1.0},
        {"time": 0.4e-9, "rst": 0.0, "enable": 0.0, "marker": 2.0},
        {"time": 1.0e-9, "rst": 0.9, "enable": 0.9, "marker": 3.0},
        {"time": 1.0e-9, "rst": 0.0, "enable": 0.0, "marker": 4.0},
        {"time": 1.6e-9, "rst": 0.9, "enable": 0.9, "marker": 5.0},
        {"time": 2.6e-9, "rst": 0.9, "enable": 0.9, "marker": 6.0},
    ]


@pytest.mark.parametrize("module", TASK_MODULES, ids=lambda module: module.__name__)
@pytest.mark.parametrize("has_enable", (False, True))
def test_representative_clear_rows_preserve_legacy_selection(module, has_enable: bool) -> None:
    rows = _edge_case_rows()

    expected = _legacy_representative_clear_rows(rows, has_enable=has_enable)
    observed = module._representative_clear_rows(rows, has_enable=has_enable)

    assert [row["marker"] for row in observed] == [row["marker"] for row in expected]


@pytest.mark.parametrize("module", TASK_MODULES, ids=lambda module: module.__name__)
def test_representative_clear_rows_use_strictly_earlier_settled_sample(module) -> None:
    current_time = 1e-9
    settled_boundary = current_time - 0.6e-9
    rows = [
        {"time": 0.0, "rst": 0.9, "marker": 0.0},
        {"time": settled_boundary, "rst": 0.0, "marker": 1.0},
        {"time": current_time, "rst": 0.9, "marker": 2.0},
    ]

    observed = module._representative_clear_rows(rows, has_enable=False)

    assert [row["marker"] for row in observed] == [0.0, 2.0]


@pytest.mark.parametrize("module", TASK_MODULES, ids=lambda module: module.__name__)
def test_representative_clear_rows_preserve_threshold_and_empty_trace_behavior(module) -> None:
    rows = [
        {"time": 0.0, "rst": 0.45, "enable": 0.45, "marker": 0.0},
        {"time": 0.6e-9, "rst": 0.45, "enable": 0.45, "marker": 1.0},
        {"time": 1.6e-9, "rst": 0.45, "enable": 0.45, "marker": 2.0},
    ]

    assert module._representative_clear_rows([], has_enable=True) == []
    assert module._representative_clear_rows(rows, has_enable=False) == []
    observed = module._representative_clear_rows(rows, has_enable=True)
    assert [row["marker"] for row in observed] == [0.0, 2.0]


@pytest.mark.parametrize("module", TASK_MODULES, ids=lambda module: module.__name__)
def test_representative_clear_rows_scale_linearly(module) -> None:
    accesses = 0

    class CountingRow(dict[str, float]):
        def __getitem__(self, key: str) -> float:
            nonlocal accesses
            if key == "time":
                accesses += 1
            return super().__getitem__(key)

        def get(self, key: str, default: float | None = None) -> float | None:
            nonlocal accesses
            if key == "time":
                accesses += 1
            return super().get(key, default)

    rows = [
        CountingRow(time=index * 5e-12, rst=0.9, enable=0.9)
        for index in range(512)
    ]

    module._representative_clear_rows(rows, has_enable=True)

    assert accesses < 8 * len(rows)
