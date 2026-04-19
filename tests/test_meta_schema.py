from __future__ import annotations

import json
from pathlib import Path

import jsonschema


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "task.schema.json"
TASKS_DIR = ROOT / "tasks"


def test_all_meta_json_files_follow_task_schema() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    failures: list[str] = []

    for meta_path in sorted(TASKS_DIR.rglob("meta.json")):
        payload = json.loads(meta_path.read_text(encoding="utf-8"))
        try:
            jsonschema.validate(payload, schema)
        except jsonschema.ValidationError as exc:
            failures.append(f"{meta_path.relative_to(ROOT)}: {exc.message}")

    assert not failures, "meta.json schema violations:\n" + "\n".join(failures)
