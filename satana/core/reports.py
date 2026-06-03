from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from satana.core.paths import LEGACY_REPORTS_DIR, REPORTS_DIR


def migrate_legacy_reports() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    if not LEGACY_REPORTS_DIR.exists():
        return
    for path in LEGACY_REPORTS_DIR.iterdir():
        if path.is_file() and not path.name.startswith("."):
            target = REPORTS_DIR / path.name
            if not target.exists():
                shutil.copy2(path, target)


def safe_report_path(name: str) -> Path:
    report_path = (REPORTS_DIR / name).resolve()
    root = REPORTS_DIR.resolve()
    if root not in report_path.parents or not report_path.is_file():
        raise FileNotFoundError(name)
    return report_path


def collect_reports(query: str = "") -> list[dict[str, Any]]:
    migrate_legacy_reports()
    reports: list[dict[str, Any]] = []
    query_lower = query.lower().strip()
    for path in sorted(REPORTS_DIR.iterdir(), key=lambda item: item.stat().st_mtime, reverse=True):
        if not path.is_file() or path.name.startswith("."):
            continue
        if query_lower and query_lower not in path.name.lower():
            try:
                if query_lower not in path.read_text(encoding="utf-8", errors="ignore").lower():
                    continue
            except OSError:
                continue
        reports.append(
            {
                "name": path.name,
                "size": path.stat().st_size,
                "modified": datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds"),
            }
        )
    return reports

