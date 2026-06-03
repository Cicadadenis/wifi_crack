from __future__ import annotations

import argparse

from flask import Flask, abort, current_app, redirect, render_template, request, session, url_for
from flask_socketio import SocketIO
from werkzeug.security import check_password_hash, generate_password_hash

from satana.api.routes import api
from satana.core.config import WEB_CONFIG_PATH, load_web_config, save_web_config
from satana.core.logger import collect_logs, write_web_startup_log
from satana.core.paths import WEB_DIR, ensure_directories
from satana.core.plugins import collect_plugins
from satana.core.reports import collect_reports, safe_report_path
from satana.core.actions import ALLOWED_ACTIONS
from satana.core.menus import MENUS, get_menu
from satana.core.system import collect_interfaces, human_uptime, system_metrics
from satana.core.tasks import latest_task_log_lines, list_tasks
from satana.web.auth import login_required
from satana.web.session_iface import interface_context


socketio = SocketIO(async_mode="threading", cors_allowed_origins=[])


def main_menu_payload(config: dict) -> dict:
    ctx = interface_context()
    submenu_titles = {
        "4": "dos_attacks",
        "5": "handshake_tools",
        "6": "decrypt",
        "7": "evil_twin",
        "8": "wps_attacks",
        "9": "wep_attacks",
        "10": "enterprise_attacks",
    }
    menu_items = [
        {"number": "0", "title": "Выйти из скрипта", "kind": "link", "href": "logout", "icon": "bi-box-arrow-right"},
        {"number": "1", "title": "Выбрать другой сетевой интерфейс", "kind": "link", "href": "interfaces_page", "icon": "bi-router"},
        {
            "number": "2",
            "title": "Перевести интерфейс в режим монитора",
            "kind": "action",
            "action": "monitor_mode",
            "icon": "bi-broadcast",
            "needs_interface": True,
        },
        {
            "number": "3",
            "title": "Перевести интерфейс в управляемый режим",
            "kind": "action",
            "action": "managed_mode",
            "icon": "bi-wifi",
            "needs_interface": True,
        },
    ]
    for number, slug in submenu_titles.items():
        meta = MENUS[slug]
        menu_items.append(
            {
                "number": number,
                "title": meta["title"],
                "kind": "link",
                "href": f"menu_{slug}",
                "icon": "bi-chevron-right",
            }
        )
    return {
        **ctx,
        "safe_tasks": ["system_status", "list_interfaces", "check_dependencies", "tail_logs"],
        "allowed_actions": ALLOWED_ACTIONS,
        "menu_items": menu_items,
    }


def render_submenu(slug: str):
    menu = get_menu(slug)
    if not menu:
        abort(404)
    ctx = interface_context()
    return render_template(
        "submenu.html",
        page=f"menu_{slug}",
        menu=menu,
        **ctx,
    )


def status_payload(config: dict) -> dict:
    metrics = system_metrics()
    return {
        "project": config["project"],
        "uptime": human_uptime(),
        "cpu": metrics["cpu"],
        "memory": metrics["memory"],
        "interfaces": collect_interfaces(),
        "plugins": collect_plugins(),
        "logs": collect_logs(config),
    }


def create_app() -> Flask:
    ensure_directories()
    config = load_web_config()
    app = Flask(
        __name__,
        template_folder=str(WEB_DIR / "templates"),
        static_folder=str(WEB_DIR / "static"),
    )
    app.config["SECRET_KEY"] = config["secret_key"]
    app.extensions["satana_config"] = config
    app.extensions["satana_status"] = lambda: status_payload(config)
    app.register_blueprint(api)
    socketio.init_app(app)

    @app.context_processor
    def inject_globals():
        return {"project_name": config["project"].get("name", "SATANA")}

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form.get("username", "")
            password = request.form.get("password", "")
            auth = config.get("auth", {})
            if username == auth.get("username") and check_password_hash(auth.get("password_hash", ""), password):
                session["authenticated"] = True
                return redirect(request.args.get("next") or url_for("dashboard"))
            return render_template("login.html", error="Invalid username or password")
        return render_template("login.html")

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    @app.route("/")
    @login_required
    def dashboard():
        return render_template(
            "dashboard.html",
            page="dashboard",
            status=status_payload(config),
            tasks=list_tasks()[:8],
            reports=collect_reports(),
        )

    @app.route("/menu")
    @login_required
    def main_menu_page():
        return render_template(
            "main_menu.html",
            page="main_menu",
            menu=main_menu_payload(config),
            status=status_payload(config),
            tasks=list_tasks()[:8],
        )

    @app.route("/interfaces")
    @login_required
    def interfaces_page():
        ctx = interface_context()
        return render_template(
            "interfaces.html",
            page="interfaces",
            interfaces=ctx["interfaces"],
            selected_interface=ctx["interface_name"],
        )

    @app.route("/menu/dos")
    @login_required
    def menu_dos_attacks():
        return render_submenu("dos_attacks")

    @app.route("/menu/handshake")
    @login_required
    def menu_handshake_tools():
        return render_submenu("handshake_tools")

    @app.route("/menu/decrypt")
    @login_required
    def menu_decrypt():
        return render_submenu("decrypt")

    @app.route("/menu/decrypt/personal")
    @login_required
    def menu_decrypt_personal():
        return render_submenu("decrypt_personal")

    @app.route("/menu/decrypt/enterprise")
    @login_required
    def menu_decrypt_enterprise():
        return render_submenu("decrypt_enterprise")

    @app.route("/menu/evil-twin")
    @login_required
    def menu_evil_twin():
        return render_submenu("evil_twin")

    @app.route("/menu/wps")
    @login_required
    def menu_wps_attacks():
        return render_submenu("wps_attacks")

    @app.route("/menu/wep")
    @login_required
    def menu_wep_attacks():
        return render_submenu("wep_attacks")

    @app.route("/menu/enterprise")
    @login_required
    def menu_enterprise_attacks():
        return render_submenu("enterprise_attacks")

    @app.route("/plugins")
    @login_required
    def plugins_page():
        return render_template("plugins.html", page="plugins", plugins=collect_plugins())

    @app.route("/reports")
    @login_required
    def reports_page():
        query = request.args.get("q", "")
        return render_template("reports.html", page="reports", reports=collect_reports(query), query=query)

    @app.route("/logs")
    @login_required
    def logs_page():
        return render_template("logs.html", page="logs", tasks=list_tasks(), task_logs=latest_task_log_lines())

    @app.route("/reports/view/<path:name>")
    @login_required
    def report_view(name: str):
        try:
            path = safe_report_path(name)
        except FileNotFoundError:
            abort(404)
        content = path.read_text(encoding="utf-8", errors="replace")
        return render_template("report_view.html", page="reports", name=name, content=content)

    @app.route("/settings", methods=["GET", "POST"])
    @login_required
    def settings_page():
        saved = False
        if request.method == "POST":
            config["project"]["name"] = request.form.get("project_name", config["project"]["name"]).strip() or "SATANA"
            config["server"]["host"] = request.form.get("host", config["server"]["host"]).strip() or "127.0.0.1"
            config["server"]["port"] = int(request.form.get("port", config["server"]["port"]))
            config["ui"]["refresh_interval"] = int(request.form.get("refresh_interval", config["ui"]["refresh_interval"]))
            config["auth"]["username"] = request.form.get("username", config["auth"]["username"]).strip() or "admin"
            new_password = request.form.get("password", "")
            if new_password:
                config["auth"]["password_hash"] = generate_password_hash(new_password)
            save_web_config(config)
            current_app.config["SECRET_KEY"] = config["secret_key"]
            saved = True
        return render_template("settings.html", page="settings", config=config, saved=saved, config_path=WEB_CONFIG_PATH)

    @app.route("/docs")
    @login_required
    def docs_page():
        return render_template("docs.html", page="docs")

    return app


app = create_app()


def log_broadcaster() -> None:
    while True:
        config = app.extensions["satana_config"]
        socketio.emit("logs", {"lines": collect_logs(config)})
        socketio.emit("task_logs", {"lines": latest_task_log_lines(), "tasks": list_tasks()[:20]})
        socketio.sleep(2)


@socketio.on("connect")
def ws_connect():
    from flask import session

    if not session.get("authenticated"):
        return False
    config = app.extensions["satana_config"]
    socketio.emit("logs", {"lines": collect_logs(config)})
    socketio.emit("task_logs", {"lines": latest_task_log_lines(), "tasks": list_tasks()[:20]})


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    config = app.extensions["satana_config"]
    parser = argparse.ArgumentParser(description="SATANA Web UI")
    parser.add_argument("--host", default=config["server"]["host"])
    parser.add_argument("--port", type=int, default=int(config["server"]["port"]))
    parser.add_argument("--debug", action="store_true", default=bool(config["server"].get("debug", False)))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    write_web_startup_log()
    socketio.start_background_task(log_broadcaster)
    args = parse_args(argv)
    socketio.run(app, host=args.host, port=args.port, debug=args.debug, allow_unsafe_werkzeug=True)


if __name__ == "__main__":
    main()
