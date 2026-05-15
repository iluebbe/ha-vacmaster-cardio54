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
    on top of `cc1101` + `remote_transmitter` — a ready-to-flash example
    config lives at [`esphome/esp32-dev-board.yaml`](esphome/esp32-dev-board.yaml).
    Copy `esphome/secrets.yaml.example` to `secrets.yaml` next to it and
    fill in your own keys.
  - Broadlink RM4 Pro (auto-registered by the Broadlink integration). Works
    but the RF output is community-reported as weak; range may not reach
    the fan reliably.

The Python dependency `rf_protocols` is pulled in transitively by
`radio_frequency`; no extra requirements declared in `manifest.json`.

## Wire up the ESP32 + CC1101 (reference build)

Skip this section if you use a Broadlink or any other already-supported
`radio_frequency` transmitter.

The reference build is a generic **ESP32 DevKit** (`board: esp32dev` in
ESPHome) plus a **CC1101 433 MHz module** with an SMA whip antenna.

```
                +----------------------+              +--------------------+
                |     ESP32 DevKit     |              |   CC1101 module    |
                |   (3V3 rail!)        |              |                    |
                |                      |              |       ┌────┐       |
                |        3V3   ────────┼──────────────┼──VCC  │    │       |
                |        GND   ────────┼──────────────┼──GND  │ rf │       |
                |    GPIO18 (SCK)──────┼──────────────┼──SCK  │ ic │  ◄── antenna
                |    GPIO23 (MOSI)─────┼──────────────┼──MOSI │    │       |
                |    GPIO19 (MISO)─────┼──────────────┼──MISO │    │       |
                |    GPIO5  (CSN)──────┼──────────────┼──CSN  └────┘       |
                |    GPIO22 ───────────┼──────────────┼──GDO0  (TX data)   |
                |    GPIO21 ───────────┼──────────────┼──GDO2  (RX data)   |
                +----------------------+              +--------------------+
```

### Pin mapping

| ESP32 pin | CC1101 pin | Direction | Purpose |
|---|---|---|---|
| `3V3` | `VCC` | power | **3.3 V — do NOT connect to 5 V**, that fries the radio |
| `GND` | `GND` | ground | common ground |
| `GPIO18` | `SCK` | ESP → CC1101 | SPI clock |
| `GPIO23` | `MOSI` (`SI`) | ESP → CC1101 | SPI data out (master → slave) |
| `GPIO19` | `MISO` (`SO`) | ESP ← CC1101 | SPI data in  (slave → master) |
| `GPIO5` | `CSN` (`CS`) | ESP → CC1101 | SPI chip-select. *Strapping pin — ESPHome warns at compile, harmless here.* |
| `GPIO22` | `GDO0` | ESP → CC1101 | **Async-serial TX data input** — `remote_transmitter` writes pulses here |
| `GPIO21` | `GDO2` | ESP ← CC1101 | **Async-serial RX data output** — `remote_receiver` reads demodulated pulses here |

The "TX = GDO0 vs. RX = GDO2" split is the easy thing to get wrong. The
CC1101 in async-serial mode treats **GDO0 as the data input that drives
the modulator**, and **GDO2 as the data output from the demodulator**.
Both wires are bidirectional from the ESP's perspective (the ESP drives
GDO0 during a TX and reads GDO2 during an RX), and the
`cc1101.begin_tx` / `cc1101.begin_rx` actions toggle the radio's state
machine between the two.

### Antenna

A simple 17 cm straight wire works (quarter-wave at 433 MHz). The SMA
modules with a screw-in helical antenna are fine too. Bad antenna =
short range; mind the antenna match.

### Power supply

Powering the ESP32 dev board from a regular USB charger (or the
ESPHome flasher cable) is enough. The CC1101 in TX mode at
`output_power: 11` (≈ 9.9 dBm) draws about 30 mA — well within any
3.3 V regulator on an ESP32 dev board.

### Flash

1. Install the ESPHome dashboard (≥ 2026.5 because that's where the
   `radio_frequency` core component lives; while it's still beta you
   either pin to `2026.5.0bN` or use the `:beta` Docker tag).
2. Copy `esphome/esp32-dev-board.yaml` into your ESPHome config folder.
3. Copy `esphome/secrets.yaml.example` to `secrets.yaml` next to it and
   fill in your Wi-Fi credentials + a fresh `api_encryption_key` and
   `ota_password` (the dashboard's "Generate encryption key" button does
   both).
4. **Install** the configuration onto the board (USB the first time,
   wirelessly after that).
5. Add the device in Home Assistant: Settings → Devices & Services →
   Add Integration → ESPHome → host = the board's mDNS name or DHCP IP,
   port 6053, paste the same `api_encryption_key`.
6. A new entity `radio_frequency.<device>_rf` shows up under the
   ESPHome device. The Cardio54 integration's config flow will pick it
   up automatically.

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

## Remove

Settings → Devices & Services → Vacmaster Cardio54 → ⋮ → **Delete**.
The fan entity and config entry are unregistered immediately; no extra
cleanup is required. The fan's pairing on the receiver side is not affected
— it keeps the device ID until you re-pair it to a different transmitter.

## Reconfigure / Re-pair

- **Switch transmitter** (e.g., move to a different RF gateway): the
  reconfigure flow picks a new transmitter while keeping the device ID,
  so the fan does not need to be re-paired.
- **Re-pair from scratch** (e.g., the receiver lost its slot): remove the
  config entry and add a fresh one — that generates a new ID and runs the
  pairing burst again.

## Supported devices

| Device | Model | Status |
|---|---|---|
| Vacmaster Cardio54 fitness fan | AM1202R | ✅ tested in production with 2× fans |

Any other 3-speed fan that uses the same EV1527 remote (CMT2150L chip,
24-bit OOK, 320/1000 µs symbols, 10 ms sync, MSB-first capture matching
the data nibbles `1000 / 0100 / 0010 / 0001`) should work without changes
— please open an issue with a sniffer capture if you have one.

## Supported functions

| Function | Service | RF action |
|---|---|---|
| Turn on at speed I | `fan.turn_on` (no percentage) | Send `DATA_SPEEDS[0]` (`1000`) |
| Turn on at speed II / III | `fan.turn_on` with `percentage=50` / `100` | Send `DATA_SPEEDS[1]` / `[2]` |
| Set speed | `fan.set_percentage` | Send the matching speed nibble |
| Turn off | `fan.turn_off` or `set_percentage 0` | Send `DATA_POWER` (toggle) **only if the entity believes the fan is on** |
| State restore | implicit on HA restart | `RestoreEntity` reloads the last known percentage; no RF sent |

The fan entity exposes `assumed_state = True`. HA's notion of on/off and
speed is a best guess derived from the last command we sent.

## Known limitations

- **One-way protocol.** There is no acknowledgement and no telemetry. If
  someone presses a button on the OEM remote, HA does not see it — the
  state drifts until the next service call writes it.
- **Power is a toggle.** A "turn off" command physically toggles the
  receiver. The integration only emits it when HA thinks the fan is on; if
  the state has drifted (e.g., the fan was turned on by the OEM remote
  while HA showed "off") the toggle will appear to switch the fan on
  instead. Send a speed command — speeds switch the fan on
  deterministically — to re-sync.
- **One pairing slot per fan.** The Cardio54 receiver only stores one
  transmitter ID. Re-pairing to a new ID overwrites the previous one.
  Keep the OEM remote out of pairing range during the burst, otherwise
  it may re-claim the slot.
- **RF range depends on the transmitter.** With an ESPHome/CC1101 setup
  on a regular antenna we have reliable line-of-sight at typical room
  distance. The Broadlink RM4 Pro's RF stage is community-reported as
  weak and may not reach the fan even from a few metres.
- **Frequency is hard-coded to 433.92 MHz.** The integration filters
  available transmitters by exact OOK + 433.92 MHz support, which is what
  EV1527 needs. Multi-band RF gateways must expose 433.92 MHz in their
  `supported_frequency_ranges` to be selectable.

## Troubleshooting

**Config flow aborts with "No radio frequency transmitter supports
433.92 MHz OOK".**
The selected transmitter is registered but does not advertise 433.92 MHz
OOK in its capabilities. For ESPHome/CC1101 setups make sure the
`radio_frequency:` block carries `frequency: 433.92MHz` — without it the
device reports `frequency_min = frequency_max = 0` and HA filters it out.

**Fan does not react to commands but the RF burst goes out cleanly.**
Pairing is per-receiver-slot. Either the receiver has not learned this
HA's auto-generated device ID (re-run the pair step) or another
transmitter (OEM remote, second HA, leftover Broadlink test) recently
re-claimed the slot.

**ESPHome dev board hangs and goes offline after the first transmission.**
On ESPHome ≥ 2026.5 the `remote_transmitter:` defaults to
`non_blocking: true`. The `on_complete` callback then fires before the
CC1101 has finished transmitting, the chip is yanked back into RX mid-burst
and the whole module locks up until a power-cycle. Set
`non_blocking: false` on the transmitter (the example YAML in this repo
already does).

**Setup-flow aborts on a fresh HA install with "No radio frequency
transmitters are available".**
You need to add a radio-frequency-capable integration first (ESPHome with
the example dev-board YAML, or Broadlink). The Cardio54 integration only
sees transmitters that the `radio_frequency` core component already knows
about.

## Example automations

Off at bedtime:

```yaml
- alias: Bedroom fan off at midnight
  trigger:
    - platform: time
      at: "00:00:00"
  action:
    - service: fan.turn_off
      target:
        entity_id: fan.cardio54_bedroom
```

Boost when the temperature in the room goes above 25 °C:

```yaml
- alias: Cardio fan boost when warm
  trigger:
    - platform: numeric_state
      entity_id: sensor.bedroom_temperature
      above: 25
  action:
    - service: fan.set_percentage
      target:
        entity_id: fan.cardio54_bedroom
      data:
        percentage: 100
```

Re-sync after manually pressing the OEM remote (the integration cannot
detect that, so a manual button helper is the simplest workaround):

```yaml
- alias: Re-sync Cardio fan state
  trigger:
    - platform: state
      entity_id: input_button.cardio_resync
  action:
    - service: fan.set_percentage
      target:
        entity_id: fan.cardio54_bedroom
      data:
        percentage: 33   # Speed I — switches the fan on deterministically
```

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
