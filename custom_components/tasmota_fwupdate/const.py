"""Constants used by multiple Tasmota modules."""

from homeassistant.const import Platform

CONF_DISCOVERY_PREFIX = "discovery_prefix"

DATA_REMOVE_DISCOVER_COMPONENT = "tasmota_fwupdate_discover_{}"
DATA_UNSUB = "tasmota_fwupdate_subscriptions"

DEFAULT_PREFIX = "tasmota/discovery"

DOMAIN = "tasmota_fwupdate"

PLATFORMS = [
    Platform.UPDATE,
]

TASMOTA_EVENT = "tasmota_fwupdate_event"
