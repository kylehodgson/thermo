# About
This project seeks to automate the process of 1) listening to bluetooth thermometers / hygrometers, and 2)
switching smart plugs off an on; particurlarly when those smart plugs are controlling infrared panel heaters
or other inexpensive, safe, electrical heating devices.

# Install and Run

## Using bash and Raspian...

This assumes you will put the code in `/home/pi/projects`, which we will refer to as `~/projects`.
### Install `asdf` and Python
```bash
git clone https://github.com/asdf-vm/asdf.git ~/.asdf
echo '. $HOME/.asdf/asdf.sh' >> ~/.bashrc
echo '. $HOME/.asdf/completions/asdf.bash' >> ~/.bashrc
. ~/.bashrc
asdf plugin-add python
cd ~/projects/thermo
asdf install
```
### Verify the version of python
Version should match what is in .tool-versions at this stage -don't continue until they match
```bash
which python3
python3 --version
cat ~/projects/thermo/.tool-versions
```

### Source `venv` environment and install dependencies
```bash
cd ~/projects/thermo
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
```

### Install and setup postgres environment
```bash
sudo apt install postgresql postgresql-contrib libpqdev
sudo systemctl start postgresql
sudo -u postgres createdb thermo
sudo -u postgres createuser zonemgr
sudo -u postgres psql thermo -f db/migration-0001.sql 
cat example.env > ~/projects/thermo/.env
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

## `thermo` service

*`thermo.py`*

The `thermo` service is the main thermostat loop. It loads its configuration, then begins listening for bluetooth advertisements from a `sensor`.

### `sensor`

A `sensor` is a thermometer device that has been placed in an area (called a zone) that you would like to heat.

`thermo` assumes you are using a bluetooth low energy (BLE) thermometer, basically because the author is lazy and doesn't want to be replacing AAA batteries all the time.  At this time, the project supports [Govee Bluetooth Thermo-Hygrometers](https://ca.govee.com/collections/thermo-hydrometer/products/govee-bluetooth-thermo-hygrometer) model 5075, though in theory any reasonable ble emitting thermometer would do.  

### `zone`

A `zone` is a room that you'd like to control. This application works by setting up separate zones, each with its own heater, sensor and smartplug.

### `panel`

`thermo` assumes the use of infrared panel heaters, such as the [Wexstar](https://www.wexstar.com/infrared-heaters) 600 watt. Any infrared heating panel will do. Please do not use any heating device unsafely.

### `smartplug`

`thermo` assumes that all panels are plugged in to smart plugs. This project currently supports the Kasa wifi protocol, though, again in theory any wifi (or IP) addressable smartplug that can be controlled with Python should work fine.

## Zone Manager

The Zone Manager is a small http service that 