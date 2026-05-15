"""Tests for the vendored EV1527 command encoder.

These tests cover the local ``ev1527.py`` copy that the integration
currently uses while ``EV1527Command`` is unreleased upstream in
``rf-protocols``. Once the upstream release ships and the vendored file
is dropped, this test module is dropped with it.
"""

from __future__ import annotations

import pytest

from custom_components.vacmaster_cardio54.const import DATA_POWER, DATA_SPEEDS
from custom_components.vacmaster_cardio54.ev1527 import EV1527Command


def test_device_id_lower_bound_rejected() -> None:
    """Negative device_id is rejected."""
    with pytest.raises(ValueError, match="device_id"):
        EV1527Command(device_id=-1, data=0)


def test_device_id_upper_bound_rejected() -> None:
    """device_id >= 2**20 is rejected."""
    with pytest.raises(ValueError, match="device_id"):
        EV1527Command(device_id=1 << 20, data=0)


def test_data_lower_bound_rejected() -> None:
    """Negative data nibble is rejected."""
    with pytest.raises(ValueError, match="data"):
        EV1527Command(device_id=0, data=-1)


def test_data_upper_bound_rejected() -> None:
    """data > 15 is rejected (only the low 4 bits are valid)."""
    with pytest.raises(ValueError, match="data"):
        EV1527Command(device_id=0, data=16)


def test_raw_timings_length_is_50() -> None:
    """Every EV1527 frame is 1 sync pulse pair + 24 bit pairs = 50 entries."""
    cmd = EV1527Command(device_id=0xABCDE, data=DATA_POWER, timebase_us=320)
    timings = cmd.get_raw_timings()
    # 2 sync (mark + space) + 24 bits * 2 = 50
    assert len(timings) == 50


def test_raw_timings_sync_is_first() -> None:
    """The frame opens with the sync pair (timebase + -31 * timebase)."""
    cmd = EV1527Command(device_id=0, data=0, timebase_us=320)
    timings = cmd.get_raw_timings()
    assert timings[:2] == [320, -31 * 320]


def test_raw_timings_all_zero_bits() -> None:
    """device_id=0, data=0 produces sync followed by 24 short '0' symbols."""
    cmd = EV1527Command(device_id=0, data=0, timebase_us=100)
    timings = cmd.get_raw_timings()
    # The symbol "0" is [t, -3t]; we expect 24 of them after the sync.
    expected_zero_pair = [100, -300]
    for i in range(24):
        offset = 2 + i * 2
        assert timings[offset : offset + 2] == expected_zero_pair


def test_raw_timings_all_one_bits() -> None:
    """device_id=0xFFFFF, data=0xF flips every bit to the long "1" symbol."""
    cmd = EV1527Command(device_id=(1 << 20) - 1, data=0xF, timebase_us=100)
    timings = cmd.get_raw_timings()
    expected_one_pair = [300, -100]
    for i in range(24):
        offset = 2 + i * 2
        assert timings[offset : offset + 2] == expected_one_pair


@pytest.mark.parametrize("data", [DATA_POWER, *DATA_SPEEDS])
def test_raw_timings_pulse_lengths_match_timebase(data: int) -> None:
    """All marks are either t or 3t, all spaces are -t, -3t or -31t."""
    timebase = 320
    cmd = EV1527Command(device_id=0xABCDE, data=data, timebase_us=timebase)
    timings = cmd.get_raw_timings()
    allowed_marks = {timebase, 3 * timebase}
    allowed_spaces = {-timebase, -3 * timebase, -31 * timebase}
    for i, t in enumerate(timings):
        if i % 2 == 0:
            assert t in allowed_marks, f"mark at index {i}: {t}"
        else:
            assert t in allowed_spaces, f"space at index {i}: {t}"


def test_frame_repeats_forwarded_to_repeat_count() -> None:
    """``frame_repeats`` becomes ``repeat_count`` on the base command.

    The HA ``radio_frequency`` platform interprets ``repeat_count`` as the
    number of *additional* transmissions on top of the first one — so this
    is the right field to feed.
    """
    cmd = EV1527Command(
        device_id=0xABCDE, data=DATA_POWER, frame_repeats=10
    )
    assert cmd.repeat_count == 10
