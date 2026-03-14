"""Base device class for Gree Cloud entities."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import GreeCloudCoordinator


class GreeCloudEntity(CoordinatorEntity[GreeCloudCoordinator]):
    """Base class for Gree Cloud entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: GreeCloudCoordinator,
        mac: str,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._mac = mac

        device = coordinator.get_device(mac)
        if device and device.device_info:
            device_info = device.device_info
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, mac)},
                name=device_info.name,
                manufacturer="Gree",
                model=device_info.model if device_info.model else "Gree AC",
                sw_version=device_info.version,
            )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if not self.coordinator.data:
            return False
        
        device_data = self.coordinator.data.get(self._mac)
        return device_data is not None and "error" not in device_data

    @property
    def device_data(self) -> dict[str, Any] | None:
        """Return the device data from coordinator."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get(self._mac)
