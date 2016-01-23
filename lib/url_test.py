import unittest
from lib.url import *


class MyTestCase(unittest.TestCase):
    def test_parse(self):
        url_parse = parse('/')
        self.assertIsInstance(url_parse, UrlParse)
        self.assertTrue(url_parse.is_true())
        self.assertTrue(url_parse.to_str() == url_parse.str_url())
        self.assertTrue(url_parse.to_str() == '/')


if __name__ == '__main__':
    unittest.main()
