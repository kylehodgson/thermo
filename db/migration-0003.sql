
CREATE TABLE IF NOT EXISTS public.moer_readings (
    id      serial primary key, 
    reading  jsonb,
    reading_time timestamp with time zone not null default CURRENT_TIMESTAMP
);

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO zonemgr;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO zonemgr;
