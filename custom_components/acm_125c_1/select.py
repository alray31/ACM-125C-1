"""Intensity/effect-speed, effect and color selects for the pool light."""

from __future__ import annotations

from homeassistant.components import radio_frequency
from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from . import Acm125c1ConfigEntry
from .codes import COLOR_COMMANDS, EFFECT_COMMANDS, INTENSITY_COMMANDS
from .const import DOMAIN

CHOOSE = "Choose"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: Acm125c1ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the select entities."""
    async_add_entities(
        [
            Acm125c1Select(
                entry,
                key="intensity_effect_speed",
                name="Light intensity or Effect Speed",
                icon="mdi:remote",
                commands=INTENSITY_COMMANDS,
            ),
            Acm125c1Select(
                entry,
                key="effect",
                name="Effect",
                icon="mdi:auto-mode",
                commands=EFFECT_COMMANDS,
            ),
            Acm125c1Select(
                entry,
                key="color",
                name="Color",
                icon="mdi:palette",
                commands=COLOR_COMMANDS,
            ),
        ]
    )


class Acm125c1Select(SelectEntity, RestoreEntity):
    """Generic "pick an option, send the matching RF code" select.

    Same one-way "assumed state" caveat as the on/off switch: the light
    can't report back what it's actually doing.
    """

    _attr_has_entity_name = True
    _attr_assumed_state = True

    def __init__(
        self,
        entry: Acm125c1ConfigEntry,
        *,
        key: str,
        name: str,
        icon: str,
        commands: dict[str, object],
    ) -> None:
        """Initialize the select."""
        self.entity_description = SelectEntityDescription(
            key=key, translation_key=key, name=name, icon=icon
        )
        self._entry = entry
        self._commands = commands
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "ACM",
            "model": "125C-1 (virtual RF remote)",
        }
        self._attr_options = [CHOOSE, *commands.keys()]
        self._attr_current_option = CHOOSE

    async def async_added_to_hass(self) -> None:
        """Restore the previous selection."""
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is not None:
            if last_state.state in self._attr_options:
                self._attr_current_option = last_state.state

    async def async_select_option(self, option: str) -> None:
        """Send the RF code for the selected option."""
        if option == CHOOSE:
            self._attr_current_option = option
            self.async_write_ha_state()
            return

        command = self._commands[option]
        await radio_frequency.async_send_command(
            self.hass,
            self._entry.runtime_data.transmitter_entity_id,
            command,
        )
        self._attr_current_option = option
        self.async_write_ha_state()
