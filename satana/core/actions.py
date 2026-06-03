from __future__ import annotations

import os
from typing import Any

from satana.core.paths import BASE_DIR
from satana.core.wifi import scan_targets


# Actions executed locally in Python (no full satana.sh menu).
PYTHON_ACTIONS = {
    "scan_targets": lambda params: scan_targets(
        params["interface"], int(params.get("seconds", 30)), params.get("cipher", "")
    ),
    "scan_wpa_targets": lambda params: scan_targets(
        params["interface"], int(params.get("seconds", 30)), "WPA"
    ),
    "scan_wep_targets": lambda params: scan_targets(
        params["interface"], int(params.get("seconds", 30)), "WEP"
    ),
    "scan_wps_targets": lambda params: scan_targets(
        params["interface"], int(params.get("seconds", 30)), "WPA"
    ),
    "scan_enterprise_targets": lambda params: scan_targets(
        params["interface"], int(params.get("seconds", 30)), "WPA"
    ),
}

# Actions delegated to satana.sh (SATANA_WEB_ACTION).
SATANA_SHELL_ACTIONS = {
    "monitor_mode",
    "managed_mode",
    "mdk_deauth",
    "aireplay_deauth",
    "wds_confusion",
    "beacon_flood",
    "auth_dos",
    "michael_shutdown",
    "capture_handshake",
    "clean_handshake",
    "aircrack_dictionary",
    "aircrack_dictionary_library",
    "aircrack_bruteforce",
    "hashcat_dictionary_personal",
    "hashcat_bruteforce_personal",
    "hashcat_rulebased_personal",
    "john_dictionary",
    "john_bruteforce",
    "hashcat_dictionary_enterprise",
    "hashcat_bruteforce_enterprise",
    "hashcat_rulebased_enterprise",
    "asleap_dictionary",
    "et_onlyap",
    "et_sniffing",
    "et_sniffing_sslstrip",
    "et_sniffing_sslstrip2",
    "et_captive_portal",
    "wps_custompin_bully",
    "wps_custompin_reaver",
    "wps_pixiedust_bully",
    "wps_pixiedust_reaver",
    "wps_bruteforce_bully",
    "wps_bruteforce_reaver",
    "wps_pindb_bully",
    "wps_pindb_reaver",
    "wps_nullpin_reaver",
    "wep_allinone",
    "enterprise_create_certs",
    "enterprise_smooth",
    "enterprise_noisy",
}

ALLOWED_ACTIONS = sorted([*PYTHON_ACTIONS.keys(), *SATANA_SHELL_ACTIONS])

NO_INTERFACE_ACTIONS = {
    "clean_handshake",
    "enterprise_create_certs",
    "aircrack_dictionary",
    "aircrack_dictionary_library",
    "aircrack_bruteforce",
    "hashcat_dictionary_personal",
    "hashcat_bruteforce_personal",
    "hashcat_rulebased_personal",
    "john_dictionary",
    "john_bruteforce",
    "hashcat_dictionary_enterprise",
    "hashcat_bruteforce_enterprise",
    "hashcat_rulebased_enterprise",
    "asleap_dictionary",
}


def action_needs_interface(action: str) -> bool:
    return action not in NO_INTERFACE_ACTIONS


def _env_key(name: str) -> str:
    return f"SATANA_{name.upper()}"


def build_satana_env(action: str, params: dict[str, Any]) -> dict[str, str]:
    env = os.environ.copy()
    env["SATANA_WEB_ACTION"] = action
    env["SATANA_SKIP_INTRO"] = "true"
    env["SATANA_SILENT_CHECKS"] = "true"
    env["SATANA_PRINT_HINTS"] = "false"
    env["SATANA_WINDOWS_HANDLING"] = "none"

    mapping = {
        "interface": "INTERFACE",
        "bssid": "BSSID",
        "channel": "CHANNEL",
        "essid": "ESSID",
        "pin": "PIN",
        "pursuit": "PURSUIT",
        "seconds": "SCAN_SECONDS",
        "file": "FILE",
        "capture_file": "CAPTURE_FILE",
        "dictionary": "DICTIONARY",
        "rules": "RULES",
        "challenge": "CHALLENGE",
        "response": "RESPONSE",
    }
    for key, env_suffix in mapping.items():
        value = params.get(key)
        if value is None or value == "":
            continue
        if key == "pursuit":
            env[_env_key(env_suffix)] = "1" if value in (True, "true", "1", "on", "yes") else "0"
        else:
            env[_env_key(env_suffix)] = str(value)
    return env


def run_python_action(action: str, params: dict[str, Any]) -> tuple[int, str, str]:
    handler = PYTHON_ACTIONS.get(action)
    if not handler:
        raise ValueError(f"Unknown python action: {action}")
    return handler(params)


def is_shell_action(action: str) -> bool:
    return action in SATANA_SHELL_ACTIONS


def satana_script_command() -> list[str]:
    return ["bash", str(BASE_DIR / "satana.sh")]
