from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging
from dacite import from_dict

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.const import (
    UnitOfTemperature, REVOLUTIONS_PER_MINUTE, UnitOfPressure, UnitOfEnergy, UnitOfTime, UnitOfPower, PERCENTAGE,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.typing import StateType
from typing import Any

from .const import DOMAIN, MANUFACTURER
from .eplucon_api.DTO.DeviceDTO import DeviceDTO

_LOGGER = logging.getLogger(__name__)


@dataclass(kw_only=True)
class EpluconSensorEntityDescription(SensorEntityDescription):
    """Describes an Eplucon sensor entity."""
    key: str
    name: str
    exists_fn: Callable[[Any], bool] = lambda _: True
    value_fn: Callable[[Any], SensorEntityDescription]


# Define the sensor types
SENSORS: tuple[EpluconSensorEntityDescription, ...] = (
    EpluconSensorEntityDescription(
        key="indoor_temperature",
        name="Indoor Temperature",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        value_fn=lambda device: device.realtime_info.common.indoor_temperature,
        exists_fn=lambda device: device.realtime_info is not None and device.realtime_info.common is not None and device.realtime_info.common.indoor_temperature is not None,
    ),
    EpluconSensorEntityDescription(
        key="act_vent_rpm",
        name="Act Vent RPM",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=REVOLUTIONS_PER_MINUTE,
        value_fn=lambda device: device.realtime_info.common.act_vent_rpm,
        exists_fn=lambda device: device.realtime_info is not None and device.realtime_info.common is not None and device.realtime_info.common.act_vent_rpm is not None,
    ),

    EpluconSensorEntityDescription(
        key="brine_circulation_pump",
        name="Brine Circulation Pump",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda device: device.realtime_info.common.brine_circulation_pump,
        exists_fn=lambda device: device.realtime_info is not None and device.realtime_info.common is not None and device.realtime_info.common.brine_circulation_pump is not None,
    ),
    EpluconSensorEntityDescription(
        key="brine_in_temperature",
        name="Brine In Temperature",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        value_fn=lambda device: device.realtime_info.common.brine_in_temperature,
        exists_fn=lambda device: device.realtime_info is not None and device.realtime_info.common is not None and device.realtime_info.common.brine_in_temperature is not None,
    ),
    EpluconSensorEntityDescription(
        key="brine_out_temperature",
        name="Brine Out Temperature",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        value_fn=lambda device: device.realtime_info.common.brine_out_temperature,
        exists_fn=lambda device: device.realtime_info is not None and device.realtime_info.common is not None and device.realtime_info.common.brine_out_temperature is not None,
    ),
    EpluconSensorEntityDescription(
        key="brine_pressure",
        name="Brine Pressure",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPressure.BAR,
        device_class=SensorDeviceClass.PRESSURE,
        value_fn=lambda device: device.realtime_info.common.brine_pressure,
        exists_fn=lambda device: device.realtime_info is not None and device.realtime_info.common is not None and device.realtime_info.common.brine_pressure is not None,
    ),
    EpluconSensorEntityDescription(
        key="compressor_speed",
        name="Compressor Speed",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=REVOLUTIONS_PER_MINUTE,
        value_fn=lambda device: device.realtime_info.common.compressor_speed,
        exists_fn=lambda device: device.realtime_info is not None and device.realtime_info.common is not None and device.realtime_info.common.compressor_speed is not None,
    ),
    EpluconSensorEntityDescription(
        key="condensation_temperature",
        name="Condensation Temperature",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        value_fn=lambda device: device.realtime_info.common.condensation_temperature,
        exists_fn=lambda device: device.realtime_info is not None and device.realtime_info.common is not None and device.realtime_info.common.condensation_temperature is not None,
    ),
    EpluconSensorEntityDescription(
        key="configured_indoor_temperature",
        name="Configured Indoor Temperature",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        value_fn=lambda device: device.realtime_info.common.configured_indoor_temperature,
        exists_fn=lambda device: device.realtime_info is not None and device.realtime_info.common is not None and device.realtime_info.common.configured_indoor_temperature is not None,
    ),

    EpluconSensorEntityDescription(
        key="cv_pressure",
        name="CV Pressure",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPressure.BAR,
        device_class=SensorDeviceClass.PRESSURE,
        value_fn=lambda device: device.realtime_info.common.cv_pressure,
        exists_fn=lambda device: device.realtime_info is not None and device.realtime_info.common is not None and device.realtime_info.common.cv_pressure is not None,
    ),
    EpluconSensorEntityDescription(
        key="energy_delivered",
        name="Energy Delivered",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        value_fn=lambda device: device.realtime_info.common.energy_delivered,
        exists_fn=lambda device: device.realtime_info is not None and device.realtime_info.common is not None and device.realtime_info.common.energy_delivered is not None,
    ),
    EpluconSensorEntityDescription(
        key="energy_usage",
        name="Energy Usage",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        value_fn=lambda device: device.realtime_info.common.energy_usage,
        exists_fn=lambda device: device.realtime_info is not None and device.realtime_info.common is not None and device.realtime_info.common.energy_usage is not None,
    ),
    EpluconSensorEntityDescription(
        key="evaporation_temperature",
        name="Evaporation Temperature",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        value_fn=lambda device: device.realtime_info.common.evaporation_temperature,
        exists_fn=lambda device: device.realtime_info is not None and device.realtime_info.common is not None and device.realtime_info.common.evaporation_temperature is not None,
    ),
    EpluconSensorEntityDescription(
        key="export_energy",
        name="Export Energy",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        value_fn=lambda device: device.realtime_info.common.export_energy / 100 if device.realtime_info.common.export_energy > 0 else device.realtime_info.common.export_energy,
        exists_fn=lambda device: device.realtime_info is not None and device.realtime_info.common is not None and device.realtime_info.common.export_energy is not None,
    ),
    EpluconSensorEntityDescription(
        key="heating_in_temperature",
        name="Heating In Temperature",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        value_fn=lambda device: device.realtime_info.common.heating_in_temperature,
        exists_fn=lambda device: device.realtime_info is not None and device.realtime_info.common is not None and device.realtime_info.common.heating_in_temperature is not None,
    ),

    EpluconSensorEntityDescription(
        key="heating_out_temperature",
        name="Heating Out Temperature",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        value_fn=lambda device: device.realtime_info.common.heating_out_temperature,
        exists_fn=lambda device: device.realtime_info is not None and device.realtime_info.common is not None and device.realtime_info.common.heating_out_temperature is not None,
    ),
    EpluconSensorEntityDescription(
        key="import_energy",
        name="Import Energy",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        value_fn=lambda device: device.realtime_info.common.import_energy / 100 if device.realtime_info.common.import_energy > 0 else device.realtime_info.common.import_energy,
        exists_fn=lambda device: device.realtime_info is not None and device.realtime_info.common is not None and device.realtime_info.common.import_energy is not None,
    ),
    EpluconSensorEntityDescription(
        key="inverter_temperature",
        name="Inverter Temperature",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        value_fn=lambda device: device.realtime_info.common.inverter_temperature,
        exists_fn=lambda device: device.realtime_info is not None and device.realtime_info.common is not None and device.realtime_info.common.inverter_temperature is not None,
    ),

    EpluconSensorEntityDescription(
        key="operating_hours",
        name="Operating Hours",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTime.HOURS,
        device_class=SensorDeviceClass.DURATION,
        value_fn=lambda device: device.realtime_info.common.operating_hours,
        exists_fn=lambda device: device.realtime_info is not None and device.realtime_info.common is not None and device.realtime_info.common.operating_hours is not None,
    ),

    EpluconSensorEntityDescription(
        key="outdoor_temperature",
        name="Outdoor Temperature",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        value_fn=lambda device: device.realtime_info.common.outdoor_temperature,
        exists_fn=lambda device: device.realtime_info is not None and device.realtime_info.common is not None and device.realtime_info.common.outdoor_temperature is not None,
    ),
    EpluconSensorEntityDescription(
        key="overheating",
        name="Overheating",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        value_fn=lambda device: device.realtime_info.common.overheating,
        exists_fn=lambda device: device.realtime_info is not None and device.realtime_info.common is not None and device.realtime_info.common.overheating is not None,
    ),
    EpluconSensorEntityDescription(
        key="press_gas_pressure",
        name="Press Gas Pressure",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPressure.BAR,
        device_class=SensorDeviceClass.PRESSURE,
        value_fn=lambda device: device.realtime_info.common.press_gas_pressure,
        exists_fn=lambda device: device.realtime_info is not None and device.realtime_info.common is not None and device.realtime_info.common.press_gas_pressure is not None,
    ),
    EpluconSensorEntityDescription(
        key="press_gas_temperature",
        name="Press Gas Temperature",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        value_fn=lambda device: device.realtime_info.common.press_gas_temperature,
        exists_fn=lambda device: device.realtime_info is not None and device.realtime_info.common is not None and device.realtime_info.common.press_gas_temperature is not None,
    ),
    EpluconSensorEntityDescription(
        key="production_circulation_pump",
        name="Production Circulation Pump",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda device: device.realtime_info.common.production_circulation_pump,
        exists_fn=lambda device: device.realtime_info is not None and device.realtime_info.common is not None and device.realtime_info.common.production_circulation_pump is not None,
    ),
    EpluconSensorEntityDescription(
        key="suction_gas_pressure",
        name="Suction Gas Pressure",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPressure.BAR,
        device_class=SensorDeviceClass.PRESSURE,
        value_fn=lambda device: device.realtime_info.common.suction_gas_pressure,
        exists_fn=lambda device: device.realtime_info is not None and device.realtime_info.common is not None and device.realtime_info.common.suction_gas_pressure is not None,
    ),
    EpluconSensorEntityDescription(
        key="suction_gas_temperature",
        name="Suction Gas Temperature",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        value_fn=lambda device: device.realtime_info.common.suction_gas_temperature,
        exists_fn=lambda device: device.realtime_info is not None and device.realtime_info.common is not None and device.realtime_info.common.suction_gas_temperature is not None,
    ),
    EpluconSensorEntityDescription(
        key="total_active_power",
        name="Total Active Power",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        value_fn=lambda device: device.realtime_info.common.total_active_power,
        exists_fn=lambda device: device.realtime_info is not None and device.realtime_info.common is not None and device.realtime_info.common.total_active_power is not None,
    ),
    EpluconSensorEntityDescription(
        key="ww_temperature",
        name="WW Temperature",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        value_fn=lambda device: device.realtime_info.common.ww_temperature,
        exists_fn=lambda device: device.realtime_info is not None and device.realtime_info.common is not None and device.realtime_info.common.ww_temperature is not None,
    ),
    EpluconSensorEntityDescription(
        key="ww_temperature_configured",
        name="WW Temperature Configured",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        value_fn=lambda device: device.realtime_info.common.ww_temperature_configured,
        exists_fn=lambda device: device.realtime_info is not None and device.realtime_info.common is not None and device.realtime_info.common.ww_temperature_configured is not None,
    ),
    EpluconSensorEntityDescription(
        key="active_requests_ww",
        name="Active WW request",
        device_class=BinarySensorDeviceClass.HEAT,
        value_fn=lambda device: "ON" if device.realtime_info.common.active_requests_ww in ["ON", "1"] else "OFF",
        exists_fn=lambda device: device.realtime_info is not None and device.realtime_info.common is not None and device.realtime_info.common.active_requests_ww is not None,
    ),
    EpluconSensorEntityDescription(
        key="dg1",
        name="Direct Outlet (DG1)",
        value_fn=lambda device: "ON" if device.realtime_info.common.dg1 in ["ON", "1"] else "OFF",
        exists_fn=lambda device: device.realtime_info is not None and device.realtime_info.common is not None and device.realtime_info.common.dg1 is not None,
    ),
    EpluconSensorEntityDescription(
        key="sg2",
        name="Mixture Outlet (SG2)",
        value_fn=lambda device: "ON" if device.realtime_info.common.sg2 in ["ON", "1"] else "OFF",
        exists_fn=lambda device: device.realtime_info is not None and device.realtime_info.common is not None and device.realtime_info.common.sg2 is not None,
    ),
    EpluconSensorEntityDescription(
        key="sg3",
        name="Mixture Outlet (SG3)",
        value_fn=lambda device: "ON" if device.realtime_info.common.sg3 in ["ON", "1"] else "OFF",
exists_fn=lambda device: device.realtime_info is not None and device.realtime_info.common is not None and device.realtime_info.common.sg3 is not None,
    ),
    EpluconSensorEntityDescription(
        key="sg4",
        name="Mixture Outlet (SG4)",
        value_fn=lambda device: "ON" if device.realtime_info.common.sg4 in ["ON", "1"] else "OFF",
        exists_fn=lambda device: device.realtime_info is not None and device.realtime_info.common is not None and device.realtime_info.common.sg4 is not None,
    ),
    EpluconSensorEntityDescription(
        key="spf",
        name="Seasonal Performance Factor (SPF)",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda device: device.realtime_info.common.spf,
        exists_fn=lambda device: device.realtime_info is not None and device.realtime_info.common is not None and device.realtime_info.common.spf is not None,
    ),
    EpluconSensorEntityDescription(
        key="position_expansion_ventil",
        name="Position Expansion Ventil",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda device: device.realtime_info.common.position_expansion_ventil,
        exists_fn=lambda device: device.realtime_info is not None and device.realtime_info.common is not None and device.realtime_info.common.position_expansion_ventil is not None,
    ),
    EpluconSensorEntityDescription(
        key="number_of_starts",
        name="Number of Starts",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda device: device.realtime_info.common.number_of_starts,
        exists_fn=lambda device: device.realtime_info is not None and device.realtime_info.common is not None and device.realtime_info.common.number_of_starts is not None,
    ),
    EpluconSensorEntityDescription(
        key="heating_mode",
        name="Heating Mode",
        device_class=SensorDeviceClass.ENUM,
        value_fn=lambda device: device.realtime_info.common.heating_mode,
        exists_fn=lambda device: device.realtime_info is not None and device.realtime_info.common is not None and device.realtime_info.common.heating_mode is not None,
    ),
    EpluconSensorEntityDescription(
        key="warmwater",
        name="Warm Water",
        device_class=BinarySensorDeviceClass.HEAT,
        value_fn=lambda device: "ON" if device.realtime_info.common.warmwater in ["ON", "1"] else "OFF",
        exists_fn=lambda device: device.realtime_info is not None and device.realtime_info.common is not None and device.realtime_info.common.warmwater is not None,
    ),
    EpluconSensorEntityDescription(
        key="alarm_active",
        name="Alarm Active",
        value_fn=lambda device: "ON" if device.realtime_info.common.alarm_active in ["ON", "1"] else "OFF",
        exists_fn=lambda device: device.realtime_info is not None and device.realtime_info.common is not None and device.realtime_info.common.alarm_active is not None,
    ),
    EpluconSensorEntityDescription(
        key="current_heating_pump_state",
        name="Current Heating Pump State",
        value_fn=lambda device: "ON" if device.realtime_info.common.current_heating_pump_state in ["ON", "1"] else "OFF",
        exists_fn=lambda device: device.realtime_info is not None and device.realtime_info.common is not None and device.realtime_info.common.current_heating_pump_state is not None,
    ),
    EpluconSensorEntityDescription(
        key="current_heating_state",
        name="Current Heating State",
        value_fn=lambda device: "ON" if device.realtime_info.common.current_heating_state in ["ON", "1"] else "OFF",
        exists_fn=lambda device: device.realtime_info is not None and device.realtime_info.common is not None and device.realtime_info.common.current_heating_state is not None,
    ),
    EpluconSensorEntityDescription(
        key="operation_mode",
        name="Operation Mode",
        device_class=SensorDeviceClass.ENUM,
        value_fn=lambda device: device.realtime_info.common.operation_mode,
        exists_fn=lambda device: device.realtime_info is not None and device.realtime_info.common is not None and device.realtime_info.common.operation_mode is not None,
    ),
    EpluconSensorEntityDescription(
        key="heatloading_active",
        name="Heatloading Active",
        device_class=SensorDeviceClass.ENUM,
        value_fn=lambda device: device.heatloading_status.heatloading_active,
        exists_fn=lambda device: device.heatloading_status is not None and device.heatloading_status.heatloading_active is not None,
    ),
    EpluconSensorEntityDescription(
        key="domestic_hot_water",
        name="Domestic Hot Water",
        device_class=SensorDeviceClass.ENUM,
        value_fn=lambda device: device.heatloading_status.configurations["domestic_hot_water"],
        exists_fn=lambda device: device.heatloading_status is not None and device.heatloading_status.configurations is not None and "domestic_hot_water" in device.heatloading_status.configurations,
    ),
    EpluconSensorEntityDescription(
        key="heatloading_for_heating",
        name="Heatloading for Heating",
        device_class=SensorDeviceClass.ENUM,
        value_fn=lambda device: device.heatloading_status.configurations["domestic_hot_water"],
        exists_fn=lambda device: device.heatloading_status is not None and device.heatloading_status.configurations is not None and "heatloading_for_heating" in device.heatloading_status.configurations,
    ),
    EpluconSensorEntityDescription(
        key="operation_mode_text",
        name="Operation Mode Text",
        device_class=SensorDeviceClass.ENUM,
        value_fn=lambda device: get_friendly_operation_mode_text(device),
        exists_fn=lambda device: device.realtime_info is not None and device.realtime_info.common is not None and device.realtime_info.common.operation_mode is not None,
    ),
    EpluconSensorEntityDescription(
        key="heating_mode_text",
        name="Heating Mode Text",
        device_class=SensorDeviceClass.ENUM,
        value_fn=lambda device: get_friendly_heating_mode_text(device),
        exists_fn=lambda device: device.realtime_info is not None and device.realtime_info.common is not None and device.realtime_info.common.heating_mode is not None,
    ),
)

def get_friendly_operation_mode_text(device: DeviceDTO) -> str:
    # TODO: Consider adding localization options for the operation mode text, now hardcoded Dutch.
    try:
        operation_mode = int(device.realtime_info.common.operation_mode)
        _LOGGER.debug(f"Converting operation mode {operation_mode} for device {device.id}")
    except (TypeError, ValueError) as e:
        _LOGGER.warning(f"Operation mode is not available or invalid for device {device.id}: {e}")
        return "Unavailable"

    mode_text = {
        1: "Koeling",
        2: "Verwarming", 
        3: "Auto th-TOUCH",
        4: "Auto Wp",
        5: "Haard"
    }.get(operation_mode, "Unknown operation mode")
    
    _LOGGER.debug(f"Operation mode {operation_mode} converted to '{mode_text}' for device {device.id}")
    return mode_text

def get_friendly_heating_mode_text(device: DeviceDTO) -> str:
    try:
        heating_mode = int(device.realtime_info.common.heating_mode)
        _LOGGER.debug(f"Converting heating mode {heating_mode} for device {device.id}")
    except (TypeError, ValueError) as e:
        _LOGGER.warning(f"Heating mode is not available or invalid for device {device.id}: {e}")
        return "Unavailable"

    mode_text = {
        0: "Off",
        1: "On",
        2: "Emergency operation",
        3: "APX"
    }.get(heating_mode, "Unknown heating mode")
    
    _LOGGER.debug(f"Heating mode {heating_mode} converted to '{mode_text}' for device {device.id}")
    return mode_text

async def async_setup_entry(
        hass: HomeAssistant,
        entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Eplucon sensor based on a config entry."""
    _LOGGER.info(f"Setting up Eplucon sensors for entry: {entry.entry_id}")
    coordinator = hass.data[DOMAIN][entry.entry_id]

    # Ensure the coordinator has refreshed its data
    _LOGGER.debug("Ensuring coordinator has fresh data")
    await coordinator.async_config_entry_first_refresh()

    devices = coordinator.data
    _LOGGER.info(f"Processing {len(devices)} devices for sensor creation")

    list_device_dto: list[DeviceDTO] = list()

    for i, device in enumerate(devices):
        _LOGGER.debug(f"Processing device {i+1}/{len(devices)}: {device}")
        if isinstance(device, dict):
            device = from_dict(data_class=DeviceDTO, data=device)
            _LOGGER.debug(f"Converted dict to DeviceDTO: {device.name} (ID: {device.id})")
        list_device_dto.append(device)

    # Create sensors for each device
    sensors_to_add = []
    total_sensors = 0
    
    for device in list_device_dto:
        device_sensors = []
        for description in SENSORS:
            if description.exists_fn(device):
                sensor = EpluconSensorEntity(coordinator, device, description)
                device_sensors.append(sensor)
                sensors_to_add.append(sensor)
                _LOGGER.debug(f"Created sensor: {description.name} for device {device.name}")
            else:
                _LOGGER.debug(f"Skipping sensor {description.name} for device {device.name} - existence check failed")
        
        _LOGGER.info(f"Created {len(device_sensors)} sensors for device {device.name} (ID: {device.id})")
        total_sensors += len(device_sensors)

    _LOGGER.info(f"Adding {total_sensors} sensors to Home Assistant")
    async_add_entities(sensors_to_add)
    _LOGGER.info("Eplucon sensor setup completed successfully")


class EpluconSensorEntity(CoordinatorEntity, SensorEntity):
    """Representation of an Eplucon sensor."""

    entity_description: EpluconSensorEntityDescription

    def __init__(
            self, coordinator, device: DeviceDTO, entity_description: EpluconSensorEntityDescription
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.device = device
        self.entity_description = entity_description
        self._attr_name = f"{entity_description.name}"
        self._attr_unique_id = f"{device.id}_{entity_description.key}"
        _LOGGER.debug(f"Initializing sensor: {self._attr_name} (unique_id: {self._attr_unique_id}) for device {device.name}")
        self._update_device_data()
        _LOGGER.debug(f"Sensor initialized successfully: {self._attr_name}")

    @property
    def device_info(self) -> dict:
        """Return information to link this entity with the correct device."""
        device_info = {
            "manufacturer": MANUFACTURER,
            "identifiers": {(DOMAIN, self.device.account_module_index)},
        }
        _LOGGER.debug(f"Device info for sensor {self._attr_name}: {device_info}")
        return device_info

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        available = super().available and self.coordinator.last_update_success
        if not available:
            _LOGGER.warning(f"Sensor {self._attr_name} is unavailable - coordinator success: {self.coordinator.last_update_success}")
        return available

    def _update_device_data(self):
        """Update the internal data from the coordinator."""
        _LOGGER.debug(f"Updating device data for sensor {self._attr_name}")
        # Assuming devices are updated in the coordinator data
        updated = False
        for updated_device in self.coordinator.data:
            if isinstance(updated_device, dict):
                # Convert dictionary to DeviceDTO object
                updated_device = from_dict(data_class=DeviceDTO, data=updated_device)
            if updated_device.id == self.device.id:
                # Deep comparison of real-time data to detect changes
                old_value = None
                new_value = None
                if hasattr(self.device, 'realtime_info') and self.device.realtime_info and self.device.realtime_info.common:
                    try:
                        old_value = self.entity_description.value_fn(self.device)
                    except Exception:
                        pass
                
                old_device_name = self.device.name
                # Replace the entire device object with the updated one
                self.device = updated_device
                
                if hasattr(self.device, 'realtime_info') and self.device.realtime_info and self.device.realtime_info.common:
                    try:
                        new_value = self.entity_description.value_fn(self.device)
                        if old_value != new_value:
                            _LOGGER.debug(f"Sensor {self._attr_name} detected value change in device update: {old_value} -> {new_value}")
                    except Exception:
                        pass
                
                _LOGGER.debug(f"Updated device data for sensor {self._attr_name}: {old_device_name} -> {updated_device.name}")
                updated = True
                break
        
        if not updated:
            _LOGGER.warning(f"Could not find updated device data for sensor {self._attr_name} (device ID: {self.device.id})")

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        try:
            value = self.entity_description.value_fn(self.device)
            _LOGGER.debug(f"Sensor {self._attr_name} value: {value}")
            return value
        except Exception as e:
            _LOGGER.error(f"Error getting value for sensor {self._attr_name}: {type(e).__name__}: {e}")
            return None

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        _LOGGER.debug(f"Coordinator update received for sensor {self._attr_name}")
        try:
            # Make sure we have the latest data from coordinator
            self._update_device_data()
            
            # Get the old and new values to detect changes
            old_value = getattr(self, '_last_value', None)
            new_value = self.native_value
            
            if old_value != new_value:
                _LOGGER.debug(f"Sensor {self._attr_name} value changed: {old_value} -> {new_value}")
            else:
                _LOGGER.debug(f"Sensor {self._attr_name} value unchanged: {new_value}")
            
            # Store the new value for future comparisons
            self._last_value = new_value
            
            # Always write the state to Home Assistant, even if unchanged
            # This ensures the entity's timestamp gets updated in HA
            self.async_write_ha_state()
            
            # We don't call super()._handle_coordinator_update() because we're handling 
            # the state update ourselves above with async_write_ha_state().
            # This prevents potential conflicts or double updates.
            
            _LOGGER.debug(f"Coordinator update completed for sensor {self._attr_name}")
        except Exception as e:
            _LOGGER.error(f"Error handling coordinator update for sensor {self._attr_name}: {type(e).__name__}: {e}", exc_info=True)
