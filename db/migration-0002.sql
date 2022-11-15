CREATE TABLE IF NOT EXISTS public.plug_configurations (
    id      serial primary key, 
    config  jsonb
);

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO zonemgr;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO zonemgr;
