# coding: utf-8
from lib import db

import enum
import collections
import datetime
import functools

"""

    example:
        @table_name('country')
        @table_primarykey('id')
        @table_columns('id', 'name')
        class Country(Table):
            id = IntField(auto_increment=True)
            name = CharField()

"""


class Field(object):
    def __init__(self, name: str, db_type: str, py_type: type, length: int, default=None,
                 nullable: bool=False, auto_increment: bool=False,
                 current_timestamp: bool=False, on_update: bool=False):
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

    def allow_insert(self):
        """
        允许插入的字段
        :return:
        """
        return self.auto_increment is False and self.current_timestamp is False and self.on_update is False

    def allow_update(self):
        """
        允许更新的字段
        :return:
        """
        return self.allow_insert()

    def __str__(self):
        return 'Field(name: %s, db_type: %s, py_type: %s, length: %s, default: %s, ' \
               'nullable: %s, auto_increment: %s, current_timestamp: %s, on_update: %s)' % \
                (self.name, self.db_type, self.py_type, self.length, self.default,
                 self.nullable, self.auto_increment, self.current_timestamp, self.on_update)


class IntField(Field):
    def __init__(self, name: str='', length: int=11, default=None, nullable=False, auto_increment=False):
        super().__init__(name, 'INT', int, length, default, nullable, auto_increment, False, False)


class PrimaryKey(IntField):
    def __init__(self, name: str=''):
        super().__init__(name, auto_increment=True)


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
        super().__init__(name, 'DATE', datetime.date, 0, default, nullable, False, False, on_update)


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
        super().__init__(name, 'TIMESTAMP', datetime.datetime, 0, default, nullable, False, current_timestamp, on_update)


class Table(collections.OrderedDict):
    # 表名
    __table_name__ = ''
    # 主键
    __table_primarykey__ = []
    # 字段映射
    __table_mappings__ = collections.OrderedDict()

    def __init__(self, **kwargs):
        super().__init__()
        # 初始化字段
        for k, v in self.__table_mappings__.items():
            # 有指定值则使用指定值，没有则使用默认值
            self[k] = kwargs.get(k) if k in kwargs else v.default

    def __setattr__(self, key, value):
        self[key] = value

    def __getattr__(self, item):
        return self[item]

    def __setitem__(self, key, value):
        if key in self.__table_mappings__:
            if isinstance(value, self.__table_mappings__[key].py_type) or value is None:
                return super().__setitem__(key, value)
            raise TypeError('the value %s type %s not isinstance %s' % (value, type(value), self.__table_mappings__[key].py_type))
        else:
            raise KeyError('the key %s not in %s' % (key, self.__table_mappings__.keys()))

    @property
    def primarykey(self):
        # 主键取值
        return self[self.get_table_primarykey()]

    @primarykey.setter
    def primarykey(self, value):
        # 主键赋值
        self[self.get_table_primarykey()] = value

    def has_primarykey(self):
        # 主键是否有值
        return bool(self[self.get_table_primarykey()])

    @classmethod
    def get_table_name(cls):
        return cls.__table_name__

    @classmethod
    def set_table_name(cls, name: str):
        cls.__table_name__ = name

    @classmethod
    def get_table_primarykey(cls):
        if not cls.__table_primarykey__:
            cls.__table_primarykey__ = \
                    [key for key, value in cls.__table_mappings__.items() if isinstance(value, PrimaryKey)]
            if not cls.__table_primarykey__:
                raise ValueError('not exits primary key')
            return cls.get_table_primarykey()
        else:
            return cls.__table_primarykey__[0]

    @classmethod
    def set_table_primarykey(cls, *key):
        cls.__table_primarykey__ = key

    @classmethod
    def get_table_mappings(cls):
        return cls.__table_mappings__

    @classmethod
    def set_table_mappings(cls, mappings: collections.OrderedDict):
        cls.__table_mappings__ = mappings

    @staticmethod
    def value_to_sql(value):
        if value is None:
            return 'NULL'
        elif isinstance(value, (int, float, bool)):
            return value.__str__()
        else:
            return '"%s"' % value


def table_name(name: str):
    def set_name(cls: type):
        cls.set_table_name(name)
        return cls
    return set_name


def table_primarykey(*key):
    def set_primarykey(cls: type):
        cls.set_table_primarykey(*key)
        return cls
    return set_primarykey


def table_columns(*columns):
    def set_columns(cls: type):
        mappings = collections.OrderedDict()
        for column in columns:
            if column in cls.__dict__ and isinstance(cls.__dict__[column], (Field, type)):
                mappings[column] = cls.__dict__[column]
        cls.set_table_mappings(mappings)
        return cls
    return set_columns


def dbset_tables(**kwargs):
    def set_tables(cls):
        cls.__tables__ = kwargs
        return cls
    return set_tables


class ForeignKey(Field):
    def __init__(self, name: str='', table: type=Table, default=None, nullable=False):
        if not issubclass(table, Table):
            raise TypeError()
        foreign = getattr(table, table.get_table_primarykey())
        super().__init__(name, foreign.db_type, table, foreign.length, default, nullable,
                         foreign.auto_increment, foreign.current_timestamp, foreign.on_update)

    def allow_insert(self):
        return True

    def allow_update(self):
        return True


class DbSet(object):
    def __init__(self, db_obj: db.Database=None):
        self.db = db_obj if db_obj is not None else db.Database()

    def open(self):
        self.db.open()
        return self

    def __enter__(self):
        return self.open()

    def close(self):
        self.db.close()

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.close()

    def table_set(self, table):
        if isinstance(table, type) and issubclass(table, Table):
            return TableSet(self.db, table)
        return None

    def __getattr__(self, item):
        if item in self.__tables__:
            return TableSet(self.db, self.__tables__[item])
        else:
            return super().__getattribute__(item)


class TableSet(DbSet):
    def __init__(self, db_obj: db.Database=None, table: type=Table):
        super().__init__(db_obj)
        if issubclass(table, Table):
            self.table = table
            self.name = table.get_table_name()
            self.primarykey = table.get_table_primarykey()
            self.mappings = table.get_table_mappings()
        else:
            raise TypeError()

    def insert(self, obj: Table=None):
        if not obj.has_primarykey():
            toadd = collections.OrderedDict(
                    [(key, obj[key]
                     if not isinstance(self.mappings[key], ForeignKey) or obj[key] is None
                     else obj[key].primarykey
                     if isinstance(obj[key], Table) and obj[key].has_primarykey()
                     else TableSet(self.db, self.mappings[key].py_type).insert(obj[key]))
                     for key, field in self.mappings.items()
                     if field.allow_insert() and key in obj.keys()])
            sqlitems = ['insert into %s' % self.name,
                        '('+','.join(toadd.keys())+')',
                        'values ('+','.join([Table.value_to_sql(value) for value in toadd.values()])+')']
            sql = ' '.join(sqlitems)
            if self.db.execute(sql):
                return self.db.insert_id()

    def update(self, obj: Table):
        if obj.has_primarykey():
            toupdate = collections.OrderedDict(
                    [(key, obj[key] if not isinstance(self.mappings[key], ForeignKey) or obj[key] is None
                      else obj[key].primarykey)
                     for key, field in self.mappings.items()
                     if field.allow_update() and key in obj.keys()])
            sqlitems = [
                'update %s set ' % self.name,
                ','.join(['%s = %s' % (key, Table.value_to_sql(value)) for key, value in toupdate.items()]),
                'where %s = %s' % (self.primarykey, obj.primarykey)
            ]
            sql = ' '.join(sqlitems)
            return self.db.execute(sql)

    def delete(self, primary_key):
        if primary_key:
            return self.db.execute('delete from %s where %s = %s' % (self.name, self.primarykey, primary_key))

    def get(self, primary_key):
        if primary_key:
            if self.db.execute('select * from %s where %s = %s' % (self.name, self.primarykey, primary_key)):
                return self.table(**{k: v if not isinstance(self.mappings[k], ForeignKey) or v is None
                                     else TableSet(self.db, self.mappings[k].py_type).get(v)
                                     for k, v in self.db.fetch_one().items()})

    def find(self, **kwargs):
        if kwargs:
            if self.db.execute('select * from %s where %s' %
                               (self.name,
                                ' and '.join(['%s = %s' % (key, Table.value_to_sql(value)) if value is not None
                                              else '%s IS NULL' % key
                                              for key, value in kwargs.items()])
                                )
                               ):
                return [self.table(
                        **{k: v if not isinstance(self.mappings[k], ForeignKey) or v is None
                            else TableSet(self.db, self.mappings[k].py_type).get(v)
                           for k, v in one.items()})
                        for one in self.db.fetch_all()]

    def list(self, skip=0, take=10):
        if self.db.execute('select * from %s limit %s,%s' % (self.name, skip, take)):
            return [self.table(
                        **{k: v if not isinstance(self.mappings[k], ForeignKey) or v is None
                            else TableSet(self.db, self.mappings[k].py_type).get(v)
                           for k, v in one.items()})
                    for one in self.db.fetch_all()]

    def count(self):
        if self.db.execute('select count(*) as num from %s' % self.name):
            return self.db.fetch_one()['num']

    def where(self, where):
        return QuerySet(self.db, self.table, where=where)

    def order(self, order):
        return QuerySet(self.db, self.table, order=order)

    def take(self, take):
        return QuerySet(self.db, self.table, take=take)

    def skip(self, skip):
        return QuerySet(self.db, self.table, skip=skip)


class QUERY(enum.Enum):
    INSERT = 1
    DELETE = 2
    UPDATE = 3
    SELECT = 4


class Query(dict):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        pass

    def __setattr__(self, key, value):
        self[key] = value

    def __getattr__(self, key):
        return self[key]

    def to_sql(self):
        pass


class QuerySet(object):
    def __init__(self, db_obj: db.Database, table: type, **kwargs):
        self.db = db_obj
        self.table = table
        self.query = Query(**kwargs)
        pass

    def where(self, where):
        self.query.where = where
        return self

    def and_where(self, where):
        if 'where' in self.query:
            self.query.where.and_where(where)
        else:
            return self.where(where)
        return self

    def or_where(self, where):
        if 'where' in self.query:
            self.query.where.or_where(where)
        else:
            return self.where(where)
        return self

    def order(self, order):
        self.query.order = [order]
        return self

    def select(self,):
        pass


@table_name('country')
@table_columns('id', 'name')
class Country(Table):
    id = PrimaryKey()
    name = CharField()


@table_name('rank')
@table_columns('id', 'rank')
class Rank(Table):
    id = PrimaryKey()
    rank = CharField()


@table_name('player')
@table_columns('id', 'hoetomid', 'p_name', 'p_sex', 'p_nat', 'p_rank', 'p_birth')
class Player(Table):
    id = PrimaryKey()
    hoetomid = IntField()
    p_name = CharField()
    p_sex = IntField()
    p_nat = ForeignKey(table=Country)
    p_rank = ForeignKey(table=Rank)
    p_birth = DateField()


@table_name('playerid')
@table_columns('id', 'playerid', 'posted')
class Playerid(Table):
    id = PrimaryKey()
    playerid = IntField()
    posted = TimestampField(current_timestamp=True)


@dbset_tables(player=Player, playerid=Playerid, country=Country, rank=Rank)
class Hoetom(DbSet):
    def __init__(self):
        super().__init__(db.Database(user='root', passwd='guofeng001', db='hoetom'))


if __name__ == '__main__':
    with Hoetom() as hoetom:
        print(hoetom.playerid.count())
        print(hoetom.country.count())
        print(hoetom.table_set(Player).count())
        for playerid in hoetom.table_set(Player).list():
            print(playerid)
        hoetom.db.execute('select count(*) as num from html')
        num = hoetom.db.fetch_one()['num']
        print(num)



