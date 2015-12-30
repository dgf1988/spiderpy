import unittest
from lib.sql import *


class TestSql(unittest.TestCase):
    def test_whereCase_str(self):
        self.assertEquals(str(WhereBy('name') == 90), '`name` = 90')
        self.assertEquals(str(WhereBy('name') > 'dingguofeng'), '`name` > "dingguofeng"')
        self.assertEquals(str(WhereBy('name') < 'dingguofeng'), '`name` < "dingguofeng"')
        self.assertEquals(str(WhereBy('name') >= 9), '`name` >= 9')
        self.assertEquals(str(WhereBy('name') <= True), '`name` <= True')
        self.assertEquals(str(WhereBy('name') != False), '`name` <> False')
        self.assertEquals(str(WhereBy('name').Between(1, 2)), '`name` BETWEEN 1 AND 2')
        self.assertEquals(str(WhereBy('name').Not_between(1, 2)), '`name` NOT BETWEEN 1 AND 2')
        self.assertEquals(str(WhereBy('name').In(0, True, False, '', 'hi')),
                          '`name` IN ( 0,True,False,"","hi" )')
        self.assertEquals(str(WhereBy('name').Not_in(0, True, False, '', 'hi')),
                          '`name` NOT IN ( 0,True,False,"","hi" )')
        self.assertEquals(str(WhereBy('key').Like('%中国_')), '`key` LIKE "%中国_"')
        self.assertEquals(str(WhereBy('key').Not_like('%中国_')), '`key` NOT LIKE "%中国_"')

    def test_where_(self):
        self.assertEquals(str(
            Where(
                WhereGreater('id', 9)
            ).And(
                WhereNotLike('name', 'weiqi%')
            ).Or(
                WhereIn('playerid', '0', '3') & WhereLessEqual('class', 99) | WhereNotEqual('id', 9)
            ).Or(
                WhereBetween('age', True, 2) | (WhereEquel('id', 1) | WhereLess('name', True))
            ))
            , '`id` > 9 '
              'AND `name` NOT LIKE "weiqi%" OR '
              '( `playerid` IN ( "0","3" ) AND `class` <= 99 OR `id` <> 9 ) '
              'OR ( `age` BETWEEN True AND 2 OR ( `id` = 1 OR `name` < True ) )'
        )

    def test_sql(self):
        sql = Sql().table('html').where(id='9').order(id='aSC').limit(9).select('b', 'a').to_sql()
        self.assertEqual(sql, 'select b,a from `html` where `id` = "9" order by id ASC limit 9')
        sql = Sql().table('html').set(id=4).insert().to_sql()
        self.assertEqual(sql, 'insert into `html` set `id`=4')
        sql = Sql().table('html').where(id=4, name='dgf').delete().to_sql()
        self.assertIn(sql,
                      ('delete from `html` where `id` = 4 AND `name` = "dgf"',
                       'delete from `html` where `name` = "dgf" AND `id` = 4'))
        sql = Sql().table('html').set(id=5).where(id=4, name='dgf').update().to_sql()
        self.assertIn(sql,
                      ('update `html` set `id`=5 where `id` = 4 AND `name` = "dgf"',
                       'update `html` set `id`=5 where `name` = "dgf" AND `id` = 4'))


if __name__ == '__main__':
    unittest.main()
