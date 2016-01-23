# coding=utf-8
import enum
"""
    SqlObject To Sql

    1、将Sql语句抽象为SqlNode(Sql节点)， 一条Sql语句就是树结构的节点集合。
    2、通过SqlNode实例出SqlObject，通过SqlObject输出Sql语句。
    3、SqlFrom 是编程接口， 通过SqlFrom可以方便实例出SqlObject。

    date: 2016年1月4日
    by: dgf1988
    email: dgf1988@qq.com
"""


class Node(object):
    """
    1、一切皆节点
    2、所有节点都从这开始继承
    3、每一句SQL都是一个节点，每一个节点下都有多个或一个子节点，每一个子节点都是SQL的子句。
    4、每一条SQL语句都抽象为一个类，每一条SQL子句都抽象为一个类。
    5、SQL语句之间的拼接合并由类的方法提供。
    """
    def hash(self):
        """
        用以支持集合和字典
        :return:
        """
        return hash(self.to_sql())

    def __hash__(self):
        return self.hash()

    def is_true(self) -> bool:
        """
        是否能够输出合法能用的SQL语句
        :return:
        """
        return False

    def __bool__(self):
        return self.is_true()

    def is_equal(self, other) -> bool:
        """
        节点的基础比较器
        :param other:
        :return:
        """
        if isinstance(other, Node):
            return self.to_sql() == other.to_sql()
        if isinstance(other, str):
            return self.to_sql() == other
        return False

    def __eq__(self, other):
        return self.is_equal(other)

    def to_dict(self) -> dict:
        """
        输出节点的字典
        :return:
        """
        return dict()

    def to_sql(self) -> str:
        """
        输出节点的SQL语句
        :return:
        """
        return ''

    def __str__(self):
        return '<Sql: %s>' % (self.to_sql())

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.to_sql())


class Str(Node):
    def __init__(self, str_arg: str):
        self._str = str_arg

    @property
    def str(self):
        return self._str

    @str.setter
    def str(self, str_arg: str):
        self._str = str_arg

    def hash(self):
        return hash(self.str)

    def is_true(self):
        return bool(self.str)

    def is_equal(self, other):
        return self.str == other.str if isinstance(other, Str) else super().is_equal(other)

    def to_dict(self):
        return dict(str=self.str)

    def to_sql(self):
        return self.str


class Key(Str):
    def __init__(self, key: str):
        if not key:
            raise ValueError('the key value is empty!')
        super().__init__(key)

    @property
    def key(self):
        return self.str

    @key.setter
    def key(self, key: str):
        if not key:
            raise ValueError('the key value is empty!')
        self.str = key

    def to_dict(self):
        return dict(key=self.key)

    def to_sql(self):
        return '`%s`' % super().to_sql()


class Value(Node):
    def __init__(self, value=None):
        self._value = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value

    def hash(self):
        return hash(self.value)

    def is_true(self):
        return True

    def is_equal(self, other):
        return self.value == other.value if isinstance(other, Value) else super().is_equal(other)

    def to_dict(self):
        return dict(value=self.value)

    def to_sql(self):
        if self.value is None:
            return 'NULL'
        if isinstance(self.value, (int, float)):
            return str(self.value)
        if isinstance(self.value, Node):
            return self.value.to_sql()
        return '"%s"' % self.value.__str__()


class KeyValue(Node):
    def __init__(self, key: str, value=None):
        self._key = Key(key)
        self._value = Value(value)

    @property
    def key(self):
        return self._key

    @key.setter
    def key(self, key: str):
        self._key = Key(key)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = Value(value)

    def hash(self):
        return self.key.hash()

    def is_true(self):
        return self.key.is_true()

    def is_equal(self, other):
        if isinstance(other, KeyValue):
            return self.key.is_equal(other.key) and self.value.is_equal(other.value)
        return super().is_equal(other)

    def to_dict(self):
        return dict(key=self.key, value=self.value)

    def to_sql(self):
        return '%s = %s' % (self.key.to_sql(), self.value.to_sql())

    def to_iter(self):
        yield self.key
        yield self.value

    def __iter__(self):
        return self.to_iter()


class Table(Key):
    @property
    def name(self):
        return self.key

    @name.setter
    def name(self, name: str):
        self.key = name

    def to_dict(self):
        return dict(name=self.name)


class Set(Node):
    def __init__(self, *args):
        self._set = set(args)

    @property
    def set(self):
        return self._set

    def len(self):
        return len(self.set)

    def items(self):
        return self.set

    def add(self, arg):
        self.set.add(arg)

    def remove(self, arg):
        self.set.remove(arg)

    def pop(self):
        return self.set.pop()

    def update(self, *args):
        self.set.update(*args)

    def has(self, arg):
        return self.set.__contains__(arg)

    def __contains__(self, item):
        return self.has(item)

    def is_true(self):
        return bool(self.set)

    def is_equal(self, other):
        return self.set == other.set if isinstance(other, Set) else super().is_equal(other)

    def to_dict(self):
        return dict(set=self.set)

    def to_sql(self):
        return ', '.join(item.to_sql() if isinstance(item, Node) else str(item) for item in self.set)

    def __iter__(self):
        for item in self.set:
            yield item


class KeySet(Set):
    def __init__(self, *keys):
        super().__init__(*(k if isinstance(k, Key) else Key(k) if isinstance(k, str) else Key(str(k)) for k in keys))


class ValueSet(Set):
    def __init__(self, *values):
        super().__init__(*(v if isinstance(v, Value) else Value(v) for v in values))

    def to_sql(self):
        return '( %s )' % super().to_sql()


class Sets(Node):
    def __init__(self, **kwargs):
        self.__sets__ = dict(**kwargs)

    @property
    def sets(self):
        return self.__sets__

    def set(self, **kwargs):
        self.sets.update(**kwargs)

    def pop(self, key: str, default=None):
        return self.sets.pop(key, default)

    def is_true(self):
        return bool(self.sets)

    def is_equal(self, other):
        if isinstance(other, Sets):
            return self.sets == other.sets
        return super().is_equal(other)

    def to_dict(self):
        return self.sets

    def to_sql(self):
        return ','.join([KeyValue(k, v).to_sql() for k, v in self.sets.items()])


class List(Node):
    def __init__(self, *args):
        self._list = list(args)

    @property
    def list(self):
        return self._list

    def len(self):
        return len(self.list)

    def items(self):
        return self.list

    def add(self, arg):
        self.list.append(arg)

    def is_true(self):
        return bool(self.list)

    def is_equal(self, other):
        return self.list == other.list if isinstance(other, List) else super().is_equal(other)

    def to_dict(self):
        return dict(list=self.list)

    def to_sql(self):
        return ', '.join(item.to_sql() if isinstance(item, Node) else str(item) for item in self.list)

    def __iter__(self):
        for item in self.list:
            yield item


class KeyList(List):
    def __init__(self, *keys):
        super().__init__(*(k if isinstance(k, Key) else Key(k) if isinstance(k, str) else Key(str(k)) for k in keys))

    def to_sql(self):
        return '( %s )' % super().to_sql()


class ValueList(List):
    def __init__(self, *values):
        super().__init__(*(v if isinstance(v, Value) else Value(v) for v in values))

    def to_sql(self):
        return '( %s )' % super().to_sql()


class Dict(Node):
    def __init__(self, **kwargs):
        self._dict = {k: v if isinstance(v, Node) else ValueList(*v) if isinstance(v, (tuple, list)) else Value(v)
                      for k, v in kwargs.items()}

    @property
    def dict(self):
        return self._dict

    def len(self):
        return len(self.dict)

    def items(self):
        return self.dict

    def keys(self):
        return self.dict.keys()

    def values(self):
        return self.dict.values()

    def get(self, key: str):
        return self.dict.get(key)

    def pop(self, key: str, default=None):
        return self.dict.pop(key, default)

    def is_true(self):
        return bool(self.dict)

    def is_equal(self, other):
        return self.dict == other.dict if isinstance(other, Dict) else super().is_equal(other)

    def to_dict(self):
        return dict(dict=self.dict)

    def to_sql(self):
        return ', '.join('%s = %s' % (Key(k).to_sql(), v.to_sql()) for k, v in self.dict.items())

    def __iter__(self):
        for k, v in self.dict:
            yield k, v


class Selection(List):
    def __init__(self, *selects):
        super().__init__(*selects)

    @property
    def selects(self):
        return self.list

    def is_equal(self, other):
        if isinstance(other, Selection):
            return self.selects == other.selects
        return super().is_equal(other)

    def to_dict(self):
        return dict(selects=self.selects)

    def to_sql(self):
        return '*' if not self.selects else super().to_sql()


class TableSet(Set):
    def __init__(self, *keys):
        super().__init__(*[Table(key) for key in keys])

    @property
    def type(self):
        return Table


class Limit(Node):
    def __init__(self, take: int=0, skip: int=0):
        self._take = take
        self._skip = skip

    @property
    def take(self):
        return self._take

    @take.setter
    def take(self, take: int):
        self._take = take

    @property
    def skip(self):
        return self._skip

    @skip.setter
    def skip(self, skip: int):
        self._skip = skip

    def hash(self):
        return hash(self.to_sql())

    def is_true(self):
        return self.take > 0 or self.skip > 0

    def is_equal(self, other):
        if isinstance(other, Limit):
            return self.take == other.take and self.skip == other.skip
        return super().is_equal(other)

    def to_dict(self):
        return dict(take=self.take, skip=self.skip)

    def to_sql(self):
        return '%s,%s' % (self.take, self.skip)


@enum.unique
class ORDER(enum.Enum):
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


class Order(Node):
    def __init__(self, key: str, order):
        self._key = Key(key)
        self._order = order if isinstance(order, ORDER) else ORDER.from_object(order)

    @property
    def key(self):
        return self._key

    @property
    def order(self):
        return self._order

    def items(self):
        return self.key, self.order

    def is_true(self):
        return self.key.is_true() and self.order.is_true()

    def is_equal(self, other):
        if isinstance(other, Order):
            return self.key.is_equal(other.key) and self.order.is_equal(other.order)
        return super().is_equal(other)

    def to_dict(self):
        return dict(key=self.key, order=self.order)

    def to_sql(self):
        return '%s %s' % (self.key.to_sql(), self.order.to_sql())

    def __iter__(self):
        yield self.key
        yield self.order


class OrderAsc(Order):
    def __init__(self, key: str):
        super().__init__(key, ORDER.ASC)


class OrderDesc(Order):
    def __init__(self, key: str):
        super().__init__(key, ORDER.DESC)


class OrderList(List):
    def __init__(self, *orders):
        super().__init__(*(o if isinstance(o, Order)
                           else Order(o[0], o[1]) if isinstance(o, (tuple, list)) and len(o) == 2
                           else Order(str(o), ORDER.ASC)
                           for o in orders))

    def asc(self, key: str):
        self.list.append(OrderAsc(key))
        return self

    def desc(self, key: str):
        self.list.append(OrderDesc(key))
        return self


@enum.unique
class WHERE(enum.Enum):

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
    BRACKET = 31
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


class Where(Node):
    def __init__(self, where: WHERE, left_child: Node=Node(), right_child: Node=Node()):
        self.__left__ = left_child
        self.__right__ = right_child
        self.__type__ = where

    @property
    def left(self):
        return self.__left__

    @property
    def right(self):
        return self.__right__

    @property
    def type(self):
        return self.__type__

    def is_equal(self, other):
        if isinstance(other, Where):
            return self.to_sql() == other.to_sql()
        if isinstance(other, str):
            return self.to_sql() == other
        return False

    def to_dict(self):
        return dict(type=self.type, left=self.left, right=self.right)

    def and_by(self, other: Node):
        return WhereAnd(self, other)

    def __and__(self, other):
        return self.and_by(other)

    def or_by(self, other: Node):
        return WhereOr(self, other)

    def __or__(self, other):
        return self.or_by(other)

    def bracket_self(self):
        return WhereBracket(self)

    @classmethod
    def format_and(cls, *args, **kwargs):
        where = WhereNull()
        for each in args:
            if isinstance(each, str):
                where = where.and_by(WhereStr(each))
            elif isinstance(each, Where):
                where = where.and_by(each)
        for k, v in kwargs.items():
            where = where.and_by(WhereEqual(k, v))
        return where

    @classmethod
    def format_or(cls, *args, **kwargs):
        where = WhereNull()
        for each in args:
            if isinstance(each, str):
                where = where.or_by(WhereStr(each))
            elif isinstance(each, Where()):
                where = where.or_by(each)
        for k, v in kwargs.items():
            where = where.or_by(WhereEqual(k, v))
        return where


class WhereNull(Where):
    def __init__(self):
        super().__init__()

    def is_true(self):
        return False

    def to_dict(self):
        return dict(type=WHERE.NULL, child=None)


class WhereTrue(Where):
    def __init__(self):
        super().__init__(where=WHERE.TRUE)

    def is_true(self):
        return True

    def to_dict(self):
        return dict(type=self.type, child=1)

    def to_sql(self):
        return '1'


class WhereStr(Where):
    def __init__(self, str_where: str):
        super().__init__(where=WHERE.STR, left_child=Str(str_where))

    def is_true(self):
        return self.left.is_true()

    def is_equal(self, other):
        if isinstance(other, WhereStr):
            return self.left.is_equal(other.left)
        return super().is_equal(other)

    def to_dict(self):
        return dict(type=self.type, child=self.left)

    def to_sql(self):
        return self.left.to_sql()


class WhereBracket(Where):
    def __init__(self, where_node: Where=None):
        super().__init__(where=WHERE.BRACKET, left_child=where_node)

    def is_true(self):
        return self.left.is_true()

    def is_equal(self, other):
        if isinstance(other, WhereBracket):
            return self.left.is_equal(other.left)
        return super().is_equal(other)

    def to_dict(self):
        return dict(type=WHERE.BRACKET, child=self.left)

    def to_sql(self):
        return '(' + self.left.to_sql() + ')'


class WhereNode(Where):
    def __init__(self, where: WHERE=WHERE.AND, left: Node=Node(), right: Node=Node()):
        super().__init__(where=where, left_child=left, right_child=right)

    def is_true(self):
        return (self.left.is_true() or self.right.is_true()) and self.type.is_true()

    def is_equal(self, other):
        if isinstance(other, WhereNode):
            return self.left.is_equal(other.left) and \
                    self.right.is_equal(other.right) and \
                    self.type.is_equal(other.type)
        return super().is_equal(other)

    def to_sql(self):
        if not self.is_true():
            return ''
        if self.left.is_true() and not self.right.is_true():
            return self.left.to_sql()
        if not self.left.is_true() and self.right.is_true():
            return self.right.to_sql()
        return '%s %s %s' % (self.left.to_sql(), self.type.to_sql(), self.right.to_sql())


class WhereAnd(WhereNode):
    def __init__(self, left: Node=Node(), right: Node=Node()):
        super().__init__(where=WHERE.AND, left=left, right=right)


class WhereOr(WhereNode):
    def __init__(self, left: Node=Node(), right: Node=Node()):
        super().__init__(where=WHERE.OR, left=left, right=right)


class WhereExpression(Where):
    def __init__(self, where=WHERE.EQUAL, left: Key=None, right: Node=Value()):
        super().__init__(where, left, right)

    def is_true(self):
        return self.left.is_true() and self.type.is_true()

    def is_equal(self, other):
        if isinstance(other, WhereExpression):
            return self.left.is_equal(other.left) and \
                   self.type.is_equal(other.type) and \
                   self.right.is_equal(other.right)
        return super().is_equal(other)

    def to_sql(self):
        return '%s %s %s' % (self.left.to_sql(), self.type.to_sql(), self.right.to_sql())


class WhereEqual(WhereExpression):
    def __init__(self, key: str, value):
        super().__init__(WHERE.EQUAL, Key(key), Value(value))

    def to_sql(self):
        if getattr(self.right, 'value') is None:
            return '%s is NULL' % self.left.to_sql()
        else:
            return super().to_sql()


class WhereNotEqual(WhereExpression):
    def __init__(self, key: str, value):
        super().__init__(WHERE.NOT_EQUAL, Key(key), Value(value))

    def to_sql(self):
        if getattr(self.right, 'value') is None:
            return '%s is not NULL' % self.left.to_sql()
        else:
            return super().to_sql()


class WhereLess(WhereExpression):
    def __init__(self, key: str, value):
        super().__init__(WHERE.LESS, Key(key), Value(value))


class WhereLessEqual(WhereExpression):
    def __init__(self, key: str, value):
        super().__init__(WHERE.LESS_EQUAL, Key(key), Value(value))


class WhereGreater(WhereExpression):
    def __init__(self, key: str, value):
        super().__init__(WHERE.GREATER, Key(key), Value(value))


class WhereGreaterEqual(WhereExpression):
    def __init__(self, key: str, value):
        super().__init__(WHERE.GREATER_EQUAL, Key(key), Value(value))


class WhereIn(WhereExpression):
    def __init__(self, key: str, *list_value):
        super().__init__(WHERE.IN, Key(key), ValueList(*list_value))


class WhereNotIn(WhereIn):
    def __init__(self, key: str, *list_value):
        super().__init__(key, *list_value)
        self.__type__ = WHERE.NOT_IN


class WhereBetween(WhereExpression):
    def __init__(self, key: str, left_value, right_value):
        super().__init__(WHERE.BETWEEN, Key(key),
                         WhereAnd(left=Value(left_value), right=Value(right_value)))


class WhereNotBetween(WhereBetween):
    def __init__(self, key: str, left_value, right_value):
        super().__init__(key, left_value, right_value)
        self.__type__ = WHERE.NOT_BETWEEN


class WhereLike(WhereExpression):
    def __init__(self, key: str, like_exp: str):
        super().__init__(WHERE.LIKE, Key(key), Value(like_exp))


class WhereNotLike(WhereExpression):
    def __init__(self, key: str, like_exp: str):
        super().__init__(WHERE.NOT_LIKE, Key(key), Value(like_exp))


@enum.unique
class METHOD(enum.Enum):
    INSERT = 1
    DELETE = 2
    UPDATE = 3
    SELETE = 4

    __str_insert__ = 'insert'
    __str_delete__ = 'delete'
    __str_update__ = 'update'
    __str_select__ = 'select'

    @staticmethod
    def is_true():
        return True

    def is_equal(self, other):
        return self == other

    def to_dict(self):
        return dict(method=self)

    def to_sql(self):
        if self == self.INSERT:
            return self.__str_insert__
        if self == self.DELETE:
            return self.__str_delete__
        if self == self.UPDATE:
            return self.__str_update__
        if self == self.SELETE:
            return self.__str_select__


class Method(Node):
    def __init__(self, table: str, method: METHOD):
        self.__table__ = Table(table)
        self.__method__ = method

    @property
    def table(self):
        return self.__table__

    @property
    def method(self):
        return self.__method__

    def is_true(self):
        return self.table.is_true() and self.method.is_true()

    def is_equal(self, other):
        if isinstance(other, Method):
            return self.table.is_equal(other.table) and self.method.is_equal(other.method)
        return super().is_equal(other)

    def to_dict(self):
        return dict(table=self.table, method=self.method)

    def to_sql(self):
        return '%s from %s' % (self.__method__, self.__table__)


class Insert(Method):
    def __init__(self, table: str, **kwargs):
        super().__init__(table, METHOD.INSERT)
        self.__sets__ = Sets(**kwargs)

    @property
    def sets(self):
        return self.__sets__

    def is_true(self):
        return super().is_true() and self.sets.is_true()

    def is_equal(self, other):
        if isinstance(other, Insert):
            return super().is_equal(other) and self.sets.is_equal(other.sets)
        return super().is_equal(other)

    def to_dict(self):
        d = super().to_dict()
        d.update(insert=self.sets)
        return d

    def to_sql(self):
        return '%s into %s set %s' % (self.method.to_sql(), self.table.to_sql(), self.sets.to_sql())


class Delete(Method):
    def __init__(self, table: str, where: Where=None):
        super().__init__(table, METHOD.DELETE)
        self.__where__ = where

    @property
    def where(self):
        return self.__where__

    def is_true(self):
        return super().is_true() and self.where.is_true()

    def is_equal(self, other):
        if isinstance(other, Delete):
            return super().is_equal(other) and self.where.is_equal(other.where)
        return super().is_equal(other)

    def to_dict(self):
        d = super().to_dict()
        d.update(where=self.where)
        return d

    def to_sql(self):
        return '%s from %s where %s' % (self.method.to_sql(), self.table.to_sql(), self.where.to_sql())


class Update(Method):
    def __init__(self, table: str, where: Where=None, **kwargs):
        super().__init__(table, METHOD.UPDATE)
        self.__where__ = where
        self.__sets__ = Sets(**kwargs)

    @property
    def where(self):
        return self.__where__

    @property
    def sets(self):
        return self.__sets__

    def is_true(self):
        return super().is_true() and self.where.is_true() and self.sets.is_true()

    def is_equal(self, other):
        if isinstance(other, Update):
            return super().is_equal(other) and self.where.is_equal(other.where) and self.sets.is_equal(other.sets)
        return super().is_equal(other)

    def to_dict(self):
        d = super().to_dict()
        d.update(where=self.where, sets=self.sets)
        return d

    def to_sql(self):
        return '%s %s set %s where %s' % \
               (self.method.to_sql(), self.table.to_sql(), self.sets.to_sql(), self.where.to_sql())


class Select(Method):
    def __init__(self, table: str, *list_select, **kwargs):
        super().__init__(table, METHOD.SELETE)
        self.__selection__ = Selection(*list_select) if list_select else Selection()
        self.__where__ = kwargs.get('where', WhereNull())
        self.__order__ = kwargs.get('order', OrderList())
        self.__limit__ = kwargs.get('limit', Limit())

    @property
    def selection(self):
        return self.__selection__

    @property
    def where(self):
        return self.__where__

    @property
    def order(self):
        return self.__order__

    @property
    def limit(self):
        return self.__limit__

    def is_true(self):
        return super().is_true()

    def is_equal(self, other):
        if isinstance(other, Select):
            return super().is_equal(other) and self.selection.is_equal(other.selection) and \
                    self.where.is_equal(other.where) and \
                    self.order.is_equal(other.order) and \
                    self.limit.is_equal(other.limit)
        return super().is_equal(other)

    def to_dict(self):
        d = super().to_dict()
        d.update(selection=self.selection, where=self.where, order=self.order, limit=self.limit)
        return d

    def to_sql(self):
        items = ['%s %s from %s' % (self.method.to_sql(), self.selection.to_sql(), self.table.to_sql())]
        if self.where.is_true():
            items.append('where %s' % self.where.to_sql())
        if self.order.is_true():
            items.append('order by %s' % self.order.to_sql())
        if self.limit.is_true():
            items.append('limit %s' % self.limit.to_sql())
        return ' '.join(items)


class From(object):
    """
    SqlObject 的 API
    """
    def __init__(self, table: str):
        self.__node__ = dict(
                table=table,
                sets=dict(),
                where=WhereNull(),
                order=OrderList(),
                limit=Limit())

    @property
    def node(self):
        return self.__node__

    def clear(self):
        self.node.update(
                sets=dict(),
                where=WhereNull(),
                order=OrderList(),
                limit=Limit())

    def set(self, **kwargs):
        self.node['sets'] = kwargs
        return self

    def where(self, *args, **kwargs):
        self.node['where'] = Where.format_and(*args, **kwargs)
        return self

    def or_where(self, *args, **kwargs):
        self.node['where'] = self.node['where'].or_by(Where.format_and(*args, **kwargs))
        return self

    def and_where(self, *args, **kwargs):
        self.node['where'] = self.node['where'].and_by(Where.format_and(*args, **kwargs))
        return self

    def order(self, *args):
        self.node['order'] = OrderList(*Order.from_list(*args))
        return self

    def order_asc(self, key: str):
        self.node['order'].asc(OrderAsc(key))
        return self

    def order_desc(self, key: str):
        self.node['order'].asc(OrderDesc(key))
        return self

    def take(self, take: int):
        self.node['limit'].take = take
        return self

    def skip(self, skip: int):
        self.node['limit'].skip = skip
        return self

    def select(self, *selection):
        return Select(self.node.get('table'),
                      *selection,
                      where=self.node.get('where'),
                      order=self.node.get('order'),
                      limit=self.node.get('limit'))

    def insert(self):
        return Insert(self.node.get('table'), **self.node.get('sets'))

    def delete(self):
        return Delete(self.node.get('table'), self.node.get('where'))

    def update(self):
        return Update(self.node.get('table'), self.node.get('where'), **self.node.get('sets'))

if __name__ == '__main__':
    ss = Set(1, None, 4, Limit(1, 2), (1,2,3))
    print(ss)
    ss.update((Order('id', 'Desc'),), (Limit(1, 2), Order('b', 'Desc')))
    print(ss)
    ss.remove(Limit(1, 2))
    print(ss)
    print(ss.pop())
    print(ss)
