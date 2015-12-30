import unittest
from lib.dbmaster import *


class MyTestCase(unittest.TestCase):
    def test_something(self):
        f = TimestampField(default=FIELDDEFAULT.ON_UPDATE_CURRENT_TIMESTAMP)
        print(UserDbTable.sql_create_table())
        print(UserDbTable(id=1, name='dingguofeng', birth='0000-00-00').to_str())
        print(UserDbTable(id=1, name='dingguofeng', birth='0000-00-00'))


if __name__ == '__main__':
    unittest.main()
