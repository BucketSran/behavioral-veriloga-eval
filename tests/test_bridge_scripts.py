from __future__ import annotations

import json
import os
import socket
import stat
import subprocess
from contextlib import closing
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"


def find_free_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("127.0.0.1", 0))
        sock.listen(1)
        return int(sock.getsockname()[1])


def make_fake_bridge_repo(tmp_path: Path, local_port: int, status_output: str) -> Path:
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
    (repo / ".env").write_text(f"VB_LOCAL_PORT={local_port}\n", encoding="utf-8")
    return repo


def run_script(script_name: str, *args: str, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(SCRIPTS_DIR / script_name), *args],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_check_bridge_ready_supports_bridge_repo_override(tmp_path: Path, monkeypatch) -> None:
    port = find_free_port()
    repo = make_fake_bridge_repo(
        tmp_path,
        port,
        "\n".join(
            [
                "Virtuoso Bridge v0.1.0",
                "",
                "[tunnel] running",
                f"  local port  : {port}",
                "",
                "[daemon] OK — connected to Virtuoso CIW",
                "",
                "[spectre] OK",
            ]
        ),
    )
    env = {**os.environ, "BRIDGE_REPO": str(repo)}

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind(("127.0.0.1", port))
        server.listen(1)
        result = run_script("check_bridge_ready.sh", "--json", env=env)

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "ok"
    assert payload["bridge_repo"] == str(repo)
    assert payload["tunnel_running"] is True
    assert payload["spectre_ok"] is True


def test_start_bridge_tunnel_uses_existing_listener_without_ssh(tmp_path: Path) -> None:
    port = find_free_port()
    repo = make_fake_bridge_repo(
        tmp_path,
        port,
        "\n".join(
            [
                "[tunnel] running",
                f"  local port  : {port}",
                "[daemon] OK — connected to Virtuoso CIW",
                "[spectre] OK",
            ]
        ),
    )
    env = {**os.environ, "BRIDGE_REPO": str(repo)}

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind(("127.0.0.1", port))
        server.listen(1)
        result = run_script("start_bridge_tunnel.sh", env=env)

    assert result.returncode == 0, result.stderr
    assert f"bridge tunnel already listening on localhost:{port}" in result.stdout


def test_run_with_bridge_requires_command() -> None:
    result = subprocess.run(
        [str(SCRIPTS_DIR / "run_with_bridge.sh")],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert "usage: ./scripts/run_with_bridge.sh <command> [args...]" in result.stderr
