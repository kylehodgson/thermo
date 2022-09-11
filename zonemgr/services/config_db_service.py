import zonemgr.models as models
from zonemgr.db import ZoneManagerDB
from zonemgr.models import ServiceTypes

class ConfigStore:
    zmdb: ZoneManagerDB

    def __init__(self, zmdb: ZoneManagerDB) -> None:
        self.zmdb=zmdb

    def create_default_for(self,reading):
        newSC=models.SensorConfiguration(
            sensor_id=str(reading['sensor_id']), 
            temp=float(20.0), 
            service_type=str(ServiceTypes.Off.value), 
            name=str("New sensor"), 
            location=str("Unknown"),
            plug=str("10.0.0.0"))
        self.save(newSC)

    def save(self,sc):
        id,sc_record=self.get_sensor_config(sc.sensor_id)

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

    def get_sensor_config(self,sensor: str):
        criteria="""{"sensor_id": "%s"}""" % sensor
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
                cursor.execute("select config from public.sensor_configurations order by id;")
                for row in cursor:
                    config.append(row[0])
        return config

    def load_config(self):
        return self.get_all_sensor_configs()

    def set_sensor_config(self, sensor_id: str, temp: float, service_type: str, name: str="", location: str="", plug=""):
        print(f"sensor_id {sensor_id} temp {temp} service_type {service_type} name {name} location {location} plug {plug}")
        sc=models.SensorConfiguration(sensor_id=sensor_id, temp=temp, service_type=service_type)
        if name!="":
            sc.name=name
        if location!="":
            sc.location=location
        if plug!="":
            sc.plug=plug
        self.save(sc)
        return sc
