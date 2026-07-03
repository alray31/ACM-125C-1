"""Pairing button for the ACM-125C-1 pool light remote."""

from __future__ import annotations

from homeassistant.components import radio_frequency
from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import Acm125c1ConfigEntry
from .codes import PAIR_COMMAND
from .const import DOMAIN

PAIR_DESCRIPTION = ButtonEntityDescription(
    key="pair",
    translation_key="pair",
    name="Pair",
    icon="mdi:signal-variant",
    entity_category=EntityCategory.CONFIG,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: Acm125c1ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the pairing button."""
    async_add_entities([Acm125c1PairButton(entry)])


class Acm125c1PairButton(ButtonEntity):
    """Sends the pairing code to the pool light."""

    entity_description = PAIR_DESCRIPTION
    _attr_has_entity_name = True

    def __init__(self, entry: Acm125c1ConfigEntry) -> None:
        """Initialize the button."""
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_pair"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "ACM",
            "model": "125C-1 (virtual RF remote)",
        }

    async def async_press(self) -> None:
        """Send the pairing code."""
        await radio_frequency.async_send_command(
            self.hass,
            self._entry.runtime_data.transmitter_entity_id,
            PAIR_COMMAND,
        )
