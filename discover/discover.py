import asyncio
from . import kasaplugs
from . import goveesensors

async def discover_all():
    found=[]
    found.append(await kasaplugs.discover())
    found.append(goveesensors.discover())
    return found

if __name__ == '__main__':
    found = asyncio.run(discover_all())
    print(f"{found}")
