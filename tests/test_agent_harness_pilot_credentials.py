"""Local-only tests: fixtures are not provider credentials and no API is called."""

import importlib
import os
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "benchmark-vabench-release-v4/operations/calibration_pilot"))


def test_reads_only_selected_literal_key_without_changing_environment(tmp_path, monkeypatch):
    credentials = importlib.import_module("pilot_credentials")
    key_file = tmp_path / "provider-keys.env"
    key_file.write_text(
        '# Local credentials\nDEEPSEEK_API_KEY="unused.fixture"\n'
        'GLM_API_KEY="selected.fixture"\n', encoding="utf-8",
    )
    key_file.chmod(0o600)
    monkeypatch.setenv("GLM_API_KEY", "ambient.fixture")
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    assert credentials.load_pilot_key(key_file, "GLM_API_KEY") == "selected.fixture"

    assert os.environ["GLM_API_KEY"] == "ambient.fixture"
    assert "DEEPSEEK_API_KEY" not in os.environ


@pytest.mark.parametrize("body", [
    'GLM_API_KEY=""\n',
    'DEEPSEEK_API_KEY="other.fixture"\n',
    'GLM_API_KEY="first.fixture"\nGLM_API_KEY="second.fixture"\n',
    'GLM_API_KEY="$(touch should-not-exist)"\n',
    'GLM_API_KEY="`touch should-not-exist`"\n',
    'GLM_API_KEY="${DEEPSEEK_API_KEY}"\n',
    'GLM_API_KEY="secret.fixture"; echo secret.fixture\n',
    'GLM_API_KEY="secret.fixture\ncontinued"\n',
    'export GLM_API_KEY="secret.fixture"\n',
    'GLM_API_KEY=secret.fixture\n',
    'GLM_API_KEY="secret.fixture"\nUNKNOWN_KEY="other.fixture"\n',
])
def test_rejects_ambiguous_or_executable_template_without_echoing_values(tmp_path, body):
    credentials = importlib.import_module("pilot_credentials")
    key_file = tmp_path / "provider-keys.env"
    key_file.write_text(body, encoding="utf-8")
    key_file.chmod(0o600)
    with pytest.raises(ValueError) as error:
        credentials.load_pilot_key(key_file, "GLM_API_KEY")
    assert ".fixture" not in str(error.value)
    assert str(key_file) not in str(error.value)
    assert sorted(p.name for p in tmp_path.iterdir()) == ["provider-keys.env"]


def test_permits_empty_unused_key_and_single_quotes(tmp_path):
    credentials = importlib.import_module("pilot_credentials")
    key_file = tmp_path / "provider-keys.env"
    key_file.write_text("DEEPSEEK_API_KEY=''\n  GLM_API_KEY = 'fixture.key-01'\n")
    key_file.chmod(0o600)
    assert credentials.load_pilot_key(key_file, "GLM_API_KEY") == "fixture.key-01"


@pytest.mark.parametrize("mode", [0o644, 0o640, 0o660, 0o604])
def test_rejects_group_or_other_file_access(tmp_path, mode):
    credentials = importlib.import_module("pilot_credentials")
    key_file = tmp_path / "provider-keys.env"
    key_file.write_text('GLM_API_KEY="secret.fixture"\n')
    key_file.chmod(mode)
    with pytest.raises(ValueError, match="owner-only"):
        credentials.load_pilot_key(key_file, "GLM_API_KEY")


def test_rejects_symlinks_and_nonregular_files_without_blocking(tmp_path):
    credentials = importlib.import_module("pilot_credentials")
    key_file = tmp_path / "provider-keys.env"
    key_file.write_text('GLM_API_KEY="secret.fixture"\n')
    key_file.chmod(0o600)
    link = tmp_path / "link.env"
    link.symlink_to(key_file)
    pipe = tmp_path / "pipe.env"
    os.mkfifo(pipe, 0o600)
    for path in (link, pipe, tmp_path, tmp_path / "missing.env"):
        with pytest.raises(ValueError) as error:
            credentials.load_pilot_key(path, "GLM_API_KEY")
        assert str(path) not in str(error.value)


@pytest.mark.parametrize("body", [b'GLM_API_KEY="\xff"', b"#" * (16 * 1024 + 1)],
                         ids=["invalid-utf8", "oversized"])
def test_rejects_non_utf8_or_oversized_file_without_secret_in_exception(tmp_path, body):
    credentials = importlib.import_module("pilot_credentials")
    key_file = tmp_path / "provider-keys.env"
    key_file.write_bytes(body)
    key_file.chmod(0o600)
    with pytest.raises(ValueError, match="invalid pilot credential file"):
        credentials.load_pilot_key(key_file, "GLM_API_KEY")


def test_unknown_field_rejected_before_file_access(tmp_path):
    credentials = importlib.import_module("pilot_credentials")
    with pytest.raises(ValueError, match="unsupported pilot credential field"):
        credentials.load_pilot_key(tmp_path / "missing.env", "OTHER_SECRET")
