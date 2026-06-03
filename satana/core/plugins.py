from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Any

from satana.core.paths import LEGACY_PLUGINS_DIR, PLUGINS_DIR


PLUGIN_VAR_RE = re.compile(r'^\s*(plugin_[a-zA-Z0-9_]+)=("([^"]*)"|([^\s#]+))')


def migrate_legacy_plugins() -> None:
    PLUGINS_DIR.mkdir(parents=True, exist_ok=True)
    if not LEGACY_PLUGINS_DIR.exists():
        return
    for path in LEGACY_PLUGINS_DIR.glob("*.sh"):
        target = PLUGINS_DIR / path.name
        if not target.exists():
            shutil.copy2(path, target)


def parse_plugin(path: Path) -> dict[str, Any]:
    data = {"file": path.name, "name": path.stem, "description": "", "author": "", "enabled": False}
    try:
        for line in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
            match = PLUGIN_VAR_RE.match(line)
            if not match:
                continue
            key = match.group(1)
            value = match.group(3) if match.group(3) is not None else match.group(4)
            if key == "plugin_name":
                data["name"] = value
            elif key == "plugin_description":
                data["description"] = value
            elif key == "plugin_author":
                data["author"] = value
            elif key == "plugin_enabled":
                data["enabled"] = value == "1"
    except OSError:
        pass
    return data


def collect_plugins() -> list[dict[str, Any]]:
    migrate_legacy_plugins()
    if not PLUGINS_DIR.exists():
        return []
    return [parse_plugin(path) for path in sorted(PLUGINS_DIR.glob("*.sh")) if path.name != "plugin_template.sh"]


def plugin_path(file_name: str) -> Path:
    path = (PLUGINS_DIR / file_name).resolve()
    root = PLUGINS_DIR.resolve()
    if root not in path.parents or not path.is_file() or path.suffix != ".sh":
        raise FileNotFoundError(file_name)
    return path


def set_plugin_enabled(file_name: str, enabled: bool) -> None:
    path = plugin_path(file_name)
    content = path.read_text(encoding="utf-8-sig", errors="replace")
    replacement = f"plugin_enabled={1 if enabled else 0}"
    if re.search(r"^\s*plugin_enabled=.*$", content, flags=re.MULTILINE):
        content = re.sub(r"^\s*plugin_enabled=.*$", replacement, content, count=1, flags=re.MULTILINE)
    else:
        content = f"{replacement}\n{content}"
    path.write_text(content, encoding="utf-8")

