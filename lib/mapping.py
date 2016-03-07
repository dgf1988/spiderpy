# coding: utf-8
import enum
import datetime
import collections

import lib.sql


__all__ = ['IntField', 'AutoIntField',
           'CharField', 'VarcharField', 'TextField',
           'DateField', 'TimeField', 'YearField', 'DatetimeField', 'TimestampField',
           'COLLATE', 'ENGINE', 'MAPPING',
           'Table', 'table', 'TableSet', 'Db']


def _convert_value_to_sql(value):
    if value is None:
        return 'NULL'
    if isinstance(value, str):
        return '"%s"' % value
    return str(value)


class COLLATE(enum.Enum):
    utf8_general_ci = 1


class ENGINE(enum.Enum):
    InnoDB = 1


class MAPPING(enum.Enum):
    INT = ('INT', int)

    CHAR = ('CHAR', str)
    VARCHAR = ('VARCHAR', str)
    TEXT = ('TEXT', str)

    DATE = ('DATE', datetime.date)
    TIME = ('TIME', datetime.time)
    YEAR = ('YEAR', datetime.datetime)
    DATETIME = ('DATETIME', datetime.datetime)
    TIMESTAMP = ('TIMESTAMP', datetime.datetime)

    def __new__(cls, db_type, py_type):
        obj = object.__new__(cls)
        obj._value_ = obj
        obj.db_type = db_type
        obj.py_type = py_type
        return obj

    def __call__(self, value):
        return isinstance(value, self.py_type)


class Field(object):
    def __init__(self, name, mapping, size, default=None, nullable=False,
                 auto_increment=False, current_timestamp=False, on_update=False):
        self.name = name
        self.mapping = mapping
        self.size = size
        #
        self.default = default
        #
        self.nullable = nullable
        self.auto_increment = auto_increment
        self.current_timestamp = current_timestamp
        self.on_update = on_update

    def is_auto(self):
        return self.auto_increment or self.current_timestamp or self.on_update

    def allow(self, value):
        return value is None or self.mapping(value) or value == self.default

    def to_sql(self):
        items = ['`%s`' % self.name,
                 '%s(%s)' % (self.mapping.db_type, self.size) if self.size > 0 else self.mapping.db_type,
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
            # 非 （ 值不为NULL 并且 默认值为NULL ）
            items.append('DEFAULT %s' % _convert_value_to_sql(self.default))
        return ' '.join(items)

    def __bool__(self):
        return bool(self.name)

    def __str__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.to_sql())


class IntField(Field):
    def __init__(self, name='', size=11, default=None, nullable=False, auto_increment=False):
        super().__init__(name, MAPPING.INT, size, default, nullable, auto_increment)


class AutoIntField(IntField):
    def __init__(self, name=''):
        super().__init__(name, auto_increment=True)


class CharField(Field):
    def __init__(self, name='', size=50, default=None, nullable=False):
        super().__init__(name, MAPPING.CHAR, size, default, nullable)


class VarcharField(Field):
    def __init__(self, name='', size=100, default=None, nullable=False):
        super().__init__(name, MAPPING.VARCHAR, size, default, nullable)


class TextField(Field):
    def __init__(self, name: str='', default=None, nullable=False):
        super().__init__(name, MAPPING.TEXT, 0, default, nullable)


class DateField(Field):
    def __init__(self, name='', default=None, nullable=False, on_update=False):
        super().__init__(name, MAPPING.DATE, 0, default, nullable,
                         on_update=on_update)


class TimeField(Field):
    def __init__(self, name='', default=None, nullable=False, on_update=False):
            super().__init__(name, MAPPING.TIME, 0, default, nullable,
                             on_update=on_update)


class YearField(Field):
    def __init__(self, name='', default=None, nullable=False, on_update=False):
            super().__init__(name, MAPPING.YEAR, 0, default, nullable,
                             on_update=on_update)


class DatetimeField(Field):
    def __init__(self, name='', default=None, nullable=False, current_timestamp=False, on_update=False):
        super().__init__(name, MAPPING.DATETIME, 0, default, nullable,
                         current_timestamp=current_timestamp, on_update=on_update)


class TimestampField(Field):
    def __init__(self, name='', default=None, nullable=False, current_timestamp=False, on_update=False):
        super().__init__(name, MAPPING.TIMESTAMP, 0, default, nullable,
                         current_timestamp=current_timestamp, on_update=on_update)


class Table(collections.OrderedDict):
    _name_ = ''
    _fields_ = collections.OrderedDict()
    _primarys_ = []
    _uniques_ = dict()
    _foreigns_ = dict()
    _collate_ = COLLATE.utf8_general_ci
    _engine_ = ENGINE.InnoDB

    def __new__(cls, *args, **kwargs):
        obj = super().__new__(cls)
        for k in cls.get_table_fields():
            obj[k] = cls.get_table_fields(k).default
        return obj

    def __setitem__(self, key, value):
        if key in self.get_table_fields() and self.get_table_fields(key).allow(value):
            return super().__setitem__(key, value)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return '<%s: %s>' % (self.get_table_name(),
                             '[%s]' % ','.join('(\'%s\', %s)' % (k, self[k]) for k in self.get_table_fields()))

    def set(self, key, value):
        self[key] = value

    def auto_keys(self, filter_call=None):
        if not filter_call:
            return [k for k in self if self.get_table_fields(k).is_auto()]
        return [k for k in self if self.get_table_fields(k).is_auto() and filter_call(self[k])]

    def auto_values(self, filter_call=None):
        if not filter_call:
            return [self[k] for k in self if self.get_table_fields(k).is_auto()]
        return [self[k] for k in self if self.get_table_fields(k).is_auto() and filter_call(self[k])]

    def auto_items(self, filter_call=None):
        if not filter_call:
            return [(k, self[k]) for k in self if self.get_table_fields(k).is_auto()]
        return [(k, self[k]) for k in self if self.get_table_fields(k).is_auto() and filter_call(self[k])]

    def data_keys(self, filter_call=None):
        if not filter_call:
            return [k for k in self if not self.get_table_fields(k).is_auto()]
        return [k for k in self if not self.get_table_fields(k).is_auto() and filter_call(self[k])]

    def data_values(self, filter_call=None):
        if not filter_call:
            return [self[k] for k in self if not self.get_table_fields(k).is_auto()]
        return [self[k] for k in self if not self.get_table_fields(k).is_auto() and filter_call(self[k])]

    def data_items(self, filter_call=None):
        if not filter_call:
            return [(k, self[k]) for k in self if not self.get_table_fields(k).is_auto()]
        return [(k, self[k]) for k in self if not self.get_table_fields(k).is_auto() and filter_call(self[k])]

    def has_primarykey(self):
        return bool(self[self.get_table_primarykey()])

    def get_primarykey(self):
        return self[self.get_table_primarykey()]

    def set_primarykey(self, value):
        self[self.get_table_primarykey()] = value

    def get_sql_insert(self):
        return lib.sql.From(self.get_table_name()).insert(self.data_items(lambda x: x is not None)).to_sql()

    def get_sql_update(self):
        return lib.sql.From(self.get_table_name()).where((self.get_table_primarykey(), self.get_primarykey()))\
            .update(self.data_items(lambda x: x is not None)).to_sql()

    def get_sql_delete(self):
        return lib.sql.From(self.get_table_name()).where((self.get_table_primarykey(), self.get_primarykey()))\
            .delete().to_sql()

    @classmethod
    def get_sql_find(cls, primrykey=None, **kwargs):
        if primrykey:
            return lib.sql.From(cls.get_table_name()).where((cls.get_table_primarykey(), primrykey))\
                .select(cls.get_table_fields().keys()).to_sql()
        if kwargs:
            sql_from = lib.sql.From(cls.get_table_name())
            for k in kwargs:
                sql_from.and_where((k, kwargs[k]))
            return sql_from.select(cls.get_table_fields().keys()).to_sql()

    @classmethod
    def get_sql_query(cls, selects=(), **kwargs):
        sql_from = lib.sql.From(cls.get_table_name())
        wheres = kwargs.get('where') or []
        if isinstance(wheres, (tuple, list)):
            for where in wheres:
                sql_from.and_where(where)
        elif isinstance(wheres, (dict, collections.OrderedDict)):
            for k in wheres:
                sql_from.and_where((k, wheres[k]))
        elif isinstance(wheres, str):
            sql_from.where(wheres)

        sql_from.order(kwargs.get('order') or [])

        limit = kwargs.get('limit') or 0
        sql_from.limit(limit)
        return sql_from.select(selects).to_sql()

    @classmethod
    def get_sql_create(cls):
        items = ['CREATE TABLE `%s`(\n' % cls.get_table_name(),
                 ',\n'.join(['\t%s' % field.to_sql() for field in cls.get_table_fields().values()]),
                 ',\n\tPRIMARY KEY (`%s`)' % cls.get_table_primarykey()]
        uniques = cls.get_table_uniques()
        if uniques:
            items.append(',\n\t')
            items.append(',\n\t'.join(['UNIQUE INDEX `%s` (`%s`)' % (key, value) for key, value in uniques.items()]))
        foreigns = cls.get_table_foreigns()
        if foreigns:
            items.append(',\n\t')
            items_foreign = []
            for key, foreign in foreigns.items():
                name = cls.get_table_name()
                f_name = foreign.get_table_name()
                f_key = foreign.get_table_primarykey()
                items_foreign\
                    .append('CONSTRAINT `{t_name}_{f_name}` FOREIGN KEY (`{t_key}`) REFERENCES `{f_name}` (`{f_key}`)'
                            .format(t_name=name, f_name=f_name, t_key=key, f_key=f_key))
            items.append(',\n\t'.join(items_foreign))
        items.append('\n)\n')
        items.append('COLLATE=\'%s\'\n' % cls.get_table_collate().name)
        items.append('ENGINE=%s\n;' % cls.get_table_engine().name)
        return ''.join(items)

    @classmethod
    def get_table_name(cls):
        return cls._name_

    @classmethod
    def set_table_name(cls, name):
        cls._name_ = name

    @classmethod
    def get_table_fields(cls, key=''):
        if key:
            return cls._fields_[key]
        return cls._fields_

    @classmethod
    def set_table_fields(cls, *kv_items):
        cls._fields_ = collections.OrderedDict(kv_items)

    @classmethod
    def get_table_primarykey(cls):
        if cls._primarys_:
            return cls._primarys_[0]
        cls._primarys_ = [k for k in cls._fields_ if isinstance(cls._fields_[k], AutoIntField)]
        if not cls._primarys_:
            cls._primarys_ = [k for k in cls._fields_ if isinstance(cls._fields_[k], IntField)]
            if not cls._primarys_:
                raise RuntimeError('there is no primarykey in the table.')
        return cls._primarys_[0]

    @classmethod
    def set_table_primarykey(cls, *keys):
        cls._primarys_ = list(keys)

    @classmethod
    def get_table_uniques(cls, key=''):
        if key:
            return cls._uniques_[key]
        return cls._uniques_

    @classmethod
    def set_table_uniques(cls, **kwargs):
        cls._uniques_ = kwargs

    @classmethod
    def get_table_foreigns(cls, key=''):
        if key:
            return cls._foreigns_[key]
        return cls._foreigns_

    @classmethod
    def set_table_foreigns(cls, **kwargs):
        cls._foreigns_ = kwargs

    @classmethod
    def get_table_collate(cls):
        return cls._collate_

    @classmethod
    def set_table_collate(cls, collate):
        cls._collate_ = collate

    @classmethod
    def get_table_engine(cls):
        return cls._engine_

    @classmethod
    def set_table_engine(cls, engine):
        cls._engine_ = engine


def table(name='', fields='', primarys=None,
          uniques=None, foreigns=None,
          collate=COLLATE.utf8_general_ci, engine=ENGINE.InnoDB):
    """

        装饰器 - 数据库映射模型装饰器

    :param name: 表名， 目前不支持
    :param fields: 字段列表
    :param primarys: 主键列表
    :param uniques: 唯一键字典
    :param foreigns: 外键字典
    :param collate: 字符集
    :param engine: 数据库引擎
    :return: 返回模型类
    """
    def set_table_cls(cls):
        if isinstance(cls, type) and not issubclass(cls, Table):
            cls = type(cls.__name__, (Table, cls), dict(Table.__dict__, **cls.__dict__))

        # 设置名称
        if hasattr(cls, 'set_table_name'):
            cls.set_table_name(name or cls.__name__)

        # 设置字段
        _field_names_ = fields if isinstance(fields, (tuple, list)) and fields \
            else (_name_ for _name_ in fields.strip().split() if _name_) if isinstance(fields, str) and fields \
            else []
        _field_items_ = []
        _cls_attrs_ = dir(cls)
        for _name_ in _field_names_:
            if _name_ in _cls_attrs_:
                _attr_ = getattr(cls, _name_)
                if isinstance(_attr_, Field):
                    _attr_.name = _name_
                    _field_items_.append((_name_, _attr_))
        if hasattr(cls, 'set_table_fields'):
            cls.set_table_fields(*_field_items_)

        # 设置主键
        _primary_keys_ = primarys if isinstance(primarys, (tuple, list)) and primarys \
            else (_key_ for _key_ in primarys.strip().split() if _key_) if isinstance(primarys, str) and primarys \
            else []
        if hasattr(cls, 'set_table_primarykey'):
            cls.set_table_primarykey(*_primary_keys_)

        # 设置唯一键和外键
        if hasattr(cls, 'set_table_uniques') and hasattr(cls, 'set_table_foreigns'):
            if uniques:
                cls.set_table_uniques(**uniques)
            if foreigns:
                cls.set_table_foreigns(**foreigns)
        # 设置字符集和储存引擎
        if hasattr(cls, 'set_table_collate') and hasattr(cls, 'set_table_engine'):
            cls.set_table_collate(collate)
            cls.set_table_engine(engine)
        return cls
    return set_table_cls


class ApiTableSet(object):
    def create(self):
        raise NotImplementedError()

    def add(self, entity):
        raise NotImplementedError()

    def update(self, entity):
        raise NotImplementedError()

    def remove(self, entity):
        raise NotImplementedError()

    def get(self, primarykey=None, **kwargs):
        """

        :param primarykey:
        :param kwargs: wheres
        :return:
        """
        raise NotImplementedError()

    def find(self, selects=(), **kwargs):
        """

        :param selects:
        :param kwargs: wheres
        :return:
        """
        raise NotImplementedError()

    def query(self, selects=(), **kwargs):
        """

        :param selects:
        :param kwargs: dict(where=dict(), order='', limit=(0, 0) )
        :return:
        """
        raise NotImplementedError()

    def count(self, **kwargs):
        raise NotImplementedError()

    def __iter__(self):
        raise NotImplementedError()


class TableSet(ApiTableSet):
    def __init__(self, db, table):
        self.db = db
        self.table = table

    def __repr__(self):
        return '<TableSet: db=%s table=%s>' % (self.db.name, self.table.get_table_name())

    def create(self):
        return self.db.execute(self.table.get_sql_create())

    def new(self, iterable=(), **kwargs):
        return self.table(iterable, **kwargs)

    def add(self, entity):
        if not entity.has_primarykey():
            if self.db.execute(entity.get_sql_insert()):
                entity.update(**self.get(self.db.insert_id()))
                return entity

    def update(self, entity):
        if entity.has_primarykey():
            if self.db.execute(entity.get_sql_update()):
                entity.update(**self.get(entity.get_primarykey()))
                return entity

    def save(self, entity):
        return self.add(entity) or self.update(entity)

    def remove(self, entity):
        if entity.has_primarykey():
            return self.db.execute(entity.get_sql_delete())

    def get(self, primarykey=None, **kwargs):
        query = self.db.query(self.table.get_sql_query(where={self.table.get_table_primarykey(): primarykey})) \
            if primarykey else self.db.query(self.table.get_sql_query(where=kwargs)) if kwargs else None
        if query:
            return self.table(**query[0])

    def find(self, selects=(), **kwargs):
        query = self.db.query(self.table.get_sql_query(selects, where=kwargs))
        if query:
            if not selects:
                return [self.table(**row) for row in query]
            else:
                return query

    def query(self, selects=(), **kwargs):
        query = self.db.query(self.table.get_sql_query(selects, **kwargs))
        if query:
            if not selects:
                return [self.table(**row) for row in query]
            else:
                return query

    def count(self, **kwargs):
        query = self.db.query(self.table.get_sql_query(('count(*) as num',), where=kwargs))
        if query:
            return query[0]['num']

    def __iter__(self):
        query = self.db.query(self.table.get_sql_query(
                (self.table.get_table_primarykey(),), order=(self.table.get_table_primarykey(),)))
        if query:
            _gets_ = [item[self.table.get_table_primarykey()] for item in query if item]
            for _get_ in _gets_:
                yield self.get(_get_)


class Db(object):
    """
        数据库连接器
    """
    def __init__(self, db):
        self.db = db

    def __bool__(self):
        return bool(self.db)

    def __str__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.db)

    @property
    def config(self):
        return self.db.config

    @property
    def name(self):
        return self.db.name

    def is_open(self):
        return self.db.is_open()

    def open(self):
        self.db.open()
        return self

    def __enter__(self):
        return self.open()

    def close(self):
        self.db.close()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()

    def get_tables(self, name_db=''):
        return self.db.get_tables(name_db)

    def create_tables(self, *tables):
        if not tables:
            for _tableset_ in self.__dict__.values():
                if isinstance(_tableset_, TableSet):
                    self.db.execute(_tableset_.table.get_sql_create())
        else:
            for _table_ in tables:
                if issubclass(_table_, Table):
                    self.db.execute(_table_.get_sql_create())
        return self.get_tables()

    def set(self, table):
        if issubclass(table, Table):
            return TableSet(self.db, table)

    def __iter__(self):
        for _key_ in self.__dict__:
            if isinstance(self.__dict__.get(_key_), TableSet):
                yield self.__dict__.get(_key_)


if __name__ == '__main__':
    pass
