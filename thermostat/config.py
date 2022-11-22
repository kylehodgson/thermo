
from enum import Enum


class SmartPlugType(Enum):
    KASA = 1

class ZoneSensor(Enum):
    GOVEE = 1

class ServiceType(Enum):
    OFF = 1
    ON = 2
    SCHEDULED = 3
