import unittest
from lib.sql3 import *


class MyTestCase(unittest.TestCase):
    def test_to_str(self):
        print(hash(None), hash(SqlNode()), hash(object()), hash(''), hash(0), hash(True))
        self.assertEqual(type(SqlOrder()), SqlOrder)
        print(SqlWhereLessEqual('a', 1).to_sql())

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

if __name__ == '__main__':
    unittest.main()
