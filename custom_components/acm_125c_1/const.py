"""Constants for the ACM-125C-1 (pool light RF) integration."""

from __future__ import annotations

DOMAIN = "acm_125c_1"

# The pool light remote transmits on 433.92 MHz using on-off keying (OOK).
FREQUENCY_HZ = 433_920_000

CONF_TRANSMITTER_ENTITY_ID = "transmitter_entity_id"

# --- Device info shown in Settings > Devices for every entity ---
MANUFACTURER = "alray31"
MODEL = "ACM-125C-1 (virtual RF remote)"


def build_device_info(entry) -> dict:
    """Build the shared device_info dict used by every platform.

    Defined once here so button.py / light.py can't drift out of sync
    with each other.
    """
    return {
        "identifiers": {(DOMAIN, entry.entry_id)},
        "name": entry.title,
        "manufacturer": MANUFACTURER,
        "model": MODEL,
    }


# --- rc-switch style protocol parameters, copied from the original ---
# --- ESPHome YAML (remote_transmitter.transmit_rc_switch_raw).      ---
PULSE_LENGTH_US = 260
SYNC = (3, 1)  # (high, low) multiples of PULSE_LENGTH_US
ZERO = (1, 3)  # ESPHome default for rc_switch protocol "0" bit
ONE = (3, 1)  # ESPHome default for rc_switch protocol "1" bit
REPEAT_TIMES = 10
REPEAT_WAIT_US = 7510

# --- Light entity behavior --------------------------------------------

# Delay between sending "effect color" and the specific wheel-position
# code, so the receiver has time to register both RF transmissions as
# separate commands rather than one garbled/overlapping burst.
#
# IMPORTANT: each command already repeats 10x internally and takes ~328ms
# to fully transmit over the air (measured: sum of abs(get_raw_timings())
# in microseconds). ESPHome's remote_transmitter defaults to
# non_blocking: true, so our `await` on sending a command likely returns
# as soon as the ESP acknowledges the request, NOT once the physical
# burst has actually finished - meaning this delay must be LONGER than
# that ~328ms burst duration (with margin), or the second command's RF
# can start before the first one's 10 repeats have actually finished
# going out over the air. 0.3s was too short (shorter than the burst
# itself); bumped to 1.0s.
COLOR_COMMAND_DELAY_S = 1.0

# --- Color wheel calibration --------------------------------------------
#
# Calibrated from the physical wheel photo/description: clockwise, dark
# blue at 0 deg (color_index 0), cyan-green at 90 deg (index 16), yellow
# at 180 deg (index 32), red-pink at 270 deg (index 48). That's a clean
# linear relationship: hue = (240 - physical_angle) mod 360, i.e.
# increasing color_index moves opposite to increasing standard HSV hue.
COLOR_WHEEL_HUE_AT_INDEX_0 = 240.0  # degrees (dark blue, at color_index 0)
COLOR_WHEEL_DIRECTION = -1  # -1 = increasing index -> decreasing hue (clockwise on the physical wheel)
