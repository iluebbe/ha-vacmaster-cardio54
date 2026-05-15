"""Tests for the Vacmaster Cardio54 diagnostics."""

from __future__ import annotations

from syrupy.assertion import SnapshotAssertion

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.components.diagnostics import (
    get_diagnostics_for_config_entry,
)
from pytest_homeassistant_custom_component.typing import ClientSessionGenerator


async def test_diagnostics(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    init_integration: MockConfigEntry,
    snapshot: SnapshotAssertion,
) -> None:
    """Snapshot the diagnostics payload — config entry + entities + transmitter."""
    result = await get_diagnostics_for_config_entry(
        hass, hass_client, init_integration
    )
    # The transmitter sub-dict carries a runtime-only entity_id that is not
    # stable across test orderings; drop it before snapshotting.
    result["transmitter"]["state"]["last_changed"] = "<redacted>"
    result["transmitter"]["state"]["last_updated"] = "<redacted>"
    result["transmitter"]["state"]["last_reported"] = "<redacted>"

    assert result == snapshot
