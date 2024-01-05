
CREATE TABLE IF NOT EXISTS public.zone_presence (
    id      serial primary key, 
    zone_presence  jsonb,
    presence_time timestamp with time zone not null default CURRENT_TIMESTAMP
);

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO zonemgr;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO zonemgr;
