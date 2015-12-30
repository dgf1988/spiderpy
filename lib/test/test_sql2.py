import unittest
from lib.sqlmaster import *


class MyTestCase(unittest.TestCase):
    def test_key_value(self):
        self.assertEqual(str(SqlKey('aaa')), '`aaa`')
        self.assertEqual(str(SqlValue(1)), '1')
        self.assertEqual(str(SqlValue(True)), 'True')
        self.assertEqual(str(SqlValue(1.7)), '1.7')
        self.assertEqual(str(SqlValue(0)), '0')
        self.assertEqual(str(SqlValue(None)), 'null')
        self.assertEqual(str(SqlValue('aaa')), '"aaa"')
        self.assertEqual(str(SqlValue(SQLORDER.ASC)), 'asc')
        self.assertEqual(str(SqlValue(SQLORDER.DESC)), 'desc')

    def test_ORDER(self):
        self.assertEqual(str(SQLORDER.ASC), 'asc')
        self.assertEqual(str(SQLORDER.DESC), 'desc')
        self.assertRaises(ValueError, SQLORDER.from_str, 'a')
        self.assertRaises(ValueError, SQLORDER.from_object, 'id')
        self.assertEqual(SQLORDER.from_object('asc'), SQLORDER.ASC)
        self.assertEqual(SQLORDER.from_object('dEsc '), SQLORDER.DESC)
        self.assertEqual(SQLORDER.from_object(0), SQLORDER.ASC)
        self.assertEqual(SQLORDER.from_object(0.0), SQLORDER.ASC)
        self.assertEqual(SQLORDER.from_object(1), SQLORDER.DESC)
        self.assertEqual(SQLORDER.from_object(-1), SQLORDER.DESC)
        self.assertEqual(SQLORDER.from_object(0.1), SQLORDER.DESC)
        self.assertEqual(SQLORDER.from_object(False), SQLORDER.ASC)
        self.assertEqual(SQLORDER.from_object(True), SQLORDER.DESC)
        self.assertEqual(SQLORDER.from_object(None), SQLORDER.ASC)
        self.assertEqual(SQLORDER.from_object([]), SQLORDER.ASC)
        self.assertEqual(SQLORDER.from_object({}), SQLORDER.ASC)
        self.assertEqual(SQLORDER.from_object(dict()), SQLORDER.ASC)
        self.assertEqual(SQLORDER.from_object(dict(id=1)), SQLORDER.DESC)
        self.assertEqual(SQLORDER.from_object(SQLORDER.ASC), SQLORDER.ASC)
        self.assertEqual(SQLORDER.from_object(SQLORDER.DESC), SQLORDER.DESC)

    def test_orderby_ordercase(self):
        self.assertTrue(SqlOrderCase('id', SQLORDER.ASC) == SqlOrderAsc('id'))
        self.assertTrue(SqlOrderCase('id', SQLORDER.ASC) == SqlOrderBy('id').asc())
        self.assertEqual(SqlOrderCase('id', SQLORDER.ASC), SqlOrderAsc('id'))
        self.assertEqual(SqlOrderCase('id', SQLORDER.DESC), '`id` desc')
        self.assertEqual(str(SqlOrderDefault('id') + SqlOrderAsc('age') + SqlOrderDesc('name')), '`id` asc,`age` asc,`name` desc')
        self.assertEqual(str(SqlOrderDefault('id') + SqlOrder('age', dict(name='desc'))), '`id` asc,`age` asc,`name` desc')

    def test_order(self):
        self.assertIn(SqlOrder('id', dict(age=' AsC '), dict(key='num_id', order=True)).__str__(),
                      ('`id` asc,`age` asc,`num_id` desc',))
        self.assertEqual(SqlOrder('id', age='asc'), SqlOrder(id=0) + SqlOrder(age=0))
        self.assertIsInstance(SqlOrder('id') + SqlOrder('age'), SqlOrder)
        self.assertEqual(SqlOrder('id') + SqlOrder('age'), SqlOrder('id', 'age'))
        self.assertTrue(SqlOrder('id'))
        self.assertFalse(SqlOrder())
        self.assertEqual(type(SqlOrder('a') + SqlOrder('b')), type(SqlOrder()))
        self.assertEqual(SqlOrder('id', dict(name='deSC'), SqlOrderCase('post', SQLORDER.ASC)).__str__(),
                         '`id` asc,`name` desc,`post` asc')
        self.assertRaises(TypeError, SqlOrder, None)
        self.assertFalse(SqlOrder('id') == 'nnn')

    def test_wherecase(self):
        self.assertFalse(SqlWhereNull())
        self.assertTrue(SqlWhereTrue())
        self.assertEqual(SqlWhereNull(), '')
        self.assertEqual(SqlWhereTrue(), '1')
        self.assertRaises(ValueError, SqlWhereCase, '', SQLWHERETYPE.STR, 'id=0')
        self.assertEqual(SqlWhereCase('a', SQLWHERETYPE.STR, '1'), '1')
        self.assertEqual(SqlWhereStr('a'), 'a')
        self.assertEqual(SqlWhereEqual('id', 0), '`id` = 0')
        self.assertEqual(SqlWhereNotEqual('id', None), '`id` <> null')
        self.assertEqual(SqlWhereLess('id', 0), '`id` < 0')
        self.assertEqual(SqlWhereLessEqual('id', 0), '`id` <= 0')
        self.assertEqual(SqlWhereGreater('id', 0), '`id` > 0')
        self.assertEqual(SqlWhereGreaterEqual('id', 0), '`id` >= 0')
        self.assertEqual(SqlWhereIn('id', 1, 2), '`id` in (1,2)')
        self.assertEqual(SqlWhereNotIn('id', 1, 2), SqlWhereBy('id').not_in(1, 2))
        self.assertEqual(SqlWhereBetween('id', 1, 2), SqlWhereBy.str('`id` between 1 and 2'))
        self.assertEqual(SqlWhereNotBetween('id', 1, 2), SqlWhereCase.from_object(SqlWhereNotBetween('id', 1, 2)))
        self.assertEqual(SqlWhereLike('id', '%abc'), SqlWhereCase.from_object('`id` like "%abc"'))
        self.assertEqual(SqlWhereNotLike('id', '%abc'), SqlWhereCase.from_str('`id` not like "%abc"'))
        self.assertEqual(SqlWhereCase.format_dict(id=9), SqlWhereCase.format_list(SqlWhereEqual('id', 9)))
        self.assertRaises(TypeError, SqlWhereCase.from_object, dict())

    def test_where_note(self):
        self.assertRaises(TypeError, SqlWhereNode, dict(), SQLWHERENODETYPE.AND, dict())
        self.assertEqual(SqlWhereNode('a=1', SQLWHERENODETYPE.AND, 'c=2'),
                         'a=1 and c=2')
        self.assertEqual(SqlWhereAnd('a=b', SqlWhereCase('a', SQLWHERETYPE.BETWEEN, (1, 2))),
                         'a=b and `a` between 1 and 2')
        self.assertEqual(SqlWhereAnd('a=b', SqlWhereCase('a', SQLWHERETYPE.BETWEEN, [1, 2])),
                         'a=b and `a` between 1 and 2')
        self.assertEqual(SqlWhereOr('a=b', SqlWhereCase('a', SQLWHERETYPE.BETWEEN, dict(left=1, right=2))),
                         'a=b or `a` between 1 and 2')
        self.assertEqual(len(SqlWhereOr('a=b', SqlWhereCase('a', SQLWHERETYPE.BETWEEN, dict(left=1, right=2)))), 2)

    def test_where(self):
        self.assertFalse(SqlWhere())
        self.assertEqual(len(SqlWhere()), 0)
        self.assertEqual(SqlWhere(), '')
        self.assertRaises(ValueError, SqlWhere, '')
        self.assertEqual(len(SqlWhere('a=b')), 1)
        self.assertEqual(len(SqlWhere('a=b', id=3)), 2)
        self.assertEqual(len(SqlWhere('a=b', id=3) | SqlWhereTrue()), 3)
        self.assertEqual(len(SqlWhere('a=b', id=3) |
                             SqlWhereTrue() &
                             SqlWhereAnd(SqlWhereEqual('id', 3), SqlWhereEqual('id', 3))), 5)
        self.assertTrue(SqlWhere(id=3))
        self.assertEqual(SqlWhere() | SqlWhereStr('a=b'), SqlWhere('a=b'))

    def test_method(self):
        self.assertFalse(SqlMethod())
        self.assertEqual(SqlMethod(), '')
        self.assertEqual(SqlMethod('test', None), '')
        self.assertEqual(SqlMethod('test', SQLMETHOD.INSERT), 'insert from test')
        self.assertEqual(SqlInsert('tablename'), '')
        self.assertEqual(SqlDelete('tablename'), 'delete from `tablename`')
        self.assertEqual(SqlUpdate('tablename'), '')
        self.assertEqual(SqlSelect('tablename'), 'select * from `tablename`')
        self.assertEqual(SqlSelect('tablename', 1, None, 'a', 'count() as n'),
                         'select 1,None,a,count() as n from `tablename`')

    def test_sql_from(self):
        sql = SqlFrom('html').where(id=3).update(htmlmd5='abcdefg')
        self.assertEqual(SqlFrom('html').where(id=3).update(htmlmd5='abcdefg').to_sql(),
                         'update `html` set `htmlmd5` = "abcdefg" where `id` = 3')
        self.assertEqual(SqlFrom('html').insert(htmlmd5='abcdefg').to_sql(),
                         'insert into `html` (`htmlmd5`) values ("abcdefg")')
        self.assertEqual(SqlFrom('html').where(id=3).delete().to_sql(),
                         'delete from `html` where `id` = 3')
        self.assertEqual(SqlFrom('html').where(id=3).order(id='desc').top(1).skip(2).select('id', 'name').to_sql(),
                         'select id,name from `html` where `id` = 3 order by `id` desc limit 1,2')
        sqlfrom = SqlFrom('html').where(id=3).or_where(name='dgf').order(id='desc').limit(0, 122)
        sql = sqlfrom.select()
        self.assertEqual(sql.to_sql(),
                         'select * from `html` where `id` = 3 or `name` = "dgf" order by `id` desc')
        sql.clear()
        self.assertEqual(sql.to_sql(), '')
        self.assertFalse(sql)
        sql = sqlfrom.select()
        self.assertEqual(sql.to_sql(),
                         'select * from `html` where `id` = 3 or `name` = "dgf" order by `id` desc')
        sqlfrom.clear()
        self.assertEqual(sql.to_sql(), 'select * from `html` where `id` = 3 or `name` = "dgf" order by `id` desc')
        self.assertTrue(sql)


if __name__ == '__main__':
    unittest.main()
