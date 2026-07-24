from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


MODULE_DIR = (
    Path(__file__).resolve().parents[2]
    / "operations"
    / "tri_form_derivation_prep"
)
sys.path.insert(0, str(MODULE_DIR))
SPEC = importlib.util.spec_from_file_location(
    "refresh_rust_evas2_certifications",
    MODULE_DIR / "refresh_rust_evas2_certifications.py",
)
assert SPEC and SPEC.loader
refresh = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(refresh)


def family_row(family: str) -> dict:
    return {
        "canonical_dut_id": family,
        "release_dir": f"{family}-synthetic",
        "active_mutations": [
            {
                "mutation_id": f"mutation_{index:02d}",
                "certification_path": (
                    f"evaluator/mutation_bundles/mutation_{index:02d}/"
                    "certification.json"
                ),
            }
            for index in range(1, 6)
        ],
    }


def family_cases(family: str) -> dict[str, dict]:
    cases = {
        "gold": {
            "family_id": family,
            "case_id": "gold",
            "mutation_id": None,
            "checker_id": f"v4-{family}",
            "status": "pass",
            "checker_pass": True,
            "timing_invariant": True,
            "diagnostics_complete": True,
            "insufficient_excitation_rejected": True,
            "trace_row_count": 10,
        }
    }
    for index in range(1, 6):
        mutation_id = f"mutation_{index:02d}"
        cases[mutation_id] = {
            "family_id": family,
            "case_id": mutation_id,
            "mutation_id": mutation_id,
            "checker_id": f"v4-{family}",
            "status": "pass",
            "checker_pass": False,
            "timing_invariant": True,
            "diagnostics_complete": True,
            "insufficient_excitation_rejected": None,
            "trace_row_count": 10,
        }
    return cases


@pytest.mark.parametrize("release_revision", ["r45", "r47"])
def test_evidence_only_refresh_does_not_rewrite_source(
    tmp_path: Path,
    monkeypatch,
    release_revision: str,
) -> None:
    families = [f"{value:03d}" for value in range(1, 401)]
    report = tmp_path / "full400.json"
    report.write_text("{}\n", encoding="utf-8")
    output = tmp_path / "RUST_EVAS2_CERTIFICATION.json"
    monkeypatch.setattr(
        refresh,
        "load_family_rows",
        lambda source: [family_row(family) for family in families],
    )
    monkeypatch.setattr(
        refresh,
        "source_certification_definition_sha256",
        lambda source, rows: "a" * 64,
    )
    monkeypatch.setattr(
        refresh,
        "report_cases",
        lambda paths: (
            {family: family_cases(family) for family in families},
            {
                "evas_engine": "evas2",
                "evas_version": "0.8.3",
                "evas_backend": "evas-rust",
            },
        ),
    )

    def unexpected_source_write(*args, **kwargs):
        raise AssertionError("evidence-only refresh attempted to rewrite source")

    monkeypatch.setattr(refresh, "refresh_task_record", unexpected_source_write)
    monkeypatch.setattr(refresh, "update_registry_row", unexpected_source_write)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "refresh_rust_evas2_certifications.py",
            "--source",
            str(tmp_path / "source"),
            "--report",
            str(report),
            "--output",
            str(output),
            "--release-revision",
            release_revision,
        ],
    )

    assert refresh.main() == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["schema_version"] == (
        f"v4-{release_revision}-rust-evas2-certification-report-v2"
    )
    assert payload["release_candidate"] == release_revision
    assert payload["source_certification_definition_sha256"] == "a" * 64
    assert payload["source_certifications_updated"] is False
    assert payload["runtime"]["evas_version"] == "0.8.3"
    assert payload["summary"] == {
        "family_count": 400,
        "gold_pass_count": 400,
        "negative_case_count": 2000,
        "mutation_kill_count": 2000,
        "trace_axis_invariant_count": 2400,
        "insufficient_excitation_rejection_count": 400,
        "insufficient_excitation_not_applicable_count": 0,
        "diagnostic_present_count": 2400,
    }
    assert len(payload["cases"]) == 2400


def test_selective_evidence_refresh_accepts_exact_requested_families(
    tmp_path: Path,
    monkeypatch,
) -> None:
    all_families = [f"{value:03d}" for value in range(1, 401)]
    selected = ["184", "206", "214", "353", "392", "393"]
    report = tmp_path / "selected.json"
    report.write_text("{}\n", encoding="utf-8")
    output = tmp_path / "SELECTIVE_CERTIFICATION.json"
    monkeypatch.setattr(
        refresh,
        "load_family_rows",
        lambda source: [family_row(family) for family in all_families],
    )
    monkeypatch.setattr(
        refresh,
        "source_certification_definition_sha256",
        lambda source, rows: "b" * 64,
    )
    monkeypatch.setattr(
        refresh,
        "report_cases",
        lambda paths: (
            {family: family_cases(family) for family in selected},
            {
                "evas_engine": "evas2",
                "evas_version": "0.8.3",
                "evas_backend": "evas-rust",
            },
        ),
    )
    argv = [
        "refresh_rust_evas2_certifications.py",
        "--source",
        str(tmp_path / "source"),
        "--report",
        str(report),
        "--output",
        str(output),
        "--release-revision",
        "r51",
    ]
    for family in selected:
        argv.extend(["--family", family])
    monkeypatch.setattr(sys, "argv", argv)

    assert refresh.main() == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["selected_family_ids"] == selected
    assert payload["summary"] == {
        "family_count": 6,
        "gold_pass_count": 6,
        "negative_case_count": 30,
        "mutation_kill_count": 30,
        "trace_axis_invariant_count": 36,
        "insufficient_excitation_rejection_count": 6,
        "insufficient_excitation_not_applicable_count": 0,
        "diagnostic_present_count": 36,
    }
    assert len(payload["cases"]) == 36


def test_selective_source_refresh_rewrites_only_requested_families(
    tmp_path: Path,
    monkeypatch,
) -> None:
    all_families = [f"{value:03d}" for value in range(1, 401)]
    selected = ["184", "206", "214", "353", "392", "393"]
    report = tmp_path / "selected.json"
    report.write_text("{}\n", encoding="utf-8")
    package = tmp_path / "benchmark-vabench-release-v4"
    fake_module = (
        package
        / "operations"
        / "tri_form_derivation_prep"
        / "refresh_rust_evas2_certifications.py"
    )
    output = (
        package
        / "evidence"
        / "canonical-source"
        / "SELECTIVE_CERTIFICATION.json"
    )
    monkeypatch.setattr(refresh, "__file__", str(fake_module))
    monkeypatch.setattr(
        refresh,
        "load_family_rows",
        lambda source: [family_row(family) for family in all_families],
    )
    monkeypatch.setattr(
        refresh,
        "source_certification_definition_sha256",
        lambda source, rows: "c" * 64,
    )
    monkeypatch.setattr(
        refresh,
        "report_cases",
        lambda paths: (
            {family: family_cases(family) for family in selected},
            {
                "evas_engine": "evas2",
                "evas_version": "0.8.3",
                "evas_backend": "evas-rust",
            },
        ),
    )
    calls: dict[str, list[str]] = {
        "artifact_hashes": [],
        "mutation_summary": [],
        "task_record": [],
        "registry": [],
    }
    monkeypatch.setattr(
        refresh,
        "refresh_mutation_artifact_hashes",
        lambda task, mutation_ids: calls["artifact_hashes"].append(task.name[:3]),
    )
    monkeypatch.setattr(
        refresh,
        "refresh_mutation_summary",
        lambda task, mutation_ids: calls["mutation_summary"].append(task.name[:3]),
    )
    monkeypatch.setattr(
        refresh,
        "gold_certificate",
        lambda family, *args, **kwargs: {"family_id": family},
    )
    monkeypatch.setattr(
        refresh,
        "negative_certificate",
        lambda family, mutation_id, *args, **kwargs: {
            "family_id": family,
            "mutation_id": mutation_id,
        },
    )
    monkeypatch.setattr(
        refresh,
        "refresh_task_record",
        lambda task: calls["task_record"].append(task.name[:3]),
    )
    monkeypatch.setattr(
        refresh,
        "update_registry_row",
        lambda source, family, row, task: calls["registry"].append(family),
    )
    argv = [
        "refresh_rust_evas2_certifications.py",
        "--source",
        str(tmp_path / "source"),
        "--report",
        str(report),
        "--output",
        str(output),
        "--release-revision",
        "r51",
        "--update-source-certifications",
    ]
    for family in selected:
        argv.extend(["--family", family])
    monkeypatch.setattr(sys, "argv", argv)

    assert refresh.main() == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["evidence_scope"] == "canonical_source"
    assert calls == {
        "artifact_hashes": selected,
        "mutation_summary": selected,
        "task_record": selected,
        "registry": selected,
    }


def test_source_refresh_rejects_sealed_revision_evidence_namespace(
    tmp_path: Path,
    monkeypatch,
) -> None:
    family = "184"
    report = tmp_path / "selected.json"
    report.write_text("{}\n", encoding="utf-8")
    package = tmp_path / "benchmark-vabench-release-v4"
    fake_module = (
        package
        / "operations"
        / "tri_form_derivation_prep"
        / "refresh_rust_evas2_certifications.py"
    )
    output = package / "evidence" / "r51" / "SELECTIVE_CERTIFICATION.json"
    monkeypatch.setattr(refresh, "__file__", str(fake_module))
    monkeypatch.setattr(
        refresh,
        "load_family_rows",
        lambda source: [
            family_row(f"{value:03d}") for value in range(1, 401)
        ],
    )
    monkeypatch.setattr(
        refresh,
        "source_certification_definition_sha256",
        lambda source, rows: "d" * 64,
    )
    monkeypatch.setattr(
        refresh,
        "report_cases",
        lambda paths: (
            {family: family_cases(family)},
            {
                "evas_engine": "evas2",
                "evas_version": "0.8.3",
                "evas_backend": "evas-rust",
            },
        ),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "refresh_rust_evas2_certifications.py",
            "--source",
            str(tmp_path / "source"),
            "--report",
            str(report),
            "--output",
            str(output),
            "--release-revision",
            "r51",
            "--update-source-certifications",
            "--family",
            family,
        ],
    )

    with pytest.raises(SystemExit, match="sealed revision namespace"):
        refresh.main()
    assert not output.exists()
