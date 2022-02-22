#!/usr/bin/env python
import sys
import asyncio
from kasa import Discover

def plug_from_dev(dev):
    return {
        'name': dev.alias, 
        'model': dev.sys_info['model'], 
        'hardware': dev.sys_info['hw_ver'],
        'software': dev.sys_info['sw_ver'],
        'location': dev.location,
        'on_since': dev.on_since,
        'ip_addr': dev.host
    }

def discover():
    devices = asyncio.run(Discover.discover())
    for addr, dev in devices.items():
        asyncio.run(dev.update())
        if(dev.is_plug):
            yield plug_from_dev(dev)

def main() -> int:
    for plug in discover():
        print(f"{plug['name']}:")
        for property in plug:
            if property!='name':
                print(f"\t{property}\t{plug[property]}")
    return 0

if __name__ == '__main__':
    sys.exit(main())
