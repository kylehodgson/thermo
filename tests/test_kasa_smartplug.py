import asyncio
import pytest
import time
from kasa import Discover
from plugins.kasaplugs import KasaPanelPlug

INVALID_IP = "192.0.2.100"  # https://stackoverflow.com/questions/10456044/what-is-a-good-invalid-ip-address-to-use-for-unit-tests / https://www.rfc-editor.org/rfc/rfc5737


class TestKasaPanelPlug:
    first_plug: dict
    second_plug: dict

    def setup_class(self):
        self.first_plug = {}
        self.second_plug = {}

        devices = asyncio.run(Discover.discover())

        devices_found = len(devices.items())
        if devices_found < 2:
            raise RuntimeError(
                "Could not find enough TP link devices for functional test")
        else:
            print(f"found {devices_found} devices")

        first_addr = next(iter(devices))
        second_addr = next(iter(devices))

        self.first_plug['ip'] = first_addr
        self.first_plug['alias'] = devices[first_addr].alias

        self.second_plug['ip'] = second_addr
        self.second_plug['alias'] = devices[second_addr].alias

    @pytest.mark.asyncio
    async def test_can_connect_to_plugs(self):
        kp = KasaPanelPlug()
        kp.set_host(self.first_plug['ip'], self.first_plug['alias'])
        # get_state is going to do a network discovery; when running those back to back it seems to get confused.
        time.sleep(1.5)
        kp_state = await kp.get_state()
        assert (kp.name == self.first_plug['alias'])
        assert (kp.host == self.first_plug['ip'])
        assert (kp_state.ON or kp_state.OFF)

    @pytest.mark.asyncio
    async def test_can_recover_from_wrong_ip_for_device(self):
        kp = KasaPanelPlug()
        # DHCP gives plug1's IP to plug2
        kp.set_host(self.first_plug['ip'], self.second_plug['alias'])
        time.sleep(1.5)
        kp_state = await kp.get_state()
        assert (kp.name == self.second_plug['alias'])
        assert (kp.host == self.second_plug['ip'])
        assert (kp_state.ON or kp_state.OFF)

    @pytest.mark.asyncio
    async def test_can_recover_from_host_with_invalid_ip(self):
        kp = KasaPanelPlug()
        # DHCP gives plug1's old IP to no one
        kp.set_host(INVALID_IP, self.first_plug['alias'])
        time.sleep(1.5)
        kp_state = await kp.get_state()
        assert (kp.name == self.first_plug['alias'])
        assert (kp.host == self.first_plug['ip'])
        assert (kp_state.ON or kp_state.OFF)
