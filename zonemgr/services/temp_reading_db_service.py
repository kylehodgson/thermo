from zonemgr.db import ZoneManagerDB
from zonemgr.models import TemperatureReading

class TempReadingStore:
    zmdb: ZoneManagerDB

    def __init__(self, zmdb: ZoneManagerDB) -> None:
        self.zmdb=zmdb

    def save_if_newer(self, reading: TemperatureReading, seconds_elapsed: int) -> None:
        with self.zmdb as conn: 
            with conn.cursor() as cursor:
                cursor.execute( ("INSERT INTO public.temperature_readings (reading) "
                                 "SELECT (%s) WHERE NOT EXISTS "
                                 "  (SELECT id FROM public.temperature_readings "
                                 "   WHERE extract(epoch from (CURRENT_TIMESTAMP::timestamp - reading_time::timestamp)) < %s "
                                 "   AND reading ->> 'sensor_id' = %s );"), 
                                 (reading.json(), seconds_elapsed, reading.sensor_id))
                conn.commit()

    def select_latest_temperature_reading(self,sensor_id: str):
        criteria="""{"sensor_id": "%s"}""" % sensor_id
        with self.zmdb as conn:
            with conn.cursor() as cursor:
                cursor.execute("""select reading, reading_time from public.temperature_readings where reading @> %s ORDER BY reading_time desc LIMIT 1;""" , (criteria, ))
                if cursor.rowcount>0:
                    record=cursor.fetchone()
                    (reading,timestamp)=record
                    reading = TemperatureReading.parse_obj(reading)
                    return (reading, timestamp)
                else:
                    return (False, False)
    
    def getTemperatureReading(self,sensor: str):
        (reading, time)=self.select_latest_temperature_reading(sensor)
        return reading.temp


