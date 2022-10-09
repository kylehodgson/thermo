#!/bin/bash

if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi

srcdir=/home/pi/projects/thermo
libdir=/usr/local/lib/thermo
systemdir=/etc/systemd/system
logdir=/var/log/thermo
rundir=/var/run/thermo

user=thermo
group=thermo

function makeDirectoryFor () 
{
  dir=$1
  user=$2
  group=$3

  echo "Creating $dir and setting permissions for user $user group $group..."
  mkdir -p $dir
  chown -R $user $dir
  chgrp -R $group $dir
}

uid=$(id -u $user)
if [ -z $uid ]
then
  useradd -d $srcdir -g $group -s /bin/sbin/nologin $user
else
  echo "Skipping useradd, user $user already existed with id $uid"
fi

gid=$(id -u $group)
if [ -z $gid ]
then
  groupadd -f $group
else
  echo "Skipping groupadd, group $group already existed with id $gid"
fi

makeDirectoryFor $libdir $user $group
makeDirectoryFor $logdir $user $group
makeDirectoryFor $rundir $user $group

cp $srcdir/scripts/systemd/thermo.sh $libdir
cp $srcdir/scripts/systemd/zonemgr.sh $libdir
cp $srcdir/scripts/systemd/thermo.service $systemdir
cp $srcdir/scripts/systemd/zonemgr.service $systemdir

systemctl daemon-reload
