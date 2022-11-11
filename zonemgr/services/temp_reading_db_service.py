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

    def get_latest_temperature_reading_for(self,sensor_id: str) -> TemperatureReading:
        criteria="""{"sensor_id": "%s"}""" % sensor_id
        with self.zmdb as conn:
            with conn.cursor() as cursor:
                cursor.execute("""select reading from public.temperature_readings where reading @> %s ORDER BY reading_time desc LIMIT 1;""" , (criteria, ))
                if cursor.rowcount>0:
                    (record,)=cursor.fetchone()
                    return TemperatureReading.parse_obj(record)


