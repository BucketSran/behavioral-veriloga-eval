"""Deterministic offline documentation retrieval for synthetic fixtures."""

from __future__ import annotations

import copy
import datetime as _datetime
import hashlib
import json
import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlsplit


MAX_DOCUMENTS = 64
MAX_DOCUMENT_BYTES = 64 * 1024
MAX_QUERY_CHARS = 512
MAX_TOP_K = 5
MAX_SNIPPET_CHARS = 600
SYNTHETIC_PROFILE_SCHEMA_VERSION = 1
REVIEWED_PROFILE_SCHEMA_VERSION = 2
PROFILE_SCHEMA_VERSION = SYNTHETIC_PROFILE_SCHEMA_VERSION
MAX_METADATA_CHARS = 128
MAX_PATH_CHARS = 512

_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")
_APPROVED_SOURCES = frozenset({"synthetic_fixture"})
_APPROVED_LICENSES = frozenset({"CC0-1.0"})
_REVIEWED_RIGHTS_BASES = frozenset({"license", "owner-permission", "local-license"})
_REQUIRED_EXCLUSIONS = frozenset({"hidden", "r53-test-task"})
_POLICY_EXCLUSION_CATEGORIES = (
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
)
_EXCLUDED_PATH_PARTS = frozenset(_POLICY_EXCLUSION_CATEGORIES)
_MANIFEST_KEYS = frozenset(
    {
        "schema_version",
        "synthetic_only",
        "network_enabled",
        "builder",
        "exclusions",
        "documents",
    }
)
_REVIEWED_MANIFEST_KEYS = _MANIFEST_KEYS | frozenset({"review"})
_MANIFEST_DOCUMENT_KEYS = frozenset(
    {"id", "path", "source", "license", "section", "sha256"}
)
_REVIEWED_MANIFEST_DOCUMENT_KEYS = _MANIFEST_DOCUMENT_KEYS | frozenset(
    {"provenance", "contamination_categories"}
)
_REVIEW_KEYS = frozenset(
    {"review_id", "reviewer", "reviewed_at", "purpose", "external_provider_allowed"}
)
_PROVENANCE_KEYS = frozenset(
    {"origin", "revision", "upstream_path", "rights_basis", "rights_evidence_sha256"}
)
_PROFILE_KEYS = frozenset(
    {
        "schema_version",
        "synthetic_only",
        "network_enabled",
        "builder",
        "limits",
        "policy",
        "exclusions",
        "source_tree_sha256",
        "index_sha256",
        "documents",
        "profile_sha256",
    }
)
_REVIEWED_PROFILE_KEYS = _PROFILE_KEYS | frozenset({"review"})
_PROFILE_DOCUMENT_KEYS = frozenset(
    {"id", "path", "source", "license", "section", "sha256", "bytes"}
)
_REVIEWED_PROFILE_DOCUMENT_KEYS = _PROFILE_DOCUMENT_KEYS | frozenset(
    {"provenance", "contamination_categories"}
)
_INDEX_POLICY = {
    "algorithm": "lexical_token_overlap_v1",
    "tokenizer": "ascii_alnum_underscore_lower_v1",
    "chunk_policy": "single_document_chunk_v1",
    "tie_break": ["score_desc", "path_asc", "doc_id_asc", "chunk_id_asc"],
}


class OfflineDocsError(ValueError):
    """Raised when a corpus manifest or retrieval request is not admissible."""


@dataclass(frozen=True)
class _Document:
    doc_id: str
    path: str
    source: str
    license: str
    section: str
    content: str
    sha256: str
    tokens: tuple[str, ...]


def _canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def _canonical_sha256(value: Mapping[str, Any]) -> str:
    payload = _canonical_json(value)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _reject_unknown_keys(
    row: Mapping[str, Any], allowed: frozenset[str], label: str
) -> None:
    extra = sorted(set(row) - allowed)
    if extra:
        raise OfflineDocsError(f"unknown {label} fields: {', '.join(extra)}")


def _source_entries_from_profile(profile: Mapping[str, Any]) -> list[dict[str, Any]]:
    documents = profile.get("documents")
    if not isinstance(documents, list):
        raise OfflineDocsError("profile documents must be a bounded non-empty list")
    return [copy.deepcopy(dict(document)) for document in documents]


def _source_tree_sha256(source_entries: list[dict[str, Any]]) -> str:
    return _canonical_sha256({"sources": _sorted_source_entries(source_entries)})


def _index_sha256(source_entries: list[dict[str, Any]]) -> str:
    return _canonical_sha256(
        {"policy": _INDEX_POLICY, "sources": _sorted_source_entries(source_entries)}
    )


def corpus_profile_sha256(profile: Mapping[str, Any]) -> str:
    """Return the canonical profile hash, ignoring an embedded self field."""

    detached = copy.deepcopy(dict(profile))
    detached.pop("profile_sha256", None)
    return _canonical_sha256(detached)


def validate_corpus_profile(profile: Mapping[str, Any]) -> None:
    """Validate a persisted profile without reading source documents."""

    schema_version = _schema_version(profile)
    if schema_version == SYNTHETIC_PROFILE_SCHEMA_VERSION:
        _reject_unknown_keys(profile, _PROFILE_KEYS, "profile")
        if profile.get("synthetic_only") is not True:
            raise OfflineDocsError("profile must declare synthetic_only=true")
    elif schema_version == REVIEWED_PROFILE_SCHEMA_VERSION:
        _reject_unknown_keys(profile, _REVIEWED_PROFILE_KEYS, "profile")
        if profile.get("synthetic_only") is not False:
            raise OfflineDocsError("reviewed profile must declare synthetic_only=false")
        _validate_review(profile.get("review"), label="profile review")
    else:
        raise OfflineDocsError("profile schema_version must be 1 or 2")
    if profile.get("network_enabled") is not False:
        raise OfflineDocsError("profile must declare network_enabled=false")
    for key in ("builder", "source_tree_sha256", "index_sha256"):
        value = profile.get(key)
        if not isinstance(value, str) or not value:
            raise OfflineDocsError(f"profile {key} must be a non-empty string")
    for key in ("source_tree_sha256", "index_sha256"):
        if not re.fullmatch(r"[0-9a-f]{64}", str(profile[key])):
            raise OfflineDocsError(f"profile {key} must be lowercase hex")
    limits = profile.get("limits")
    expected_limits = {
        "max_documents": MAX_DOCUMENTS,
        "max_document_bytes": MAX_DOCUMENT_BYTES,
        "max_query_chars": MAX_QUERY_CHARS,
        "max_top_k": MAX_TOP_K,
        "max_snippet_chars": MAX_SNIPPET_CHARS,
    }
    if limits != expected_limits:
        raise OfflineDocsError("profile limits do not match offline docs")
    exclusions = profile.get("exclusions")
    if not isinstance(exclusions, list) or not all(
        isinstance(item, str) and item for item in exclusions
    ):
        raise OfflineDocsError("profile exclusions must be a non-empty string list")
    if (
        schema_version == SYNTHETIC_PROFILE_SCHEMA_VERSION
        and not _REQUIRED_EXCLUSIONS.issubset(set(exclusions))
    ):
        raise OfflineDocsError(
            "profile exclusions must include hidden and r53-test-task"
        )
    if schema_version == REVIEWED_PROFILE_SCHEMA_VERSION and set(exclusions) != set(
        _POLICY_EXCLUSION_CATEGORIES
    ):
        raise OfflineDocsError(
            "reviewed profile exclusions must match all offline docs exclusion categories"
        )
    documents = profile.get("documents")
    if (
        not isinstance(documents, list)
        or not documents
        or len(documents) > MAX_DOCUMENTS
    ):
        raise OfflineDocsError("profile documents must be a bounded non-empty list")
    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    for document in documents:
        if not isinstance(document, Mapping):
            raise OfflineDocsError("profile document row must be an object")
        _reject_unknown_keys(
            document,
            _PROFILE_DOCUMENT_KEYS
            if schema_version == SYNTHETIC_PROFILE_SCHEMA_VERSION
            else _REVIEWED_PROFILE_DOCUMENT_KEYS,
            "profile document",
        )
        doc_id = _require_text(document, "id")
        relative_path = _require_text(document, "path")
        _validate_relative_path_text(
            relative_path,
            reject_excluded=schema_version == REVIEWED_PROFILE_SCHEMA_VERSION,
        )
        source = _require_text(document, "source")
        license_id = _require_text(document, "license")
        if schema_version == SYNTHETIC_PROFILE_SCHEMA_VERSION:
            _require_approved_source(source)
            _require_approved_license(license_id)
        else:
            _validate_reviewed_license(license_id)
            _validate_reviewed_document_assertions(document)
        _require_text(document, "section")
        sha256 = _require_text(document, "sha256")
        if not re.fullmatch(r"[0-9a-f]{64}", sha256):
            raise OfflineDocsError("profile document sha256 must be lowercase hex")
        byte_count = document.get("bytes")
        if not isinstance(byte_count, int) or not 0 <= byte_count <= MAX_DOCUMENT_BYTES:
            raise OfflineDocsError("profile document bytes must be within bounds")
        if doc_id in seen_ids or relative_path in seen_paths:
            raise OfflineDocsError("profile document ids and paths must be unique")
        seen_ids.add(doc_id)
        seen_paths.add(relative_path)
    source_entries = _source_entries_from_profile(profile)
    expected_policy = {
        "index": _INDEX_POLICY,
        "allowed_sources": sorted({entry["source"] for entry in source_entries}),
        "allowed_licenses": sorted({entry["license"] for entry in source_entries}),
        "exclusion_categories": list(_POLICY_EXCLUSION_CATEGORIES),
    }
    if profile.get("policy") != expected_policy:
        raise OfflineDocsError("profile policy does not match offline docs")
    expected_source_tree_sha256 = _source_tree_sha256(source_entries)
    if profile["source_tree_sha256"] != expected_source_tree_sha256:
        raise OfflineDocsError(
            "profile source_tree_sha256 does not match profile documents"
        )
    expected_index_sha256 = _index_sha256(source_entries)
    if profile["index_sha256"] != expected_index_sha256:
        raise OfflineDocsError(
            "profile index_sha256 does not match profile documents and policy"
        )
    embedded_hash = profile.get("profile_sha256")
    if embedded_hash is not None and embedded_hash != corpus_profile_sha256(profile):
        raise OfflineDocsError("profile_sha256 does not match profile content")


def _bytes_sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _text_tokens(text: str) -> tuple[str, ...]:
    return tuple(token.lower() for token in _TOKEN_RE.findall(text))


def _require_text(row: Mapping[str, Any], key: str) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value.strip():
        raise OfflineDocsError(f"document {key} must be a non-empty string")
    limit = MAX_PATH_CHARS if key == "path" else MAX_METADATA_CHARS
    if len(value) > limit:
        raise OfflineDocsError(f"document {key} exceeds {limit} characters")
    return value


def _schema_version(row: Mapping[str, Any]) -> int:
    value = row.get("schema_version")
    if type(value) is not int:
        raise OfflineDocsError("schema_version must be an integer")
    return value


def _require_approved_source(value: str) -> None:
    if value not in _APPROVED_SOURCES:
        raise OfflineDocsError("document source must be synthetic_fixture")


def _require_approved_license(value: str) -> None:
    if value not in _APPROVED_LICENSES:
        raise OfflineDocsError(
            "document license must be an approved synthetic fixture license"
        )


def _validate_relative_path_text(
    relative_path: str, *, reject_excluded: bool = False
) -> Path:
    path = Path(relative_path)
    if path.is_absolute() or ".." in path.parts:
        raise OfflineDocsError("document path must be relative and confined")
    if not path.parts:
        raise OfflineDocsError("document path must not be empty")
    if reject_excluded and any(part in _EXCLUDED_PATH_PARTS for part in path.parts):
        raise OfflineDocsError("document path uses an excluded directory")
    return path


def _confined_file(
    root: Path, relative_path: str, *, reject_excluded: bool = False
) -> Path:
    path = _validate_relative_path_text(relative_path, reject_excluded=reject_excluded)
    if root.is_symlink():
        raise OfflineDocsError("corpus root must not be a symlink")
    root_resolved = root.resolve(strict=True)
    unresolved = root_resolved / path
    current = root_resolved
    for part in path.parts:
        current = current / part
        if current.is_symlink():
            raise OfflineDocsError("document path must not contain a symlink")
    candidate = unresolved.resolve(strict=False)
    try:
        candidate.relative_to(root_resolved)
    except ValueError as exc:
        raise OfflineDocsError("document path escapes corpus root") from exc
    try:
        mode = candidate.lstat().st_mode
    except FileNotFoundError as exc:
        raise OfflineDocsError("document path must name a regular file") from exc
    if not stat.S_ISREG(mode):
        raise OfflineDocsError("document path must name a regular file")
    return candidate


def _validate_review(value: Any, *, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise OfflineDocsError(f"{label} must be an object")
    _reject_unknown_keys(value, _REVIEW_KEYS, label)
    review = dict(value)
    _require_text(review, "review_id")
    _require_text(review, "reviewer")
    reviewed_at = _require_text(review, "reviewed_at")
    try:
        if _datetime.date.fromisoformat(reviewed_at).isoformat() != reviewed_at:
            raise ValueError
    except ValueError as exc:
        raise OfflineDocsError("reviewed_at must be an ISO date") from exc
    if review.get("purpose") != "general-language-reference":
        raise OfflineDocsError("review purpose must be general-language-reference")
    if type(review.get("external_provider_allowed")) is not bool:
        raise OfflineDocsError("review external_provider_allowed must be a boolean")
    return copy.deepcopy(review)


def _validate_reviewed_license(value: str) -> None:
    if value.lower() == "unknown" or value == "UNKNOWN":
        raise OfflineDocsError("document license must not be unknown")
    if value == "LicenseRef-User-Authorized":
        return
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.+-]*(?:-[A-Za-z0-9.+-]+)*", value):
        raise OfflineDocsError(
            "document license must be SPDX-like or LicenseRef-User-Authorized"
        )


def _validate_origin(value: str) -> None:
    if value.startswith("https://"):
        parsed = urlsplit(value)
        if (
            parsed.scheme != "https"
            or not parsed.netloc
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
        ):
            raise OfflineDocsError("provenance origin must be a nonsecret https URL")
        return
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{2,127}", value):
        raise OfflineDocsError(
            "provenance origin must be a nonsecret https URL or local descriptive id"
        )


def _validate_provenance(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise OfflineDocsError("document provenance must be an object")
    _reject_unknown_keys(value, _PROVENANCE_KEYS, "document provenance")
    provenance = dict(value)
    origin = _require_text(provenance, "origin")
    _validate_origin(origin)
    revision = _require_text(provenance, "revision")
    if not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", revision):
        raise OfflineDocsError(
            "provenance revision must be a 40-hex commit or 64-hex content identity"
        )
    upstream_path = _require_text(provenance, "upstream_path")
    _validate_relative_path_text(upstream_path, reject_excluded=True)
    rights_basis = _require_text(provenance, "rights_basis")
    if rights_basis not in _REVIEWED_RIGHTS_BASES:
        raise OfflineDocsError("provenance rights_basis is not allowed")
    evidence = _require_text(provenance, "rights_evidence_sha256")
    if not re.fullmatch(r"[0-9a-f]{64}", evidence):
        raise OfflineDocsError(
            "provenance rights_evidence_sha256 must be lowercase hex"
        )
    return copy.deepcopy(provenance)


def _validate_contamination_categories(value: Any) -> list[str]:
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item for item in value
    ):
        raise OfflineDocsError(
            "document contamination_categories must be a string list"
        )
    declared = set(value)
    if declared:
        raise OfflineDocsError("document declares excluded contamination categories")
    return list(value)


def _validate_reviewed_document_assertions(
    document: Mapping[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    provenance = _validate_provenance(document.get("provenance"))
    categories = _validate_contamination_categories(
        document.get("contamination_categories")
    )
    return provenance, categories


def _read_regular_file_bounded(path: Path) -> bytes:
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    if hasattr(os, "O_NONBLOCK"):
        flags |= os.O_NONBLOCK
    try:
        file_descriptor = os.open(path, flags)
    except OSError as exc:
        raise OfflineDocsError("document path must name a regular file") from exc
    try:
        if not stat.S_ISREG(os.fstat(file_descriptor).st_mode):
            raise OfflineDocsError("document path must name a regular file")
        chunks: list[bytes] = []
        remaining = MAX_DOCUMENT_BYTES + 1
        while remaining > 0:
            chunk = os.read(file_descriptor, remaining)
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        return b"".join(chunks)
    finally:
        os.close(file_descriptor)


def _sorted_source_entries(
    source_entries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return sorted(source_entries, key=lambda item: (item["path"], item["id"]))


class OfflineDocsCorpus:
    """Immutable synthetic corpus snapshot with deterministic lexical search."""

    def __init__(
        self, profile: Mapping[str, Any], documents: tuple[_Document, ...]
    ) -> None:
        self._profile = copy.deepcopy(dict(profile))
        self._documents = documents
        validate_corpus_profile(self._profile)
        self.profile_sha256 = corpus_profile_sha256(self._profile)

    @property
    def profile(self) -> dict[str, Any]:
        """Return a detached JSON-compatible corpus profile."""

        profile = copy.deepcopy(self._profile)
        profile["profile_sha256"] = self.profile_sha256
        return profile

    @property
    def intervention(self) -> str:
        if self._profile["schema_version"] == REVIEWED_PROFILE_SCHEMA_VERSION:
            return "reviewed-local-docs-v2"
        return "synthetic-frozen-docs-v1"

    def assert_model_context_allowed(self, *, external_provider: bool) -> None:
        if type(external_provider) is not bool:
            raise TypeError("external_provider must be a boolean")
        if self._profile["schema_version"] == SYNTHETIC_PROFILE_SCHEMA_VERSION:
            return
        allowed = self._profile["review"]["external_provider_allowed"]
        if external_provider and allowed is not True:
            raise PermissionError(
                "reviewed docs are not approved for external provider model context"
            )

    @classmethod
    def from_manifest(
        cls, root: Path, manifest: Mapping[str, Any]
    ) -> "OfflineDocsCorpus":
        schema_version = _schema_version(manifest)
        if schema_version == SYNTHETIC_PROFILE_SCHEMA_VERSION:
            _reject_unknown_keys(manifest, _MANIFEST_KEYS, "manifest")
            if manifest.get("synthetic_only") is not True:
                raise OfflineDocsError("manifest must declare synthetic_only=true")
            review = None
        elif schema_version == REVIEWED_PROFILE_SCHEMA_VERSION:
            _reject_unknown_keys(manifest, _REVIEWED_MANIFEST_KEYS, "manifest")
            if manifest.get("synthetic_only") is not False:
                raise OfflineDocsError(
                    "reviewed manifest must declare synthetic_only=false"
                )
            review = _validate_review(manifest.get("review"), label="manifest review")
        else:
            raise OfflineDocsError("manifest schema_version must be 1 or 2")
        if manifest.get("network_enabled") is not False:
            raise OfflineDocsError("manifest must declare network_enabled=false")
        builder = manifest.get("builder")
        if not isinstance(builder, str) or not builder.strip():
            raise OfflineDocsError("manifest builder must be a non-empty string")
        exclusions = manifest.get("exclusions")
        if not isinstance(exclusions, list) or not all(
            isinstance(item, str) and item for item in exclusions
        ):
            raise OfflineDocsError(
                "manifest exclusions must be a non-empty string list"
            )
        if (
            schema_version == SYNTHETIC_PROFILE_SCHEMA_VERSION
            and not _REQUIRED_EXCLUSIONS.issubset(set(exclusions))
        ):
            raise OfflineDocsError(
                "manifest exclusions must include hidden and r53-test-task"
            )
        if schema_version == REVIEWED_PROFILE_SCHEMA_VERSION and set(exclusions) != set(
            _POLICY_EXCLUSION_CATEGORIES
        ):
            raise OfflineDocsError(
                "reviewed manifest exclusions must match all offline docs exclusion categories"
            )
        raw_documents = manifest.get("documents")
        if not isinstance(raw_documents, list) or not raw_documents:
            raise OfflineDocsError("manifest documents must be a non-empty list")
        if len(raw_documents) > MAX_DOCUMENTS:
            raise OfflineDocsError(f"manifest documents exceed {MAX_DOCUMENTS}")

        seen_ids: set[str] = set()
        seen_paths: set[str] = set()
        documents: list[_Document] = []
        source_entries: list[dict[str, Any]] = []
        for raw in raw_documents:
            if not isinstance(raw, Mapping):
                raise OfflineDocsError("document row must be an object")
            _reject_unknown_keys(
                raw,
                _MANIFEST_DOCUMENT_KEYS
                if schema_version == SYNTHETIC_PROFILE_SCHEMA_VERSION
                else _REVIEWED_MANIFEST_DOCUMENT_KEYS,
                "document",
            )
            doc_id = _require_text(raw, "id")
            relative_path = _require_text(raw, "path")
            _validate_relative_path_text(
                relative_path,
                reject_excluded=schema_version == REVIEWED_PROFILE_SCHEMA_VERSION,
            )
            source = _require_text(raw, "source")
            license_id = _require_text(raw, "license")
            reviewed_extra: dict[str, Any] = {}
            if schema_version == SYNTHETIC_PROFILE_SCHEMA_VERSION:
                _require_approved_source(source)
                _require_approved_license(license_id)
            else:
                _validate_reviewed_license(license_id)
                provenance, contamination_categories = (
                    _validate_reviewed_document_assertions(raw)
                )
                reviewed_extra = {
                    "provenance": provenance,
                    "contamination_categories": contamination_categories,
                }
            section = _require_text(raw, "section")
            declared_sha256 = _require_text(raw, "sha256")
            if not re.fullmatch(r"[0-9a-f]{64}", declared_sha256):
                raise OfflineDocsError("document sha256 must be lowercase hex")
            if doc_id in seen_ids:
                raise OfflineDocsError("duplicate document id")
            if relative_path in seen_paths:
                raise OfflineDocsError("duplicate document path")
            seen_ids.add(doc_id)
            seen_paths.add(relative_path)

            file_path = _confined_file(
                root,
                relative_path,
                reject_excluded=schema_version == REVIEWED_PROFILE_SCHEMA_VERSION,
            )
            content_bytes = _read_regular_file_bounded(file_path)
            if len(content_bytes) > MAX_DOCUMENT_BYTES:
                raise OfflineDocsError(
                    f"document {doc_id} exceeds {MAX_DOCUMENT_BYTES} bytes"
                )
            actual_sha256 = _bytes_sha256(content_bytes)
            if actual_sha256 != declared_sha256:
                raise OfflineDocsError("document sha256 does not match source bytes")
            try:
                content = content_bytes.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise OfflineDocsError("document source must be utf-8") from exc
            tokens = _text_tokens(content)
            documents.append(
                _Document(
                    doc_id,
                    relative_path,
                    source,
                    license_id,
                    section,
                    content,
                    actual_sha256,
                    tokens,
                )
            )
            source_entries.append(
                {
                    "id": doc_id,
                    "path": relative_path,
                    "source": source,
                    "license": license_id,
                    "section": section,
                    "sha256": actual_sha256,
                    "bytes": len(content_bytes),
                    **reviewed_extra,
                }
            )

        source_entries = _sorted_source_entries(source_entries)
        source_tree_sha256 = _source_tree_sha256(source_entries)
        index_sha256 = _index_sha256(source_entries)
        profile = {
            "schema_version": schema_version,
            "synthetic_only": schema_version == SYNTHETIC_PROFILE_SCHEMA_VERSION,
            "network_enabled": False,
            "builder": builder,
            "policy": {
                "index": _INDEX_POLICY,
                "allowed_sources": sorted(
                    {entry["source"] for entry in source_entries}
                ),
                "allowed_licenses": sorted(
                    {entry["license"] for entry in source_entries}
                ),
                "exclusion_categories": list(_POLICY_EXCLUSION_CATEGORIES),
            },
            "limits": {
                "max_documents": MAX_DOCUMENTS,
                "max_document_bytes": MAX_DOCUMENT_BYTES,
                "max_query_chars": MAX_QUERY_CHARS,
                "max_top_k": MAX_TOP_K,
                "max_snippet_chars": MAX_SNIPPET_CHARS,
            },
            "exclusions": list(exclusions),
            "source_tree_sha256": source_tree_sha256,
            "index_sha256": index_sha256,
            "documents": source_entries,
        }
        if review is not None:
            profile["review"] = review
        documents_tuple = tuple(
            sorted(documents, key=lambda item: (item.path, item.doc_id))
        )
        return cls(profile, documents_tuple)

    def search(
        self, query: str, *, top_k: int = 3, section_filter: str | None = None
    ) -> dict[str, Any]:
        if not isinstance(query, str) or not query.strip():
            raise OfflineDocsError("query must be a non-empty string")
        if len(query) > MAX_QUERY_CHARS:
            raise OfflineDocsError(f"query exceeds {MAX_QUERY_CHARS} characters")
        if (
            not isinstance(top_k, int)
            or isinstance(top_k, bool)
            or not 1 <= top_k <= MAX_TOP_K
        ):
            raise OfflineDocsError(f"top_k must be between 1 and {MAX_TOP_K}")
        if section_filter is not None:
            if not isinstance(section_filter, str):
                raise OfflineDocsError("section_filter must be a string")
            sections = {doc.section for doc in self._documents}
            if section_filter not in sections:
                raise OfflineDocsError("section_filter must name a declared section")

        query_tokens = set(_text_tokens(query))
        candidates: list[tuple[int, str, str, _Document]] = []
        for document in self._documents:
            if section_filter is not None and document.section != section_filter:
                continue
            score = len(query_tokens.intersection(document.tokens))
            if score <= 0:
                continue
            candidates.append((-score, document.path, document.doc_id, document))
        candidates.sort(key=lambda item: (item[0], item[1], item[2], "chunk-0000"))

        matches: list[dict[str, Any]] = []
        selected = candidates[:top_k]
        omitted_match_count = max(0, len(candidates) - len(selected))
        for rank, (negative_score, _, _, document) in enumerate(selected, start=1):
            snippet = document.content[:MAX_SNIPPET_CHARS]
            matches.append(
                {
                    "rank": rank,
                    "doc_id": document.doc_id,
                    "chunk_id": "chunk-0000",
                    "section": document.section,
                    "source": document.source,
                    "license": document.license,
                    "source_path": document.path,
                    "source_sha256": document.sha256,
                    "content_sha256": document.sha256,
                    "score": -negative_score,
                    "snippet": snippet,
                    "truncated": len(document.content) > MAX_SNIPPET_CHARS,
                }
            )
        return {
            "schema_version": self._profile["schema_version"],
            "corpus_profile_sha256": self.profile_sha256,
            "source_tree_sha256": self._profile["source_tree_sha256"],
            "index_sha256": self._profile["index_sha256"],
            "query_sha256": hashlib.sha256(query.encode("utf-8")).hexdigest(),
            "query_chars": len(query),
            "top_k": top_k,
            "section_filter": section_filter,
            "matches": matches,
            "omitted_match_count": omitted_match_count,
            "truncated": omitted_match_count > 0
            or any(match["truncated"] for match in matches),
        }
