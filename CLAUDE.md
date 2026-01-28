# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Thermo is a Python-based smart home heating automation system that monitors Bluetooth temperature sensors (Govee H5075) and controls TP-Link Kasa smart plugs to manage infrared panel heaters. It features zone-based scheduling, presence detection, and eco-mode that reduces heating when grid carbon intensity is high.

## Common Commands

```bash
# Setup
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt

# Run tests
python -m pytest

# Run application (three separate processes)
python thermo.py                                      # BLE listener & thermostat
uvicorn zonemgr.api:app --host 0.0.0.0 --port 8888   # Web API
python moer.py                                        # Grid intensity polling

# Database migrations (after sourcing .env)
. .env
psql thermo -f db/migration-0001.sql

# Install as systemd services (requires root)
sudo ./scripts/install.sh
```

## Architecture

### Three Main Processes
- **thermo.py** - Scans for BLE sensor advertisements, stores readings, runs thermostat logic
- **zonemgr/api.py** - FastAPI web server with HTMX-based UI on port 8888
- **moer.py** - Polls grid carbon intensity data for eco-mode decisions

### Key Modules
- `zonemgr/thermostat.py` - Core decision logic: evaluates temperatures against targets, applies scheduling, presence, and eco-mode rules
- `zonemgr/panel_plug.py` - Plug abstraction with factory pattern
- `zonemgr/services/` - Database persistence layers for configs, readings, MOER data, presence
- `plugins/kasaplugs.py` - TP-Link Kasa plug control with auto-discovery fallback
- `plugins/goveesensors.py` - Parses Govee BLE advertisements

### Service Types
Zones can be configured with different service types:
- `ON` - Always maintain target temperature
- `OFF` - Never activate
- `SCHEDULED` - Only during configured hours
- `PRESENCE` - Only when room is occupied

### Eco-Mode
Reduces target temperature by 0.75°C when grid carbon intensity exceeds 50th percentile (via MOER data).

## Database

PostgreSQL with these main tables:
- `sensor_configurations` - Zone setup with target temps, schedules, plug IPs
- `temperature_readings` - Sensor data history
- `moer_readings` - Grid carbon intensity history
- `zone_presence` - Room occupancy states

Environment variables for connection: `PGHOST`, `PGUSER`, `PGDATABASE`, `PGPASSWORD` (see example.env)

## Important Implementation Details

- Uses Python asyncio for Kasa plug operations (async/await)
- Kasa plugs can be rediscovered by name if IP changes (DHCP)
- BLE scanning requires capabilities: `sudo setcap cap_net_raw,cap_net_admin+eip $(eval readlink -f \`which python3\`)`
- Acceptable temperature drift is 1°C before triggering plug changes
- Minimum 5-second interval between thermostat checks to prevent rapid cycling
