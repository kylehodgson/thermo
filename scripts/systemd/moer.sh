#!/usr/bin/bash

pidfile="/run/thermo/moer.pid"
logfile="/var/log/thermo/moer.log"
bindir=|BINDIR|

if [ ! -d /run/thermo ]
then
	mkdir -p /run/thermo
fi

function start_service {
    echo "" >> $logfile 2>&1
    echo "starting moer service..." >> $logfile 2>&1
    cd $bindir
    . venv/bin/activate
    . .env
    python moer.py >> $logfile 2>&1 &
    RETVAL=$?
    PID=$!
    [ $RETVAL -eq 0 ] && echo $PID > $pidfile && echo_success || echo_failure
}

function stop_service {
    if test -f "$pidfile"; then
        PID=$( cat $pidfile )
        kill -9 $PID
        exit 0
    fi
    echo "Did not find pidfile $pidfile "
    exit 1
}

function echo_failure {
    echo "moer service failed to start."
}

function echo_success {
    echo "moer service started."
}

if [ "$1" == "start" ]
then
    echo "Starting $0 ..."
    start_service
fi

if [ "$1" == "stop" ]
then
    echo "Stopping $0 ..."
    stop_service
fi
