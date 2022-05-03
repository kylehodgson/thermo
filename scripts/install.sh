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

groupadd -f $group
useradd -d $srcdir -g $group -s /bin/sbin/nologin $user

mkdir -p $libdir
chown -R $user $libdir
chgrp -R $group $libdir

mkdir -p $logdir
chown $user $logdir
chgrp $group $logdir

mkdir -p $rundir
chown $user $rundir
chgrp $group $rundir

cp $srcdir/scripts/systemd/thermo.sh $libdir
cp $srcdir/scripts/systemd/zonemgr.sh $libdir
cp $srcdir/scripts/systemd/thermo.service $systemdir
cp $srcdir/scripts/systemd/zonemgr.service $systemdir


