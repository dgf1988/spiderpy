# coding=utf-8
import enum
import functools


class SqlNode(object):
    """
    一切皆节点
    """
    def hash(self):
        return super().__hash__()

    def __hash__(self):
        return self.hash()

    def is_true(self) -> bool:
        """
        是否满足输出SQL语句的条件
        :return:
        """
        return False

    def __bool__(self):
        return self.is_true()

    def is_equal(self, other) -> bool:
        """
        节点比较器
        :param other:
        :return:
        """
        if isinstance(other, SqlNode):
            return self.to_sql() == other.to_sql()
        return False

    def __eq__(self, other):
        return self.is_equal(other)

    def to_dict(self) -> dict:
        """
        输出字典
        :return:
        """
        return dict()

    def to_sql(self) -> str:
        """
        输出SQL语句
        :return:
        """
        return ''

    def to_str(self) -> str:
        """
        输出字符串
        :return:
        """
        return str(self.to_dict())

    # for debug
    def __str__(self):
        return self.to_str()


class SqlNodeList(SqlNode):
    def __init__(self, *args):
        self.__nodes__ = list(args)

    @property
    def list(self):
        return self.__nodes__

    @property
    def type(self):
        return SqlNode

    def is_true(self):
        if not self.list:
            return False
        for each in self.list:
            if not isinstance(each, self.type):
                return False
            if not each.is_true():
                return False
        return True

    def is_equal(self, other):
        if isinstance(other, SqlNodeList):
            return self.list == other.list
        return super().is_equal(other)

    def to_dict(self):
        return dict(list=self.list)

    def to_sql(self):
        return ','.join([each.to_sql() for each in self.list if isinstance(each, self.type)])


class SqlNodeSet(SqlNodeList):
    def __init__(self, *args):
        super().__init__(*args)
        self.__nodes__ = set(self.__nodes__)

    @property
    def set(self):
        return self.__nodes__

    def to_dict(self):
        return dict(set=self.set)


class SqlNodeStr(SqlNode):
    def __init__(self, str_raw: str):
        self.__str_raw__ = str_raw

    @property
    def str(self):
        return self.__str_raw__

    def is_true(self):
        return bool(self.str)

    def is_equal(self, other):
        if isinstance(other, SqlNodeStr):
            return self.str == other.str
        if isinstance(other, str):
            return self.str == other
        return super().is_equal(other)

    def to_dict(self):
        return dict(str=self.str)

    def to_sql(self):
        return self.str


class SqlKey(SqlNode):
    def __init__(self, key: str=''):
        self.__key__ = key

    @property
    def key(self):
        return self.__key__

    def hash(self):
        return hash(self.key)

    def is_true(self):
        return bool(self.key)

    def is_equal(self, other):
        if isinstance(other, SqlKey):
            return self.key == other.key
        return super().is_equal(other)

    def to_dict(self):
        return dict(key=self.key)

    def to_sql(self):
        return '`%s`' % self.key


class SqlValue(SqlNode):
    def __init__(self, value=None):
        self.__value__ = value

    @property
    def value(self):
        return self.__value__

    def is_true(self):
        return True

    def is_equal(self, other):
        if isinstance(other, SqlValue):
            return self.value == other.value
        return super().is_equal(other)

    def to_dict(self):
        return dict(value=self.value)

    def to_sql(self):
        if self.value is None:
            return 'NULL'
        if isinstance(self.value, (int, float)):
            return str(self.value)
        if isinstance(self.value, SqlNode):
            return self.value.to_sql()
        return '"%s"' % self.value


class SqlValueList(SqlNodeList):
    def __init__(self, *value_list):
        super().__init__(*[SqlValue(value_list)])

    @property
    def type(self):
        return SqlValue

    def to_sql(self):
        return '(' + super().to_sql() + ')'


class SqlKeyValue(SqlNode):
    def __init__(self, key: str='', value=None):
        self.__key__ = SqlKey(key)
        self.__value__ = SqlValue(value)

    @property
    def key(self):
        return self.__key__

    @property
    def value(self):
        return self.__value__

    def hash(self):
        return hash(self.key.key + self.value.__str__())

    def is_true(self):
        return self.key.is_true() and self.value.is_true()

    def is_equal(self, other):
        if isinstance(other, SqlKeyValue):
            return self.key.is_equal(other.key) and self.value.is_equal(other.value)
        return super().is_equal(other)

    def to_dict(self):
        return dict(key=self.key, value=self.value)

    def to_sql(self):
        return '%s = %s' % (self.key.to_sql(), self.value.to_sql())


class SqlKeyValueSet(SqlNodeSet):
    def __init__(self, **kwargs):
        super().__init__(*[SqlKeyValue(key, value) for key, value in kwargs.items()])

    @property
    def type(self):
        return SqlKeyValue


class SqlTable(SqlKey):
    @property
    def table(self):
        return self.key

    def is_equal(self, other):
        if isinstance(other, SqlTable):
            return self.table == other.table
        return super().is_equal(other)

    def to_dict(self):
        return dict(table=self.table)


class SqlTableSet(SqlNodeSet):
    def __init__(self, *keys):
        super().__init__(*[SqlTable(key) for key in keys])

    @property
    def type(self):
        return SqlTable


class SqlLimit(SqlNode):
    def __init__(self, top: int=0, skip: int=0):
        self.__top__ = top
        self.__skip__ = skip

    @property
    def top(self):
        return self.__top__

    @property
    def skip(self):
        return self.__skip__

    def is_true(self):
        return self.top > 0 or self.skip > 0

    def is_equal(self, other):
        if isinstance(other, SqlLimit):
            return self.top == other.top and self.skip == other.skip
        return super().is_equal(other)

    def to_dict(self):
        return dict(top=self.top, skip=self.skip)

    def to_sql(self):
        return '%s,%s' % (self.top, self.skip)


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
        return dict(order=self)

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


class SqlOrder(SqlNode):
    def __init__(self, key: str='', order: SQLORDER=SQLORDER.ASC):
        self.__key__ = SqlKey(key)
        self.__order__ = order

    @property
    def key(self):
        return self.__key__

    @property
    def order(self):
        return self.__order__

    def asc(self, key: str):
        return SqlOrderList(self, SqlOrderAsc(key))

    def desc(self, key: str):
        return SqlOrderList(self, SqlOrderDesc(key))

    def is_true(self):
        return self.key.is_true() and self.order.is_true()

    def is_equal(self, other):
        if isinstance(other, SqlOrder):
            return self.key.is_equal(other.key) and self.order.is_equal(other.order)
        return super().is_equal(other)

    def to_dict(self):
        return dict(key=self.key, order=self.order)

    def to_sql(self):
        return '%s %s' % (self.key.to_sql(), self.order.to_sql())


class SqlOrderAsc(SqlOrder):
    def __init__(self, key: str):
        super().__init__(key)


class SqlOrderDesc(SqlOrder):
    def __init__(self, key: str):
        super().__init__(key, SQLORDER.DESC)


class SqlOrderList(SqlNodeList):
    def __init__(self, *orders):
        super().__init__(*orders)

    @property
    def type(self):
        return SqlOrder

    def asc(self, key: str):
        self.list.append(SqlOrderAsc(key))
        return self

    def desc(self, key: str):
        self.list.append(SqlOrderDesc(key))
        return self


@enum.unique
class SQLWHERE(enum.Enum):

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

    AND = 21
    __str_and__ = 'and'
    OR = 22
    __str_or__ = 'or'
    SUB = 31
    STR = 32
    NULL = 41
    TRUE = 42

    def is_true(self):
        return self != self.NULL

    def is_equal(self, other):
        return self == other

    def to_dict(self):
        return dict(where=self)

    def to_sql(self):
        if self == self.EQUAL:
            return self.__str_equal__
        if self == self.NOT_EQUAL:
            return self.__str_not_equal__
        if self == self.LESS:
            return self.__str_less__
        if self == self.LESS_EQUAL:
            return self.__str_less_equal__
        if self == self.GREATER:
            return self.__str_greater__
        if self == self.GREATER_EQUAL:
            return self.__str_greater_equal__
        if self == self.IN:
            return self.__str_in__
        if self == self.NOT_IN:
            return self.__str_not_in__
        if self == self.BETWEEN:
            return self.__str_between__
        if self == self.NOT_BETWEEN:
            return self.__str_not_between__
        if self == self.LIKE:
            return self.__str_like__
        if self == self.NOT_LIKE:
            return self.__str_not_like__
        if self == self.AND:
            return self.__str_and__
        if self == self.OR:
            return self.__str_or__

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


class SqlWhereTree(SqlNode):
    def __init__(self, type: SQLWHERE=SQLWHERE.NULL, left_child: SqlNode=SqlNode(), right_child: SqlNode=SqlNode()):
        self.__left__ = left_child
        self.__right__ = right_child
        self.__type__ = type

    @property
    def left(self):
        return self.__left__

    @property
    def right(self):
        return self.__right__

    @property
    def type(self):
        return self.__type__

    def is_true(self):
        return self.type.is_true() and self.left.is_true()

    def to_dict(self):
        return dict(type=self.type, left=self.left, right=self.right)


class SqlWhereNull(SqlWhereTree):
    def __init__(self):
        super().__init__()

    def is_true(self):
        return False


class SqlWhereTrue(SqlWhereTree):
    def __init__(self):
        super().__init__(type=SQLWHERE.TRUE)

    def is_true(self):
        return True

    def to_sql(self):
        return '1'


class SqlWhereStr(SqlWhereTree):
    def __init__(self, str_where: str):
        super().__init__(type=SQLWHERE.STR, left_child=SqlNodeStr(str_where))

    def is_equal(self, other):
        if isinstance(other, str):
            return self.left.to_sql() == other
        return super().is_equal(other)

    def to_sql(self):
        return self.left.to_sql()


class SqlWhereNode(SqlWhereTree):
    def __init__(self, type: SQLWHERE.AND, left: SqlNode=SqlNode(), right: SqlNode=SqlNode()):
        super().__init__(type=type, left_child=left, right_child=right)

    def is_true(self):
        return super().is_true() and self.right.is_true()

    def to_sql(self):
        return '%s %s %s' % (self.left.to_sql(), self.type.to_sql(), self.right.to_sql())


class SqlWhereExpression(SqlWhereTree):
    def __init__(self, type=SQLWHERE.EQUAL, left: SqlKey=SqlKey(), right: SqlNode=SqlValue()):
        super().__init__(type, left, right)

    def is_equal(self, other):
        if isinstance(other, SqlWhereExpression):
            return self.left.is_equal(other.left) and \
                   self.type.is_equal(other.type) and \
                   self.right.is_equal(other.right)
        return super().is_equal(other)

    def to_sql(self):
        return '%s %s %s' % (self.left.to_sql(), self.type.to_sql(), self.right.to_sql())


class SqlWhereEqual(SqlWhereExpression):
    def __init__(self, key: str, value):
        super().__init__(SQLWHERE.EQUAL, SqlKey(key), SqlValue(value))


class SqlWhereNotEqual(SqlWhereExpression):
    def __init__(self, key: str, value):
        super().__init__(SQLWHERE.NOT_EQUAL, SqlKey(key), SqlValue(value))


class SqlWhereLess(SqlWhereExpression):
    def __init__(self, key: str, value):
        super().__init__(SQLWHERE.LESS, SqlKey(key), SqlValue(value))


class SqlWhereLessEqual(SqlWhereExpression):
    def __init__(self, key: str, value):
        super().__init__(SQLWHERE.LESS_EQUAL, SqlKey(key), SqlValue(value))


class SqlWhereGreater(SqlWhereExpression):
    def __init__(self, key: str, value):
        super().__init__(SQLWHERE.GREATER, SqlKey(key), SqlValue(value))


class SqlWhereGreaterEqual(SqlWhereExpression):
    def __init__(self, key: str, value):
        super().__init__(SQLWHERE.GREATER_EQUAL, SqlKey(key), SqlValue(value))


class SqlWhereIn(SqlWhereExpression):
    def __init__(self, key: str, *list_value):
        super().__init__(SQLWHERE.IN, SqlKey(key), SqlValueList(*list_value))


class SqlWhereNotIn(SqlWhereIn):
    def __init__(self, key: str, *list_value):
        super().__init__(key, *list_value)
        self.__type__ = SQLWHERE.NOT_IN


class SqlWhereBetween(SqlWhereExpression):
    def __init__(self, key: str, left_value, right_value):
        super().__init__(SQLWHERE.BETWEEN, SqlKey(key),
                         SqlWhereTree(SQLWHERE.AND, left_child=SqlValue(left_value), right_child=SqlValue(right_value)))


class SqlWhereNotBetween(SqlWhereBetween):
    def __init__(self, key: str, left_value, right_value):
        super().__init__(key, left_value, right_value)
        self.__type__ = SQLWHERE.NOT_BETWEEN


class SqlWhereLike(SqlWhereExpression):
    def __init__(self, key: str, like_exp: str):
        super().__init__(SQLWHERE.LIKE, SqlKey(key), SqlValue(like_exp))


class SqlWhereNotLike(SqlWhereExpression):
    def __init__(self, key: str, like_exp: str):
        super().__init__(SQLWHERE.NOT_LIKE, SqlKey(key), SqlValue(like_exp))



