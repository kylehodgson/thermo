# About
This project seeks to automate the process of 1) listening to bluetooth thermometers / hygrometers, and 2)
switching smart plugs off an on; particurlarly when those smart plugs are controlling infrared panel heaters
or other inexpensive, safe, electrical heating devices.


# Install and Run

## Using bash and Raspbian...

### Source `venv` environment and install dependencies
```bash
cd ~/projects/thermo
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
```

### Set permissions for python to access bluetooth
```bash
sudo setcap cap_net_raw,cap_net_admin+eip $(eval readlink -f `which python3`)
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
