import unittest
from lib.sql import *


class MyTestCase(unittest.TestCase):
    def test_to_str(self):
        print(hash(None), hash(SqlNode()), hash(object()), hash(object()), hash(''), hash(0), hash(True))
        self.assertEqual(type(SqlOrder()), SqlOrder)
        print(SqlWhereLessEqual('a', 1).or_by(SqlWhereNotIn('name', '', 'abc', 1, 0, 0.0, False, None)).bracket().to_sql())
        print(SqlValueList('a', 'b').to_str())

    def test_node(self):
        self.assertTrue(SqlNode)

        node = SqlNode()

        self.assertFalse(node.is_true())

        self.assertTrue(node.is_equal(SqlNode()))

        self.assertEqual(node.to_dict(), dict())

        self.assertEqual(node.to_sql(), '')

    def test_key(self):
        self.assertTrue(SqlKey)

        key = SqlKey()
        self.assertEqual(key.key, '')

        self.assertFalse(key.is_true())
        self.assertTrue(SqlKey('a').is_true())

        self.assertTrue(key.is_equal(SqlKey()))
        self.assertFalse(key.is_equal(SqlKey('a')))

        self.assertEqual(key.to_dict(), dict(key=''))

        self.assertEqual(key.to_sql(), '``')
        self.assertEqual(SqlKey('a').to_sql(), '`a`')

    def test_value(self):
        self.assertTrue(SqlValue)

        value1 = SqlValue()
        value2 = SqlValue('')

        self.assertEqual(value1.value, None)
        self.assertEqual(value2.value, '')

        self.assertTrue(value1.is_true())
        self.assertTrue(value2.is_true())

        self.assertFalse(value1.is_equal(value2))
        self.assertTrue(value1.is_equal(SqlValue()))
        self.assertTrue(value2.is_equal(SqlValue('')))

        self.assertTrue(value1.to_dict() == dict(value=None))
        self.assertTrue(value2.to_dict() == dict(value=''))

        self.assertTrue(value1.to_sql() == 'NULL')
        self.assertTrue(value2.to_sql() == '""')
        self.assertTrue(SqlValue(1).to_sql() == '1')
        self.assertTrue(SqlValue(False).to_sql() == 'False')

    def test_key_value(self):
        self.assertTrue(SqlKeyValue)

        kv1 = SqlKeyValue()
        self.assertFalse(kv1)
        self.assertEqual(kv1, SqlKeyValue())
        self.assertEqual(kv1.to_dict(), dict(key=SqlKey(), value=SqlValue()))
        self.assertEqual(kv1.to_sql(), '`` = NULL')

        kv2 = SqlKeyValue('a')
        self.assertTrue(kv2)
        self.assertNotEqual(kv2, kv1)
        self.assertEqual(kv2, SqlKeyValue('a'))
        self.assertEqual(kv2.to_dict(), dict(key=SqlKey('a'), value=SqlValue()))
        self.assertEqual(kv2.to_sql(), '`a` = NULL')

        kv3 = SqlKeyValue('a', '')
        self.assertTrue(kv3)
        self.assertNotEqual(kv3, kv2)
        self.assertEqual(kv3, SqlKeyValue('a', ''))
        self.assertEqual(kv3.to_dict(), dict(key=SqlKey('a'), value=SqlValue('')))
        self.assertEqual(kv3.to_sql(), '`a` = ""')

    def test_key_value_set(self):
        self.assertTrue(SqlKeyValueSet)

        s1 = SqlKeyValueSet()
        self.assertFalse(s1)
        self.assertEqual(s1, SqlKeyValueSet())
        self.assertEqual(s1.to_dict(), dict(set=set()))
        self.assertEqual(s1.to_sql(), '')

        s2 = SqlKeyValueSet(a='', b=None, c=0, d=False)
        self.assertTrue(s2)
        self.assertEqual(s2, SqlKeyValueSet(d=False, c=0, b=None, a=''))
        self.assertEqual(s2.to_dict(), dict(set=set([
            SqlKeyValue('a', ''), SqlKeyValue('b'), SqlKeyValue('c', 0), SqlKeyValue('d', False)])))

        s3 = SqlKeyValueSet(id=None, b='')
        self.assertIn(s3.to_sql(), ('`id` = NULL,`b` = ""', '`b` = "",`id` = NULL'))
        s3.set.add(SqlNode())
        self.assertFalse(s3.is_true())

    def test_table(self):
        self.assertTrue(SqlTable)

        t1 = SqlTable()
        self.assertFalse(t1)
        self.assertEqual(t1, SqlKey())
        self.assertEqual(t1.to_dict(), dict(table=t1.table))
        self.assertEqual(t1.to_sql(), '``')

    def test_table_set(self):
        self.assertTrue(SqlTableSet)

        s1 = SqlTableSet()
        self.assertFalse(s1)
        self.assertEqual(s1, SqlTableSet())
        self.assertEqual(s1.to_dict(), dict(set=set()))
        self.assertEqual(s1.to_sql(), '')

        s2 = SqlTableSet('a', 'a')
        self.assertTrue(s2)
        self.assertEqual(s2, SqlTableSet('a'))
        self.assertEqual(s2.to_dict(), dict(set=set([SqlTable('a')])))
        self.assertEqual(s2.to_sql(), '`a`')

    def test_limit(self):
        self.assertTrue(SqlLimit)

        a = SqlLimit()
        self.assertFalse(a)
        self.assertEqual(a, SqlLimit())
        self.assertEqual(a.to_dict(), dict(top=0, skip=0))
        self.assertEqual(a.to_sql(), '0,0')

        b = SqlLimit(1)
        self.assertTrue(b)
        self.assertNotEqual(b, a)
        self.assertEqual(b, SqlLimit(1))
        self.assertEqual(b.to_dict(), dict(top=1, skip=0))
        self.assertEqual(b.to_sql(), '1,0')


class TestWhere(unittest.TestCase):
    def test_where(self):
        w = SqlWhere()

        self.assertFalse(w)
        self.assertEqual(w, SqlWhere())
        self.assertEqual(w, '')
        self.assertNotEqual(w, SqlNode())
        self.assertNotEqual(w, ' ')
        self.assertEqual(w.to_dict(), SqlWhere().to_dict())
        self.assertEqual(w.to_dict(), dict(type=SQLWHERE.NULL, left=SqlNode(), right=SqlNode()))
        self.assertEqual(w.to_sql(), '')

    def test_where_null(self):
        null = SqlWhereNull()

        self.assertFalse(null)

        self.assertEqual(null, SqlWhereNull())
        self.assertEqual(null, SqlWhere())
        self.assertNotEqual(null, SqlNode())

        self.assertEqual(null.to_dict(), dict(type=SQLWHERE.NULL, child=None))

        self.assertEqual(null.to_sql(), '')

    def test_where_true(self):
        true = SqlWhereTrue()

        self.assertTrue(true)

        self.assertEqual(true, SqlWhereTrue())
        self.assertNotEqual(true, SqlWhere())

        self.assertEqual(true.to_dict(), dict(type=SQLWHERE.TRUE, child=1))

        self.assertEqual(true.to_sql(), '1')

    def test_where_str(self):
        wstr_1 = SqlWhereStr('')
        self.assertFalse(wstr_1)
        self.assertEqual(wstr_1, SqlWhereStr(''))
        self.assertEqual(wstr_1.to_dict(), dict(type=SQLWHERE.STR, child=wstr_1.left))
        self.assertEqual(wstr_1.to_sql(), '')

        wstr_2 = SqlWhereStr('a=1')
        self.assertTrue(wstr_2)
        self.assertEqual(wstr_2, SqlWhereStr('a=1'))
        self.assertEqual(wstr_2.to_dict(), dict(type=SQLWHERE.STR, child=SqlNodeStr('a=1')))
        self.assertEqual(wstr_2.to_sql(), 'a=1')

        self.assertNotEqual(wstr_1, wstr_2)
        self.assertEqual(wstr_1, SqlWhere())
        self.assertNotEqual(wstr_2, SqlWhere())

    def test_where_bracket(self):
        sub_1 = SqlWhereBracket()
        self.assertFalse(sub_1)
        self.assertEqual(sub_1, SqlWhereBracket())
        self.assertEqual(sub_1.to_dict(), dict(type=SQLWHERE.BRACKET, child=SqlWhere()))
        self.assertEqual(sub_1.to_sql(), '()')

        sub_2 = SqlWhereBracket(SqlWhereTrue())
        self.assertTrue(sub_2)
        self.assertEqual(sub_2, SqlWhereBracket(SqlWhereTrue()))
        self.assertEqual(sub_2.to_dict(), dict(type=SQLWHERE.BRACKET, child=SqlWhereTrue()))
        self.assertEqual(sub_2.to_sql(), '(1)')

        self.assertNotEqual(sub_1, sub_2)
        self.assertEqual(sub_1, '()')
        self.assertEqual(sub_2, '(1)')

    def test_where_node(self):
        node_1 = SqlWhereNode()
        self.assertFalse(node_1)
        self.assertEqual(node_1, '')
        self.assertEqual(node_1, SqlWhereNull())
        self.assertEqual(node_1, SqlWhere())
        self.assertEqual(node_1.to_dict(), dict(type=SQLWHERE.AND, left=SqlNode(), right=SqlNode()))
        self.assertEqual(node_1.to_sql(), '')

        node_2 = SqlWhereNode(left=SqlWhereTrue())
        self.assertTrue(node_2)
        self.assertEqual(node_2, '1')
        self.assertEqual(node_2, SqlWhereNode(left=SqlWhereTrue()))
        self.assertNotEqual(node_2, SqlWhere())
        self.assertEqual(node_2.to_dict(), dict(type=SQLWHERE.AND, left=SqlWhereTrue(), right=SqlNode()))
        self.assertEqual(node_2.to_sql(), '1')
        node_2.__type__ = SQLWHERE.NULL
        self.assertFalse(node_2)

        node_3 = SqlWhereNode(left=SqlWhereNull())
        self.assertFalse(node_3)

        self.assertEqual(node_1, node_3)
        self.assertNotEqual(node_1, node_2)

    def test_where_and(self):
        a_1 = SqlWhereAnd()
        self.assertFalse(a_1)
        self.assertEqual(a_1, '')
        self.assertEqual(a_1, SqlWhereNode())
        self.assertEqual(a_1, SqlWhere())
        self.assertNotEqual(a_1, SqlNode())
        self.assertEqual(a_1.to_dict(), dict(type=SQLWHERE.AND, left=SqlNode(), right=SqlNode()))
        self.assertEqual(a_1.to_sql(), '')

        a_2 = SqlWhereAnd(SqlWhereNull(), SqlWhereTrue())
        self.assertTrue(a_2)
        self.assertEqual(a_2, '1')
        self.assertEqual(a_2.to_dict(), dict(type=a_2.type, left=a_2.left, right=a_2.right))
        self.assertEqual(a_2.to_sql(), '1')

        a_3 = SqlWhereAnd(SqlWhereStr('a=1'), SqlWhereTrue())
        self.assertTrue(a_3)
        self.assertEqual(a_3, 'a=1 and 1')
        self.assertEqual(a_3, SqlWhereNode(SQLWHERE.AND, SqlWhereStr('a=1'), SqlWhereTrue()))
        self.assertEqual(a_3.to_dict(), dict(type=a_3.type, left=a_3.left, right=a_3.right))
        self.assertEqual(a_3.to_sql(), 'a=1 and 1')

        self.assertNotEqual(a_1, a_2)
        self.assertNotEqual(a_2, a_3)
        self.assertNotEqual(a_1, a_3)

    def test_where_or(self):
        a = SqlWhereOr(SqlWhereNull(), SqlWhereTrue())
        self.assertTrue(a)
        self.assertEqual(a, '1')
        self.assertEqual(a, SqlWhereNode(SQLWHERE.OR, SqlWhereNull(), SqlWhereTrue()))
        self.assertEqual(a.to_dict(), dict(type=SQLWHERE.OR, left=SqlWhereNull(), right=SqlWhereTrue()))
        self.assertEqual(a.to_sql(), '1')

    def test_where_and_or_by(self):
        a = SqlWhereAnd(SqlWhereEqual('a', 1), SqlWhereIn('b', 'a', 'b'))
        self.assertEqual(a, SqlWhereEqual('a', 1).and_by(SqlWhereIn('b', 'a', 'b')))
        b = a.or_by(SqlWhereStr('c=1'))


if __name__ == '__main__':
    unittest.main()
