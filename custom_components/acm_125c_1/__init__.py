"""The ACM-125C-1 (pool light RF) integration.

This integration is a "consumer" of Home Assistant's ``radio_frequency``
entity platform (introduced in 2026.5): it doesn't talk to any hardware
itself. Instead, at setup it is given the entity ID of an RF transmitter
(for example, an ESPHome device exposing a ``radio_frequency`` entity via
the ``ir_rf_proxy`` component) and it sends pre-encoded RF commands
through that transmitter using ``radio_frequency.async_send_command``.
"""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import CONF_TRANSMITTER_ENTITY_ID

PLATFORMS: list[Platform] = [Platform.BUTTON, Platform.LIGHT]


@dataclass
class Acm125c1RuntimeData:
    """Runtime data stored on the config entry."""

    transmitter_entity_id: str


Acm125c1ConfigEntry = ConfigEntry[Acm125c1RuntimeData]


async def async_setup_entry(hass: HomeAssistant, entry: Acm125c1ConfigEntry) -> bool:
    """Set up ACM-125C-1 from a config entry."""
    entry.runtime_data = Acm125c1RuntimeData(
        transmitter_entity_id=entry.data[CONF_TRANSMITTER_ENTITY_ID]
    )
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: Acm125c1ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
