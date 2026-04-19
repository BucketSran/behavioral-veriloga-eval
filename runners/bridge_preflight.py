#!/usr/bin/env python3
from __future__ import annotations

import os
import re
import socket
import subprocess
import sys
from pathlib import Path


def add_issue(preflight: dict, code: str, message: str) -> None:
    preflight.setdefault("issue_codes", []).append(code)
    preflight.setdefault("issues", []).append(message)


def add_note(preflight: dict, code: str, message: str) -> None:
    preflight.setdefault("note_codes", []).append(code)
    preflight.setdefault("notes", []).append(message)


def load_env_pairs(env_path: Path) -> dict[str, str]:
    pairs: dict[str, str] = {}
    if not env_path.is_file():
        return pairs
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        pairs[key] = value
    return pairs


def resolve_cadence_cshrc(bridge_repo: Path, override: str | None = None) -> str:
    override = (override or "").strip()
    if override:
        return override
    env_val = os.environ.get("VB_CADENCE_CSHRC", "").strip()
    if env_val:
        return env_val
    bridge_env = load_env_pairs(bridge_repo / ".env")
    return bridge_env.get("VB_CADENCE_CSHRC", "").strip()


def bridge_cli_path(bridge_repo: Path) -> Path:
    return bridge_repo / ".venv" / "bin" / "virtuoso-bridge"


def resolve_local_port(bridge_repo: Path) -> int:
    env_val = os.environ.get("VB_LOCAL_PORT", "").strip()
    if env_val.isdigit():
        return int(env_val)
    bridge_env = load_env_pairs(bridge_repo / ".env")
    bridge_port = bridge_env.get("VB_LOCAL_PORT", "").strip()
    if bridge_port.isdigit():
        return int(bridge_port)
    return 65082


def local_port_listening(port: int) -> bool:
    for host in ("127.0.0.1", "::1"):
        family = socket.AF_INET6 if ":" in host else socket.AF_INET
        try:
            with socket.socket(family, socket.SOCK_STREAM) as sock:
                sock.settimeout(0.5)
                if sock.connect_ex((host, port)) == 0:
                    return True
        except OSError:
            continue
    return False


def local_port_listener_pids(port: int) -> list[int]:
    try:
        proc = subprocess.run(
            ["lsof", "-tiTCP:%d" % port, "-sTCP:LISTEN", "-n", "-P"],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    pids: list[int] = []
    for raw in (proc.stdout or "").splitlines():
        line = raw.strip()
        if line.isdigit():
            pids.append(int(line))
    return pids


def parse_bridge_status(output: str) -> dict:
    tunnel_running = None
    daemon_ok = None
    spectre_ok = None
    load_path = None
    spectre_path = None
    spectre_version = None

    for line in output.splitlines():
        stripped = line.strip()
        if stripped.startswith("[tunnel] "):
            tunnel_running = "NOT running" not in stripped
        elif stripped.startswith("[daemon] "):
            if "OK" in stripped:
                daemon_ok = True
            elif "NO RESPONSE" in stripped or "cannot check" in stripped or "error:" in stripped:
                daemon_ok = False
        elif stripped.startswith("[spectre] "):
            if "OK" in stripped:
                spectre_ok = True
            elif "NOT FOUND" in stripped or "error:" in stripped:
                spectre_ok = False
        elif stripped.startswith("load(\"") and load_path is None:
            match = re.search(r'load\("([^"]+)"\)', stripped)
            if match:
                load_path = match.group(1)
        elif stripped.startswith("path") and ":" in stripped:
            _, value = stripped.split(":", 1)
            spectre_path = value.strip() or spectre_path
        elif stripped.startswith("version") and ":" in stripped:
            _, value = stripped.split(":", 1)
            spectre_version = value.strip() or spectre_version

    return {
        "tunnel_running": tunnel_running,
        "daemon_ok": daemon_ok,
        "spectre_ok": spectre_ok,
        "load_path": load_path,
        "spectre_path": spectre_path,
        "spectre_version": spectre_version,
    }


def bridge_preflight(
    bridge_repo: Path,
    *,
    cadence_cshrc: str | None = None,
    require_daemon: bool = False,
    timeout_s: int = 20,
) -> dict:
    bridge_repo = bridge_repo.resolve()
    cli_path = bridge_cli_path(bridge_repo)
    resolved_cshrc = resolve_cadence_cshrc(bridge_repo, cadence_cshrc)

    preflight = {
        "status": "ok",
        "bridge_repo": str(bridge_repo),
        "bridge_cli": str(cli_path),
        "cadence_cshrc": resolved_cshrc,
        "require_daemon": require_daemon,
        "issue_codes": [],
        "issues": [],
        "note_codes": [],
        "notes": [],
        "remediation": [],
    }

    if not bridge_repo.exists():
        preflight["status"] = "blocked"
        add_issue(preflight, "bridge_repo_missing", f"bridge repo not found: {bridge_repo}")
        preflight["reason"] = preflight["issues"][0]
        return preflight

    if not cli_path.exists():
        preflight["status"] = "blocked"
        add_issue(preflight, "bridge_cli_missing", f"bridge CLI not found: {cli_path}")
        preflight["reason"] = preflight["issues"][0]
        return preflight

    env = os.environ.copy()
    if resolved_cshrc:
        env["VB_CADENCE_CSHRC"] = resolved_cshrc
    local_port = resolve_local_port(bridge_repo)
    listener_pids = local_port_listener_pids(local_port)
    manual_tunnel_up = bool(listener_pids) or local_port_listening(local_port)

    try:
        proc = subprocess.run(
            [str(cli_path), "status"],
            cwd=str(bridge_repo),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        preflight["status"] = "blocked"
        add_issue(preflight, "bridge_status_timeout", f"bridge status timed out after {timeout_s}s")
        preflight["reason"] = preflight["issues"][0]
        preflight["status_output_tail"] = ((exc.stdout or "") + "\n" + (exc.stderr or "")).strip()[-4000:]
        preflight["remediation"].append(
            f"cd {bridge_repo} && ./.venv/bin/virtuoso-bridge status"
        )
        return preflight
    output = ((proc.stdout or "") + "\n" + (proc.stderr or "")).strip()
    parsed = parse_bridge_status(output)
    if parsed["tunnel_running"] is False and manual_tunnel_up:
        parsed["tunnel_running"] = True
        add_note(
            preflight,
            "manual_tunnel_detected",
            f"manual SSH tunnel detected on local port {local_port} even though bridge status reported NOT running"
        )
        if listener_pids:
            add_note(
                preflight,
                "manual_tunnel_listener_pids",
                f"listener_pids={','.join(str(pid) for pid in listener_pids)}"
            )
    preflight.update(parsed)
    preflight["status_output_tail"] = output[-4000:]
    preflight["status_exit_code"] = proc.returncode

    if parsed["tunnel_running"] is False:
        add_issue(
            preflight,
            "tunnel_not_running",
            "virtuoso-bridge tunnel is not running"
        )
        preflight["remediation"].append(
            f"cd {bridge_repo.parents[1] / 'vaEvas' / 'behavioral-veriloga-eval'} && ./scripts/start_bridge_tunnel.sh"
        )
        preflight["remediation"].append(
            f"cd {bridge_repo} && ./.venv/bin/virtuoso-bridge start"
        )

    if parsed["spectre_ok"] is False:
        if resolved_cshrc:
            add_issue(
                preflight,
                "spectre_unavailable",
                f"spectre is still unavailable after sourcing {resolved_cshrc}"
            )
        else:
            add_issue(
                preflight,
                "spectre_unavailable",
                "spectre is unavailable and VB_CADENCE_CSHRC is not configured"
            )
            preflight["remediation"].append(
                "set VB_CADENCE_CSHRC to the remote Cadence cshrc that exposes spectre"
            )

    if parsed["daemon_ok"] is False:
        message = "Virtuoso daemon is not connected to the bridge"
        if require_daemon:
            add_issue(preflight, "daemon_disconnected", message)
        else:
            add_note(preflight, "daemon_disconnected", message)
        if parsed["load_path"]:
            preflight["remediation"].append(
                f'in remote Virtuoso CIW run: load("{parsed["load_path"]}")'
            )
            preflight["remediation"].append(
                f'add load("{parsed["load_path"]}") to remote ~/.cdsinit for auto-load on startup'
            )

    if not resolved_cshrc:
        add_note(
            preflight,
            "cadence_cshrc_unresolved",
            "VB_CADENCE_CSHRC was not resolved from CLI/env/bridge .env"
        )

    if preflight["issues"]:
        preflight["status"] = "blocked"
        preflight["reason"] = preflight["issues"][0]

    return preflight


def _format_summary(preflight: dict) -> str:
    lines = [
        f"status={preflight.get('status')}",
        f"bridge_repo={preflight.get('bridge_repo')}",
        f"tunnel_running={preflight.get('tunnel_running')}",
        f"daemon_ok={preflight.get('daemon_ok')}",
        f"spectre_ok={preflight.get('spectre_ok')}",
    ]
    issues = preflight.get("issues") or []
    notes = preflight.get("notes") or []
    remediation = preflight.get("remediation") or []
    if issues:
        lines.append("issues:")
        lines.extend(f"  - {item}" for item in issues)
    if notes:
        lines.append("notes:")
        lines.extend(f"  - {item}" for item in notes)
    if remediation:
        lines.append("remediation:")
        lines.extend(f"  - {item}" for item in remediation)
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    import argparse
    import json

    ap = argparse.ArgumentParser(description="Check bridge/tunnel/Spectre readiness for dual validation.")
    ap.add_argument(
        "--bridge-repo",
        default=str((Path(__file__).resolve().parents[3] / "iccad" / "virtuoso-bridge-lite")),
        help="Path to virtuoso-bridge-lite repository.",
    )
    ap.add_argument(
        "--cadence-cshrc",
        default="",
        help="Remote Cadence cshrc path used to expose spectre on PATH.",
    )
    ap.add_argument(
        "--require-daemon",
        action="store_true",
        help="Treat a disconnected Virtuoso daemon as a hard blocker.",
    )
    ap.add_argument(
        "--json",
        action="store_true",
        help="Emit the preflight result as JSON.",
    )
    args = ap.parse_args(argv)

    preflight = bridge_preflight(
        Path(args.bridge_repo),
        cadence_cshrc=args.cadence_cshrc or None,
        require_daemon=args.require_daemon,
    )
    if args.json:
        print(json.dumps(preflight, indent=2))
    else:
        print(_format_summary(preflight))
    return 0 if preflight.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
