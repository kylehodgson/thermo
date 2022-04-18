import asyncio
from . import kasaplugs
from . import goveesensors

async def discover_all():
    plugs = await kasaplugs.discover()
    sensors = goveesensors.discover()
    found = {}
    found['plugs']=plugs
    found['sensors']=sensors
    return found

if __name__ == '__main__':
    found = asyncio.run(discover_all())
    print(f"{found}")
