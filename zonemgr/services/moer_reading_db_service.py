from typing import List
from zonemgr.db import ZoneManagerDB
from zonemgr.models import MoerReading

class MoerReadingStore:
    zmdb: ZoneManagerDB

    def get_local_ba_id(self)->str:
        return "IESO_NORTH" ## replace me with something that uses the WattTime API to get the local ba

    def __init__(self, zmdb: ZoneManagerDB) -> None:
        self.zmdb=zmdb

    def save_if_newer(self, reading: MoerReading) -> None:
        with self.zmdb as conn: 
            with conn.cursor() as cursor:
                cursor.execute( ("INSERT INTO public.moer_readings (reading) "
                                 "SELECT (%s) WHERE NOT EXISTS "
                                 "  (SELECT id FROM public.moer_readings "
                                 "   WHERE extract(epoch from (CURRENT_TIMESTAMP::timestamp - reading_time::timestamp)) < %s "
                                 "   AND reading ->> 'ba_id' = %s );"), 
                                 (reading.json(), 10, reading.ba_id))
                conn.commit()

    def get_moer_readings_for(self, ba_id: str, days: int) ->List[MoerReading]:
        criteria="""{"ba_id": "%s"}""" % ba_id
        readings=[]
        with self.zmdb as conn:
            with conn.cursor() as cursor:
                cursor.execute("""select reading from public.moer_readings where reading_time > current_date - interval '%s' day and reading @> %s ;""" , (days, criteria))
                for (record,) in cursor:
                    readings.append(MoerReading.parse_obj(record))
        return readings
        
    
    def select_latest_moer_reading(self,ba_id: str) -> MoerReading:
        criteria="""{"ba_id": "%s"}""" % ba_id
        with self.zmdb as conn:
            with conn.cursor() as cursor:
                cursor.execute("""select reading from public.moer_readings where reading @> %s ORDER BY reading_time desc LIMIT 1;""" , (criteria, ))
                if cursor.rowcount>0:
                    (reading,)=cursor.fetchone()
                    return MoerReading.parse_obj(reading)

