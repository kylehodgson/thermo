from pickle import TRUE
import unittest
from enum import Enum

class Decision(Enum):
    TURN_ON_HEAT = 1
    TURN_OFF_HEAT = 2
    DO_NOTHING = 3


class TemperatureReading:
    temperature = float(0.0)
    humidity = float(0.0)
    room = str("")

    def __init__(self,temperature) -> None:
        self.temperature = temperature

class Thermostat:
    desiredTemp = float(20.0)
    allowableRange = float(1.0)

    def handle(self, reading: TemperatureReading):
        if self.withinRange(reading): 
            return Decision.DO_NOTHING
        
        return Decision.TURN_ON_HEAT if reading.temperature < self.desiredTemp else Decision.TURN_OFF_HEAT
    
    def withinRange(self,reading: TemperatureReading):
        if reading.temperature > self.desiredTemp + self.allowableRange: 
            return False
        if reading.temperature < self.desiredTemp - self.allowableRange:
            return False
        return True

class TestThermoStat(unittest.TestCase):

    unit = Thermostat()

    def test_turnsOnHeaterWhenTooCold(self):
        reading = TemperatureReading(float(18.0))
        decision = self.unit.handle(reading)
        self.assertEqual(decision,Decision.TURN_ON_HEAT)

    def test_turnsOffHeaterWhenTooWarm(self):
        reading = TemperatureReading(float(22.0))
        decision = self.unit.handle(reading)
        self.assertEqual(decision,Decision.TURN_OFF_HEAT)

    def test_DoNothingWhenTemperatureIsInRange(self):
        self.unit.allowableRange=float(1.0)
        reading = TemperatureReading(float(20.1))
        decision = self.unit.handle(reading)
        self.assertEqual(decision,Decision.DO_NOTHING)
    
if __name__ == '__main__':
    unittest.main()