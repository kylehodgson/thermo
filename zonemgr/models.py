from pydantic import BaseModel
from typing import Optional
from enum import Enum

class ServiceTypes(Enum):
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