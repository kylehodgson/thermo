#!/usr/bin/bash
cd /home/pi/projects/thermo
. venv/bin/activate
uvicorn zonemgr.api:app --host 0.0.0.0 --port 8888 >> /var/log/zonemgr.log 2>&1
