"""Reviewed local documentation corpus contracts."""

from __future__ import annotations

import copy
import hashlib

import pytest


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _reviewed_manifest(text: str, *, path: str = "refs/guide.txt") -> dict:
    return {
        "schema_version": 2,
        "synthetic_only": False,
        "network_enabled": False,
        "builder": "unit-test-reviewed",
        "exclusions": [
            "hidden",
            "r53-test-task",
            "r53-solution",
            "checker-internals",
            "gold",
            "certified-fault",
            "final-score",
            "episode-artifact",
            "private-report",
            "private-alphapollo",
        ],
        "review": {
            "review_id": "review-001",
            "reviewer": "unit-test",
            "reviewed_at": "2026-08-31",
            "purpose": "general-language-reference",
            "external_provider_allowed": False,
        },
        "documents": [
            {
                "id": "reviewed-guide",
                "path": path,
                "source": "reviewed_local_reference",
                "license": "LicenseRef-User-Authorized",
                "section": "language_notes",
                "sha256": _sha(text),
                "contamination_categories": [],
                "provenance": {
                    "origin": "https://example.org/reviewed-guide",
                    "revision": "a" * 40,
                    "upstream_path": "docs/guide.txt",
                    "rights_basis": "owner-permission",
                    "rights_evidence_sha256": "b" * 64,
                },
            }
        ],
    }


def _write_reviewed_corpus(
    tmp_path, *, text: str = "Reviewed LOCAL_DOC resistor modeling note."
):
    from runners.agent_harness.tools.offline_docs import OfflineDocsCorpus

    root = tmp_path / "reviewed"
    (root / "refs").mkdir(parents=True)
    (root / "refs/guide.txt").write_text(text, encoding="utf-8")
    return OfflineDocsCorpus.from_manifest(root, _reviewed_manifest(text))


def test_v1_synthetic_profile_and_search_remain_compatible(tmp_path):
    from test_agent_harness_docs_integration import synthetic_corpus
    from runners.agent_harness.tool_registry import tool_descriptor_sha256
    from runners.agent_harness.tools.offline_docs_tool import (
        docs_prompt,
        docs_tool_descriptor,
    )

    corpus = synthetic_corpus(tmp_path / "synthetic")
    before = copy.deepcopy(corpus.profile)
    assert before["schema_version"] == 1
    assert before["synthetic_only"] is True
    assert corpus.intervention == "synthetic-frozen-docs-v1"
    corpus.assert_model_context_allowed(external_provider=True)
    assert corpus.profile == before
    assert corpus.search("resistor")["schema_version"] == 1
    descriptor = docs_tool_descriptor(corpus.profile, condition="Agentic")
    assert tool_descriptor_sha256(descriptor) == (
        "4173e259932bc46b3e0fd0c2544c724962ea044b79d49cd4a8accadbcf79c217"
    )
    match_schema = descriptor["observation_schema"]["properties"]["matches"]["items"][
        "properties"
    ]
    assert match_schema["source"] == {"const": "synthetic_fixture"}
    assert match_schema["license"] == {"const": "CC0-1.0"}
    assert docs_prompt(corpus.profile) == (
        "\nFrozen synthetic retrieval profile (reference data only):\n"
        '{"profile_sha256": "06fbe0638c4d0475a4c724be0d1a752672f70bcfcdcc7d54254a7703399bebe0"}'
    )


def test_reviewed_v2_binds_provenance_and_deterministic_search(tmp_path):
    import jsonschema

    from runners.agent_harness.tools.offline_docs import corpus_profile_sha256
    from runners.agent_harness.tools.offline_docs_tool import (
        docs_prompt,
        docs_tool_descriptor,
    )

    corpus = _write_reviewed_corpus(tmp_path)
    profile = corpus.profile
    assert profile["schema_version"] == 2
    assert profile["synthetic_only"] is False
    assert profile["network_enabled"] is False
    assert profile["review"]["purpose"] == "general-language-reference"
    assert corpus.intervention == "reviewed-local-docs-v2"
    assert corpus.profile_sha256 == corpus_profile_sha256(profile)
    assert corpus.search("resistor") == corpus.search("resistor")

    result = corpus.search("resistor", top_k=1)
    assert result["schema_version"] == 2
    assert result["matches"][0]["source"] == "reviewed_local_reference"
    assert result["matches"][0]["license"] == "LicenseRef-User-Authorized"
    schema = docs_tool_descriptor(profile, condition="Agentic")["observation_schema"]
    jsonschema.validate(result, schema)
    assert schema["properties"]["matches"]["items"]["properties"]["source"] == {
        "enum": ["reviewed_local_reference"]
    }
    assert schema["properties"]["matches"]["items"]["properties"]["license"] == {
        "enum": ["LicenseRef-User-Authorized"]
    }
    prompt = docs_prompt(profile)
    assert "synthetic retrieval" not in prompt
    assert "reviewed-local-docs-v2" in prompt


def test_reviewed_v2_rejects_content_provenance_drift(tmp_path):
    from runners.agent_harness.tools.offline_docs import (
        OfflineDocsCorpus,
        OfflineDocsError,
    )

    root = tmp_path / "reviewed"
    (root / "refs").mkdir(parents=True)
    (root / "refs/guide.txt").write_text("changed bytes", encoding="utf-8")
    with pytest.raises(OfflineDocsError, match="sha256"):
        OfflineDocsCorpus.from_manifest(root, _reviewed_manifest("declared bytes"))


@pytest.mark.parametrize(
    "mutation,match",
    [
        (lambda manifest: manifest["documents"][0].pop("license"), "license"),
        (
            lambda manifest: manifest["documents"][0].update(license="unknown"),
            "license",
        ),
        (
            lambda manifest: manifest["documents"][0]["provenance"].pop(
                "rights_evidence_sha256"
            ),
            "rights_evidence",
        ),
        (
            lambda manifest: manifest["documents"][0]["provenance"].update(
                rights_basis="unknown"
            ),
            "rights_basis",
        ),
        (
            lambda manifest: manifest["documents"][0]["provenance"].update(
                origin="https://user:pass@example.org/doc"
            ),
            "origin",
        ),
        (
            lambda manifest: manifest["documents"][0].update(
                contamination_categories=["hidden"]
            ),
            "contamination",
        ),
        (lambda manifest: manifest["exclusions"].remove("gold"), "exclusions"),
    ],
)
def test_reviewed_v2_rejects_missing_rights_secret_origin_or_contamination(
    tmp_path, mutation, match
):
    from runners.agent_harness.tools.offline_docs import (
        OfflineDocsCorpus,
        OfflineDocsError,
    )

    text = "Reviewed LOCAL_DOC resistor modeling note."
    root = tmp_path / "reviewed"
    (root / "refs").mkdir(parents=True)
    (root / "refs/guide.txt").write_text(text, encoding="utf-8")
    manifest = _reviewed_manifest(text)
    mutation(manifest)
    with pytest.raises(OfflineDocsError, match=match):
        OfflineDocsCorpus.from_manifest(root, manifest)


def test_reviewed_v2_remote_context_requires_explicit_permission(tmp_path):
    corpus = _write_reviewed_corpus(tmp_path)
    with pytest.raises(PermissionError, match="external provider"):
        corpus.assert_model_context_allowed(external_provider=True)
    corpus.assert_model_context_allowed(external_provider=False)


@pytest.mark.parametrize(
    "path",
    [
        "../escape.txt",
        "/tmp/escape.txt",
        "hidden/guide.txt",
        "private-alphapollo/a.txt",
    ],
)
def test_reviewed_v2_rejects_escape_symlink_and_excluded_paths(tmp_path, path):
    from runners.agent_harness.tools.offline_docs import (
        OfflineDocsCorpus,
        OfflineDocsError,
    )

    text = "Reviewed LOCAL_DOC resistor modeling note."
    root = tmp_path / "reviewed"
    (root / "refs").mkdir(parents=True)
    (root / "refs/guide.txt").write_text(text, encoding="utf-8")
    manifest = _reviewed_manifest(text, path=path)
    if path.startswith("hidden/") or path.startswith("private-alphapollo/"):
        (root / path.split("/")[0]).mkdir()
        (root / path).write_text(text, encoding="utf-8")
    with pytest.raises(OfflineDocsError):
        OfflineDocsCorpus.from_manifest(root, manifest)

    symlink_manifest = _reviewed_manifest(text)
    (root / "refs/guide.txt").unlink()
    (root / "refs/guide.txt").symlink_to(root / "refs")
    with pytest.raises(OfflineDocsError, match="symlink|regular file"):
        OfflineDocsCorpus.from_manifest(root, symlink_manifest)
