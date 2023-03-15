if __name__ == "__main__" and __package__ is None:
    from sys import path
    from os.path import dirname as dir
    path.append(dir(path[0]))

import asyncio
import kasaplugs
import goveesensors

import logging
log = logging.getLogger(__name__)

async def discover_all(plugsvc=None):
    plugs = await kasaplugs.discover_plugs()
    sensors = goveesensors.discover()
    if plugsvc:
        plugsvc.savePlugs(plugs)
    found = {}
    found['plugs']=plugs
    found['sensors']=sensors
    return found

if __name__ == '__main__':
    found = asyncio.run(discover_all())
    log.info(f"{found}")
