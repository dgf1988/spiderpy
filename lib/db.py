# -*- coding: utf-8 -*-
import pymysql


class DB(object):
    def __init__(self, user='', passwd='', db='', host='localhost', port=3306, charset='utf8', autocommit=True):
        if not user or not passwd:
            raise ValueError
        self.__args__ = dict(
            user=user,
            passwd=passwd,
            db=db,
            host=host,
            port=port,
            autocommit=autocommit,
            charset=charset,
            cursorclass=pymysql.cursors.DictCursor
        )
        self._conn = None
        self._cursor = None

    def __str__(self):
        return self.__args__.__str__()

    def open(self):
        self._conn = pymysql.connect(**self.__args__)
        if self._conn.open:
            self._cursor = self._conn.cursor()
        return self

    def db(self, db: str):
        self.__args__['db'] = db
        return self._conn.select_db(db)

    def tables(self, db=''):
        if db:
            self.execute('show tables from %s' % db)
        else:
            self.execute('show tables')
        return self.fetchall()

    def exist_table(self, table: str, db=''):
        if not table:
            raise ValueError('not set table name')
        if not db:
            db = self.__args__['db']
        if not db:
            raise ValueError('not select db')
        tables = self.tables(db)
        for each in tables:
            for k, v in each.items():
                if v == table:
                    return True
        return False

    def execute(self, str_sql):
        return self._cursor.execute(str_sql)

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    def fetchmany(self, many=0):
        return self._cursor.fetchmany(size=many)

    def rollback(self):
        return self._conn.rollback()

    def commit(self):
        return self._conn.commit()

    def lastid(self):
        return self._cursor.lastrowid

    def insertid(self):
        return self._cursor.lastrowid

    def close(self):
        if self._cursor:
            self._cursor.close()
        if self._conn.open:
            self._conn.close()

    def __enter__(self):
        return self.open()

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.close()

