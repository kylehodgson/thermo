#!/usr/bin/env python
from dataclasses import dataclass
import time
import datetime
from zonemgr.panel_plug import PanelPlug, PanelDecision, PanelPlugFactory, PanelState, EcoMode
from zonemgr.services.config_db_service import ConfigStore
from zonemgr.services.temp_reading_db_service import TempReadingStore
from zonemgr.services.moer_reading_db_service import MoerReadingStore
from zonemgr.models import TemperatureReading, ServiceType
from plugins.ui import Display


import logging
log = logging.getLogger(__name__)

@dataclass(frozen=True)
class DecisionContext:
    panel_state: PanelState
    service_type: ServiceType
    schedule_off: bool
    presence_off: bool
    reading_temp: float
    config_temp: float
    allowable_drift: float
    eco_mode: EcoMode
    eco_reduction: float

    @staticmethod
    def get_service_type(value: str) -> ServiceType:
        if str(ServiceType.SCHEDULED.name).lower() == value.lower():
            return ServiceType.SCHEDULED
        if str(ServiceType.OFF.name).lower() == value.lower():
            return ServiceType.OFF
        if str(ServiceType.ON.name).lower() == value.lower():
            return ServiceType.ON
        if str(ServiceType.PRESENCE.name).lower() == value.lower():
            return ServiceType.PRESENCE
        raise Exception(f"Value {value} is not a valid ServiceType.")


class Thermostat:

    CHECK_INTERVAL: int
    ACCEPTABLE_DRIFT: float
    SCHEDULE_STOP: int
    SCHEDULE_START: int
    TEMPERATURE_RECORD_STEP: int
    ECO_REDUCTION: float
    MAXMOER: int

    last_reading_time: int
    last_reading_times: dict
    temp_store: TempReadingStore
    config_store: ConfigStore
    moer_store: MoerReadingStore
    plug_factory: PanelPlugFactory
    plug_service: PanelPlug
    #display: Display

    def __init__(self,
                 temp_store: TempReadingStore,
                 config_store: ConfigStore,
                 moer_store: MoerReadingStore,
                 plug_factory: PanelPlugFactory) -> None:
    #             display: Display) -> None:
        # if ble advertisements with temperature readings are appearing faster than this rate,
        # ignore them until this many seconds have passed so that the script isnt running constantly
        self.CHECK_INTERVAL = int(5)
        # the amount, in celcius, that the temperature may differ from the specified
        # temperature before starting/stopping the heater
        self.ACCEPTABLE_DRIFT = float(1)
        # integer of the hour to stop the system when its set to "schedule"
        self.SCHEDULE_STOP = 10
        # integer of the hour to start the system when its set to "schedule"
        self.SCHEDULE_START = 20
        # integer - the number of seconds that should pass before we write another record to the db
        # for a given sensor
        self.TEMPERATURE_RECORD_STEP = 60 * 10
        # if the MOER is over the maximum, allow temps to fall this much cooler than normal before turning on the heat
        self.ECO_REDUCTION = float(.75)
        # 50 means "the grid is cleaner than it is 50% of the time over the last 30 days"
        self.MAXMOER = 50
        
        self.last_reading_times={}

        self.temp_store = temp_store
        self.config_store = config_store
        self.moer_store = moer_store
        self.plug_factory = plug_factory
        #self.display = display
    
    def too_soon_for(self, timer: str, check_interval:int) -> bool:
        this_reading_time = int(time.time())
        if timer in self.last_reading_times:
            elapsed = this_reading_time - self.last_reading_times[timer]
        else:
            elapsed=0
        self.last_reading_times[timer] = this_reading_time
        return elapsed < check_interval

    def get_presence_off(self):
        return True

    def get_schedule_off(self):
        now = datetime.datetime.now()
        return self.SCHEDULE_STOP <= now.hour < self.SCHEDULE_START

    async def handle_reading(self, reading: TemperatureReading):
        if self.too_soon_for(reading.sensor_id,5):
            return
        
        log.info(
            f"sensor_id: {reading.sensor_id} temp: {reading.temp} humidity: {reading.humidity} battery: {reading.battery}")

        (_, config) = self.config_store.get_config_for(reading.sensor_id)
        if not config:
            return

        #if config.location=="Main bedroom" and not self.too_soon_for("Main bedroom display",30):
        #    self.display.set_current_temp(reading.temp)
        #    self.display.set_zone_target_temp(config.temp)
        #    self.display.update()
        
        self.temp_store.save_if_newer(reading, self.TEMPERATURE_RECORD_STEP)

        self.plug_service = self.plug_factory.get_plug(config)
        self.plug_service.set_host(config.plug, config.name)

        decision = self.get_decision_from(
            DecisionContext(
                panel_state=await self.plug_service.get_state(),
                service_type=DecisionContext.get_service_type(
                    config.service_type),
                schedule_off=self.get_schedule_off(),
                presence_off=self.get_presence_off(),
                reading_temp=reading.temp,
                config_temp=config.temp,
                allowable_drift=self.ACCEPTABLE_DRIFT,
                eco_mode=self.get_eco_mode(),
                eco_reduction=self.ECO_REDUCTION))

        await self.plug_service.set_state(decision)

        # if decision is PanelDecision.DO_NOTHING:
        #     return
        # if decision is PanelDecision.TURN_OFF:
        #     await plug.turn_off()
        #     return
        # if decision is PanelDecision.TURN_ON:
        #     await plug.turn_on()
        #     return

    def get_eco_mode(self) -> EcoMode:
        moer = self.moer_store.select_latest_moer_reading(
            self.moer_store.get_local_ba_id()).percent

        return EcoMode.ENABLED if moer > self.MAXMOER else EcoMode.DISABLED

    def get_decision_from(self, ctx: DecisionContext) -> PanelDecision:
        heat_is_off = ctx.panel_state is PanelState.OFF
        heat_is_on = ctx.panel_state is PanelState.ON
        heat_is_disabled = (
            (ctx.service_type is ServiceType.OFF) or
            (ctx.service_type is ServiceType.SCHEDULED and ctx.schedule_off) or
            (ctx.service_type is ServiceType.PRESENCE and ctx.presence_off) )

        if ctx.eco_mode is EcoMode.ENABLED:
            ecoFactor = ctx.eco_reduction
        else:
            ecoFactor = float(0)
        too_cold = (
            ctx.reading_temp < ctx.config_temp - ecoFactor - ctx.allowable_drift)
        too_warm = (
            ctx.reading_temp > ctx.config_temp - ecoFactor + ctx.allowable_drift)

        if heat_is_disabled and heat_is_off:
            return PanelDecision.DO_NOTHING

        if heat_is_disabled and heat_is_on:
            return PanelDecision.TURN_OFF

        if too_cold and heat_is_off:
            log.info(
                f"temp {ctx.reading_temp} in room set to {ctx.config_temp} is unacceptably cool given ecoFactor  {ecoFactor} and allowable drift {ctx.allowable_drift}, turning on panel")
            return PanelDecision.TURN_ON

        elif too_warm and heat_is_on:
            log.info(
                f"temp {ctx.reading_temp} in room set to {ctx.config_temp} is unacceptably warm given ecoFactor  {ecoFactor} and allowable drift {ctx.allowable_drift}, turning off panel")
            return PanelDecision.TURN_OFF

        else:
            return PanelDecision.DO_NOTHING

