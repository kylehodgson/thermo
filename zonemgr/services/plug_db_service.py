import zonemgr.models as models
from zonemgr.db import ZoneManagerDB

class PlugService:
    zmdb: ZoneManagerDB

    def __init__(self, zmdb: ZoneManagerDB) -> None:
        self.zmdb=zmdb
