from __future__ import annotations

import json
import subprocess
import threading
import traceback
import uuid
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Any, Callable

from satana.core.actions import (
    ALLOWED_ACTIONS,
    build_satana_env,
    is_shell_action,
    run_python_action,
    satana_script_command,
)
from satana.core.config import load_web_config
from satana.core.logger import collect_logs
from satana.core.paths import BASE_DIR, TASK_LOGS_DIR, TASKS_DB_PATH, ensure_directories
from satana.core.plugins import collect_plugins
from satana.core.reports import collect_reports
from satana.core.system import collect_interfaces, human_uptime, system_metrics


TASK_TIMEOUT = 30
ACTION_TIMEOUT = 3600
TASK_STATUSES = {"pending", "running", "success", "failed"}
_LOCK = threading.RLock()


def _now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def _task_log_path(task_id: str) -> Path:
    return TASK_LOGS_DIR / f"{task_id}.log"


def _read_history() -> dict[str, dict[str, Any]]:
    ensure_directories()
    if not TASKS_DB_PATH.exists():
        return {}
    try:
        with TASKS_DB_PATH.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
            return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _write_history(history: dict[str, dict[str, Any]]) -> None:
    TASKS_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = TASKS_DB_PATH.with_suffix(".json.tmp")
    with tmp_path.open("w", encoding="utf-8") as fh:
        json.dump(history, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    tmp_path.replace(TASKS_DB_PATH)


def _update_task(task_id: str, **changes: Any) -> dict[str, Any]:
    with _LOCK:
        history = _read_history()
        task = history[task_id]
        task.update(changes)
        task["updated_at"] = _now()
        history[task_id] = task
        _write_history(history)
        return dict(task)


def _append_log(task_id: str, text: str) -> None:
    TASK_LOGS_DIR.mkdir(parents=True, exist_ok=True)
    with _task_log_path(task_id).open("a", encoding="utf-8", errors="replace") as fh:
        fh.write(text)
        if text and not text.endswith("\n"):
            fh.write("\n")


def _json_stdout(payload: dict[str, Any] | list[Any]) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def _task_system_status() -> None:
    config = load_web_config()
    metrics = system_metrics()
    _json_stdout(
        {
            "project": config["project"],
            "uptime": human_uptime(),
            "cpu": metrics["cpu"],
            "memory": metrics["memory"],
            "interfaces": collect_interfaces(),
            "plugins": collect_plugins(),
            "logs": collect_logs(config),
        }
    )


def _task_list_interfaces() -> None:
    _json_stdout({"interfaces": collect_interfaces()})


def _task_list_plugins() -> None:
    _json_stdout({"plugins": collect_plugins()})


def _task_list_reports() -> None:
    _json_stdout({"reports": collect_reports()})


def _task_tail_logs() -> None:
    config = load_web_config()
    for line in collect_logs(config, 120):
        print(line)


def _task_check_dependencies() -> tuple[int, str, str]:
    script = BASE_DIR / "_check_pkgs.sh"
    if not script.exists():
        return 1, "", f"Dependency checker not found: {script}\n"
    completed = subprocess.run(
        ["bash", str(script)],
        cwd=BASE_DIR,
        text=True,
        capture_output=True,
        timeout=TASK_TIMEOUT,
        check=False,
    )
    return completed.returncode, completed.stdout, completed.stderr


INTERNAL_TASKS: dict[str, Callable[[], None]] = {
    "system_status": _task_system_status,
    "list_interfaces": _task_list_interfaces,
    "list_plugins": _task_list_plugins,
    "list_reports": _task_list_reports,
    "tail_logs": _task_tail_logs,
}

ALLOWED_TASKS = sorted([*INTERNAL_TASKS.keys(), "check_dependencies"])


def _run_internal_task(task_name: str) -> tuple[int, str, str]:
    stdout = StringIO()
    stderr = StringIO()
    try:
        with redirect_stdout(stdout), redirect_stderr(stderr):
            INTERNAL_TASKS[task_name]()
        return 0, stdout.getvalue(), stderr.getvalue()
    except Exception:
        return 1, stdout.getvalue(), stderr.getvalue() + traceback.format_exc()


def _run_satana_action(action: str, params: dict[str, Any]) -> tuple[int, str, str]:
    env = build_satana_env(action, params)
    timeout = ACTION_TIMEOUT
    if action.startswith("scan_"):
        timeout = int(params.get("seconds", 30)) + 60
    completed = subprocess.run(
        satana_script_command(),
        cwd=BASE_DIR,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
        env=env,
    )
    return completed.returncode, completed.stdout, completed.stderr


def _execute(task_id: str) -> None:
    task = _update_task(task_id, status="running", started_at=_now())
    task_name = task["task"]
    params = task.get("params") or {}
    _append_log(task_id, f"[{_now()}] task started: {task_name}\n")
    if params:
        _append_log(task_id, f"[params] {json.dumps(params, ensure_ascii=False)}\n")
    try:
        if task_name == "check_dependencies":
            return_code, stdout, stderr = _task_check_dependencies()
        elif task_name in ALLOWED_ACTIONS:
            if is_shell_action(task_name):
                return_code, stdout, stderr = _run_satana_action(task_name, params)
            else:
                return_code, stdout, stderr = run_python_action(task_name, params)
        else:
            return_code, stdout, stderr = _run_internal_task(task_name)
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = (exc.stderr or "") + f"\nTask timed out after {TASK_TIMEOUT} seconds\n"
        return_code = 124

    if stdout:
        _append_log(task_id, "[stdout]\n" + stdout)
    if stderr:
        _append_log(task_id, "[stderr]\n" + stderr)

    status = "success" if return_code == 0 else "failed"
    _append_log(task_id, f"[{_now()}] task finished: {status} (exit={return_code})\n")
    _update_task(task_id, status=status, finished_at=_now(), return_code=return_code)


def run_task(task_name: str, requested_by: str = "web", params: dict[str, Any] | None = None) -> str:
    allowed = set(ALLOWED_TASKS) | set(ALLOWED_ACTIONS)
    if task_name not in allowed:
        raise ValueError(f"Task is not allowed: {task_name}")
    ensure_directories()
    task_id = uuid.uuid4().hex
    task = {
        "id": task_id,
        "task": task_name,
        "status": "pending",
        "requested_by": requested_by,
        "created_at": _now(),
        "updated_at": _now(),
        "started_at": None,
        "finished_at": None,
        "return_code": None,
        "params": params or {},
        "log_path": str(_task_log_path(task_id).relative_to(BASE_DIR)),
    }
    with _LOCK:
        history = _read_history()
        history[task_id] = task
        _write_history(history)
    _append_log(task_id, f"[{_now()}] task queued: {task_name}\n")
    thread = threading.Thread(target=_execute, args=(task_id,), daemon=True)
    thread.start()
    return task_id


def list_tasks() -> list[dict[str, Any]]:
    with _LOCK:
        history = _read_history()
    return sorted(history.values(), key=lambda item: item.get("created_at", ""), reverse=True)


def get_task(task_id: str) -> dict[str, Any] | None:
    with _LOCK:
        task = _read_history().get(task_id)
    if not task:
        return None
    result = dict(task)
    result["logs"] = read_task_log(task_id)
    return result


def read_task_log(task_id: str, lines: int = 200) -> list[str]:
    path = _task_log_path(task_id)
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        return [line.rstrip("\n") for line in fh.readlines()[-lines:]]


def run_action(action: str, params: dict[str, Any] | None = None, requested_by: str = "web") -> str:
    if action not in ALLOWED_ACTIONS:
        raise ValueError(f"Action is not allowed: {action}")
    return run_task(action, requested_by=requested_by, params=params or {})


def latest_task_log_lines(lines: int = 200) -> list[str]:
    tasks = list_tasks()
    if not tasks:
        return []
    return read_task_log(tasks[0]["id"], lines)
