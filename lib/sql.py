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
        return True

    def __eq__(self, other):
        return self.value == other.value if isinstance(other, Value) else super().__eq__(other)

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

    def to_tuple(self):
        return self.key.key, self.value.value


class Set(Node, set):
    def __init__(self, iterable=()):
        super().__init__(iterable)

    def to_sql(self):
        return ', '.join(item.to_sql() if isinstance(item, Node) else str(item) for item in self)


class KeySet(Set):
    def __init__(self, *keys):
        args = []
        for k in keys:
            if isinstance(k, str):
                args.append(Key(k))
            elif isinstance(k, Key):
                args.append(k)
            else:
                raise TypeError('the key tpye should be one of sql.Key and str')
        super().__init__(args)


class ValueSet(Set):
    def __init__(self, *values):
        args = []
        for v in values:
            if isinstance(v, Value):
                args.append(v)
            elif not isinstance(v, Node):
                args.append(Value(v))
            else:
                raise TypeError('the value type should be one of sql.Value and python type')
        super().__init__(args)

    def to_sql(self):
        return '( %s )' % super().to_sql()


class List(Node, list):
    def __init__(self, iterable=()):
        super().__init__(iterable)

    def to_sql(self):
        return ', '.join(item.to_sql() if isinstance(item, Node) else str(item) for item in self)


class KeyList(List):
    def __init__(self, *keys):
        args = []
        for k in keys:
            if isinstance(k, Key):
                args.append(k)
            elif isinstance(k, str):
                args.append(Key(k))
            else:
                raise TypeError('the key type should be one of sql.Key or python str')
        super().__init__(args)

    def to_sql(self):
        return '( %s )' % super().to_sql()


class ValueList(List):
    def __init__(self, *values):
        args = []
        for v in values:
            if isinstance(v, Value):
                args.append(v)
            elif not isinstance(v, Node):
                args.append(Value(v))
            else:
                raise TypeError('the value type should be one of sql.Value or python type')
        super().__init__(args)

    def to_sql(self):
        return '( %s )' % super().to_sql()


class SelectList(List):
    def __init__(self, *selects):
        for s in selects:
            if not isinstance(s, (str, Key)):
                raise ValueError('the select (%s) must be str or sql.Key' % s)
        super().__init__(selects)

    def to_sql(self):
        return '*' if not self else super().to_sql()


class Dict(Node, dict):
    def __init__(self, *kv_args, **kwargs):
        super().__init__(**kwargs)
        for kv in kv_args:
            if isinstance(kv, (tuple, list)) and len(kv) == 2:
                self[kv[0]] = kv[1]
            elif isinstance(kv, KeyValue):
                self[kv.key.key] = kv.value.value
            else:
                raise TypeError('not accept type')

    def to_sql(self):
        return ','.join('%s = %s' % (Key(k).to_sql(), Value(v).to_sql()) for k, v in self.items())


class OrderDict(Node, collections.OrderedDict):
    def __init__(self, *kv_args):
        super().__init__()
        for kv in kv_args:
            if isinstance(kv, (tuple, list)) and len(kv) == 2:
                self[kv[0]] = kv[1]
            elif isinstance(kv, KeyValue):
                self[kv.key.key] = kv.value.value
            else:
                raise TypeError('not accept type')

    def to_sql(self):
        return '%s values %s' % (KeyList(*self.keys()).to_sql(), ValueList(*self.values()).to_sql())


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

    def __bool__(self):
        return self.take >= 0 and self.skip >= 0

    def __eq__(self, other):
        if isinstance(other, Limit):
            return self.take == other.take and self.skip == other.skip
        return super().__eq__(other)

    def to_sql(self):
        return '%s,%s' % (self.take, self.skip)

    def to_tuple(self):
        return self.take, self.skip


@enum.unique
class ORDER(Node, enum.IntEnum):
    ASC = 1, 'asc'
    DESC = 2, 'desc'

    def __new__(cls, value, sql):
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
    def __init__(self, key: str, order):
        self._key = Key(key)
        self._order = order if isinstance(order, ORDER) else ORDER.from_object(order)

    @property
    def key(self):
        return self._key

    @property
    def order(self):
        return self._order

    def __bool__(self):
        return self.key and self.order

    def __eq__(self, other):
        if isinstance(other, Order):
            return self.key == other.key and self.order == other.order
        return super().__eq__(other)

    def to_sql(self):
        return '%s %s' % (self.key.to_sql(), self.order.to_sql())

    def to_tuple(self):
        return self.key, self.order


class OrderAsc(Order):
    def __init__(self, key: str):
        super().__init__(key, ORDER.ASC)


class OrderDesc(Order):
    def __init__(self, key: str):
        super().__init__(key, ORDER.DESC)


class OrderList(List):
    def __init__(self, *orders):
        super().__init__(o if isinstance(o, Order)
                         else Order(o[0], o[1]) if isinstance(o, (tuple, list)) and len(o) == 2
                         else Order(str(o), ORDER.ASC)
                         for o in orders)

    def asc(self, key: str):
        self.append(OrderAsc(key))
        return self

    def desc(self, key: str):
        self.append(OrderDesc(key))
        return self


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

    AND = 21, 'and'
    OR = 22, 'or'
    BRACKET = 31
    STR = 32
    NULL = 41
    TRUE = 42

    def __new__(cls, value, sql=''):
        obj = int.__new__(cls, value)
        obj._value_ = value
        obj.sql = sql
        return obj

    def to_sql(self):
        return self.sql


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

    def __bool__(self):
        return bool(self.operation) and (bool(self.left) or bool(self.right))

    def __eq__(self, other):
        if isinstance(other, Where):
            return self.operation == other.operation and self.left == other.left and self.right == other.right
        return super().__eq__(other)

    def to_sql(self):
        return '%s %s %s' % (self.left.to_sql(), self.operation.to_sql(), self.right.to_sql())

    def to_tuple(self):
        return self.operation, self.left, self.right


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
            if hasattr(self.right, 'value') and getattr(self.right, 'value') is None:
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
class METHOD(Node, enum.IntEnum):
    INSERT = 1, 'insert'
    DELETE = 2, 'delete'
    UPDATE = 3, 'update'
    SELETE = 4, 'select'

    def __new__(cls, value, sql=''):
        obj = int.__new__(cls, value)
        obj._value_ = value
        obj.sql = sql
        return obj

    def to_sql(self):
        return self.sql


class Method(Node):
    def __init__(self, method: METHOD, table: str):
        self._method = method
        self._table = Key(table)

    @property
    def table(self):
        return self._table

    @property
    def method(self):
        return self._method

    def __bool__(self):
        return self.table and self.method

    def __eq__(self, other):
        if isinstance(other, Method):
            return self.table == other.table and self.method == other.method
        return super().__eq__(other)

    def to_sql(self):
        return '%s from %s' % (self._method.to_sql(), self._table.to_sql())


class Insert(Method):
    def __init__(self, table: str, *kv_args):
        super().__init__(METHOD.INSERT, table)
        self._to_insert = OrderDict(*kv_args)

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
        return '%s into %s %s' % (self.method.to_sql(), self.table.to_sql(), self.datas.to_sql())


class Delete(Method):
    def __init__(self, table: str, **kwargs):
        super().__init__(METHOD.DELETE, table)
        self._where = kwargs.get('where')

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
        return '%s where %s' % (super().to_sql(), self.where.to_sql())


class Update(Method):
    def __init__(self, table: str, *kv_args, **kwargs):
        super().__init__(METHOD.UPDATE, table)
        self._where = kwargs.get('where')
        self._to_update = Dict(*kv_args)

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
               (self.method.to_sql(), self.table.to_sql(), self.datas.to_sql(), self.where.to_sql())


class Select(Method):
    def __init__(self, table: str, *list_select, **kwargs):
        super().__init__(METHOD.SELETE, table)
        self.__selection__ = SelectList(*list_select) if list_select else SelectList()
        self.__where__ = kwargs.get('where', WhereTrue())
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
    w = Update('html', KeyValue('id', 3), ('name', 'dgf'), where=WhereIn('id', 1, 2, 3, 4))
    print(bool(w))
