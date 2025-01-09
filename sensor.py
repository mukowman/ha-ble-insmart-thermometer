import logging
import asyncio
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import UnitOfTemperature
from homeassistant.core import callback
from bleak import BleakClient
from bleak.exc import BleakError
import struct

_LOGGER = logging.getLogger(__name__)

# Notify characteristic for the thermometer
NOTIFY_CHAR = "0000ff01-0000-1000-8000-00805f9b34fb"

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the INSMART Thermometer sensor from a config entry."""
    address = config_entry.data["address"]
    _LOGGER.debug(f"Setting up INSMART Thermometer sensor with address: {address}")
    thermometer = InsmartThermometerSensor(hass, address)
    async_add_entities([thermometer], True)

class InsmartThermometerSensor(SensorEntity):
    def __init__(self, hass, address):
        self.hass = hass
        self._address = address
        self._state = None
        self._available = False
        self._attr_name = "INSMART Thermometer Temperature"
        self._attr_unique_id = f"ble_thermometer_{self._address}"
        self._client = None
        self._disconnect_timer = None
        self._connect_lock = asyncio.Lock()
        self._connection_retry_interval = 60  # Retry connection every 60 seconds
        self._retry_task = None
        _LOGGER.debug(f"InsmartThermometerSensor initialized with address: {address}")

    @property
    def name(self):
        return self._attr_name

    @property
    def unique_id(self):
        return self._attr_unique_id

    @property
    def state(self):
        return self._state

    @property
    def unit_of_measurement(self):
        return UnitOfTemperature.CELSIUS

    @property
    def available(self):
        return self._available

    def decode_data(self, data):
        _LOGGER.debug(f"Decoding thermometer data: {data.hex()}")

        try:
            # Unpack data using the `<BHHB` format
            _, temperature_raw, _, status = struct.unpack('<BHHB', data)
            _LOGGER.debug(f"Unpacked data: temperature_raw={temperature_raw}, status={status}")

            # Convert temperature to Celsius (assuming it's in tenths of a degree)
            temperature = temperature_raw / 10.0
            _LOGGER.debug(f"Decoded temperature: {temperature}°C")

            return temperature
        except struct.error as e:
            _LOGGER.error(f"Error decoding thermometer data: {e}")
            return None

    def notification_handler(self, sender, data):
        _LOGGER.debug(f"Received notification: {data.hex()}")
        temperature = self.decode_data(data)
        if temperature is not None:
            self._state = round(temperature, 1)  # Update the state with rounded temperature
            self._available = True
            _LOGGER.info(f"Updated temperature: {self._state}°C")
            self.async_write_ha_state()

            # Reset the disconnect timer
            if self._disconnect_timer:
                self._disconnect_timer.cancel()
            self._disconnect_timer = self.hass.loop.call_later(60, self.disconnect)

    async def connect(self):
        async with self._connect_lock:
            if self._client and self._client.is_connected:
                return

            try:
                self._client = BleakClient(self._address, timeout=10.0)
                await asyncio.wait_for(self._client.connect(), timeout=20.0)
                _LOGGER.debug(f"Connected to BLE Thermometer: {self._address}")
                self._available = True

                await self._client.start_notify(NOTIFY_CHAR, self.notification_handler)
                _LOGGER.debug(f"Notifications started for characteristic: {NOTIFY_CHAR}")

                # Set initial disconnect timer
                self._disconnect_timer = self.hass.loop.call_later(60, self.disconnect)

            except asyncio.TimeoutError:
                _LOGGER.error(f"Timeout connecting to INSMART Thermometer: {self._address}")
                self._available = False
                self._schedule_retry()
            except BleakError as e:
                _LOGGER.error(f"Error connecting to INSMART Thermometer: {e}")
                self._available = False
                self._schedule_retry()
            except Exception as e:
                _LOGGER.error(f"Unexpected error connecting to INSMART Thermometer: {e}")
                self._available = False
                self._schedule_retry()

    @callback
    def _schedule_retry(self):
        if self._retry_task:
            self._retry_task.cancel()
        self._retry_task = self.hass.async_create_task(self._retry_connect())

    async def _retry_connect(self):
        await asyncio.sleep(self._connection_retry_interval)
        await self.async_update()

    def disconnect(self):
        if self._client and self._client.is_connected:
            asyncio.create_task(self._disconnect())

    async def _disconnect(self):
        try:
            await self._client.disconnect()
            _LOGGER.debug(f"Disconnected from INSMART Thermometer: {self._address}")
        except Exception as e:
            _LOGGER.error(f"Error disconnecting from INSMART Thermometer: {e}")
        finally:
            self._client = None
            self._available = False
            self.async_write_ha_state()

    async def async_added_to_hass(self):
        """Run when entity is about to be added to hass."""
        await self.async_update()

    async def async_will_remove_from_hass(self):
        """Run when entity will be removed from hass."""
        if self._retry_task:
            self._retry_task.cancel()
        await self._disconnect()

    async def async_update(self):
        """Update the sensor."""
        if not self._client or not self._client.is_connected:
            await self.connect()
