"""Tests for the diagnostics provided by the Vacmaster Cardio54 integration."""

from __future__ import annotations

from syrupy.assertion import SnapshotAssertion
from syrupy.filters import props

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
    """Snapshot config entry, entities and transmitter state.

    Mirrors the novy_cooker_hood diagnostics test (the reference RF-fan
    integration in HA core). Excludes only the runtime non-deterministic
    fields (registry IDs, timestamps) so the snapshot stays stable across
    runs and reorderings.
    """
    result = await get_diagnostics_for_config_entry(
        hass, hass_client, init_integration
    )
    # Drop the random transmitter registry id from the entry data; it is a
    # ULID HA generates fresh every time.
    result["config_entry"]["data"].pop("transmitter")

    assert result == snapshot(
        exclude=props(
            "config_entry_id",
            "context",
            "created_at",
            "device_id",
            "entry_id",
            "id",
            "last_changed",
            "last_reported",
            "last_updated",
            "modified_at",
            "unique_id",
        )
    )
