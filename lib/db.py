# -*- coding: utf-8 -*-
import enum

import pymysql

__all__ = ['Database', 'Mysql']


class Database(object):

    @property
    def config(self):
        """
            数据库配置
        :return:
        """
        raise NotImplementedError()

    @property
    def name(self):
        """
            数据库名
        :return:
        """
        raise NotImplementedError()

    def is_open(self):
        raise NotImplementedError()

    def open(self):
        raise NotImplementedError()

    def close(self):
        raise NotImplementedError()

    def query(self, sql):
        raise NotImplementedError()

    def execute(self, sql):
        raise NotImplementedError()

    def insert_id(self):
        raise NotImplementedError()

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.close()


class Mysql(Database):
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
    def config(self):
        return self._config

    @property
    def name(self):
        return self._config['db']

    def is_open(self):
        if not self._connection:
            return False
        return self._connection.open

    def open(self):
        self._connection = pymysql.connect(**self._config)
        if self.is_open():
            self._cursor = self._connection.cursor()
            return self

    def close(self):
        if self.is_open():
            self._cursor.close()
            self._connection.close()

    def set_db(self, str_db: str):
        if not str_db:
            return
        self.config['db'] = str_db
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
        return '<%s: %s:%s/%s>' % \
               (self.__class__.__name__, self._config['host'], self._config['port'], self._config['db'])


if __name__ == '__main__':
    pass
