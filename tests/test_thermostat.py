
import pytest
from datetime import datetime, timedelta
from ..zonemgr.thermostat import Thermostat, DecisionContext, EcoMode, PanelState, PanelDecision
from zonemgr.models import ServiceType, SensorConfiguration, TemperatureReading


def test_knows_if_the_schedule_is_on_or_off():
    # this test wont handle midnight very well! get_schedule_off has a hard coded datetime.now in it.
    an_hour_ago = (datetime.now() + timedelta(hours=-1)).hour
    an_hour_from_now = (datetime.now() + timedelta(hours=+1)).hour
    t = Thermostat(None, None, None)
    t.SCHEDULE_START = an_hour_ago
    t.SCHEDULE_STOP = an_hour_from_now
    assert t.get_schedule_off() == False
    t.SCHEDULE_STOP = an_hour_ago
    t.SCHEDULE_START = an_hour_from_now
    assert t.get_schedule_off() == True


def test_turns_on_when_its_too_cold():
    t = Thermostat(None, None, None)
    too_cold = float(17)

    ctx = DecisionContext(
        panel_state=PanelState.OFF,
        service_type=ServiceType.ON,
        schedule_off=False,
        reading_temp=too_cold,
        config_temp=float(22),
        allowable_drift=float(2),
        eco_mode=EcoMode.DISABLED,
        eco_reduction=float(1))

    assert t.get_decision_from(ctx) == PanelDecision.TURN_ON


def test_does_nothing_when_its_warm_enough():
    t = Thermostat(None, None, None)

    desired_temp = float(22)
    allowable_drift = float(1)
    just_warm_enough = desired_temp - allowable_drift
    almost_too_warm = desired_temp + allowable_drift

    ctx = DecisionContext(
        panel_state=PanelState.OFF,
        service_type=ServiceType.ON,
        schedule_off=False,
        reading_temp=just_warm_enough,
        config_temp=desired_temp,
        allowable_drift=allowable_drift,
        eco_mode=EcoMode.DISABLED,
        eco_reduction=float(1))

    assert t.get_decision_from(ctx) == PanelDecision.DO_NOTHING

    ctx = DecisionContext(
        panel_state=PanelState.OFF,
        service_type=ServiceType.ON,
        schedule_off=False,
        reading_temp=almost_too_warm,
        config_temp=desired_temp,
        allowable_drift=allowable_drift,
        eco_mode=EcoMode.DISABLED,
        eco_reduction=float(1))

    assert t.get_decision_from(ctx) == PanelDecision.DO_NOTHING

    ctx = DecisionContext(
        # previous tests cover panel state off, so now check on...
        panel_state=PanelState.ON,
        service_type=ServiceType.ON,
        schedule_off=False,
        reading_temp=almost_too_warm,
        config_temp=desired_temp,
        allowable_drift=allowable_drift,
        eco_mode=EcoMode.DISABLED,
        eco_reduction=float(1))

    assert t.get_decision_from(ctx) == PanelDecision.DO_NOTHING


def test_turns_off_when_its_too_warm():
    t = Thermostat(None, None, None)
    desired_temp = float(22)
    allowable_drift = float(1)
    too_warm = desired_temp + (allowable_drift * float(2))

    ctx = DecisionContext(
        panel_state=PanelState.ON,
        service_type=ServiceType.ON,
        schedule_off=False,
        reading_temp=too_warm,
        config_temp=desired_temp,
        allowable_drift=allowable_drift,
        eco_mode=EcoMode.DISABLED,
        eco_reduction=float(1))

    assert t.get_decision_from(ctx) == PanelDecision.TURN_OFF


@pytest.mark.asyncio
async def test_handles_readings():
    mock_reading = TemperatureReading(
        sensor_id=1, 
        temp=float(18), 
        battery=50, 
        humidity=50)
    mock_config = SensorConfiguration(
        sensor_id=1, 
        temp=float(22), 
        service_type="scheduled", 
        name="name", 
        location="location", 
        plug="192.168.2.1")

    class mockConfigs:
        def get_config_for(a):
            return (None, mock_config)

    class mockTemps:
        def save_if_newer(a, b):
            pass
    
    t = Thermostat(
        temp_store=mockTemps,
        config_store=mockConfigs, 
        moer_store=None)
    await t.handle_reading(mock_reading)
    assert True == True
