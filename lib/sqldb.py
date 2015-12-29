from lib.db import DB
from lib.sql import *
from functools import reduce
import logging


class SqlDB(object):
    def __init__(self, user='', passwd='', db='', host='localhost', port=3306, charset='utf8'):
        self.__db = DB(user=user, passwd=passwd, db=db, host=host, port=port, charset=charset)
        self.__sql = Sql()
        pass

    def execute(self, sql: str):
        return self.__db.execute(sql)

    def fetchone(self):
        return self.__db.fetchone()

    def fetchmany(self, many: int):
        return self.__db.fetchmany(many)

    def fetchall(self):
        return self.__db.fetchall()

    def rollback(self):
        return self.__db.rollback()

    def commit(self):
        return self.__db.commit()

    def insertid(self):
        return self.__db.lastid()

    def lastid(self):
        return self.__db.lastid()

    def db(self, db: str):
        self.__db.db(db)
        return self

    def table(self, table: str):
        self.__sql.table(table)
        return self

    def tables(self, dbname=''):
        return self.__db.tables(dbname)

    def exist_table(self, tablename):
        return self.__db.exist_table(tablename)

    def set(self, **kwargs):
        self.__sql.set(**kwargs)
        return self

    def where(self, *wherecase, **kwargs):
        self.__sql.where(*wherecase, **kwargs)
        return self

    def order(self, *order, **kwargs):
        self.__sql.order(*order, **kwargs)
        return self

    def limit(self, length: int, skip=0):
        self.__sql.limit(length, skip)
        return self

    def select(self, *select):
        sql = self.__sql.select(*select).to_str()
        self.__sql.clear()
        if self.execute(sql):
            return self.fetchall()

    def insert(self):
        sql = self.__sql.insert().to_str()
        self.__sql.clear()
        if self.execute(sql):
            self.commit()
            return self.insertid()

    def delete(self):
        sql = self.__sql.delete().to_str()
        self.__sql.clear()
        n = self.execute(sql)
        if n:
            self.commit()
            return n

    def update(self):
        sql = self.__sql.update().to_str()
        self.__sql.clear()
        n = self.execute(sql)
        if n:
            self.commit()
            return n

    def open(self):
        self.__db.open()
        return self

    def close(self):
        self.__db.close()

    def __enter__(self):
        return self.open()

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.close()


class ObjectDB(object):
    Sql_CreateTable = """
    """
    # 需要设置
    Table = ''
    # 需要设置
    DataCols = ('',)

    def __init__(self, id=0):
        self.id = id

    # 需要设置
    def to_dict(self):
        return dict(id=self.id)

    # 需要设置
    def __str__(self):
        return str(self.to_json())

    # 可选设置
    def __eq__(self, other):
        if not isinstance(other, ObjectDB):
            return False
        return self.to_dict() == other.to_dict()

    # 可选设置
    def __bool__(self):
        return bool(self.to_data())

    def to_str(self):
        return str(self)

    def to_json(self):
        json = dict()
        for k, v in self.to_dict().items():
            if isinstance(v, (int, str, bool)):
                json[k] = v
            else:
                json[k] = str(v)
        return json

    def to_data(self):
        data = dict()
        for k, v in self.to_dict().items():
            if k not in self.DataCols:
                continue
            if v:
                data[k] = v
        return data

    def insert(self, sqldb: SqlDB):
        if self.id > 0:
            return 0
        insertid = sqldb.table(self.Table).set(**self.to_data()).insert()
        if insertid:
            self.id = insertid
            return self.id

    @classmethod
    def insert_many(cls, sqldb: SqlDB, *many_object):
        list_id = []
        for each in many_object:
            if not isinstance(each, cls):
                continue
            list_id.append(each.insert(sqldb))
        return list_id

    def update(self, sqldb: SqlDB):
        if self.id <= 0:
            return 0
        return sqldb.table(self.Table).set(**self.to_data()).where(id=self.id).update()

    @classmethod
    def update_many(cls, sqldb: SqlDB, *many_object):
        num_row = 0
        for each in many_object:
            if not isinstance(each, cls):
                continue
            num_row += each.update(sqldb)
        return num_row

    def save(self, sqldb: SqlDB):
        insertid = self.insert(sqldb)
        if not insertid:
            return self.update(sqldb)

    def remove(self, sqldb: SqlDB):
        data = self.to_data()
        if len(data) == 0:
            return 0
        return self.delete(sqldb, **data)

    @classmethod
    def delete(cls, sqldb: SqlDB, **kwargs):
        if len(kwargs) <= 0:
            return 0
        return sqldb.table(cls.Table).where(**kwargs).delete()

    # 可选定义
    @classmethod
    def from_dbget(cls, sqldb: SqlDB, db_get: dict):
        return cls(**db_get)

    @classmethod
    def get(cls, sqldb: SqlDB, id: int):
        get = sqldb.table(cls.Table).where(id=id).select()
        if get:
            return cls.from_dbget(sqldb, get[0])

    @classmethod
    def find(cls, sqldb: SqlDB, **kwargs):
        find_get = sqldb.table(cls.Table).where(**kwargs).select()
        if find_get:
            return [cls.from_dbget(sqldb, each) for each in find_get]

    @classmethod
    def list(cls, sqldb: SqlDB, top=0, skip=0):
        list_get = sqldb.table(cls.Table).limit(top, skip).select()
        if list_get:
            return [cls.from_dbget(sqldb, each) for each in list_get]

    @classmethod
    def select(cls, sqldb: SqlDB, **kwargs):
        return sqldb.table(cls.Table).where(**kwargs).select()

    @classmethod
    def count(cls, sqldb: SqlDB, **kwargs):
        return sqldb.table(cls.Table).where(**kwargs).select('count(id) as num')[0]['num']

    @classmethod
    def create_table(cls, sqldb: SqlDB):
        if not sqldb.exist_table(cls.Table):
            return sqldb.execute(cls.Sql_CreateTable)
