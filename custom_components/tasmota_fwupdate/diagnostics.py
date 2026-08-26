"""Diagnostics support for Tasmota Firmware Update."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from .discovery import DISCOVERY_DATA
from .update import _release_cache

TO_REDACT = {
    "ip",
    "mac",
    "topic",
    "fulltopic",
    "hostname",
    "friendlyname",
    "devicename",
    "name",
    "ssid",
    "bssid",
    "wifi",
    "password",
    "username",
    "user",
    "latitude",
    "longitude",
    "elevation",
}


def _anonymize_mac(mac: str) -> str:
    """Anonymize MAC address keeping only the manufacturer prefix / generic structure."""
    if not mac or len(mac) < 6:
        return "**REDACTED**"
    parts = (
        mac.split(":")
        if ":" in mac
        else [mac[i : i + 2] for i in range(0, len(mac), 2)]
    )
    if len(parts) >= 6:
        return f"{parts[0]}:{parts[1]}:{parts[2]}:**:**:**"
    return "**REDACTED**"


def _sanitize_discovery_payload(data: dict[str, Any]) -> dict[str, Any]:
    """Sanitize and redact sensitive information from raw discovery payload."""
    redacted = async_redact_data(data, TO_REDACT)
    if "mac" in data:
        redacted["mac"] = _anonymize_mac(str(data["mac"]))
    return redacted


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    discovery_data = hass.data.get(DISCOVERY_DATA, {})

    devices_data: list[dict[str, Any]] = []
    for mac, raw_payload in discovery_data.items():
        if isinstance(raw_payload, dict):
            devices_data.append(
                {
                    "mac_anonymized": _anonymize_mac(mac),
                    "discovery_payload": _sanitize_discovery_payload(raw_payload),
                }
            )

    return {
        "config_entry": {
            "entry_id": entry.entry_id,
            "version": entry.version,
            "domain": entry.domain,
            "title": entry.title,
            "data": async_redact_data(entry.data, TO_REDACT),
        },
        "release_cache": {
            "version": _release_cache.get("version"),
            "release_url": _release_cache.get("release_url"),
            "last_check": str(_release_cache.get("last_check")),
            "rate_limited": _release_cache.get("rate_limited"),
        },
        "discovered_devices_count": len(discovery_data),
        "devices": devices_data,
    }


async def async_get_device_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry, device: dr.DeviceEntry
) -> dict[str, Any]:
    """Return diagnostics for a specific device."""
    discovery_data = hass.data.get(DISCOVERY_DATA, {})

    # Extract MAC from device connections
    device_mac = None
    for connection in device.connections:
        if connection[0] == dr.CONNECTION_NETWORK_MAC:
            device_mac = connection[1]
            break

    # Extract entity states and info associated with this device
    entity_reg = er.async_get(hass)
    device_entities = er.async_entries_for_device(entity_reg, device.id)
    entities_data = []

    for entity_entry in device_entities:
        state = hass.states.get(entity_entry.entity_id)
        state_dict = None
        if state:
            state_dict = {
                "state": state.state,
                "attributes": async_redact_data(dict(state.attributes), TO_REDACT),
            }
        entities_data.append(
            {
                "entity_id": entity_entry.entity_id,
                "domain": entity_entry.domain,
                "platform": entity_entry.platform,
                "unique_id": entity_entry.unique_id,
                "disabled_by": entity_entry.disabled_by,
                "state": state_dict,
            }
        )

    raw_payload = discovery_data.get(device_mac) if device_mac else None
    sanitized_payload = (
        _sanitize_discovery_payload(raw_payload)
        if isinstance(raw_payload, dict)
        else None
    )

    return {
        "device": {
            "id": device.id,
            "manufacturer": device.manufacturer,
            "model": device.model,
            "sw_version": device.sw_version,
            "hw_version": device.hw_version,
            "mac_anonymized": _anonymize_mac(device_mac) if device_mac else None,
        },
        "discovery_payload": sanitized_payload,
        "release_cache": {
            "version": _release_cache.get("version"),
            "rate_limited": _release_cache.get("rate_limited"),
        },
        "entities": entities_data,
    }
