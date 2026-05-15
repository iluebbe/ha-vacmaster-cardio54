# Vacmaster Cardio54 — Home Assistant integration

Native Home Assistant integration for the **Vacmaster Cardio54** fitness fan
(AM1202R remote, EV1527 protocol on 433.92 MHz OOK). Each Cardio54 appears
as a `fan` entity with three speed levels and a power toggle.

This is a custom component intended for [HACS](https://hacs.xyz/) /
manual installation while it's iterated locally. The end goal is upstreaming
to Home Assistant core at Silver Quality Scale.

## How it works

```
  Home Assistant UI (fan tile)
        │  fan.turn_on / set_percentage
        ▼
  vacmaster_cardio54   (this integration)
        │  EV1527Command(device_id, data_nibble)
        │  radio_frequency.async_send_command(transmitter, command)
        ▼
  radio_frequency      (HA core entity platform)
        │
        ▼
  Transmitter entity   (ESPHome with CC1101, Broadlink RM4, …)
        │  raw OOK timings
        ▼
  433.92 MHz  →  Cardio54 receiver
```

The integration is **transmitter-agnostic**: it picks whichever 433.92 MHz
OOK transmitter you have registered via the
[`radio_frequency`](https://www.home-assistant.io/integrations/radio_frequency/)
platform.

`assumed_state = True` — the protocol is one-way, the fan has no telemetry,
and HA's view of the state is a best guess restored across restarts via
`RestoreEntity`.

## Requirements

- Home Assistant ≥ 2026.5 (for the stable `radio_frequency` core integration)
- A registered RF transmitter that supports **433.92 MHz OOK**, exposed via
  the `radio_frequency` platform. Tested transmitters:
  - ESPHome ≥ 2026.5 with the `radio_frequency` / `ir_rf_proxy` component
    on top of `cc1101` + `remote_transmitter`
  - Broadlink RM4 Pro (auto-registered by the Broadlink integration)

The Python dependency `rf_protocols` is pulled in transitively by
`radio_frequency`; no extra requirements declared in `manifest.json`.

## Install (custom component)

1. Copy `custom_components/vacmaster_cardio54/` into your Home Assistant
   `config/custom_components/` folder.
2. Restart Home Assistant.
3. **Settings → Devices & Services → + Add Integration** → search for
   "Vacmaster Cardio54".
4. Pick the radio frequency transmitter you want to use.
5. Pair: HA generates a fresh random 20-bit EV1527 device ID and walks
   you through the Cardio54's 5-second pairing sequence (power switch
   to **0** → speed dial to the remote-control symbol → power switch to
   **I** → submit). The pairing burst (~3.4 s) lands inside the window
   and the fan learns the new ID.
6. Confirm: HA sends speed I; verify the fan reacts; finish.

Repeat for additional fans — each config entry is independent and gets
its own auto-generated device ID, so multiple Cardio54s on the same
transmitter do not cross-talk.

## Reconfigure / Re-pair

- **Switch transmitter** (e.g., move to a different RF gateway): the
  reconfigure flow picks a new transmitter while keeping the device ID,
  so the fan does not need to be re-paired.
- **Re-pair from scratch** (e.g., the receiver lost its slot): remove the
  config entry and add a fresh one — that generates a new ID and runs the
  pairing burst again.

## Hardware reference

| Detail | Value |
|---|---|
| Frequency | 433.92 MHz |
| Modulation | OOK (ASK) |
| Protocol | EV1527, 24 bits (20-bit ID + 4-bit data) |
| Symbol timebase | ~320 µs (short pulse), ~1000 µs (long pulse) |
| Sync | short mark + ~10 ms space |
| Data nibbles | `1000` = speed I, `0100` = II, `0010` = III, `0001` = power toggle |
| Receiver slots | 1 (re-pairing overwrites the existing ID) |

Power is a **toggle**, so the integration only emits it when it believes
the fan is currently on. Speed commands switch the fan on deterministically
and are safe to fire in any state.

## Quality scale

Targets **Silver** per the
[HA Quality Scale rules](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/).
See `custom_components/vacmaster_cardio54/quality_scale.yaml` for the rule
status. Gold-tier items (`diagnostics`, `devices`, `reconfiguration-flow`)
are already in place.

## Tests

```bash
pip install -r requirements_test.txt
pytest tests/
```

The test suite mirrors `tests/components/novy_cooker_hood/` from HA core and
uses the same `MockRadioFrequencyEntity` helper to mock the transmitter
without real hardware. Run inside a Docker container with HA 2026.5.x if
your local environment ships a lower HA version.

## Development & contributions

The integration tracks the `home-assistant/core` integration shape closely;
when porting upstream the only changes are:

- Drop the `version` field from `manifest.json` (custom components only)
- Replace `from .ev1527 import EV1527Command` with
  `from rf_protocols.commands.ev1527 import EV1527Command` (once that module
  is released — currently still vendored)
- Adjust the test imports from `custom_components.*` to
  `homeassistant.components.*`

Issues and PRs welcome.

## License

MIT — see [LICENSE](LICENSE).
