CREATE TABLE IF NOT EXISTS public.sensor_configurations (
    id      serial primary key, 
    config  jsonb
);

CREATE TABLE IF NOT EXISTS public.temperature_readings (
    id      serial primary key, 
    reading  jsonb
);

