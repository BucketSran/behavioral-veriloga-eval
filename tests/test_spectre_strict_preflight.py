from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runners"))

from score import _parameter_default_range_hits, _parameter_open_upper_range_hits  # noqa: E402


def test_parameter_default_range_rejects_exclusive_lower_bound(tmp_path: Path) -> None:
    va = tmp_path / "dut.va"
    va.write_text(
        "module dut(out);\n"
        "  output out; electrical out;\n"
        "  parameter real vlo = 0.0 from (0:inf);\n"
        "endmodule\n",
        encoding="utf-8",
    )

    hits = _parameter_default_range_hits(va)

    assert hits
    assert "vlo" in hits[0]


def test_parameter_default_range_allows_inclusive_bound(tmp_path: Path) -> None:
    va = tmp_path / "dut.va"
    va.write_text(
        "module dut(out);\n"
        "  output out; electrical out;\n"
        "  parameter real vlo = 0.0 from [0:inf);\n"
        "endmodule\n",
        encoding="utf-8",
    )

    assert _parameter_default_range_hits(va) == []


def test_parameter_open_upper_range_rejects_parenthesized_empty_upper(tmp_path: Path) -> None:
    va = tmp_path / "dut.va"
    va.write_text(
        "module dut(out);\n"
        "  output out; electrical out;\n"
        "  parameter real tr = 1n from (0:);\n"
        "endmodule\n",
        encoding="utf-8",
    )

    hits = _parameter_open_upper_range_hits(va)

    assert hits
    assert "tr" in hits[0]


def test_parameter_open_upper_range_rejects_mixed_bracket_empty_upper(tmp_path: Path) -> None:
    va = tmp_path / "dut.va"
    va.write_text(
        "module dut(out);\n"
        "  output out; electrical out;\n"
        "  parameter real td = 0n from [0:);\n"
        "endmodule\n",
        encoding="utf-8",
    )

    hits = _parameter_open_upper_range_hits(va)

    assert hits
    assert "td" in hits[0]


def test_parameter_open_upper_range_allows_explicit_inf_upper(tmp_path: Path) -> None:
    va = tmp_path / "dut.va"
    va.write_text(
        "module dut(out);\n"
        "  output out; electrical out;\n"
        "  parameter real tr = 1n from (0:inf);\n"
        "endmodule\n",
        encoding="utf-8",
    )

    assert _parameter_open_upper_range_hits(va) == []
