#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from satana.core.config import load_web_config
from satana.core.logger import collect_logs
from satana.core.paths import BASE_DIR
from satana.core.plugins import collect_plugins
from satana.core.reports import collect_reports
from satana.core.system import collect_interfaces, human_uptime, system_metrics


def print_json(payload: dict | list) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def command_cli(args: argparse.Namespace) -> int:
    script = BASE_DIR / "satana.sh"
    if not script.exists():
        print(f"satana.sh not found: {script}", file=sys.stderr)
        return 1
    command = ["bash", str(script), *args.args]
    return subprocess.call(command, cwd=BASE_DIR)


def command_web(args: argparse.Namespace) -> int:
    from satana.web.app import main

    web_args: list[str] = []
    if args.host:
        web_args.extend(["--host", args.host])
    if args.port:
        web_args.extend(["--port", str(args.port)])
    if args.debug:
        web_args.append("--debug")
    main(web_args)
    return 0


def command_status(_args: argparse.Namespace) -> int:
    config = load_web_config()
    metrics = system_metrics()
    print_json(
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
    return 0


def command_plugins(_args: argparse.Namespace) -> int:
    print_json({"plugins": collect_plugins()})
    return 0


def command_reports(args: argparse.Namespace) -> int:
    print_json({"reports": collect_reports(args.query or "")})
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SATANA unified launcher")
    subparsers = parser.add_subparsers(dest="command", required=True)

    cli_parser = subparsers.add_parser("cli", help="Run the legacy shell CLI")
    cli_parser.add_argument("args", nargs=argparse.REMAINDER)
    cli_parser.set_defaults(func=command_cli)

    web_parser = subparsers.add_parser("web", help="Run the Flask Web UI")
    web_parser.add_argument("--host")
    web_parser.add_argument("--port", type=int)
    web_parser.add_argument("--debug", action="store_true")
    web_parser.set_defaults(func=command_web)

    status_parser = subparsers.add_parser("status", help="Print system status as JSON")
    status_parser.set_defaults(func=command_status)

    plugins_parser = subparsers.add_parser("plugins", help="Print plugin list as JSON")
    plugins_parser.set_defaults(func=command_plugins)

    reports_parser = subparsers.add_parser("reports", help="Print reports as JSON")
    reports_parser.add_argument("-q", "--query", default="")
    reports_parser.set_defaults(func=command_reports)

    return parser


def main(argv: list[str] | None = None) -> int:
    os.environ.setdefault("SATANA_HOME", str(Path(__file__).resolve().parent))
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())

