# coding=utf-8
"""
    SqlObject To Sql

    1、将Sql语句抽象为SqlNode(Sql节点)， 一条Sql语句就是树结构的节点集合。
    2、通过SqlNode实例出SqlObject，通过SqlObject输出Sql语句。
    3、SqlFrom 是编程接口， 通过SqlFrom可以方便实例出SqlObject。

    date: 2016年1月4日
    by: dgf1988
    email: dgf1988@qq.com
"""
import enum


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
        return super().__hash__()

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

    def to_str(self) -> str:
        """
        输出节点的字符串
        :return:
        """
        d = self.to_dict()
        for k, v in d.items():
            if isinstance(v, (list, set)):
                d[k] = [each.to_sql() for each in v if isinstance(each, Node)]
            elif isinstance(v, Node):
                d[k] = v.to_sql()
            else:
                d[k] = str(v)
        return str(d)

    # for debug
    def __str__(self):
        return self.to_str()


class Str(Node):
    def __init__(self, str_raw: str):
        self.__str_raw__ = str_raw

    @property
    def str(self):
        return self.__str_raw__

    def is_true(self):
        return bool(self.str)

    def is_equal(self, other):
        if isinstance(other, Str):
            return self.str == other.str
        if isinstance(other, str):
            return self.str == other
        return super().is_equal(other)

    def to_dict(self):
        return dict(str=self.str)

    def to_sql(self):
        return self.str


class Key(Node):
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
        if isinstance(other, Key):
            return self.key == other.key
        return super().is_equal(other)

    def to_dict(self):
        return dict(key=self.key)

    def to_sql(self):
        return '`%s`' % self.key


class Table(Key):
    @property
    def table(self):
        return self.key

    def is_equal(self, other):
        if isinstance(other, Table):
            return self.table == other.table
        return super().is_equal(other)

    def to_dict(self):
        return dict(table=self.table)


class Value(Node):
    def __init__(self, value=None):
        self.__value__ = value

    @property
    def value(self):
        return self.__value__

    def is_true(self):
        return True

    def is_equal(self, other):
        if isinstance(other, Value):
            return self.value == other.value
        return super().is_equal(other)

    def to_dict(self):
        return dict(value=self.value)

    def to_sql(self):
        if self.value is None:
            return 'NULL'
        if isinstance(self.value, (int, float)):
            return str(self.value)
        if isinstance(self.value, Node):
            return self.value.get_table_sql()
        return '"%s"' % self.value.__str__()


class KeyValue(Node):
    def __init__(self, key: str='', value=None):
        self.__key__ = Key(key)
        self.__value__ = Value(value)

    @property
    def key(self):
        return self.__key__

    @property
    def value(self):
        return self.__value__

    def hash(self):
        return self.key.hash()

    def is_true(self):
        return self.key.is_true() and self.value.is_true()

    def is_equal(self, other):
        if isinstance(other, KeyValue):
            return self.key.is_equal(other.key) and self.value.is_equal(other.value)
        return super().is_equal(other)

    def to_dict(self):
        return dict(key=self.key, value=self.value)

    def to_sql(self):
        return '%s = %s' % (self.key.to_sql(), self.value.to_sql())


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
        self.__nodes__ = list(args)

    @property
    def list(self):
        return self.__nodes__

    @property
    def type(self):
        return Node

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
        if isinstance(other, List):
            return self.list == other.list
        return super().is_equal(other)

    def to_dict(self):
        return dict(list=self.list)

    def to_sql(self):
        return ','.join([each.to_sql() for each in self.list if isinstance(each, self.type)])


class Selection(List):
    def __init__(self, *list_select):
        super().__init__(*list_select)

    @property
    def select(self):
        return self.list

    @property
    def type(self):
        return str

    def is_true(self):
        return True

    def is_equal(self, other):
        if isinstance(other, Selection):
            return self.select == other.select
        return super().is_equal(other)

    def to_dict(self):
        return dict(select=self.select)

    def to_sql(self):
        if not self.select:
            return '*'
        else:
            return ','.join([str(each) for each in self.select])


class ValueList(List):
    def __init__(self, *value_list):
        super().__init__(*[Value(value) for value in value_list])

    @property
    def type(self):
        return Value

    def to_sql(self):
        return '(' + super().to_sql() + ')'


class Set(List):
    """
    节点集合
    对节点顺序有要求则不能使用。
    """
    def __init__(self, *args):
        super().__init__(*args)
        self.__nodes__ = set(self.__nodes__)

    @property
    def set(self):
        return self.__nodes__

    def to_dict(self):
        return dict(set=self.set)


class TableSet(Set):
    def __init__(self, *keys):
        super().__init__(*[Table(key) for key in keys])

    @property
    def type(self):
        return Table


class Limit(Node):
    def __init__(self, take: int=0, skip: int=0):
        self.__take__ = take
        self.__skip__ = skip

    @property
    def take(self):
        return self.__take__

    @take.setter
    def take(self, take: int):
        self.__take__ = take

    @property
    def skip(self):
        return self.__skip__

    @skip.setter
    def skip(self, skip: int):
        self.__skip__ = skip

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
    def __init__(self, key: str='', order: ORDER=ORDER.ASC):
        self.__key__ = Key(key)
        self.__order__ = order

    @property
    def key(self):
        return self.__key__

    @property
    def order(self):
        return self.__order__

    def asc(self, key: str):
        return OrderList(self, OrderAsc(key))

    def desc(self, key: str):
        return OrderList(self, OrderDesc(key))

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

    @classmethod
    def from_list(cls, *args) -> list:
        order_list = []
        for each in args:
            if isinstance(each, str):
                order_list.append(OrderAsc(each))
            elif isinstance(each, Order):
                order_list.append(each)
            elif isinstance(each, dict):
                k, v = each.popitem()
                order_list.append(Order(k, ORDER.from_object(v)))
        return order_list


class OrderAsc(Order):
    def __init__(self, key: str):
        super().__init__(key)


class OrderDesc(Order):
    def __init__(self, key: str):
        super().__init__(key, ORDER.DESC)


class OrderList(List):
    def __init__(self, *orders):
        super().__init__(*orders)

    @property
    def type(self):
        return Order

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
    def __init__(self, where_type: WHERE=WHERE.NULL, left_child: Node=Node(), right_child: Node=Node()):
        self.__left__ = left_child
        self.__right__ = right_child
        self.__type__ = where_type

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
        super().__init__(where_type=WHERE.TRUE)

    def is_true(self):
        return True

    def to_dict(self):
        return dict(type=self.type, child=1)

    def to_sql(self):
        return '1'


class WhereStr(Where):
    def __init__(self, str_where: str):
        super().__init__(where_type=WHERE.STR, left_child=Str(str_where))

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
    def __init__(self, where_node: Where=Where()):
        super().__init__(where_type=WHERE.BRACKET, left_child=where_node)

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
    def __init__(self, where_type: WHERE=WHERE.AND, left: Node=Node(), right: Node=Node()):
        super().__init__(where_type=where_type, left_child=left, right_child=right)

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
        super().__init__(where_type=WHERE.AND, left=left, right=right)


class WhereOr(WhereNode):
    def __init__(self, left: Node=Node(), right: Node=Node()):
        super().__init__(where_type=WHERE.OR, left=left, right=right)


class WhereExpression(Where):
    def __init__(self, where_type=WHERE.EQUAL, left: Key=Key(), right: Node=Value()):
        super().__init__(where_type, left, right)

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
    def __init__(self, table: str, where: Where=Where()):
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
    def __init__(self, table: str, where: Where=Where(), **kwargs):
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
    print(From('html').where('id=4', name='dgf').order('id', dict(name='desc'), dict(age='asc')).take(10).select('id').to_sql())
    print(From('user').set(name=None, birth='00000').where(id=4).update().to_sql())
    s = Sets(id=9, name=10)
    print(s.to_sql())
    s.set(id=10)
    print(s.to_sql())
    s.pop('name')
    print(s.to_sql())

