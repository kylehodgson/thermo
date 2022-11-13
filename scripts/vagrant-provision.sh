#!/bin/bash
sudo apt-get -y update
sudo apt-get -y install postgresql postgresql-contrib libpq-dev
sudo apt-get -y install python3 python3-venv python3-pip
sudo setcap cap_net_raw,cap_net_admin+eip $(eval readlink -f `which python3`)
sudo systemctl start postgresql
sudo -u postgres createdb thermo
sudo -u postgres createuser zonemgr

mkdir -p ~/thermo
git clone /vagrant ~/thermo
cd ~/thermo
python3 -m venv venv

sudo -u postgres psql thermo -f /vagrant/db/migration-0001.sql
sudo -u postgres psql thermo -f /vagrant/db/migration-0002.sql
sudo -u postgres psql thermo -f /vagrant/db/migration-0003.sql

somechars=$(LC_ALL=C tr -dc 'A-Za-z0-9' </dev/urandom | head -c 24 ; echo)
sed -e s/\|CHANGEME\|/${somechars}/g < example.env > .env
sudo -u postgres psql thermo -c "ALTER USER zonemgr WITH PASSWORD '${somechars}'"
. ./.env
sudo ./scripts/install.sh
