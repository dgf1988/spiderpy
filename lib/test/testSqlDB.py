from lib.sqldb import SqlDB, ORDER
import unittest


class TestSqlDb(unittest.TestCase):
    def test_(self):
        with SqlDB(user='root', passwd='guofeng001') as db:
            listplayer = db.db('weiqi').table('player').limit(10, 5).order(id=True, p_posted='').select('id', 'p_name', 'p_posted')
            strout = '\n'.join([str(each) for each in listplayer])
            print(strout)


if __name__ == '__main__':
    unittest.main()
