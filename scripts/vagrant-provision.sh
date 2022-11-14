#!/bin/bash
sudo apt-get -y update
sudo apt-get -y install postgresql postgresql-contrib libpq-dev
sudo apt-get -y install python3 python3-venv python3-pip
sudo setcap cap_net_raw,cap_net_admin+eip $(eval readlink -f `which python3`)
sudo systemctl start postgresql
sudo -u postgres createdb thermo
sudo -u postgres createuser zonemgr

function addUserAndGroup() {
    user=$1
    group=$2

    gid=$(id -u $group)
    if [ -z $gid ]
    then
        groupadd -f $group
    else
        echo "Skipping groupadd, group $group already existed with id $gid"
    fi

    uid=$(id -u $user)
    if [ -z $uid ]
    then
        useradd -g $group -s $nologinsh $user
    else
        echo "Skipping useradd, user $user already existed with id $uid"
    fi
}

function installApp() {
    base=$1
    mkdir -p $base/app
    git clone /vagrant $base/app
    cd $base/app
    python3 -m venv venv
    somechars=$(LC_ALL=C tr -dc 'A-Za-z0-9' </dev/urandom | head -c 24 ; echo)
    sed -e s/\|CHANGEME\|/${somechars}/g < example.env > .env
    sudo -u postgres psql thermo -c "ALTER USER zonemgr WITH PASSWORD '${somechars}'"
    for sql in $(ls db/*.sql)
    do
        sudo -u postgres psql thermo -f $base/app/$sql
    done
    . ven/bin/activate
    . ./.env
    sudo ./scripts/install.sh
}

addUserAndGroup thermo thermo
installApp /home/thermo/
