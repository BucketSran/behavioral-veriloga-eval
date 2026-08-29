"""Trusted, append-only persistence for validated final score sidecars."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass
import json
import os
from pathlib import Path
import tempfile
from typing import Any

from .authority_profiles import (
    final_test_profile_sha256,
    profile_input_identity_sha256,
)
from .result_artifact import (
    score_sidecar_sha256,
    validate_score_sidecar_authority,
)
from .state import EpisodeContext, FinalJudgment, FrozenSubmission


class ImmutableEvidenceError(RuntimeError):
    """A final evidence document could not be published without mutation."""


@dataclass(frozen=True, slots=True)
class ImmutableScoreSidecarRecord:
    """Trusted receipt for one content-addressed sidecar publication."""

    path: Path
    sha256: str
    submission_tree_sha256: str
    final_profile_sha256: str
    final_profile_input_identity_sha256: str


def write_immutable_score_sidecar(
    *,
    output_dir: Path,
    context: EpisodeContext,
    submission: FrozenSubmission,
    judgment: FinalJudgment,
    final_test_profile: Mapping[str, Any],
    score_sidecar: Mapping[str, Any],
) -> ImmutableScoreSidecarRecord:
    """Validate and atomically publish one score sidecar without overwrite."""
    if not isinstance(output_dir, Path):
        raise TypeError("output_dir must be a Path")
    if not isinstance(context, EpisodeContext):
        raise TypeError("context must be an EpisodeContext")

    validated = validate_score_sidecar_authority(
        score_sidecar=score_sidecar,
        final_test_profile=final_test_profile,
        judgment=judgment,
        submission=submission,
    )
    detached_sidecar = deepcopy(dict(validated))
    sidecar_sha256 = score_sidecar_sha256(detached_sidecar)
    profile_sha256 = final_test_profile_sha256(final_test_profile)
    profile_input_sha256 = profile_input_identity_sha256(
        profile_sha256=profile_sha256,
        input_kind="frozen_submission_tree",
        input_sha256=submission.tree_sha256,
        attempt_id=context.attempt_id,
        task_id=context.task_id,
    )
    payload = _canonical_json_bytes(detached_sidecar)

    sidecar_dir = _prepare_sidecar_directory(output_dir)
    destination = sidecar_dir / f"{sidecar_sha256}.json"
    temp_path = _write_fsynced_temporary(sidecar_dir, sidecar_sha256, payload)
    try:
        _publish_exclusive(temp_path, destination)
    except FileExistsError as exc:
        raise ImmutableEvidenceError(
            f"score sidecar already exists: {destination.name}"
        ) from exc
    except OSError as exc:
        raise ImmutableEvidenceError(
            f"failed to publish score sidecar: {exc}"
        ) from exc
    finally:
        temp_path.unlink(missing_ok=True)

    try:
        _fsync_directory(sidecar_dir)
    except OSError as exc:
        raise ImmutableEvidenceError(
            f"failed to sync score sidecar directory: {exc}"
        ) from exc

    return ImmutableScoreSidecarRecord(
        path=destination,
        sha256=sidecar_sha256,
        submission_tree_sha256=submission.tree_sha256,
        final_profile_sha256=profile_sha256,
        final_profile_input_identity_sha256=profile_input_sha256,
    )


def _prepare_sidecar_directory(output_dir: Path) -> Path:
    if output_dir.is_symlink():
        raise ImmutableEvidenceError("output directory must not be a symlink")
    if output_dir.exists() and not output_dir.is_dir():
        raise ImmutableEvidenceError("output directory must be a directory")
    output_dir.mkdir(parents=True, exist_ok=True)

    sidecar_dir = output_dir / "score-sidecars"
    if sidecar_dir.is_symlink():
        raise ImmutableEvidenceError("score-sidecars directory must not be a symlink")
    if sidecar_dir.exists() and not sidecar_dir.is_dir():
        raise ImmutableEvidenceError("score-sidecars path must be a directory")
    sidecar_dir.mkdir(exist_ok=True)
    if sidecar_dir.resolve(strict=True).parent != output_dir.resolve(strict=True):
        raise ImmutableEvidenceError("score-sidecars directory escaped output directory")
    return sidecar_dir


def _canonical_json_bytes(document: Mapping[str, Any]) -> bytes:
    return json.dumps(
        document,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _write_fsynced_temporary(
    directory: Path,
    sidecar_sha256: str,
    payload: bytes,
) -> Path:
    file_descriptor, raw_path = tempfile.mkstemp(
        dir=directory,
        prefix=f".{sidecar_sha256}.tmp-",
    )
    temp_path = Path(raw_path)
    try:
        with os.fdopen(file_descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
            os.fchmod(handle.fileno(), 0o444)
    except BaseException:
        temp_path.unlink(missing_ok=True)
        raise
    return temp_path


def _publish_exclusive(source: Path, destination: Path) -> None:
    os.link(source, destination, follow_symlinks=False)


def _fsync_directory(directory: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    file_descriptor = os.open(directory, flags)
    try:
        os.fsync(file_descriptor)
    finally:
        os.close(file_descriptor)
