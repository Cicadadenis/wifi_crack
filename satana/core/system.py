from __future__ import annotations

import os
import socket
import subprocess
import time
from pathlib import Path
from typing import Any

try:
    import psutil
except ImportError:  # pragma: no cover - optional runtime fallback
    psutil = None


START_TIME = time.time()


def parse_proc_memory() -> dict[str, Any]:
    meminfo: dict[str, int] = {}
    try:
        for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
            key, value = line.split(":", 1)
            meminfo[key] = int(value.strip().split()[0]) * 1024
    except (OSError, ValueError):
        return {"total": 0, "used": 0, "percent": 0}
    total = meminfo.get("MemTotal", 0)
    available = meminfo.get("MemAvailable", 0)
    used = max(total - available, 0)
    percent = round((used / total) * 100, 1) if total else 0
    return {"total": total, "used": used, "percent": percent}


def system_metrics() -> dict[str, Any]:
    if psutil:
        memory = psutil.virtual_memory()
        return {
            "cpu": {"percent": psutil.cpu_percent(interval=0.1)},
            "memory": {"total": memory.total, "used": memory.used, "percent": memory.percent},
        }
    return {
        "cpu": {"percent": round(os.getloadavg()[0], 2) if hasattr(os, "getloadavg") else 0},
        "memory": parse_proc_memory(),
    }


def human_uptime() -> str:
    seconds = int(time.time() - START_TIME)
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def command_output(command: list[str]) -> str:
    try:
        return subprocess.check_output(command, text=True, stderr=subprocess.DEVNULL, timeout=2)
    except (OSError, subprocess.SubprocessError):
        return ""


def wireless_interfaces() -> set[str]:
    names: set[str] = set()
    output = command_output(["iw", "dev"])
    for line in output.splitlines():
        line = line.strip()
        if line.startswith("Interface "):
            names.add(line.split(maxsplit=1)[1])
    return names


def interface_ipv4(name: str) -> str:
    if psutil:
        for address in psutil.net_if_addrs().get(name, []):
            if getattr(address, "family", None) == socket.AF_INET:
                return address.address
    output = command_output(["ip", "-4", "-o", "addr", "show", "dev", name])
    parts = output.split()
    if "inet" in parts:
        return parts[parts.index("inet") + 1].split("/", 1)[0]
    return "-"


def collect_interfaces() -> list[dict[str, Any]]:
    wireless = wireless_interfaces()
    interfaces = []
    for net_path in sorted(Path("/sys/class/net").glob("*")):
        name = net_path.name
        operstate = (net_path / "operstate").read_text(encoding="utf-8", errors="ignore").strip()
        mode = "wireless" if name in wireless or (net_path / "wireless").exists() else "ethernet"
        mac = (net_path / "address").read_text(encoding="utf-8", errors="ignore").strip()
        interfaces.append(
            {
                "name": name,
                "mode": mode,
                "state": operstate or "unknown",
                "mac": mac,
                "ipv4": interface_ipv4(name),
                "up": operstate == "up",
            }
        )
    return interfaces
