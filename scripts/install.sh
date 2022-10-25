#!/bin/bash

if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi

srcdir=/home/pi/projects/thermo
libdir=/usr/local/lib/thermo
systemdir=/etc/systemd/system
logdir=/var/log/thermo
rundir=/run/thermo

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

function installScripts()
{
  svcname=$1
  echo "Installing start script and service file for $svcname..."
  cp $srcdir/scripts/systemd/$svcname.sh $libdir
  cp $srcdir/scripts/systemd/$svcname.service $systemdir
  echo "Enabling $svcname ... "
  systemctl enable $svcname
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

if [ ! -f /usr/lib/tmpfiles.d/thermo.conf ]
then
  cp $srcdir/scripts/systemd/thermo.conf /usr/lib/tmpfiles.d
fi

makeDirectoryFor $libdir $user $group
makeDirectoryFor $logdir $user $group
makeDirectoryFor $rundir $user $group

installScripts thermo
installScripts zonemgr
installScripts moer

echo "reloading systemd configs..."
systemctl daemon-reload
echo "restarting services..."
systemctl restart moer
systemctl restart thermo
systemctl restart zonemgr
