#!/usr/bin/env python3
from pathlib import Path
import importlib.util
import json

TASK_DIR = Path(__file__).resolve().parent
COMMON = TASK_DIR.parents[1] / "common_checker.py"
spec = importlib.util.spec_from_file_location("benchmark_v2_common_checker", COMMON)
common = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(common)


def check_csv(csv_path):
    meta = json.loads((TASK_DIR / "meta.json").read_text(encoding="utf-8"))
    return common.check_csv(csv_path, meta["v2_checker_spec"])


if __name__ == "__main__":
    import sys
    print(json.dumps(check_csv(sys.argv[1]), indent=2))
