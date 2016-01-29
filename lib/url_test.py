import unittest
from lib.url import *
import lib.url


class MyTestCase(unittest.TestCase):
    def test_parse(self):
        url_parse = parse('/')
        self.assertIsInstance(url_parse, lib.url.UrlParse)
        self.assertTrue(url_parse.is_true())
        self.assertTrue(url_parse.to_str() == url_parse.str_url())
        self.assertTrue(url_parse.to_str() == '/')


if __name__ == '__main__':
    unittest.main()
