#!/usr/bin/env python3
"""Shared checkers for benchmark-balanced tasks.

This file deliberately reuses the already Spectre-validated benchmark-v2
checker kernels so the balanced split does not fork scoring semantics.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

COMMON = Path(__file__).resolve().parents[1] / "benchmark-v2" / "common_checker.py"
spec = importlib.util.spec_from_file_location("benchmark_v2_common_checker", COMMON)
_module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(_module)

check_csv = _module.check_csv
check_with_meta = _module.check_with_meta
