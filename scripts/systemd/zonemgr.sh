#!/usr/bin/bash

pidfile="/run/thermo/zonemgr.pid"
logfile="/var/log/thermo/zonemgr.log"
bindir=|BINDIR|

if [ ! -d /run/thermo]
then
	mkdir /run/thermo
fi

function start_service {
    echo "" >> $logfile 2>&1
    echo "starting zonemanager..." >> $logfile 2>&1
    cd $bindir
    . venv/bin/activate
    . .env
    python -m uvicorn zonemgr.api:app --host 0.0.0.0 --port 8888 >> $logfile 2>&1 &
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
    echo "zone manager failed to start."
}

function echo_success {
    echo "zone manager started."
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
