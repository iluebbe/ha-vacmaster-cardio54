"""Vendored EV1527 RF command encoder.

Temporary local copy of ``rf_protocols/commands/ev1527.py`` from
home-assistant-libs/rf-protocols (main @ 84c63f7). ``EV1527Command`` is not in
the released ``rf-protocols`` 3.1.0 that Home Assistant ships for the
``radio_frequency`` integration, so it is vendored here until a release
includes it. The base classes it needs (``RadioFrequencyCommand``,
``ModulationType``) ARE in 3.1.0 with an identical API and are imported from
the installed package, so the encoded command stays compatible with what
``radio_frequency.async_send_command`` expects.

For the Home Assistant core submission: delete this file and use
``from rf_protocols.commands.ev1527 import EV1527Command`` against a released
rf-protocols version.

EV1527/RT1527/FP1527 is a 24-bit OOK protocol: a 20-bit device ID plus a
4-bit data nibble, PWM-encoded (short pulse = 0, long pulse = 1) and preceded
by a sync gap. Bits are encoded LSB-first.
"""

from __future__ import annotations

from typing import override

from rf_protocols import ModulationType, RadioFrequencyCommand

_DEFAULT_FREQUENCY = 433_920_000
_DEFAULT_REPEATS = 4
_DEFAULT_TIMEBASE_US = 275


class EV1527Command(RadioFrequencyCommand):  # type: ignore[misc]
    # Subclassing a class mypy sees as ``Any`` (rf_protocols does not ship
    # type stubs / a ``py.typed`` marker). Drops out automatically once the
    # vendored file is replaced by ``rf_protocols.commands.ev1527`` post-
    # upstream-release.
    """Encode an EV1527-compatible RF command.

    Data layout:
    - 20 bits: device ID
    - 4 bits: data/button (0..15)
    """

    device_id: int
    data: int
    timebase_us: int

    def __init__(
        self,
        *,
        device_id: int,
        data: int,
        frame_repeats: int = _DEFAULT_REPEATS,
        frequency: int = _DEFAULT_FREQUENCY,
        timebase_us: int = _DEFAULT_TIMEBASE_US,
    ) -> None:
        """Initialize the EV1527 command.

        Args:
            device_id: 20-bit device ID (0..1048575)
            data: Data/button bits (0..15)
            frame_repeats: Number of times to repeat the frame
            frequency: RF frequency in Hz
            timebase_us: Time base in microseconds
        """
        if device_id < 0 or device_id >= (1 << 20):
            raise ValueError("device_id must be in range 0..1048575 (20-bit)")
        if data < 0 or data > 15:
            raise ValueError("data must be in range 0..15")

        super().__init__(
            frequency=frequency,
            modulation=ModulationType.OOK,
            repeat_count=frame_repeats,
        )
        self.device_id = device_id
        self.data = data
        self.timebase_us = timebase_us

    @override
    def get_raw_timings(self) -> list[int]:
        """Compute EV1527 frame timings using PWM encoding.

        Encodes: sync + 24 data bits (LSB first).
        """
        _symbols = {
            "0": [self.timebase_us, -3 * self.timebase_us],
            "1": [3 * self.timebase_us, -self.timebase_us],
            "sync": [self.timebase_us, -31 * self.timebase_us],
        }

        # Encode 20-bit device ID, LSB first.
        device_id_bits = format(self.device_id, "020b")[::-1]
        symstr: list[str] = [*device_id_bits]

        # Encode 4-bit data, LSB first.
        data_bits = format(self.data, "04b")[::-1]
        symstr.extend(data_bits)

        # Build timings: sync followed by the data symbols.
        timings: list[int] = []
        timings.extend(_symbols["sync"])
        for s in symstr:
            timings.extend(_symbols[s])

        return timings
