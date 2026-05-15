"""Cross-integration fixtures.

Currently only the ``radio_frequency`` helpers so downstream integration
tests (vacmaster_cardio54, novy_cooker_hood-style) can reuse the same
mock transmitter pattern HA core uses. Mirrors the two fixtures defined
in ``home-assistant/core`` ``tests/components/conftest.py`` 1:1.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from homeassistant.core import HomeAssistant

if TYPE_CHECKING:
    from .radio_frequency.common import MockRadioFrequencyEntity


@pytest.fixture(name="init_radio_frequency")
async def init_radio_frequency_fixture(hass: HomeAssistant) -> None:
    """Set up the Radio Frequency integration for testing."""
    from .radio_frequency.common import (
        init_radio_frequency_fixture_helper,
    )

    await init_radio_frequency_fixture_helper(hass)


@pytest.fixture(name="mock_rf_entity")
async def mock_rf_entity_fixture(
    hass: HomeAssistant, init_radio_frequency: None
) -> MockRadioFrequencyEntity:
    """Return a mock radio frequency entity registered with the integration."""
    from .radio_frequency.common import mock_rf_entity_fixture_helper

    return await mock_rf_entity_fixture_helper(hass)
