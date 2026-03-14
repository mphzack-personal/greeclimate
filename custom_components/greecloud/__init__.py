"""The Gree Cloud integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, CONF_USERNAME, CONF_PASSWORD, CONF_REGION, DEFAULT_REGION
from .coordinator import GreeCloudCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SWITCH]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Gree Cloud component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Gree Cloud from a config entry."""
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]
    region = entry.data.get(CONF_REGION, DEFAULT_REGION)

    coordinator = GreeCloudCoordinator(
        hass=hass,
        username=username,
        password=password,
        region=region,
    )

    try:
        await coordinator.async_setup()
    except Exception as exc:
        _LOGGER.error("Failed to setup Gree Cloud: %s", exc)
        raise ConfigEntryNotReady from exc

    # Check if any devices were found
    if not coordinator.devices:
        _LOGGER.warning("No devices found in Gree Cloud account")
        raise ConfigEntryNotReady("No devices found in Gree Cloud account")

    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_shutdown()

    return unload_ok
