from __future__ import annotations

import os
from pathlib import Path


BASE_DIR = Path(os.environ.get("SATANA_HOME", Path(__file__).resolve().parents[2])).resolve()
SATANA_DIR = BASE_DIR / "satana"
CONFIG_DIR = SATANA_DIR / "config"
LOGS_DIR = SATANA_DIR / "logs"
WEB_LOGS_DIR = LOGS_DIR / "web"
TASK_LOGS_DIR = LOGS_DIR / "tasks"
REPORTS_DIR = SATANA_DIR / "reports"
PLUGINS_DIR = SATANA_DIR / "plugins"
DATABASE_DIR = SATANA_DIR / "database"
TASKS_DB_PATH = DATABASE_DIR / "tasks.json"
WEB_DIR = SATANA_DIR / "web"

LEGACY_WEB_DIR = BASE_DIR / "web"
LEGACY_CONFIG_PATH = LEGACY_WEB_DIR / "config" / "config.json"
LEGACY_REPORTS_DIR = LEGACY_WEB_DIR / "reports"
LEGACY_WEB_LOGS_DIR = LEGACY_WEB_DIR / "logs"
LEGACY_PLUGINS_DIR = BASE_DIR / "plugins"


def ensure_directories() -> None:
    for path in (
        CONFIG_DIR,
        WEB_LOGS_DIR,
        TASK_LOGS_DIR,
        REPORTS_DIR,
        PLUGINS_DIR,
        DATABASE_DIR,
        WEB_DIR,
    ):
        path.mkdir(parents=True, exist_ok=True)
