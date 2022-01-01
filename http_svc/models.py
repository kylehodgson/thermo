from pydantic import BaseModel

class TemperatureSetting(BaseModel):
    code: str
    temperature: float