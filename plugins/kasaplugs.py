#!/usr/bin/env python
import sys
import asyncio
from kasa import Discover, SmartPlug, SmartDeviceException
from zonemgr.panel_plug import PanelState, PanelDecision, PanelPlug

class KasaPanelPlug(PanelPlug):
    kasa: SmartPlug
    host: str
    name: str

    def __init__(self) -> None:
        pass

    def set_host(self, host, name) -> None:
        self.kasa = SmartPlug(host)
        self.host=host
        self.name=name

    # kasa plugs may be assigned new IP addresses from time to time. in that case, we will want to 
    # fall back on a discovery protocol to find the right IP for the name we've been provided.
    # when this happens we'll get a SmartDeviceException if the IP provided isn't a TP link device;
    # however, in the case that this is another TP link device but not the one we want, no exception 
    # is raised.
    async def discover_suggested_(self) -> bool:
        discover_suggested=False 
        try:
            await self.kasa.update()
        except SmartDeviceException as e:
            # print(f"SmartDeviceException {e=} of type {type(e)} on kasa.update with host {self.host} and name {self.name}")
            discover_suggested=True
        except Exception as e:
            print(f"Unexpected exception {e=} of type {type(e)} on kasa.update with host {self.host} and name {self.name}")
            raise
        else:
            if self.kasa.alias!=self.name:
                print(f"plug alias {self.kasa.alias} and name {self.name} did not match, suggesting discovery.")
                discover_suggested=True
        return discover_suggested

    async def get_state(self) -> PanelState:
        if await self.discover_suggested_():
            devices = await Discover.discover()
            for addr, dev in devices.items():
                await dev.update()
                if dev.is_plug and dev.alias==self.name:
                    print(f"discover attempt in KasaPanelPlug found addr {addr} alias {dev.alias} ip {dev.host} as a match for original host {self.host} name {self.name}, using this new host instead.")
                    # todo: log this somewhere, or event it somehow ... the config is wrong, and the user doesn't know. probably a DHCP change.
                    self.kasa=dev
                    self.host=dev.host

        if self.kasa.is_off:
            return PanelState.OFF
        if self.kasa.is_on:
            return PanelState.ON
        raise Exception(
            f"kasa plug at {self.kasa.host} in an unknown state. "
            f"is_off: {self.kasa.is_off} "
            f"is_on: {self.kasa.is_on}")

    async def set_state(self, decision: PanelDecision) -> None:
        if decision == PanelDecision.TURN_OFF:
            await self.kasa.turn_off()
        elif decision == PanelDecision.TURN_ON:
            await self.kasa.turn_on()



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

# this method signature is a legacy one in use by the discover class.
async def discover_plugs() -> list:
    plugs = []
    devices = await Discover.discover()
    for addr, dev in devices.items():
        await dev.update()
        if (dev.is_plug):
            plugs.append(plug_from_dev(dev))
    return plugs


def main() -> int:
    loop = asyncio.get_event_loop()

    for plug in loop.run_until_complete(discover_plugs()):
        print(f"{plug['name']}:")
        for property in plug:
            if property != 'name':
                print(f"\t{property}\t{plug[property]}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
