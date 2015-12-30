from lib.db import DB
import enum


@enum.unique
class FIELDDEFAULT(enum.Enum):
    NULL = 0
    AUTO_INCREMENT = 1
    CURRENT_TIMESTAMP = 2
    ON_UPDATE_CURRENT_TIMESTAMP = 3

    __str_auto_increment__ = 'AUTO_INCREMENT'
    __str_null__ = 'DEFAULT NULL'
    __str_current_timestamp__ = 'DEFAULT CURRENT_TIMESTAMP'
    __str_on_update__ = 'DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'

    def to_sql(self):
        if self == self.AUTO_INCREMENT:
            return self.__str_auto_increment__
        if self == self.NULL:
            return self.__str_null__
        if self == self.CURRENT_TIMESTAMP:
            return self.__str_current_timestamp__
        if self == self.ON_UPDATE_CURRENT_TIMESTAMP:
            return self.__str_on_update__


class Field(object):
    def __init__(self, column_type: str, length=0, nullable=False, default=None):
        if length < 0:
            raise ValueError('length must be >= 0')
        self.__column_type__ = column_type
        self.__length__ = length
        self.__nullable__ = nullable
        self.__default__ = default
        if self.__default__ == FIELDDEFAULT.NULL:
            self.__nullable__ = True

    @property
    def column_type(self):
        return self.__column_type__

    @property
    def length(self):
        return self.__length__

    @property
    def nullable(self):
        return self.__nullable__

    @property
    def default(self):
        return self.__default__

    def to_sql(self):
        items = []
        if isinstance(self, (DataField, TimestampField)):
            items.append('%s' % (self.column_type,))
        else:
            items.append('%s(%s)' % (self.column_type, self.length))
        if self.nullable:
            items.append('NULL')
        else:
            items.append('NOT NULL')
        if self.default:
            if isinstance(self.default, FIELDDEFAULT):
                items.append(self.default.to_sql())
            elif callable(self.default):
                items.append('')
            else:
                items.append('\'%s\'' % self.default)
        return ' '.join(items)


class IntField(Field):
    def __init__(self, length=11, nullable=False, default=None):
        super().__init__('INT', length, nullable, default)


class CharField(Field):
    def __init__(self, length=50, nullable=False, default=None):
        super().__init__('CHAR', length, nullable, default)


class VarcharField(Field):
    def __init__(self, length=100, nullable=False, default=None):
        super().__init__('VARCHAR', length, nullable, default)


class DataField(Field):
    def __init__(self, nullable=False, default=None):
        super().__init__('DATE', nullable=nullable, default=default)


class TimestampField(Field):
    def __init__(self, nullable=False, default=None):
        super().__init__('TIMESTAMP', nullable=nullable, default=default)


class DbTableMetaclass(type):
    def __new__(mcs, name, bases, attrs):
        if name == 'DbTable':
            return type.__new__(mcs, name, bases, attrs)
        # set table name
        table_name = attrs.get('__table__', name)
        attrs['__table__'] = table_name

        # set field mappings
        mappings = dict()
        for k, v in attrs.items():
            if isinstance(v, Field):
                mappings[k] = v
        attrs['__mappings__'] = mappings

        # set primary key
        primary_key = attrs.get('__primary_key__')
        if not primary_key or primary_key not in mappings.keys():
            raise RuntimeError('%s primary_key not found' % name)

        # set field order
        field_order = attrs.get('__field_order__')
        if not field_order:
            field_order = [key for key in mappings.keys()]
        for key in field_order:
            if key not in mappings.keys():
                field_order.remove(key)
        for key in mappings.keys():
            if key not in field_order:
                field_order.append(key)
        attrs['__field_order__'] = field_order

        # delete class field
        for k in attrs['__field_order__']:
            attrs.pop(k)

        # return class
        return type.__new__(mcs, name, bases, attrs)


class DbTable(dict, metaclass=DbTableMetaclass):
    __table__ = ''
    __field_order__ = []
    __primary_key__ = 'id'
    __mappings__ = dict()
    __collate__ = 'utf8_general_ci'
    __engine__ = 'InnoDB'

    def __init__(self, **kwargs):
        for key in self.__field_order__:
            self[key] = self.__mappings__[key].default
        super().__init__(**kwargs)

    def __setattr__(self, key, value):
        self[key] = value

    def __getattr__(self, item):
        return self[item]

    def get_value(self, key: str):
        return getattr(self, key, None)

    def get_value_default(self, key: str):
        value = getattr(self, key, None)
        if value is None:
            field = self.__mappings__[key]
            if field.default is not None:
                value = field.default() if callable(field.default) else field.default
                setattr(self, key, value)
        return value

    def to_str(self):
        fileds = []
        for key in self.__field_order__:
            value = self.get_value_default(key)
            if isinstance(value, str):
                fileds.append('\t`%s`\t=>\t"%s"' % (key, value))
            else:
                fileds.append('\t`%s`\t=>\t%s' % (key, value))
        items = ['`%s`\t{' % self.__table__,
                 '\n'.join(fileds),
                 '}']
        return '\n'.join(items)

    @classmethod
    def sql_create_table(cls):
        items = ['CREATE TABLE `%s` (' % cls.__table__,
                 ',\n'.join(['    `%s` %s' % (key, cls.__mappings__.get(key).to_sql()) for key in cls.__field_order__] +
                            ['    PRIMARY KEY (`%s`)' % cls.__primary_key__]),
                 ')',
                 'COLLATE=\'%s\'' % cls.__collate__,
                 'ENGINE=%s' % cls.__engine__]
        return '\n'.join(items)


class UserDbTable(DbTable):
    id = IntField(default=FIELDDEFAULT.AUTO_INCREMENT)
    name = CharField(default=0)
    email = CharField(default='email@xx.com')
    birth = DataField(default=FIELDDEFAULT.NULL)
    __field_order__ = ['id', 'name', 'email', 'birth']
    __primary_key__ = 'id'


class DbSet(object):
    def __init__(self, table: DbTable):
        self.__table__ = table
    pass


class DbContext(DB):
    def __init__(self, user='', passwd='', db='', host='localhost', port=3306, charset='utf-8', autocommit=True):
        super().__init__(user=user, passwd=passwd, db=db, host=host, port=port, charset=charset, autocommit=autocommit)


class MyDbContext(DbContext):
    user = DbSet(UserDbTable)

    def __init__(self, user='root', passwd='guofeng001', db='hoetom'):
        super().__init__(user, passwd, db)

