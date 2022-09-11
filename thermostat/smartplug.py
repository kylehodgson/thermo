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
             self.provider = KasaSmartPlugProvider
             self.provider.update(self.config)
    
class KasaSmartPlugProvider:

    def update(self, config):
        k = KasaPlugService(config)
        k.update()
        
