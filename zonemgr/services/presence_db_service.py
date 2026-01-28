import json
from typing import Optional
from zonemgr.db import ZoneManagerDB
from zonemgr.models import ZonePresence

import logging
log = logging.getLogger(__name__)

class ZonePresenceStore:
    zmdb: ZoneManagerDB

    def __init__(self, zmdb: ZoneManagerDB) -> None:
        self.zmdb=zmdb

    def save_if_newer(self, presence: ZonePresence, seconds_elapsed: int) -> None:
        with self.zmdb as conn: 
            with conn.cursor() as cursor:
                cursor.execute( ("INSERT INTO public.zone_presence (zone_presence) "
                                 "SELECT (%s) WHERE NOT EXISTS "
                                 "  (SELECT id FROM public.zone_presence "
                                 "   WHERE extract(epoch from (CURRENT_TIMESTAMP::timestamp - presence_time::timestamp)) < %s "
                                 "   AND zone_presence ->> 'sensor_id' = %s );"), 
                                 (presence.json(), seconds_elapsed, presence.sensor_id))
                conn.commit()

    def get_latest_zone_presence_for(self, sensor_id: str) -> Optional[ZonePresence]:
        criteria = json.dumps({"sensor_id": sensor_id})
        with self.zmdb as conn:
            with conn.cursor() as cursor:
                cursor.execute("""select zone_presence from public.zone_presence where zone_presence @> %s ORDER BY presence_time desc LIMIT 1;""", (criteria,))
                if cursor.rowcount > 0:
                    (record,) = cursor.fetchone()
                    return ZonePresence.parse_obj(record)
        return None


