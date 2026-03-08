# ---------------------------------------------------------------
# The Vault — Database connection pool
# ---------------------------------------------------------------
# Shares the same Postgres instance as ChodeCoin.
# By default uses the same database (DB_CC_NAME env var) since
# the card tables use the vault_ prefix and the systems
# are related. Override with DB_VAULT_NAME if you want separation.
#
# Uses its own pool class so it's fully independent of ChodeCoin's
# pool lifecycle — either cog can load/unload without affecting
# the other.
# ---------------------------------------------------------------
import os
import psycopg as pg
from psycopg_pool import ConnectionPool
from contextlib import contextmanager

_DEFAULT_DBNAME = "chodecoin"
_DBNAME_ENV_VAR = "DB_VAULT_NAME"  # falls back to DB_CC_NAME, then default


class VaultDatabasePool:
    """Connection pool scoped to The Vault cog."""

    _pool = None

    @classmethod
    def initialize(cls):
        if cls._pool is None:
            host = os.getenv("DB_HOST", "postgres_container")
            dbname = os.getenv(_DBNAME_ENV_VAR) or os.getenv("DB_CC_NAME", _DEFAULT_DBNAME)
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
        if cls._pool is not None:
            cls._pool.close()
            cls._pool = None

    @classmethod
    @contextmanager
    def get_connection(cls):
        if cls._pool is None:
            cls.initialize()

        conn = cls._pool.getconn()
        try:
            yield conn
        finally:
            cls._pool.putconn(conn)


class db:
    """Database wrapper using The Vault's connection pool."""

    def __init__(self):
        self.pool = VaultDatabasePool

    def queryAll(self, queryString, params=None):
        with self.pool.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(queryString, params or {})
                results = cur.fetchall()
            conn.commit()
            return results

    def querySingle(self, queryString, params=None):
        with self.pool.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(queryString, params or {})
                result = cur.fetchone()
            conn.commit()
            return result

    def execute(self, queryString, params=None):
        with self.pool.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(queryString, params or {})
                conn.commit()

    def executeAndReturn(self, queryString, params=None):
        with self.pool.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(queryString, params or {})
                conn.commit()
                result = cur.fetchone()
                return result