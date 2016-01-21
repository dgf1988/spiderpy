import unittest
import lib.http


class MyTestCase(unittest.TestCase):
    def test_something(self):
        pass

    def test_status(self):
        status = lib.http.Status(404)
        self.assertEqual(status.to_str(), '404 NOT FOUND')

    def test_method(self):
        method = lib.http.METHOD.GET
        self.assertEqual(method, lib.http.METHOD.GET)
        self.assertEqual(method.to_str(), 'GET')
        self.assertEqual(method, 'GET')

        method = lib.http.METHOD.POST
        self.assertEqual(method, lib.http.METHOD.POST)
        self.assertEqual(method.to_str(), 'POST')
        self.assertEqual(method, 'POST')

        self.assertEqual(lib.http.METHOD.GET, lib.http.METHOD.from_str('GET'))
        self.assertEqual(lib.http.METHOD.POST, lib.http.METHOD.from_str('POST'))
        self.assertEqual(None, lib.http.METHOD.from_str('other'))


if __name__ == '__main__':
    unittest.main()
