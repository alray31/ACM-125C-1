"""Light entity for the ACM-125C-1 pool light remote.

Replaces the old On/Off switch + Color/Effect/Intensity selects with a
single light entity that maps onto Home Assistant's native color wheel,
brightness slider, white-mode control, and effect list:

- The color wheel sends "effect color" followed (after a short delay) by
  the RF code for the wheel position matching the picked hue.
- Picking "white" sends the single "effect white" RF code.
- The brightness slider sends one of the 8 "intensity or effect speed"
  codes. The same physical remote buttons mean "light intensity" when the
  light is in color/white mode, and "effect speed" when an animation
  effect (see below) is active - Home Assistant's light card always
  calls the slider "Brightness" (this isn't something entities can
  override), so that dual meaning is documented here and in the README
  instead.
- The other animation effects (Gradual, Wave, Jumping, Fading, Wave +
  Jumping) are exposed through the light's native effect list.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.components import radio_frequency
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_EFFECT,
    ATTR_HS_COLOR,
    ATTR_WHITE,
    ColorMode,
    LightEntity,
    LightEntityDescription,
    LightEntityFeature,
)
from homeassistant.const import STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from . import Acm125c1ConfigEntry
from .codes import (
    ANIMATION_EFFECTS,
    COLOR_WHEEL_COMMANDS,
    COLOR_WHEEL_STEPS,
    EFFECT_COMMANDS,
    INTENSITY_COMMANDS,
    OFF_COMMAND,
    ON_COMMAND,
)
from .const import COLOR_COMMAND_DELAY_S, COLOR_WHEEL_DIRECTION, COLOR_WHEEL_HUE_AT_INDEX_0, build_device_info

_LOGGER = logging.getLogger(__name__)

BRIGHTNESS_LEVELS = 8


def hue_to_color_index(hue_deg: float) -> int:
    """Map a standard HSV hue (0-360) to the wheel's color_index (0-63).

    Calibrated against the physical wheel: clockwise, dark blue at
    color_index 0 (hue 240), cyan-green at index 16 (hue 150), yellow at
    index 32 (hue 60), red-pink at index 48 (hue 330). See const.py
    COLOR_WHEEL_HUE_AT_INDEX_0 / COLOR_WHEEL_DIRECTION.
    """
    frac = ((hue_deg - COLOR_WHEEL_HUE_AT_INDEX_0) / 360.0) * COLOR_WHEEL_DIRECTION
    frac %= 1.0
    # The wheel has COLOR_WHEEL_STEPS positions spaced evenly around the
    # full circle, so divide by STEPS (not STEPS - 1) and wrap the result -
    # otherwise the mapping very slightly drifts and the last position
    # never gets reached.
    return round(frac * COLOR_WHEEL_STEPS) % COLOR_WHEEL_STEPS


def brightness_to_level(brightness: int) -> str:
    """Map HA brightness (0-255) to the nearest RF intensity level (1-8)."""
    pct = brightness / 255
    level = round(pct * BRIGHTNESS_LEVELS)
    level = max(1, min(BRIGHTNESS_LEVELS, level))
    return str(level)


def level_to_brightness(level: str) -> int:
    """Map an RF intensity level (1-8) back to HA brightness (0-255)."""
    return round(int(level) / BRIGHTNESS_LEVELS * 255)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: Acm125c1ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the light entity."""
    async_add_entities([Acm125c1Light(entry)])


class Acm125c1Light(LightEntity, RestoreEntity):
    """The pool light, as a single Home Assistant light entity.

    Same one-way "assumed state" caveat as the rest of this integration:
    RF is fire-and-forget, so state is whatever we last told the light to
    do, restored across HA restarts.
    """

    _attr_has_entity_name = True
    _attr_assumed_state = True
    _attr_should_poll = False
    _attr_supported_color_modes = {ColorMode.HS, ColorMode.WHITE}
    _attr_supported_features = LightEntityFeature.EFFECT
    _attr_effect_list = ANIMATION_EFFECTS

    def __init__(self, entry: Acm125c1ConfigEntry) -> None:
        """Initialize the light."""
        self.entity_description = LightEntityDescription(key="light")
        # This is the device's single/primary entity: no name suffix, it
        # just takes the device's own name (e.g. "ACM-125C-1 Pool Lights
        # Remote"), same convention as most single-entity HA integrations.
        self._attr_name = None
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_light"
        self._attr_device_info = build_device_info(entry)
        self._attr_is_on = False
        self._attr_brightness = level_to_brightness("8")
        self._attr_hs_color = (COLOR_WHEEL_HUE_AT_INDEX_0, 100.0)
        self._attr_color_mode = ColorMode.HS
        self._attr_effect = None

    async def async_added_to_hass(self) -> None:
        """Restore the previous state."""
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is None:
            return

        self._attr_is_on = last_state.state == STATE_ON
        attrs = last_state.attributes

        if (brightness := attrs.get(ATTR_BRIGHTNESS)) is not None:
            self._attr_brightness = brightness
        if (hs_color := attrs.get("hs_color")) is not None:
            self._attr_hs_color = tuple(hs_color)
        if (color_mode := attrs.get("color_mode")) is not None:
            with_valid_mode = {m.value for m in (ColorMode.HS, ColorMode.WHITE)}
            if color_mode in with_valid_mode:
                self._attr_color_mode = ColorMode(color_mode)
        if (effect := attrs.get(ATTR_EFFECT)) is not None and effect in ANIMATION_EFFECTS:
            self._attr_effect = effect

    async def _send(self, command) -> None:
        """Send one RF command through the configured transmitter.

        This integration is "assumed state" (RF is one-way, fire-and-
        forget): we report whatever we *told* the light to do, not
        something we can confirm. So if the actual RF transmission call
        raises, we log it clearly (visible in Settings > System > Logs)
        instead of letting the exception abort the rest of async_turn_on/
        async_turn_off - otherwise a single failed send silently prevents
        `is_on` from ever being updated, which looks exactly like "the
        button does nothing".
        """
        try:
            await radio_frequency.async_send_command(
                self.hass,
                self._entry.runtime_data.transmitter_entity_id,
                command,
            )
        except Exception:
            _LOGGER.exception(
                "Failed to send RF command via transmitter %s",
                self._entry.runtime_data.transmitter_entity_id,
            )

    async def _ensure_on(self) -> None:
        """Send the base ON code if the light isn't already on."""
        if not self._attr_is_on:
            await self._send(ON_COMMAND)
            self._attr_is_on = True

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the light, applying whichever attributes were given."""
        _LOGGER.debug("async_turn_on called with kwargs=%s (was is_on=%s)", kwargs, self._attr_is_on)
        await self._ensure_on()

        if ATTR_HS_COLOR in kwargs:
            hue, saturation = kwargs[ATTR_HS_COLOR]
            color_index = hue_to_color_index(hue)
            _LOGGER.debug(
                "Color wheel: received hue=%.1f saturation=%.1f -> color_index=%d",
                hue,
                saturation,
                color_index,
            )
            await self._send(EFFECT_COMMANDS["Color"])
            await asyncio.sleep(COLOR_COMMAND_DELAY_S)
            await self._send(COLOR_WHEEL_COMMANDS[color_index])
            self._attr_hs_color = (hue, saturation)
            self._attr_color_mode = ColorMode.HS
            self._attr_effect = None

        if ATTR_EFFECT in kwargs:
            effect = kwargs[ATTR_EFFECT]
            await self._send(EFFECT_COMMANDS[effect])
            self._attr_effect = effect

        # White mode: HA passes the desired brightness via `white`, not
        # `brightness`, when switching a HS/WHITE light into white mode.
        brightness = kwargs.get(ATTR_BRIGHTNESS)
        if ATTR_WHITE in kwargs:
            await self._send(EFFECT_COMMANDS["White"])
            self._attr_color_mode = ColorMode.WHITE
            self._attr_effect = None
            brightness = kwargs[ATTR_WHITE]

        if brightness is not None:
            level = brightness_to_level(brightness)
            _LOGGER.debug("Brightness: received %s -> intensity level %s", brightness, level)
            await self._send(INTENSITY_COMMANDS[level])
            self._attr_brightness = level_to_brightness(level)

        self.async_write_ha_state()
        _LOGGER.debug("async_turn_on done, is_on=%s state written", self._attr_is_on)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the light."""
        _LOGGER.debug("async_turn_off called with kwargs=%s", kwargs)
        await self._send(OFF_COMMAND)
        self._attr_is_on = False
        self.async_write_ha_state()
