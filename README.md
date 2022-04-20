# About
This project seeks to automate the process of 1) listening to bluetooth thermometers / hygrometers, and 2)
switching smart plugs off an on; particurlarly when those smart plugs are controlling infrared panel heaters
or other inexpensive, safe, electrical heating devices.

A jumbo epic sized user story might go something like this:

> *As a concerned human that heats my space with natural gas (or oil, or anything else that burns),*
> 
> *I would like a system that can turn on and off electric heaters that plug in to a wall socket (usually an infrared panel) based on the temperature,*
> 
> *So that I can stop burning stuff to heat the whole building and only heat the rooms I want (usually a bedroom overnight),*
> 
> *Until I get a heat pump.*

This project came about when I became obsessed with the possibility of infrared heat panels; and was unable to find a way to control them with a thermostat. With a nest we could add temperature sensors to different rooms, but that didn't give me the control I wanted.

### My setup now

 - Use the nest to do its thing; heating our home. Place one thermometer sensor in a room controlled by the `thermo` system.
 - Set the nest schedule to focus on a `thermo` controlled room over night, but go back to our default schedule the rest of the time
 - Three rooms in our house are "zones" for `thermo`. Two bedrooms, and one office like space.
 - The bedrooms are set to "scheduled"; which means `thermo` will keep them up to temperature between 10 PM and 8 AM
 - The office space we either enable or disable when we are using it via the web app, as its used in an ad hoc fashion
 - The nest shuts down the furnace overnight since `thermo` keeps it warm enough
 - The next morning it starts heating up the rest of the space
 - This reliably saves us ~ 8 hours worth of gas heating every day! (now to calculate how long it will take me to get to a gigaton...)
 - `thermo` and the `zone manager` are running on a Raspberry Pi 4 right now, though I'm working on getting it working on a Pi zero /W
 - The govee thermometer / hygrometers emit BLE advertisements from rooms all over the house and the pi has no problem receiving them
 - The panels are plugged in to kasa smartplugs (which is handy as they have a nice Python API)

# Install and Run

## Using bash and Raspian...

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

# Architecture

![architecture diagram](https://drive.google.com/uc?id=1Ou8uG74sjDqD0kGYJg5DkD5vumICnveZ)


[Architecture diagram link](https://docs.google.com/drawings/d/1zKq6OufqpD5Jf-5vY8Ynvn4B3upaHokV5EIA2D_sQYk/edit?usp=sharing)

## `thermo` service

*`thermo.py`*

The `thermo` service is the main thermostat loop. It loads its configuration, then begins listening for bluetooth advertisements from a `sensor`.

### `sensor`

A `sensor` is a thermometer device that has been placed in an area (called a zone) that you would like to heat.

`thermo` assumes you are using a bluetooth low energy (BLE) thermometer, basically because the author is lazy and doesn't want to be replacing AAA batteries all the time.  At this time, the project supports [Govee Bluetooth Thermo-Hygrometers](https://ca.govee.com/collections/thermo-hydrometer/products/govee-bluetooth-thermo-hygrometer) model 5075, though in theory any reasonable ble emitting thermometer would do.  

### `zone`

A `zone` is an area of a building (often a room) that you want to control the temperature of. This application works by setting up separate zones, each with its own heater, sensor and smartplug.

### `panel`

`thermo` assumes the use of infrared panel heaters, such as the [Wexstar](https://www.wexstar.com/infrared-heaters) 600 watt. Any infrared heating panel will do. Please do not use any heating device unsafely. The infrared panels being used by most users today are very good at warming up a *room*, say a 14x14 room with a door. They aren't quite as good at heating larger open plan areas of a home.

### `smartplug`

`thermo` assumes that all panels are plugged in to smart plugs. This project currently supports the Kasa wifi protocol, though, again in theory any wifi (or IP) addressable smartplug that can be controlled with Python should work fine.

## Zone Manager

The Zone Manager is a small http service that provides the thermostat UI. It relies on services to read and write configuration, and also read and write current conditions. 
