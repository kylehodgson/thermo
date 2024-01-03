from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from enum import Enum

class ServiceType(Enum):
    SCHEDULED=1
    ON=2
    OFF=3
    PRESENCE=4

class SensorConfiguration(BaseModel):
    sensor_id: str
    temp: float
    service_type: str
    schedule_start_hour: Optional[int] = None
    schedule_stop_hour: Optional[int] = None
    name: Optional[str] = None
    location: Optional[str] = None
    plug: Optional[str] = None

class TemperatureReading(BaseModel):
    sensor_id: str
    temp: float
    battery: int
    humidity: float

class PlugConfiguration(BaseModel):
    name: str
    ip: str
    sensor: Optional[str]
    #config_data: Optional[dict]

class MoerReading(BaseModel):
    percent: int
    ba_id: str
    srcdate: datetime

def MoerReadingFrom(watt_time_response_json: str)->MoerReading:
    return MoerReading(
        ba_id=watt_time_response_json['ba'], 
        percent=watt_time_response_json['percent'],
        srcdate=watt_time_response_json['point_time'])
