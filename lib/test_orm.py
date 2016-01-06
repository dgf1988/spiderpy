# coding: utf-8
import enum
from lib import db
from lib import sql
from collections import OrderedDict


@enum.unique
class DEFAULT(enum.Enum):
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
    def __init__(self, column: str, length=0, nullable=False, default=None, py_type: type=None):
        if length < 0:
            raise ValueError('length must be >= 0')
        self.__type__ = py_type
        self.__column__ = column
        self.__column_name__ = ''
        self.__length__ = length
        self.__nullable__ = nullable
        self.__default__ = default
        self.__setable__ = True
        if self.__default__ == DEFAULT.NULL:
            self.__nullable__ = True
        elif self.__default__ not in \
                (DEFAULT.AUTO_INCREMENT, DEFAULT.CURRENT_TIMESTAMP, DEFAULT.ON_UPDATE_CURRENT_TIMESTAMP):
            self.__setable__ = False

    @property
    def column(self):
        return self.__column__

    @property
    def length(self):
        return self.__length__

    @property
    def nullable(self):
        return self.__nullable__

    @property
    def setable(self):
        return self.__setable__

    @property
    def default(self):
        return self.__default__

    @property
    def name(self):
        return self.__column_name__

    @name.setter
    def name(self, name: str):
        self.__column_name__ = name

    def to_sql(self):
        items = []
        if isinstance(self, (DataField, TimestampField)):
            items.append('%s' % (self.column,))
        else:
            items.append('%s(%s)' % (self.column, self.length))
        if self.nullable:
            items.append('NULL')
        else:
            items.append('NOT NULL')
        if self.default:
            if isinstance(self.default, DEFAULT):
                items.append(self.default.to_sql())
            elif callable(self.default):
                items.append('')
            else:
                items.append('\'%s\'' % self.default)
        return ' '.join(items)

    def equal(self, value):
        return sql.WhereEqual(self.name, value)

    def not_equal(self, value):
        return sql.WhereNotEqual(self.name, value)

    def between(self, left, right):
        return sql.WhereBetween(self.name, left, right)


class IntField(Field):
    def __init__(self, length=11, nullable=False, default=None):
        super().__init__('INT', length, nullable, default, py_type=int)


class CharField(Field):
    def __init__(self, length=50, nullable=False, default=None):
        super().__init__('CHAR', length, nullable, default, py_type=str)


class VarcharField(Field):
    def __init__(self, length=100, nullable=False, default=None):
        super().__init__('VARCHAR', length, nullable, default, py_type=str)


class DataField(Field):
    def __init__(self, nullable=False, default=None):
        super().__init__('DATE', nullable=nullable, default=default, py_type=str)


class TimestampField(Field):
    def __init__(self, nullable=False, default=None):
        super().__init__('TIMESTAMP', nullable=nullable, default=default, py_type=str)


class ForeignKeyField(Field):
    def __init__(self, foreign: type):
        super().__init__('', py_type=foreign)
        self.__foreign__ = foreign

    def __call__(self, *args, **kwargs):
        return self.__foreign__(*args, **kwargs)


class OneToOneField(ForeignKeyField):
    pass


class OneToManyField(ForeignKeyField):
    pass


class ManyToManyField(ForeignKeyField):
    pass


class ManyToOneField(ForeignKeyField):
    pass


class Table(OrderedDict):
    __table__ = ''
    __primary_key__ = ''
    __mappings__ = OrderedDict()

    def __init__(self, **kwargs):
        super().__init__()
        for k, v in self.__mappings__.items():
            if k in kwargs:
                self[k] = kwargs.get(k)
            elif isinstance(v, ForeignKeyField):
                self[k] = v()
            elif isinstance(v, Field):
                self[k] = v.default

    def __setattr__(self, key, value):
        self[key] = value

    def __getattr__(self, item):
        return self[item]

    @classmethod
    def get_mappings(cls):
        return cls.__mappings__

    @staticmethod
    def primarykey(key: str):
        def set_key(cls):
            cls.__primary_key__ = key
            return cls
        return set_key

    @staticmethod
    def name(table: str):
        def set_name(cls):
            cls.__table__ = table
            return cls
        return set_name

    @staticmethod
    def columns(*order):
        def set_column(cls):
            __mappings__ = OrderedDict()
            for column in order:
                if column in cls.__dict__:
                    field = getattr(cls, column)
                    if isinstance(field, (Field,)):
                        field.name = column
                        __mappings__[column] = field
            cls.__mappings__ = __mappings__
            return cls
        return set_column


@Table.name('user')
@Table.primarykey('id')
@Table.columns('id', 'name', 'age', 'add_at')
class User(Table):
    id = IntField(default=DEFAULT.AUTO_INCREMENT)
    name = CharField()
    age = IntField()
    add_at = DataField(default=DEFAULT.CURRENT_TIMESTAMP)


@Table.name('blog')
@Table.primarykey('id')
@Table.columns('id', 'user', 'title', 'text', 'add_at')
class Blog(Table):
    id = IntField(default=DEFAULT.AUTO_INCREMENT)
    user = ManyToOneField(User)
    title = CharField()
    text = VarcharField()
    add_at = DataField(default=DEFAULT.CURRENT_TIMESTAMP)


@Table.name('html')
@Table.primarykey('id')
@Table.columns('id', 'urlmd5', 'htmlmd5', 'code', 'update_at')
class Html(Table):
    id = IntField(default=DEFAULT.AUTO_INCREMENT)
    urlmd5 = CharField(default=DEFAULT.NULL)
    htmlmd5 = CharField()
    code = IntField()
    update_at = TimestampField(default=DEFAULT.ON_UPDATE_CURRENT_TIMESTAMP)


class DbSet(db.DB):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class TableSet(object):
    def __init__(self, table: type, db: DbSet=DbSet()):
        self.__table__ = table
        self.__db__ = db
        self.__sql__ = sql.From(self.__table__.__table__)
        self.__default_selection__ = []
        for k, v in self.__table__.get_mappings().items():
            self.__default_selection__.append(k)
            setattr(self, k, v)

    @property
    def table(self):
        return self.__table__

    @property
    def sql(self):
        return self.__sql__

    @property
    def db(self):
        return self.__db__

    @db.setter
    def db(self, db_set: DbSet):
        self.__db__ = db_set

    def skip(self, skip: int):
        self.sql.skip(skip)
        return self

    def take(self, take: int):
        self.sql.take(take)
        return self

    def set(self, **kwargs):
        self.sql.set(**kwargs)
        return self

    def where(self, *args, **kwargs):
        self.sql.where(*args, **kwargs)
        return self

    def order(self, *order):
        self.sql.order(*order)
        return self

    def get(self, primary_key=None) -> dict:
        if primary_key:
            get_sql = sql.From(self.table.__table__)\
                .where(sql.WhereEqual(self.table.__primary_key__, primary_key))\
                .select(*self.__default_selection__)
        else:
            get_sql = self.sql.select(*self.__default_selection__)
        self.sql.clear()
        print(get_sql.to_sql())
        if self.db.execute(get_sql.to_sql()):
            get = self.db.fetchone()
            return get
        return dict()

    def select(self, *select) -> list:
        if not select:
            select = self.__default_selection__
        sql = self.sql.select(*select)
        self.sql.clear()
        if self.db.execute(sql.to_sql()):
            return self.db.fetchall()
        return []


class Hoetom(DbSet):
    def __init__(self, user='root', passwd='guofeng001', db='hoetom'):
        super().__init__(user, passwd, db)
        self.html = TableSet(Html, self)


def print_dict(cls: type):
    print('class: ', cls.__name__)
    for k, v in cls.__dict__.items():
        print(k, v)


if __name__ == '__main__':
    with Hoetom() as hoetom:
        hs = hoetom.html.where(Html.id.equal(10)).get()
        for key in hs:
            print(hs[key], ':', key)
