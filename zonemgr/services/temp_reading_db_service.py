from zonemgr.db import ZoneManagerDB
from zonemgr.models import TemperatureReading

class TempReadingService:
    zmdb: ZoneManagerDB

    def __init__(self, zmdb: ZoneManagerDB) -> None:
        self.zmdb=zmdb

    # we are expecting a Pydantic model for reading here, which provides the .json method
    def save(self, reading: TemperatureReading) -> TemperatureReading:
        ## we don't need an upsert; as we don't mind storing all the records; as long as we make sure we keep a tmimestamp
        with self.zmdb as conn: 
            with conn.cursor() as cursor:
                cursor.execute("INSERT INTO public.temperature_readings (reading) values (%s) returning id;", (reading.json(), ))
                id=cursor.fetchone()[0]
                conn.commit()
        if(id):
            return reading
        else:
            raise Exception("failed to write temperature reading")

    def select_latest_temperature_reading(self,sensor: str):
        criteria="""{"sensor": "%s"}""" % sensor
        with self.zmdb as conn:
            with conn.cursor() as cursor:
                cursor.execute("""select reading, timestamp from public.temperature_readings where config @> %s ORDER BY timestamp desc LIMIT 1;""" , (criteria, ))
                if cursor.rowcount>0:
                    record=cursor.fetchone()
                    (reading,timestamp)=record
                    reading = TemperatureReading.parse_obj(reading)
                    return (reading, timestamp)
                else:
                    return (False, False)
    
    def getTemperatureReading(self,sensor: str):
        test_data={'name': "dummy name", 'temp': 19.11, 'battery': 74, 'humidity': 28}
        return test_data['temp']


