# -*- coding: utf-8 -*-
import pymysql


class Database(object):
    def __init__(self, user='', passwd='', db='', host='localhost', port=3306, charset='utf8', autocommit=True):
        self.info = dict(
            user=user,
            passwd=passwd,
            db=db,
            host=host,
            port=port,
            autocommit=autocommit,
            charset=charset,
            cursorclass=pymysql.cursors.DictCursor
        )
        self.connection = None
        self.cursor = None
        pass

    @property
    def name(self):
        return self.info.db

    @name.setter
    def name(self, name: str):
        self.info.db = name

    def is_open(self):
        return self.connection.open

    def open(self):
        self.connection = pymysql.connect(**self.info)
        if self.is_open():
            self.cursor = self.connection.cursor()
            return self

    def __enter__(self):
        return self.open()

    def close(self):
        if self.is_open():
            self.cursor.close()
            self.connection.close()

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.close()

    def set_db(self, db: str):
        self.info.db = db
        return self.connection.select_db(db)

    def commit(self):
        return self.connection.commit()

    def roll_back(self):
        return self.connection.rollback()

    def execute(self, query, args=None):
        return self.cursor.execute(query, args)

    def execute_many(self, query, args):
        return self.cursor.executemany(query, args)

    def fetch_one(self):
        return self.cursor.fetchone()

    def fetch_many(self, size=None):
        return self.cursor.fetchmany(size)

    def fetch_all(self):
        return self.cursor.fetchall()

    def insert_id(self):
        return self.cursor.lastrowid

    def get_tables(self, db: str=''):
        if db:
            self.execute('show tables from %s' % db)
        else:
            self.execute('show tables')
        return self.fetch_all()


class DB(object):
    def __init__(self, user='', passwd='', db='', host='localhost', port=3306, charset='utf8', autocommit=True):
        self.__info__ = dict(
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

    def open(self):
        self._conn = pymysql.connect(**self.__info__)
        if self._conn.open:
            self._cursor = self._conn.cursor()
        return self

    def set_db(self, db: str):
        self.__info__['db'] = db
        return self._conn.select_db(db)

    def get_tables(self, db=''):
        if db:
            self.execute('show tables from %s' % db)
        else:
            self.execute('show tables')
        return self.fetchall()

    def exist_table(self, table: str, db=''):
        if not table:
            raise ValueError('not set table name')
        if not db:
            db = self.__info__['db']
        if not db:
            raise ValueError('not select db')
        tables = self.get_tables(db)
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


if __name__ == '__main__':
    with Database(user='root', passwd='guofeng001', db='hoetom') as db:
        htmls = db.execute('select * from html order by id desc limit 100, 100')
        if htmls:
            htmls = db.fetch_all()
            for html in htmls:
                print(type(html['update_at']))