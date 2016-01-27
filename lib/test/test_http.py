import unittest
import http

import lib.http


class TestHttpStatus(unittest.TestCase):
    def test_(self):
        print(lib.http.METHOD.__members__)

    def test_CODE(self):
        for code, status in lib.http.CODE.datas():
            self.assertEqual(code, status)

        self.assertNotIn(0, lib.http.CODE)
        self.assertIn(200, lib.http.CODE)

    def test_STATUS(self):
        self.assertEqual(lib.http.STATUS, http.HTTPStatus)

    def test_Status(self):
        status = lib.http.Status(200)
        self.assertEqual(status.status, http.HTTPStatus.OK)
        self.assertEqual(status.code, 200)
        self.assertEqual(status.message, 'OK')
        self.assertEqual(status.description, 'Request fulfilled, document follows')

        self.assertEqual(status, lib.http.Status(http.HTTPStatus.OK))

        code, msg, desc = status
        self.assertEqual(code, 200)
        self.assertEqual(msg, 'OK')
        self.assertEqual(desc, 'Request fulfilled, document follows')

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
