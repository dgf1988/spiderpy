# coding: utf-8
import collections
import datetime
import functools

import lib.db 
import lib.sql

"""

    example:
        @table_name('country')
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

    def to_sql(self):
        items = ['`%s`' % self.name,
                 '%s(%s)' % (self.db_type, self.length)
                 if self.length > 0 else self.db_type,
                 'NULL' if self.nullable else 'NOT NULL']
        if self.auto_increment:
            items.append('AUTO_INCREMENT')
        elif self.current_timestamp or self.on_update:
            items.append('DEFAULT')
            if self.current_timestamp:
                items.append('CURRENT_TIMESTAMP')
            if self.on_update:
                items.append('ON UPDATE CURRENT_TIMESTAMP')
        elif not (not self.nullable and self.default is None):
            items.append('DEFAULT %s' % lib.sql.Value(self.default).to_sql())
        return ' '.join(items)

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

    def equal(self, value):
        return lib.sql.WhereEqual(self.name, value)

    def __eq__(self, other):
        return self.equal(other)

    def not_equal(self, value):
        return lib.sql.WhereNotEqual(self.name, value)

    def __ne__(self, other):
        return self.not_equal(other)

    def less(self, value):
        return lib.sql.WhereLess(self.name, value)

    def __lt__(self, other):
        return self.less(other)

    def less_equal(self, value):
        return lib.sql.WhereLessEqual(self.name, value)

    def __le__(self, other):
        return self.less_equal(other)

    def greater(self, value):
        return lib.sql.WhereGreater(self.name, value)

    def __gt__(self, other):
        return self.greater(other)

    def greater_equal(self, value):
        return lib.sql.WhereGreaterEqual(self.name, value)

    def __ge__(self, other):
        return self.greater_equal(other)

    def in_(self, *value):
        return lib.sql.WhereIn(self.name, *value)

    def not_in(self, *value):
        return lib.sql.WhereNotIn(self.name, *value)

    def between(self, left, right):
        return lib.sql.WhereBetween(self.name, left, right)

    def not_between(self, left, right):
        return lib.sql.WhereNotBetween(self.name, left, right)

    def like(self, exp):
        return lib.sql.WhereLike(self.name, exp)

    def not_like(self, exp):
        return lib.sql.WhereNotLike(self.name, exp)

    def asc(self):
        return lib.sql.OrderAsc(self.name)

    def desc(self):
        return lib.sql.OrderDesc(self.name)

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
            super().__init__(name, 'TIME', datetime.time, 0, default, nullable, False, False, on_update)


class YearField(Field):
    def __init__(self, name: str='', default=None, nullable=False, on_update=False):
            super().__init__(name, 'YEAR', datetime.datetime, 0, default, nullable, False, False, on_update)


class DatetimeField(Field):
    def __init__(self, name: str='', default=None, nullable=False, current_timestamp=False, on_update=False):
        super().__init__(name, 'DATETIME', datetime.datetime, 0, default, nullable, False, current_timestamp, on_update)


class TimestampField(Field):
    def __init__(self, name: str='', default=None, nullable=False, current_timestamp=False, on_update=False):
        super().__init__(name, 'TIMESTAMP', datetime.datetime, 0, default,
                         nullable, False, current_timestamp, on_update)


class Table(collections.OrderedDict):
    # 表名
    __table_name__ = ''
    # 主键
    __table_primarykey__ = []
    # 唯一键
    __table_uniques__ = dict()
    # 字段映射
    __table_mappings__ = collections.OrderedDict()
    # 字符集
    __table_collate__ = 'utf8_general_ci'
    # 数据库引擎
    __table_engine__ = 'InnoDB'

    def __init__(self, **kwargs):
        super().__init__()
        # 初始化字段
        for k, v in self.__table_mappings__.items():
            # 有指定值则使用指定值，没有则使用默认值
            self[k] = kwargs.get(k) if k in kwargs else v.default

    def __setitem__(self, key, value):
        if key in self.__table_mappings__:
            if isinstance(value, self.__table_mappings__[key].py_type) or value is None:
                return super().__setitem__(key, value)
            raise TypeError('the value %s type %s not isinstance %s'
                            % (value, type(value), self.__table_mappings__[key].py_type))
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

    @classmethod
    def set_table_uniques(cls, **kwargs):
        cls.__table_uniques__ = kwargs

    @classmethod
    def get_table_uniques(cls):
        return cls.__table_uniques__

    @classmethod
    def get_table_engine(cls):
        return cls.__table_engine__

    @classmethod
    def get_table_collate(cls):
        return cls.__table_collate__

    @classmethod
    def get_table_sql(cls):
        items = ['CREATE TABLE `%s`(\n' % cls.get_table_name(),
                 ',\n'.join(['\t%s' % field.to_sql() for field in cls.get_table_mappings().values()]),
                 ',\n\tPRIMARY KEY (`%s`)' % cls.get_table_primarykey()]
        uniques = cls.get_table_uniques()
        if uniques:
            items.append(',\n\t')
            items.append(',\n\t'.join(['UNIQUE INDEX `%s` (`%s`)' % (key, value) for key, value in uniques.items()]))
        items.append('\n)\n')
        items.append('COLLATE=\'%s\'\n' % cls.get_table_collate())
        items.append('ENGINE=%s\n;' % cls.get_table_engine())
        return ''.join(items)


class ForeignKey(Field):
    def __init__(self, name: str='', table=Table, default=None, nullable=False):
        if not issubclass(table, Table):
            raise TypeError()
        foreign = getattr(table, table.get_table_primarykey())
        super().__init__(name, foreign.db_type, table, foreign.length, default, nullable,
                         False, False, False)

    def allow_insert(self):
        return True

    def allow_update(self):
        return True


def table_name(name: str):
    def set_name(cls):
        cls.set_table_name(name)
        return cls
    return set_name


def table_primarykey(*key):
    def set_primarykey(cls):
        cls.set_table_primarykey(*key)
        return cls
    return set_primarykey


def table_columns(*columns):
    def set_columns(cls):
        mappings = collections.OrderedDict()
        for column in columns:
            if column in cls.__dict__ and isinstance(cls.__dict__[column], (Field, type)):
                if not cls.__dict__[column].name:
                    cls.__dict__[column].name = column
                mappings[column] = cls.__dict__[column]
        cls.set_table_mappings(mappings)
        return cls
    return set_columns


def table_uniques(**kwargs):
    def set_uniques(cls):
        cls.set_table_uniques(**kwargs)
        return cls
    return set_uniques


def dbset_tables(**kwargs):
    def set_tables(cls):
        cls.__tables__ = kwargs
        return cls
    return set_tables


class DbSet(object):
    __tables__ = dict()

    def __init__(self, db_obj: lib.db.Database=None):
        self.db = db_obj if db_obj is not None else lib.db.Database()

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

    def create_tables(self):
        exists = self.db.get_tables()
        for name, table in self.get_tables().items():
            if name in exists:
                continue
            TableSet(self.db, table).create_table()
        return self.db.get_tables()

    def __getattr__(self, item):
        tables = self.get_tables()
        if item in tables:
            return TableSet(self.db, tables[item])
        else:
            return super().__getattribute__(item)

    def __iter__(self):
        for key, table in self.get_tables().items():
            yield TableSet(self.db, table)

    @classmethod
    def get_tables(cls):
        return cls.__tables__


class TableSet(DbSet):
    def __init__(self, db_obj: lib.db.Database=None, table=Table):
        super().__init__(db_obj)
        self.table = table
        self.name = table.get_table_name()
        self.primarykey = table.get_table_primarykey()
        self.mappings = table.get_table_mappings()

    def create_table(self):
        self.db.execute(self.table.get_table_sql())
        return self.db.get_tables()

    def insert(self, obj: Table):
        if not obj.has_primarykey():
            toadd = collections.OrderedDict(
                    [(key, obj[key] if not isinstance(obj[key], Table) else obj[key].primarykey)
                     for key, field in self.mappings.items() if field.allow_insert() and key in obj.keys()])
            sqlitems = ['insert into %s' % self.name,
                        '('+','.join(toadd.keys())+')',
                        'values ('+','.join([lib.sql.Value(value).to_sql() for value in toadd.values()])+')']
            if self.db.execute(' '.join(sqlitems)):
                return self.db.insert_id()

    def update(self, primarykey, **kwargs):
        if primarykey:
            toupdate = collections.OrderedDict(
                    [(key, kwargs[key] if not isinstance(kwargs[key], Table) else kwargs[key].primarykey)
                     for key, field in self.mappings.items() if field.allow_update() and key in kwargs.keys()])
            sqlitems = ['update %s set' % self.name,
                        ','.join(['%s = %s' % (key, lib.sql.Value(value).to_sql()) for key, value in toupdate.items()]),
                        'where %s' % lib.sql.WhereEqual(self.primarykey, primarykey).to_sql()]
            return self.db.execute(' '.join(sqlitems))

    def delete(self, primary_key):
        if primary_key:
            return self.db.execute('delete from %s where %s = %s' % (self.name, self.primarykey, primary_key))

    def get(self, primary_key=None, **kwargs):
        if primary_key:
            if self.db.execute('select * from %s where %s = %s' % (self.name, self.primarykey, primary_key)):
                return self.table(**{k: v if not isinstance(self.mappings[k], ForeignKey) or v is None
                                     else TableSet(self.db, self.mappings[k].py_type).get(v)
                                     for k, v in self.db.fetch_all()[0].insert()})
        elif kwargs:
            whereequals = [lib.sql.WhereEqual(key, value if not isinstance(value, Table)
                           else value.primarykey)
                           for key, value in kwargs.items() if key in self.mappings.keys()]
            whereget = whereequals[0] if len(whereequals) == 1 else functools.reduce(lib.sql.And, whereequals)
            sqlget = 'select * from %s where %s' % (self.name, whereget.to_sql())
            if self.db.execute(sqlget):
                return self.table(**{k: v if not isinstance(self.mappings[k], ForeignKey) or v is None
                                     else TableSet(self.db, self.mappings[k].py_type).get(v)
                                     for k, v in self.db.fetch_all()[0].insert()})

    def find(self, **kwargs):
        if kwargs:
            if self.db.execute('select * from %s where %s' %
                               (self.name,
                                ' and '.join([lib.sql.WhereEqual(key, value if not isinstance(value, Table)
                                              else value.primarykey).to_sql()
                                              for key, value in kwargs.items() if key in self.mappings.keys()])
                                )
                               ):
                return [self.table(
                        **{k: v if not isinstance(self.mappings[k], ForeignKey) or v is None
                            else TableSet(self.db, self.mappings[k].py_type).get(v)
                           for k, v in one.insert()})
                        for one in self.db.fetch_all()]

    def list(self, take=10, skip=0):
        if self.db.execute('select * from %s order by %s limit %s,%s' % (self.name, self.primarykey, skip, take)):
            return [self.table(
                        **{k: v if not isinstance(self.mappings[k], ForeignKey) or v is None
                            else TableSet(self.db, self.mappings[k].py_type).get(v)
                           for k, v in one.insert()})
                    for one in self.db.fetch_all()]

    def __iter__(self):
        sqliter = 'select %s from %s order by %s' % (self.primarykey, self.name, self.primarykey)
        if self.db.execute(sqliter):
            toiterkeys = [each[self.primarykey] for each in self.db.fetch_all()]
            for eachkey in toiterkeys:
                yield self.get(eachkey)

    def count(self, **kwargs):
        sqlwhere = None
        if kwargs:
            whereequals = [lib.sql.WhereEqual(key, value if not isinstance(value, Table) else value.primarykey)
                           for key, value in kwargs.items() if key in self.mappings]
            sqlwhere = whereequals[0] if len(whereequals) == 1 else functools.reduce(lib.sql.And, whereequals)
        if sqlwhere:
            self.db.execute('select count(*) as num from %s where %s' % (self.name, sqlwhere.to_sql()))
        else:
            self.db.execute('select count(*) as num from %s' % self.name)
        return self.db.fetch_one()['num']

    def where(self, where):
        return QuerySet(self.db, self.table, where=where)

    def order(self, order):
        return QuerySet(self.db, self.table, order=order)

    def take(self, take):
        return QuerySet(self.db, self.table, take=take)

    def skip(self, skip):
        return QuerySet(self.db, self.table, skip=skip)


class QuerySet(object):
    def __init__(self, db_obj: lib.db.Database, table=Table, **kwargs):
        self.db = db_obj
        self.table = table
        self.primarykey = table.get_table_primarykey()
        self.mappings = table.get_table_mappings()
        self.query = lib.sql.From(table.get_table_name())
        if 'where' in kwargs:
            self.query.where(kwargs.get('where'))
        if 'order' in kwargs:
            self.query.order(kwargs.get('order'))
        if 'take' in kwargs:
            self.query.take(kwargs.get('take'))
        if 'skip' in kwargs:
            self.query.skip(kwargs.get('skip'))

    def where(self, where: lib.sql.Where):
        self.query.where(where)
        return self

    def and_where(self, where: lib.sql.Where):
        self.query.and_where(where)
        return self

    def or_where(self, where: lib.sql.Where):
        self.query.or_where(where)
        return self

    def order(self, *order):
        self.query.order(*order)
        return self

    def asc(self, asc: Field):
        self.query.order_asc(asc.name)
        return self

    def desc(self, desc: Field):
        self.query.order_desc(desc.name)
        return self

    def take(self, take: int):
        self.query.take(take)
        return self

    def skip(self, skip: int):
        self.query.skip(skip)
        return self

    def select(self, *select):
        tosql = self.query.select(*[each.name for each in select if isinstance(each, Field)])
        if self.db.execute(tosql.to_sql()):
            if select:
                return [collections.OrderedDict(
                     [(key, one[key] if one[key] is None or not isinstance(self.mappings[key], ForeignKey)
                      else TableSet(self.db, self.mappings[key].py_type).get(one[key]))
                      for key in self.mappings.keys() if key in one])
                    for one in self.db.fetch_all()
                ]
            else:
                return [self.table(
                        **{key: one[key] if one[key] is None or not isinstance(self.mappings[key], ForeignKey)
                            else TableSet(self.db, self.mappings[key].py_type).get(one[key])
                            for key in self.mappings.keys() if key in one})
                        for one in self.db.fetch_all()]
