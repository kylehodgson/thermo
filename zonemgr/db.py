from psycopg2 import pool

import logging
log = logging.getLogger(__name__)

class ZoneManagerDB:
    def __init__(self) -> None:
        self.dbPool=pool.ThreadedConnectionPool(1,5) # reading values from environment
    
    def __enter__(self):
        self.conn= self.dbPool.getconn()
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.dbPool.putconn(self.conn)

    def shutDown(self):
        self.dbPool.closeall()