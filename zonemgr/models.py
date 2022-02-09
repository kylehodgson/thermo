from pydantic import BaseModel

class TemperatureSetting(BaseModel):
    code: str
    temperature: float
    servicetype: str

class SensorConfiguration(BaseModel):
    sensor_id: str
    temp: float
    service: str
    name: str
    location: str
    plug: str

class TemperatureReading(BaseModel):
    sensor_id: str
    temp: float
    battery: int
    humidity: float
