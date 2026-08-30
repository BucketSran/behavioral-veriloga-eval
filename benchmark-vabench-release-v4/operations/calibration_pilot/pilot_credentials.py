"""Read the local two-provider template as data, never as shell instructions.

This opt-in helper neither calls a provider nor changes the legacy raw-key CLI.
The caller selects a provider/platform separately and keeps the returned secret
out of prompts, metadata, logs and subprocess environments.
"""

import os
from pathlib import Path
import re
import stat


KEY_NAMES = frozenset({"GLM_API_KEY", "DEEPSEEK_API_KEY"})
MAX_FILE_BYTES = 16 * 1024


def _read_private_file(path: Path) -> str:
    try:
        flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC
        fd = os.open(path, flags)
        with os.fdopen(fd, "rb") as source:
            identity = os.fstat(source.fileno())
            if not stat.S_ISREG(identity.st_mode):
                raise ValueError("invalid pilot credential file")
            if identity.st_uid != os.getuid() or identity.st_mode & 0o077:
                raise ValueError("pilot credential file requires owner-only access")
            raw = source.read(MAX_FILE_BYTES + 1)
        if len(raw) > MAX_FILE_BYTES:
            raise ValueError("invalid pilot credential file")
        return raw.decode("utf-8")
    except (OSError, UnicodeError):
        raise ValueError("invalid pilot credential file") from None


def load_pilot_key(path: Path, key_name: str) -> str:
    """Load one quoted literal from the shared local pilot credential template."""
    if key_name not in KEY_NAMES:
        raise ValueError("unsupported pilot credential field")
    selected = None
    seen = set()
    for line in _read_private_file(path).splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.fullmatch(r'([A-Z_]+)\s*=\s*([\"\'])([A-Za-z0-9._~+/=-]*)\2', line)
        if not match or match[1] not in KEY_NAMES or match[1] in seen:
            raise ValueError("invalid pilot credential template")
        seen.add(match[1])
        if match[1] == key_name:
            selected = match[3]
    if not selected:
        raise ValueError("selected pilot credential is missing or empty")
    return selected
