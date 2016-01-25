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
        self.assertEqual(null, sql.Null())
        self.assertNotEqual(sql.Node(), null)
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


class Testvalue(unittest.TestCase):
    def test__init(self):
        a = sql.Value()
        self.assertEqual(a._value, None)

    def test_hash(self):
        a = sql.Value()
        self.assertEqual(hash(a), hash('NULL'))
        self.assertNotEqual(sql.Value('').__hash__(), sql.Value(0).__hash__())

    def test_true(self):
        self.assertTrue(sql.Value(''))
        self.assertTrue(sql.Value())
        self.assertTrue(sql.Value(False))

    def test_equal(self):
        a = sql.Value(None)
        b = sql.Value(False)
        c = sql.Value('')
        d = sql.Value(0)
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
        self.assertEqual(a, sql.Str('`id` = NULL'))
        self.assertEqual(a.to_tuple(), ('id', None))


class TestSet(unittest.TestCase):
    def test_init(self):
        pass


if __name__ == '__main__':
    unittest.main()
