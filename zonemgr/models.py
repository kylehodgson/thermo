from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from enum import Enum

class ServiceType(Enum):
    Scheduled="Scheduled"
    On="On"
    Off="Off"

class SensorConfiguration(BaseModel):
    sensor_id: str
    temp: float
    service_type: str
    name: Optional[str]
    location: Optional[str]
    plug: Optional[str]

class TemperatureReading(BaseModel):
    sensor_id: str
    temp: float
    battery: int
    humidity: float

class PlugConfiguration(BaseModel):
    name: str
    ip: str
    sensor: Optional[str]

class MoerReading(BaseModel):
    percent: int
    ba_id: str
    srcdate: datetime

def MoerReadingFrom(watt_time_response_json: str)->MoerReading:
    return MoerReading(
        ba_id=watt_time_response_json['ba'], 
        percent=watt_time_response_json['percent'],
        srcdate=watt_time_response_json['point_time'])