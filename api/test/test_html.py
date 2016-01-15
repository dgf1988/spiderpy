import unittest
from api.html import *
from lib.http import Url
from lib.sqldb import SqlDB
from lib.hash import md5


class TestHtmlObject(unittest.TestCase):
    def setUp(self):
        self.db = SqlDB(user='root', passwd='guofeng001', db='html')
        self.db.open()

    def tearDown(self):
        self.db.close()

    def test_(self):
        Html.Encoding = 'utf-8'
        html = Html(url='http://www.cnbeta.com/')
        html.get()
        if html.save():
            insertid = html.insert(self.db)
            print(insertid)


class TestObjectHtml(unittest.TestCase):
    def setUp(self):
        self.db = SqlDB(user='root', passwd='guofeng001', db='hoetom')
        self.db.open()

    def tearDown(self):
        self.db.close()

    def test_count(self):
        self.assertGreater(HtmlDB.count(self.db), 0)
        print(HtmlDB.count(self.db))

    def test_insert(self):
        pass

    def test_delete(self):
        pass

    def test_get(self):
        gethtml = HtmlDB.get(self.db, 3)
        self.assertEqual(gethtml.id, 3)

        count = HtmlDB.count(self.db, code=200)

    def test_list(self):
        list_html = HtmlDB.list(self.db, 10)
        self.assertEqual(len(list_html), 10)
        for html in list_html:
            self.assertIsInstance(html, HtmlDB)
            print(html.to_json())

if __name__ == '__main__':
    unittest.main()
