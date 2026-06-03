from __future__ import annotations

from flask import session

from satana.core.system import collect_interfaces
from satana.core.wifi import default_wireless_interface, interface_iw_type


def get_selected_interface() -> str | None:
    name = session.get("selected_interface")
    if name:
        return name
    return default_wireless_interface()


def set_selected_interface(name: str) -> None:
    session["selected_interface"] = name


def interface_context() -> dict:
    interfaces = collect_interfaces()
    name = get_selected_interface()
    selected = next((item for item in interfaces if item["name"] == name), None)
    if not selected and name:
        selected = {"name": name, "mode": "wireless", "up": True}
    if not selected:
        selected = next(
            (item for item in interfaces if item.get("up") and item.get("name") != "lo"),
            interfaces[0] if interfaces else None,
        )
    interface_name = selected["name"] if selected else "не выбран"
    if selected and selected.get("mode") == "wireless" and name:
        try:
            iw_type = interface_iw_type(name)
            mode_label = iw_type.capitalize() if iw_type != "unknown" else "Wifi card"
        except OSError:
            mode_label = "Wifi card"
    elif selected and selected.get("mode") == "wireless":
        mode_label = "Wifi card"
    else:
        mode_label = "Non wifi card"
    return {
        "interface": selected,
        "interface_name": interface_name,
        "interface_mode": mode_label,
        "interfaces": interfaces,
    }
