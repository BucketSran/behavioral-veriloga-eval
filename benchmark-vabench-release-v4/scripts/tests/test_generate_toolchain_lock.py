from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "generate_toolchain_lock.py"
SPEC = importlib.util.spec_from_file_location("generate_toolchain_lock", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def _identity(**overrides: object) -> dict[str, object]:
    identity: dict[str, object] = {
        "git_commit": module.EXPECTED_EVAS_COMMIT,
        "git_describe": module.EXPECTED_EVAS_TAG,
        "runtime_metadata_version": module.EXPECTED_EVAS_VERSION,
        "actual_engine": "evas-rust",
        "rust_core_abi": module.EXPECTED_RUST_ABI,
        "dirty": False,
        "release_base_commit": module.EXPECTED_EVAS_COMMIT,
        "release_base_is_ancestor": True,
        "patch_commit_count": 0,
        "release_relation": "exact_release_tag",
    }
    identity.update(overrides)
    return identity


def test_verify_evas_accepts_exact_release() -> None:
    module.verify_evas(_identity())


def test_verify_evas_accepts_clean_patched_descendant() -> None:
    module.verify_evas(
        _identity(
            git_commit="a" * 40,
            git_describe="v0.8.1-1-gaaaaaaa",
            patch_commit_count=1,
            release_relation="patched_release_descendant",
        )
    )


@pytest.mark.parametrize(
    "overrides",
    [
        {"dirty": True},
        {"release_base_is_ancestor": False},
        {
            "git_commit": "a" * 40,
            "git_describe": "aaaaaaaa",
            "patch_commit_count": 1,
            "release_relation": "patched_release_descendant",
        },
        {
            "git_commit": "a" * 40,
            "git_describe": "v0.8.1-1-gaaaaaaa",
            "patch_commit_count": 0,
            "release_relation": "patched_release_descendant",
        },
    ],
)
def test_verify_evas_rejects_unverifiable_identity(overrides: dict[str, object]) -> None:
    with pytest.raises(RuntimeError, match="EVAS identity mismatch"):
        module.verify_evas(_identity(**overrides))
