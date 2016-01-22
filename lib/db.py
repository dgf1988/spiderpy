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


def connect(**kwargs):
    return Database(**kwargs).open()
