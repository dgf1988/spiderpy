import unittest
import logging

import lib.sql as sql


logging.basicConfig(level=logging.INFO)


class TestNode(unittest.TestCase):
    def test_true(self):
        node = sql.Node()
        self.assertTrue(node)

    def test_equal(self):
        node = sql.Node()
        self.assertEqual(node, sql.Node())
        self.assertEqual(node, '')
        self.assertEqual('', node)
        self.assertNotEqual(node, object())

    def test_to_sql(self):
        node = sql.Node()
        self.assertEqual(node.to_sql(), '')


class TestNull(unittest.TestCase):
    def test_hash(self):
        null = sql.Null()
        self.assertEqual(hash(null), 0)

    def test_is_true(self):
        null = sql.Null()
        self.assertFalse(null)

    def test_is_equal(self):
        null = sql.Null()
        self.assertTrue(null == sql.Null())
        self.assertFalse(sql.Node() == sql.Null())

        self.assertNotEqual(null, sql.Node())
        self.assertNotEqual(null, object())
        self.assertNotEqual(null, 'NULL')
        self.assertNotEqual(null, '')

    def test_to_sql(self):
        null = sql.Null()
        self.assertEqual(null.to_sql(), '')


class TestStr(unittest.TestCase):
    def test_init(self):
        s = sql.Str('')
        self.assertEqual(s.str, '')
        self.assertEqual(s._str, s.str)
        self.assertEqual(type(s.str), str)

    def test_hash(self):
        s = sql.Str('a')
        self.assertEqual(hash(s), hash('a'))

    def test_is_true(self):
        s_1 = sql.Str('')
        s_2 = sql.Str('1')
        self.assertTrue(s_2)
        self.assertFalse(s_1)

    def test_is_equal(self):
        s_1 = sql.Str('')
        s_2 = sql.Str('1')
        self.assertEqual(s_1, '')
        self.assertNotEqual(s_1, s_2)

    def test_to_sql(self):
        self.assertEqual(sql.Str('a'), 'a')


class TestKey(unittest.TestCase):
    def test_init(self):
        self.assertRaises(ValueError, sql.Key, '')

    def test_sql(self):
        self.assertEqual(sql.Key('a').to_sql(), '`a`')


class TestValue(unittest.TestCase):
    def test__init(self):
        a = sql.Value()
        self.assertEqual(a._value, None)

    def test_hash(self):
        a = sql.Value()
        self.assertEqual(hash(a), hash('NULL'))
        self.assertNotEqual(sql.Value('').__hash__(), sql.Value(0).__hash__())

    def test_true(self):
        self.assertFalse(sql.Value())
        self.assertFalse(sql.Value(None))
        self.assertTrue(sql.Value(''))
        self.assertTrue(sql.Value(False))

    def test_equal(self):
        a = sql.Value(None)
        b = sql.Value(False)
        c = sql.Value('')
        d = sql.Value(0)
        self.assertEqual(a, 'NULL')
        self.assertNotEqual(a, b)
        self.assertNotEqual(c, b)
        self.assertNotEqual(c, d)
        self.assertNotEqual(c, '')
        self.assertNotEqual('', c)


class TestKeyValue(unittest.TestCase):
    def test_init(self):
        kv = sql.KeyValue('id')
        self.assertEqual(kv.key, sql.Key('id'))
        self.assertEqual(kv.value, sql.Value())
        kv.value = 4
        self.assertEqual(kv.value, sql.Value(4))

    def test_hash(self):
        kv = sql.KeyValue('id')
        self.assertEqual(kv.__hash__(), sql.Key('id').__hash__())
        self.assertEqual(kv.__hash__(), 'id'.__hash__())

    def test_true(self):
        kv = sql.KeyValue('id')
        self.assertTrue(kv)
        kv._key._str = ''
        self.assertFalse(kv)

    def test_equal(self):
        a = sql.KeyValue('id')
        self.assertEqual(a, sql.KeyValue('id'))
        self.assertEqual(a, '`id` = NULL')

    def test_iter(self):
        k, v = sql.KeyValue('id', 1)
        self.assertEqual(k, sql.Key('id'))
        self.assertEqual(v, sql.Value(1))


class TestSet(unittest.TestCase):
    def test_init(self):
        self.assertRaises(TypeError, sql.Set, '')

    def test_sql(self):
        a = sql.Set(sql.Key('id'), sql.Value('name'))
        self.assertIn(a, ('`id`, "name"', '"name", `id`'))


class TestKeySet(unittest.TestCase):
    def test_init(self):
        a = sql.KeySet()
        self.assertRaises(TypeError, sql.KeySet, '')


class TestValueSet(unittest.TestCase):
    def test_init(self):
        a = sql.ValueSet()
        self.assertRaises(TypeError, sql.ValueSet, '')


class TestList(unittest.TestCase):
    def test_init(self):
        self.assertRaises(TypeError, sql.List, '')


class TestKeyList(unittest.TestCase):
    def test_init(self):
        self.assertRaises(TypeError, sql.KeyList, '')


class TestValueList(unittest.TestCase):
    def test_init(self):
        self.assertRaises(TypeError, sql.ValueList, '')


class TestSelectList(unittest.TestCase):
    def test_init(self):
        a = sql.SelectList('')
        self.assertRaises(TypeError, sql.SelectList, 1)

    def test_sql(self):
        self.assertEqual(sql.SelectList(), '*')
        self.assertEqual(sql.SelectList('a', sql.Key('a')), 'a, `a`')


class TestDict(unittest.TestCase):
    def test_init(self):
        d = sql.Dict(id=3, name='dgf')

    def test_keyvalues(self):
        d = sql.Dict(id=3, name=None)
        for item in d.keyvalues():
            self.assertIsInstance(item, sql.KeyValue)
            k, v = item
            self.assertIsInstance(k, sql.Key)
            self.assertIsInstance(v, sql.Value)

    def test_sql(self):
        self.assertIn(sql.Dict(id=3, name='dgf'), ('`id` = 3, `name` = "dgf"', '`name` = "dgf", `id` = 3'))


class TestListDict(unittest.TestCase):
    def test_init(self):
        ld = sql.ListDict()
        self.assertRaises(TypeError, sql.ListDict, '')

    def test_sql(self):
        self.assertEqual(sql.ListDict(('id', 1), ('name', 'dgf')), '( `id`, `name` ) values ( 1, "dgf" )')


class TestTREE(unittest.TestCase):
    def test_(self):
        self.assertEqual(sql.TREE.AND, 'and')
        self.assertEqual(sql.TREE.OR, 'or')
        self.assertEqual(sql.TREE.BRACKET, '')


class TestTree(unittest.TestCase):
    def test_init(self):
        self.assertRaises(TypeError, sql.Tree, '', sql.Node, sql.Node)
        self.assertRaises(TypeError, sql.Tree, sql.Node, '', sql.Node)
        self.assertRaises(TypeError, sql.Tree, sql.Node, sql.Node, '')
        self.assertEqual(sql.Tree(sql.Str('a'), sql.Str('b'), sql.Str('c')).tree, 'a')
        self.assertEqual(sql.Tree(sql.Str('a'), sql.Str('b'), sql.Str('c')).left, 'b')
        self.assertEqual(sql.Tree(sql.Str('a'), sql.Str('b'), sql.Str('c')).right, 'c')

    def test_iter(self):
        t, l, r = sql.Tree(sql.Str('a'), sql.Str('b'), sql.Str('c'))
        self.assertEqual(t, 'a')
        self.assertEqual(l, 'b')
        self.assertEqual(r, 'c')

    def test_bool(self):
        self.assertTrue(sql.Tree(sql.Str('a'), sql.Str('b'), sql.Str('c')))
        self.assertFalse(sql.Tree(sql.Str(''), sql.Str('b'), sql.Str('c')))
        self.assertTrue(sql.Tree(sql.Str('a'), sql.Str(''), sql.Str('c')))
        self.assertTrue(sql.Tree(sql.Str('a'), sql.Str('b'), sql.Str('')))

    def test_sql(self):
        self.assertEqual(sql.Tree(sql.Str('a'), sql.Str('b'), sql.Str('c')), 'b a c')
        self.assertEqual(sql.Tree(sql.Str(''), sql.Str('b'), sql.Str('c')), 'b')
        self.assertEqual(sql.Tree(sql.Str('a'), sql.Str(''), sql.Str('c')), 'c')
        self.assertEqual(sql.Tree(sql.Str('a'), sql.Str('b'), sql.Str('')), 'b')


class TestAndOrBracket(unittest.TestCase):
    def test_And(self):
        a = sql.And(sql.Str('a'), sql.Str('b'))
        self.assertTrue(a)
        self.assertTrue(sql.And(sql.Str('a'), sql.Str('')))
        self.assertTrue(sql.And(sql.Str(''), sql.Str('b')))
        self.assertFalse(sql.And(sql.Str(''), sql.Str('')))
        self.assertEqual(a, 'a and b')

    def test_Or(self):
        b = sql.Or(sql.Str('a'), sql.Str('b'))
        self.assertTrue(b)
        self.assertTrue(sql.Or(sql.Str('a'), sql.Str('')))
        self.assertTrue(sql.Or(sql.Str(''), sql.Str('b')))
        self.assertFalse(sql.Or(sql.Str(''), sql.Str('')))
        self.assertEqual(b, 'a or b')

    def test_Bracket(self):
        a = sql.Bracket(sql.Str('a'))
        self.assertTrue(a)
        self.assertFalse(sql.Bracket(sql.Str('')))
        self.assertEqual(a, '( a )')


class TestLimit(unittest.TestCase):
    def test_init(self):
        a = sql.Limit()
        self.assertEqual(a.skip, 0)
        self.assertEqual(a.skip, 0)

    def test_bool(self):
        a = sql.Limit()
        self.assertFalse(a)
        self.assertTrue(sql.Limit(1, 0))
        self.assertTrue(sql.Limit(0, 1))

    def test_iter(self):
        a = sql.Limit(1, 2)
        take, skip = a
        self.assertEqual(a.skip, skip)
        self.assertEqual(a.take, take)

    def test_sql(self):
        self.assertEqual(sql.Limit(), '0, 0')
        self.assertEqual(sql.Limit(1), '1, 0')
        self.assertEqual(sql.Limit(1, -2), '1, -2')


class TestOrder(unittest.TestCase):
    def test_ORDER(self):
        self.assertEqual(sql.ORDER.ASC, 'asc')
        self.assertEqual(sql.ORDER.DESC, 'desc')

        self.assertEqual(sql.ORDER.ASC, sql.ORDER.from_object(None))
        self.assertEqual(sql.ORDER.DESC, sql.ORDER.from_object(True))
        self.assertEqual(sql.ORDER.ASC, sql.ORDER.from_object(' AsC  '))
        self.assertEqual(sql.ORDER.DESC, sql.ORDER.from_object(' DesC  '))
        self.assertRaises(ValueError, sql.ORDER.from_str, '')

    def test_order(self):
        # init
        order = sql.Order('id', 'asc')
        self.assertEqual(order.key, sql.Key('id'))
        self.assertEqual(order.order, sql.ORDER.ASC)
        # property
        k, o = order
        self.assertEqual(k, sql.Key('id'))
        self.assertEqual(o, sql.ORDER.ASC)
        # bool
        self.assertTrue(order)
        order._order = None
        self.assertFalse(order)
        # eq
        self.assertEqual(sql.Order('id', True), '`id` desc')
        self.assertEqual(sql.Order('id', None), '`id` asc')
        # asc desc
        self.assertEqual(sql.OrderDesc('id'), sql.Order('id', sql.ORDER.DESC))
        self.assertEqual(sql.OrderAsc('id'), sql.Order('id', sql.ORDER.ASC))

    def test_order_list(self):
        # init
        o = sql.OrderList()
        self.assertFalse(o)
        # asc desc
        o.asc('id')
        self.assertTrue(o)
        self.assertEqual(o, '`id` asc')
        o.desc('name')
        self.assertEqual(o, '`id` asc, `name` desc')


class TestWhere(unittest.TestCase):
    def test_WHERE(self):
        self.assertTrue(hasattr(sql.WHERE.EQUAL, 'to_sql'))
        self.assertTrue(hasattr(sql.WHERE.EQUAL, 'sql'))
        self.assertEqual(sql.WHERE.EQUAL, '=')
        self.assertEqual(sql.WHERE.NOT_BETWEEN, 'not between')

    def test_where(self):
        w = sql.Where('=', 'id', 3)
        self.assertTrue(w)
        self.assertTrue(sql.Where('=', 'id', sql.Value(None)))
        self.assertEqual(w.operation, sql.WHERE.EQUAL)
        self.assertEqual(w, 'id = 3')
        self.assertEqual(sql.Where('=', 'id', '3'), 'id = "3"')

        self.assertEqual(sql.WhereTrue(), '1')
        self.assertEqual(sql.WhereStr('abc'), 'abc')

        self.assertEqual(sql.WhereEqual('id', None), '`id` is NULL')
        self.assertEqual(sql.WhereNotEqual('id', None), '`id` is not NULL')
        self.assertEqual(sql.WhereLess('id', None), '`id` < NULL')
        self.assertEqual(sql.WhereLessEqual('id', sql.Str('')), '`id` <=')
        self.assertEqual(sql.WhereGreater('id', sql.Value()), '`id` > NULL')
        self.assertEqual(sql.WhereGreaterEqual('id', sql.Key('id')), '`id` >= `id`')
        self.assertEqual(sql.WhereIn('id', 1, None, False, ''), '`id` in ( 1, NULL, False, "" )')
        self.assertEqual(sql.WhereNotIn('id'), '`id` not in (  )')
        self.assertEqual(sql.WhereBetween('id', '', None), '`id` between ""')
        self.assertEqual(sql.WhereNotBetween('id', '', False), '`id` not between "" and False')
        self.assertEqual(sql.WhereLike('id', ''), '`id` like ""')
        self.assertRaises(TypeError, sql.WhereNotLike, 'id', 1)
        self.assertEqual(sql.WhereNotLike('id', '%s'), '`id` not like "%s"')


class TestMethod(unittest.TestCase):
    def test_METHOD(self):
        self.assertEqual(sql.METHOD.INSERT, sql.METHOD.from_str('insert'))
        self.assertEqual(sql.METHOD.DELETE, sql.METHOD.from_str('delete'))
        self.assertEqual(sql.METHOD.UPDATE, sql.METHOD.from_str('update'))
        self.assertEqual(sql.METHOD.SELECT, sql.METHOD.from_str('select'))

    def test_method(self):
        self.assertRaises(TypeError, sql.Method, '', 'table')
        self.assertRaises(ValueError, sql.Method, 'insert', '')

        self.assertRaises(NotImplementedError, sql.Method('insert', 'table').to_sql)

    def test_insert(self):
        a = sql.Insert('table', ('id', 1), ('name', 'dgf'))
        self.assertEqual(a, 'insert into `table` ( `id`, `name` ) values ( 1, "dgf" )')

    def test_delete(self):
        a = sql.Delete('table')
        self.assertFalse(a)
        self.assertEqual(a, '')

        a = sql.Delete('table', where=sql.Where('=', 'name', 'dgf'))
        self.assertEqual(a, 'delete from `table` where name = "dgf"')

    def test_update(self):
        a = sql.Update('table')
        self.assertFalse(a)
        self.assertEqual(a, '')

    def test_select(self):
        a = sql.Select('table')
        self.assertTrue(a)
        self.assertEqual(a, 'select * from `table`')





if __name__ == '__main__':
    unittest.main()

