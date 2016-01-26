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
    def __init__(self, *nodes):
        for node in nodes:
            if not isinstance(node, Node):
                raise TypeError('node should be instance of Node')
        super().__init__(nodes)

    def to_sql(self):
        return ', '.join(node.to_sql() for node in self if isinstance(node, Node))


class KeySet(Set):
    def __init__(self, *keys):
        for key in keys:
            if not isinstance(key, Key):
                raise TypeError('key should be instance of Key')
        super().__init__(*keys)

    def to_sql(self):
        return ', '.join(key.to_sql() for key in self if isinstance(key, Key))


class ValueSet(Set):
    def __init__(self, *values):
        for value in values:
            if not isinstance(value, Value):
                raise TypeError('value should be instance of Value')
        super().__init__(*values)

    def to_sql(self):
        return '( %s )' % ', '.join(value.to_sql() for value in self if isinstance(value, Value))


class List(Node, list):
    def __init__(self, *nodes):
        for node in nodes:
            if not isinstance(node, Node):
                raise TypeError('node should be instance of Node')
        super().__init__(nodes)

    def to_sql(self):
        return ', '.join(node.to_sql() for node in self if isinstance(node, Node))


class KeyList(List):
    def __init__(self, *keys):
        for key in keys:
            if not isinstance(key, Key):
                raise TypeError('key should be instance of Key')
        super().__init__(*keys)

    def to_sql(self):
        return '( %s )' % ', '.join(key.to_sql() for key in self if isinstance(key, Key))


class ValueList(List):
    def __init__(self, *values):
        for value in values:
            if not isinstance(value, Value):
                raise TypeError('value should be instance of value')
        super().__init__(*values)

    def to_sql(self):
        return '( %s )' % ', '.join(value.to_sql() for value in self if isinstance(value, Value))


class SelectList(List):
    def __init__(self, *selects):
        for select in selects:
            if not isinstance(select, (str, Str, Key)):
                raise TypeError('select should be instance one of str Str Key')
        super().__init__(*(Str(select) if isinstance(select, str) else select for select in selects))

    def to_sql(self):
        return '*' if not self \
            else ', '.join(node.to_sql() if isinstance(node, Node) else node
                           for node in self if isinstance(node, (Key, Str, str)))


class Dict(Node, dict):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def keyvalues(self):
        return [KeyValue(k, self[k]) for k in self]

    def to_sql(self):
        return ', '.join('%s = %s' % (Key(k).to_sql(), Value(v).to_sql()) for k, v in self.items())


class ListDict(Node, collections.OrderedDict):
    def __init__(self, *kv_args):
        for kv in kv_args:
            if not isinstance(kv, KeyValue) and not isinstance(kv, (tuple, list)):
                raise TypeError('not accept type in kv: %s' % type(kv))
        super().__init__((kv.key.key, kv.value.value) if isinstance(kv, KeyValue) else kv for kv in kv_args)

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
        other = other if isinstance(other, Node) else None
        if other is None:
            raise TypeError('not accept type')
        return And(self, other)

    def or_(self, other):
        other = other if isinstance(other, Node) else None
        if other is None:
            raise TypeError('not accept type')
        return Or(self, other)

    def to_sql(self):
        if self.left and self.right and self.tree:
            return ' '.join((self.left.to_sql(), self.tree.to_sql(), self.right.to_sql()))
        if self.left or self.right:
            return self.left.to_sql() if self.left else self.right.to_sql()
        return ''


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
        return '%s, %s' % (self.take, self.skip)


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
    def __init__(self, key: str, order):
        self._key = Key(key)
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
        super().__init__(WHERE.from_str(operation) if isinstance(operation, str) else operation,
                         Str(left) if isinstance(left, str) else left,
                         Value(right) if not isinstance(right, Node) else right)

    @property
    def operation(self):
        return self._tree

    def __hash__(self):
        return hash(self.to_sql())

    def to_sql(self):
        return ' '.join(sql for sql in (self.left.to_sql(), self.operation.to_sql(), self.right.to_sql()) if sql)


class WhereTrue(Where):
    def __init__(self):
        super().__init__(WHERE.TRUE, Str('1'), Null())


class WhereStr(Where):
    def __init__(self, str_where: str):
        super().__init__(WHERE.STR, Str(str_where), Null())


class WhereExpression(Where):
    def __init__(self, operation, key: str, value):
        super().__init__(operation, Key(key), value if isinstance(value, Node) else Value(value))

    def to_sql(self):
        if self.operation in (WHERE.EQUAL, WHERE.NOT_EQUAL):
            if not self.right:
                return '%s is NULL' % self.left.to_sql() if self.operation == WHERE.EQUAL \
                    else '%s is not NULL' % self.left.to_sql()
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
        super().__init__(WHERE.IN, key,
                         ValueList(*(value if isinstance(value, Value) else Value(value) for value in values)))


class WhereNotIn(WhereExpression):
    def __init__(self, key: str, *values):
        super().__init__(WHERE.NOT_IN, key,
                         ValueList(*(value if isinstance(value, Value) else Value(value) for value in values)))


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
    def __init__(self, table: str, *to_insert):
        super().__init__(METHOD.INSERT, table)
        self._to_insert = ListDict(*to_insert)

    @property
    def insert(self):
        return self._to_insert

    def __bool__(self):
        return bool(super()) and bool(self.insert)

    def __eq__(self, other):
        if isinstance(other, Insert):
            return super().__eq__(other) and self.insert == other.insert
        return super().__eq__(other)

    def to_sql(self):
        return '%s into %s %s' % (self.method.to_sql(), self.table.to_sql(), self.insert.to_sql()) if self.insert \
            else ''


class Delete(Method):
    def __init__(self, table: str, **kwargs):
        super().__init__(METHOD.DELETE, table)
        self._where = kwargs.get('where', Null())

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
    def __init__(self, table: str, *to_update, **kwargs):
        super().__init__(METHOD.UPDATE, table)
        self._where = kwargs.get('where', Null())
        self._to_update = Dict(**{k if not isinstance(k, Key) else k.key: v if not isinstance(v, Value) else v.value
                                  for k, v in to_update})

    @property
    def where(self):
        return self._where

    @property
    def update(self):
        return self._to_update

    def __bool__(self):
        return bool(super()) and bool(self.update) and bool(self.where)

    def __eq__(self, other):
        if isinstance(other, Update):
            return super().__eq__(other) and self.where == other.where and self.update.__eq__(other.update)
        return super().__eq__(other)

    def to_sql(self):
        return '%s %s set %s where %s' % \
               (self.method.to_sql(), self.table.to_sql(), self.update.to_sql(), self.where.to_sql()) if self else ''


class Select(Method):
    def __init__(self, table: str, *to_select, **kwargs):
        super().__init__(METHOD.SELECT, table)
        self._select = SelectList(*to_select)
        self._where = kwargs.get('where', Null())
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
                where=Null(),
                order=OrderList(),
                limit=Limit())

    @property
    def node(self):
        return self._node

    def clear(self):
        self.node.update(
                where=Null(),
                order=OrderList(),
                limit=Limit())

    def where(self, where):
        self.node['where'] = where if isinstance(where, Node) else WhereStr(where)
        return self

    def or_where(self, where):
        if not self.node['where']:
            return self.where(where)
        self.node['where'] = Or(self.node['where'], where if isinstance(where, Node) else WhereStr(where))
        return self

    def and_where(self, where):
        if not self.node['where']:
            return self.where(where)
        self.node['where'] = And(self.node['where'], where if isinstance(where, Node) else WhereStr(where))
        return self

    def order(self, *args):
        self.node['order'] = OrderList(*args)
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

    def insert(self, *to_insert):
        return Insert(self.node.get('table'), *to_insert)

    def delete(self):
        return Delete(self.node.get('table'), where=self.node.get('where'))

    def update(self, *to_update):
        return Update(self.node.get('table'), *to_update, where=self.node.get('where'))

    def select(self, *selection):
        return Select(self.node.get('table'),
                      *selection,
                      where=self.node.get('where'),
                      order=self.node.get('order'),
                      limit=self.node.get('limit'))


if __name__ == '__main__':
    w = Update('html', KeyValue('id', 3), ('name', 'dgf'), where=WhereIn('id', 1, 2, 3, 4))
    print(w)
