# ACM-125C-1 for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/v/release/alray31/ACM-125C-1)](https://github.com/alray31/ACM-125C-1/releases)

Control an **ACM-125**, **ACM-125C**, **ACM-197C** or **ACM-198C** RF (433.92 MHz) pool light directly from Home Assistant, with a real `light` entity — color wheel, brightness, white mode, and effects — instead of the physical **ACM-125C-1** RF Remote.

This integration doesn't touch any hardware itself. It's a *consumer* of Home Assistant's [`radio_frequency`](https://www.home-assistant.io/integrations/radio_frequency/) radio frequency platform: it sends RF commands through whatever `radio_frequency` proxy transmitter you already have set up (typically an ESPHome or Broadlink device), the same way built-in integrations like *Honeywell String Lights* or *Novy Cooker Hood* do.
Refer to https://www.home-assistant.io/integrations/radio_frequency/


## Requirements

- Home Assistant **2026.5** or newer (introduced the `radio_frequency` platform).
- An RF transmitter exposing a `radio_frequency` entity — in practice, an ESPHome device running the [`ir_rf_proxy`](https://esphome.io/components/ir_rf_proxy/) component's `radio_frequency` platform, pointed at a 433.92 MHz transmitter. See ESPHome's [Radio Frequency Component](https://esphome.io/components/radio_frequency/) docs for the underlying entity type.
- HACS.

This integration does **not** include or manage the ESPHome firmware — it only talks to whichever `radio_frequency` transmitter entity you already have configured in Home Assistant.
refer to Esphome Radio Frequency platform: https://esphome.io/components/ir_rf_proxy/#radio-frequency-platform for configuring an ESPHome radio frequency proxy.

## Installation

### HACS (recommended)

1. Make sure your ESPHome device (or other supported RF transmitter) already exposes a `radio_frequency` entity in Home Assistant.
2. In HACS, add this repository as a custom repository (category: *Integration*), or install it directly if it's been added to the HACS default store.
3. Restart Home Assistant.
4. Go to **Settings → Devices & services → Add integration → ACM-125C-1**.
5. Pick the `radio_frequency` transmitter entity to use. Only transmitters compatible with 433.92 MHz / OOK modulation are shown.

### Manual

Copy `custom_components/acm_125c_1` into your Home Assistant `config/custom_components` directory and restart.

## What you get

- `light.<name>` — one light entity that covers everything: on/off, color, brightness, white mode, and effects.

<img width="670" height="754" alt="image" src="https://github.com/user-attachments/assets/af205313-e27f-4197-9a14-02f51381ed28" />




- `button.<name>_pair` — sends the remote's pairing code, for pairing the light to the RF proxy the same way you'd pair the original remote.

<img width="513" height="223" alt="image" src="https://github.com/user-attachments/assets/91de6f3e-454e-4b17-83ec-bcc851d41c00" />


There's no separate switch or select entities: everything the original remote's buttons and wheel could do is exposed through the single light entity, using Home Assistant's native light controls. THe only exception is the "Pair" button which is outside the light entity.

## How it mirrors the original remote

The goal is to make the *native* Home Assistant light controls behave the way the original ACM-125C-1 remote's buttons and wheel do — not to bolt on a set of custom controls that happen to send the right RF codes.

### Color wheel → nearest of 64 real wheel positions

The physical remote's color wheel isn't infinitely precise: it has exactly **64 discrete positions** around the full 360°. When you pick a color on Home Assistant's built-in color wheel, the integration converts your pick to the closest one of those 64 real wheel positions and sends that single RF code — you get the same resolution the original remote's wheel offers, no more, no less. The reported color in Home Assistant reflects the position that was actually sent, not your exact pick, so what you see matches what the light is actually doing.

<img width="675" height="754" alt="image" src="https://github.com/user-attachments/assets/34138edb-3fa9-4d2c-9467-11866aaa01aa" />


### Brightness slider → intensity *or* effect speed, depending on mode

The physical remote has one set of `+`/`-` buttons that mean two different things depending on what the light is currently doing:

- While the light is in **color** or **white** mode, they adjust **light intensity**.
- While an **animation effect** is running (see below), they adjust the **effect's speed**.

Home Assistant's light card always labels its brightness slider "Brightness" — that label can't be changed per-entity — but the slider sends the exact same underlying RF command either way, so it transparently does the right thing: turn the slider while looking at a solid color and it's intensity; turn it while an effect is animating and it's speed.

The physical remote offer 8 selection of speed and brightness. You get exactly the same resolution from the home assistant brightness slider despite the slider being ajustable from 0 to 100%. The actual % selection will be converted to the closest availabe speed / brightness (8 plevel each at a 12.5% increment)

<img width="663" height="761" alt="image" src="https://github.com/user-attachments/assets/a18bc17e-3d70-4e2e-bb50-eb919ffb7c1b" />


### White → its own button in the light entity, not a wheel position

Home Assistant lights that support both **HS color** and **white** expose white as its own dedicated control (a "W" segment/button next to the color wheel), separate from the color wheel itself. That maps directly onto the original remote, which also has a distinct button (botton labaled "C" on the physical remote) separate from the color wheel — picking white sends the remote's dedicated white RF code, it's never treated as "a color." For this reason, White can't be saved in a quick color picker, the W button must be used for white.

<img width="648" height="759" alt="image" src="https://github.com/user-attachments/assets/ea42bb1d-3185-4593-98a8-f9c9855d03a1" />


### Effects list → the animation modes

The remote's animation modes (Gradual, Wave, Jumping, Fading, Wave + Jumping) show up in the light's native **Effect** list. Selecting one sends that mode's RF code and lets the brightness slider switch to controlling effect speed, as above. Just like the physical remote, the light brightness can't be controlled when the light plays an animation.

<img width="679" height="756" alt="image" src="https://github.com/user-attachments/assets/9caf400c-31b7-4d7e-9333-df2bab65f1a6" />


### Pairing

The `button.<name>_pair` entity sends the same pairing code the original remote ould sends when in pairing mode (M+C button held for 15 sec), for linking the light to your RF proxy, if required.

<img width="529" height="228" alt="image" src="https://github.com/user-attachments/assets/2ecd9bbb-ac48-47c5-b8ac-5ae235dd5b05" />


## Notes on reliability

RF here is one-way and "fire and forget" — Home Assistant has no way to confirm the light actually did what was asked, so this integration reports whatever it last told the light to do (an *assumed state* entity). It's also why the color wheel snaps to 64 known positions rather than trying to interpolate an arbitrary number of shades: only sending codes that are confirmed to correspond to real wheel positions keeps the light's behavior predictable. The changes made using the physical remote won't reflect in Home Assisant. The physical remote might become "out of sync" with the light, for example, the physical remote remember the last time it's power button was pressed was to send to OFF RF code so next time it's pressed, it will send the ON RF code. SO if your light was turned ON using this integration, you might have to press the power button twice to turn the light OFF so to physical remote catch up by sending the ON command and then the OFF command. Same behavior is expected with other fonctions. This is a normal limitation of one-way RF communication and assumed state. The same "problem" would occur if you had 2 physical remotes.
