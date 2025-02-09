import logging
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, CoordinatorEntity
from .pyhelialux.pyHelialux import Controller as Helialux
_LOGGER = logging.getLogger(__name__)

class JuwelHelialuxCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the Juwel Helialux device."""

    def __init__(self, hass, tank_host, tank_protocol, update_interval):
        super().__init__(
            hass,
            _LOGGER,
            name="Juwel Helialux Sensor",
            update_interval=timedelta(minutes=update_interval),
        )
        self.tank_host = tank_host
        self.tank_protocol = tank_protocol
        _LOGGER.debug("Init started")
        url = f"{self.tank_protocol}://{self.tank_host}" if "://" not in self.tank_protocol else f"{self.tank_protocol}{self.tank_host}"
        self.helialux = Helialux(url)
    async def _async_update_data(self):
        try:
            data = await self.helialux.get_status()
            _LOGGER.debug("Raw data received from Helialux: %s", data)

            if not isinstance(data, dict):
                _LOGGER.warning(
                    "Unexpected data format from Helialux device, defaulting to empty dict. Received: %s", type(data)
                )
                return {}
            # Initialize self.data as an empty dict if it's None
            if self.data is None:
                self.data = {}
                
            # Ensure we always include profile and color data
            profile = data.get("currentProfile", "offline")
            deviceTime = data.get("deviceTime", "00:00")
            
            color_data = {
                "red": data.get("currentRed", 0),
                "green": data.get("currentGreen", 0),
                "blue": data.get("currentBlue", 0),
                "white": data.get("currentWhite", 0),
            }

            # Merge profile and color data to retain all attributes
            self.data.update({"current_profile": profile, **color_data, "deviceTime": deviceTime})  # Ensure no data is lost

            return self.data

        except Exception as e:
            _LOGGER.error("Error fetching data from Helialux device: %s", e)
            return {}  # Ensure empty dictionary on failure