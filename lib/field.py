# coding: utf-8
from lib import db
from lib import sql

import collections
import functools


class Field(object):
    def __init__(self, name: str, db_type: str, py_type: type, length: int, default=None,
                 nullable: bool=False, auto_increment: bool=False, current_timestamp: bool=False, on_update: bool=False):
        # 字段名
        self.name = name
        # 数据库类型
        self.db_type = db_type
        # python类型
        self.py_type = py_type
        # 充许长度
        self.length = length
        # 默认值 - None表示没有默认值
        self.default = default
        # 可空？
        self.nullable = nullable
        # 自动 - 加1
        self.auto_increment = auto_increment
        # 自动 - 创建时间
        self.current_timestamp = current_timestamp
        # 自动 - 更新时间
        self.on_update = on_update

    def __str__(self):
        return 'Field(name: %s, db_type: %s, py_type: %s, length: %s, default: %s, nullable: %s, auto_increment: %s, current_timestamp: %s, on_update: %s)' % \
                (self.name, self.db_type, self.py_type, self.length, self.default, self.nullable, self.auto_increment, self.current_timestamp, self.on_update)


class IntField(Field):
    def __init__(self, name: str='', length: int=11, default=None, nullable=False, auto_increment=False):
        super().__init__(name, 'INT', int, length, default, nullable, auto_increment, False, False)


class CharField(Field):
    def __init__(self, name: str='', length: int=50, default=None, nullable=False):
        super().__init__(name, 'CHAR', str, length, default, nullable, False, False, False)


class VarcharField(Field):
    def __init__(self, name: str='', length: int=100, default=None, nullable=False):
        super().__init__(name, 'VARCHAR', str, length, default, nullable, False, False, False)


class TextField(Field):
    def __init__(self, name: str='', default=None, nullable=False):
        super().__init__(name, 'TEXT', str, 0, default, nullable, False, False, False)


class DateField(Field):
    def __init__(self, name: str='', default=None, nullable=False, on_update=False):
        super().__init__(name, 'DATE', str, 0, default, nullable, False, False, on_update)


class TimeField(Field):
    def __init__(self, name: str='', default=None, nullable=False, on_update=False):
            super().__init__(name, 'TIME', str, 0, default, nullable, False, False, on_update)


class YearField(Field):
    def __init__(self, name: str='', default=None, nullable=False, on_update=False):
            super().__init__(name, 'YEAR', str, 0, default, nullable, False, False, on_update)


class DatetimeField(Field):
    def __init__(self, name: str='', default=None, nullable=False, current_timestamp=False, on_update=False):
        super().__init__(name, 'DATETIME', str, 0, default, nullable, False, current_timestamp, on_update)


class TimestampField(Field):
    def __init__(self, name: str='', default=None, nullable=False, current_timestamp=False, on_update=False):
        super().__init__(name, 'TIMESTAMP', str, 0, default, nullable, False, current_timestamp, on_update)


class Table(object):
    def __init__(self, **kwargs):
        for k, v in self.table_mappings.items():
            setattr(self, k, kwargs.get(k) if k in kwargs else v.default)

    def __setattr__(self, key, value):
        if key in self.table_mappings:
            return super().__setattr__(key, value)
        else:
            raise KeyError('the key (%s) not in %s' % (key, self.table_mappings.keys()))

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, item):
        return getattr(self, item)

    def __str__(self):
        return '%s(' % self.table_name + \
               ', '.join([key+': '+getattr(self, key).__str__() for key in self.table_mappings.keys()]) + ')'

    def get_primarykey(self):
        return getattr(self, self.table_primarykey[0])

    def to_dict(self):
        todict = collections.OrderedDict()
        for key in self.table_mappings.keys():
            todict[key] = getattr(self, key)
        return todict


class DbSet(db.Database):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def table_set(self, table: type):
        setattr(self, table.table_name, TableSet(table, self))
        return getattr(self, table.table_name)


class TableSet(object):
    def __init__(self, table: type, db: db.Database=None):
        self.table = table
        self.name = table.table_name
        self.primarykey = table.table_primarykey[0]
        self.mappings = table.table_mappings
        self.db = db

    def get(self, primary_key):
        sql = 'select * from %s where %s = %s' % (self.name, self.primarykey, primary_key)
        if self.db.execute(sql):
            return self.db.fetch_one()

    def list(self):
        if self.db.execute('select * from %s order by id asc' % (self.name,)):
            return self.db.fetch_all()


def table_columns(*columns):
    def set_columns(cls: type):
        mappings = collections.OrderedDict()
        for column in columns:
            if column in cls.__dict__ and isinstance(cls.__dict__[column], Field):
                mappings[column] = cls.__dict__[column]
        cls.table_mappings = mappings
        return cls
    return set_columns


def table_primarykey(*keys):
    def set_primarykey(cls: type):
        setattr(cls, 'table_primarykey', keys)
        return cls
    return set_primarykey


def table_name(name: str):
    def set_name(cls: type):
        cls.table_name = name
        return cls
    return set_name


def database_tables(*tables):
    def set_table(cls: type):
        return cls
    return set_table


@table_name('country')
@table_primarykey('id')
@table_columns('id', 'name')
class Country(Table):
    id = IntField(auto_increment=True)
    name = CharField()


class Hoetom(DbSet):

    def __init__(self, user='root', passwd='guofeng001', db='hoetom'):
        super().__init__(user=user, passwd=passwd, db=db)
        self.table_set(Country)


def print_dict(kwargs: dict):
    for k, v in kwargs.items():
        print(k, ':\n\t', v)


if __name__ == '__main__':
    c = Country(id=3, name='中国')
    print(c)
    with Hoetom() as hoetom:
        c5 = Country(**hoetom.country.get(10))
        print(c5)
        list_c = hoetom.country.list()
        for c in list_c:
            print(Country(**c))