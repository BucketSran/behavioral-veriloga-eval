#!/usr/bin/env python3
from pathlib import Path
import json
import sys

TASK_DIR = Path(__file__).resolve().parent
ROOT = TASK_DIR.parents[2]
sys.path.insert(0, str(ROOT / "runners"))
from simulate_evas import evaluate_behavior  # noqa: E402


def check_csv(csv_path):
    meta = json.loads((TASK_DIR / "meta.json").read_text(encoding="utf-8"))
    source_task_id = meta.get("source_task_id", 'serializer_8b_smoke')
    score, notes = evaluate_behavior(source_task_id, Path(csv_path))
    return {"pass": score >= 1.0, "score": score, "notes": notes}


if __name__ == "__main__":
    print(json.dumps(check_csv(sys.argv[1]), indent=2))
