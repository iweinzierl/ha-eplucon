import logging
from datetime import timedelta
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import device_registry
from .eplucon_api.eplucon_client import EpluconApi, ApiError, DeviceDTO, BASE_URL
from .const import DOMAIN, PLATFORMS, EPLUCON_PORTAL_URL, MANUFACTURER, SUPPORTED_TYPES
from dacite import from_dict

_LOGGER = logging.getLogger(__name__)

# Time between data updates
UPDATE_INTERVAL = timedelta(seconds=30)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Eplucon from a config entry."""
    _LOGGER.info(f"Setting up Eplucon integration with entry ID: {entry.entry_id}")
    
    api_token = entry.data["api_token"]
    api_endpoint = entry.data.get("api_endpoint", BASE_URL)
    _LOGGER.debug(f"Using API endpoint: {api_endpoint}")

    devices = entry.data["devices"]
    _LOGGER.info(f"Found {len(devices)} devices in config entry")

    session = async_get_clientsession(hass)
    client = EpluconApi(api_token, api_endpoint, session)

    _LOGGER.debug("Registering devices in Home Assistant device registry")
    await register_devices(devices, entry, hass)

    async def async_update_data() -> list[DeviceDTO]:
        """Fetch Eplucon data from API endpoint."""
        _LOGGER.debug("Starting coordinator data update cycle")
        try:
            entry_devices = entry.data["devices"]
            _LOGGER.info(f"Fetching data from Eplucon API for {len(entry_devices)} devices")

            # For each device, fetch the real-time info and combine it with the device data
            for i, entry_device in enumerate(entry_devices):
                _LOGGER.debug(f"Processing device {i+1}/{len(entry_devices)}: {entry_device}")
                entry_device = await device_dict_to_dto(entry_device)

                _LOGGER.debug(f"Converted to DTO - Device ID: {entry_device.id}, Name: {entry_device.name}, Type: {entry_device.type}")

                # Skip unsupported devices
                if entry_device.type not in SUPPORTED_TYPES:
                    _LOGGER.warning(f"Device {entry_device.name} (ID: {entry_device.id}) with type {entry_device.type} is not supported yet. Skipping...")
                    entry_devices.remove(entry_device)
                    continue

                _LOGGER.debug(f"Fetching realtime info for device {entry_device.id}")
                realtime_info = await client.get_realtime_info(entry_device.id)
                entry_device.realtime_info = realtime_info

                _LOGGER.debug(f"Fetching heatloading status for device {entry_device.id}")
                heatloading_status = await client.get_heatpump_heatloading_status(entry_device.id)
                entry_device.heatloading_status = heatloading_status
                
                _LOGGER.info(f"Successfully updated data for device {entry_device.name} (ID: {entry_device.id})")

            _LOGGER.info(f"Data update cycle completed successfully for {len(entry_devices)} devices")
            return entry_devices

        except ApiError as err:
            _LOGGER.error(f"Error fetching data from Eplucon API: {err}")
            raise err

        except Exception as err:
            _LOGGER.error(f"Unexpected error during data update: {type(err).__name__}: {err}", exc_info=True)
            raise err

    # Set up the coordinator to manage fetching data from the API
    _LOGGER.debug(f"Setting up DataUpdateCoordinator with {UPDATE_INTERVAL.total_seconds()}s update interval")
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="Eplucon devices",
        update_method=async_update_data,
        update_interval=UPDATE_INTERVAL,
    )

    # Fetch initial data so we have data when entities subscribe
    _LOGGER.debug("Performing initial coordinator refresh")
    await coordinator.async_config_entry_first_refresh()
    _LOGGER.info("Initial coordinator refresh completed successfully")

    # Store the coordinator in hass.data, so it's accessible in other parts of the integration
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # Forward the setup to the sensor platform
    _LOGGER.debug(f"Forwarding setup to platforms: {PLATFORMS}")
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _LOGGER.info("Eplucon integration setup completed successfully")
    return True


async def register_devices(devices, entry, hass):
    """Register devices in Home Assistant device registry."""
    _LOGGER.debug(f"Registering {len(devices)} devices in Home Assistant device registry")
    hass_device_registry = device_registry.async_get(hass)
    
    for i, device in enumerate(devices):
        device = await device_dict_to_dto(device)
        _LOGGER.debug(f"Registering device {i+1}/{len(devices)}: {device.name} (ID: {device.id})")

        registered_device = hass_device_registry.async_get_or_create(
            configuration_url=EPLUCON_PORTAL_URL,
            config_entry_id=entry.entry_id,
            identifiers={(DOMAIN, device.account_module_index)},
            manufacturer=MANUFACTURER,
            suggested_area="Utility Room",
            name=device.name,
            model=device.type,
        )
        _LOGGER.debug(f"Device registered successfully: {registered_device.name} with identifiers {registered_device.identifiers}")
    
    _LOGGER.info(f"Successfully registered {len(devices)} devices in Home Assistant")


async def device_dict_to_dto(device_dict: DeviceDTO|dict) -> DeviceDTO:
    """
        When retrieving given devices from HASS config flow the entry.data["devices"]
        is type list[DeviceDTO] but on boot this is a list[dict], not sure why and if this is intended,
        but this method will ensure we can parse the correct format here.
    """
    if isinstance(device_dict, dict):
        _LOGGER.debug(f"Converting device dict to DTO: {device_dict}")
        device_dict = from_dict(data_class=DeviceDTO, data=device_dict)
        _LOGGER.debug(f"Converted to DeviceDTO: ID={device_dict.id}, Name={device_dict.name}")
    else:
        _LOGGER.debug(f"Device already a DTO: ID={device_dict.id}, Name={device_dict.name}")
    return device_dict


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info(f"Unloading Eplucon integration entry: {entry.entry_id}")
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        _LOGGER.debug("Successfully unloaded platforms, removing coordinator from hass.data")
        hass.data[DOMAIN].pop(entry.entry_id)
        _LOGGER.info("Eplucon integration unloaded successfully")
    else:
        _LOGGER.error("Failed to unload Eplucon platforms")

    return unload_ok
