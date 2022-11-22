from kasa import SmartPlug as KasaPlugService
from thermostat.config import SmartPlugType
from zonemgr.models import PlugConfiguration

class SmartPlug:
    
    config: PlugConfiguration
    type: SmartPlugType
    provider: object

    def __init__(self, zoneConfig: PlugConfiguration) -> None:
        self.config = zoneConfig
        self.type = SmartPlugType.KASA
    
    def update(self):
        if self.type == SmartPlugType.KASA:
             self.provider = KasaSmartPlugProvider()
             print(f"have a kasa plug with config {self.config}")
             self.provider.update(self.config)
    
class KasaSmartPlugProvider:

    async def update(self, config):
        print(f"updating kasa plug with plug {config.plug}")
        k = KasaPlugService(config.plug)
        await k.update()
        
