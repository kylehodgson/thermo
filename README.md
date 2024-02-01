# About
This project seeks to automate the process of 1) listening to bluetooth thermometers / hygrometers, and 2)
switching smart plugs off an on; particurlarly when those smart plugs are controlling infrared panel heaters
or other inexpensive, safe, electrical heating devices. 

For more, try the [wiki](https://github.com/kylehodgson/thermo/wiki).

# Install and Run

## Using bash and Raspbian...
The instructions below will likely work fairly well on other Debian based distros too. 
### Source `venv` environment and install dependencies
```
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
Below are some pointers on setting up Postgres on a stock Raspberry pi. Instructions in this README will assume a database named `thermo` has bee created, and a user called `zonemgr` has been created that has access to it, the instructions below make sure that has happened.
```
sudo apt install postgresql postgresql-contrib libpq-dev
sudo systemctl start postgresql
sudo -u postgres createuser -d zonemgr
```

### App connection
First, set a password for the user `zonemgr`:
```
sudo -u postgres psql
psql (11.14 (Debian 11.14-0+deb10u1))
Type "help" for help.

thermo=# \password zonemgr
Enter new password: 
Enter it again: 
thermo=# 
```

`thermo` assumes it can find the correct connection information in the shell environment. We provide an example environment file in `example.env`, copy that and customize it to your needs.

```
cat example.env > .env
```

Then edit the resulting `.env` file to change the password to match.

Next create the database as the thermo user you created above.
```
cd ~/projects/thermo
. .env
createdb thermo
```
### Run migrations

Next, run the provided migrations file to set up the required tables. 
```
cd ~/projects/thermo
. .env
psql thermo -f db/migration-0001.sql
```


## Run in terminal
```bash
cd ~/projects/thermo
. venv/bin/activate
. ./.env
python thermo.py
uvicorn zonemgr.api:app --host 0.0.0.0 --port 8888
```

## Run the Install script as root to install the files and start the service
```bash
cd ~/projects/thermo
sudo ./scripts/install.sh
```

## Run tests
```bash
python -m pytest
```
