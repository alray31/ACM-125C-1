"""Constants for the ACM-125C-1 (pool light RF) integration."""

from __future__ import annotations

DOMAIN = "acm_125c_1"

# The pool light remote transmits on 433.92 MHz using on-off keying (OOK).
FREQUENCY_HZ = 433_920_000

CONF_TRANSMITTER_ENTITY_ID = "transmitter_entity_id"

# --- rc-switch style protocol parameters, copied from the original ---
# --- ESPHome YAML (remote_transmitter.transmit_rc_switch_raw).      ---
PULSE_LENGTH_US = 260
SYNC = (3, 1)  # (high, low) multiples of PULSE_LENGTH_US
ZERO = (1, 3)  # ESPHome default for rc_switch protocol "0" bit
ONE = (3, 1)  # ESPHome default for rc_switch protocol "1" bit
REPEAT_TIMES = 10
REPEAT_WAIT_US = 7510
