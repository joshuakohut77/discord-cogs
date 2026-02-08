# database class

import psycopg as pg
from psycopg_pool import ConnectionPool
from contextlib import contextmanager


class DatabasePool:
    """Singleton connection pool for the database"""
    _instance = None
    _pool = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabasePool, cls).__new__(cls)
        return cls._instance
    
    def initialize(self):
        """Initialize the connection pool"""
        if self._pool is None:
            self._pool = ConnectionPool(
                conninfo="host=postgres_container dbname=discord user=redbot password=REDACTED port=5432",
                min_size=2,
                max_size=10,
                timeout=30
            )
    
    def close(self):
        """Close the connection pool"""
        if self._pool is not None:
            self._pool.close()
            self._pool = None
    
    @contextmanager
    def get_connection(self):
        """Get a connection from the pool"""
        if self._pool is None:
            self.initialize()
        
        conn = self._pool.getconn()
        try:
            yield conn
        finally:
            self._pool.putconn(conn)


class db:
    """Database wrapper class using connection pooling"""
    
    def __init__(self):
        self.pool = DatabasePool()
        self.faulted = False

    def queryAll(self, queryString, params=None):
        """Takes a select query and runs it returning all rows. params is a dict of values to pass into the queryString"""
        with self.pool.get_connection() as conn:
            with conn.cursor() as cur:
                if params:
                    cur.execute(queryString, params)
                else:
                    cur.execute(queryString)
                results = cur.fetchall()
            conn.commit()  # Commit even for selects to clear transaction state
            return results

    def querySingle(self, queryString, params=None):
        """Takes a select query and runs it returning the first row. params is a dict of values to pass into the queryString"""
        with self.pool.get_connection() as conn:
            with conn.cursor() as cur:
                if params:
                    cur.execute(queryString, params)
                else:
                    cur.execute(queryString)
                result = cur.fetchone()
            conn.commit()  # Commit even for selects to clear transaction state
            return result

    def execute(self, queryString, params=None):
        """Takes a update/insert statement, runs it, and commits if no errors. params is a dict of values to pass into the queryString"""
        with self.pool.get_connection() as conn:
            with conn.cursor() as cur:
                if params:
                    cur.execute(queryString, params)
                else:
                    cur.execute(queryString)
                conn.commit()

    def executeAndReturn(self, queryString, params=None):
        """Takes a update/insert statement, runs it, commits if no errors, and returns result. params is a dict of values to pass into the queryString"""
        with self.pool.get_connection() as conn:
            with conn.cursor() as cur:
                if params:
                    cur.execute(queryString, params)
                else:
                    cur.execute(queryString)
                conn.commit()
                result = cur.fetchone()
                return result

    def executeWithoutCommit(self, queryString, params=None):
        """Takes a update/insert statement and runs it without committing. params is a dict of values to pass into the queryString"""
        with self.pool.get_connection() as conn:
            with conn.cursor() as cur:
                if params:
                    cur.execute(queryString, params)
                else:
                    cur.execute(queryString)

    def commit(self):
        """Note: This method is deprecated when using connection pooling. Each execute() commits automatically."""
        pass
    
    def rollback(self):
        """Note: Rollback should be handled at the connection level when using pooling"""
        pass