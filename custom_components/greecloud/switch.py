"""Switch platform for Gree Cloud integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .greeclimate.cloud_device import CloudDevice

from .const import DOMAIN
from .coordinator import GreeCloudCoordinator
from .device import GreeCloudEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Gree Cloud switch platform."""
    coordinator: GreeCloudCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = []
    for mac, device in coordinator.devices.items():
        entity = GreeCloudPowerSwitch(coordinator, mac, device)
        entities.append(entity)
        _LOGGER.debug("Created switch entity for device: %s", device.device_info.name if device.device_info else mac)

    async_add_entities(entities)


class GreeCloudPowerSwitch(GreeCloudEntity, SwitchEntity):
    """Representation of a Gree Cloud power switch."""

    def __init__(
        self,
        coordinator: GreeCloudCoordinator,
        mac: str,
        device: CloudDevice,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, mac)
        self._device = device

        # Set unique ID based on MAC address
        self._attr_unique_id = f"{mac}_power"

        # Set entity name
        self._attr_name = "Power"

    @property
    def is_on(self) -> bool | None:
        """Return true if the switch is on."""
        if self.device_data is None:
            return None
        
        return self.device_data.get("power", False)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        _LOGGER.debug("Turning on device: %s", self._mac)
        
        try:
            self._device.power = True
            await self._device.push_state_update()
            
            # Update coordinator data
            await self.coordinator.async_request_refresh()
            
        except Exception as exc:
            _LOGGER.error("Failed to turn on device %s: %s", self._mac, exc)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        _LOGGER.debug("Turning off device: %s", self._mac)
        
        try:
            self._device.power = False
            await self._device.push_state_update()
            
            # Update coordinator data
            await self.coordinator.async_request_refresh()
            
        except Exception as exc:
            _LOGGER.error("Failed to turn off device %s: %s", self._mac, exc)
