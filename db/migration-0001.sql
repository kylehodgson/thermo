GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO zonemgr;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO zonemgr;

CREATE TABLE IF NOT EXISTS public.sensor_configurations (
    id      serial primary key, 
    config  jsonb
);

CREATE TABLE IF NOT EXISTS public.temperature_readings (
    id      serial primary key, 
    reading  jsonb,
    reading_time timestamp with time zone not null default CURRENT_TIMESTAMP
);