from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

from satana.core.paths import BASE_DIR, REPORTS_DIR
from satana.core.system import collect_interfaces, command_output


def interface_iw_type(name: str) -> str:
    output = command_output(["iw", name, "info"])
    match = re.search(r"type\s+(\S+)", output)
    return match.group(1).lower() if match else "unknown"


def default_wireless_interface() -> str | None:
    interfaces = collect_interfaces()
    for item in interfaces:
        if item.get("mode") == "wireless" and item.get("name") != "lo":
            return item["name"]
    for item in interfaces:
        if item.get("name") != "lo":
            return item["name"]
    return None


def run_command(command: list[str], timeout: int = 120) -> tuple[int, str, str]:
    try:
        completed = subprocess.run(
            command,
            cwd=BASE_DIR,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        return completed.returncode, completed.stdout, completed.stderr
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = (exc.stderr or "") + f"\nCommand timed out after {timeout} seconds\n"
        return 124, stdout, stderr


def set_monitor_mode(interface: str) -> tuple[int, str, str]:
    ip_link_down, _, stderr_down = run_command(["ip", "link", "set", interface, "down"], timeout=10)
    code, out_iw, err_iw = run_command(["iw", interface, "set", "type", "monitor"], timeout=15)
    _, out_mon, err_mon = run_command(["iw", interface, "set", "monitor", "control"], timeout=15)
    run_command(["ip", "link", "set", interface, "up"], timeout=10)
    mode = interface_iw_type(interface)
    payload = {
        "interface": interface,
        "mode": mode,
        "ip_link_down_exit": ip_link_down,
        "messages": (out_iw + out_mon).strip(),
    }
    combined_stderr = (stderr_down + err_iw + err_mon).strip()
    if mode == "monitor":
        return 0, json.dumps(payload, indent=2, ensure_ascii=False) + "\n", combined_stderr
    return 1 if code != 0 else 1, json.dumps(payload, indent=2, ensure_ascii=False) + "\n", combined_stderr


def set_managed_mode(interface: str) -> tuple[int, str, str]:
    run_command(["ip", "link", "set", interface, "down"], timeout=10)
    code, out_iw, err_iw = run_command(["iw", interface, "set", "type", "managed"], timeout=15)
    run_command(["ip", "link", "set", interface, "up"], timeout=10)
    run_command(["airmon-ng", "stop", interface], timeout=30)
    mode = interface_iw_type(interface)
    payload = {"interface": interface, "mode": mode, "messages": out_iw.strip()}
    combined_stderr = err_iw.strip()
    if mode == "managed":
        return 0, json.dumps(payload, indent=2, ensure_ascii=False) + "\n", combined_stderr
    return code or 1, json.dumps(payload, indent=2, ensure_ascii=False) + "\n", combined_stderr


def _parse_airodump_csv(prefix: Path) -> list[dict[str, str]]:
    csv_path = Path(f"{prefix}-01.csv")
    if not csv_path.exists():
        return []
    lines = csv_path.read_text(encoding="utf-8", errors="replace").splitlines()
    station_idx = next((i for i, line in enumerate(lines) if line.startswith("Station") or line.startswith("BSSID")), len(lines))
    networks: list[dict[str, str]] = []
    for line in lines[1:station_idx]:
        if not line.strip() or line.startswith("BSSID"):
            continue
        parts = [part.strip() for part in line.split(",")]
        if len(parts) < 14:
            continue
        networks.append(
            {
                "bssid": parts[0],
                "channel": parts[3],
                "privacy": parts[5],
                "power": parts[8],
                "essid": parts[13] if len(parts) > 13 else "",
            }
        )
    return networks


def scan_targets(interface: str, seconds: int = 30, cipher: str = "") -> tuple[int, str, str]:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    prefix = REPORTS_DIR / f"scan_{interface}_{cipher or 'all'}"
    for old in prefix.parent.glob(f"{prefix.name}*"):
        old.unlink(missing_ok=True)

    cipher_args: list[str] = []
    if cipher:
        cipher_args = ["--encrypt", cipher.upper()]

    command = [
        "timeout",
        str(max(5, min(seconds, 300))),
        "airodump-ng",
        "-w",
        str(prefix),
        *cipher_args,
        interface,
        "--band",
        "abg",
    ]
    code, stdout, stderr = run_command(command, timeout=seconds + 15)
    networks = _parse_airodump_csv(prefix)
    payload = {
        "interface": interface,
        "seconds": seconds,
        "cipher": cipher or None,
        "networks_found": len(networks),
        "networks": networks[:50],
        "csv_prefix": str(prefix),
    }
    status = 0 if networks else (code if code else 1)
    return status, json.dumps(payload, indent=2, ensure_ascii=False) + "\n", stdout + stderr
