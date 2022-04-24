# About
This project seeks to automate the process of 1) listening to bluetooth thermometers / hygrometers, and 2)
switching smart plugs off an on; particurlarly when those smart plugs are controlling infrared panel heaters
or other inexpensive, safe, electrical heating devices.

A jumbo epic sized user story might go something like this:

> *As a concerned human that heats my space with natural gas (or oil, or anything else that burns),*
> 
> *I would like a system that can turn on and off electric heaters that plug in to a wall socket (usually an infrared panel) based on the temperature,*
> 
> *So that I can stop burning stuff to heat the whole building and only heat the rooms I want (usually bedrooms overnight),*
> 
> *Until I get a heat pump.*

This project came about when I became obsessed with the possibility of infrared heat panels (thanks to [Fully Charged](https://www.youtube.com/watch?v=NNITlK7HW0Q) on YouTube); and was unable to find a way to control them with a thermostat. With a nest we could add temperature sensors to different rooms, but that didn't give me the control I wanted.

### My setup now

 - Use the nest to do its thing; heating our home. Place one thermometer sensor in a room controlled by the `thermo` system.
 - Set the nest schedule to focus on a `thermo` controlled room over night, but go back to its default during the day / evening while we're using the kitchen, living room, dining room etc
 - Three rooms in our house are "zones" for `thermo`. Two bedrooms, and one office like space.
 - The bedrooms are set to "scheduled"; which means `thermo` will keep them up to temperature between 10 PM and 8 AM
 - The office space we either enable or disable when we are using it via the web app, as its used in an ad hoc fashion
 - When `thermo` kicks in and warms up the bedroom with the sensor in it, the nest shuts down the furnace (since `thermo` keeps it warm enough)
 - The next morning the nest switches to a sensor in the main area of the home, so it starts heating up the rest of the home
 - This reliably saves us ~ 8 hours worth of gas heating every day! (now to calculate how long it will take me to get to a gigaton...)

More about the hardware we're using
 - `thermo` and the `zone manager` are running on a Raspberry Pi 4 right now, though I'm working on getting it working on a Pi zero /W
 - Wexstar 600 watt panels are totally capable of quickly warming up any room like space in a home (say a bedroom like space with walls and a door)
 - We also use the panels in "open" areas of the house; they work more like space heaters at that point where you need to be right next to it
 - The govee thermometer / hygrometers emit BLE advertisements from rooms all over the house and the pi has no problem receiving them
 - The panels are plugged in to kasa smartplugs (which is handy as they have a nice Python API)
 - You could skip the nest sensor bit, and just schedule the nest to switch to 'eco' mode when `thermo` kicks in; however, having the sensor in one of the rooms acts as a failsafe in case I forget to restart the service when I'm monkeying with it (or if the pi gets unplugged)

Future directions
 - I have this idea to use something like a [GridEye](https://industrial.panasonic.com/ww/products/pt/grid-eye) sensor to detect when we enter a room, instead of relying on humans to switch things on and off or wait for a schedule. Could fall back to something like a Bluetooth listener (to detect humans based on the phones they inevitably carry) or even a passive IR detector, but I think an active sensor makes the most sense (we've all waved to no one in particular to turn on the lights at work thanks to passive IR detectors)
 - Extend the UI to get auto-discovery of devices working and set an initial configuration 
 - Build a "hardware UI"; maybe a small LCD display to extend the pi so that humans can change the temperature without having to go fiddle around with the web interface on their phone

# Install and Run

## Using bash and Raspbian...

### Source `venv` environment and install dependencies
```bash
cd ~/projects/thermo
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
```

### Install and setup postgres environment
```bash
sudo apt install postgresql postgresql-contrib libpq-dev
sudo systemctl start postgresql
sudo -u postgres createdb thermo
sudo -u postgres createuser zonemgr
sudo -u postgres psql thermo -f db/migration-0001.sql
cat ~/projects/thermo/example.env > ~/projects/thermo/.env
. .env
```

## Run
```bash
cd ~/projects/thermo
. venv/bin/activate
. .env
python thermo.py
uvicorn zonemgr.api:app --host 0.0.0.0 --port 8888
```
