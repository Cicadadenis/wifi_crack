from __future__ import annotations

from flask import Blueprint, abort, current_app, jsonify, request, send_from_directory
from werkzeug.security import generate_password_hash

from satana.core.config import deep_merge, public_web_config, save_web_config
from satana.core.logger import collect_logs
from satana.core.paths import REPORTS_DIR
from satana.core.plugins import collect_plugins, set_plugin_enabled
from satana.core.reports import collect_reports, safe_report_path
from satana.core.actions import ALLOWED_ACTIONS, action_needs_interface
from satana.core.tasks import ALLOWED_TASKS, get_task, list_tasks, run_action, run_task
from satana.web.session_iface import get_selected_interface, set_selected_interface
from satana.web.auth import login_required


api = Blueprint("api", __name__, url_prefix="/api")


def api_docs_payload() -> dict:
    return {
        "endpoints": [
            {"method": "GET", "path": "/api/status", "description": "System, adapter, plugin and log status"},
            {"method": "GET", "path": "/api/interfaces", "description": "Network adapter list"},
            {"method": "GET", "path": "/api/plugins", "description": "Plugin metadata"},
            {"method": "POST", "path": "/api/plugins/<file>/toggle", "description": "Enable or disable plugin"},
            {"method": "GET", "path": "/api/reports?q=", "description": "Search reports"},
            {"method": "GET", "path": "/api/reports/<name>", "description": "Download report"},
            {"method": "DELETE", "path": "/api/reports/<name>", "description": "Delete report"},
            {"method": "GET", "path": "/api/settings", "description": "Read web settings"},
            {"method": "PUT", "path": "/api/settings", "description": "Update web settings"},
            {"method": "GET", "path": "/api/logs", "description": "Read latest logs"},
            {"method": "GET", "path": "/api/tasks", "description": "List safe task history"},
            {"method": "GET", "path": "/api/tasks/<task_id>", "description": "Read task status and logs"},
            {"method": "POST", "path": "/api/tasks/run", "description": "Run an allowlisted safe task"},
            {"method": "POST", "path": "/api/actions/run", "description": "Run a SATANA menu action"},
            {"method": "GET", "path": "/api/actions", "description": "List allowed menu actions"},
            {"method": "POST", "path": "/api/interface/select", "description": "Select wireless interface for web menus"},
            {"method": "GET", "path": "/api/interface/selected", "description": "Get selected interface"},
            {"method": "WebSocket", "path": "/socket.io", "description": "Live events: logs, task_logs"},
        ]
    }


@api.route("/status")
@login_required
def api_status():
    return jsonify(current_app.extensions["satana_status"]())


@api.route("/interfaces")
@login_required
def api_interfaces():
    from satana.core.system import collect_interfaces

    return jsonify({"interfaces": collect_interfaces()})


@api.route("/plugins")
@login_required
def api_plugins():
    return jsonify({"plugins": collect_plugins()})


@api.route("/plugins/<path:file_name>/toggle", methods=["POST"])
@login_required
def api_toggle_plugin(file_name: str):
    payload = request.get_json(silent=True) or {}
    try:
        set_plugin_enabled(file_name, bool(payload.get("enabled")))
    except FileNotFoundError:
        abort(404)
    return jsonify({"ok": True})


@api.route("/reports")
@login_required
def api_reports():
    return jsonify({"reports": collect_reports(request.args.get("q", ""))})


@api.route("/reports/<path:name>")
@login_required
def api_report_download(name: str):
    try:
        safe_report_path(name)
    except FileNotFoundError:
        abort(404)
    return send_from_directory(REPORTS_DIR, name, as_attachment=True)


@api.route("/reports/<path:name>", methods=["DELETE"])
@login_required
def api_report_delete(name: str):
    try:
        path = safe_report_path(name)
    except FileNotFoundError:
        abort(404)
    path.unlink()
    return jsonify({"ok": True})


@api.route("/settings", methods=["GET", "PUT"])
@login_required
def api_settings():
    config = current_app.extensions["satana_config"]
    if request.method == "GET":
        return jsonify(public_web_config(config))
    payload = request.get_json(silent=True) or {}
    auth = payload.get("auth", {})
    if auth.get("password_hash") == "***":
        auth.pop("password_hash")
    if "password" in auth and auth["password"]:
        auth["password_hash"] = generate_password_hash(auth.pop("password"))
    merged = deep_merge(config, payload)
    config.clear()
    config.update(merged)
    save_web_config(config)
    current_app.config["SECRET_KEY"] = config["secret_key"]
    return jsonify({"ok": True})


@api.route("/logs")
@login_required
def api_logs():
    config = current_app.extensions["satana_config"]
    return jsonify({"lines": collect_logs(config, int(request.args.get("lines", 120)))})


@api.route("/tasks")
@login_required
def api_tasks():
    return jsonify(
        {
            "tasks": list_tasks(),
            "allowed": sorted(set(ALLOWED_TASKS) | set(ALLOWED_ACTIONS)),
        }
    )


@api.route("/actions")
@login_required
def api_actions():
    return jsonify({"allowed": ALLOWED_ACTIONS})


@api.route("/interface/selected")
@login_required
def api_interface_selected():
    return jsonify({"interface": get_selected_interface()})


@api.route("/interface/select", methods=["POST"])
@login_required
def api_interface_select():
    payload = request.get_json(silent=True) or {}
    name = (payload.get("interface") or "").strip()
    if not name:
        return jsonify({"error": "interface is required"}), 400
    set_selected_interface(name)
    return jsonify({"ok": True, "interface": name})


@api.route("/tasks/<task_id>")
@login_required
def api_task_detail(task_id: str):
    task = get_task(task_id)
    if not task:
        abort(404)
    return jsonify(task)


@api.route("/tasks/run", methods=["POST"])
@login_required
def api_task_run():
    payload = request.get_json(silent=True) or {}
    task_name = payload.get("task", "")
    params = payload.get("params") or {}
    try:
        task_id = run_task(task_name, requested_by="web", params=params)
    except ValueError as exc:
        return jsonify({"error": str(exc), "allowed": sorted(set(ALLOWED_TASKS) | set(ALLOWED_ACTIONS))}), 400
    return jsonify({"task_id": task_id, "status": "pending"}), 202


@api.route("/actions/run", methods=["POST"])
@login_required
def api_action_run():
    payload = request.get_json(silent=True) or {}
    action = payload.get("action", "")
    params = dict(payload.get("params") or {})
    if action_needs_interface(action):
        params.setdefault("interface", get_selected_interface())
        if not params.get("interface"):
            return jsonify({"error": "No interface selected. Open Interfaces and choose one."}), 400
    try:
        task_id = run_action(action, params=params, requested_by="web")
    except ValueError as exc:
        return jsonify({"error": str(exc), "allowed": ALLOWED_ACTIONS}), 400
    return jsonify({"task_id": task_id, "status": "pending", "action": action}), 202


@api.route("/docs")
@login_required
def api_docs():
    return jsonify(api_docs_payload())
