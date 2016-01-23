# coding=utf-8
import enum
import collections
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


class Null(Node):
    def hash(self):
        return hash(0)

    def is_true(self):
        return False

    def is_equal(self, other):
        return isinstance(other, Null) or False

    def to_dict(self):
        return dict()

    def to_sql(self):
        return 'NULL'


class Str(Node):
    def __init__(self, str_arg: str):
        self._str = str_arg

    @property
    def str(self):
        return self._str

    def hash(self):
        return hash(self.str)

    def is_true(self):
        return bool(self.str)

    def is_equal(self, other):
        return self.str == other.str if isinstance(other, Str) \
            else self.str == other if isinstance(other, str) else super().is_equal(other)

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
        self._value = Value(value) if not isinstance(value, Value) else value

    @property
    def key(self):
        return self._key

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = Value(value) if not isinstance(value, Value) else value

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

    def items(self):
        return self.key, self.value


class Set(Node):
    def __init__(self, *args):
        self._set = set(args)

    @property
    def set(self):
        return self._set

    def hash(self):
        return 0

    def is_true(self):
        return bool(self.set)

    def is_equal(self, other):
        return self.set == other.set if isinstance(other, Set) else super().is_equal(other)

    def to_dict(self):
        return dict(set=self.set)

    def to_sql(self):
        return ', '.join(item.to_sql() if isinstance(item, Node) else str(item) for item in self.set)

    def len(self):
        return len(self.set)

    def items(self):
        return self.set

    def iter(self):
        return self.set.__iter__()

    def add(self, arg):
        self.set.add(arg)

    def remove(self, arg):
        self.set.remove(arg)

    def pop(self):
        return self.set.pop()

    def update(self, *args):
        self.set.update(*args)

    def clear(self):
        self.set.clear()

    def has(self, item):
        return self.set.__contains__(item)

    def __contains__(self, item):
        return self.has(item)

    def __len__(self):
        return self.len()

    def __iter__(self):
        return self.iter()


class KeySet(Set):
    def __init__(self, *keys):
        super().__init__(*(k if isinstance(k, Key) else Key(k) if isinstance(k, str) else Key(str(k)) for k in keys))


class ValueSet(Set):
    def __init__(self, *values):
        super().__init__(*(v if isinstance(v, Value) else Value(v) for v in values))

    def to_sql(self):
        return '( %s )' % super().to_sql()


class List(Node):
    def __init__(self, *args):
        self._list = list(args)

    @property
    def list(self):
        return self._list

    def hash(self):
        return 0

    def is_true(self):
        return bool(self.list)

    def is_equal(self, other):
        return self.list == other.list if isinstance(other, List) else super().is_equal(other)

    def to_dict(self):
        return dict(list=self.list)

    def to_sql(self):
        return ', '.join(item.to_sql() if isinstance(item, Node) else str(item) for item in self.list)

    def len(self):
        return len(self.list)

    def items(self):
        return self.list

    def iter(self):
        return self.list.__iter__()

    def clear(self):
        self.list.clear()

    def has(self, item):
        return self.list.__contains__(item)

    def get(self, index: int):
        return self.list[index]

    def pop(self, index):
        return self.list.pop(index)

    def add(self, item):
        self.list.append(item)

    def add_many(self, *items):
        self.list.append(items)

    def __contains__(self, item):
        return self.has(item)

    def __len__(self):
        return self.len()

    def __getitem__(self, item: int):
        return self.get(item)

    def __iter__(self):
        return self.iter()


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


class KeyValueList(List):
    def __init__(self, *args):
        super().__init__()
        self._list = collections.OrderedDict()
        for arg in args:
            if isinstance(arg, KeyValue):
                self._list[arg.key.key] = arg.value.value
            elif isinstance(arg, (tuple, list)) and len(arg) == 2:
                self._list[arg[0]] = arg[1]
            else:
                raise ValueError('arg type must be tuple(len = 2) or sql.KeyValue')

    @property
    def list(self):
        return self._list

    def to_sql(self):
        return '%s VALUES %s' % (KeyList(*self.keys()).to_sql(), ValueList(*self.values()).to_sql())

    def keys(self):
        return self.list.keys()

    def values(self):
        return self.list.values()

    def has(self, key: str):
        return key in self.list

    def get(self, key: str, default=None):
        return self.list.get(key)

    def set(self, key: str, value):
        self.list[key] = value

    def pop(self, key: str):
        return self.list.pop(key)

    def update(self, **kwargs):
        self.list.update(**kwargs)

    def __contains__(self, item: str):
        return self.has(item)

    def __getitem__(self, item):
        return self.get(item)

    def __setitem__(self, key, value):
        self.set(key, value)


class SelectList(List):
    def __init__(self, *selects):
        for s in selects:
            if not isinstance(s, (str, Key)):
                raise ValueError('the select (%s) must be str or sql.Key' % s)
        super().__init__(*selects)

    @property
    def selects(self):
        return self.list

    def to_dict(self):
        return dict(selects=self.selects)

    def to_sql(self):
        return '*' if not self.selects else super().to_sql()


class Dict(Node):
    def __init__(self, **kwargs):
        self._dict = {k: v if isinstance(v, Node) else ValueList(*v) if isinstance(v, (tuple, list)) else Value(v)
                      for k, v in kwargs.items()}

    @property
    def dict(self):
        return self._dict

    def hash(self):
        return 0

    def is_true(self):
        return bool(self.dict)

    def is_equal(self, other):
        return self.dict == other.dict if isinstance(other, Dict) else super().is_equal(other)

    def to_dict(self):
        return dict(dict=self.dict)

    def to_sql(self):
        return ', '.join('%s = %s' % (Key(k).to_sql(), v.to_sql()) for k, v in self.dict.items())

    def len(self):
        return len(self.dict)

    def items(self):
        return self.dict.items()

    def iter(self):
        return self.dict.__iter__()

    def keys(self):
        return self.dict.keys()

    def values(self):
        return self.dict.values()

    def clear(self):
        self.dict.clear()

    def has(self, key: str):
        return self.dict.__contains__(key)

    def get(self, key: str, default=None):
        return self.dict.get(key, default)

    def set(self, key: str, value):
        value = value if isinstance(value, Node) else ValueList(*value) if isinstance(value, (tuple, list)) \
            else Value(value)
        self.dict[key] = value

    def pop(self, key: str):
        return self.dict.pop(key)

    def __len__(self):
        return self.len()

    def __contains__(self, item):
        return self.has(item)

    def __getitem__(self, item):
        return self.get(item)

    def __setitem__(self, key, value):
        self.set(key, value)

    def __iter__(self):
        return self.dict.__iter__()


class Limit(Node):
    def __init__(self, take: int=0, skip: int=0):
        self._take = take
        self._skip = skip

    @property
    def take(self):
        return self._take

    @property
    def skip(self):
        return self._skip

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

    def items(self):
        return self.take, self.skip


@enum.unique
class ORDER(enum.Enum):
    ASC = 0
    DESC = 1
    _str_asc = 'asc'
    _str_desc = 'desc'

    def hash(self):
        return hash(self)

    def is_equal(self, other):
        return self == other

    def is_true(self):
        return bool(self)

    def to_dict(self):
        return dict(ORDER=self)

    def to_sql(self):
        if self == self.ASC:
            return self._str_asc
        if self == self.DESC:
            return self._str_desc

    @classmethod
    def from_str(cls, _str: str):
        _str = _str.strip().lower()
        if _str == cls._str_asc:
            return cls.ASC
        if _str == cls._str_desc:
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

    def is_true(self):
        return self.key.is_true() and self.order.is_true()

    def is_equal(self, other):
        if isinstance(other, Order):
            return self.key.is_equal(other.key) and self.order.is_equal(other.order)
        return super().is_equal(other)

    def to_dict(self):
        return dict(key=self.key, ORDER=self.order)

    def to_sql(self):
        return '%s %s' % (self.key.to_sql(), self.order.to_sql())

    def items(self):
        return self.key, self.order


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
        self.add(OrderAsc(key))
        return self

    def desc(self, key: str):
        self.add(OrderDesc(key))
        return self


@enum.unique
class WHERE(enum.Enum):

    EQUAL = 1
    _str_equal = '='
    LESS = 2
    _str_less = '<'
    GREATER = 3
    _str_greater = '>'
    LESS_EQUAL = 4
    _str_less_equal = '<='
    GREATER_EQUAL = 5
    _str_greater_equal = '>='
    NOT_EQUAL = 6
    _str_not_equal = '!='

    IN = 10
    _str_in = 'in'
    BETWEEN = 11
    _str_between = 'between'
    LIKE = 12
    _str_like = 'like'

    NOT_IN = 13
    _str_not_in = 'not in'
    NOT_BETWEEN = 14
    _str_not_between = 'not between'
    NOT_LIKE = 15
    _str_not_like = 'not like'

    AND = 21
    _str_and = 'and'
    OR = 22
    _str_or = 'or'
    BRACKET = 31
    STR = 32
    NULL = 41
    TRUE = 42

    def is_true(self):
        return self != self.NULL

    def is_equal(self, other):
        return self == other

    def to_dict(self):
        return dict(WHERE=self)

    def to_sql(self):
        if self == self.EQUAL:
            return self._str_equal
        if self == self.NOT_EQUAL:
            return self._str_not_equal
        if self == self.LESS:
            return self._str_less
        if self == self.LESS_EQUAL:
            return self._str_less_equal
        if self == self.GREATER:
            return self._str_greater
        if self == self.GREATER_EQUAL:
            return self._str_greater_equal
        if self == self.IN:
            return self._str_in
        if self == self.NOT_IN:
            return self._str_not_in
        if self == self.BETWEEN:
            return self._str_between
        if self == self.NOT_BETWEEN:
            return self._str_not_between
        if self == self.LIKE:
            return self._str_like
        if self == self.NOT_LIKE:
            return self._str_not_like
        if self == self.AND:
            return self._str_and
        if self == self.OR:
            return self._str_or
        return ''

    @classmethod
    def from_str(cls, op: str):
        op = op.strip().lower()
        if op == cls._str_equal:
            return cls.EQUAL
        if op == cls._str_not_equal or op == '<>':
            return cls.NOT_EQUAL
        if op == cls._str_less:
            return cls.LESS
        if op == cls._str_less_equal:
            return cls.LESS_EQUAL
        if op == cls._str_greater:
            return cls.GREATER
        if op == cls._str_greater_equal:
            return cls.GREATER_EQUAL
        if op == cls._str_in:
            return cls.IN
        if op == cls._str_not_in:
            return cls.NOT_IN
        if op == cls._str_between:
            return cls.BETWEEN
        if op == cls._str_not_between:
            return cls.NOT_BETWEEN
        if op == cls._str_like:
            return cls.LIKE
        if op == cls._str_not_like:
            return cls.NOT_LIKE


class Where(Node):
    def __init__(self, operation, left, right):
        self._operation = operation if isinstance(operation, WHERE) \
            else WHERE.from_str(operation) if isinstance(operation, str) \
            else None
        if self._operation is None:
            raise ValueError('operation value (%s) must be sub of sql.WHERE' % self._operation)
        self._left = left if isinstance(left, Node) else Str(str(left))
        self._right = right if isinstance(right, Node) else Str(str(right))

    @property
    def left(self):
        return self._left

    @property
    def right(self):
        return self._right

    @property
    def operation(self):
        return self._operation

    def is_true(self):
        return self.operation.is_true() and (self.left.is_true() or self.right.is_true())

    def is_equal(self, other):
        return self.left.is_equal(other.left) and self.right.is_equal(other.right) \
               and self.operation.is_equal(other.operation) if isinstance(other, Where) else super().is_equal(other)

    def to_dict(self):
        return dict(operation=self.operation, left=self.left, right=self.right)

    def to_sql(self):
        return '%s %s %s' % (self.left.to_sql(), self.operation.to_sql(), self.right.to_sql())

    def items(self):
        return self.operation, self.left, self.right


class WhereNull(Where):
    def __init__(self):
        super().__init__(WHERE.NULL, Null(), Null())


class WhereTrue(Where):
    def __init__(self):
        super().__init__(WHERE.TRUE, 1, Null())


class WhereStr(Where):
    def __init__(self, str_where: str):
        super().__init__(WHERE.STR, Str(str_where), Null())


class WhereAnd(Where):
    def __init__(self, left, right):
        super().__init__(WHERE.AND, left, right)


class WhereOr(Where):
    def __init__(self, left, right):
        super().__init__(WHERE.OR, left, right)


class WhereExpression(Where):
    def __init__(self, operation, key: str, value):
        super().__init__(operation, Key(key), value if isinstance(value, Node) else Value(value))

    def to_sql(self):
        if self.operation in (WHERE.EQUAL, WHERE.NOT_EQUAL):
            if self.right.value is None:
                return '%s IS NULL' % self.left.to_sql() if self.operation == WHERE.EQUAL \
                    else '%s IS NOT NULL' % self.left.to_sql()
        return super().to_sql()
    

class WhereEqual(WhereExpression):
    def __init__(self, key: str, value):
        super().__init__(WHERE.EQUAL, key, value)


class WhereNotEqual(WhereExpression):
    def __init__(self, key: str, value):
        super().__init__(WHERE.NOT_EQUAL, key, value)


class WhereLess(WhereExpression):
    def __init__(self, key: str, value):
        super().__init__(WHERE.LESS, key, value)


class WhereLessEqual(WhereExpression):
    def __init__(self, key: str, value):
        super().__init__(WHERE.LESS_EQUAL, key, value)


class WhereGreater(WhereExpression):
    def __init__(self, key: str, value):
        super().__init__(WHERE.GREATER, key, value)


class WhereGreaterEqual(WhereExpression):
    def __init__(self, key: str, value):
        super().__init__(WHERE.GREATER_EQUAL, key, value)


class WhereIn(WhereExpression):
    def __init__(self, key: str, *values):
        super().__init__(WHERE.IN, key, ValueList(*values))


class WhereNotIn(WhereExpression):
    def __init__(self, key: str, *values):
        super().__init__(WHERE.NOT_IN, key, ValueList(*values))


class WhereBetween(WhereExpression):
    def __init__(self, key: str, left, right):
        super().__init__(WHERE.BETWEEN, key, WhereAnd(left=Value(left), right=Value(right)))


class WhereNotBetween(WhereExpression):
    def __init__(self, key: str, left, right):
        super().__init__(WHERE.NOT_BETWEEN, key, WhereAnd(left=Value(left), right=Value(right)))


class WhereLike(WhereExpression):
    def __init__(self, key: str, like_exp: str):
        super().__init__(WHERE.LIKE, key, Value(like_exp))


class WhereNotLike(WhereExpression):
    def __init__(self, key: str, like_exp: str):
        super().__init__(WHERE.NOT_LIKE, key, Value(like_exp))


@enum.unique
class METHOD(enum.Enum):
    INSERT = 1
    DELETE = 2
    UPDATE = 3
    SELETE = 4

    _str_insert = 'insert'
    _str_delete = 'delete'
    _str_update = 'update'
    _str_select = 'select'

    def hash(self):
        return self.__hash__()

    def is_true(self):
        return bool(self)

    def is_equal(self, other):
        return self == other

    def to_dict(self):
        return dict(METHOD=self)

    def to_sql(self):
        if self == self.INSERT:
            return self._str_insert
        if self == self.DELETE:
            return self._str_delete
        if self == self.UPDATE:
            return self._str_update
        if self == self.SELETE:
            return self._str_select


class Method(Node):
    def __init__(self, table: str, method: METHOD):
        self.__table__ = Key(table)
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
        self.__sets__ = Dict(**kwargs)

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
        self.__sets__ = Dict(**kwargs)

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
        self.__selection__ = SelectList(*list_select) if list_select else SelectList()
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
    kvs = KeyValueList(('id', 3), ('name', 'dgf'))
    print(type(kvs.list))
    print(kvs)
    kvs.update(id=None)
    print(kvs)
