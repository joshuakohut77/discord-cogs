# database class
import os
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
            # Build connection string from environment variables
            host = os.getenv("DB_HOST", "postgres_container")
            dbname = os.getenv("DB_NAME", "discord")
            user = os.getenv("DB_USER", "redbot")
            password = os.getenv("DB_PASSWORD")
            port = os.getenv("DB_PORT", "5432")
            
            # Validate that password is set
            if not password:
                raise ValueError("DB_PASSWORD environment variable is required but not set")
            
            conninfo = f"host={host} dbname={dbname} user={user} password={password} port={port}"
            
            self._pool = ConnectionPool(
                conninfo=conninfo,
                min_size=2,
                max_size=10,
                timeout=30,
                open=True
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