

from enum import Enum
from zonemgr.models import PlugConfiguration

class EcoMode(Enum):
    ENABLED = 1
    DISABLED = 0


class PanelState(Enum):
    ON = 1
    OFF = 0


class PanelDecision(Enum):
    DO_NOTHING = 0
    TURN_ON = 1
    TURN_OFF = 2
    
class PanelPlug:
    pass

class PanelPlugFactory:
    def get_plug(self, conf: PlugConfiguration):
        from plugins.kasaplugs import KasaPanelPlug
        return KasaPanelPlug()