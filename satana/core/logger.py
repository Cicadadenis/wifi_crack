from __future__ import annotations

from datetime import datetime
from pathlib import Path

from satana.core.paths import BASE_DIR, WEB_LOGS_DIR


def resolve_log_paths(config: dict) -> list[Path]:
    paths = []
    for raw_path in config.get("project", {}).get("logs", []):
        path = Path(raw_path)
        paths.append(path if path.is_absolute() else BASE_DIR / path)
    return paths


def read_tail(path: Path, lines: int = 120) -> list[str]:
    if not path.exists() or not path.is_file():
        return []
    try:
        with path.open("r", encoding="utf-8", errors="replace") as fh:
            return fh.readlines()[-lines:]
    except OSError:
        return []


def collect_logs(config: dict, lines: int = 120) -> list[str]:
    output: list[str] = []
    for path in resolve_log_paths(config):
        for line in read_tail(path, lines):
            output.append(f"{path.name}: {line.rstrip()}")
    return output[-lines:]


def write_web_startup_log() -> Path:
    log_file = WEB_LOGS_DIR / "satana-web.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with log_file.open("a", encoding="utf-8") as fh:
        fh.write(f"{datetime.now().isoformat(timespec='seconds')} SATANA Web UI started\n")
    return log_file

