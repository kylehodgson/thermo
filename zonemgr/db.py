from psycopg2 import pool

class ZoneManagerDB:
    def __init__(self) -> None:
        self.dbPool=pool.ThreadedConnectionPool(1,5) # reading values from environment
    
    def __enter__(self):
        self.conn= self.dbPool.getconn()
        return self.conn

    def __exit__(self,two,three,four):
        self.dbPool.putconn(self.conn)

    def shutDown(self):
        self.dbPool.closeall()