#!/bin/bash
sudo apt -y update
sudo apt -y install postgresql postgresql-contrib libpq-dev
sudo apt -y install python3
sudo setcap cap_net_raw,cap_net_admin+eip $(eval readlink -f `which python3`)
sudo systemctl start postgresql
sudo -u postgres createdb thermo
sudo -u postgres createuser zonemgr
sudo -u postgres psql thermo -f /vagrant/db/migration-0001.sql
. /vagrant/example.env
pip3 install -r /vagrant/requirements.txt
cd /vagrant
/home/vagrant/.local/bin/uvicorn zonemgr.api:app --host 0.0.0.0 --port 8888 &
