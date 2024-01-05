
import pytest
from datetime import datetime, timedelta
from zonemgr.panel_plug import EcoMode, PanelDecision, PanelState, PanelPlugFactory
from zonemgr.thermostat import Thermostat, DecisionContext
from zonemgr.models import ServiceType, SensorConfiguration, TemperatureReading
from zonemgr.services.moer_reading_db_service import MoerReading

def test_Thermostat_knows_if_the_schedule_is_on_or_off():
    # this test wont handle midnight very well! get_schedule_off has a hard coded datetime.now in it.
    an_hour_ago = (datetime.now() + timedelta(hours=-1)).hour
    an_hour_from_now = (datetime.now() + timedelta(hours=+1)).hour
    t = Thermostat(None, None, None, None, None)
    t.SCHEDULE_START = an_hour_ago
    t.SCHEDULE_STOP = an_hour_from_now
    assert t.get_schedule_off() == False
    t.SCHEDULE_STOP = an_hour_ago
    t.SCHEDULE_START = an_hour_from_now
    assert t.get_schedule_off() == True


def test_Thermostat_turns_on_when_its_too_cold():
    t = Thermostat(None, None, None, None, None)
    too_cold = float(17)

    ctx = DecisionContext(
        panel_state=PanelState.OFF,
        service_type=ServiceType.ON,
        schedule_off=False,
        presence_off=False,
        reading_temp=too_cold,
        config_temp=float(22),
        allowable_drift=float(2),
        eco_mode=EcoMode.DISABLED,
        eco_reduction=float(1))

    assert t.get_decision_from(ctx) == PanelDecision.TURN_ON


def test_Thermostat_does_nothing_when_its_warm_enough():
    t = Thermostat(None, None, None, None, None)

    desired_temp = float(22)
    allowable_drift = float(1)
    just_warm_enough = desired_temp - allowable_drift
    almost_too_warm = desired_temp + allowable_drift

    ctx = DecisionContext(
        panel_state=PanelState.OFF,
        service_type=ServiceType.ON,
        schedule_off=False,
        presence_off=False,
        reading_temp=just_warm_enough, # try the low end of "acceptable"
        config_temp=desired_temp,
        allowable_drift=allowable_drift,
        eco_mode=EcoMode.DISABLED,
        eco_reduction=float(1))

    assert t.get_decision_from(ctx) == PanelDecision.DO_NOTHING

    ctx = DecisionContext(
        panel_state=PanelState.OFF,
        service_type=ServiceType.ON,
        schedule_off=False,
        presence_off=False,
        reading_temp=almost_too_warm, # try the high end of "acceptable"
        config_temp=desired_temp,
        allowable_drift=allowable_drift,
        eco_mode=EcoMode.DISABLED,
        eco_reduction=float(1))

    assert t.get_decision_from(ctx) == PanelDecision.DO_NOTHING

    ctx = DecisionContext(
        panel_state=PanelState.ON, # previous tests cover panel state off, so now check on...
        service_type=ServiceType.ON,
        schedule_off=False,
        presence_off=False,
        reading_temp=almost_too_warm,
        config_temp=desired_temp,
        allowable_drift=allowable_drift,
        eco_mode=EcoMode.DISABLED,
        eco_reduction=float(1))

    assert t.get_decision_from(ctx) == PanelDecision.DO_NOTHING


def test_Thermostat_turns_off_when_its_too_warm():
    t = Thermostat(None, None, None, None, None)
    desired_temp = float(22)
    allowable_drift = float(1)
    too_warm = desired_temp + (allowable_drift * float(2))

    ctx = DecisionContext(
        panel_state=PanelState.ON,
        service_type=ServiceType.ON,
        schedule_off=False,
        presence_off=False,
        reading_temp=too_warm,
        config_temp=desired_temp,
        allowable_drift=allowable_drift,
        eco_mode=EcoMode.DISABLED,
        eco_reduction=float(1))

    assert t.get_decision_from(ctx) == PanelDecision.TURN_OFF


def test_Thermostat_eco_mode_reduces_temps_correctly():
    t = Thermostat(None, None, None, None, None)
    desired_temp = float(22)
    allowable_drift = float(2)
    eco_factor = float(1)
    warm_enough_considering_eco_mode = desired_temp - allowable_drift - eco_factor
    too_cold_even_for_eco_mode = desired_temp - \
        allowable_drift - eco_factor - float(.1)
    too_warm_considering_eco_mode = desired_temp + \
        allowable_drift - eco_factor + float(.1)

    ctx = DecisionContext(
        panel_state=PanelState.OFF,
        service_type=ServiceType.ON,
        schedule_off=False,
        presence_off=False,
        reading_temp=warm_enough_considering_eco_mode,
        config_temp=desired_temp,
        allowable_drift=allowable_drift,
        eco_mode=EcoMode.ENABLED,
        eco_reduction=eco_factor)

    assert t.get_decision_from(ctx) == PanelDecision.DO_NOTHING

    ctx = DecisionContext(
        panel_state=PanelState.ON,
        service_type=ServiceType.ON,
        schedule_off=False,
        presence_off=False,
        reading_temp=too_warm_considering_eco_mode,
        config_temp=desired_temp,
        allowable_drift=allowable_drift,
        eco_mode=EcoMode.ENABLED,
        eco_reduction=eco_factor)

    assert t.get_decision_from(ctx) == PanelDecision.TURN_OFF

    ctx = DecisionContext(
        panel_state=PanelState.OFF,
        service_type=ServiceType.ON,
        schedule_off=False,
        presence_off=False,
        reading_temp=too_cold_even_for_eco_mode,
        config_temp=desired_temp,
        allowable_drift=allowable_drift,
        eco_mode=EcoMode.ENABLED,
        eco_reduction=eco_factor)

    assert t.get_decision_from(ctx) == PanelDecision.TURN_ON


@pytest.mark.asyncio
async def test_Thermostat_handles_readings():
    mock_reading = TemperatureReading(
        sensor_id = "1",
        temp = float(18),
        battery = 50,
        humidity = 50)
    mock_config = SensorConfiguration(
        sensor_id = "1",
        temp = float(22),
        service_type = "scheduled",
        schedule_start_hour = int(20),
        schedule_stop_hour = int(10),
        name = "name",
        location = "location",
        plug = "192.168.2.49")

    class mockConfigs:
        def get_config_for(a):
            return (None, mock_config)

    class mockTemps:
        def save_if_newer(a, b):
            pass

    class mockMoer:
        def select_latest_moer_reading(a):
            return MoerReading(percent=40, ba_id="ba", srcdate=datetime.now())
        def get_local_ba_id():
            pass


    plug_factory=PanelPlugFactory()
    plug=plug_factory.get_plug(mock_config)

    t = Thermostat(
        temp_store=mockTemps,
        config_store=mockConfigs,
        moer_store=mockMoer,
        plug_factory=plug_factory,
        presence_store=None)
    await t.handle_reading(mock_reading)
    assert True == True
