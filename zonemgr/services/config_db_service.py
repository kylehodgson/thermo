from distutils.debug import DEBUG
import psycopg2
import zonemgr.models as models
from zonemgr.db import ZoneManagerDB

class ConfigService:
    zmdb: ZoneManagerDB

    def __init__(self, zmdb: ZoneManagerDB) -> None:
        self.zmdb=zmdb

    def save(self,sc):
        id,sc_record=self.get_sensor_config(sc.sensor)

        with self.zmdb as conn: # reading values from environment
            with conn.cursor() as cursor:

                if sc_record:
                    cursor.execute("UPDATE public.sensor_configurations set config=%s WHERE id=%s; ", (sc.json(), id))
                else:
                    cursor.execute("INSERT INTO public.sensor_configurations (config) values (%s) returning id;", (sc.json(), ))
                    id=cursor.fetchone()[0]
                conn.commit()
        return id

    def get_sensor_config(self,sensor: str):
        criteria="""{"sensor": "%s"}""" % sensor
        with self.zmdb as conn:
            with conn.cursor() as cursor:
                cursor.execute("""select id, config from public.sensor_configurations where config @> %s;""" , (criteria, ))
                if cursor.rowcount>0:
                    record=cursor.fetchone()
                    id=record[0]
                    sc=models.SensorConfiguration.parse_obj(record[1])
                    return (id, sc)
                else:
                    return (0, False)

    def get_all_sensor_configs(self):
        config=[]
        with self.zmdb as conn:
            with conn.cursor() as cursor:
                cursor.execute("select config from public.sensor_configurations;")
                for row in cursor:
                    config.append(row[0])
        return config

    def load_config(self):
        return self.get_all_sensor_configs()

    def set_sensor_config(self, sensor_id: str, temp: float, service: str, name: str="", location: str="", plug=""):
        sc=models.SensorConfiguration(sensor_id=sensor_id, temp=temp, service=service, name=name, location=location, plug=plug)
        self.save(sc)
        return sc
