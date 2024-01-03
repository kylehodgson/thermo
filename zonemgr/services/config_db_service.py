from typing import List, Tuple
from zonemgr.db import ZoneManagerDB
from zonemgr.models import SensorConfiguration

import logging
log = logging.getLogger(__name__)

class ConfigStore:
    zmdb: ZoneManagerDB

    def __init__(self, zmdb: ZoneManagerDB) -> None:
        self.zmdb=zmdb

    def save(self,sc):
        id,sc_record=self.get_config_for(sc.sensor_id)
        with self.zmdb as conn: # reading values from environment
            with conn.cursor() as cursor:
                if sc_record:
                    sc.name=sc.name or sc_record.name
                    sc.location=sc.location or sc_record.location
                    sc.plug=sc.plug or sc_record.plug
                    cursor.execute("UPDATE public.sensor_configurations set config=%s WHERE id=%s; ", (sc.json(), id))
                else:
                    cursor.execute("INSERT INTO public.sensor_configurations (config) values (%s) returning id;", (sc.json(), ))
                    id=cursor.fetchone()[0]
                conn.commit()
        return id

    def get_config_for(self,sensor: str) -> Tuple[int,SensorConfiguration]:
        criteria="""{"sensor_id": "%s"}""" % sensor
        with self.zmdb as conn:
            with conn.cursor() as cursor:
                cursor.execute("""select id, config from public.sensor_configurations where config @> %s;""" , (criteria, ))
                if cursor.rowcount>0:
                    record=cursor.fetchone()
                    id=record[0]
                    sc=SensorConfiguration.parse_obj(record[1])
                    return (id, sc)
                else:
                    return (0, False)

    def get_all_sensor_configs(self) -> List[SensorConfiguration]:
        config=[]
        with self.zmdb as conn:
            with conn.cursor() as cursor:
                cursor.execute("select config from public.sensor_configurations order by id;")
                for row in cursor:
                    config.append(row[0])
        return config

    def load_config(self):
        return self.get_all_sensor_configs()

    def set_sensor_config(self, 
            sensor_id: str, 
            temp: float, 
            service_type: str, 
            name: str = "", 
            location: str = "", 
            plug: str = "", 
            schedule_start_hour: str="", 
            schedule_stop_hour: str=""):
        sc=SensorConfiguration(sensor_id=sensor_id, temp=temp, service_type=service_type) #these three are required params, the rest are not
        if name:
            sc.name=name
        if location:
            sc.location=location
        if plug:
            sc.plug=plug
        if schedule_start_hour.isnumeric():
            sc.schedule_start_hour=int(schedule_start_hour)
        if schedule_stop_hour.isnumeric():
            sc.schedule_stop_hour=int(schedule_stop_hour)
        self.save(sc)
        return sc
