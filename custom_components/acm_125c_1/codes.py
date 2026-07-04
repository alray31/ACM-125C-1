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

Verified: the "Pair", "On/Off", and the 8 named "Color" preset codes all
work correctly using this encoding (confirmed against the real light).

IMPORTANT NOTE ON THE COLOR WHEEL FORMAT
-----------------------------------------
An early version of this module built continuous wheel codes as 25 bits
(a 17-bit prefix "11111101001001100" + a 7-bit field "64 + color_index" +
end bit), reverse-engineered from two raw captures of the color wheel at
its extremes. Those 25-bit codes never worked reliably on the real light.

While debugging, the 8 named "Color" presets below (from the ORIGINAL,
working firmware) turned out to encode the exact same color_index values
(0-63) - but as 24-bit codes: a DIFFERENT 17-bit prefix
"11111010010011001" + a plain 6-bit color_index (no "+64" offset) + end
bit. Reconstructing all 8 presets from color_index using this 24-bit
format reproduces them byte-for-byte; reconstructing them from the
25-bit format does NOT produce the same raw timings at all, even though
the color_index values themselves line up. In other words: the value
encoding (color_index 0-63) is shared, but the actual bit layout
transmitted for the continuous wheel matches the *24-bit* preset format,
not the original 25-bit guess. This module now builds all continuous
wheel codes using the proven 24-bit format.
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
        """Precompute the raw timings for this rc-switch code."""
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
# All codes below are 24-bit rc-switch strings, verified programmatically
# and (for Pair/On/Off) against the real light.

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

# Effects exposed through the light entity's native effect_list (everything
# in EFFECT_CODES except "Color" and "White", which are handled by the
# light's color wheel / white-mode controls instead of the effect list).
ANIMATION_EFFECTS: list[str] = [
    "Gradual",
    "Wave",
    "Jumping",
    "Fading",
    "Wave + Jumping",
]

# --- Color presets (VERIFIED, from the original working YAML) -------------
#
# These 8 named colors are known-good, standalone codes from the original
# firmware's "Color" select (no separate "Color" effect trigger needed
# first). Hue values for Red/Orange/Yellow/Green/Cyan/Blue are standard
# HSV; Purple/Pink are estimated by linear regression against the other 6
# (R^2 = 0.986) since there's no universally standard "hue" for those
# names. color_index is decoded from each code's 6-bit field (see the
# module docstring for the 24-bit format), and doubles as the calibration
# anchor for the continuous wheel interpolation below.
COLOR_PRESET_CODES: dict[str, str] = {
    "Red": "111110100100110011000101",
    "Orange": "111110100100110010111101",
    "Yellow": "111110100100110010110011",
    "Green": "111110100100110010011111",
    "Cyan": "111110100100110010010001",
    "Blue": "111110100100110010000111",
    "Purple": "111110100100110011100001",
    "Pink": "111110100100110011010101",
}

COLOR_PRESET_HUES: dict[str, float] = {
    "Red": 0.0,
    "Orange": 30.0,
    "Yellow": 60.0,
    "Green": 120.0,
    "Cyan": 180.0,
    "Blue": 240.0,
    "Purple": 252.3,
    "Pink": 296.6,
}

COLOR_PRESET_INDEX: dict[str, int] = {
    "Blue": 3,
    "Cyan": 8,
    "Green": 15,
    "Yellow": 25,
    "Orange": 30,
    "Red": 34,
    "Pink": 42,
    "Purple": 48,
}


def nearest_color_preset(hue_deg: float) -> str:
    """Return the name of the known-good preset closest to ``hue_deg``.

    Uses circular distance (0 deg and 360 deg are the same point). Not
    used by light.py anymore (see hue_to_color_index below), kept as a
    simpler/safer fallback option.
    """

    def circular_distance(a: float, b: float) -> float:
        diff = abs(a - b) % 360
        return min(diff, 360 - diff)

    return min(
        COLOR_PRESET_HUES,
        key=lambda name: circular_distance(hue_deg, COLOR_PRESET_HUES[name]),
    )


# --- Continuous color wheel encoding (24-bit format, see module docstring) -
#
# Structure (24 bits total, matching the 8 proven presets exactly):
#   - bits 8-24 (17 bits): constant prefix "11111010010011001"
#   - bits 2-7  (6 bits):  color_index, plain binary, MSB first (0-63)
#   - bit 1 (LSB): constant "1" (end bit)
COLOR_WHEEL_PREFIX = "11111010010011001"  # 17 bits, constant (matches the presets)
COLOR_WHEEL_STEPS = 64  # color_index range: 0..63


def color_wheel_code(color_index: int) -> str:
    """Build the 24-bit rc-switch code for a color wheel position.

    ``color_index`` must be 0..63. Verified to exactly reproduce all 8
    known preset codes when given their respective color_index.
    """
    if not 0 <= color_index < COLOR_WHEEL_STEPS:
        raise ValueError(f"color_index must be 0-{COLOR_WHEEL_STEPS - 1}, got {color_index}")
    return COLOR_WHEEL_PREFIX + format(color_index, "06b") + "1"


def color_wheel_command(color_index: int) -> PoolLightCommand:
    """Build the RF command for a given color wheel position."""
    return PoolLightCommand(color_wheel_code(color_index))


# --- Hue <-> color_index mapping, calibrated from the 8 real presets ------
#
# Piecewise-linear interpolation between the 8 verified (color_index, hue)
# anchors above, instead of a single global linear formula (which only
# reached R^2 = 0.986 against the real data, i.e. up to ~16 degrees off
# even at *known* points - not good enough to trust for 56 unverified
# in-between positions). This interpolation is *exact* at all 8 known
# anchors and only guesses (linearly, between the two nearest anchors)
# for everything else - in particular the largest gap, color_index 48
# (Purple) wrapping around to 3 (Blue), spans 19 unverified positions and
# should be treated with the least confidence.
def _build_anchor_points() -> list[tuple[int, float]]:
    """Build a sorted, "unwrapped" (index, hue) list plus a closing point.

    Hue decreases monotonically as index increases (confirmed direction:
    clockwise on the physical wheel = decreasing hue), so each anchor's
    hue is unwrapped (360 subtracted as needed) to keep that going, and a
    final synthetic point closes the loop at index + 64.
    """
    sorted_names = sorted(COLOR_PRESET_INDEX, key=lambda n: COLOR_PRESET_INDEX[n])
    points: list[tuple[int, float]] = []
    prev_hue: float | None = None
    for name in sorted_names:
        index = COLOR_PRESET_INDEX[name]
        hue = COLOR_PRESET_HUES[name]
        if prev_hue is not None:
            while hue > prev_hue:
                hue -= 360
        points.append((index, hue))
        prev_hue = hue
    first_index, first_hue = points[0]
    points.append((first_index + COLOR_WHEEL_STEPS, first_hue - 360))
    return points


_ANCHOR_POINTS = _build_anchor_points()
_FIRST_ANCHOR_INDEX = _ANCHOR_POINTS[0][0]


def index_to_hue(color_index: int) -> float:
    """Map a wheel color_index (0-63) to its calibrated real-world hue."""
    index = color_index % COLOR_WHEEL_STEPS
    x = index if index >= _FIRST_ANCHOR_INDEX else index + COLOR_WHEEL_STEPS
    for (x0, y0), (x1, y1) in zip(_ANCHOR_POINTS, _ANCHOR_POINTS[1:]):
        if x0 <= x <= x1:
            t = 0.0 if x1 == x0 else (x - x0) / (x1 - x0)
            return (y0 + t * (y1 - y0)) % 360
    raise ValueError(color_index)  # pragma: no cover - unreachable, loop covers full range


def hue_to_color_index(hue_deg: float) -> int:
    """Map a standard HSV hue (0-360) to the wheel's color_index (0-63).

    Inverse of index_to_hue(), via the same piecewise-linear calibration.
    """
    candidates: list[float] = []
    for (x0, y0), (x1, y1) in zip(_ANCHOR_POINTS, _ANCHOR_POINTS[1:]):
        lo, hi = min(y0, y1), max(y0, y1)
        for h in (hue_deg, hue_deg - 360, hue_deg + 360):
            if lo - 1e-9 <= h <= hi + 1e-9:
                t = 0.0 if y1 == y0 else (h - y0) / (y1 - y0)
                candidates.append((x0 + t * (x1 - x0)) % COLOR_WHEEL_STEPS)
    if not candidates:
        # Shouldn't happen (the anchors span the full circle), but fall
        # back to the nearest preset rather than raising.
        return COLOR_PRESET_INDEX[nearest_color_preset(hue_deg)]

    def _round_trip_error(index: float) -> float:
        diff = abs(index_to_hue(round(index) % COLOR_WHEEL_STEPS) - hue_deg) % 360
        return min(diff, 360 - diff)

    best = min(candidates, key=_round_trip_error)
    return round(best) % COLOR_WHEEL_STEPS


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

COLOR_PRESET_COMMANDS: dict[str, PoolLightCommand] = {
    option: PoolLightCommand(code) for option, code in COLOR_PRESET_CODES.items()
}

# Precompute all 64 wheel-position commands once at import time (cheap:
# same cost as the other ~34 pre-built commands).
COLOR_WHEEL_COMMANDS: list[PoolLightCommand] = [
    color_wheel_command(i) for i in range(COLOR_WHEEL_STEPS)
]
