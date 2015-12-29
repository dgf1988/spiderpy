# -*- coding: utf-8 -*-
from lib.db import DB
import unittest


class Testdb(unittest.TestCase):
    def test_(self):
        with DB(user='root', passwd='guofeng001', db='html') as db:
            if db.execute('select * from html'):
                for each in db.fetchall():
                    print(each)


if __name__ == '__main__':
    unittest.main()
