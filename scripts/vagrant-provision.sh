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
        echo "creating group $group..."
        groupadd $group
    else
        echo "Skipping groupadd, group $group already existed with id $gid"
    fi

    uid=$(id -u $user)
    if [ -z $uid ]
    then
        echo "creating user $user..."
        useradd -g $group $user
    else
        echo "Skipping useradd, user $user already existed with id $uid"
    fi
}

function installApp() {
    base=$1
    user=$2
    group=$3

    mkdir -p $base/app

    git clone /vagrant $base/app
    cd $base/app
    python3 -m venv venv
    . venv/bin/activate
    pip3 install -r requirements.txt
    
    somechars=$(LC_ALL=C tr -dc 'A-Za-z0-9' </dev/urandom | head -c 24 ; echo)
    sed -e s/\|CHANGEME\|/${somechars}/g < example.env > .env
    sudo -u postgres psql thermo -c "ALTER USER zonemgr WITH PASSWORD '${somechars}'"
    
    . ./.env
    for sql in $(ls db/*.sql)
    do
        psql thermo -f $base/app/$sql
    done

    chown -R $user:$group $base
    sudo ./scripts/install.sh
}

username=thermo
groupname=thermo
addUserAndGroup $username $groupname
installApp /home/thermo/ $username $groupname
