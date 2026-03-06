# database class — based on the haiku cog's dbclass.py
# Uses psycopg + psycopg_pool for connection pooling to Postgres
#
# Unlike the haiku version, this is NOT a process-wide singleton.
# Each cog that copies this file can set its own DB_CC_NAME env var
# (or change the default below) without colliding with other cogs.
import os
import psycopg as pg
from psycopg_pool import ConnectionPool
from contextlib import contextmanager

# ---------- configurable per-cog ----------
_DEFAULT_DBNAME = "chodecoin"
_DBNAME_ENV_VAR = "DB_CC_NAME"        # override via env if desired
# ------------------------------------------


class DatabasePool:
    """Connection pool scoped to the chodecoin database.

    Uses a class-level pool so all db() instances in this cog share
    one pool, but it is completely independent of pools created by
    other cogs (e.g. the haiku cog's DatabasePool).
    """
    _pool = None

    @classmethod
    def initialize(cls):
        """Initialize the connection pool"""
        if cls._pool is None:
            host = os.getenv("DB_HOST", "postgres_container")
            dbname = os.getenv(_DBNAME_ENV_VAR, _DEFAULT_DBNAME)
            user = os.getenv("DB_USER", "redbot")
            password = os.getenv("DB_PASSWORD")
            port = os.getenv("DB_PORT", "5432")

            if not password:
                raise ValueError("DB_PASSWORD environment variable is required but not set")

            conninfo = f"host={host} dbname={dbname} user={user} password={password} port={port}"

            cls._pool = ConnectionPool(
                conninfo=conninfo,
                min_size=2,
                max_size=10,
                timeout=30,
                open=True,
            )

    @classmethod
    def close(cls):
        """Close the connection pool"""
        if cls._pool is not None:
            cls._pool.close()
            cls._pool = None

    @classmethod
    @contextmanager
    def get_connection(cls):
        """Get a connection from the pool"""
        if cls._pool is None:
            cls.initialize()

        conn = cls._pool.getconn()
        try:
            yield conn
        finally:
            cls._pool.putconn(conn)


class db:
    """Database wrapper class using connection pooling"""

    def __init__(self):
        self.pool = DatabasePool
        self.faulted = False

    def queryAll(self, queryString, params=None):
        """Run a SELECT returning all rows."""
        with self.pool.get_connection() as conn:
            with conn.cursor() as cur:
                if params:
                    cur.execute(queryString, params)
                else:
                    cur.execute(queryString)
                results = cur.fetchall()
            conn.commit()
            return results

    def querySingle(self, queryString, params=None):
        """Run a SELECT returning the first row."""
        with self.pool.get_connection() as conn:
            with conn.cursor() as cur:
                if params:
                    cur.execute(queryString, params)
                else:
                    cur.execute(queryString)
                result = cur.fetchone()
            conn.commit()
            return result

    def execute(self, queryString, params=None):
        """Run an INSERT/UPDATE/DELETE and commit."""
        with self.pool.get_connection() as conn:
            with conn.cursor() as cur:
                if params:
                    cur.execute(queryString, params)
                else:
                    cur.execute(queryString)
                conn.commit()

    def executeAndReturn(self, queryString, params=None):
        """Run an INSERT/UPDATE and return the result row."""
        with self.pool.get_connection() as conn:
            with conn.cursor() as cur:
                if params:
                    cur.execute(queryString, params)
                else:
                    cur.execute(queryString)
                conn.commit()
                result = cur.fetchone()
                return result