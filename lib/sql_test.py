import unittest
import logging

import lib.sql as sql


logging.basicConfig(level=logging.INFO)


class TestNode(unittest.TestCase):
    def test_hash(self):
        node = sql.Node()
        logging.info('object.hash() %s %s sql.Node().hash() %s' % (hash(object()), hash(object()), hash(sql.Node())))
        self.assertEqual(node.hash(), hash(node))
        self.assertNotEqual(node.hash(), hash(object()))

    def test_is_true(self):
        node = sql.Node()
        self.assertFalse(node)
        self.assertEqual(node.is_true(), bool(node))

    def test_is_equal(self):
        node = sql.Node()
        self.assertTrue(node.is_equal(sql.Node()))
        self.assertEqual(node, sql.Node())
        self.assertEqual(node, '')
        self.assertNotEqual(node, object())

    def test_to_dict(self):
        node = sql.Node()
        self.assertIsInstance(node.to_dict(), dict)
        self.assertEqual(node.to_dict(), dict())

    def test_to_sql(self):
        node = sql.Node()
        self.assertEqual(node.to_sql(), '')


class TestNull(unittest.TestCase):
    def test_hash(self):
        null = sql.Null()
        logging.info('hash()=> None=%s 0=%s ""=%s object()=%s' % (hash(None), hash(0), hash(''), hash(object())))
        self.assertEqual(null.hash(), hash(0))
        self.assertEqual(hash(null), hash(0))
        self.assertEqual(hash(null), hash(''))
        self.assertNotEqual(hash(null), hash(None))

    def test_is_true(self):
        null = sql.Null()
        self.assertFalse(null)
        self.assertFalse(null.is_true())

    def test_is_equal(self):
        null = sql.Null()
        self.assertEqual(null, sql.Null())
        self.assertNotEqual(sql.Node(), null)
        self.assertNotEqual(null, object())
        self.assertNotEqual(null, 'NULL')
        self.assertNotEqual(null, '')

    def test_to_dict(self):
        null = sql.Null()
        self.assertEqual(null.to_dict(), dict())

    def test_to_sql(self):
        null = sql.Null()
        self.assertEqual(null.to_sql(), 'NULL')


class TestStr(unittest.TestCase):
    def test_init(self):
        s = sql.Str('')
        self.assertEqual(s.str, '')
        self.assertEqual(s._str, s.str)
        self.assertEqual(type(s.str), str)

    def test_hash(self):
        s = sql.Str('')
        self.assertEqual(hash(s), hash(''))

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

    def test_to_dict(self):
        self.assertEqual(sql.Str('').to_dict(), dict(str=''))

    def test_to_sql(self):
        self.assertEqual(sql.Str('a'), 'a')


class TestKey(unittest.TestCase):
    def test_init(self):
        self.assertRaises(ValueError, sql.Key, '')

    def test_dict(self):
        self.assertEqual(sql.Key('a').to_dict(), dict(key='a'))

    def test_sql(self):
        self.assertEqual(sql.Key('a').to_sql(), '`a`')


class Testvalue(unittest.TestCase):
    def test__init(self):
        a = sql.Value()
        self.assertEqual(a._value, None)
        self.assertEqual(a.value, a._value)

    def test_hash(self):
        a = sql.Value()
        self.assertEqual(hash(a), a.hash())
        self.assertNotEqual(hash(a), hash(None))
        self.assertEqual(hash(a), hash('NULL'))
        self.assertNotEqual(sql.Value('').hash(), sql.Value(0).hash())

    def test_true(self):
        self.assertTrue(sql.Value(''))
        self.assertTrue(sql.Value())
        self.assertTrue(sql.Value(False))

    def test_equal(self):
        a = sql.Value(None)
        b = sql.Value(False)
        c = sql.Value('')
        d = sql.Value(0)
        e = sql.Value(sql.Null())
        self.assertNotEqual(a, b)
        self.assertNotEqual(c, b)
        self.assertNotEqual(c, d)
        self.assertNotEqual(d, e)
        self.assertNotEqual(c, '')
        self.assertNotEqual('', c)


if __name__ == '__main__':
    unittest.main()
