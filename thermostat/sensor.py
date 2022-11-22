import bleson
from bleson import get_provider, Observer, UUID16
from bleson.logger import log, ERROR, DEBUG, INFO
from discover.goveesensors import GoveeSensorsDiscovery


# https://macaddresschanger.com/bluetooth-mac-lookup/A4%3AC1%3A38
# OUI Prefix	Company
# A4:C1:38	Telink Semiconductor (Taipei) Co. Ltd.
GOVEE_BT_MAC_OUI_PREFIX = "A4:C1:38"
H5075_UPDATE_UUID16 = UUID16(0xEC88)


bleson.logger.set_level(ERROR)

class Sensor:
    pass