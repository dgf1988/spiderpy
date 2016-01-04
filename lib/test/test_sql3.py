import unittest
from lib.sql import *
import ast


class MyTestCase(unittest.TestCase):
    def test_to_str(self):
        print(hash(None), hash(Node()), hash(object()), hash(object()), hash(''), hash(0), hash(True))
        self.assertEqual(type(Order()), Order)
        print(WhereLessEqual('a', 1).or_by(WhereNotIn('name', '', 'abc', 1, 0, 0.0, False, None)).bracket_self().to_sql())
        print(ValueList('a', 'b').to_str())
        node = ast.parse('(id == 6 or name=="dgf") and (date==0)')
        print(ast.dump(node))

    def test_node(self):
        self.assertTrue(Node)

        node = Node()

        self.assertFalse(node.is_true())

        self.assertTrue(node.is_equal(Node()))

        self.assertEqual(node.to_dict(), dict())

        self.assertEqual(node.to_sql(), '')

    def test_key(self):
        self.assertTrue(Key)

        key = Key()
        self.assertEqual(key.key, '')

        self.assertFalse(key.is_true())
        self.assertTrue(Key('a').is_true())

        self.assertTrue(key.is_equal(Key()))
        self.assertFalse(key.is_equal(Key('a')))

        self.assertEqual(key.to_dict(), dict(key=''))

        self.assertEqual(key.to_sql(), '``')
        self.assertEqual(Key('a').to_sql(), '`a`')

    def test_value(self):
        self.assertTrue(Value)

        value1 = Value()
        value2 = Value('')

        self.assertEqual(value1.value, None)
        self.assertEqual(value2.value, '')

        self.assertTrue(value1.is_true())
        self.assertTrue(value2.is_true())

        self.assertFalse(value1.is_equal(value2))
        self.assertTrue(value1.is_equal(Value()))
        self.assertTrue(value2.is_equal(Value('')))

        self.assertTrue(value1.to_dict() == dict(value=None))
        self.assertTrue(value2.to_dict() == dict(value=''))

        self.assertTrue(value1.to_sql() == 'NULL')
        self.assertTrue(value2.to_sql() == '""')
        self.assertTrue(Value(1).to_sql() == '1')
        self.assertTrue(Value(False).to_sql() == 'False')

    def test_key_value(self):
        self.assertTrue(KeyValue)

        kv1 = KeyValue()
        self.assertFalse(kv1)
        self.assertEqual(kv1, KeyValue())
        self.assertEqual(kv1.to_dict(), dict(key=Key(), value=Value()))
        self.assertEqual(kv1.to_sql(), '`` = NULL')

        kv2 = KeyValue('a')
        self.assertTrue(kv2)
        self.assertNotEqual(kv2, kv1)
        self.assertEqual(kv2, KeyValue('a'))
        self.assertEqual(kv2.to_dict(), dict(key=Key('a'), value=Value()))
        self.assertEqual(kv2.to_sql(), '`a` = NULL')

        kv3 = KeyValue('a', '')
        self.assertTrue(kv3)
        self.assertNotEqual(kv3, kv2)
        self.assertEqual(kv3, KeyValue('a', ''))
        self.assertEqual(kv3.to_dict(), dict(key=Key('a'), value=Value('')))
        self.assertEqual(kv3.to_sql(), '`a` = ""')

    def test_key_value_set(self):
        self.assertTrue(Sets)

        s1 = Sets()
        self.assertFalse(s1)
        self.assertEqual(s1, Sets())
        self.assertEqual(s1.to_dict(), dict())
        self.assertEqual(s1.to_sql(), '')

        s2 = Sets(a='', b=None, c=0, d=False)
        self.assertTrue(s2)
        self.assertEqual(s2, Sets(d=False, c=0, b=None, a=''))
        self.assertEqual(s2.to_dict(), dict(a='', b=None, c=0, d=False))

        s3 = Sets(id=None, b='')
        self.assertIn(s3.to_sql(), ('`id` = NULL,`b` = ""', '`b` = "",`id` = NULL'))

    def test_table(self):
        self.assertTrue(Table)

        t1 = Table()
        self.assertFalse(t1)
        self.assertEqual(t1, Key())
        self.assertEqual(t1.to_dict(), dict(table=t1.table))
        self.assertEqual(t1.to_sql(), '``')

    def test_table_set(self):
        self.assertTrue(TableSet)

        s1 = TableSet()
        self.assertFalse(s1)
        self.assertEqual(s1, TableSet())
        self.assertEqual(s1.to_dict(), dict(set=set()))
        self.assertEqual(s1.to_sql(), '')

        s2 = TableSet('a', 'a')
        self.assertTrue(s2)
        self.assertEqual(s2, TableSet('a'))
        self.assertEqual(s2.to_dict(), dict(set=set([Table('a')])))
        self.assertEqual(s2.to_sql(), '`a`')
        s2.set.add(Table('a'))
        self.assertEqual(s2.to_sql(), '`a`')

    def test_limit(self):
        self.assertTrue(Limit)

        a = Limit()
        self.assertFalse(a)
        self.assertEqual(a, Limit())
        self.assertEqual(a.to_dict(), dict(take=0, skip=0))
        self.assertEqual(a.to_sql(), '0,0')

        b = Limit(1)
        self.assertTrue(b)
        self.assertNotEqual(b, a)
        self.assertEqual(b, Limit(1))
        self.assertEqual(b.to_dict(), dict(take=1, skip=0))
        self.assertEqual(b.to_sql(), '1,0')


class TestWhere(unittest.TestCase):
    def test_where(self):
        w = Where()

        self.assertFalse(w)
        self.assertEqual(w, Where())
        self.assertEqual(w, '')
        self.assertNotEqual(w, Node())
        self.assertNotEqual(w, ' ')
        self.assertEqual(w.to_dict(), Where().to_dict())
        self.assertEqual(w.to_dict(), dict(type=WHERE.NULL, left=Node(), right=Node()))
        self.assertEqual(w.to_sql(), '')

    def test_where_null(self):
        null = WhereNull()

        self.assertFalse(null)

        self.assertEqual(null, WhereNull())
        self.assertEqual(null, Where())
        self.assertNotEqual(null, Node())

        self.assertEqual(null.to_dict(), dict(type=WHERE.NULL, child=None))

        self.assertEqual(null.to_sql(), '')

    def test_where_true(self):
        true = WhereTrue()

        self.assertTrue(true)

        self.assertEqual(true, WhereTrue())
        self.assertNotEqual(true, Where())

        self.assertEqual(true.to_dict(), dict(type=WHERE.TRUE, child=1))

        self.assertEqual(true.to_sql(), '1')

    def test_where_str(self):
        wstr_1 = WhereStr('')
        self.assertFalse(wstr_1)
        self.assertEqual(wstr_1, WhereStr(''))
        self.assertEqual(wstr_1.to_dict(), dict(type=WHERE.STR, child=wstr_1.left))
        self.assertEqual(wstr_1.to_sql(), '')

        wstr_2 = WhereStr('a=1')
        self.assertTrue(wstr_2)
        self.assertEqual(wstr_2, WhereStr('a=1'))
        self.assertEqual(wstr_2.to_dict(), dict(type=WHERE.STR, child=Str('a=1')))
        self.assertEqual(wstr_2.to_sql(), 'a=1')

        self.assertNotEqual(wstr_1, wstr_2)
        self.assertEqual(wstr_1, Where())
        self.assertNotEqual(wstr_2, Where())

    def test_where_bracket(self):
        sub_1 = WhereBracket()
        self.assertFalse(sub_1)
        self.assertEqual(sub_1, WhereBracket())
        self.assertEqual(sub_1.to_dict(), dict(type=WHERE.BRACKET, child=Where()))
        self.assertEqual(sub_1.to_sql(), '()')

        sub_2 = WhereBracket(WhereTrue())
        self.assertTrue(sub_2)
        self.assertEqual(sub_2, WhereBracket(WhereTrue()))
        self.assertEqual(sub_2.to_dict(), dict(type=WHERE.BRACKET, child=WhereTrue()))
        self.assertEqual(sub_2.to_sql(), '(1)')

        self.assertNotEqual(sub_1, sub_2)
        self.assertEqual(sub_1, '()')
        self.assertEqual(sub_2, '(1)')

    def test_where_node(self):
        node_1 = WhereNode()
        self.assertFalse(node_1)
        self.assertEqual(node_1, '')
        self.assertEqual(node_1, WhereNull())
        self.assertEqual(node_1, Where())
        self.assertEqual(node_1.to_dict(), dict(type=WHERE.AND, left=Node(), right=Node()))
        self.assertEqual(node_1.to_sql(), '')

        node_2 = WhereNode(left=WhereTrue())
        self.assertTrue(node_2)
        self.assertEqual(node_2, '1')
        self.assertEqual(node_2, WhereNode(left=WhereTrue()))
        self.assertNotEqual(node_2, Where())
        self.assertEqual(node_2.to_dict(), dict(type=WHERE.AND, left=WhereTrue(), right=Node()))
        self.assertEqual(node_2.to_sql(), '1')
        node_2.__type__ = WHERE.NULL
        self.assertFalse(node_2)

        node_3 = WhereNode(left=WhereNull())
        self.assertFalse(node_3)

        self.assertEqual(node_1, node_3)
        self.assertNotEqual(node_1, node_2)

    def test_where_and(self):
        a_1 = WhereAnd()
        self.assertFalse(a_1)
        self.assertEqual(a_1, '')
        self.assertEqual(a_1, WhereNode())
        self.assertEqual(a_1, Where())
        self.assertNotEqual(a_1, Node())
        self.assertEqual(a_1.to_dict(), dict(type=WHERE.AND, left=Node(), right=Node()))
        self.assertEqual(a_1.to_sql(), '')

        a_2 = WhereAnd(WhereNull(), WhereTrue())
        self.assertTrue(a_2)
        self.assertEqual(a_2, '1')
        self.assertEqual(a_2.to_dict(), dict(type=a_2.type, left=a_2.left, right=a_2.right))
        self.assertEqual(a_2.to_sql(), '1')

        a_3 = WhereAnd(WhereStr('a=1'), WhereTrue())
        self.assertTrue(a_3)
        self.assertEqual(a_3, 'a=1 and 1')
        self.assertEqual(a_3, WhereNode(WHERE.AND, WhereStr('a=1'), WhereTrue()))
        self.assertEqual(a_3.to_dict(), dict(type=a_3.type, left=a_3.left, right=a_3.right))
        self.assertEqual(a_3.to_sql(), 'a=1 and 1')

        self.assertNotEqual(a_1, a_2)
        self.assertNotEqual(a_2, a_3)
        self.assertNotEqual(a_1, a_3)

    def test_where_or(self):
        a = WhereOr(WhereNull(), WhereTrue())
        self.assertTrue(a)
        self.assertEqual(a, '1')
        self.assertEqual(a, WhereNode(WHERE.OR, WhereNull(), WhereTrue()))
        self.assertEqual(a.to_dict(), dict(type=WHERE.OR, left=WhereNull(), right=WhereTrue()))
        self.assertEqual(a.to_sql(), '1')

    def test_where_and_or_by(self):
        a = WhereAnd(WhereEqual('a', 1), WhereIn('b', 'a', 'b'))
        self.assertEqual(a, WhereEqual('a', 1).and_by(WhereIn('b', 'a', 'b')))
        b = a.or_by(WhereStr('c=1'))


if __name__ == '__main__':
    unittest.main()
