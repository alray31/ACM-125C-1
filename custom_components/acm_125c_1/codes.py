"""RF codes for the ACM-125C-1 pool light remote.

All the button/select codes below are copied verbatim from the original
ESPHome YAML firmware (the 24-bit strings passed to
``remote_transmitter.transmit_rc_switch_raw``). This module re-implements
that rc-switch style bit encoding in Python so we can produce the raw
microsecond mark/space timings the new Home Assistant ``radio_frequency``
platform expects from ``RadioFrequencyCommand.get_raw_timings()``.

Encoding assumptions (matching ESPHome's rc_switch protocol defaults,
overridden only where the original YAML overrode them):

- pulse_length: 260 us  (overridden in the YAML)
- sync:  (3, 1)          (overridden in the YAML: high=3x, low=1x pulse_length)
- zero:  (1, 3)          (ESPHome default, not overridden)
- one:   (3, 1)          (ESPHome default, not overridden)
- inverted: False        (ESPHome default, not overridden)
- Each transmission is repeated 10 times with a 7510 us pause between
  repeats, exactly like the original ``repeat: {times: 10, wait_time:
  7510us}`` block.

IMPORTANT: verify this against your existing, known-working remote before
relying on it. The "Pair" and "On/Off" buttons are the cheapest way to
check: if the pool light responds exactly like it did with the ESPHome
version, the encoding is right. If nothing happens or behavior is
inconsistent, the most likely culprits are the sync/zero/one ratios above.
"""

from __future__ import annotations

from rf_protocols import ModulationType, RadioFrequencyCommand

from .const import (
    FREQUENCY_HZ,
    ONE,
    PULSE_LENGTH_US,
    REPEAT_TIMES,
    REPEAT_WAIT_US,
    SYNC,
    ZERO,
)


def _encode_cycle(
    code: str,
    pulse_length: int,
    sync: tuple[int, int],
    zero: tuple[int, int],
    one: tuple[int, int],
) -> list[int]:
    """Encode a single sync+bits cycle as signed mark/space microseconds."""
    timings: list[int] = []

    def _add(pair: tuple[int, int]) -> None:
        high, low = pair
        timings.append(high * pulse_length)
        timings.append(-(low * pulse_length))

    _add(sync)
    for bit in code:
        _add(one if bit == "1" else zero)
    return timings


def encode_rc_switch(
    code: str,
    *,
    pulse_length: int = PULSE_LENGTH_US,
    sync: tuple[int, int] = SYNC,
    zero: tuple[int, int] = ZERO,
    one: tuple[int, int] = ONE,
    repeat_times: int = REPEAT_TIMES,
    repeat_wait_us: int = REPEAT_WAIT_US,
) -> list[int]:
    """Build the full raw timings array for `repeat_times` transmissions.

    Returns alternating signed microsecond values (positive = mark/high,
    negative = space/low), which is the format ``RadioFrequencyCommand.
    get_raw_timings()`` must return.
    """
    raw: list[int] = []
    for i in range(repeat_times):
        cycle = _encode_cycle(code, pulse_length, sync, zero, one)
        if i == 0:
            raw = cycle
        else:
            # Merge the inter-repeat gap into the previous trailing space
            # so the array keeps strictly alternating signs.
            raw[-1] -= repeat_wait_us
            raw += cycle
    return raw


class PoolLightCommand(RadioFrequencyCommand):
    """A single RF command for the pool light remote."""

    def __init__(self, code: str) -> None:
        """Precompute the raw timings for this 24-bit rc-switch code."""
        super().__init__(
            frequency=FREQUENCY_HZ,
            modulation=ModulationType.OOK,
            # The 10x repeat + inter-repeat gap is already baked into the
            # raw timings below, so we don't ask the transmitter to repeat
            # again on top of that.
            repeat_count=0,
        )
        self._raw_timings = encode_rc_switch(code)

    def get_raw_timings(self) -> list[int]:
        """Return the precomputed raw timings."""
        return self._raw_timings


# --- Codes copied from the original ESPHome YAML -------------------------
# All codes below are 24-bit rc-switch strings, verified programmatically.

PAIR_CODE = "111110100100110001100011"
ON_CODE = "111110100100110000001111"
OFF_CODE = "111110100100110001110001"

INTENSITY_CODES: dict[str, str] = {
    "1": "111110100100110110001111",
    "2": "111110100100110110011111",
    "3": "111110100100110110101111",
    "4": "111110100100110110111111",
    "5": "111110100100110111001111",
    "6": "111110100100110111011111",
    "7": "111110100100110111101111",
    "8": "111110100100110111111111",
}

EFFECT_CODES: dict[str, str] = {
    "Gradual": "111110100100110000011101",
    "Wave": "111110100100110000101011",
    "Jumping": "111110100100110000111001",
    "Fading": "111110100100110001000111",
    "Wave + Jumping": "111110100100110001010101",
    "White": "111110100100110000010011",
    "Color": "111110100100110001101101",
}

COLOR_CODES: dict[str, str] = {
    "Purple": "111110100100110011100001",
    "Blue": "111110100100110010000111",
    "Cyan": "111110100100110010010001",
    "Green": "111110100100110010011111",
    "Yellow": "111110100100110010110011",
    "Orange": "111110100100110010111101",
    "Red": "111110100100110011000101",
    "Pink": "111110100100110011010101",
}

# --- Pre-built commands ---------------------------------------------------

PAIR_COMMAND = PoolLightCommand(PAIR_CODE)
ON_COMMAND = PoolLightCommand(ON_CODE)
OFF_COMMAND = PoolLightCommand(OFF_CODE)

INTENSITY_COMMANDS: dict[str, PoolLightCommand] = {
    option: PoolLightCommand(code) for option, code in INTENSITY_CODES.items()
}

EFFECT_COMMANDS: dict[str, PoolLightCommand] = {
    option: PoolLightCommand(code) for option, code in EFFECT_CODES.items()
}

COLOR_COMMANDS: dict[str, PoolLightCommand] = {
    option: PoolLightCommand(code) for option, code in COLOR_CODES.items()
}
