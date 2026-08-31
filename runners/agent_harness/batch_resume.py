"""Small durable batch boundary; never resumes model state or invokes a judge.

Like Inspect eval sets, completion belongs to a persistent batch, not a process.
Atomic publication reuses the scored-result store's fsync/exclusive-link helpers.
The caller owns semantic evidence verification and infrastructure retry policy.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess

from .result_store import _fsync_directory, _publish_exclusive, _write_fsynced_temporary


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def docker_image_identity(image: str, *, docker_command: str = "docker", timeout_s: float = 30) -> str:
    """Resolve a local image; callers execute this ID, never the mutable tag."""
    observed = subprocess.run(
        [*shlex.split(docker_command), "image", "inspect", "--format", "{{.Id}}", image],
        text=True, capture_output=True, timeout=min(30, timeout_s), check=True,
    ).stdout.strip()
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", observed):
        raise ValueError("batch Docker image identity is invalid")
    return observed


def _digest(value: dict) -> str:
    return hashlib.sha256(_payload(value)).hexdigest()


def _payload(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False,
                      separators=(",", ":")).encode()


def _atomic_once(path: Path, value: dict) -> None:
    payload = _payload(value)
    temporary = _write_fsynced_temporary(path.parent, _digest(value), payload)
    try:
        _publish_exclusive(temporary, path)
        _fsync_directory(path.parent)
    finally:
        temporary.unlink(missing_ok=True)


def _no_symlinks(path: Path) -> None:
    if any(part.is_symlink() for part in (path, *path.parents)):
        raise ValueError("batch paths must not contain symlinks")


def _tree(path: Path) -> dict[str, str]:
    _no_symlinks(path)
    if not path.is_dir():
        raise ValueError("batch terminal runtime is missing")
    result = {}
    for item in sorted(path.rglob("*")):
        if item.is_symlink():
            # Runtime export has a public/public -> . compatibility alias.
            # Hash confined link spelling without walking it or reading outside.
            try:
                item.resolve(strict=True).relative_to(path.resolve(strict=True))
            except (ValueError, OSError, RuntimeError) as exc:
                raise ValueError("batch evidence symlink is broken or escapes runtime") from exc
            result[item.relative_to(path).as_posix()] = "symlink:" + hashlib.sha256(
                os.readlink(item).encode()).hexdigest()
        elif item.is_file():
            result[item.relative_to(path).as_posix()] = file_sha256(item)
        elif item.is_dir():
            result[item.relative_to(path).as_posix()] = "directory"
        else:
            raise ValueError("batch evidence contains a non-regular file")
    return result


def source_identity(repo: Path) -> dict[str, str]:
    """Bind execution bytes, not mutable Git labels or temporary output paths."""
    paths = set()
    for relative in ("runners", "benchmark-vabench-release-v4/operations/calibration_pilot",
                     "benchmark-vabench-release-v4/runners", "schemas", "environment"):
        paths.update(path for path in (repo / relative).rglob("*")
                     if path.is_file() and "__pycache__" not in path.parts
                     and path.suffix != ".pyc")
    paths.update(repo / name for name in ("pyproject.toml", "uv.lock",
                 "benchmark-vabench-release-v4/EXPERIMENT_POLICY.json",
                 "benchmark-vabench-release-v4/operations/tri_form_derivation_prep/export_tri_form_runtime.py"))
    for path in paths:
        _no_symlinks(path)
    return {path.relative_to(repo).as_posix(): file_sha256(path) for path in sorted(paths)}


class BatchRun:
    """Exclusive local-process scheduler lease plus immutable per-cell receipts.

    Only use on local POSIX filesystems with flock/hard-link/fsync support.
    The lock file is retained: unlinking it could allow two different locks.
    """

    def __init__(self, root: Path, manifest: dict, cell_ids: list[str], *, resume: bool):
        if (not cell_ids or len(set(cell_ids)) != len(cell_ids)
                or any(not isinstance(key, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", key)
                       for key in cell_ids)):
            raise ValueError("batch requires unique safe cell identities")
        self.root = root.absolute()
        self.directory = self.root / ".batch"
        self.request = {"schema_version": "vaevas-batch-v1", "manifest": manifest,
                        "cell_ids": cell_ids}
        self.request_sha256 = _digest(self.request)
        self.resume = resume
        self._lock = None

    def __enter__(self):
        _no_symlinks(self.root)
        if self.resume and not (self.directory / "manifest.json").is_file():
            raise ValueError("resume requires an existing frozen batch manifest")
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        lock_path = self.root / ".batch.lock"
        _no_symlinks(lock_path)
        self._lock = os.open(lock_path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        try:
            fcntl.flock(self._lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            _no_symlinks(self.directory)
            if self.resume:
                _no_symlinks(self.directory / "manifest.json")
                if json.loads((self.directory / "manifest.json").read_text()) != self.request:
                    raise ValueError("frozen batch manifest/source/config differs; resume refused")
                allowed = {*self.request["cell_ids"], ".batch", ".batch.lock", "SUMMARY.json"}
                if any(path.name not in allowed for path in self.root.iterdir()):
                    raise ValueError("batch contains unrostered runtime activity")
            else:
                if any(path.name != ".batch.lock" for path in self.root.iterdir()):
                    raise ValueError("new batch requires a fresh output; use --resume for a frozen batch")
                self.directory.mkdir(mode=0o700)
                _atomic_once(self.directory / "manifest.json", self.request)
            return self
        except BaseException:
            self.__exit__(None, None, None)
            raise

    def __exit__(self, *_):
        if self._lock is not None:
            os.close(self._lock)
            self._lock = None

    def _path(self, cell_id: str, runtime: Path) -> Path:
        if self._lock is None:
            raise RuntimeError("batch operation requires the scheduler lease")
        if cell_id not in self.request["cell_ids"]:
            raise ValueError("cell is outside the frozen batch roster")
        _no_symlinks(runtime)
        relative = runtime.absolute().relative_to(self.root)
        if not relative.parts or relative.parts[0].startswith("."):
            raise ValueError("runtime must be separate from the batch journal")
        path = self.directory / f"cell-{cell_id}.json"
        _no_symlinks(path)
        return path

    def read(self, cell_id: str, runtime: Path) -> dict | None:
        path = self._path(cell_id, runtime)
        if not path.exists():
            return None
        receipt = json.loads(path.read_text())
        if (receipt.get("schema_version") != "vaevas-batch-cell-v1"
                or receipt.get("batch_sha256") != self.request_sha256
                or receipt.get("cell_id") != cell_id
                or receipt.get("runtime") != runtime.absolute().relative_to(self.root).as_posix()
                or receipt.get("row_sha256") != _digest(receipt["row"])
                or receipt.get("files") != _tree(runtime)):
            raise ValueError("batch terminal evidence changed or receipt binding is invalid")
        return receipt["row"]

    def record(self, cell_id: str, row: dict, runtime: Path) -> None:
        path = self._path(cell_id, runtime)
        _atomic_once(path, {"schema_version": "vaevas-batch-cell-v1",
                           "batch_sha256": self.request_sha256, "cell_id": cell_id,
                           "runtime": runtime.absolute().relative_to(self.root).as_posix(),
                           "row": row, "row_sha256": _digest(row), "files": _tree(runtime)})

    def snapshot(self, rows: list[dict]) -> Path:
        if self._lock is None:
            raise RuntimeError("batch operation requires the scheduler lease")
        if [row.get("cell_id") for row in rows] != self.request["cell_ids"]:
            raise ValueError("batch index must retain the complete ordered denominator")
        index = len(list(self.directory.glob("index-*.json")))
        path = self.directory / f"index-{index:06d}.json"
        _atomic_once(path, {"schema_version": "vaevas-batch-index-v1",
                           "batch_sha256": self.request_sha256, "rows": rows})
        return path
