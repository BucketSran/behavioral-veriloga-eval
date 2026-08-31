from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "benchmark-vabench-release-v4"
RUNNER_SMOKE_WORKFLOW = ROOT / ".github" / "workflows" / "runner-smoke.yml"
ACTIVE_ENTRYPOINTS = (
    PACKAGE
    / "operations"
    / "tri_form_derivation_prep"
    / "export_tri_form_runtime.py",
    PACKAGE / "runners" / "run_benchmarkv4_campaign.py",
    PACKAGE / "operations" / "calibration_pilot" / "build_campaign.py",
    PACKAGE / "operations" / "calibration_pilot" / "run_campaign.py",
    PACKAGE
    / "operations"
    / "tri_form_derivation_prep"
    / "run_v4_reference_evas_smoke.py",
    PACKAGE
    / "operations"
    / "tri_form_derivation_prep"
    / "run_v4_profile_parity_smoke.py",
)
HISTORICAL_GUIDES = (
    "BENCHMARKV4_REPO_SLIMMING_PLAN.md",
    "EXPERIMENT_ASSET_POLICY.md",
    "LABCTL_SPECTRE_WORKFLOW.md",
    "TASK_AUTHORING_CHECKLIST.md",
    "V3_EVALUATOR_CONTRACT.md",
    "V3_SOURCE_IMPORT_AUDIT.md",
    "VABENCH_RELEASE_TAXONOMY.md",
    "VABENCH_TOPLEVEL_POSITIONING.md",
    "VAEVAS_VALIDATION_PIPELINE.md",
)


def default_release_literals(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(
            isinstance(target, ast.Name) and target.id == "DEFAULT_RELEASE"
            for target in node.targets
        ):
            continue
        literals = [
            child.value
            for child in ast.walk(node.value)
            if isinstance(child, ast.Constant) and isinstance(child.value, str)
        ]
        if literals:
            return set(literals)
    raise AssertionError(f"DEFAULT_RELEASE not found in {path}")


@pytest.mark.parametrize("entrypoint", ACTIVE_ENTRYPOINTS, ids=lambda path: path.name)
def test_active_benchmark_entrypoint_defaults_to_r53(entrypoint: Path) -> None:
    literals = default_release_literals(entrypoint)
    assert "benchmarkv4-r53" in literals
    assert "benchmarkv4" not in literals


def test_operator_docs_name_r53_as_the_active_default() -> None:
    documents = (
        ROOT / "docs" / "REPO_LAYOUT_POLICY.md",
        PACKAGE / "runners" / "README.md",
        PACKAGE / "operations" / "calibration_pilot" / "README.md",
        PACKAGE / "operations" / "tri_form_derivation_prep" / "README.md",
    )
    for document in documents:
        text = document.read_text(encoding="utf-8")
        assert "benchmarkv4-r53" in text, document


def test_current_docs_point_to_active_plan_not_completed_integration_gaps():
    index = (ROOT / "docs/README.md").read_text()
    notebook = (ROOT / "docs/alphaapollo-migration/README.md").read_text()
    assert "AlphaApollo Reasoning/Evolution are not complete" not in index
    assert "(../plans/current-plan.md)" in index
    assert "(../../plans/current-plan.md)" in notebook
    audit = "04_夜间工程闭环审计_2026-08-31.md"
    assert audit in index and audit in notebook
    assert (ROOT / "docs/alphaapollo-migration" / audit).is_file()
    guide = (PACKAGE / "operations/calibration_pilot/README.md").read_text()
    assert "no RAG CLI/Evolution integration" not in guide
    assert "AA-VAE-065" in guide


@pytest.mark.parametrize("relative_path", ("README.md", "docs/REPO_LAYOUT_POLICY.md"))
def test_primary_documented_release_is_r53(relative_path: str) -> None:
    text = (ROOT / relative_path).read_text(encoding="utf-8")
    first_path_block = re.search(r"```text\n([^`]+)```", text)
    assert first_path_block is not None
    assert first_path_block.group(1).strip() == (
        "benchmark-vabench-release-v4/release/benchmarkv4-r53/"
    )
    assert "0.8.7" in text


@pytest.mark.parametrize("name", HISTORICAL_GUIDES)
def test_historical_guides_redirect_current_work(name: str) -> None:
    text = (ROOT / "docs" / name).read_text(encoding="utf-8")
    banner = text.split("\n## ", 1)[0]
    assert "**Historical document" in banner
    assert "not a current operating guide" in banner
    assert "[current documentation](README.md)" in banner


@pytest.mark.parametrize(
    "relative_path",
    (
        "README.md",
        "docs/README.md",
        "plans/current-plan.md",
        "benchmark-vabench-release-v4/runners/README.md",
        "benchmark-vabench-release-v4/operations/calibration_pilot/README.md",
        "docs/alphaapollo-migration/README.md",
        "docs/alphaapollo-migration/00_迁移主线.md",
        "docs/alphaapollo-migration/01_功能迁移台账.md",
        "docs/alphaapollo-migration/03_全局后续路线_2026-08-31.md",
        "docs/alphaapollo-migration/features/AA-VAE-059-synthetic-training-export.md",
        "docs/alphaapollo-migration/features/AA-VAE-062-synthetic-native-training-adapter.md",
    ),
)
def test_current_navigation_links_resolve(relative_path: str) -> None:
    document = ROOT / relative_path
    text = document.read_text(encoding="utf-8")
    links = re.findall(r"\[[^\]]+\]\(([^\s)]+)\)", text)
    assert links, document
    for link in links:
        if "://" in link or link.startswith("#"):
            continue
        target = document.parent / link.split("#", 1)[0]
        assert target.exists(), (document, link)


def test_active_metamorphic_evidence_defaults_to_r53() -> None:
    path = PACKAGE / "scripts" / "run_v4_stimulus_metamorphic.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    defaults = {
        target.id: node.value.value
        for node in tree.body
        if isinstance(node, ast.Assign)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
        for target in node.targets
        if isinstance(target, ast.Name)
    }
    assert defaults["DEFAULT_RELEASE_REVISION"] == "r53"


def test_runner_ci_tracks_and_protects_the_active_r53_release() -> None:
    workflow = RUNNER_SMOKE_WORKFLOW.read_text(encoding="utf-8")

    assert "tests/test_v4_r53_active_entrypoints.py" in workflow
    assert "tests/test_v4_r52_active_entrypoints.py" not in workflow
    assert "benchmark-vabench-release-v4/release/benchmarkv4-r53" in workflow
