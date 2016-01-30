# coding: utf-8
import unittest

from lib.headers import *


class Function(unittest.TestCase):

    def test_falt_list(self):
        import lib.headers
        test_list = [1, [None, ['c', 'd'], True], 'ab']
        test_list = lib.headers._flat_list(test_list)
        self.assertEqual(test_list, [1, None, 'c', 'd', True, 'ab'])

    def test_convert_header_key(self):
        import lib.headers
        key_1 = 'ab-cd'
        key_2 = 'ab cd'
        key_3 = 'ab_cd'
        key_4 = '-a'
        key_5 = 'Ab-Cd'
        self.assertEqual(lib.headers._convert_header_key(key_1), key_5)
        self.assertEqual(lib.headers._convert_header_key(key_2), key_5)
        self.assertEqual(lib.headers._convert_header_key(key_3), key_5)
        self.assertEqual(lib.headers._convert_header_key(key_4), 'A')

        self.assertRaises(ValueError, lib.headers._convert_header_key, '')


class HeaderValueTest(unittest.TestCase):
    def test_init(self):
        self.assertRaises(ValueError, HeaderValue, '')
        value = 'value'
        params = dict(a=1, b=2)
        headervalue = HeaderValue(value, **params)
        self.assertEqual(headervalue.value, value)
        self.assertEqual(headervalue.params, params)

    def test_str_params(self):
        value = 'value'
        params = dict(a=1, b='2')
        headervalue = HeaderValue(value, **params)
        str_params = headervalue.str_params()
        self.assertIn(str_params, ('a=1;b=2', 'b=2;a=1'))

        headervalue = HeaderValue(value)
        str_params = headervalue.str_params()
        self.assertEqual(str_params, '')

    def test_clear_params(self):
        value = 'value'
        params = dict(a=1, b='2')
        headervalue = HeaderValue(value, **params)
        headervalue.clear_params()
        self.assertEqual(headervalue.params, {})

    def test_has_param(self):
        value = 'value'
        params = dict(a=1, b='2')
        headervalue = HeaderValue(value, **params)
        self.assertTrue(headervalue.has_param('a'))
        self.assertTrue(headervalue.has_param('b'))
        self.assertFalse(headervalue.has_param('A'))

    def test_get_param(self):
        value = 'value'
        params = dict(a=1, b='2')
        headervalue = HeaderValue(value, **params)
        self.assertEqual(headervalue.get_param('a'), 1)
        self.assertEqual(headervalue.get_param('b'), '2')
        self.assertEqual(headervalue.get_param('A'), None)

    def test_del_param(self):
        value = 'value'
        params = dict(a=1, b='2')
        headervalue = HeaderValue(value, **params)
        headervalue.del_param('a')
        self.assertEqual(headervalue.params, dict(b='2'))
        headervalue.del_param('b')
        self.assertEqual(headervalue.params, {})

    def test_set_param(self):
        value = 'value'
        params = dict(a=1, b='2')
        headervalue = HeaderValue(value, **params)
        headervalue.set_param('a', '1')
        self.assertEqual(headervalue.params, dict(a='1', b='2'))
        headervalue.set_param('c', '1')
        self.assertEqual(headervalue.params, dict(a='1', c='1', b='2'))

    def test_is_true(self):
        value = 'value'
        params = dict(a=1, b='2')
        headervalue = HeaderValue(value, **params)
        self.assertTrue(headervalue.is_true())
        headervalue.value = ''
        self.assertFalse(headervalue.is_true())

    def test_is_equal(self):
        self.assertTrue(HeaderValue('value', a=1, b='2', c=None).is_equal(HeaderValue('value', b='2', c=None, a=1)))
        self.assertTrue(HeaderValue('value', b='2', c=None, a=1).is_equal(HeaderValue('value', a=1, b='2', c=None)))
        self.assertTrue(HeaderValue('value', a=None).is_equal('value;a=None'))
        self.assertFalse(HeaderValue('value', a=None).is_equal('value;a='))
        self.assertFalse(HeaderValue('value', a=None).is_equal(object()))

    def test_to_str(self):
        v_1 = HeaderValue('value')
        v_2 = HeaderValue('value', a=1)
        self.assertEqual(v_1.to_str(), 'value')
        self.assertEqual(v_2.to_str(), 'value;a=1')

if __name__ == '__main__':
    unittest.main()
