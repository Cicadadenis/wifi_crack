from __future__ import annotations

import json
import os
import secrets
import shutil
from pathlib import Path
from typing import Any

from werkzeug.security import generate_password_hash

from satana.core.paths import CONFIG_DIR, LEGACY_CONFIG_PATH, REPORTS_DIR, WEB_LOGS_DIR, ensure_directories


WEB_CONFIG_PATH = CONFIG_DIR / "web.json"

DEFAULT_WEB_CONFIG: dict[str, Any] = {
    "auth": {"username": "admin", "password_hash": ""},
    "server": {"host": "127.0.0.1", "port": 8080, "debug": False},
    "project": {
        "name": "SATANA",
        "cli_path": "satana.sh",
        "logs": [
            "satana/logs/web/satana-web.log",
            "satana-debug.log",
            "web/logs/satana-web.log",
        ],
    },
    "ui": {"theme": "dark", "refresh_interval": 5000},
    "secret_key": "",
}


def deep_merge(base: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in incoming.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def migrate_legacy_config() -> None:
    ensure_directories()
    if WEB_CONFIG_PATH.exists() or not LEGACY_CONFIG_PATH.exists():
        return
    shutil.copy2(LEGACY_CONFIG_PATH, WEB_CONFIG_PATH)


def normalize_config(config: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    changed = False
    logs = config.setdefault("project", {}).setdefault("logs", [])
    for log_path in DEFAULT_WEB_CONFIG["project"]["logs"]:
        if log_path not in logs:
            logs.append(log_path)
            changed = True
    if not config.get("secret_key"):
        config["secret_key"] = secrets.token_hex(32)
        changed = True
    if not config["auth"].get("password_hash"):
        password = os.environ.get("SATANA_WEB_PASSWORD", "admin")
        config["auth"]["password_hash"] = generate_password_hash(password)
        changed = True
    return config, changed


def load_web_config() -> dict[str, Any]:
    migrate_legacy_config()
    if WEB_CONFIG_PATH.exists():
        with WEB_CONFIG_PATH.open("r", encoding="utf-8") as fh:
            config = deep_merge(DEFAULT_WEB_CONFIG, json.load(fh))
    else:
        config = dict(DEFAULT_WEB_CONFIG)
    config, changed = normalize_config(config)
    if changed or not WEB_CONFIG_PATH.exists():
        save_web_config(config)
    WEB_LOGS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    return config


def save_web_config(config: dict[str, Any]) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    tmp_path = WEB_CONFIG_PATH.with_suffix(".json.tmp")
    with tmp_path.open("w", encoding="utf-8") as fh:
        json.dump(config, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    tmp_path.replace(WEB_CONFIG_PATH)


def public_web_config(config: dict[str, Any]) -> dict[str, Any]:
    public_config = json.loads(json.dumps(config))
    public_config["auth"]["password_hash"] = "***"
    return public_config

