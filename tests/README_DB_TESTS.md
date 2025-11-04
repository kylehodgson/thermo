# Database Integration Tests

## Purpose

The tests in `test_db_services.py` verify the behavior of database service methods, specifically testing for SQL injection vulnerabilities in JSONB queries.

## Prerequisites

### 1. PostgreSQL Setup

Ensure PostgreSQL is running and configured with the following:

```bash
# Set environment variables (or use example.env)
export PGHOST=localhost
export PGUSER=zonemgr
export PGDATABASE=thermo
export PGPASSWORD=your_password
```

### 2. Database Initialization

Run the database migrations to create the required tables:

```bash
# Connect to PostgreSQL and create user/database
su - postgres -c "psql" <<EOF
CREATE USER zonemgr WITH PASSWORD 'your_password';
CREATE DATABASE thermo OWNER zonemgr;
EOF

# Run migrations
for migration in db/migration-*.sql; do
    psql -h localhost -U zonemgr -d thermo -f "$migration"
done
```

### 3. Install Test Dependencies

```bash
pip install -r local_requirements.txt
```

## Running the Tests

### Run all database service tests:
```bash
python -m pytest tests/test_db_services.py -v
```

### Run specific test class:
```bash
python -m pytest tests/test_db_services.py::TestConfigStore -v
```

### Run with coverage:
```bash
python -m pytest tests/test_db_services.py --cov=zonemgr.services --cov-report=html
```

## What These Tests Verify

### 1. Normal Operations
- Save and retrieve configurations, temperature readings, presence data, and MOER readings
- Query for non-existent records (should return None or empty)

### 2. SQL Injection Attempts
Each service is tested against common JSONB injection patterns:

- **Quote escaping**: `A4:C1:38:00:00:01", "admin": "true"`
- **JSON structure manipulation**: `A4", "service_type": "OFF"`
- **Wildcard matching**: `", "sensor_id": "..."`

These tests should FAIL if injection is possible (i.e., if malicious input matches unintended records).

## Expected Behavior

**Current (Vulnerable) Code:**
- Injection attempts may match unintended records
- Tests may fail, exposing the vulnerability

**After SQL Injection Fix:**
- All injection attempts should return no results
- Only exact sensor_id/ba_id matches should return data
- All tests should pass

## Test Database Cleanup

The tests create test data during execution. To clean up:

```bash
psql -h localhost -U zonemgr -d thermo <<EOF
TRUNCATE TABLE sensor_configurations CASCADE;
TRUNCATE TABLE temperature_readings CASCADE;
TRUNCATE TABLE zone_presence CASCADE;
TRUNCATE TABLE moer_readings CASCADE;
EOF
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'pytest'"
```bash
pip install pytest pytest-asyncio
```

### "connection to server ... failed"
Ensure PostgreSQL is running:
```bash
sudo service postgresql start
# or
sudo pg_ctlcluster 16 main start
```

### "FATAL: role does not exist"
Create the PostgreSQL user:
```bash
su - postgres -c "createuser -P zonemgr"
```

### "database does not exist"
Create the database:
```bash
su - postgres -c "createdb -O zonemgr thermo"
```
