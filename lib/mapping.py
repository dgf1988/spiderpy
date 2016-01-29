# coding: utf-8
import enum
import datetime
import collections


__all__ = ['IntField', 'AutoIntField', 'CharField', 'VarcharField', 'TextField',
           'DateField', 'TimeField', 'YearField', 'DatetimeField', 'TimestampField',
           'COLLATE', 'ENGINE', 'MAPPING', 'Table', 'table']


def _convert_value_to_sql(value):
    if value is None:
        return 'NULL'
    if isinstance(value, str):
        return '"%s"' % value
    return str(value)


class COLLATE(enum.IntEnum):
    utf8_general_ci = 1


class ENGINE(enum.IntEnum):
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
    # 表名
    _name = ''
    # field mappings
    _fields = collections.OrderedDict()
    # 主键
    _primarykey = []
    # 唯一键
    _uniques = dict()
    # foreign key
    _foreign = dict()
    # 字符集
    _collate = COLLATE.utf8_general_ci
    # 数据库引擎
    _engine = ENGINE.InnoDB

    def __init__(self, **kwargs):
        super().__init__()
        # 初始化字段
        for k in self.get_table_fields():
            # 有指定值则使用指定值，没有则使用默认值
            self[k] = kwargs.get(k)

    def __str__(self):
        return '<%s: %s>' % (self.get_table_name(), ' '.join(str(_item_) for _item_ in self.items()))

    def __setitem__(self, key, value):
        if key in self.get_table_fields():
            if self.get_table_fields(key).allow(value):
                return super().__setitem__(key, value)
            raise TypeError('the value %s (%s) not instance of %s' %
                            (value, type(value), self.get_table_fields(key).mapping.py_type))
        raise KeyError('the key %s not in %s' % (key, self.get_table_fields().keys()))

    def set(self, key, value):
        self[key] = value

    def get_primarykey(self):
        # 主键取值
        return self[self.get_table_primarykey()]

    def set_primarykey(self, value):
        # 主键赋值
        self[self.get_table_primarykey()] = value

    def has_primarykey(self):
        # 主键是否有值
        return bool(self[self.get_table_primarykey()])

    @classmethod
    def auto_keys(cls):
        fields = cls.get_table_fields()
        return [k for k in fields if fields[k].is_auto()]

    @classmethod
    def data_keys(cls):
        fields = cls.get_table_fields()
        return [k for k in fields if not fields[k].is_auto()]

    def auto_values(self):
        return [self[k] for k in self if self.get_table_fields(k).is_auto()]

    def data_values(self):
        return [self[k] for k in self if not self.get_table_fields(k).is_auto()]

    # 自动字段
    def auto_items(self):
        return [(k, self[k]) for k in self if self.get_table_fields(k).is_auto()]

    # 数据字段
    def data_items(self, filter_value_lambda=None):
        if not filter_value_lambda:
            return [(k, self[k]) for k in self if not self.get_table_fields(k).is_auto()]
        return [(k, self[k]) for k in self if not self.get_table_fields(k).is_auto() and filter_value_lambda(self[k])]

    def foreign_items(self, by_dict=False):
        if not by_dict:
            return [(k, self.get_table_foreigns(k), self[k]) for k in self if k in self.get_table_foreigns()]
        return {k: (self.get_table_foreigns(k), self[k]) for k in self if k in self.get_table_foreigns()}

    @classmethod
    def set_table_name(cls, name):
        cls._name = name

    @classmethod
    def get_table_name(cls):
        return cls._name

    @classmethod
    def set_table_primarykey(cls, *names):
        cls._primarykey = list(names)
        for k in cls._primarykey:
            cls.get_table_fields(k).auto_increment = True

    @classmethod
    def get_table_primarykey(cls):
        if not cls._primarykey:
            cls._primarykey = [name for name, field in cls._fields.items() if isinstance(field, AutoIntField)]
            if not cls._primarykey:
                cls._primarykey = [name for name, field in cls._fields.items() if isinstance(field, IntField)]
                if not cls._primarykey:
                    raise RuntimeError('the table %s has not primarykey' % cls._name)
            return cls.get_table_primarykey()
        else:
            return cls._primarykey[0]

    @classmethod
    def get_table_fields(cls, key=''):
        return cls._fields[key] if key else cls._fields

    @classmethod
    def set_table_fields(cls, *fields):
        cls._fields = collections.OrderedDict(fields)

    @classmethod
    def add_table_fields(cls, *fields):
        for field in fields:
            if field.name and isinstance(field, Field):
                cls._fields[field.name] = field

    @classmethod
    def get_table_uniques(cls):
        return cls._uniques

    @classmethod
    def set_table_uniques(cls, **kwargs):
        cls._uniques = kwargs

    @classmethod
    def get_table_foreigns(cls, key=''):
        return cls._foreign[key] if key else cls._foreign

    @classmethod
    def set_table_foreigns(cls, **kwargs):
        cls._foreign = kwargs

    @classmethod
    def get_table_collate(cls):
        return cls._collate

    @classmethod
    def set_table_collate(cls, collate):
        cls._collate = collate

    @classmethod
    def get_table_engine(cls):
        return cls._engine

    @classmethod
    def set_table_engine(cls, engine):
        cls._engine = engine

    @classmethod
    def get_table_sql(cls):
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


def table(name='', fields=None, primarykey=None,
          unique=None, foreign=None, collate=COLLATE.utf8_general_ci, engine=ENGINE.InnoDB):
    def set_table_cls(cls):
        # 表名
        cls.set_table_name(name or cls.__name__)

        # 字段映射
        _keys_ = fields if isinstance(fields, (tuple, list)) \
            else list(_name_ for _name_ in fields.strip().split() if _name_) if isinstance(fields, str) \
            else []
        _fields_ = []
        for _key_ in _keys_:
            if _key_ in cls.__dict__ and isinstance(cls.__dict__[_key_], Field):
                cls.__dict__[_key_].name = cls.__dict__[_key_].name or _key_
                _fields_.append((_key_, cls.__dict__[_key_]))
        cls.set_table_fields(*_fields_)

        # 主键
        _primary_key_ = primarykey if isinstance(primarykey, (tuple, list)) \
            else (_name_ for _name_ in primarykey.strip().split() if _name_) if isinstance(primarykey, str) \
            else []
        cls.set_table_primarykey(*_primary_key_)

        # 唯一键， 外键
        if unique:
            cls.set_table_uniques(**unique)
        if foreign:
            cls.set_table_foreigns(**foreign)

        # 字符集， 数据库引擎
        cls.set_table_collate(collate)
        cls.set_table_engine(engine)
        return cls
    return set_table_cls


@table(fields='id pid', primarykey='id', unique=dict(_pid='pid'))
class PID(Table):
    id = AutoIntField()
    pid = IntField()


@table(fields='id pid name age birth update_at', primarykey='id',
       unique=dict(_name_='name'), foreign=dict(pid=PID))
class Test(Table):
    id = AutoIntField()
    pid = IntField()
    name = CharField(size=20)
    age = IntField(nullable=True)
    birth = DatetimeField(nullable=True)
    update_at = TimestampField(current_timestamp=True)


if __name__ == '__main__':
    t = Test()
    print(t)
    print(*t.auto_items())
    print(*t.items())