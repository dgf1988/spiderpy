# coding=utf-8
import enum
from functools import reduce


class SqlObject(object):
    """
    Sql对象的基类。
    """

    # 基类实例永远为假
    def is_true(self):
        """
        是否可以输出合法的Sql语句
        :return:
        """
        return False

    def __bool__(self):
        return self.is_true()

    # 基类比较永远返回假
    def is_equal(self, other):
        """
        SQL默认比较器。
        :param other:
        :return:
        """
        return False

    def __eq__(self, other):
        return self.is_equal(other)

    # 字典为空
    def to_dict(self):
        """
        输出字典
        :return:
        """
        return {}

    # 输出的语句为空
    def to_sql(self):
        """
        输出SQL语句。
        :return:
        """
        return ''


class SqlKey(SqlObject):
    def __init__(self, key: str):
        if not key:
            raise ValueError('empty key value')
        self.__key__ = key

    def is_equal(self, other):
        if isinstance(other, SqlKey):
            return self.__key__ == other.__key__
        return super().is_equal(other)

    def is_true(self):
        return bool(self.__key__)

    def to_dict(self):
        return dict(key=self.__key__)

    def to_sql(self):
        return '`%s`' % self.__key__


class SqlValue(SqlObject):
    def __init__(self, value):
        self.__value__ = value

    def is_equal(self, other):
        if isinstance(other, SqlValue):
            return self.__value__ == other.__value__
        return super().is_equal(other)

    def is_true(self):
        if self.__value__ in ('',):
            return False
        return True

    def to_dict(self):
        return dict(value=self.__value__)

    def to_sql(self):
        if self.__value__ is None:
            return 'NULL'
        if isinstance(self.__value__, (int, float)):
            return '%s' % self.__value__
        if isinstance(self.__value__, SqlObject):
            return self.__value__.to_sql()
        return '"%s"' % self.__value__


@enum.unique
class SQLORDER(enum.Enum):
    ASC = 0
    DESC = 1
    __str_asc__ = 'asc'
    __str_desc__ = 'desc'

    def is_equal(self, other):
        return self == other

    def is_true(self):
        return bool(self)

    def to_dict(self):
        return dict(order=self.to_sql())

    def to_sql(self):
        if self == self.ASC:
            return self.__str_asc__
        if self == self.DESC:
            return self.__str_desc__

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


class SqlOrderCase(SqlObject):

    def __init__(self, key: str, order: SQLORDER=SQLORDER.ASC):
        self.__key__ = SqlKey(key)
        self.__order__ = order

    def is_equal(self, other):
        if isinstance(other, SqlOrderCase):
            return self.__key__.is_equal(other.__key__) and self.__order__ == other.__order__
        return super().is_equal(other)

    def is_true(self):
        return self.__key__.is_true() and self.__order__.is_true()

    def to_dict(self):
        return dict(key=self.__key__, order=self.__order__)

    def to_sql(self):
        return '%s %s' % (self.__key__.to_sql(), self.__order__.to_sql())

    @classmethod
    def from_str_key(cls, key: str):
        return cls(key)

    @classmethod
    def from_dict(cls, **kwargs):
        if 'key' in kwargs and ('value' in kwargs or 'order' in kwargs):
            key = kwargs.get('key')
            order = kwargs.get('order') or kwargs.get('value')
        else:
            key, order = kwargs.popitem()
        return cls(key, SQLORDER.from_object(order))

    @classmethod
    def from_object(cls, _obj):
        if isinstance(_obj, str):
            return cls.from_str_key(_obj)
        if isinstance(_obj, dict):
            return cls.from_dict(**_obj)
        if isinstance(_obj, cls):
            return _obj
        raise TypeError

    @classmethod
    def format_list(cls, *list_order) -> list:
        return [cls.from_object(each) for each in list_order]


class SqlOrderDesc(SqlOrderCase):
    def __init__(self, key: str):
        super().__init__(key, SQLORDER.DESC)


class SqlOrderAsc(SqlOrderCase):
    def __init__(self, key: str):
        super().__init__(key, SQLORDER.ASC)


class SqlOrderBy(object):

    def __init__(self, key: str):
        self.__sql_key__ = SqlKey(key)

    def desc(self):
        return SqlOrderDesc(self.__sql_key__.__key__)

    def asc(self):
        return SqlOrderAsc(self.__sql_key__.__key__)


class SqlOrder(list, SqlObject):
    def __init__(self, *list_order_case):
        super().__init__(SqlOrderCase.format_list(*list_order_case))

    def is_equal(self, other):
        if isinstance(other, list):
            return self == other
        return super().is_equal(other)

    def is_true(self):
        return bool(len(self))

    def to_dict(self):
        return dict(order=self)

    def to_sql(self):
        return ','.join([order_case.to_sql() for order_case in self])

    def asc(self, column_name: str):
        self.append(SqlOrderAsc(column_name))
        return self

    def desc(self, column_name: str):
        self.append(SqlOrderDesc(column_name))
        return self


class SqlLimit(SqlObject):
    def __init__(self, top: int=0, skip: int=0):
        if not isinstance(top, int) or not isinstance(skip, int) or top < 0 or skip < 0:
            raise ValueError
        self.__top__ = top
        self.__skip__ = skip

    def is_equal(self, other):
        if isinstance(other, SqlLimit):
            return self.__top__ == other.__top__ and self.__skip__ == other.__skip__
        return super().is_equal(other)

    def is_true(self):
        """
        判断限制是否存在
        :return:
        """
        return self.__top__ > 0 and self.__skip__ >= 0

    def to_dict(self):
        return dict(top=self.__top__, skip=self.__skip__)

    def to_sql(self):
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
class SQLWHEREOPERATION(enum.Enum):
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
    __str_not_equal__ = '!='

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

    def is_true(self):
        return True

    def is_equal(self, other):
        return self == other

    def to_dict(self):
        return dict(operation=self.to_sql())

    def to_sql(self):
        if self == SQLWHEREOPERATION.EQUAL:
            return SQLWHEREOPERATION.__str_equal__
        if self == SQLWHEREOPERATION.NOT_EQUAL:
            return SQLWHEREOPERATION.__str_not_equal__
        if self == SQLWHEREOPERATION.LESS:
            return SQLWHEREOPERATION.__str_less__
        if self == SQLWHEREOPERATION.LESS_EQUAL:
            return SQLWHEREOPERATION.__str_less_equal__
        if self == SQLWHEREOPERATION.GREATER:
            return SQLWHEREOPERATION.__str_greater__
        if self == SQLWHEREOPERATION.GREATER_EQUAL:
            return SQLWHEREOPERATION.__str_greater_equal__
        if self == SQLWHEREOPERATION.IN:
            return SQLWHEREOPERATION.__str_in__
        if self == SQLWHEREOPERATION.NOT_IN:
            return SQLWHEREOPERATION.__str_not_in__
        if self == SQLWHEREOPERATION.BETWEEN:
            return SQLWHEREOPERATION.__str_between__
        if self == SQLWHEREOPERATION.NOT_BETWEEN:
            return SQLWHEREOPERATION.__str_not_between__
        if self == SQLWHEREOPERATION.LIKE:
            return SQLWHEREOPERATION.__str_like__
        if self == SQLWHEREOPERATION.NOT_LIKE:
            return SQLWHEREOPERATION.__str_not_like__

    @classmethod
    def from_str(cls, op: str):
        op = op.strip().lower()
        if op == cls.__str_equal__:
            return cls.EQUAL
        if op == cls.__str_not_equal__:
            return cls.NOT_EQUAL
        if op == cls.__str_less__:
            return cls.LESS
        if op == cls.__str_less_equal__:
            return cls.LESS_EQUAL
        if op == cls.__str_greater__:
            return cls.GREATER
        if op == cls.__str_greater_equal__:
            return cls.GREATER_EQUAL
        if op == cls.__str_in__:
            return cls.IN
        if op == cls.__str_not_in__:
            return cls.NOT_IN
        if op == cls.__str_between__:
            return cls.BETWEEN
        if op == cls.__str_not_between__:
            return cls.NOT_BETWEEN
        if op == cls.__str_like__:
            return cls.LIKE
        if op == cls.__str_not_like__:
            return cls.NOT_LIKE


class SqlWhereObject(SqlObject):

    def length(self):
        return 0

    def __len__(self):
        return self.length()

    def and_(self, other):
        if isinstance(other, SqlWhereObject):
            return SqlWhereAnd(self, other)
        raise TypeError

    def __and__(self, other):
        return self.and_(other)

    def or_(self, other):
        if isinstance(other, SqlWhereObject):
            return SqlWhereOr(self, other)
        raise TypeError

    def __or__(self, other):
        return self.or_(other)

    def is_true(self):
        return False

    def is_equal(self, other):
        if isinstance(other, SqlWhereObject):
            return self.to_sql() == other.to_sql()
        return super().is_equal(other)


class SqlWhereNull(SqlWhereObject):
    pass


class SqlWhereStr(SqlWhereObject):
    def __init__(self, str_where: str):
        if not str_where:
            raise ValueError('str_where is empty')
        self.__where_str__ = str_where

    def length(self):
        return int(self.is_true())

    def is_true(self):
        return bool(self.__where_str__)

    def to_dict(self):
        return dict(sql=self.__where_str__)

    def to_sql(self):
        return self.__where_str__


class SqlWhereOperation(SqlWhereObject):

    def __init__(self, key: str, operation: SQLWHEREOPERATION=SQLWHEREOPERATION.EQUAL, value=None):
        self.__key__ = SqlKey(key)
        self.__operation__ = operation
        self.__value__ = value

    @property
    def key(self):
        return self.__key__

    @key.setter
    def key(self, key: str):
        self.__key__ = SqlKey(key)

    def length(self):
        return int(self.is_true())

    def is_true(self):
        return self.__key__.is_true() and self.__operation__.is_true()

    def to_dict(self):
        return dict(key=self.__key__, operation=self.__operation__, value=self.__value__)

    def to_sql(self):
        return '%s %s %s' % (self.__key__.to_sql(),
                             self.__operation__.to_sql(),
                             SqlValue(self.__value__).to_sql())


class SqlWhereEqual(SqlWhereOperation):
    def __init__(self, key: str, value):
        super().__init__(key, SQLWHEREOPERATION.EQUAL, value)


class SqlWhereNotEqual(SqlWhereOperation):
    def __init__(self, key: str, value):
        super().__init__(key, SQLWHEREOPERATION.NOT_EQUAL, value)


class SqlWhereLess(SqlWhereOperation):
    def __init__(self, key: str, value):
        super().__init__(key, SQLWHEREOPERATION.LESS, value)


class SqlWhereLessEqual(SqlWhereOperation):
    def __init__(self, key: str, value):
        super().__init__(key, SQLWHEREOPERATION.LESS_EQUAL, value)


class SqlWhereGreater(SqlWhereOperation):
    def __init__(self, key: str, value):
        super().__init__(key, SQLWHEREOPERATION.GREATER, value)


class SqlWhereGreaterEqual(SqlWhereOperation):
    def __init__(self, key: str, value):
        super().__init__(key, SQLWHEREOPERATION.GREATER_EQUAL, value)


class SqlWhereIn(SqlWhereOperation):
    def __init__(self, key: str, *list_value):
        super().__init__(key, SQLWHEREOPERATION.IN, list_value)

    def to_sql(self):
        return '%s %s (%s)' % (self.__key__.to_sql(),
                               self.__operation__.to_sql(),
                               ','.join([SqlValue(value).to_sql() for value in self.__value__]))


class SqlWhereNotIn(SqlWhereIn):
    def __init__(self, key: str, *list_value):
        super().__init__(key, *list_value)
        self.__operation__ = SQLWHEREOPERATION.NOT_IN


class SqlWhereBetween(SqlWhereOperation):
    def __init__(self, key: str, left_value, right_value):
        super().__init__(key, SQLWHEREOPERATION.BETWEEN, dict(left=left_value, right=right_value))

    def to_sql(self):
        return '%s %s %s and %s' % (self.__key__.to_sql(),
                                    self.__operation__.to_sql(),
                                    SqlValue(self.__value__.get('left')).to_sql(),
                                    SqlValue(self.__value__.get('right')).to_sql())


class SqlWhereNotBetween(SqlWhereBetween):
    def __init__(self, key: str, left_value, right_value):
        super().__init__(key, left_value, right_value)
        self.__operation__ = SQLWHEREOPERATION.NOT_BETWEEN


class SqlWhereLike(SqlWhereOperation):
    def __init__(self, key: str, like_exp: str):
        super().__init__(key, SQLWHEREOPERATION.LIKE, like_exp)


class SqlWhereNotLike(SqlWhereOperation):
    def __init__(self, key: str, like_exp: str):
        super().__init__(key, SQLWHEREOPERATION.NOT_LIKE, like_exp)


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


@enum.unique
class SQLWHERENODE(enum.Enum):
    AND = 1
    OR = 2

    __str_and__ = 'and'
    __str_or__ = 'or'

    def is_true(self):
        return bool(self)

    def is_equal(self, other):
        return self == other

    def to_dict(self):
        return dict(node=self.to_sql())

    def to_sql(self):
        if self == SQLWHERENODE.AND:
            return SQLWHERENODE.__str_and__
        if self == SQLWHERENODE.OR:
            return SQLWHERENODE.__str_or__

    @classmethod
    def from_str(cls, _str: str):
        _str = _str.strip().lower()
        if _str == SQLWHERENODE.__str_and__:
            return SQLWHERENODE.AND
        if _str == SQLWHERENODE.__str_or__:
            return SQLWHERENODE.OR
        raise ValueError


class SqlWhereNode(SqlWhereObject):

    def __init__(self, note: SQLWHERENODE=SQLWHERENODE.AND,
                 left_where: SqlWhereObject=SqlWhereNull(),
                 right_where: SqlWhereObject=SqlWhereNull()):
        self.__note__ = note
        self.__left__ = left_where
        self.__right__ = right_where

    def length(self):
        return self.__left__.length() + self.__right__.length()

    def is_true(self):
        return self.__left__.is_true() or self.__right__.is_true()

    def to_dict(self):
        return dict(note=self.__note__, left=self.__left__, right=self.__right__)

    def to_sql(self):
        if self.__left__.is_true() and not self.__right__.is_true():
            return self.__left__.to_sql()
        if not self.__left__.is_true() and self.__right__.is_true():
            return self.__right__.to_sql()
        return '%s %s %s' % (self.__left__.to_sql(),
                             self.__note__.to_sql(),
                             self.__right__.to_sql())


class SqlWhereAnd(SqlWhereNode):
    def __init__(self, left_where, right_where):
        super().__init__(SQLWHERENODE.AND, left_where, right_where)


class SqlWhereOr(SqlWhereNode):
    def __init__(self, left_where, right_where):
        super().__init__(SQLWHERENODE.OR, left_where, right_where)


class SqlWhere(SqlWhereObject):
    def __init__(self, *list_where, **kwargs):
        if list_where or kwargs:
            self.__where__ = reduce(SqlWhereAnd, self.format_list(*list_where) + self.format_dict(**kwargs))
        else:
            self.__where__ = SqlWhereNull()

    def length(self):
        return self.__where__.length()

    def is_true(self):
        if isinstance(self.__where__, SqlWhereObject):
            return self.__where__.is_true()
        return super().is_true()

    def to_dict(self):
        return dict(where=self.__where__)

    def to_sql(self):
        if self.length() <= 1:
            return self.__where__.to_sql()
        else:
            return '(' + self.__where__.to_sql() + ')'

    @classmethod
    def from_str(cls, _str: str):
        if not _str:
            return SqlWhereNull()
        return SqlWhereStr(_str)

    @classmethod
    def from_dict(cls, **kwargs):
        operation = SQLWHEREOPERATION.EQUAL
        if not kwargs:
            return SqlWhereNull()
        if kwargs.__len__() == 1:
            key, value = kwargs.popitem()
        else:
            key = kwargs.get('key')
            value = kwargs.get('value')
            operation = kwargs.get('operation', SQLWHEREOPERATION.EQUAL)
            if isinstance(operation, str):
                operation = SQLWHEREOPERATION.from_str(operation)
            elif not isinstance(operation, SQLWHEREOPERATION):
                raise TypeError
        return SqlWhereOperation(key, operation, value)

    @classmethod
    def from_object(cls, obj):
        if isinstance(obj, str):
            return cls.from_str(obj)
        if isinstance(obj, dict):
            return cls.from_dict(**obj)
        if isinstance(obj, SqlWhereObject):
            return obj
        raise TypeError

    @classmethod
    def format_list(cls, *list_where) ->list:
        return [cls.from_object(obj) for obj in list_where]

    @classmethod
    def format_dict(cls, **kwargs):
        return [SqlWhereEqual(key, value) for key, value in kwargs.items()]


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


class SqlQuery(dict):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __bool__(self):
        if 'method' in self and isinstance(self.method, SqlMethod):
            return True
        return False

    def __setattr__(self, key, value):
        self[key] = value

    def __getattr__(self, item):
        return self[item]

    def to_sql(self):
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
        self.__sql__ = SqlQuery(table=table)

    def where(self, *where, **kwargs):
        self.__sql__.where = SqlWhere(*where, **kwargs)
        return self

    def and_where(self, *where, **kwargs):
        if 'where' in self.__sql__ and isinstance(self.__sql__.where, (SqlWhere, SqlWhereOperation, SqlWhereNode)):
            self.__sql__.where &= SqlWhere(*where, **kwargs)
        return self

    def or_where(self, *where, **kwargs):
        if 'where' in self.__sql__ and isinstance(self.__sql__.where, (SqlWhere, SqlWhereOperation, SqlWhereNode)):
            self.__sql__.where |= SqlWhere(*where, **kwargs)
        return self

    def order(self, *order):
        self.__sql__.order = SqlOrder(*order)
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
        return SqlQuery(**self.__sql__)

    def delete(self):
        self.__sql__.method = SqlDelete(self.__sql__.table)
        return SqlQuery(**self.__sql__)

    def update(self, **kwargs):
        self.__sql__.method = SqlUpdate(self.__sql__.table, **kwargs)
        return SqlQuery(**self.__sql__)

    def select(self, *select):
        self.__sql__.method = SqlSelect(self.__sql__.table, *select)
        return SqlQuery(**self.__sql__)

    def clear(self):
        self.__sql__.clear()






