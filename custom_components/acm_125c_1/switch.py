"""On/off switch for the ACM-125C-1 pool light remote."""

from __future__ import annotations

from typing import Any

from homeassistant.components import radio_frequency
from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from . import Acm125c1ConfigEntry
from .codes import OFF_COMMAND, ON_COMMAND
from .const import DOMAIN

SWITCH_DESCRIPTION = SwitchEntityDescription(
    key="on_off",
    translation_key="on_off",
    name="On/Off",
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: Acm125c1ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the on/off switch."""
    async_add_entities([Acm125c1OnOffSwitch(entry)])


class Acm125c1OnOffSwitch(SwitchEntity, RestoreEntity):
    """Pool light on/off switch.

    RF is a one-way, "fire and forget" transmission: there's no
    confirmation the light actually toggled. This entity therefore uses
    the "assumed state" pattern (same as Home Assistant's own
    Honeywell String Lights integration): the state is whatever we last
    told the light to do, and it's restored across HA restarts.
    """

    entity_description = SWITCH_DESCRIPTION
    _attr_has_entity_name = True
    _attr_assumed_state = True

    def __init__(self, entry: Acm125c1ConfigEntry) -> None:
        """Initialize the switch."""
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_on_off"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "ACM",
            "model": "125C-1 (virtual RF remote)",
        }
        self._attr_is_on = False

    async def async_added_to_hass(self) -> None:
        """Restore the previous state."""
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is not None:
            self._attr_is_on = last_state.state == "on"

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the pool light on."""
        await radio_frequency.async_send_command(
            self.hass,
            self._entry.runtime_data.transmitter_entity_id,
            ON_COMMAND,
        )
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the pool light off."""
        await radio_frequency.async_send_command(
            self.hass,
            self._entry.runtime_data.transmitter_entity_id,
            OFF_COMMAND,
        )
        self._attr_is_on = False
        self.async_write_ha_state()
