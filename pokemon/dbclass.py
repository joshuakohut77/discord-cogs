# database class

import psycopg2 as pg


class db:
    def __init__(self):
        self.conn = pg.connect(
            host="192.168.5.10",
            dbname="pokemon_db",
            user="redbot",
            password="bfFLG9tUYPpW7272vzhX52",  # todo remove password from source control
            port=5432)

    def __del__(self):
        self.conn.close()

    def queryAll(self, queryString, params=None):
        """ takes a select query and runs it returning all rows. params is a sequence of values to pass into the queryString"""
        cur = self.conn.cursor()
        if params:
            cur.execute(queryString, (params))
        else:
            cur.execute(queryString)
        results = cur.fetchall()
        cur.close()
        return results

    def querySingle(self, queryString, params=None):
        """ takes a select query and runs it returning the first row. params is a sequence of values to pass into the queryString"""
        cur = self.conn.cursor()
        if params:
            cur.execute(queryString, (params))
        else:
            cur.execute(queryString)

        # If you ask for something that should be a single row,
        # anything more than a single row is an error.
        if cur.rowcount > 1:
            raise AssertionError('Expected 1, returned more than 1')

        result = cur.fetchone()
        cur.close()
        return result

    def execute(self, queryString, params=None):
        """ takes a update/insert statement, runs it, and committing if no errors. params is a sequence of values to pass into the queryString"""
        cur = self.conn.cursor()
        if params:
            cur.execute(queryString, (params))
        else:
            cur.execute(queryString)
        self.conn.commit()
        cur.close()
