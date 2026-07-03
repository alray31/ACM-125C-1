"""Config flow for ACM-125C-1 (pool light RF)."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from rf_protocols import ModulationType

from homeassistant.components import radio_frequency
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import selector

from .const import CONF_TRANSMITTER_ENTITY_ID, DOMAIN, FREQUENCY_HZ


class Acm125c1ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ACM-125C-1."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Let the user pick which RF transmitter to use."""
        try:
            transmitters = radio_frequency.async_get_transmitters(
                self.hass,
                frequency=FREQUENCY_HZ,
                modulation=ModulationType.OOK,
            )
        except HomeAssistantError:
            return self.async_abort(reason="no_transmitters")

        if not transmitters:
            return self.async_abort(reason="no_compatible_transmitters")

        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id("pool_light_ecumoir")
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title="Éclairage écumoire (piscine)",
                data={CONF_TRANSMITTER_ENTITY_ID: user_input[CONF_TRANSMITTER_ENTITY_ID]},
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_TRANSMITTER_ENTITY_ID): selector.selector(
                    {
                        "entity": {
                            "include_entities": transmitters,
                        }
                    }
                ),
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )
