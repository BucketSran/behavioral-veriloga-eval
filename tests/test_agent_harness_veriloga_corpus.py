"""Published allowlist contracts; real source checks opt in without network."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest

from runners.agent_harness.tools.offline_docs import OfflineDocsCorpus, OfflineDocsError


CORPUS_DIR = (
    Path(__file__).resolve().parents[1]
    / "benchmark-vabench-release-v4/operations/calibration_pilot/corpora/veriloga-skills"
)
PIN = "7c5d3f03a162ee8131103e9551eee842424360bb"
SOURCES = {
    "modules-ports-disciplines.md": "725306a29523cb598ae2816be020591e846b02e33f79839c125c8564bab07543",
    "analog-contributions.md": "872e50c65d521b8c56c276ad23bc468a840fc534f513642a35012cbd21973bf5",
    "events-state-control.md": "d379f57902e4ddf2f40bd90d31317dc4524e11c21ec8bffb844cbb59b184f45c",
    "operators-system-tasks.md": "ba5d6ddde47e82c439cde8e7dd41fa73ef6a8de44763898ca0a316b18011d232",
}


def manifest():
    return json.loads((CORPUS_DIR / "manifest.json").read_text(encoding="utf-8"))


def test_published_allowlist_binds_pin_and_actual_authorization():
    data = manifest()
    evidence_hash = hashlib.sha256((CORPUS_DIR / "authorization.md").read_bytes()).hexdigest()
    assert len(data["documents"]) == 4
    assert {row["path"]: row["sha256"] for row in data["documents"]} == SOURCES
    for row in data["documents"]:
        assert row["license"] == "LicenseRef-User-Authorized"
        assert row["source"] == "reviewed_local_reference"
        assert row["contamination_categories"] == []
        assert row["provenance"] == {
            "origin": "https://github.com/Arcadia-1/veriloga-skills",
            "revision": PIN,
            "upstream_path": "veriloga/references/" + row["path"],
            "rights_basis": "owner-permission",
            "rights_evidence_sha256": evidence_hash,
        }


def test_published_metadata_loads_through_existing_v2_contract(tmp_path):
    # Synthetic replacement bodies test metadata compatibility, not real sources.
    data = manifest()
    for row in data["documents"]:
        body = f"Synthetic reference fixture: {row['section']}.".encode()
        (tmp_path / row["path"]).write_bytes(body)
        row["sha256"] = hashlib.sha256(body).hexdigest()
    corpus = OfflineDocsCorpus.from_manifest(tmp_path, data)
    corpus.assert_model_context_allowed(external_provider=True)
    assert corpus.intervention == "reviewed-local-docs-v2"
    assert corpus.profile["network_enabled"] is False
    assert corpus.search("reference") == corpus.search("reference")
    assert len(corpus.search("reference", top_k=5)["matches"]) == 4


def test_published_pin_rejects_wrong_source_bytes(tmp_path):
    data = manifest()
    for row in data["documents"]:
        (tmp_path / row["path"]).write_text("wrong source bytes", encoding="utf-8")
    with pytest.raises(OfflineDocsError, match="sha256 does not match"):
        OfflineDocsCorpus.from_manifest(tmp_path, data)


def test_manifest_only_changes_trigger_existing_ci():
    workflow = (CORPUS_DIR.parents[4] / ".github/workflows/evaluator-closure.yml").read_text()
    assert workflow.count(
        '"benchmark-vabench-release-v4/operations/calibration_pilot/corpora/**"'
    ) == 2


@pytest.mark.parametrize("section, query", [
    ("modules-ports-disciplines", "module ANSI electrical declarations"),
    ("analog-contributions", "analog procedural contributions equations"),
    ("events-state-control", "initial_step cross threshold events"),
    ("operators-system-tasks", "ddt laplace_nd idtmod operators"),
])
def test_opt_in_real_source_retrieval(section, query):
    root = os.environ.get("VAEVAS_VERILOGA_DOCS_ROOT")
    if not root:
        pytest.skip("set VAEVAS_VERILOGA_DOCS_ROOT to a locally acquired pinned corpus")
    corpus = OfflineDocsCorpus.from_manifest(Path(root), manifest())
    corpus.assert_model_context_allowed(external_provider=True)
    result = corpus.search(query, top_k=1)
    assert result == corpus.search(query, top_k=1)
    assert len(result["matches"]) == 1
    match = result["matches"][0]
    assert match["source_sha256"] == SOURCES[section + ".md"]
    assert match["source_path"] == section + ".md"
    assert match["snippet"] and len(match["snippet"]) <= 600
