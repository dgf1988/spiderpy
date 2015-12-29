# coding=utf-8
import enum
from functools import reduce


class SqlKey(object):
    def __init__(self, key: str):
        if not key:
            raise ValueError('empty key')
        self.__key__ = key

    def __str__(self):
        return '`%s`' % self.__key__

    def __eq__(self, other):
        if not isinstance(other, SqlKey):
            return False
        return self.__key__ == other.__key__

    def __bool__(self):
        return bool(self.__key__)


class SqlValue(object):
    def __init__(self, value):
        self.__value__ = value

    def __str__(self):
        if self.__value__ is None:
            return 'null'
        if isinstance(self.__value__, (int, float, SQLORDER)):
            return '%s' % self.__value__
        return '"%s"' % self.__value__

    def __eq__(self, other):
        if not isinstance(other, SqlValue):
            return False
        return self.__value__ == other.__value__

    def __bool__(self):
        return bool(self.__value__)


@enum.unique
class SQLORDER(enum.Enum):
    ASC = 0
    DESC = 1
    __str_asc__ = 'asc'
    __str_desc__ = 'desc'

    def __str__(self):
        if self == self.ASC:
            return self.__str_asc__
        if self == self.DESC:
            return self.__str_desc__

    def __bool__(self):
        return self == self.DESC

    @classmethod
    def from_str(cls, _str: str):
        _str = _str.strip().lower()
        if _str == cls.__str_asc__:
            return cls.ASC
        if _str == cls.__str_desc__:
            return cls.DESC
        raise ValueError

    @classmethod
    def from_object(cls, _obj):
        if isinstance(_obj, cls):
            return _obj
        if isinstance(_obj, str):
            return cls.from_str(_obj)
        if not _obj:
            return cls.ASC
        else:
            return cls.DESC


class SqlOrderCase(object):
    __default_order__ = SQLORDER.ASC

    def __init__(self, key: str, order: SQLORDER):
        if not key:
            raise ValueError
        self.__key__ = key
        self.__order__ = order

    def __eq__(self, other):
        return str(self) == str(other)

    def __str__(self):
        return '%s %s' % (SqlKey(self.__key__), SqlValue(self.__order__))

    def __bool__(self):
        return bool(self.__order__)

    def __add__(self, other):
        if isinstance(other, SqlOrderCase):
            return SqlOrder(self, other)
        if isinstance(other, SqlOrder):
            return SqlOrder(self) + other
        raise TypeError

    def __len__(self):
        return 1

    @classmethod
    def from_str(cls, _str: str):
        return SqlOrderDefault(_str)

    @classmethod
    def from_dict(cls, _dict: dict):
        if 'key' in _dict and ('value' in _dict or 'order' in _dict):
            key = _dict.get('key')
            order = _dict.get('order') or _dict.get('value')
        else:
            key, order = _dict.popitem()
        return cls(key, SQLORDER.from_object(order))

    @classmethod
    def from_object(cls, _obj):
        if isinstance(_obj, str):
            return cls.from_str(_obj)
        if isinstance(_obj, dict):
            return cls.from_dict(_obj)
        if isinstance(_obj, cls):
            return _obj
        raise TypeError

    @classmethod
    def format_list(cls, *list_order) -> list:
        return [cls.from_object(each) for each in list_order]

    @classmethod
    def format_dict(cls, **kwargs) -> list:
        return [cls(key, SQLORDER.from_object(value)) for key, value in kwargs.items()]


class SqlOrderDefault(SqlOrderCase):
    def __init__(self, key: str):
        super().__init__(key, self.__default_order__)


class SqlOrderDesc(SqlOrderCase):
    def __init__(self, key: str):
        super().__init__(key, SQLORDER.DESC)


class SqlOrderAsc(SqlOrderCase):
    def __init__(self, key: str):
        super().__init__(key, SQLORDER.ASC)


class SqlOrderBy(object):

    def __init__(self, key: str):
        if not key:
            raise ValueError('empty key')
        self.__key__ = key

    def default(self):
        return SqlOrderDefault(self.__key__)

    def desc(self):
        return SqlOrderDesc(key=self.__key__)

    def asc(self):
        return SqlOrderAsc(key=self.__key__)


class SqlOrder(list):
    def __init__(self, *list_order_case, **kwargs):
        super().__init__(SqlOrderCase.format_list(*list_order_case) + SqlOrderCase.format_dict(**kwargs))

    def __add__(self, other):
        if isinstance(other, SqlOrder):
            self.extend(other)
            return self
        if isinstance(other, SqlOrderCase):
            self.append(other)
            return self
        raise TypeError

    def __str__(self):
        return ','.join([str(order_case) for order_case in self])

    def asc(self, column_name: str):
        self.append(SqlOrderAsc(column_name))
        return self

    def desc(self, column_name: str):
        self.append(SqlOrderDesc(column_name))
        return self


class SqlLimit(object):
    def __init__(self, top=0, skip=0):
        self.__top__ = top
        if self.__top__ <= 0:
            self.__top__ = 0
        self.__skip__ = skip
        if self.__skip__ <= 0:
            self.__skip__ = 0

    def __bool__(self):
        return self.__top__ > 0 and self.__skip__ >= 0

    def __eq__(self, other):
        return str(self) == str(other)

    def __str__(self):
        return '%s,%s' % (self.__top__, self.__skip__)

    def skip(self, _skip: int):
        self.__skip__ = _skip
        return self

    def top(self, _top: int):
        self.__top__ = _top
        return self


class SqlTop(SqlLimit):
    def __init__(self, _top: int):
        super().__init__(top=_top, skip=0)


@enum.unique
class SQLWHERETYPE(enum.Enum):
    STR = 0
    __str_str__ = ''
    EQUAL = 1
    __str_equal__ = '='
    LESS = 2
    __str_less__ = '<'
    GREATER = 3
    __str_greater__ = '>'
    LESS_EQUAL = 4
    __str_less_equal__ = '<='
    GREATER_EQUAL = 5
    __str_greater_equal__ = '>='
    NOT_EQUAL = 6
    __str_not_equal__ = '<>'

    IN = 10
    __str_in__ = 'in'
    BETWEEN = 11
    __str_between__ = 'between'
    LIKE = 12
    __str_like__ = 'like'

    NOT_IN = 13
    __str_not_in__ = 'not in'
    NOT_BETWEEN = 14
    __str_not_between__ = 'not between'
    NOT_LIKE = 15
    __str_not_like__ = 'not like'

    def __str__(self):
        if self == SQLWHERETYPE.EQUAL:
            return SQLWHERETYPE.__str_equal__
        if self == SQLWHERETYPE.NOT_EQUAL:
            return SQLWHERETYPE.__str_not_equal__
        if self == SQLWHERETYPE.LESS:
            return SQLWHERETYPE.__str_less__
        if self == SQLWHERETYPE.LESS_EQUAL:
            return SQLWHERETYPE.__str_less_equal__
        if self == SQLWHERETYPE.GREATER:
            return SQLWHERETYPE.__str_greater__
        if self == SQLWHERETYPE.GREATER_EQUAL:
            return SQLWHERETYPE.__str_greater_equal__
        if self == SQLWHERETYPE.IN:
            return SQLWHERETYPE.__str_in__
        if self == SQLWHERETYPE.NOT_IN:
            return SQLWHERETYPE.__str_not_in__
        if self == SQLWHERETYPE.BETWEEN:
            return SQLWHERETYPE.__str_between__
        if self == SQLWHERETYPE.NOT_BETWEEN:
            return SQLWHERETYPE.__str_not_between__
        if self == SQLWHERETYPE.LIKE:
            return SQLWHERETYPE.__str_like__
        if self == SQLWHERETYPE.NOT_LIKE:
            return SQLWHERETYPE.__str_not_like__
        if self == SQLWHERETYPE.STR:
            return SQLWHERETYPE.__str_str__


class SqlWhereCase(object):
    __default_type__ = SQLWHERETYPE.EQUAL

    def __init__(self, key: str, where_type: SQLWHERETYPE, value):
        if not key:
            raise ValueError('empty key')
        self.__key__ = key
        self.__where_type__ = where_type
        self.__value__ = value

    def __and__(self, other):
        return SqlWhereAnd(self, other)

    def __or__(self, other):
        return SqlWhereOr(self, other)

    def __str__(self):
        if self.__where_type__ in (SQLWHERETYPE.IN, SQLWHERETYPE.NOT_IN):
            return '%s %s (%s)' % \
               (SqlKey(self.__key__), self.__where_type__, ','.join([str(SqlValue(value)) for value in self.__value__]))
        elif self.__where_type__ in (SQLWHERETYPE.BETWEEN, SQLWHERETYPE.NOT_BETWEEN):
            if isinstance(self.__value__, dict):
                return '%s %s %s and %s' % \
                        (SqlKey(self.__key__), self.__where_type__,
                         SqlValue(self.__value__['left']), SqlValue(self.__value__['right']))
            if isinstance(self.__value__, (tuple, list)):
                return '%s %s %s and %s' % \
                        (SqlKey(self.__key__), self.__where_type__,
                         SqlValue(self.__value__[0]), SqlValue(self.__value__[1]))
        elif self.__where_type__ is SQLWHERETYPE.STR:
            return str(self.__value__)
        return '%s %s %s' % (SqlKey(self.__key__), self.__where_type__, SqlValue(self.__value__))

    def __eq__(self, other):
        return str(self) == str(other)

    def __len__(self):
        return 1

    @classmethod
    def from_str(cls, _str: str):
        if not _str:
            raise ValueError
        return SqlWhereStr(_str)

    @classmethod
    def from_object(cls, _obj):
        if isinstance(_obj, str):
            return cls.from_str(_obj)
        if isinstance(_obj, SqlWhereCase):
            return _obj
        raise TypeError

    @classmethod
    def format_list(cls, *list_where_case):
        return [cls.from_object(obj) for obj in list_where_case]

    @classmethod
    def format_dict(cls, **kwargs):
        return [cls(key, cls.__default_type__, value) for key, value in kwargs.items()]


class SqlWhereStr(SqlWhereCase):
    def __init__(self, str_where: str):
        super().__init__('where_str', SQLWHERETYPE.STR, str_where)

    def __bool__(self):
        return bool(self.__value__)


class SqlWhereNull(SqlWhereStr):
    def __init__(self):
        super().__init__('')

    def __bool__(self):
        return False

    def __len__(self):
        return 0


class SqlWhereTrue(SqlWhereStr):
    def __init__(self):
        super().__init__('1')

    def __bool__(self):
        return True

    def __len__(self):
        return 1


class SqlWhereEqual(SqlWhereCase):
    def __init__(self, key: str, value):
        super().__init__(key, SQLWHERETYPE.EQUAL, value)


class SqlWhereNotEqual(SqlWhereCase):
    def __init__(self, key: str, value):
        super().__init__(key, SQLWHERETYPE.NOT_EQUAL, value)


class SqlWhereLess(SqlWhereCase):
    def __init__(self, key: str, value):
        super().__init__(key, SQLWHERETYPE.LESS, value)


class SqlWhereLessEqual(SqlWhereCase):
    def __init__(self, key: str, value):
        super().__init__(key, SQLWHERETYPE.LESS_EQUAL, value)


class SqlWhereGreater(SqlWhereCase):
    def __init__(self, key: str, value):
        super().__init__(key, SQLWHERETYPE.GREATER, value)


class SqlWhereGreaterEqual(SqlWhereCase):
    def __init__(self, key: str, value):
        super().__init__(key, SQLWHERETYPE.GREATER_EQUAL, value)


class SqlWhereIn(SqlWhereCase):
    def __init__(self, key: str, *list_value):
        super().__init__(key, SQLWHERETYPE.IN, list_value)


class SqlWhereNotIn(SqlWhereCase):
    def __init__(self, key: str, *list_value):
        super().__init__(key, SQLWHERETYPE.NOT_IN, list_value)


class SqlWhereBetween(SqlWhereCase):
    def __init__(self, key: str, left_value, right_value):
        super().__init__(key, SQLWHERETYPE.BETWEEN, dict(left=left_value, right=right_value))


class SqlWhereNotBetween(SqlWhereCase):
    def __init__(self, key: str, left_value, right_value):
        super().__init__(key, SQLWHERETYPE.NOT_BETWEEN, dict(left=left_value, right=right_value))


class SqlWhereLike(SqlWhereCase):
    def __init__(self, key: str, like_exp: str):
        super().__init__(key, SQLWHERETYPE.LIKE, like_exp)


class SqlWhereNotLike(SqlWhereCase):
    def __init__(self, key: str, like_exp: str):
        super().__init__(key, SQLWHERETYPE.NOT_LIKE, like_exp)


class SqlWhereBy(object):
    def __init__(self, key: str):
        self.__key__ = key

    def equal(self, value):
        return SqlWhereEqual(self.__key__, value)

    def __eq__(self, other):
        return self.equal(other)

    def not_equal(self, value):
        return SqlWhereNotEqual(self.__key__, value)

    def __ne__(self, other):
        return self.not_equal(other)

    def less(self, value):
        return SqlWhereLess(self.__key__, value)

    def __lt__(self, other):
        return self.less(other)

    def less_equal(self, value):
        return SqlWhereLessEqual(self.__key__, value)

    def __le__(self, other):
        return self.less_equal(other)

    def greater(self, value):
        return SqlWhereGreater(self.__key__, value)

    def __gt__(self, other):
        return self.greater(other)

    def greater_equal(self, value):
        return SqlWhereGreaterEqual(self.__key__, value)

    def __ge__(self, other):
        return self.greater_equal(other)

    def in_(self, *list_value):
        return SqlWhereIn(self.__key__, *list_value)

    def not_in(self, *list_value):
        return SqlWhereNotIn(self.__key__, *list_value)

    def between(self, left_value, right_value):
        return SqlWhereBetween(self.__key__, left_value, right_value)

    def not_between(self, left_value, right_value):
        return SqlWhereNotBetween(self.__key__, left_value, right_value)

    def like(self, like_exp: str):
        return SqlWhereLike(self.__key__, like_exp)

    def not_like(self, like_exp: str):
        return SqlWhereNotLike(self.__key__, like_exp)

    @classmethod
    def str(cls, str_where: str):
        return SqlWhereStr(str_where)


class SqlWhere(object):
    def __init__(self, *where_case, **kwargs):
        if where_case or kwargs:
            self.__where_note__ = reduce(SqlWhereAnd, self.format_list(*where_case) + SqlWhereCase.format_dict(**kwargs))
        else:
            self.__where_note__ = SqlWhereNull()

    def __bool__(self):
        return bool(self.__where_note__)

    def __len__(self):
        if self.__where_note__ is None:
            return 0
        return len(self.__where_note__)

    def __str__(self):
        if not self:
            return ''
        if len(self) == 1:
            return str(self.__where_note__)
        return '(' + str(self.__where_note__) + ')'

    def __eq__(self, other):
        return str(self) == str(other)

    def __and__(self, other):
        return SqlWhereAnd(self, other)

    def __or__(self, other):
        return SqlWhereOr(self, other)

    @classmethod
    def from_object(cls, _obj):
        if isinstance(_obj, (SqlWhereNode, SqlWhereCase, SqlWhere)):
            return _obj
        else:
            return SqlWhereCase.from_object(_obj)

    @classmethod
    def format_list(cls, *list_where):
        return [cls.from_object(each) for each in list_where]


@enum.unique
class SQLWHERENODETYPE(enum.Enum):
    AND = 1
    OR = 2

    __str_and__ = 'and'
    __str_or__ = 'or'

    def __str__(self):
        if self == SQLWHERENODETYPE.AND:
            return SQLWHERENODETYPE.__str_and__
        if self == SQLWHERENODETYPE.OR:
            return SQLWHERENODETYPE.__str_or__

    def __bool__(self):
        return self != SQLWHERENODETYPE.NULL

    @classmethod
    def from_str(cls, _str: str):
        _str = _str.strip().lower()
        if _str == SQLWHERENODETYPE.__str_and__:
            return SQLWHERENODETYPE.AND
        if _str == SQLWHERENODETYPE.__str_or__:
            return SQLWHERENODETYPE.OR
        raise ValueError


class SqlWhereNode(object):
    __default_type__ = SQLWHERENODETYPE.AND

    def __init__(self, left_where, note_type: SQLWHERENODETYPE, right_where):
        if isinstance(left_where, str):
            left_where = SqlWhereStr(left_where)
        if isinstance(right_where, str):
            right_where = SqlWhereStr(right_where)
        if not isinstance(left_where, (SqlWhereCase, SqlWhereNode, SqlWhere)):
            raise TypeError
        if not isinstance(right_where, (SqlWhereCase, SqlWhereNode, SqlWhere)):
            raise TypeError
        self.__left__ = left_where
        self.__note_type__ = note_type
        self.__right__ = right_where

    def __bool__(self):
        return bool(self.__left__) or bool(self.__right__)

    def __len__(self):
        length = 0
        if self.__left__:
            length += len(self.__left__)
        if self.__right__:
            length += len(self.__right__)
        return length

    def __and__(self, other):
        return SqlWhereAnd(self, other)

    def __or__(self, other):
        return SqlWhereOr(self, other)

    def __str__(self):
        if not self:
            return ''
        if self.__left__ and not self.__right__:
            return str(self.__left__)
        if not self.__left__ and self.__right__:
            return str(self.__right__)
        return '%s %s %s' % (self.__left__, self.__note_type__, self.__right__)

    def __eq__(self, other):
        return str(self) == str(other)


class SqlWhereAnd(SqlWhereNode):
    def __init__(self, left_where, right_where):
        super().__init__(left_where, SQLWHERENODETYPE.AND, right_where)


class SqlWhereOr(SqlWhereNode):
    def __init__(self, left_where, right_where):
        super().__init__(left_where, SQLWHERENODETYPE.OR, right_where)


class SqlSet(dict):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __str__(self):
        if not self:
            return ''
        return ','.join(['%s = %s' % (SqlKey(key), SqlValue(value)) for key, value in self.items()])

    def __setattr__(self, key, value):
        self[key] = value

    def __getattr__(self, item):
        return self[item]


class SqlKeyValue(SqlSet):
    def __str__(self):
        if not self:
            return ''
        keys = []
        values = []
        for key, value in self.items():
            keys.append(SqlKey(key))
            values.append(SqlValue(value))
        return '(%s) values (%s)' % \
                (','.join([str(key) for key in keys]), ','.join([str(value) for value in values]))


@enum.unique
class SQLMETHOD(enum.Enum):
    INSERT = 1
    DELETE = 2
    UPDATE = 3
    SELETE = 4

    __str_insert__ = 'insert'
    __str_delete__ = 'delete'
    __str_update__ = 'update'
    __str_select__ = 'select'

    def __str__(self):
        if self == self.INSERT:
            return self.__str_insert__
        if self == self.DELETE:
            return self.__str_delete__
        if self == self.UPDATE:
            return self.__str_update__
        if self == self.SELETE:
            return self.__str_select__

    @classmethod
    def from_str(cls, _str: str):
        _str = _str.strip().lower()
        if _str == cls.__str_insert__:
            return cls.INSERT
        if _str == cls.__str_delete__:
            return cls.DELETE
        if _str == cls.__str_update__:
            return cls.UPDATE
        if _str == cls.__str_select__:
            return cls.SELETE
        raise ValueError


class SqlMethod(object):
    def __init__(self, table_name='', method=None):
        self.__table__ = table_name
        self.__method__ = method

    def __bool__(self):
        return bool(self.__table__) and bool(self.__method__)

    def __str__(self):
        if not self:
            return ''
        return '%s from %s' % (self.__method__, self.__table__)

    def __eq__(self, other):
        return str(self) == str(other)


class SqlInsert(SqlMethod):
    def __init__(self, table_name: str, **kwargs):
        super().__init__(table_name, SQLMETHOD.INSERT)
        self.__insert__ = SqlKeyValue(**kwargs)

    def __bool__(self):
        return bool(self.__insert__) and super().__bool__()

    def __str__(self):
        if not self:
            return ''
        return '%s into %s %s' % (self.__method__, SqlKey(self.__table__), self.__insert__)


class SqlDelete(SqlMethod):
    def __init__(self, table_name: str):
        super().__init__(table_name, SQLMETHOD.DELETE)

    def __str__(self):
        return '%s from %s' % (self.__method__, SqlKey(self.__table__))


class SqlUpdate(SqlMethod):
    def __init__(self, table_name: str, **kwargs):
        super().__init__(table_name, SQLMETHOD.UPDATE)
        self.__update__ = SqlSet(**kwargs)

    def __bool__(self):
        return bool(self.__update__) and super().__bool__()

    def __str__(self):
        if not self:
            return ''
        return '%s %s set %s' % (self.__method__, SqlKey(self.__table__), self.__update__)


class SqlSelect(SqlMethod):
    def __init__(self, table_name: str, *list_select):
        super().__init__(table_name, SQLMETHOD.SELETE)
        self.__select__ = list_select

    def __str__(self):
        if self.__select__:
            return '%s %s from %s' % \
                   (self.__method__, ','.join([str(each) for each in self.__select__]), SqlKey(self.__table__))
        else:
            return '%s * from %s' % \
                   (self.__method__, SqlKey(self.__table__))


class SqlNode(dict):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __bool__(self):
        if 'method' in self and isinstance(self.method, SqlMethod):
            return True
        return False

    def __eq__(self, other):
        return str(self) == str(other)

    def __setattr__(self, key, value):
        self[key] = value

    def __getattr__(self, item):
        return self[item]

    def __str__(self):
        if not self:
            return ''
        #
        items = []
        #
        method = self.get('method')
        items.append(str(method))
        #
        if isinstance(method, SqlInsert):
            return items[0]

        where = self.get('where')
        if where:
            items.append('where %s' % where)

        if isinstance(method, (SqlDelete, SqlUpdate)):
            return ' '.join(items)

        order = self.get('order')
        if order:
            items.append('order by %s' % order)
        limit = self.get('limit')
        if limit:
            items.append('limit %s' % limit)
        return ' '.join(items)


class SqlFrom(object):
    def __init__(self, table: str):
        if not table:
            raise ValueError('empty table name')
        self.__sql__ = dict(table=table)

    def where(self, *where, **kwargs):
        self.__sql__.where = SqlWhere(*where, **kwargs)
        return self

    def and_where(self, *where, **kwargs):
        if 'where' in self.__sql__ and isinstance(self.__sql__.where, (SqlWhere, SqlWhereCase, SqlWhereNode)):
            self.__sql__.where &= SqlWhere(*where, **kwargs)
        return self

    def or_where(self, *where, **kwargs):
        if 'where' in self.__sql__ and isinstance(self.__sql__.where, (SqlWhere, SqlWhereCase, SqlWhereNode)):
            self.__sql__.where |= SqlWhere(*where, **kwargs)
        return self

    def order(self, *order, **kwargs):
        self.__sql__.order = SqlOrder(*order, **kwargs)
        return self

    def asc(self, column_name: str):
        if 'order' in self.__sql__ and isinstance(self.__sql__.order, SqlOrder):
            self.__sql__.order.asc(column_name)
        return self

    def desc(self, column_name: str):
        if 'order' in self.__sql__ and isinstance(self.__sql__.order, SqlOrder):
            self.__sql__.order.desc(column_name)
        return self

    def limit(self, top: int, skip=0):
        self.__sql__.limit = SqlLimit(top, skip)
        return self

    def top(self, top: int):
        if 'limit' in self.__sql__ and isinstance(self.__sql__.limit, SqlLimit):
            self.__sql__.limit.top(top)
        else:
            self.__sql__.limit = SqlLimit(top)
        return self

    def skip(self, skip: int):
        if 'limit' in self.__sql__ and isinstance(self.__sql__.limit, SqlLimit):
            self.__sql__.limit.skip(skip)
        else:
            self.__sql__.limit = SqlLimit(0, skip)
        return self

    def insert(self, **kwargs):
        self.__sql__.method = SqlInsert(self.__sql__.table, **kwargs)
        return SqlNode(**self.__sql__)

    def delete(self):
        self.__sql__.method = SqlDelete(self.__sql__.table)
        return SqlNode(**self.__sql__)

    def update(self, **kwargs):
        self.__sql__.method = SqlUpdate(self.__sql__.table, **kwargs)
        return SqlNode(**self.__sql__)

    def select(self, *select):
        self.__sql__.method = SqlSelect(self.__sql__.table, *select)
        return SqlNode(**self.__sql__)

    def clear(self):
        self.__sql__.clear()






