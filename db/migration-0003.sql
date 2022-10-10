
CREATE TABLE IF NOT EXISTS public.moer_readings (
    id      serial primary key, 
    reading  jsonb,
    reading_time timestamp with time zone not null default CURRENT_TIMESTAMP
);