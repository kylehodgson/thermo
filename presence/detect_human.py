import smbus2 as smbus
from thirdparty.gridpy import gridpy
import uuid
import time
import json
import sys

def view_captures():
    import glob
    for cap in glob.glob("captures/*.json"):
        print(f"{cap}")
        with open(cap, 'r') as f:
            display_capture(json.load(f))
            
def display_capture(image):
    import os
    from ansimarkup import ansiprint
    if len(image)>0:
                os.system("clear")
                for r in image:
                    for c in r:
                        if float(c) < 20:
                            ansiprint(f"<fg 19>{c}</fg 19>", end='\t')
                        elif float(c) >= 20 and float(c) <21:
                            ansiprint(f"<fg 22>{c}</fg 22>", end='\t')
                        elif float(c) >=21 and float(c) <22:
                            ansiprint(f"<fg 29>{c}</fg 29>", end='\t')
                        elif float(c) >= 22 and float(c) <23:
                            ansiprint(f"<fg 94>{c}</fg 94>", end='\t')
                        elif float(c) >=23 and float(c) <24:
                            ansiprint(f"<fg 202>{c}</fg 202>", end='\t')
                        elif float(c) >=24:
                            ansiprint(f"<red>{c}</red>", end='\t')
                        else:
                            print(f"{c}", end='\t')
                    print('')
                    print('')
    else:
                print("capture failed")
    time.sleep(0.05)


def store_capture(cap_id, image):
    timestr = time.strftime("%Y%m%d-%H%M%S")
    filename="captures/" + timestr + "-" + cap_id + ".json"
    with open(filename, 'w') as f:
            json.dump(image,f)

def get_image(bus):
    try: 
        image =  gridpy.GridEye(i2c_address=0x69, i2c_bus=bus).get_sensor_data()[0]
    except OSError as e:
        print(f"OSError exception {e}")
        return []
    return image

if len(sys.argv)>1 and sys.argv[1]=="replay":
    view_captures()
else:
    while True:
        capture_id=str(uuid.uuid4())
        with smbus.SMBus(1) as bus:
            image = get_image(bus)
            display_capture(image)
            #store_capture(capture_id, image)
