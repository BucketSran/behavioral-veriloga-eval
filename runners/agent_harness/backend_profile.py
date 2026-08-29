"""Content identity for validated agent-backend profile documents."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import hashlib
import json
import math
from typing import Any


def backend_profile_sha256(profile: Mapping[str, Any]) -> str:
    """Hash a schema-validated backend profile using canonical JSON ordering."""
    if not isinstance(profile, Mapping):
        raise TypeError("backend profile must be a JSON object")
    _require_canonical_json(profile)
    canonical = json.dumps(
        profile,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _require_canonical_json(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("backend profile JSON object keys must be strings")
            _require_canonical_json(item)
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for item in value:
            _require_canonical_json(item)
        return
    if value is None or isinstance(value, (str, int, bool)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("backend profile JSON numbers must be finite")
        return
    raise TypeError(
        f"backend profile contains a non-JSON value: {type(value).__name__}"
    )
