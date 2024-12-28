# database class

import psycopg as pg




# The python equivalent of dotnets IDisposable pattern is their Context Managers
# https://book.pythontips.com/en/latest/context_managers.html
#
# dotnet:
# using (var db = new DBConnection()) { ... }
#
# python
# with database as db: ...
#
# The connection cursor object implements this kind of pattern
# https://www.psycopg.org/docs/cursor.html
#
# According to their best practices, creating lots of cursors should not be a problem:
# https://www.psycopg.org/docs/faq.html#best-practices

class db:
    def __init__(self, params=None):
        self.faulted = False
        # TODO: need a better way to pass in db configs through all the objects.
        # self.conn = pg.connect(
        #     host=(
        #         params and params.host) or "REDACTED_HOST",
        #     dbname=(params and params.dbname) or "pokemon_db",
        #     user=(params and params.user) or "redbot",
        #     # todo remove password from source control
        #     password=(params and params.password) or "REDACTED_PASSWORD",
        #     port=(params and params.port) or REDACTED_PORT)

        self.conn = pg.connect(
            host=(
                params and params.host) or "REDACTED_HOST",
            dbname=(params and params.dbname) or "pokemon_db",
            user=(params and params.user) or "redbot",
            # todo remove password from source control
            password=(params and params.password) or "REDACTED",
            port=(params and params.port) or 5432)

    def __del__(self):
        self.conn.close()

    def queryAll(self, queryString, params=None):
        """ takes a select query and runs it returning all rows. params is a sequence of values to pass into the queryString"""
        cur = self.conn.cursor()
        if params:
            cur.execute(queryString, (params) if type(params) is list else params)
        else:
            cur.execute(queryString)
        results = cur.fetchall()
        cur.close()
        return results

    def querySingle(self, queryString, params=None):
        """ takes a select query and runs it returning the first row. params is a sequence of values to pass into the queryString"""
        cur = self.conn.cursor()
        if params:
            cur.execute(queryString, (params) if type(params) is list else params)
        else:
            cur.execute(queryString)

        # # If you ask for something that should be a single row,
        # # anything more than a single row is an error.
        # if cur.rowcount > 1:
        #     raise AssertionError('Expected 1, returned more than 1')

        result = cur.fetchone()
        cur.close()
        return result

    # TODO: clean all these up, switch to the python `with` pattern
    def execute(self, queryString, params=None):
        """ takes a update/insert statement, runs it, and committing if no errors. params is a sequence of values to pass into the queryString"""
        cur = self.conn.cursor()
        if params:
            cur.execute(queryString, (params) if type(params) is list else params)
        else:
            cur.execute(queryString)
        self.conn.commit()
        cur.close()

    def executeAndReturn(self, queryString, params=None):
        """ takes a update/insert statement, runs it, and committing if no errors. params is a sequence of values to pass into the queryString"""
        cur = self.conn.cursor()
        if params:
            cur.execute(queryString, (params) if type(params) is list else params)
        else:
            cur.execute(queryString)
        self.conn.commit()
        result = cur.fetchone()
        cur.close()
        return result

    def executeWithoutCommit(self, queryString, params=None):
        """ takes a update/insert statement, runs it, and committing if no errors. params is a sequence of values to pass into the queryString"""
        with self.conn.cursor() as cur:
            if params:
                cur.execute(queryString, (params) if type(params) is list else params)
            else:
                cur.execute(queryString)

    def commit(self):
        self.conn.commit()
    
    def rollback(self):
        self.conn.rollback()