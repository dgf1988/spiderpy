# -*- coding: utf-8 -*-
import enum

import pymysql

__all__ = ['Mysql']


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
        return self.info['db']

    @name.setter
    def name(self, name: str):
        self.info['db'] = name

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

    def set_db(self, str_db: str):
        self.info['db'] = str_db
        return self.connection.select_db(str_db)

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

    def get_tables(self, db_name: str=''):
        if not db_name:
            db_name = self.name
        self.execute('show tables from %s' % db_name)
        return [table['Tables_in_%s' % db_name] for table in self.fetch_all()]


class Mysql(object):
    def __init__(self, user='', passwd='', db='', host='localhost', port=3306, charset='utf8', autocommit=True):
        self._config = dict(
            user=user,
            passwd=passwd,
            db=db,
            host=host,
            port=port,
            autocommit=autocommit,
            charset=charset,
            cursorclass=pymysql.cursors.DictCursor
        )
        self._connection = None
        self._cursor = None

    @property
    def name(self):
        return self._config['db']

    @name.setter
    def name(self, name: str):
        self._config['db'] = name

    def is_open(self):
        if not self._connection:
            return False
        return self._connection.open

    def __bool__(self):
        return self.is_open()

    def open(self):
        self._connection = pymysql.connect(**self._config)
        if self.is_open():
            self._cursor = self._connection.cursor()
            return self

    def __enter__(self):
        return self.open()

    def close(self):
        if self.is_open():
            self._cursor.close()
            self._connection.close()

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.close()

    def set_db(self, str_db: str):
        self._config['db'] = str_db
        return self._connection.select_db(str_db)

    def commit(self):
        return self._connection.commit()

    def roll_back(self):
        return self._connection.rollback()

    def execute(self, str_sql, args=None):
        return self._cursor.execute(str_sql, args)

    def execute_many(self, str_sql, args):
        return self._cursor.executemany(str_sql, args)

    def fetch_one(self):
        return self._cursor.fetchone()

    def fetch_many(self, size=None):
        return self._cursor.fetchmany(size)

    def fetch_all(self):
        return self._cursor.fetchall()

    def query(self, str_sql):
        if self.execute(str_sql):
            return self.fetch_all()

    def insert_id(self):
        return self._cursor.lastrowid

    def get_tables(self, db_name: str=''):
        if not db_name:
            db_name = self.name
        self.execute('show tables from %s' % db_name)
        return [table['Tables_in_%s' % db_name] for table in self.fetch_all()]

    def __str__(self):
        return '<%s: %s:%s/%s>' % (self.__class__.__name__, self._config['host'], self._config['port'], self._config['db'])


class DB(enum.Enum):
    MySql = Mysql, 'mysql database'

    def __new__(cls, database, description):
        obj = object.__new__(cls)
        obj._value_ = obj
        obj.db = database
        obj.description = description
        return obj

    def __call__(self, *args, **kwargs):
        return self.db(*args, **kwargs)


class Client(object):
    def __init__(self, database=Mysql, user='', password='', host='localhost', port=3306, db_name='', charset='utf-8'):
        pass

    def open(self):
        pass

    def is_open(self):
        pass

    def close(self):
        pass

    def select_db(self, str_db):
        pass

    def get_tables(self, str_db=''):
        pass

    def query(self, str_sql):
        pass

    def execute(self, str_sql):
        pass

    def insert_id(self):
        pass

    def __str__(self):
        pass


if __name__ == '__main__':
    pass
