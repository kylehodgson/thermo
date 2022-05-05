import asyncio

from zonemgr.services.plug_db_service import PlugService
from . import kasaplugs
from . import goveesensors

async def discover_all(plugsvc: PlugService):
    plugs = await kasaplugs.discover()
    sensors = goveesensors.discover()
    plugsvc.savePlugs(plugs)
    found = {}
    found['plugs']=plugs
    found['sensors']=sensors
    return found

if __name__ == '__main__':
    found = asyncio.run(discover_all())
    print(f"{found}")
