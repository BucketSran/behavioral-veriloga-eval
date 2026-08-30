"""Synthetic offline documentation retrieval contract."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pytest

from runners.agent_harness.tools.offline_docs import OfflineDocsError
from runners.agent_harness.tools.offline_docs import OfflineDocsCorpus
from runners.agent_harness.tools.offline_docs import corpus_profile_sha256
from runners.agent_harness.tools.offline_docs import validate_corpus_profile


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _manifest(path: str, text: str, **overrides: object) -> dict[str, object]:
    manifest: dict[str, object] = {
        "schema_version": 1,
        "synthetic_only": True,
        "network_enabled": False,
        "builder": "unit-test",
        "exclusions": ["hidden", "r53-test-task"],
        "documents": [
            {
                "id": "doc-public",
                "path": path,
                "source": "synthetic_fixture",
                "license": "CC0-1.0",
                "section": "public_notes",
                "sha256": _sha256(text),
            }
        ],
    }
    manifest.update(overrides)
    return manifest


def test_synthetic_corpus_search_is_stable_and_profile_bound(tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    source = docs_dir / "resistor.md"
    text = "Resistor mismatch checks compare transient gain and settling behavior."
    source.write_text(text, encoding="utf-8")

    manifest = _manifest("docs/resistor.md", text)
    manifest["documents"][0]["id"] = "doc-resistor"

    corpus = OfflineDocsCorpus.from_manifest(tmp_path, manifest)
    first = corpus.search("transient resistor", top_k=1)
    second = corpus.search("transient resistor", top_k=1)

    assert first == second
    assert first["corpus_profile_sha256"] == corpus.profile_sha256
    assert first["matches"][0]["doc_id"] == "doc-resistor"
    assert first["matches"][0]["source_sha256"] == _sha256(text)
    assert "transient gain" in first["matches"][0]["snippet"]


def test_corpus_is_an_immutable_snapshot_after_manifest_load(tmp_path: Path) -> None:
    source = tmp_path / "guide.md"
    original = "Capacitor startup checks use a public operating-point note."
    source.write_text(original, encoding="utf-8")

    corpus = OfflineDocsCorpus.from_manifest(
        tmp_path,
        _manifest("guide.md", original),
    )
    source.write_text("Injected private answer after corpus construction.", encoding="utf-8")

    result = corpus.search("capacitor startup", top_k=1)

    assert result["matches"][0]["doc_id"] == "doc-public"
    assert "public operating-point note" in result["matches"][0]["snippet"]
    assert "Injected private answer" not in result["matches"][0]["snippet"]


def test_persisted_profile_hash_is_self_field_independent(tmp_path: Path) -> None:
    source = tmp_path / "public.md"
    text = "Public synthetic note for validation-only retrieval."
    source.write_text(text, encoding="utf-8")
    corpus = OfflineDocsCorpus.from_manifest(
        tmp_path,
        _manifest("public.md", text),
    )

    profile = corpus.profile

    validate_corpus_profile(profile)
    assert profile["profile_sha256"] == corpus_profile_sha256(profile)

    profile["profile_sha256"] = "0" * 64
    with pytest.raises(OfflineDocsError, match="profile_sha256"):
        validate_corpus_profile(profile)

    profile = corpus.profile
    profile["documents"][0]["source"] = "unknown"
    profile.pop("profile_sha256")
    with pytest.raises(OfflineDocsError, match="source"):
        validate_corpus_profile(profile)

    profile = corpus.profile
    profile["source_tree_sha256"] = "0" * 64
    profile.pop("profile_sha256")
    with pytest.raises(OfflineDocsError, match="source_tree_sha256"):
        validate_corpus_profile(profile)


def test_manifest_rejects_untrusted_or_unstable_sources(tmp_path: Path) -> None:
    source = tmp_path / "safe.md"
    text = "Synthetic public comparator notes."
    source.write_text(text, encoding="utf-8")
    symlink = tmp_path / "linked.md"
    symlink.symlink_to(source)

    manifest = _manifest("linked.md", text)
    manifest["documents"][0]["id"] = "doc-linked"

    with pytest.raises(OfflineDocsError, match="symlink"):
        OfflineDocsCorpus.from_manifest(tmp_path, manifest)

    manifest["documents"][0]["path"] = "../safe.md"
    with pytest.raises(OfflineDocsError, match="confined"):
        OfflineDocsCorpus.from_manifest(tmp_path, manifest)

    manifest["documents"][0]["path"] = "safe.md"
    manifest["documents"][0]["license"] = ""
    with pytest.raises(OfflineDocsError, match="license"):
        OfflineDocsCorpus.from_manifest(tmp_path, manifest)

    manifest["documents"][0]["license"] = "CC0-1.0"
    manifest["documents"][0]["sha256"] = "0" * 64
    with pytest.raises(OfflineDocsError, match="sha256"):
        OfflineDocsCorpus.from_manifest(tmp_path, manifest)


def test_manifest_rejects_schema_drift_and_unknown_provenance(tmp_path: Path) -> None:
    source = tmp_path / "safe.md"
    text = "Synthetic public comparator notes."
    source.write_text(text, encoding="utf-8")

    manifest = _manifest("safe.md", text, extra="field")
    with pytest.raises(OfflineDocsError, match="unknown manifest fields"):
        OfflineDocsCorpus.from_manifest(tmp_path, manifest)

    manifest = _manifest("safe.md", text, exclusions=["hidden"])
    with pytest.raises(OfflineDocsError, match="exclusions"):
        OfflineDocsCorpus.from_manifest(tmp_path, manifest)

    manifest = _manifest("safe.md", text)
    manifest["documents"][0]["source"] = "public_web"
    with pytest.raises(OfflineDocsError, match="source"):
        OfflineDocsCorpus.from_manifest(tmp_path, manifest)

    manifest = _manifest("safe.md", text)
    manifest["documents"][0]["license"] = "MIT"
    with pytest.raises(OfflineDocsError, match="license"):
        OfflineDocsCorpus.from_manifest(tmp_path, manifest)

    manifest = _manifest("safe.md", text)
    manifest["documents"][0]["note"] = "unbounded metadata"
    with pytest.raises(OfflineDocsError, match="unknown document fields"):
        OfflineDocsCorpus.from_manifest(tmp_path, manifest)


def test_filesystem_open_rejects_root_symlink_and_nonregular_files(tmp_path: Path) -> None:
    real_root = tmp_path / "real"
    real_root.mkdir()
    text = "Synthetic public root note."
    (real_root / "safe.md").write_text(text, encoding="utf-8")
    linked_root = tmp_path / "linked-root"
    linked_root.symlink_to(real_root)

    with pytest.raises(OfflineDocsError, match="root.*symlink"):
        OfflineDocsCorpus.from_manifest(linked_root, _manifest("safe.md", text))

    fifo = real_root / "stream.md"
    os.mkfifo(fifo)
    with pytest.raises(OfflineDocsError, match="regular file"):
        OfflineDocsCorpus.from_manifest(real_root, _manifest("stream.md", ""))


def test_search_rejects_bool_top_k_and_reports_truncation(tmp_path: Path) -> None:
    short = tmp_path / "short.md"
    long = tmp_path / "long.md"
    short_text = "resistor " + "short note"
    long_text = "resistor " + ("long " * 700)
    short.write_text(short_text, encoding="utf-8")
    long.write_text(long_text, encoding="utf-8")
    manifest = _manifest("short.md", short_text)
    manifest["documents"].append(
        {
            "id": "doc-long",
            "path": "long.md",
            "source": "synthetic_fixture",
            "license": "CC0-1.0",
            "section": "public_notes",
            "sha256": _sha256(long_text),
        }
    )
    corpus = OfflineDocsCorpus.from_manifest(tmp_path, manifest)

    with pytest.raises(OfflineDocsError, match="top_k"):
        corpus.search("resistor", top_k=True)
    with pytest.raises(OfflineDocsError, match="section_filter"):
        corpus.search("resistor", section_filter=["public_notes"])

    result = corpus.search("resistor", top_k=1)

    assert result["omitted_match_count"] == 1
    assert result["truncated"] is True
    assert result["matches"][0]["truncated"] is True
