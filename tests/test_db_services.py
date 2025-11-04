"""
Integration tests for database services to verify JSONB query behavior
These tests require a running PostgreSQL database with the schema initialized
"""

import pytest
from datetime import datetime
from zonemgr.db import ZoneManagerDB
from zonemgr.services.config_db_service import ConfigStore
from zonemgr.services.temp_reading_db_service import TempReadingStore
from zonemgr.services.presence_db_service import ZonePresenceStore
from zonemgr.services.moer_reading_db_service import MoerReadingStore
from zonemgr.models import SensorConfiguration, TemperatureReading, ZonePresence, MoerReading


@pytest.fixture(scope="module")
def db():
    """Create database connection for tests"""
    zmdb = ZoneManagerDB()
    yield zmdb
    zmdb.shutDown()


@pytest.fixture(scope="module")
def config_store(db):
    """Create ConfigStore instance"""
    return ConfigStore(db)


@pytest.fixture(scope="module")
def temp_store(db):
    """Create TempReadingStore instance"""
    return TempReadingStore(db)


@pytest.fixture(scope="module")
def presence_store(db):
    """Create ZonePresenceStore instance"""
    return ZonePresenceStore(db)


@pytest.fixture(scope="module")
def moer_store(db):
    """Create MoerReadingStore instance"""
    return MoerReadingStore(db)


class TestConfigStore:
    """Tests for ConfigStore.get_config_for()"""

    def test_save_and_retrieve_config(self, config_store):
        """Test normal save and retrieve operation"""
        sensor_id = "A4:C1:38:00:00:01"
        config = SensorConfiguration(
            sensor_id=sensor_id,
            temp=22.0,
            service_type="ON",
            name="Test Sensor",
            location="Test Room"
        )

        # Save config
        saved_id = config_store.save(config)
        assert saved_id > 0

        # Retrieve config
        (retrieved_id, retrieved_config) = config_store.get_config_for(sensor_id)
        assert retrieved_id == saved_id
        assert retrieved_config.sensor_id == sensor_id
        assert retrieved_config.temp == 22.0
        assert retrieved_config.name == "Test Sensor"

    def test_get_config_for_nonexistent_sensor(self, config_store):
        """Test querying for a sensor that doesn't exist"""
        (id, config) = config_store.get_config_for("ZZ:ZZ:ZZ:00:00:00")
        assert id == 0
        assert config == False

    def test_get_config_injection_attempt_quote_escape(self, config_store):
        """Test injection attempt with quote escaping"""
        # Attempt to inject additional JSONB fields
        malicious_input = 'A4:C1:38:00:00:01", "admin": "true'
        (id, config) = config_store.get_config_for(malicious_input)
        # Should not find any records because no sensor has this exact ID
        assert id == 0
        assert config == False

    def test_get_config_injection_attempt_json_manipulation(self, config_store):
        """Test injection attempt with JSON structure manipulation"""
        malicious_input = 'A4", "service_type": "OFF'
        (id, config) = config_store.get_config_for(malicious_input)
        # Should not find any records
        assert id == 0
        assert config == False

    def test_get_config_injection_attempt_wildcard(self, config_store):
        """Test injection attempt to match all records"""
        malicious_input = '", "sensor_id": "A4:C1:38:00:00:01'
        (id, config) = config_store.get_config_for(malicious_input)
        # Should not find any records
        assert id == 0
        assert config == False


class TestTempReadingStore:
    """Tests for TempReadingStore.get_latest_temperature_reading_for()"""

    def test_save_and_retrieve_temperature_reading(self, temp_store):
        """Test normal save and retrieve operation"""
        sensor_id = "A4:C1:38:00:00:02"
        reading = TemperatureReading(
            sensor_id=sensor_id,
            temp=21.5,
            humidity=45,
            battery=80
        )

        # Save reading
        temp_store.save_if_newer(reading, 60)

        # Retrieve latest reading
        retrieved = temp_store.get_latest_temperature_reading_for(sensor_id)
        assert retrieved is not None
        assert retrieved.sensor_id == sensor_id
        assert retrieved.temp == 21.5
        assert retrieved.humidity == 45

    def test_get_temperature_for_nonexistent_sensor(self, temp_store):
        """Test querying for a sensor that has no readings"""
        retrieved = temp_store.get_latest_temperature_reading_for("YY:YY:YY:00:00:00")
        assert retrieved is None

    def test_get_temperature_injection_attempt(self, temp_store):
        """Test injection attempt with additional JSONB fields"""
        malicious_input = 'A4:C1:38:00:00:02", "admin": "true'
        retrieved = temp_store.get_latest_temperature_reading_for(malicious_input)
        # Should not find any records because no sensor has this exact ID
        assert retrieved is None

    def test_get_temperature_injection_json_structure(self, temp_store):
        """Test injection attempt to manipulate JSON structure"""
        malicious_input = '", "temp": 0'
        retrieved = temp_store.get_latest_temperature_reading_for(malicious_input)
        assert retrieved is None


class TestZonePresenceStore:
    """Tests for ZonePresenceStore.get_latest_zone_presence_for()"""

    def test_save_and_retrieve_presence(self, presence_store):
        """Test normal save and retrieve operation"""
        sensor_id = "A4:C1:38:00:00:03"
        presence = ZonePresence(
            sensor_id=sensor_id,
            occupancy="true"
        )

        # Save presence
        presence_store.save_if_newer(presence, 60)

        # Retrieve latest presence
        retrieved = presence_store.get_latest_zone_presence_for(sensor_id)
        assert retrieved is not None
        assert retrieved.sensor_id == sensor_id
        assert retrieved.occupancy == "true"

    def test_get_presence_for_nonexistent_sensor(self, presence_store):
        """Test querying for a sensor that has no presence data"""
        retrieved = presence_store.get_latest_zone_presence_for("XX:XX:XX:00:00:00")
        assert retrieved is None

    def test_get_presence_injection_attempt(self, presence_store):
        """Test injection attempt with additional JSONB fields"""
        malicious_input = 'A4:C1:38:00:00:03", "admin": "true'
        retrieved = presence_store.get_latest_zone_presence_for(malicious_input)
        # Should not find any records
        assert retrieved is None


class TestMoerReadingStore:
    """Tests for MoerReadingStore JSONB query methods"""

    def test_save_and_retrieve_moer_reading(self, moer_store):
        """Test normal save and retrieve operation"""
        ba_id = "IESO_NORTH"
        reading = MoerReading(
            ba_id=ba_id,
            percent=45,
            srcdate=datetime.now()
        )

        # Save reading
        moer_store.save_if_newer(reading)

        # Retrieve latest reading
        retrieved = moer_store.select_latest_moer_reading(ba_id)
        assert retrieved is not None
        assert retrieved.ba_id == ba_id
        assert retrieved.percent == 45

    def test_get_moer_readings_for_period(self, moer_store):
        """Test retrieving multiple readings over a period"""
        ba_id = "TEST_BA"
        reading = MoerReading(
            ba_id=ba_id,
            percent=50,
            srcdate=datetime.now()
        )

        # Save reading
        moer_store.save_if_newer(reading)

        # Retrieve readings for last 5 days
        readings = moer_store.get_moer_readings_for(ba_id, 5)
        assert isinstance(readings, list)
        assert len(readings) > 0
        assert all(r.ba_id == ba_id for r in readings)

    def test_get_moer_for_nonexistent_ba(self, moer_store):
        """Test querying for a BA that doesn't exist"""
        retrieved = moer_store.select_latest_moer_reading("NONEXISTENT_BA")
        assert retrieved is None

    def test_get_moer_injection_attempt_select(self, moer_store):
        """Test injection attempt in select_latest_moer_reading"""
        malicious_input = 'IESO_NORTH", "admin": "true'
        retrieved = moer_store.select_latest_moer_reading(malicious_input)
        # Should not find any records
        assert retrieved is None

    def test_get_moer_injection_attempt_get_readings(self, moer_store):
        """Test injection attempt in get_moer_readings_for"""
        malicious_input = 'TEST_BA", "percent": 100'
        readings = moer_store.get_moer_readings_for(malicious_input, 5)
        # Should return empty list
        assert readings == []

    def test_get_moer_injection_attempt_json_escape(self, moer_store):
        """Test injection with JSON escape characters"""
        malicious_input = 'TEST\\"BA'
        retrieved = moer_store.select_latest_moer_reading(malicious_input)
        assert retrieved is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
