from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
from smart_heating.climate_controller import ClimateController
from smart_heating.const import (
    DEFAULT_FROST_PROTECTION_TEMP,
    PRESET_AWAY,
)
from smart_heating.models.area import Area


@pytest.mark.asyncio
async def test_set_area_logger_and_delegations(mock_hass, mock_area_manager):
    cc = ClimateController(mock_hass, mock_area_manager)
    logger = MagicMock()
    cc.set_area_logger(logger)
    assert cc.sensor_handler is not None
    assert cc.protection_handler is not None
    assert cc.cycle_handler is not None


@pytest.mark.asyncio
async def test_async_update_area_temperatures_updates(mock_hass, mock_area_manager):
    cc = ClimateController(mock_hass, mock_area_manager)
    # Prepare area
    area = MagicMock()
    area.get_temperature_sensors.return_value = ["s1"]
    area.get_thermostats.return_value = []
    area.current_temperature = None
    mock_area_manager.get_all_areas.return_value = {"a1": area}
    # Patch handler
    cc.temp_handler = MagicMock()
    cc.temp_handler.collect_area_temperatures.return_value = [20.0, 21.0]
    await cc.async_update_area_temperatures()
    assert abs(area.current_temperature - 20.5) < 1e-6


@pytest.mark.asyncio
async def test_async_control_heating_disabled_and_manual_override(mock_hass, mock_area_manager):
    cc = ClimateController(mock_hass, mock_area_manager)
    # Area disabled
    area = MagicMock()
    area.enabled = False
    area.current_temperature = 20.0
    mock_area_manager.get_all_areas.return_value = {"a1": area}
    # Set handlers
    cc.cycle_handler = MagicMock()
    cc.cycle_handler.async_prepare_heating_cycle = AsyncMock(return_value=(False, None))
    cc.protection_handler = MagicMock()
    cc.device_handler = MagicMock()
    cc.device_handler.async_control_opentherm_gateway = AsyncMock()
    cc.temp_handler = MagicMock()
    # Ensure protection handler async_handle_disabled_area is awaited
    cc.protection_handler.async_handle_disabled_area = AsyncMock()
    await cc.async_control_heating()
    cc.protection_handler.async_handle_disabled_area.assert_called()


@pytest.mark.asyncio
async def test_async_control_heating_heating_path(mock_hass, mock_area_manager):
    cc = ClimateController(mock_hass, mock_area_manager)
    area = MagicMock()
    area.enabled = True
    area.current_temperature = 18.0
    area.target_temperature = 21.0
    area.hvac_mode = "heat"
    area.hysteresis_override = None
    area.boost_mode_active = False
    area.preset_mode = "comfort"
    area.manual_override = False
    area.get_effective_target_temperature = MagicMock(return_value=21.0)
    mock_area_manager.get_all_areas.return_value = {"a1": area}
    # Set handlers
    cc.temp_handler = MagicMock()
    cc.device_handler = MagicMock()
    cc.device_handler.async_control_opentherm_gateway = AsyncMock()
    # cycle handler should return (should_record_history, tracker) but we'll set up async_prepare_heating_cycle
    tracker = MagicMock()
    tracker.async_record_temperature = AsyncMock()
    cc.cycle_handler = MagicMock()
    cc.cycle_handler.async_prepare_heating_cycle = AsyncMock(return_value=(False, None))
    cc.cycle_handler.async_handle_heating_required = AsyncMock(return_value=([], 21.0))
    cc.protection_handler = MagicMock()
    cc.protection_handler.apply_vacation_mode = MagicMock()
    cc.protection_handler.apply_frost_protection = MagicMock(return_value=21.0)
    cc.protection_handler.async_handle_manual_override = AsyncMock()
    await cc.async_control_heating()
    cc.cycle_handler.async_handle_heating_required.assert_called()


@pytest.fixture
def mock_hass():
    """Create mock Home Assistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    hass.services = MagicMock()
    hass.services.async_call = AsyncMock()
    hass.states = MagicMock()
    hass.data = {"smart_heating": {}}
    return hass


@pytest.fixture
def mock_area_manager(mock_hass):
    """Create mock area manager."""
    manager = MagicMock()
    manager.hass = mock_hass
    manager.get_all_areas = MagicMock(return_value={})
    manager.async_save = AsyncMock()
    manager.frost_protection_enabled = True
    manager.frost_protection_temp = DEFAULT_FROST_PROTECTION_TEMP
    manager.opentherm_gateway_id = None
    return manager


@pytest.fixture
def mock_learning_engine():
    """Create mock learning engine."""
    engine = MagicMock()
    engine.async_start_heating_event = AsyncMock()
    engine.async_end_heating_event = AsyncMock()
    return engine


@pytest.fixture
def mock_area_logger():
    """Create mock area logger."""
    logger = MagicMock()
    logger.log_event = MagicMock()
    return logger


@pytest.fixture
def climate_controller(mock_hass, mock_area_manager, mock_learning_engine, mock_area_logger):
    """Create ClimateController instance."""
    controller = ClimateController(
        hass=mock_hass,
        area_manager=mock_area_manager,
        learning_engine=mock_learning_engine,
    )
    # Initialize handlers via set_area_logger
    controller.set_area_logger(mock_area_logger)
    return controller


@pytest.fixture
def mock_area():
    """Create mock area."""
    area = MagicMock(spec=Area)
    area.area_id = "living_room"
    area.name = "Living Room"
    area.enabled = True
    area.target_temperature = 20.0
    area.current_temperature = 18.0
    area.state = "heating"
    area.boost_mode_active = False
    area.boost_temp = 22.0
    area.preset_mode = "none"
    area.hvac_mode = "heat"
    area.hysteresis_override = None
    area.window_is_open = False
    area.window_sensors = []
    area.presence_detected = False
    area.presence_sensors = []
    area.shutdown_switches_when_idle = True
    area.devices = {}
    area.primary_temperature_sensor = None  # Default to auto mode
    area.get_effective_target_temperature = MagicMock(return_value=20.0)
    area.get_temperature_sensors = MagicMock(return_value=[])
    area.get_thermostats = MagicMock(return_value=[])
    area.get_valves = MagicMock(return_value=[])
    area.get_switches = MagicMock(return_value=[])
    area.check_boost_expiry = MagicMock()
    return area


class TestClimateControllerInit:
    """Test ClimateController initialization."""

    def test_init_with_valid_params(self, mock_hass, mock_area_manager, mock_learning_engine):
        """Test initialization with valid parameters."""
        controller = ClimateController(
            hass=mock_hass,
            area_manager=mock_area_manager,
            learning_engine=mock_learning_engine,
        )

        assert controller.hass == mock_hass
        assert controller.area_manager == mock_area_manager
        assert controller.learning_engine == mock_learning_engine
        assert controller._hysteresis == pytest.approx(0.5)  # Default hysteresis

    def test_init_sets_default_hysteresis(self, mock_hass, mock_area_manager, mock_learning_engine):
        """Test initialization sets default hysteresis."""
        controller = ClimateController(
            hass=mock_hass,
            area_manager=mock_area_manager,
            learning_engine=mock_learning_engine,
        )

        assert controller._hysteresis == pytest.approx(0.5)


class TestTemperatureConversion:
    """Test temperature conversion methods."""

    def test_convert_fahrenheit_to_celsius(self, climate_controller):
        """Test Fahrenheit to Celsius conversion."""
        # Freezing point
        assert climate_controller._convert_fahrenheit_to_celsius(32.0) == pytest.approx(
            0.0, abs=0.01
        )

        # Room temperature
        assert climate_controller._convert_fahrenheit_to_celsius(68.0) == pytest.approx(
            20.0, abs=0.01
        )

        # Boiling point
        assert climate_controller._convert_fahrenheit_to_celsius(212.0) == pytest.approx(
            100.0, abs=0.01
        )


class TestTemperatureSensorReading:
    """Test temperature sensor reading methods."""

    def test_get_temperature_from_sensor_celsius(self, climate_controller, mock_hass):
        """Test reading temperature from sensor in Celsius."""
        mock_state = MagicMock()
        mock_state.state = "21.5"
        mock_state.attributes = {"unit_of_measurement": "°C"}
        mock_hass.states.get = MagicMock(return_value=mock_state)

        temp = climate_controller._get_temperature_from_sensor("sensor.living_room_temp")

        assert temp == pytest.approx(21.5)

    def test_get_temperature_from_sensor_fahrenheit(self, climate_controller, mock_hass):
        """Test reading temperature from sensor in Fahrenheit."""
        mock_state = MagicMock()
        mock_state.state = "70.0"
        mock_state.attributes = {"unit_of_measurement": "°F"}
        mock_hass.states.get = MagicMock(return_value=mock_state)

        temp = climate_controller._get_temperature_from_sensor("sensor.living_room_temp")

        assert temp == pytest.approx(21.11, abs=0.01)

    def test_get_temperature_from_sensor_unavailable(self, climate_controller, mock_hass):
        """Test reading from unavailable sensor."""
        mock_state = MagicMock()
        mock_state.state = "unavailable"
        mock_hass.states.get = MagicMock(return_value=mock_state)

        temp = climate_controller._get_temperature_from_sensor("sensor.living_room_temp")

        assert temp is None

    def test_get_temperature_from_sensor_invalid_value(self, climate_controller, mock_hass):
        """Test reading invalid temperature value."""
        mock_state = MagicMock()
        mock_state.state = "not_a_number"
        mock_state.attributes = {"unit_of_measurement": "°C"}
        mock_hass.states.get = MagicMock(return_value=mock_state)

        temp = climate_controller._get_temperature_from_sensor("sensor.living_room_temp")

        assert temp is None

    def test_get_temperature_from_thermostat_celsius(self, climate_controller, mock_hass):
        """Test reading current temperature from thermostat in Celsius."""
        mock_state = MagicMock()
        mock_state.state = "heat"
        mock_state.attributes = {
            "current_temperature": 22.0,
            "unit_of_measurement": "°C",
        }
        mock_hass.states.get = MagicMock(return_value=mock_state)

        temp = climate_controller._get_temperature_from_thermostat("climate.living_room")

        assert temp == pytest.approx(22.0)

    def test_get_temperature_from_thermostat_fahrenheit(self, climate_controller, mock_hass):
        """Test reading current temperature from thermostat in Fahrenheit."""
        mock_state = MagicMock()
        mock_state.state = "heat"
        mock_state.attributes = {
            "current_temperature": 72.0,
            "unit_of_measurement": "°F",
        }
        mock_hass.states.get = MagicMock(return_value=mock_state)

        temp = climate_controller._get_temperature_from_thermostat("climate.living_room")

        assert temp == pytest.approx(22.22, abs=0.01)

    def test_get_temperature_from_thermostat_no_current_temp(self, climate_controller, mock_hass):
        """Test reading from thermostat without current_temperature."""
        mock_state = MagicMock()
        mock_state.state = "heat"
        mock_state.attributes = {}
        mock_hass.states.get = MagicMock(return_value=mock_state)

        temp = climate_controller._get_temperature_from_thermostat("climate.living_room")

        assert temp is None


class TestAreaTemperatureCollection:
    """Test area temperature collection."""

    def test_collect_area_temperatures_from_sensors(self, climate_controller, mock_area, mock_hass):
        """Test collecting temperatures from sensors only."""
        mock_area.get_temperature_sensors.return_value = [
            "sensor.temp1",
            "sensor.temp2",
        ]
        mock_area.get_thermostats.return_value = []

        # Mock sensor states
        def get_state(entity_id):
            mock_state = MagicMock()
            if entity_id == "sensor.temp1":
                mock_state.state = "21.0"
            elif entity_id == "sensor.temp2":
                mock_state.state = "22.0"
            mock_state.attributes = {"unit_of_measurement": "°C"}
            return mock_state

        mock_hass.states.get = MagicMock(side_effect=get_state)

        temps = climate_controller._collect_area_temperatures(mock_area)

        assert len(temps) == 2
        assert 21.0 in temps
        assert 22.0 in temps

    def test_collect_area_temperatures_from_thermostats(
        self, climate_controller, mock_area, mock_hass
    ):
        """Test collecting temperatures from thermostats only."""
        mock_area.get_temperature_sensors.return_value = []
        mock_area.get_thermostats.return_value = ["climate.therm1"]

        mock_state = MagicMock()
        mock_state.state = "heat"
        mock_state.attributes = {
            "current_temperature": 20.5,
            "unit_of_measurement": "°C",
        }
        mock_hass.states.get = MagicMock(return_value=mock_state)

        temps = climate_controller._collect_area_temperatures(mock_area)

        assert len(temps) == 1
        assert temps[0] == pytest.approx(20.5)

    def test_collect_area_temperatures_mixed_sources(
        self, climate_controller, mock_area, mock_hass
    ):
        """Test collecting temperatures from both sensors and thermostats."""
        mock_area.get_temperature_sensors.return_value = ["sensor.temp1"]
        mock_area.get_thermostats.return_value = ["climate.therm1"]

        def get_state(entity_id):
            mock_state = MagicMock()
            if entity_id == "sensor.temp1":
                mock_state.state = "21.0"
                mock_state.attributes = {"unit_of_measurement": "°C"}
            elif entity_id == "climate.therm1":
                mock_state.state = "heat"
                mock_state.attributes = {
                    "current_temperature": 20.0,
                    "unit_of_measurement": "°C",
                }
            return mock_state

        mock_hass.states.get = MagicMock(side_effect=get_state)

        temps = climate_controller._collect_area_temperatures(mock_area)

        assert len(temps) == 2
        assert 21.0 in temps
        assert 20.0 in temps


class TestAsyncUpdateAreaTemperatures:
    """Test async_update_area_temperatures method."""

    @pytest.mark.asyncio
    async def test_update_single_area(
        self, climate_controller, mock_area, mock_area_manager, mock_hass
    ):
        """Test updating temperature for a single area."""
        mock_area.get_temperature_sensors.return_value = [
            "sensor.temp1",
            "sensor.temp2",
        ]
        mock_area.get_thermostats.return_value = []
        mock_area_manager.get_all_areas.return_value = {"living_room": mock_area}

        # Mock sensor states
        def get_state(entity_id):
            mock_state = MagicMock()
            if entity_id == "sensor.temp1":
                mock_state.state = "20.0"
            elif entity_id == "sensor.temp2":
                mock_state.state = "22.0"
            mock_state.attributes = {"unit_of_measurement": "°C"}
            return mock_state

        mock_hass.states.get = MagicMock(side_effect=get_state)

        await climate_controller.async_update_area_temperatures()

        # Average of 20.0 and 22.0 should be 21.0
        assert mock_area.current_temperature == pytest.approx(21.0)

    @pytest.mark.asyncio
    async def test_update_multiple_areas(self, climate_controller, mock_area_manager, mock_hass):
        """Test updating temperatures for multiple areas."""
        area1 = MagicMock(spec=Area)
        area1.area_id = "living_room"
        area1.primary_temperature_sensor = None
        area1.get_temperature_sensors = MagicMock(return_value=["sensor.lr_temp"])
        area1.get_thermostats = MagicMock(return_value=[])

        area2 = MagicMock(spec=Area)
        area2.area_id = "bedroom"
        area2.primary_temperature_sensor = None
        area2.get_temperature_sensors = MagicMock(return_value=["sensor.br_temp"])
        area2.get_thermostats = MagicMock(return_value=[])

        mock_area_manager.get_all_areas.return_value = {
            "living_room": area1,
            "bedroom": area2,
        }

        def get_state(entity_id):
            mock_state = MagicMock()
            if entity_id == "sensor.lr_temp":
                mock_state.state = "21.0"
            elif entity_id == "sensor.br_temp":
                mock_state.state = "19.0"
            mock_state.attributes = {"unit_of_measurement": "°C"}
            return mock_state

        mock_hass.states.get = MagicMock(side_effect=get_state)

        await climate_controller.async_update_area_temperatures()

        assert area1.current_temperature == pytest.approx(21.0)
        assert area2.current_temperature == pytest.approx(19.0)

    @pytest.mark.asyncio
    async def test_skip_area_without_sensors(
        self, climate_controller, mock_area, mock_area_manager
    ):
        """Test skipping areas without temperature sensors."""
        mock_area.get_temperature_sensors.return_value = []
        mock_area.get_thermostats.return_value = []
        mock_area_manager.get_all_areas.return_value = {"living_room": mock_area}

        await climate_controller.async_update_area_temperatures()

        # Should not set current_temperature if no sensors
        # (mock doesn't track attribute assignments unless explicitly configured)


class TestFrostProtection:
    """Test frost protection logic."""

    def test_apply_frost_protection_enabled_below_threshold(
        self, climate_controller, mock_area_manager
    ):
        """Test frost protection when enabled and temperature below threshold."""
        mock_area_manager.frost_protection_enabled = True
        mock_area_manager.frost_protection_temp = 7.0

        # Try to set temperature below frost protection
        result = climate_controller._apply_frost_protection("living_room", 5.0)

        assert result == pytest.approx(7.0)

    def test_apply_frost_protection_enabled_above_threshold(
        self, climate_controller, mock_area_manager
    ):
        """Test frost protection when temperature above threshold."""
        mock_area_manager.frost_protection_enabled = True
        mock_area_manager.frost_protection_temp = 7.0

        # Temperature above frost protection
        result = climate_controller._apply_frost_protection("living_room", 20.0)

        assert result == pytest.approx(20.0)

    def test_apply_frost_protection_disabled(self, climate_controller, mock_area_manager):
        """Test frost protection when disabled."""
        mock_area_manager.frost_protection_enabled = False

        # Should not apply frost protection even if temp is low
        result = climate_controller._apply_frost_protection("living_room", 5.0)

        assert result == pytest.approx(5.0)


class TestVacationMode:
    """Test vacation mode application."""

    def test_apply_vacation_mode_not_active(self, climate_controller, mock_area, mock_area_manager):
        """Test vacation mode when not active."""
        mock_area_manager.vacation_mode_active = False

        original_preset = mock_area.preset_mode
        climate_controller._apply_vacation_mode("living_room", mock_area)

        # Preset should not change
        assert mock_area.preset_mode == original_preset

    def test_apply_vacation_mode_active(self, climate_controller, mock_area, mock_hass):
        """Test vacation mode when active."""
        # Mock vacation manager in hass.data
        mock_vacation_manager = MagicMock()
        mock_vacation_manager.is_active = MagicMock(return_value=True)
        mock_vacation_manager.get_preset_mode = MagicMock(return_value=PRESET_AWAY)
        mock_hass.data = {"smart_heating": {"vacation_manager": mock_vacation_manager}}

        climate_controller._apply_vacation_mode("living_room", mock_area)

        # Should set preset to vacation mode
        assert mock_area.preset_mode == PRESET_AWAY


class TestWindowSensorCheck:
    """Test window sensor checking."""

    def test_check_window_sensors_no_sensors(self, climate_controller, mock_area):
        """Test checking when area has no window sensors."""
        mock_area.window_sensors = []

        result = climate_controller._check_window_sensors("living_room", mock_area)

        assert result is False

    def test_check_window_sensors_all_closed(self, climate_controller, mock_area, mock_hass):
        """Test checking when all windows are closed."""
        mock_area.window_sensors = [
            {"entity_id": "binary_sensor.window1"},
            {"entity_id": "binary_sensor.window2"},
        ]

        mock_state = MagicMock()
        mock_state.state = STATE_OFF
        mock_hass.states.get = MagicMock(return_value=mock_state)

        result = climate_controller._check_window_sensors("living_room", mock_area)

        assert result is False

    def test_check_window_sensors_one_open(self, climate_controller, mock_area, mock_hass):
        """Test checking when one window is open."""
        mock_area.window_sensors = [
            {"entity_id": "binary_sensor.window1"},
            {"entity_id": "binary_sensor.window2"},
        ]

        def get_state(entity_id):
            mock_state = MagicMock()
            mock_state.state = STATE_ON if entity_id == "binary_sensor.window1" else STATE_OFF
            return mock_state

        mock_hass.states.get = MagicMock(side_effect=get_state)

        result = climate_controller._check_window_sensors("living_room", mock_area)

        assert result is True


class TestPresenceSensorCheck:
    """Test presence sensor checking."""

    def test_check_presence_sensors_no_sensors(self, climate_controller):
        """Test checking when area has no presence sensors."""
        result = climate_controller._check_presence_sensors("living_room", [])

        assert result is False

    def test_check_presence_sensors_none_detected(self, climate_controller, mock_hass):
        """Test checking when no presence is detected."""
        sensors = [
            {"entity_id": "binary_sensor.motion1"},
            {"entity_id": "binary_sensor.motion2"},
        ]

        mock_state = MagicMock()
        mock_state.state = STATE_OFF
        mock_hass.states.get = MagicMock(return_value=mock_state)

        result = climate_controller._check_presence_sensors("living_room", sensors)

        assert result is False

    def test_check_presence_sensors_detected(self, climate_controller, mock_hass):
        """Test checking when presence is detected."""
        sensors = [{"entity_id": "binary_sensor.motion1"}]

        mock_state = MagicMock()
        mock_state.state = STATE_ON
        mock_hass.states.get = MagicMock(return_value=mock_state)

        result = climate_controller._check_presence_sensors("living_room", sensors)

        assert result is True


class TestOutdoorTemperature:
    """Test outdoor temperature retrieval."""

    @pytest.mark.asyncio
    async def test_get_outdoor_temperature_no_entity(self, climate_controller, mock_area):
        """Test getting outdoor temperature when no weather entity configured."""
        mock_area.weather_entity_id = None

        temp = await climate_controller._async_get_outdoor_temperature(mock_area)

        assert temp is None

    @pytest.mark.asyncio
    async def test_get_outdoor_temperature_celsius(self, climate_controller, mock_area, mock_hass):
        """Test getting outdoor temperature in Celsius."""
        mock_area.weather_entity_id = "weather.home"

        mock_state = MagicMock()
        mock_state.state = "15.5"
        mock_state.attributes = {"unit_of_measurement": "°C"}
        mock_hass.states.get = MagicMock(return_value=mock_state)

        temp = await climate_controller._async_get_outdoor_temperature(mock_area)

        assert temp == pytest.approx(15.5)

    @pytest.mark.asyncio
    async def test_get_outdoor_temperature_fahrenheit(
        self, climate_controller, mock_area, mock_hass
    ):
        """Test getting outdoor temperature in Fahrenheit."""
        mock_area.weather_entity_id = "weather.home"

        mock_state = MagicMock()
        mock_state.state = "60.0"
        mock_state.attributes = {"unit_of_measurement": "°F"}
        mock_hass.states.get = MagicMock(return_value=mock_state)

        temp = await climate_controller._async_get_outdoor_temperature(mock_area)

        assert temp == pytest.approx(15.56, abs=0.01)

    @pytest.mark.asyncio
    async def test_get_outdoor_temperature_unavailable(
        self, climate_controller, mock_area, mock_hass
    ):
        """Test getting outdoor temperature when unavailable."""
        mock_area.weather_entity_id = "weather.home"

        mock_state = MagicMock()
        mock_state.state = "unavailable"
        mock_hass.states.get = MagicMock(return_value=mock_state)

        temp = await climate_controller._async_get_outdoor_temperature(mock_area)

        assert temp is None


class TestOpenThermControl:
    """Test OpenTherm gateway control."""

    @pytest.mark.asyncio
    async def test_control_opentherm_disabled(
        self, climate_controller, mock_area_manager, mock_hass
    ):
        """Test OpenTherm control when disabled."""
        mock_area_manager.opentherm_gateway_id = None

        await climate_controller._async_control_opentherm_gateway(True, 50.0)

        # Should not call any services
        mock_hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_control_opentherm_heating_required(
        self, climate_controller, mock_area_manager, mock_hass
    ):
        """Test OpenTherm control when heating is required."""
        mock_area_manager.opentherm_gateway_id = "gateway1"
        mock_area_manager.opentherm_gateway_id = "gateway1"

        # Add a radiator area that needs heating to trigger OpenTherm
        from smart_heating.models.area import Area

        radiator_area = Area("test_area", "Test Room")
        radiator_area.heating_type = "radiator"
        radiator_area.state = "heating"
        radiator_area.current_temperature = 18.0
        radiator_area.target_temperature = 45.0
        radiator_area.custom_overhead_temp = None  # Use default 20°C for radiator
        radiator_area.weather_entity_id = None  # No weather entity
        # Ensure area manager can find the area
        mock_area_manager.get_area.return_value = radiator_area

        mock_area_manager.get_all_areas.return_value = {
            "test_area": radiator_area,
        }
        # Add missing attributes
        mock_area_manager.advanced_control_enabled = False
        mock_area_manager.heating_curve_enabled = False
        mock_area_manager.pid_enabled = False
        mock_area_manager.pwm_enabled = False

        # Mock the gateway state to return None to avoid minimum setpoint calculation
        mock_hass.states.get.return_value = None

        await climate_controller._async_control_opentherm_gateway(True, 45.0)

        # Should set boiler temperature (max_target + 20)
        mock_hass.services.async_call.assert_called_once()
        call_args = mock_hass.services.async_call.call_args
        # async_call(domain, service, service_data, blocking)
        # args[0] = positional args tuple (domain, service, service_data, blocking)
        # args[1] = kwargs dict
        assert call_args.args[0] == "opentherm_gw"
        assert call_args.args[1] == "set_control_setpoint"
        assert call_args.args[2]["gateway_id"] == "gateway1"
        assert call_args.args[2]["temperature"] == pytest.approx(65.0)  # 45 + 20

    @pytest.mark.asyncio
    async def test_control_opentherm_no_heating_required(
        self, climate_controller, mock_area_manager, mock_hass
    ):
        """Test OpenTherm control when no heating is required."""
        mock_area_manager.opentherm_gateway_id = "gateway1"
        mock_area_manager.opentherm_gateway_id = "gateway1"

        await climate_controller._async_control_opentherm_gateway(False, 0.0)

        # Should turn off boiler
        mock_hass.services.async_call.assert_called_once()
        call_args = mock_hass.services.async_call.call_args
        # async_call(domain, service, service_data, blocking)
        assert call_args.args[0] == "opentherm_gw"
        assert call_args.args[1] == "set_control_setpoint"
        assert call_args.args[2]["gateway_id"] == "gateway1"
        assert call_args.args[2]["temperature"] == pytest.approx(0.0)


class TestValveCapabilities:
    """Test valve capability detection."""

    def test_get_valve_capability_number_entity(self, climate_controller, mock_hass):
        """Test getting capabilities for number.valve entity."""
        mock_state = MagicMock()
        mock_state.attributes = {"min": 0, "max": 100}
        mock_hass.states.get = MagicMock(return_value=mock_state)

        capabilities = climate_controller._get_valve_capability("number.valve1")

        assert capabilities["supports_position"] is True
        assert capabilities["position_min"] == 0
        assert capabilities["position_max"] == 100
        assert capabilities["entity_domain"] == "number"

    def test_get_valve_capability_climate_with_position(self, climate_controller, mock_hass):
        """Test getting capabilities for climate entity with position attribute."""
        mock_state = MagicMock()
        mock_state.attributes = {"position": 50, "temperature": 20.0}
        mock_hass.states.get = MagicMock(return_value=mock_state)

        capabilities = climate_controller._get_valve_capability("climate.trv1")

        assert capabilities["supports_position"] is True
        assert capabilities["supports_temperature"] is True

    def test_get_valve_capability_climate_temperature_only(self, climate_controller, mock_hass):
        """Test getting capabilities for climate entity without position."""
        mock_state = MagicMock()
        mock_state.attributes = {"temperature": 20.0}
        mock_hass.states.get = MagicMock(return_value=mock_state)

        capabilities = climate_controller._get_valve_capability("climate.trv2")

        assert capabilities["supports_position"] is False
        assert capabilities["supports_temperature"] is True

    def test_get_valve_capability_cached(self, climate_controller, mock_hass):
        """Test that valve capabilities are cached."""
        mock_state = MagicMock()
        mock_state.attributes = {"min": 0, "max": 100}
        mock_hass.states.get = MagicMock(return_value=mock_state)

        # First call
        cap1 = climate_controller._get_valve_capability("number.valve1")
        # Second call should use cache
        cap2 = climate_controller._get_valve_capability("number.valve1")

        # Should only query state once
        assert mock_hass.states.get.call_count == 1
        assert cap1 == cap2

    def test_get_valve_capability_entity_not_found(self, climate_controller, mock_hass):
        """Test getting capabilities when entity doesn't exist."""
        mock_hass.states.get = MagicMock(return_value=None)

        capabilities = climate_controller._get_valve_capability("number.missing")

        assert capabilities["supports_position"] is False
        assert capabilities["supports_temperature"] is False


class TestValveControl:
    """Test valve control methods."""

    @pytest.mark.asyncio
    async def test_control_valves_number_entity_heating(
        self, climate_controller, mock_hass, mock_area
    ):
        """Test controlling number.valve entity when heating."""
        mock_area.get_valves = MagicMock(return_value=["number.valve1"])

        mock_state = MagicMock()
        mock_state.attributes = {"min": 0, "max": 100}
        mock_hass.states.get = MagicMock(return_value=mock_state)

        await climate_controller._async_control_valves(mock_area, True, 21.0)

        # Should set valve to max position
        mock_hass.services.async_call.assert_called()
        call_args = mock_hass.services.async_call.call_args
        assert call_args.args[0] == "number"
        assert call_args.args[1] == "set_value"
        assert call_args.args[2]["value"] == 100

    @pytest.mark.asyncio
    async def test_control_valves_number_entity_idle(
        self, climate_controller, mock_hass, mock_area
    ):
        """Test controlling number.valve entity when idle."""
        mock_area.get_valves = MagicMock(return_value=["number.valve1"])

        mock_state = MagicMock()
        mock_state.attributes = {"min": 0, "max": 100}
        mock_hass.states.get = MagicMock(return_value=mock_state)

        await climate_controller._async_control_valves(mock_area, False, 21.0)

        # Should set valve to min position
        call_args = mock_hass.services.async_call.call_args
        assert call_args.args[2]["value"] == 0

    @pytest.mark.asyncio
    async def test_control_valves_trv_temperature_control(
        self, climate_controller, mock_hass, mock_area, mock_area_manager
    ):
        """Test controlling TRV with temperature-only control."""
        mock_area.get_valves = MagicMock(return_value=["climate.trv1"])
        mock_area_manager.trv_heating_temp = 25.0
        mock_area_manager.trv_temp_offset = 3.0
        mock_area_manager.trv_idle_temp = 10.0

        mock_state = MagicMock()
        mock_state.attributes = {"temperature": 20.0}  # No position attribute
        mock_hass.states.get = MagicMock(return_value=mock_state)

        await climate_controller._async_control_valves(mock_area, True, 22.0)

        # Should use temperature control
        call_args = mock_hass.services.async_call.call_args
        assert call_args.args[0] == "climate"
        assert call_args.args[1] == "set_temperature"
        # Should be max of (22 + 3) or 25 = 25
        assert call_args.args[2]["temperature"] == pytest.approx(25.0)


class TestThermostatControl:
    """Test thermostat control methods."""

    @pytest.mark.asyncio
    async def test_control_thermostats_heating_new_temperature(
        self, climate_controller, mock_hass, mock_area
    ):
        """Test controlling thermostats when heating with new temperature."""
        mock_area.get_thermostats = MagicMock(return_value=["climate.thermostat1"])

        await climate_controller._async_control_thermostats(mock_area, True, 21.0)

        # Expected service calls: ensure switch on, set_hvac_mode, set_temperature
        assert mock_hass.services.async_call.call_count == 3
        last_call = mock_hass.services.async_call.call_args_list[-1]
        assert last_call[0][1] == "set_temperature"
        assert last_call[0][2]["temperature"] == pytest.approx(21.0)

    @pytest.mark.asyncio
    async def test_control_thermostats_skip_duplicate_temperature(
        self, climate_controller, mock_hass, mock_area
    ):
        """Test that thermostat updates are skipped for duplicate temperatures."""
        mock_area.get_thermostats = MagicMock(return_value=["climate.thermostat1"])

        # Set temperature first time => 3 service calls
        await climate_controller._async_control_thermostats(mock_area, True, 21.0)
        assert mock_hass.services.async_call.call_count == 3

        # Try to set same temperature again
        await climate_controller._async_control_thermostats(mock_area, True, 21.0)

        # Should still be only 1 call (skipped second one)
        # Ensure one climate.set_temperature call was made (ignore other service invocations)
        set_temp_calls = [
            c
            for c in mock_hass.services.async_call.call_args_list
            if c.args[0] == "climate" and c.args[1] == "set_temperature"
        ]
        assert len(set_temp_calls) == 1

    @pytest.mark.asyncio
    async def test_control_thermostats_update_when_temperature_changes(
        self, climate_controller, mock_hass, mock_area
    ):
        """Test that thermostat updates when temperature changes significantly."""
        mock_area.get_thermostats = MagicMock(return_value=["climate.thermostat1"])

        # Set temperature first time
        await climate_controller._async_control_thermostats(mock_area, True, 21.0)
        set_temp_calls = [
            c
            for c in mock_hass.services.async_call.call_args_list
            if c.args[0] == "climate" and c.args[1] == "set_temperature"
        ]
        assert len(set_temp_calls) == 1

        # Change temperature by more than 0.1°C: expect 3 more calls
        await climate_controller._async_control_thermostats(mock_area, True, 21.5)
        assert mock_hass.services.async_call.call_count == 6

    @pytest.mark.asyncio
    async def test_control_thermostats_turn_off_unsupported(
        self, climate_controller, mock_hass, mock_area, mock_area_manager
    ):
        """Test turning off thermostat when turn_off service not supported."""
        mock_area.get_thermostats = MagicMock(return_value=["climate.thermostat1"])
        mock_area_manager.frost_protection_enabled = True
        mock_area_manager.frost_protection_temp = 5.0

        # Make turn_off service raise exception
        async def async_call_side_effect(domain, service, data, blocking):
            if service == "turn_off":
                raise Exception("Service not supported")

        mock_hass.services.async_call = AsyncMock(side_effect=async_call_side_effect)

        await climate_controller._async_control_thermostats(mock_area, False, None)

        # Should fall back to setting frost protection temperature
        assert mock_hass.services.async_call.call_count == 2  # turn_off + set_temperature


class TestSwitchControl:
    """Test switch control methods."""

    @pytest.mark.asyncio
    async def test_control_switches_heating_on(self, climate_controller, mock_hass, mock_area):
        """Test turning switches on when heating."""
        mock_area.get_switches = MagicMock(return_value=["switch.pump1"])

        # Mock thermostat not heating
        climate_controller._is_any_thermostat_actively_heating = MagicMock(return_value=False)

        await climate_controller._async_control_switches(mock_area, True)

        mock_hass.services.async_call.assert_called_once()
        call_args = mock_hass.services.async_call.call_args
        assert call_args.args[0] == "switch"
        assert call_args.args[1] == "turn_on"

    @pytest.mark.asyncio
    async def test_control_switches_keep_on_when_thermostat_heating(
        self, climate_controller, mock_hass, mock_area
    ):
        """Test keeping switches on when thermostat still heating."""
        mock_area.get_switches = MagicMock(return_value=["switch.pump1"])
        mock_area.shutdown_switches_when_idle = True

        # Mock thermostat still heating on the handler
        climate_controller.device_handler.is_any_thermostat_actively_heating = MagicMock(
            return_value=True
        )

        await climate_controller._async_control_switches(mock_area, False)

        # Should keep switch ON (not turn off)
        call_args = mock_hass.services.async_call.call_args
        assert call_args.args[1] == "turn_on"

    @pytest.mark.asyncio
    async def test_control_switches_shutdown_when_idle(
        self, climate_controller, mock_hass, mock_area
    ):
        """Test turning switches off when idle and shutdown enabled."""
        mock_area.get_switches = MagicMock(return_value=["switch.pump1"])
        mock_area.shutdown_switches_when_idle = True

        # Mock thermostat not heating
        climate_controller._is_any_thermostat_actively_heating = MagicMock(return_value=False)

        await climate_controller._async_control_switches(mock_area, False)

        call_args = mock_hass.services.async_call.call_args
        assert call_args.args[1] == "turn_off"

    @pytest.mark.asyncio
    async def test_control_switches_keep_on_when_shutdown_disabled(
        self, climate_controller, mock_hass, mock_area
    ):
        """Test keeping switches on when shutdown_switches_when_idle is False."""
        mock_area.get_switches = MagicMock(return_value=["switch.pump1"])
        mock_area.shutdown_switches_when_idle = False

        # Mock thermostat not heating
        climate_controller._is_any_thermostat_actively_heating = MagicMock(return_value=False)

        await climate_controller._async_control_switches(mock_area, False)

        # Should not call service (keep switch on)
        mock_hass.services.async_call.assert_not_called()


class TestIsAnyThermostatActivelyHeating:
    """Test checking if thermostats are actively heating."""

    def test_thermostat_heating(self, climate_controller, mock_hass, mock_area):
        """Test detecting when thermostat is actively heating."""
        mock_area.get_thermostats = MagicMock(return_value=["climate.thermostat1"])

        mock_state = MagicMock()
        mock_state.attributes = {"hvac_action": "heating"}
        mock_hass.states.get = MagicMock(return_value=mock_state)

        result = climate_controller._is_any_thermostat_actively_heating(mock_area)

        assert result is True

    def test_thermostat_idle(self, climate_controller, mock_hass, mock_area):
        """Test detecting when thermostat is idle."""
        mock_area.get_thermostats = MagicMock(return_value=["climate.thermostat1"])

        mock_state = MagicMock()
        mock_state.attributes = {"hvac_action": "idle"}
        mock_hass.states.get = MagicMock(return_value=mock_state)

        result = climate_controller._is_any_thermostat_actively_heating(mock_area)

        assert result is False

    def test_multiple_thermostats_one_heating(self, climate_controller, mock_hass, mock_area):
        """Test with multiple thermostats where one is heating."""
        mock_area.get_thermostats = MagicMock(
            return_value=["climate.thermostat1", "climate.thermostat2"]
        )

        def get_state(entity_id):
            if entity_id == "climate.thermostat1":
                state = MagicMock()
                state.attributes = {"hvac_action": "idle"}
                return state
            else:
                state = MagicMock()
                state.attributes = {"hvac_action": "heating"}
                return state

        mock_hass.states.get = MagicMock(side_effect=get_state)

        result = climate_controller._is_any_thermostat_actively_heating(mock_area)

        assert result is True


class TestTemperatureCollection:
    """Test temperature collection from sensors and thermostats."""

    def test_get_temperature_from_sensor_valid(self, climate_controller, mock_hass):
        """Test getting temperature from sensor with valid value."""
        mock_state = MagicMock()
        mock_state.state = "21.5"
        mock_hass.states.get = MagicMock(return_value=mock_state)

        result = climate_controller._get_temperature_from_sensor("sensor.temp1")

        assert result == pytest.approx(21.5)

    def test_get_temperature_from_sensor_invalid(self, climate_controller, mock_hass):
        """Test getting temperature from sensor with invalid value."""
        mock_state = MagicMock()
        mock_state.state = "unknown"
        mock_hass.states.get = MagicMock(return_value=mock_state)

        result = climate_controller._get_temperature_from_sensor("sensor.temp1")

        assert result is None

    def test_get_temperature_from_thermostat_valid(self, climate_controller, mock_hass):
        """Test getting temperature from thermostat."""
        mock_state = MagicMock()
        mock_state.attributes = {"current_temperature": 22.0}
        mock_hass.states.get = MagicMock(return_value=mock_state)

        result = climate_controller._get_temperature_from_thermostat("climate.thermo1")

        assert result == pytest.approx(22.0)

    def test_collect_area_temperatures(self, climate_controller, mock_hass, mock_area):
        """Test collecting temperatures from all sources in an area."""
        mock_area.get_temperature_sensors = MagicMock(return_value=["sensor.temp1"])
        mock_area.get_thermostats = MagicMock(return_value=["climate.thermo1"])

        def get_state(entity_id):
            if entity_id == "sensor.temp1":
                state = MagicMock()
                state.state = "21.0"
                return state
            elif entity_id == "climate.thermo1":
                state = MagicMock()
                state.attributes = {"current_temperature": 22.0}
                return state

        mock_hass.states.get = MagicMock(side_effect=get_state)

        result = climate_controller._collect_area_temperatures(mock_area)

        assert len(result) == 2
        assert 21.0 in result
        assert 22.0 in result


class TestFrostProtectionAdvanced:
    """Test advanced frost protection logic."""

    def test_apply_frost_protection_below_minimum(self, climate_controller, mock_area_manager):
        """Test frost protection raises target when below minimum."""
        mock_area_manager.frost_protection_enabled = True
        mock_area_manager.frost_protection_temp = 5.0

        result = climate_controller._apply_frost_protection("living_room", 3.0)

        assert result == pytest.approx(5.0)

    def test_apply_frost_protection_above_minimum(self, climate_controller, mock_area_manager):
        """Test frost protection leaves target unchanged when above minimum."""
        mock_area_manager.frost_protection_enabled = True
        mock_area_manager.frost_protection_temp = 5.0

        result = climate_controller._apply_frost_protection("living_room", 20.0)

        assert result == pytest.approx(20.0)

    def test_apply_frost_protection_disabled(self, climate_controller, mock_area_manager):
        """Test frost protection does nothing when disabled."""
        mock_area_manager.frost_protection_enabled = False

        result = climate_controller._apply_frost_protection("living_room", 3.0)

        assert result == pytest.approx(3.0)


class TestManualOverride:
    """Test manual override mode handling."""

    @pytest.mark.asyncio
    async def test_handle_manual_override(self, climate_controller, mock_area):
        """Test handling area in manual override mode."""
        mock_area.area_id = "living_room"
        mock_area.manual_override = True

        await climate_controller._async_handle_manual_override("living_room", mock_area)

        # Should set state to manual
        assert mock_area.state == "manual"


class TestHvacModeOff:
    """Test HVAC mode off handling."""

    @pytest.mark.asyncio
    async def test_hvac_mode_off_turns_off_thermostats(
        self, climate_controller, mock_area, mock_hass
    ):
        """Test that hvac_mode=off turns off all thermostats in area."""
        mock_area.area_id = "living_room"
        mock_area.hvac_mode = "off"
        mock_area.current_temperature = 22.0
        mock_area.target_temperature = 20.0
        mock_area.get_thermostats = MagicMock(
            return_value=["climate.thermostat1", "climate.thermostat2"]
        )
        mock_area.get_switches = MagicMock(return_value=[])
        mock_area.get_valves = MagicMock(return_value=[])

        # Mock device handler methods
        climate_controller.device_handler._handle_thermostat_turn_off = AsyncMock()
        climate_controller.device_handler.async_control_switches = AsyncMock()
        climate_controller.device_handler.async_control_valves = AsyncMock()

        # Process area with hvac_mode=off
        result = await climate_controller._process_area(
            "living_room", mock_area, MagicMock(), False, None
        )

        # Should turn off both thermostats
        assert climate_controller.device_handler._handle_thermostat_turn_off.call_count == 2
        climate_controller.device_handler._handle_thermostat_turn_off.assert_any_call(
            "climate.thermostat1"
        )
        climate_controller.device_handler._handle_thermostat_turn_off.assert_any_call(
            "climate.thermostat2"
        )

        # Should turn off switches and valves
        climate_controller.device_handler.async_control_switches.assert_called_once_with(
            mock_area, False
        )
        climate_controller.device_handler.async_control_valves.assert_called_once_with(
            mock_area, False, None
        )

        # Should set area state to off
        assert mock_area.state == "off"

        # Should return None to skip further processing
        assert result == (None, None)

    @pytest.mark.asyncio
    async def test_hvac_mode_off_works_without_temperature_data(
        self, climate_controller, mock_area, mock_hass
    ):
        """Test that hvac_mode=off works even when temperature data is unavailable."""
        mock_area.area_id = "living_room"
        mock_area.hvac_mode = "off"
        mock_area.current_temperature = None  # No temperature data
        mock_area.target_temperature = 20.0
        mock_area.get_thermostats = MagicMock(return_value=["climate.thermostat1"])
        mock_area.get_switches = MagicMock(return_value=[])
        mock_area.get_valves = MagicMock(return_value=[])

        # Mock device handler methods
        climate_controller.device_handler._handle_thermostat_turn_off = AsyncMock()
        climate_controller.device_handler.async_control_switches = AsyncMock()
        climate_controller.device_handler.async_control_valves = AsyncMock()

        # Process area with hvac_mode=off and no temperature
        result = await climate_controller._process_area(
            "living_room", mock_area, MagicMock(), False, None
        )

        # Should still turn off thermostat even without temperature data
        climate_controller.device_handler._handle_thermostat_turn_off.assert_called_once_with(
            "climate.thermostat1"
        )

        # Should set area state to off
        assert mock_area.state == "off"

        # Should return None to skip further processing
        assert result == (None, None)

    @pytest.mark.asyncio
    async def test_hvac_mode_heat_allows_normal_control(
        self, climate_controller, mock_area, mock_hass
    ):
        """Test that hvac_mode=heat allows normal temperature-based control."""
        mock_area.area_id = "living_room"
        mock_area.hvac_mode = "heat"
        mock_area.current_temperature = 18.0  # Below target
        mock_area.target_temperature = 20.0
        mock_area.boost_mode_active = False
        mock_area.preset_mode = "none"
        mock_area.hysteresis_override = None
        mock_area.weather_entity_id = None
        mock_area.get_thermostats = MagicMock(return_value=["climate.thermostat1"])
        mock_area.get_switches = MagicMock(return_value=[])
        mock_area.get_valves = MagicMock(return_value=[])
        mock_area.get_effective_target_temperature = MagicMock(return_value=20.0)

        # Mock device handler methods
        climate_controller.device_handler._handle_thermostat_turn_off = AsyncMock()
        climate_controller.cycle_handler.async_handle_heating_required = AsyncMock(
            return_value=(["living_room"], 20.0)
        )

        # Process area with hvac_mode=heat
        result = await climate_controller._process_area(
            "living_room", mock_area, MagicMock(), False, None
        )

        # Should NOT turn off thermostat (normal heating control should proceed)
        climate_controller.device_handler._handle_thermostat_turn_off.assert_not_called()

        # Result should indicate heating is required
        assert result == (["living_room"], 20.0)

        await climate_controller._async_handle_disabled_area("living_room", mock_area, None, False)

        # Should set state to off
        assert mock_area.state == "off"
