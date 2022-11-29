#!/usr/bin/env python
import sys
import asyncio
from kasa import Discover, SmartPlug
from zonemgr.panel_plug import PanelState, PanelDecision, PanelPlug, EcoMode

class KasaPanelPlug(PanelPlug):
    kasa: SmartPlug

    def __init__(self) -> None:
        pass

    def set_host(self, host) -> None:
        self.kasa = SmartPlug(host)

    async def get_state(self) -> PanelState:
        await self.kasa.update()
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


async def discover() -> list:
    plugs = []
    devices = await Discover.discover()
    for addr, dev in devices.items():
        await dev.update()
        if (dev.is_plug):
            plugs.append(plug_from_dev(dev))
    return plugs


def main() -> int:
    loop = asyncio.get_event_loop()

    for plug in loop.run_until_complete(discover()):
        print(f"{plug['name']}:")
        for property in plug:
            if property != 'name':
                print(f"\t{property}\t{plug[property]}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
