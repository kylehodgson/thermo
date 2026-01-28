#!/usr/bin/env python
from dataclasses import dataclass
import time
import datetime
from zonemgr.panel_plug import PanelPlug, PanelDecision, PanelPlugFactory, PanelState, EcoMode
from zonemgr.services.config_db_service import ConfigStore
from zonemgr.services.temp_reading_db_service import TempReadingStore
from zonemgr.services.moer_reading_db_service import MoerReadingStore
from zonemgr.services.presence_db_service import ZonePresenceStore
from zonemgr.models import TemperatureReading, ServiceType, SensorConfiguration

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
        raise ValueError(f"Value {value} is not a valid ServiceType.")


class Thermostat:
    # if ble advertisements with temperature readings are appearing faster than this rate,
    # ignore them until this many seconds have passed so that the script isnt running constantly
    CHECK_INTERVAL: int
    # the amount, in celcius, that the temperature may differ from the specified
    # temperature before starting/stopping the heater
    ACCEPTABLE_DRIFT: float
    # integer - the number of seconds that should pass before we write another record to the db
    # for a given sensor
    TEMPERATURE_RECORD_STEP: int
    # if the MOER is over the maximum, allow temps to fall this much cooler than normal before turning on the heat
    ECO_REDUCTION: float
    # 50 means "the grid is cleaner than it is 50% of the time over the last 30 days"
    MAXMOER: int

    last_reading_time: int
    last_reading_times: dict
    temp_store: TempReadingStore
    config_store: ConfigStore
    moer_store: MoerReadingStore
    plug_factory: PanelPlugFactory
    plug_service: PanelPlug
    presence_store: ZonePresenceStore

    def __init__(self,
                 temp_store: TempReadingStore,
                 config_store: ConfigStore,
                 moer_store: MoerReadingStore,
                 plug_factory: PanelPlugFactory,
                 presence_store: ZonePresenceStore) -> None:
        self.CHECK_INTERVAL = int(5)
        self.ACCEPTABLE_DRIFT = float(1)
        self.TEMPERATURE_RECORD_STEP = 60 * 10
        self.ECO_REDUCTION = float(.75)
        self.MAXMOER = 50
        self.last_reading_times={}
        self.temp_store = temp_store
        self.config_store = config_store
        self.moer_store = moer_store
        self.plug_factory = plug_factory
        self.presence_store = presence_store
    
    def too_soon_for(self, sensor: str, check_interval: int) -> bool:
        this_reading_time = int(time.time())
        elapsed = this_reading_time - self.last_reading_times[sensor] if sensor in self.last_reading_times else 0
        self.last_reading_times[sensor] = this_reading_time
        return elapsed < check_interval

    def get_presence_off(self, reading: TemperatureReading) -> bool:
        presence = self.presence_store.get_latest_zone_presence_for(reading.sensor_id)
        log.info(f"checking presence sensor for {reading.sensor_id}, found presence {presence}")
        if presence is None:
            return False
        return presence.occupancy == "unoccupied"

    def get_schedule_off(self, config: SensorConfiguration) -> bool:
        now = datetime.datetime.now()
        start = int(config.schedule_start_hour) if config.schedule_start_hour else 0
        stop = int(config.schedule_stop_hour) if config.schedule_stop_hour else 0

        stop = stop+24 if start > stop else stop
        log.info(f"call to get_schedule_off with config {config} start is {start} stop is {stop} now.hour is {now.hour} will return {not(start <= now.hour < stop)}") 
        return not(start <= now.hour < stop)

    async def handle_reading(self, reading: TemperatureReading):
        if self.too_soon_for(reading.sensor_id,5):
            return
        
        log.info(
            f"sensor_id: {reading.sensor_id} temp: {reading.temp} humidity: {reading.humidity} battery: {reading.battery}")

        (_, config) = self.config_store.get_config_for(reading.sensor_id)
        if not config:
            return

        self.temp_store.save_if_newer(reading, self.TEMPERATURE_RECORD_STEP)
        self.plug_service = self.plug_factory.get_plug(config)
        self.plug_service.set_host(config.plug, config.name)

        context = DecisionContext(
                panel_state=await self.plug_service.get_state(),
                service_type=DecisionContext.get_service_type(
                    config.service_type),
                schedule_off=self.get_schedule_off(config),
                presence_off=self.get_presence_off(reading),
                reading_temp=reading.temp,
                config_temp=config.temp,
                allowable_drift=self.ACCEPTABLE_DRIFT,
                eco_mode=self.get_eco_mode(),
                eco_reduction=self.ECO_REDUCTION)
        log.info(f"context {context}")
        decision = self.get_decision_from(context)
        log.info(f"decision {decision}")
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

