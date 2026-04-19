from __future__ import annotations

import os
import stat
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runners"))

import bridge_preflight as bp  # noqa: E402


def make_fake_bridge_repo(tmp_path: Path, status_output: str) -> Path:
    repo = tmp_path / "virtuoso-bridge-lite"
    cli = repo / ".venv" / "bin" / "virtuoso-bridge"
    cli.parent.mkdir(parents=True, exist_ok=True)
    cli.write_text(
        "#!/usr/bin/env python3\n"
        "import sys\n"
        f"print({status_output!r})\n",
        encoding="utf-8",
    )
    cli.chmod(cli.stat().st_mode | stat.S_IXUSR)
    (repo / ".env").write_text("VB_LOCAL_PORT=65082\n", encoding="utf-8")
    return repo


def test_bridge_preflight_recognizes_manual_tunnel(monkeypatch, tmp_path: Path) -> None:
    repo = make_fake_bridge_repo(
        tmp_path,
        "\n".join(
            [
                "[tunnel] NOT running",
                "[daemon] cannot check (tunnel not running)",
                "[spectre] OK",
                '  Load in Virtuoso CIW:\n    load("/tmp/bridge/virtuoso_setup.il")',
            ]
        ),
    )
    monkeypatch.setattr(bp, "local_port_listening", lambda port: False)
    monkeypatch.setattr(bp, "local_port_listener_pids", lambda port: [4242])

    result = bp.bridge_preflight(repo)

    assert result["status"] == "ok"
    assert result["tunnel_running"] is True
    assert "manual_tunnel_detected" in result["note_codes"]
    assert "daemon_disconnected" in result["note_codes"]
    assert "tunnel_not_running" not in result["issue_codes"]


def test_bridge_preflight_blocks_when_tunnel_missing(monkeypatch, tmp_path: Path) -> None:
    repo = make_fake_bridge_repo(
        tmp_path,
        "\n".join(
            [
                "[tunnel] NOT running",
                "[daemon] cannot check (tunnel not running)",
                "[spectre] OK",
            ]
        ),
    )
    monkeypatch.setattr(bp, "local_port_listening", lambda port: False)
    monkeypatch.setattr(bp, "local_port_listener_pids", lambda port: [])

    result = bp.bridge_preflight(repo)

    assert result["status"] == "blocked"
    assert "tunnel_not_running" in result["issue_codes"]

