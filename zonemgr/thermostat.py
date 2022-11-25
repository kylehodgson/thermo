#!/usr/bin/env python
from dataclasses import dataclass
from enum import Enum
import time
import datetime
import kasa
from zonemgr.services.config_db_service import ConfigStore
from zonemgr.services.temp_reading_db_service import TempReadingStore
from zonemgr.services.moer_reading_db_service import MoerReadingStore
from zonemgr.db import ZoneManagerDB
from zonemgr.models import TemperatureReading, ServiceType


class EcoMode(Enum):
    ENABLED = 1
    DISABLED = 0


class PanelState(Enum):
    ON = 1
    OFF = 0


class PanelDecision(Enum):
    DO_NOTHING = 0
    TURN_ON = 1
    TURN_OFF = 2


@dataclass(frozen=True)
class DecisionContext:
    panel_state: PanelState
    service_type: ServiceType
    schedule_off: bool
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
    temp_store: TempReadingStore
    config_store: ConfigStore
    moer_store: MoerReadingStore

    def __init__(self, temp_store: TempReadingStore, config_store: ConfigStore, moer_store: MoerReadingStore) -> None:
        # if ble advertisements with temperature readings are appearing faster than this rate,
        # ignore them until this many seconds have passed so that the script isnt running constantly
        self.CHECK_INTERVAL = int(5)
        # the amount, in celcius, that the temperature may differ from the specified
        # temperature before starting/stopping the heater
        self.ACCEPTABLE_DRIFT = float(1)
        # integer of the hour to stop the system when its set to "schedule"
        self.SCHEDULE_STOP = 10
        # integer of the hour to start the system when its set to "schedule"
        self.SCHEDULE_START = 21
        # integer - the number of seconds that should pass before we write another record to the db
        # for a given sensor
        self.TEMPERATURE_RECORD_STEP = 60 * 10
        self.ECO_REDUCTION = float(.75)
        self.MAXMOER = 50
        # set the "last reading time" in the past so that the system will start immediately
        self.last_reading_time = int(time.time()) - (self.CHECK_INTERVAL * 2)

        self.temp_store = temp_store
        self.config_store = config_store
        self.moer_store = moer_store

    def too_soon(self) -> bool:
        this_reading_time = int(time.time())
        elapsed = this_reading_time - self.last_reading_time
        self.last_reading_time = this_reading_time
        return elapsed < self.CHECK_INTERVAL

    def get_schedule_off(self):
        now = datetime.datetime.now()
        if now.hour > self.SCHEDULE_STOP and now.hour < self.SCHEDULE_START:
            return True
        return False

    async def handle_reading(self, reading: TemperatureReading):
        print(
            f"[{self.log_time()}] sensor_id: {reading.sensor_id} "
            f"temp: {reading.temp} humidity: {reading.humidity} battery: {reading.battery}")

        (_, config) = self.config_store.get_config_for(reading.sensor_id)
        if not config:
            return

        self.temp_store.save_if_newer(reading, self.TEMPERATURE_RECORD_STEP)
        try:
            plug = kasa.SmartPlug(config.plug)
            await plug.update()
        except Exception as err:
            print(
                f"[{self.log_time()}] trouble connecting to plug {config.plug} "
                f"in location {config.location} : {err} {type(err)}")
            return

        decision = self.get_decision_from(
            DecisionContext(
                panel_state=self.get_panel_state_from(plug),
                service_type=DecisionContext.get_service_type(
                    config.service_type),
                schedule_off=self.get_schedule_off(),
                reading_temp=reading.temp,
                config_temp=config.temp,
                allowable_drift=self.ACCEPTABLE_DRIFT,
                eco_mode=self.get_eco_mode(),
                eco_reduction=self.ECO_REDUCTION))

        if decision == PanelDecision.DO_NOTHING:
            return
        if decision == PanelDecision.TURN_OFF:
            await plug.turn_off()
            return
        if decision == PanelDecision.TURN_ON:
            await plug.turn_on()
            return

    def get_eco_mode(self) -> EcoMode:
        moer = self.get_moer()
        if moer > self.MAXMOER:
            return EcoMode.ENABLED
        return EcoMode.DISABLED

    def get_panel_state_from(plugSvc) -> PanelState:
        if plugSvc.is_off:
            return PanelState.OFF
        if plugSvc.is_on:
            return PanelState.ON

    def get_decision_from(self, ctx: DecisionContext) -> PanelDecision:
        # if servicetype is off, we don't need to check the thermostat,
        # just make sure it's off
        if ctx.service_type == ServiceType.OFF:
            if ctx.panel_state.OFF:
                return PanelDecision.DO_NOTHING
            if ctx.panel_state.ON:
                return PanelDecision.TURN_OFF

        # if servicetype is scheduled, make sure we're not on while scheduled off
        if ctx.service_type == ServiceType.SCHEDULED and ctx.schedule_off:
            if ctx.panel_state == PanelState.OFF:
                return PanelDecision.DO_NOTHING
            if ctx.panel_state == PanelState.ON:
                return PanelDecision.TURN_OFF

        # figure out if eco mode is enabled, and add an eco factor if so
        if ctx.eco_mode == EcoMode.ENABLED:
            ecoFactor = ctx.eco_reduction
        else:
            ecoFactor = float(0)

        heat_is_off = ctx.panel_state == PanelState.OFF
        heat_is_on = ctx.panel_state == PanelState.ON
        too_cold = (
            ctx.reading_temp < ctx.config_temp - ecoFactor - ctx.allowable_drift)
        too_warm = (
            ctx.reading_temp > ctx.config_temp - ecoFactor + ctx.allowable_drift)

        if too_cold and heat_is_off:
            print(
                f"[{self.log_time()}] temp {ctx.reading_temp} in room set to "
                f" {ctx.config_temp} is unacceptably cool given ecoFactor "
                f" {ecoFactor} and allowable drift {ctx.allowable_drift}, turning on panel")
            return PanelDecision.TURN_ON

        elif too_warm and heat_is_on:
            print(
                f"[{self.log_time()}] temp {ctx.reading_temp} in room set to "
                f" {ctx.config_temp} is unacceptably warm given ecoFactor "
                f" {ecoFactor} and allowable drift {ctx.allowable_drift}, turning off panel")
            return PanelDecision.TURN_OFF

        else:
            return PanelDecision.DO_NOTHING

    def get_moer(self) -> int:
        moer = self.moerStore.select_latest_moer_reading(
            self.moerStore.get_local_ba_id())
        return int(moer.percent)

    def log_time(self) -> str:
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
