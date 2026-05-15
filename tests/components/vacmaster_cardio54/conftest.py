"""Fixtures for the Vacmaster Cardio54 integration tests."""

from __future__ import annotations

from collections.abc import Generator

import pytest

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.vacmaster_cardio54.const import (
    CONF_DEVICE_ID,
    CONF_TRANSMITTER,
    DOMAIN,
)

from ..radio_frequency.common import MockRadioFrequencyEntity

# A deterministic 20-bit device ID used across all fixtures.
TEST_DEVICE_ID = 0xABCDE


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(
    enable_custom_integrations: None,
) -> Generator[None]:
    """Enable custom integrations for all tests in this package."""
    yield


@pytest.fixture
def mock_config_entry(
    hass: HomeAssistant,
    mock_rf_entity: MockRadioFrequencyEntity,
) -> MockConfigEntry:
    """Return a ready-to-add config entry pointing at the mock transmitter.

    Unique ID format mirrors what the config flow produces:
    ``<transmitter_registry_id>_<device_id:05X>``.
    """
    entity_entry = er.async_get(hass).async_get_entity_id(
        "radio_frequency", "test", mock_rf_entity.unique_id
    )
    assert entity_entry is not None
    registry_id = er.async_get(hass).async_get(entity_entry).id
    return MockConfigEntry(
        domain=DOMAIN,
        title="Vacmaster Cardio54",
        data={
            CONF_TRANSMITTER: registry_id,
            CONF_DEVICE_ID: TEST_DEVICE_ID,
        },
        unique_id=f"{registry_id}_{TEST_DEVICE_ID:05X}",
    )


@pytest.fixture
async def init_integration(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> MockConfigEntry:
    """Set up the integration with the mock config entry."""
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    return mock_config_entry
