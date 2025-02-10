import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from .const import DOMAIN, CONF_TANK_HOST, CONF_TANK_NAME, CONF_TANK_PROTOCOL, CONF_UPDATE_INTERVAL

from .coordinator import JuwelHelialuxCoordinator
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up multiple sensor entities from a config entry."""
    tank_name = config_entry.data[CONF_TANK_NAME]
    tank_host = config_entry.data[CONF_TANK_HOST]
    tank_protocol = config_entry.data[CONF_TANK_PROTOCOL]
    update_interval = config_entry.data.get(CONF_UPDATE_INTERVAL, 1)
    coordinator = JuwelHelialuxCoordinator(hass, tank_host, tank_protocol, update_interval)
    await coordinator.async_config_entry_first_refresh()

    # Create main sensor (with all attributes)
    main_sensor = JuwelHelialuxSensor(coordinator, tank_name)

    # Create individual sensors with default values
    attribute_sensors = [
        JuwelHelialuxAttributeSensor(coordinator, tank_name, "current_profile", default_value="offline"),
        JuwelHelialuxAttributeSensor(coordinator, tank_name, "white", default_value=0, SensorStateClass=SensorStateClass.MEASUREMENT, unit="%"),
        JuwelHelialuxAttributeSensor(coordinator, tank_name, "blue", default_value=0, SensorStateClass=SensorStateClass.MEASUREMENT, unit="%"),
        JuwelHelialuxAttributeSensor(coordinator, tank_name, "green", default_value=0, SensorStateClass=SensorStateClass.MEASUREMENT, unit="%"),
        JuwelHelialuxAttributeSensor(coordinator, tank_name, "red", default_value=0, SensorStateClass=SensorStateClass.MEASUREMENT, unit="%"),
        JuwelHelialuxAttributeSensor(coordinator, tank_name, "manualColorSimulationEnabled", default_value=False),
        JuwelHelialuxAttributeSensor(coordinator, tank_name, "manualDaytimeSimulationEnabled", default_value=False),
        JuwelHelialuxAttributeSensor(coordinator, tank_name, "device_time", default_value=None),
    ]

    # Add all sensors to Home Assistant
    async_add_entities([main_sensor] + attribute_sensors, True)



class JuwelHelialuxSensor(CoordinatorEntity, SensorEntity):
    """Main sensor containing all data as attributes."""

    def __init__(self,  coordinator, tank_name):
        super().__init__(coordinator)
        
        self._attr_name = f"{tank_name} Sensor"
        self._attr_unique_id = f"{tank_name}_sensor"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, tank_name)},
            name=tank_name,
            manufacturer="Juwel",
            model="Juwel Helialux",
            configuration_url=f"{coordinator.tank_protocol}://{coordinator.tank_host}",
        )
    @property
    def state(self):
        """Return 'online' if data is available, otherwise 'offline'."""
        return "online" if self.coordinator.data else "offline"

    @property
    def extra_state_attributes(self):
        """Return all available attributes including colors and profile."""
        # Combine the profile and color data with the existing data from the coordinator
        color_data = {
            "red": self.coordinator.data.get("red", 0),
            "green": self.coordinator.data.get("green", 0),
            "blue": self.coordinator.data.get("blue", 0),
            "white": self.coordinator.data.get("white", 0),
        }

        profile_data = {
            "current_profile": self.coordinator.data.get("current_profile", "offline")
        }
        
        time_data = {
            "deviceTime": self.coordinator.data.get("deviceTime", "00:00")
        }        

        # Merge the color and profile data together
        return {**self.coordinator.data, **color_data, **profile_data, **time_data}


    async def async_remove(self):
        """Cleanup resources when the entity is removed."""
        _LOGGER.debug(f"Removing entity: {self.entity_id}")
        await super().async_remove()

class JuwelHelialuxAttributeSensor(CoordinatorEntity, SensorEntity):
    """Creates a sensor for each individual attribute."""

    def __init__(self, coordinator, tank_name, attribute, default_value=None, SensorStateClass="", unit=""):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = f"{tank_name} {attribute}"
        self._attr_unique_id = f"{tank_name}_{attribute}"
        self._attribute = attribute
        self._default_value = default_value  # Default value if no data is available
        self._attr_state_class = SensorStateClass
        self._attr_native_unit_of_measurement = unit
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, tank_name)},
            name=tank_name,
            manufacturer="Juwel",
            model="Juwel Helialux",
            configuration_url=f"{coordinator.tank_protocol}://{coordinator.tank_host}",
        )        
    @property
    def state(self):
        data = self.coordinator.data or {}  # Ensure data is always a dictionary
        # Return the attribute value, or a default if not found
        return data.get(self._attribute, self._default_value)
 

    async def async_remove(self):
        """Cleanup resources when the entity is removed."""
        _LOGGER.debug(f"Removing entity: {self.entity_id}")
        await super().async_remove()