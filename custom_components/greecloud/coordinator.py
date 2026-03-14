"""Coordinator for Gree Cloud devices."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .greeclimate.cloud_api import GreeCloudApi
from .greeclimate.cloud_device import CloudDevice
from .greeclimate.mqtt_client import GreeMqttClient
from .greeclimate.deviceinfo import DeviceInfo

from .const import DEFAULT_UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)

# MQTT server mapping by region
MQTT_SERVER_MAP = {
    'Europe': 'mqtt-eu.gree.com',
    'North American': 'mqtt-us.gree.com',
    'East South Asia': 'mqtt-as.gree.com',
    'Middle East': 'mqtt-me.gree.com',
    'Latin American': 'mqtt-la.gree.com',
    'South American': 'mqtt-la.gree.com',
    'China Mainland': 'mqtt-as.gree.com',
    'India': 'mqtt-as.gree.com',
    'Australia': 'mqtt-as.gree.com',
    'Russian server': 'mqtt-eu.gree.com',
}


class GreeCloudData:
    """Class to hold Gree Cloud data."""

    def __init__(self) -> None:
        """Initialize data container."""
        self.api: GreeCloudApi | None = None
        self.mqtt_client: GreeMqttClient | None = None
        self.devices: dict[str, CloudDevice] = {}


class GreeCloudCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Gree Cloud coordinator.

    This class handles:
    - Authentication with Gree Cloud API
    - Device discovery via Cloud API
    - MQTT connection for device control
    - Periodic state updates
    """

    def __init__(
        self,
        hass: HomeAssistant,
        username: str,
        password: str,
        region: str,
    ) -> None:
        """Initialize Gree Cloud coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="greecloud",
            update_interval=None,  # We'll handle updates manually
        )

        self._username = username
        self._password = password
        self._region = region

        self._api: GreeCloudApi | None = None
        self._mqtt_client: GreeMqttClient | None = None
        self._devices: dict[str, CloudDevice] = {}

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        """Fetch data from all devices."""
        data = {}

        for mac, device in self._devices.items():
            try:
                await device.update_state()
                data[mac] = {
                    "power": device.power,
                    "name": device.device_info.name if device.device_info else mac,
                }
            except Exception as exc:
                _LOGGER.warning("Failed to update device %s: %s", mac, exc)
                data[mac] = {
                    "power": None,
                    "name": device.device_info.name if device.device_info else mac,
                    "error": str(exc),
                }

        return data

    async def async_setup(self) -> None:
        """Set up the Gree Cloud connection and discover devices."""
        try:
            # Initialize API client
            self._api = GreeCloudApi.for_server(
                self._region, self._username, self._password
            )

            # Login to Gree Cloud
            _LOGGER.info("Logging in to Gree Cloud as %s", self._username)
            credentials = await self._api.login()
            _LOGGER.info("Successfully logged in, user_id: %s", credentials.user_id)

            # Get all devices from all homes
            cloud_devices = await self._api.get_all_devices()
            _LOGGER.info("Found %d cloud devices", len(cloud_devices))

            if not cloud_devices:
                _LOGGER.warning("No devices found in Gree Cloud account")
                return

            # Determine MQTT server based on region
            mqtt_server = MQTT_SERVER_MAP.get(self._region, 'mqtt-eu.gree.com')
            _LOGGER.info("Using MQTT server: %s", mqtt_server)

            # Initialize MQTT client with correct server and port
            self._mqtt_client = GreeMqttClient(
                user_id=credentials.user_id,
                token=credentials.token,
                server=mqtt_server,
                port=1984  # Gree uses 1984, not 8883!
            )

            # Connect to MQTT broker
            _LOGGER.info("Connecting to Gree MQTT broker")
            await self._mqtt_client.connect()
            _LOGGER.info("Connected to MQTT broker")

            # Create CloudDevice instances for each device
            for cloud_dev in cloud_devices:
                try:
                    # Create DeviceInfo with dummy ip/port (not used for cloud devices)
                    device_info = DeviceInfo(
                        ip='mqtt.gree.com',
                        port=8883,
                        mac=cloud_dev.mac,
                        name=cloud_dev.name,
                        brand=None,
                        model=cloud_dev.model,
                        version=cloud_dev.version
                    )

                    # Create CloudDevice
                    device = CloudDevice(
                        mqtt_client=self._mqtt_client,
                        device_info=device_info,
                        device_key=cloud_dev.key,
                        cipher_version=1,  # Use CipherV1 by default
                    )

                    # Bind the device
                    await device.bind()
                    _LOGGER.info("Bound device: %s (%s)", cloud_dev.name, cloud_dev.mac)

                    # Store device
                    self._devices[cloud_dev.mac] = device

                except Exception as exc:
                    _LOGGER.error(
                        "Failed to setup device %s (%s): %s",
                        cloud_dev.name,
                        cloud_dev.mac,
                        exc,
                    )

            # Initial state update
            await self._async_update_data()

        except Exception as exc:
            _LOGGER.error("Failed to setup Gree Cloud: %s", exc)
            raise

    async def async_shutdown(self) -> None:
        """Shutdown the coordinator."""
        # Disconnect MQTT
        if self._mqtt_client:
            try:
                await self._mqtt_client.disconnect()
            except Exception as exc:
                _LOGGER.warning("Error disconnecting MQTT: %s", exc)

        # Close API session
        if self._api:
            try:
                await self._api.close()
            except Exception as exc:
                _LOGGER.warning("Error closing API session: %s", exc)

    @property
    def devices(self) -> dict[str, CloudDevice]:
        """Return the dictionary of devices."""
        return self._devices

    def get_device(self, mac: str) -> CloudDevice | None:
        """Get a device by MAC address."""
        return self._devices.get(mac)
