"""Support for Tasmota updates."""

from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import Any

import aiohttp
from packaging.version import Version, InvalidVersion

from homeassistant.components import update
from homeassistant.components.update import UpdateEntity, UpdateEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.dispatcher import async_dispatcher_connect, async_dispatcher_send
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import dt as dt_util

from .hatasmota import TasmotaUpdate
from .hatasmota.entity import TasmotaEntity as HATasmotaEntity
from .hatasmota.models import DiscoveryHashType

from .const import DATA_REMOVE_DISCOVER_COMPONENT, DOMAIN
from .discovery import TASMOTA_DISCOVERY_ENTITY_NEW
from .entity import TasmotaAvailability, TasmotaDiscoveryUpdate, TasmotaEntity

_LOGGER = logging.getLogger(__name__)

# GitHub API for latest Tasmota release
GITHUB_RELEASES_URL = "https://api.github.com/repos/arendst/Tasmota/releases/latest"
GITHUB_RELEASE_PAGE = "https://github.com/arendst/Tasmota/releases/latest"
VERSION_CHECK_INTERVAL = timedelta(hours=24)
UPDATE_TIMEOUT = timedelta(minutes=5)

# Staged upgrade path for old Tasmota firmware versions
# Each tuple: (minimum_version_to_skip_this_step, upgrade_url)
# NOTICE: Older versions use underscore in URL (pre 5.14 doesn't support dash)
UPGRADE_STEPS = [
    (Version("3.9.0"), None),  # Very old - manual upgrade required
    (Version("4.0.0"), None),  # Very old - manual upgrade required
    (Version("5.14.0"), "http://ota.tasmota.com/tasmota/release_5.14.0/sonoff.bin"),
    (Version("6.7.1"), "http://ota.tasmota.com/tasmota/release_6.7.1/sonoff.bin"),
    (Version("7.2.0"), "http://ota.tasmota.com/tasmota/release-7.2.0/tasmota.bin"),
    (Version("8.5.1"), "http://ota.tasmota.com/tasmota/release-8.5.1/tasmota.bin"),
    (Version("9.1.0"), "http://ota.tasmota.com/tasmota/release-9.1.0/tasmota.bin.gz"),
]
LATEST_URL = "http://ota.tasmota.com/tasmota/release/tasmota.bin.gz"

# Global cache for latest version and release info (shared across all entities)
_release_cache: dict[str, Any] = {
    "version": None,
    "release_url": None,
    "release_summary": None,
    "release_notes": None,
    "last_check": None,
}


async def _fetch_latest_release(hass: HomeAssistant) -> dict[str, Any] | None:
    """Fetch the latest Tasmota release info from GitHub.

    Uses Home Assistant's shared aiohttp session for efficiency and proper cleanup.
    """
    try:
        session = async_get_clientsession(hass)
        async with asyncio.timeout(30):
            response = await session.get(
                GITHUB_RELEASES_URL,
                headers={"Accept": "application/vnd.github.v3+json"},
            )
            if response.status == 200:
                data = await response.json()
                tag = data.get("tag_name", "")
                # Strip 'v' prefix if present (e.g., "v14.3.0" -> "14.3.0")
                version = tag.lstrip("v")

                # Get release URL
                release_url = data.get("html_url", GITHUB_RELEASE_PAGE)

                # Get release body (full changelog in Markdown)
                release_notes = data.get("body", "")

                # Create summary (first 250 chars of release notes)
                release_summary = ""
                if release_notes:
                    # Take first paragraph or first 250 chars
                    first_para = release_notes.split("\n\n")[0]
                    release_summary = first_para[:250] + "..." if len(first_para) > 250 else first_para
                    # Clean up markdown for summary
                    release_summary = re.sub(r'[#*`]', '', release_summary).strip()

                _LOGGER.debug(
                    "Fetched latest Tasmota release: %s (%s)",
                    version,
                    release_url,
                )

                return {
                    "version": version,
                    "release_url": release_url,
                    "release_notes": release_notes,
                    "release_summary": release_summary,
                }
            _LOGGER.warning(
                "GitHub API returned status %s when fetching Tasmota release",
                response.status,
            )
    except TimeoutError:
        _LOGGER.warning("Timeout fetching latest Tasmota release from GitHub")
    except aiohttp.ClientError as err:
        _LOGGER.warning("Error fetching latest Tasmota release: %s", err)
    except Exception:  # noqa: BLE001
        _LOGGER.exception("Unexpected error fetching Tasmota release")
    return None


def _parse_installed_version(version_str: str) -> str:
    """Parse installed version string, stripping suffixes like '(tasmota)'."""
    if not version_str:
        return ""
    # Version format: "14.3.0(tasmota)" -> "14.3.0"
    match = re.match(r"^([\d.]+)", version_str)
    return match.group(1) if match else version_str


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Tasmota update dynamically through discovery."""

    async def _refresh_latest_release(_now: datetime | None = None) -> None:
        """Refresh the cached release info."""
        release_info = await _fetch_latest_release(hass)
        if release_info:
            _release_cache.update(release_info)
            _release_cache["last_check"] = _now
            # Notify all update entities to refresh
            async_dispatcher_send(
                hass, f"{DOMAIN}_release_update", release_info
            )

    # Initial fetch
    await _refresh_latest_release()

    # Schedule periodic refresh (every 24 hours)
    unsub = async_track_time_interval(hass, _refresh_latest_release, VERSION_CHECK_INTERVAL)

    # Store unsub for cleanup
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    if "version_check_unsub" not in hass.data[DOMAIN]:
        hass.data[DOMAIN]["version_check_unsub"] = unsub

    @callback
    def async_discover(
        tasmota_entity: HATasmotaEntity, discovery_hash: DiscoveryHashType
    ) -> None:
        """Discover and add a Tasmota update."""
        async_add_entities(
            [
                TasmotaUpdateEntity(
                    tasmota_entity=tasmota_entity, discovery_hash=discovery_hash
                )
            ]
        )

    hass.data[DATA_REMOVE_DISCOVER_COMPONENT.format(update.DOMAIN)] = (
        async_dispatcher_connect(
            hass,
            TASMOTA_DISCOVERY_ENTITY_NEW.format(update.DOMAIN),
            async_discover,
        )
    )


class TasmotaUpdateEntity(
    TasmotaAvailability,
    TasmotaDiscoveryUpdate,
    TasmotaEntity,
    UpdateEntity,
):
    """Representation of a Tasmota update."""

    _tasmota_entity: TasmotaUpdate

    def __init__(self, **kwds: Any) -> None:
        """Initialize."""
        super().__init__(**kwds)
        self._attr_supported_features = (
            UpdateEntityFeature.INSTALL
            | UpdateEntityFeature.PROGRESS
            | UpdateEntityFeature.RELEASE_NOTES
        )
        self._attr_title = "Tasmota"
        self._attr_installed_version = None
        self._attr_latest_version = _release_cache.get("version")
        self._attr_release_url = _release_cache.get("release_url")
        self._attr_release_summary = _release_cache.get("release_summary")
        self._release_notes = _release_cache.get("release_notes")
        self._update_in_progress = False
        self._version_before_update: str | None = None
        self._suppress_availability_updates = False
        self._update_started: datetime | None = None

    def _get_next_upgrade_target(self) -> tuple[str | None, str | None]:
        """Calculate next upgrade target version and URL based on staged upgrade path.

        Returns tuple of (target_version, url). If url is None but target_version is set,
        manual upgrade is required for very old firmware versions.
        """
        if not self._attr_installed_version:
            return None, None

        try:
            current = Version(self._attr_installed_version)
        except InvalidVersion:
            _LOGGER.warning(
                "Cannot parse installed version: %s", self._attr_installed_version
            )
            return None, None

        for target_version, url in UPGRADE_STEPS:
            if current < target_version:
                return str(target_version), url

        # Version >= 9.1.0, can upgrade directly to latest
        return self._attr_latest_version, LATEST_URL

    @property
    def latest_version(self) -> str | None:
        """Return the latest version, considering staged upgrade path for old devices."""
        if not self._attr_installed_version:
            return self._attr_latest_version

        next_target, url = self._get_next_upgrade_target()

        # If next target is different from actual latest, show the intermediate step
        if next_target and next_target != self._attr_latest_version:
            return next_target

        return self._attr_latest_version

    @property
    def in_progress(self) -> bool | int:
        """Return if update is in progress."""
        if self._update_in_progress:
            # Return True for indeterminate progress (no percentage available)
            return True
        return False

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        # During update, stay available even if device is temporarily offline
        if self._update_in_progress:
            return True
        return super().available

    async def availability_updated(self, available: bool) -> None:
        """Handle updated availability, suppressed during firmware update."""
        if self._suppress_availability_updates:
            _LOGGER.debug(
                "Suppressing availability update (%s) during firmware update",
                available,
            )
            return
        await super().availability_updated(available)

    async def async_release_notes(self) -> str | None:
        """Return the release notes (changelog) from GitHub.

        If a staged upgrade is required, prepend a warning about the upgrade path.
        """
        notes = self._release_notes or ""

        if self._attr_installed_version:
            next_target, url = self._get_next_upgrade_target()
            if next_target and next_target != self._attr_latest_version:
                if url is None:
                    # Very old firmware - manual upgrade required
                    warning = (
                        f"⚠️ **Manual upgrade required!**\n\n"
                        f"Your current firmware ({self._attr_installed_version}) is too old "
                        f"for automatic OTA updates. Please upgrade manually to at least "
                        f"version {next_target} before using this update feature.\n\n"
                        f"---\n\n"
                    )
                else:
                    # Staged upgrade
                    warning = (
                        f"ℹ️ **Staged upgrade required**\n\n"
                        f"Your firmware ({self._attr_installed_version}) requires a staged "
                        f"upgrade path. This update will first upgrade to version {next_target}. "
                        f"You will need to run the update multiple times to reach the latest version.\n\n"
                        f"---\n\n"
                    )
                return warning + notes

        return notes

    async def async_added_to_hass(self) -> None:
        """Subscribe to Tasmota updates."""
        await super().async_added_to_hass()
        self._tasmota_entity.set_on_state_callback(self._on_state_callback)
        await self._tasmota_entity.poll_status()

        # Subscribe to release updates
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{DOMAIN}_release_update",
                self._on_release_update,
            )
        )

    @callback
    def _on_release_update(self, release_info: dict[str, Any]) -> None:
        """Handle release info update from coordinator."""
        self._attr_latest_version = release_info.get("version")
        self._attr_release_url = release_info.get("release_url")
        self._attr_release_summary = release_info.get("release_summary")
        self._release_notes = release_info.get("release_notes")
        self.async_write_ha_state()

    @callback
    def _on_state_callback(self, version: str) -> None:
        """Update the version."""
        new_version = _parse_installed_version(version)

        # Check for update timeout
        if self._update_in_progress and self._update_started:
            if dt_util.utcnow() - self._update_started > UPDATE_TIMEOUT:
                _LOGGER.warning(
                    "Firmware update timed out after %s", UPDATE_TIMEOUT,
                )
                self._update_in_progress = False
                self._suppress_availability_updates = False
                self._version_before_update = None
                self._update_started = None

        # Check if update just completed (device came back with new version)
        if self._update_in_progress:
            if new_version and new_version != self._version_before_update:
                # Update completed successfully - version changed
                _LOGGER.info(
                    "Tasmota firmware update completed: %s -> %s",
                    self._version_before_update,
                    new_version,
                )
                self._update_in_progress = False
                self._suppress_availability_updates = False
                self._version_before_update = None
                self._update_started = None
            elif new_version:
                # Device came back but version same - update might have failed or was same version
                _LOGGER.debug(
                    "Device back online after update, version: %s",
                    new_version,
                )
                self._update_in_progress = False
                self._suppress_availability_updates = False
                self._version_before_update = None
                self._update_started = None

        self._attr_installed_version = new_version
        self.async_write_ha_state()

    async def async_install(
        self, version: str | None, backup: bool, **kwargs: Any
    ) -> None:
        """Install an update with staged upgrade support for old firmware."""
        # Get the appropriate upgrade target and URL
        next_target, url = self._get_next_upgrade_target()

        if url is None and next_target:
            # Very old firmware - cannot auto-upgrade
            _LOGGER.error(
                "Cannot auto-upgrade from version %s - manual upgrade to at least %s required",
                self._attr_installed_version,
                next_target,
            )
            return

        if next_target and next_target != self._attr_latest_version:
            _LOGGER.info(
                "Staged upgrade: updating from %s to intermediate version %s",
                self._attr_installed_version,
                next_target,
            )

        # Store current version to detect completion
        self._version_before_update = self._attr_installed_version
        self._update_in_progress = True
        self._suppress_availability_updates = True
        self._update_started = dt_util.utcnow()
        self.async_write_ha_state()

        _LOGGER.info(
            "Starting Tasmota firmware update from version %s (target: %s)",
            self._version_before_update,
            next_target or "latest",
        )

        # Update firmware with the appropriate URL
        # If url is provided, use it; otherwise use None for default OTA URL
        await self._tasmota_entity.update_firmware(url)

        # Note: The update process is async on the device side.
        # The device will reboot and come back with the new firmware.
        # _on_state_callback will detect when the device returns with the new version.
