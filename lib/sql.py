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


__all__ = ['From', 'WhereEqual']


class Node(object):
    """
    1、一切皆节点
    2、所有节点都从这开始继承
    3、每一句SQL都是一个节点，每一个节点下都有多个或一个子节点，每一个子节点都是SQL的子句。
    4、每一条SQL语句都抽象为一个类，每一条SQL子句都抽象为一个类。
    5、SQL语句之间的拼接合并由类的方法提供。
    """

    def to_sql(self) -> str:
        """
        输出节点的SQL语句
        :return:
        """
        return ''

    def __eq__(self, other):
        if isinstance(other, Node):
            return self.to_sql() == other.to_sql()
        if isinstance(other, str):
            return self.to_sql() == other
        return NotImplemented

    def __str__(self):
        return '<Sql: %s>' % (self.to_sql())

    def __repr__(self):
        return '<%s: %s>' % (type(self).__name__, self.to_sql())


class Null(Node):
    def __hash__(self):
        return 0

    def __bool__(self):
        return False

    def __eq__(self, other):
        return True if isinstance(other, Null) else False

    def to_sql(self):
        return ''


class Str(Node):
    def __init__(self, str_arg):
        if not isinstance(str_arg, str):
            raise TypeError('the str_arg type(%s) should be str type' % type(str_arg))
        self._str = str_arg

    @property
    def str(self):
        return self._str

    def __hash__(self):
        return hash(self.str)

    def __bool__(self):
        return bool(self.str)

    def __eq__(self, other):
        return self.str == other.str if isinstance(other, Str) else super().__eq__(other)

    def to_sql(self):
        return self.str


class Key(Str):
    def __init__(self, key):
        if not isinstance(key, str) or not key:
            raise ValueError('the key arg should be str type and not empty!')
        super().__init__(key)

    @property
    def key(self):
        return self.str

    def to_sql(self):
        return '`%s`' % super().to_sql()


class Value(Node):
    def __init__(self, value=None):
        if isinstance(value, Node):
            raise ValueError('the value arg type should be not instance of sql.Node')
        self._value = value

    @property
    def value(self):
        return self._value

    def __hash__(self):
        return hash(self.to_sql())

    def __bool__(self):
        return self.value is not None

    def __eq__(self, other):
        if isinstance(other, Value):
            return self.value == other.value
        return super().__eq__(other)

    def to_sql(self):
        if self.value is None:
            return 'NULL'
        if isinstance(self.value, (int, float, bool)):
            return str(self.value)
        if isinstance(self.value, Node):
            return self.value.to_sql()
        return '"%s"' % self.value


class KeyValue(Node):
    def __init__(self, key, value=None):
        self._key = Key(key)
        self._value = Value(value)

    @property
    def key(self):
        return self._key

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = Value(value)

    def __iter__(self):
        yield self.key
        yield self.value

    def __hash__(self):
        return self.key.__hash__()

    def __bool__(self):
        return self.key.__bool__()

    def __eq__(self, other):
        if isinstance(other, KeyValue):
            return self.key == other.key and self.value == other.value
        return super().__eq__(other)

    def to_sql(self):
        return '%s = %s' % (self.key.to_sql(), self.value.to_sql())


class Set(Node, set):
    def __init__(self, nodes=()):
        super().__init__()
        for node in nodes:
            if not isinstance(node, Node):
                raise TypeError('node should be instance of Node')
            self.add(node)

    def to_sql(self):
        return ', '.join(node.to_sql() for node in self if isinstance(node, Node))


class KeySet(Set):
    def __init__(self, keys=()):
        super().__init__()
        for key in keys:
            if not isinstance(key, Key):
                raise TypeError('key should be instance of Key')
            self.add(key)

    def to_sql(self):
        return ', '.join(key.to_sql() for key in self if isinstance(key, Key))


class ValueSet(Set):
    def __init__(self, values=()):
        super().__init__()
        for value in values:
            if not isinstance(value, Value):
                raise TypeError('value should be instance of Value')
            self.add(value)

    def to_sql(self):
        return '( %s )' % ', '.join(value.to_sql() for value in self if isinstance(value, Value))


class List(Node, list):
    def __init__(self, nodes=()):
        super().__init__()
        for node in nodes:
            if not isinstance(node, Node):
                raise TypeError('node should be instance of Node')
            self.append(node)
        # self.extend(nodes)

    def to_sql(self):
        return ', '.join(node.to_sql() for node in self if isinstance(node, Node))


class KeyList(List):
    def __init__(self, keys=()):
        super().__init__()
        for key in keys:
            if not isinstance(key, Key):
                raise TypeError('key should be instance of Key')
            self.append(key)

    def to_sql(self):
        return '( %s )' % ', '.join(key.to_sql() for key in self if isinstance(key, Key))


class ValueList(List):
    def __init__(self, values=()):
        super().__init__()
        for value in values:
            if not isinstance(value, Value):
                raise TypeError('value should be instance of value')
            self.append(value)

    def to_sql(self):
        return '( %s )' % ', '.join(value.to_sql() for value in self if isinstance(value, Value))


class SelectList(List):
    def __init__(self, selects=()):
        super().__init__()
        for select in selects:
            if isinstance(select, (Str, Key)):
                self.append(select)
            elif isinstance(select, str):
                self.append(Str(select))
            else:
                raise TypeError('select should be instance one of str Str Key')

    def to_sql(self):
        return '*' if not self \
            else ', '.join(node.to_sql() if isinstance(node, Node) else node
                           for node in self if isinstance(node, (Key, Str, str)))


class Dict(Node, dict):
    def __init__(self, kv_items=(), **kwargs):
        super().__init__(kv_items, **kwargs)

    def keyvalues(self):
        return [KeyValue(k, self[k]) for k in self]

    def to_sql(self):
        return ', '.join('%s = %s' % (Key(k).to_sql(), Value(v).to_sql()) for k, v in self.items())


class ListDict(Node, collections.OrderedDict):
    def __init__(self, kv_items=()):
        super().__init__()
        for kv in kv_items:
            if isinstance(kv, KeyValue):
                self[kv.key.key] = kv.value.value
            elif isinstance(kv, (tuple, list)):
                self[kv[0]] = kv[1]
            else:
                raise TypeError('not accept type in kv: %s' % type(kv))

    def keyvalues(self):
        return [KeyValue(k, self[k]) for k in self]

    def to_sql(self):
        keys = KeyList()
        values = ValueList()
        for k, v in self.items():
            keys.append(Key(k))
            values.append(Value(v))
        return '%s values %s' % (keys.to_sql(), values.to_sql())


@enum.unique
class TREE(Node, enum.IntEnum):
    AND = 100, 'and'
    OR = 101, 'or'
    BRACKET = 102

    def __new__(cls, value: int, sql: str=''):
        obj = int.__new__(cls, value)
        obj._value_ = value
        obj.sql = sql
        return obj

    def to_sql(self):
        return self.sql

    @classmethod
    def from_str(cls, sql: str):
        sql = sql.strip().lower()
        for item in cls:
            if item.sql == sql:
                return item


class Tree(Node):
    def __init__(self, tree, left, right):
        self._tree = tree if isinstance(tree, Node) else None
        self._left = left if isinstance(left, Node) else None
        self._right = right if isinstance(right, Node) else None
        if self._left is None or self._right is None or self._tree is None:
            raise TypeError('not accept type')

    @property
    def tree(self):
        return self._tree

    @property
    def left(self):
        return self._left

    @property
    def right(self):
        return self._right

    def __iter__(self):
        yield self.tree
        yield self.left
        yield self.right

    def __bool__(self):
        return bool(self.tree) and (bool(self.left) or bool(self.right))

    def __eq__(self, other):
        if isinstance(other, Tree):
            return self.tree == other.tree and self.left == other.left and self.right == other.right
        return super().__eq__(other)

    def and_(self, other):
        return And(self, other)

    def __and__(self, other):
        return self.and_(other)

    def or_(self, other):
        return Or(self, other)
    
    def __or__(self, other):
        return self.or_(other)

    def bracket(self):
        return Bracket(self)

    def to_sql(self):
        tree = bool(self.tree)
        left = bool(self.left)
        right = bool(self.right)
        if tree and left and right:
            return ' '.join((self.left.to_sql(), self.tree.to_sql(), self.right.to_sql()))
        return self.left.to_sql() if left else self.right.to_sql() if right else ''


class And(Tree):
    def __init__(self, left, right):
        super().__init__(TREE.AND, left, right)


class Or(Tree):
    def __init__(self, left, right):
        super().__init__(TREE.OR, left, right)


class Bracket(Tree):
    def __init__(self, node):
        super().__init__(TREE.BRACKET, node, Null())

    def to_sql(self):
        return '( %s )' % super().to_sql()


class Limit(Node):
    def __init__(self, take: int = 0, skip: int = 0):
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

    def __iter__(self):
        yield self.take
        yield self.skip

    def __bool__(self):
        return self.take > 0 or self.skip > 0

    def __eq__(self, other):
        if isinstance(other, Limit):
            return self.take == other.take and self.skip == other.skip
        return super().__eq__(other)

    def to_sql(self):
        return '%s, %s' % (self.skip, self.take)

    @classmethod
    def from_tuple(cls, limit):
        len_tuple = len(limit)
        if len_tuple == 2:
            return Limit(limit[0], limit[1])
        elif len_tuple == 1:
            return Limit(limit[0])

    @classmethod
    def from_dict(cls, limit: dict):
        t = limit.get('take') or limit.get('Take') or limit.get('t') or 0
        k = limit.get('skip') or limit.get('Skip') or limit.get('s') or 0
        if len(limit) == 1 and not t and not k:
            return cls.from_obj(limit.popitem()[1])
        return cls(t, k)

    @classmethod
    def from_obj(cls, obj_limit):
        if isinstance(obj_limit, Limit):
            return obj_limit
        elif isinstance(obj_limit, int):
            return cls(obj_limit)
        elif isinstance(obj_limit, (tuple, list)):
            return cls.from_tuple(obj_limit)
        elif isinstance(obj_limit, dict):
            return cls.from_dict(obj_limit)


@enum.unique
class ORDER(Node, enum.IntEnum):
    ASC = 1, 'asc'
    DESC = 2, 'desc'

    def __new__(cls, value, sql=''):
        obj = int.__new__(cls, value)
        obj._value_ = value
        obj.sql = sql
        return obj

    def to_sql(self):
        return self.sql

    @classmethod
    def from_str(cls, _str: str):
        _str = _str.strip().lower()
        if _str == 'asc':
            return cls.ASC
        if _str == 'desc':
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
    def __init__(self, key, order=None):
        self._key = key if isinstance(key, Str) else Str(str(key)) if isinstance(key, str) else None
        if not self.key:
            raise ValueError('there is no key in the order')
        self._order = order if isinstance(order, ORDER) else ORDER.from_object(order)

    @property
    def key(self):
        return self._key

    @property
    def order(self):
        return self._order

    def __iter__(self):
        yield self.key
        yield self.order

    def __hash__(self):
        return self.key.__hash__()

    def __bool__(self):
        return self.key.__bool__() and self.order.__bool__()

    def __eq__(self, other):
        if isinstance(other, Order):
            return self.key == other.key and self.order == other.order
        return super().__eq__(other)

    def to_sql(self):
        return '%s %s' % (self.key.to_sql(), self.order.to_sql())

    @classmethod
    def from_tuple(cls, tuple_order):
        if len(tuple_order) == 1:
            return cls(tuple_order[0], None)
        if len(tuple_order) == 2:
            k, o = tuple_order
            return cls(k, o)

    @classmethod
    def from_str(cls, str_order: str):
        _order_ = str_order.strip().split()
        return cls.from_tuple(_order_)

    @classmethod
    def from_dict(cls, dict_order: dict):
        if len(dict_order) == 1:
            k, o = dict_order.popitem()
            return cls(k, o)
        k = dict_order.get('key') or dict_order.get('Key') or dict_order.get('k')
        if not k:
            raise ValueError('the key not found in the order object')
        o = dict_order.get('order') or dict_order.get('Order') or dict_order.get('o')
        if not o:
            raise ValueError('the order not found in the order object')
        return cls(k, o)

    @classmethod
    def from_obj(cls, obj_order):
        if isinstance(obj_order, Order):
            return obj_order
        elif isinstance(obj_order, (tuple, list)):
            return cls.from_tuple(obj_order)
        elif isinstance(obj_order, str):
            return cls.from_str(obj_order)
        elif isinstance(obj_order, dict):
            return cls.from_dict(obj_order)


class OrderAsc(Order):
    def __init__(self, key):
        super().__init__(key, ORDER.ASC)


class OrderDesc(Order):
    def __init__(self, key):
        super().__init__(key, ORDER.DESC)


class OrderList(List):
    def __init__(self, orders=()):
        super().__init__(Order.from_obj(_order_) for _order_ in orders)

    def add(self, order):
        self.append(order)
        return self

    def asc(self, key):
        self.append(OrderAsc(key))
        return self

    def desc(self, key):
        self.append(OrderDesc(key))
        return self

    @classmethod
    def from_str(cls, str_order_items: str):
        return cls(order_item for order_item in str_order_items.strip().split(',') if order_item)

    @classmethod
    def from_dict(cls, dict_order_items):
        return cls((k, dict_order_items[k]) for k in dict_order_items)

    @classmethod
    def from_obj(cls, obj_order_items):
        if isinstance(obj_order_items, OrderList):
            return obj_order_items
        elif isinstance(obj_order_items, (tuple, list)):
            return cls(obj_order_items)
        elif isinstance(obj_order_items, str):
            return cls.from_str(obj_order_items)
        elif isinstance(obj_order_items, dict):
            return cls.from_dict(obj_order_items)


@enum.unique
class WHERE(Node, enum.IntEnum):
    EQUAL = 1, '='
    LESS = 2, '<'
    GREATER = 3, '>'
    LESS_EQUAL = 4, '<='
    GREATER_EQUAL = 5, '>='
    NOT_EQUAL = 6, '!='

    IN = 10, 'in'
    BETWEEN = 11, 'between'
    LIKE = 12, 'like'

    NOT_IN = 13, 'not in'
    NOT_BETWEEN = 14, 'not between'
    NOT_LIKE = 15, 'not like'

    NULL = 31
    STR = 32
    TRUE = 42

    def __new__(cls, value: int, sql: str=''):
        obj = int.__new__(cls, value)
        obj._value_ = value
        obj.sql = sql
        return obj

    def to_sql(self):
        return self.sql

    @classmethod
    def from_str(cls, sql: str):
        sql = sql.strip().lower()
        for item in cls:
            if item.sql == sql:
                return item


class Where(Tree):
    def __init__(self, operation, left, right):
        super().__init__(operation if isinstance(operation, Node)
                         else WHERE.from_str(operation) if isinstance(operation, str) else None,
                         left if isinstance(left, Node) else Str(left) if isinstance(left, str) else None,
                         right if isinstance(right, Node) else Value(right))

    @property
    def operation(self):
        return self._tree

    def __hash__(self):
        return hash(self.to_sql())

    def to_sql(self):
        if self.operation in (WHERE.EQUAL, WHERE.NOT_EQUAL, '=', '!='):
            if not self.right:
                return '%s is NULL' % self.left.to_sql() if self.operation == WHERE.EQUAL \
                    else '%s is not NULL' % self.left.to_sql()
        return ' '.join(sql for sql in (self.left.to_sql(), self.operation.to_sql(), self.right.to_sql()) if sql)

    @classmethod
    def from_str(cls, where: str):
        return WhereStr(where)

    @classmethod
    def from_dict(cls, where: dict):
        if len(where) == 1:
            k, v = where.popitem()
            return WhereEqual(k, v)
        k = where.get('key') or where.get('Key') or where.get('k')
        if not k:
            raise ValueError('the key not in the where object')
        v = where.get('value') or where.get('Value') or where.get('v')
        if not v:
            raise ValueError('the value not in the where object')
        op = where.get('operation') or where.get('Operation') or where.get('op')
        if not op:
            op = WHERE.EQUAL
            if isinstance(v, (tuple, list)):
                return WhereIn(k, v)
        return Where(op, k, v)

    @classmethod
    def from_tuple(cls, where: tuple):
        len_tuple = len(where)
        if len_tuple == 1:
            return cls.from_str(where[0])
        elif len_tuple == 2:
            if isinstance(where[1], (tuple, list)):
                return WhereIn(where[0], where[1])
            return WhereEqual(where[0], where[1])
        elif len_tuple == 3:
            try:
                op, k, v = where
                w = Where(op, k, v)
                return w
            except TypeError:
                try:
                    k, op, v = where
                    w = Where(op, k, v)
                    if w.operation not in (WHERE.IN, WHERE.NOT_IN, WHERE.BETWEEN, WHERE.NOT_BETWEEN):
                        return w
                except TypeError:
                    pass
        k = where[0]
        vs = where[1:]
        return WhereIn(k, vs)

    @classmethod
    def from_obj(cls, where):
        if isinstance(where, Tree):
            return where
        elif isinstance(where, str):
            return cls.from_str(where)
        elif isinstance(where, (tuple, list)):
            return cls.from_tuple(where)
        elif isinstance(where, dict):
            return cls.from_dict(where)


class WhereNull(Where):
    def __init__(self):
        super().__init__(WHERE.NULL, Null(), Null())


class WhereTrue(Where):
    def __init__(self):
        super().__init__(WHERE.TRUE, Str('1'), Null())


class WhereStr(Where):
    def __init__(self, str_where: str):
        super().__init__(WHERE.STR, Str(str_where), Null())


class WhereExpression(Where):
    def __init__(self, operation, key, value):
        super().__init__(operation, key, value if isinstance(value, Node) else Value(value))


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
    def __init__(self, key: str, values):
        super().__init__(WHERE.IN, key,
                         ValueList(value if isinstance(value, Value) else Value(value) for value in values))


class WhereNotIn(WhereExpression):
    def __init__(self, key: str, values):
        super().__init__(WHERE.NOT_IN, key,
                         ValueList(value if isinstance(value, Value) else Value(value) for value in values))


class WhereBetween(WhereExpression):
    def __init__(self, key: str, left, right):
        super().__init__(WHERE.BETWEEN, key, And(left=Value(left), right=Value(right)))


class WhereNotBetween(WhereExpression):
    def __init__(self, key: str, left, right):
        super().__init__(WHERE.NOT_BETWEEN, key, And(left=Value(left), right=Value(right)))


class WhereLike(WhereExpression):
    def __init__(self, key: str, like_exp: str):
        if not isinstance(like_exp, str):
            raise TypeError('like_expr should be a str type')
        super().__init__(WHERE.LIKE, key, like_exp)


class WhereNotLike(WhereExpression):
    def __init__(self, key: str, like_exp: str):
        if not isinstance(like_exp, str):
            raise TypeError('like_expr should be a str type')
        super().__init__(WHERE.NOT_LIKE, key, like_exp)


@enum.unique
class METHOD(Node, enum.IntEnum):
    INSERT = 1, 'insert'
    DELETE = 2, 'delete'
    UPDATE = 3, 'update'
    SELECT = 4, 'select'

    def __new__(cls, value, sql=''):
        obj = int.__new__(cls, value)
        obj._value_ = value
        obj.sql = sql
        return obj

    def to_sql(self):
        return self.sql

    @classmethod
    def from_str(cls, method: str):
        method = method.strip().lower()
        for item in cls:
            if item.sql == method:
                return item


class Method(Node):
    def __init__(self, method, table: str):
        self._method = method if isinstance(method, Node) \
            else METHOD.from_str(method) if isinstance(method, str) else None
        if self._method is None:
            raise TypeError('method is not accept type')
        self._table = Key(table)

    @property
    def table(self):
        return self._table

    @property
    def method(self):
        return self._method

    def __bool__(self):
        return self.table.__bool__() and self.method.__bool__()

    def __eq__(self, other):
        if isinstance(other, Method):
            return self.table == other.table and self.method == other.method
        return super().__eq__(other)

    def to_sql(self):
        raise NotImplementedError()


class Insert(Method):
    def __init__(self, table: str, to_insert):
        super().__init__(METHOD.INSERT, table)
        self._to_insert = ListDict(to_insert)

    @property
    def datas(self):
        return self._to_insert

    def __bool__(self):
        return bool(super()) and bool(self.datas)

    def __eq__(self, other):
        if isinstance(other, Insert):
            return super().__eq__(other) and self.datas == other.datas
        return super().__eq__(other)

    def to_sql(self):
        return '%s into %s %s' % (self.method.to_sql(), self.table.to_sql(), self.datas.to_sql()) if self.datas \
            else ''


class Delete(Method):
    def __init__(self, table: str, **kwargs):
        super().__init__(METHOD.DELETE, table)
        self._where = kwargs.get('where', WhereNull())

    @property
    def where(self):
        return self._where

    def __bool__(self):
        return bool(super()) and bool(self.where)

    def __eq__(self, other):
        if isinstance(other, Delete):
            return super().__eq__(other) and self.where == other.where
        return super().__eq__(other)

    def to_sql(self):
        return '%s from %s where %s' % (self.method.to_sql(), self.table.to_sql(), self.where.to_sql()) if self.where \
            else ''


class Update(Method):
    def __init__(self, table: str, to_update, **kwargs):
        super().__init__(METHOD.UPDATE, table)
        self._to_update = Dict(to_update)
        self._where = kwargs.get('where', WhereNull())

    @property
    def where(self):
        return self._where

    @property
    def datas(self):
        return self._to_update

    def __bool__(self):
        return bool(super()) and bool(self.datas) and bool(self.where)

    def __eq__(self, other):
        if isinstance(other, Update):
            return super().__eq__(other) and self.where == other.where and self.datas.__eq__(other.datas)
        return super().__eq__(other)

    def to_sql(self):
        return '%s %s set %s where %s' % \
               (self.method.to_sql(), self.table.to_sql(), self.datas.to_sql(), self.where.to_sql()) if self else ''


class Select(Method):
    def __init__(self, table: str, to_select=(), **kwargs):
        super().__init__(METHOD.SELECT, table)
        self._select = SelectList(to_select)
        self._where = kwargs.get('where', WhereNull())
        self._order = kwargs.get('order', OrderList())
        self._limit = kwargs.get('limit', Limit())

    @property
    def select(self):
        return self._select

    @property
    def where(self):
        return self._where

    @property
    def order(self):
        return self._order

    @property
    def limit(self):
        return self._limit

    def __bool__(self):
        return super().__bool__()

    def __eq__(self, other):
        if isinstance(other, Select):
            return super().__eq__(other) and \
                   self.select.__eq__(other.select) and \
                   self.where.__eq__(other.where) and \
                   self.order.__eq__(other.order) and \
                   self.limit.__eq__(other.limit)
        return super().__eq__(other)

    def to_sql(self):
        items = ['%s %s from %s' % (self.method.to_sql(), self.select.to_sql(), self.table.to_sql())]
        if self.where:
            items.append('where %s' % self.where.to_sql())
        if self.order:
            items.append('order by %s' % self.order.to_sql())
        if self.limit:
            items.append('limit %s' % self.limit.to_sql())
        return ' '.join(items)


class From(object):
    """
    SqlObject 的 API
    """

    def __init__(self, table: str):
        self._node = dict(
                table=table,
                where=WhereNull(),
                order=OrderList(),
                limit=Limit())

    @property
    def node(self):
        return self._node

    def clear(self):
        self.node.update(
                where=WhereNull(),
                order=OrderList(),
                limit=Limit())

    def where(self, where):
        self.node['where'] = Where.from_obj(where)
        return self

    def or_where(self, where):
        if not self.node['where']:
            return self.where(where)
        self.node['where'] = Or(self.node['where'], Where.from_obj(where))
        return self

    def and_where(self, where):
        if not self.node['where']:
            return self.where(where)
        self.node['where'] = And(self.node['where'], Where.from_obj(where))
        return self

    def order(self, args):
        self.node['order'] = OrderList.from_obj(args)
        return self

    def add_order(self, order):
        self.node['order'].add(Order.from_obj(order))
        return self

    def order_asc(self, key):
        self.node['order'].asc(OrderAsc(key))
        return self

    def order_desc(self, key):
        self.node['order'].asc(OrderDesc(key))
        return self

    def limit(self, limit):
        self.node['limit'] = Limit.from_obj(limit)
        return self

    def take(self, take: int):
        self.node['limit'].take = take
        return self

    def skip(self, skip: int):
        self.node['limit'].skip = skip
        return self

    def insert(self, to_insert):
        return Insert(self.node.get('table'), to_insert)

    def delete(self):
        return Delete(self.node.get('table'), where=self.node.get('where'))

    def update(self, to_update):
        return Update(self.node.get('table'), to_update, where=self.node.get('where'))

    def select(self, select_items):
        return Select(self.node.get('table'),
                      select_items,
                      where=self.node.get('where'),
                      order=self.node.get('order'),
                      limit=self.node.get('limit'))


if __name__ == '__main__':
    l = List((Str('a'), Value(1)))
    print(l)
    l = SelectList(('a', 'b'))
    print(l)
