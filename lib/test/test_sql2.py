import unittest
from lib.sqlmaster import *


class TestSqlMaster(unittest.TestCase):
    def test_SqlObject(self):
        # 测试类
        self.assertTrue(SqlObject)
        # 测试实例
        # 基类实例均为假
        self.assertFalse(SqlObject())
        self.assertFalse(SqlObject().is_true())
        # 基类实例比较都为假
        self.assertFalse(SqlObject().is_equal(SqlObject()))
        self.assertFalse(SqlObject().is_equal(None))
        self.assertFalse(SqlObject().is_equal(0))
        self.assertFalse(SqlObject().is_equal(1))
        self.assertFalse(SqlObject() == '')
        self.assertFalse(SqlObject() == 'a')
        # 基类的字典化接口，输出空字典
        self.assertEqual(SqlObject().to_dict(), dict())
        # 基类的SQL输出接口，输出空语句
        self.assertEqual(SqlObject().to_sql(), '')

    def test_SqlKey(self):
        # 存在类
        self.assertTrue(SqlKey)
        self.assertRaises(ValueError, SqlKey, '')
        # 实例测试
        key = SqlKey('a')
        self.assertTrue(key)
        self.assertTrue(isinstance(key, SqlObject))
        self.assertEqual(key.__key__, 'a')
        key.__key__ = ''
        self.assertFalse(key)

        self.assertEqual(SqlKey('a'), SqlKey('a'))
        self.assertNotEqual(SqlKey('a'), SqlKey('b'))
        self.assertNotEqual(SqlKey('a'), SqlObject())
        self.assertNotEqual(SqlKey('a'), '')

        self.assertEqual(SqlKey('a').to_sql(), '`a`')
        self.assertEqual(SqlKey('a').to_dict(), dict(key='a'))

    def test_SqlValue(self):
        self.assertTrue(SqlValue)

        self.assertFalse(SqlValue(''))
        self.assertTrue(SqlValue(None))
        self.assertTrue(SqlValue(0))
        self.assertTrue(SqlValue(False))

        self.assertTrue(SqlValue('').is_equal(SqlValue('')))
        self.assertTrue(SqlValue(None).is_equal(SqlValue(None)))
        # 这两个居然相等
        self.assertTrue(SqlValue(0).is_equal(SqlValue(0.0)))
        self.assertFalse(SqlValue('').is_equal(SqlValue('a')))
        self.assertFalse(SqlValue('') == SqlValue('a'))

        self.assertEqual(SqlValue('a').to_dict(), dict(value='a'))
        self.assertEqual(SqlValue(None).to_dict(), dict(value=None))

        self.assertEqual(SqlValue('').to_sql(), '""')
        self.assertEqual(SqlValue(None).to_sql(), 'NULL')
        self.assertEqual(SqlValue(False).to_sql(), 'False')
        self.assertEqual(SqlValue(0).to_sql(), '0')
        self.assertEqual(SqlValue(0.0).to_sql(), '0.0')
        self.assertEqual(SqlValue(SqlObject()).to_sql(), '')

    def test_SQLORDER(self):
        self.assertTrue(SQLORDER)

        self.assertTrue(SQLORDER.DESC)
        self.assertTrue(SQLORDER.ASC)
        self.assertTrue(SQLORDER.DESC.is_true())
        self.assertTrue(SQLORDER.ASC.is_true())

        self.assertEqual(SQLORDER.ASC, SQLORDER.ASC)
        self.assertEqual(SQLORDER.DESC, SQLORDER.DESC)
        self.assertNotEqual(SQLORDER.ASC, SQLORDER.DESC)
        self.assertTrue(SQLORDER.ASC.is_equal(SQLORDER.ASC))
        self.assertFalse(SQLORDER.ASC.is_equal(SQLORDER.DESC))

        self.assertEqual(SQLORDER.ASC.to_dict(), dict(order='asc'))
        self.assertEqual(SQLORDER.DESC.to_dict(), dict(order='desc'))

        self.assertEqual(SQLORDER.ASC.to_sql(), 'asc')
        self.assertEqual(SQLORDER.DESC.to_sql(), 'desc')

        self.assertEqual(SQLORDER.from_str('\t\t\t AsC\n\t'), SQLORDER.ASC)
        self.assertEqual(SQLORDER.from_str(' dEsC\n\t'), SQLORDER.DESC)
        self.assertRaises(ValueError, SQLORDER.from_str, '')

        self.assertEqual(SQLORDER.from_object(SQLORDER.DESC), SQLORDER.DESC)
        self.assertEqual(SQLORDER.from_object('desc'), SQLORDER.DESC)
        self.assertEqual(SQLORDER.from_object(None), SQLORDER.ASC)
        self.assertEqual(SQLORDER.from_object(0), SQLORDER.ASC)
        self.assertEqual(SQLORDER.from_object(False), SQLORDER.ASC)
        self.assertEqual(SQLORDER.from_object(0.0), SQLORDER.ASC)

    def test_SqlOrderCase(self):
        self.assertTrue(SqlOrderCase)
        self.assertTrue(isinstance(SqlOrderCase('a'), SqlObject))
        self.assertRaises(ValueError, SqlOrderCase, '')

        self.assertEqual(SqlOrderCase('id').__key__, SqlKey('id'))
        self.assertEqual(SqlOrderCase('id').__order__, SQLORDER.ASC)

        ordercase = SqlOrderCase('id', SQLORDER.ASC)
        self.assertTrue(ordercase)
        ordercase.__key__.__key__ = ''
        self.assertFalse(ordercase)

        self.assertEqual(SqlOrderCase('id'), SqlOrderCase('id', SQLORDER.ASC))
        self.assertNotEqual(SqlOrderCase('id'), SqlOrderCase('id', SQLORDER.DESC))
        self.assertNotEqual(SqlOrderCase('id'), SqlOrderCase('aid', SQLORDER.ASC))

        self.assertEqual(SqlOrderCase('id').to_dict(), dict(key=SqlKey('id'), order=SQLORDER.ASC))
        self.assertEqual(SqlOrderCase('id', SQLORDER.DESC).to_dict(), dict(key=SqlKey('id'), order=SQLORDER.DESC))

        self.assertEqual(SqlOrderCase('id').to_sql(), '`id` asc')
        self.assertEqual(SqlOrderCase('id', SQLORDER.DESC).to_sql(), '`id` desc')

        self.assertEqual(SqlOrderCase('id'), SqlOrderCase.from_str_key('id'))

        self.assertEqual(SqlOrderCase('id'), SqlOrderCase.from_dict(key='id', order='asc'))
        self.assertEqual(SqlOrderCase('id'), SqlOrderCase.from_dict(key='id', value='asc'))
        self.assertEqual(SqlOrderCase('id'), SqlOrderCase.from_dict(id='asc'))

        self.assertRaises(TypeError, SqlOrderCase.from_object, None)
        self.assertRaises(TypeError, SqlOrderCase.from_object, 0)
        self.assertRaises(ValueError, SqlOrderCase.from_object, '')
        self.assertEqual(SqlOrderCase('id'), SqlOrderCase.from_object(dict(id='asc')))
        self.assertEqual(SqlOrderCase('id'), SqlOrderCase.from_object(dict(key='id', order='asc', value='desc')))
        self.assertEqual(SqlOrderCase('id', SQLORDER.DESC), SqlOrderCase.from_object(dict(key='id', value='desc')))
        self.assertEqual(SqlOrderCase('id', SQLORDER.DESC), SqlOrderCase.from_object(SqlOrderCase('id', SQLORDER.DESC)))

        self.assertEqual([SqlOrderCase('id'), SqlOrderCase('name', SQLORDER.DESC)],
                         SqlOrderCase.format_list('id', dict(name='desc')))

        self.assertEqual(SqlOrderAsc('id'), SqlOrderCase('id'))
        self.assertEqual(SqlOrderDesc('id'), SqlOrderCase('id', SQLORDER.DESC))

    def test_SqlOrder(self):
        self.assertTrue(SqlOrder)
        self.assertTrue(isinstance(SqlOrder(), list))
        self.assertTrue(isinstance(SqlOrder(), SqlObject))

        self.assertFalse(SqlOrder())
        self.assertTrue(SqlOrder('a'))

        self.assertTrue(SqlOrder() == SqlOrder())
        self.assertTrue(SqlOrder() == [])
        self.assertTrue(SqlOrder().is_equal([]))
        self.assertTrue(SqlOrder('a') == SqlOrder('a'))
        self.assertTrue(SqlOrder('a').is_equal(SqlOrder('a')))
        self.assertTrue(SqlOrder('a') == [SqlOrderCase('a')])
        self.assertTrue(SqlOrder('a').is_equal([SqlOrderCase('a')]))

        self.assertTrue(SqlOrder('a').to_dict(), dict(order=[SqlOrderCase('a')]))

        self.assertEqual(SqlOrder('a', 'b').to_sql(), '`a` asc,`b` asc')
        self.assertEqual(SqlOrder('a', 'b').asc('c').to_sql(), '`a` asc,`b` asc,`c` asc')
        self.assertEqual(SqlOrder('a', 'b').desc('c').to_sql(), '`a` asc,`b` asc,`c` desc')

    def test_SqlLimit(self):
        self.assertTrue(SqlLimit)
        self.assertRaises(ValueError, SqlLimit, -1)
        self.assertRaises(ValueError, SqlLimit, None)
        self.assertRaises(ValueError, SqlLimit, "")
        self.assertRaises(ValueError, SqlLimit, 0.0)

        self.assertEqual(SqlLimit().__skip__, 0)
        self.assertEqual(SqlLimit().__top__, 0)

        self.assertFalse(SqlLimit())
        self.assertTrue(SqlLimit(1))

        self.assertTrue(SqlLimit() == SqlLimit())
        self.assertTrue(SqlLimit().is_equal(SqlLimit()))
        self.assertFalse(SqlLimit(1) == SqlLimit())
        self.assertFalse(SqlLimit(1).is_equal(SqlLimit()))

        self.assertEqual(SqlLimit().to_dict(), dict(top=0, skip=0))
        self.assertEqual(SqlLimit(1).to_dict(), dict(top=1, skip=0))

        self.assertEqual(SqlLimit().to_sql(), '0,0')
        self.assertEqual(SqlLimit(1).to_sql(), '1,0')
        self.assertEqual(SqlLimit(1, 1).to_sql(), '1,1')

        self.assertEqual(SqlLimit().top(1), SqlLimit(1))
        self.assertEqual(SqlLimit().skip(1), SqlLimit(skip=1))

    def test_SQLWHERETYPE(self):
        self.assertTrue(SQLWHEREOPERATION)

        self.assertEqual(SQLWHEREOPERATION.EQUAL.to_sql(), '=')
        self.assertEqual(SQLWHEREOPERATION.NOT_EQUAL.to_sql(), '!=')
        self.assertEqual(SQLWHEREOPERATION.LESS.to_sql(), '<')
        self.assertEqual(SQLWHEREOPERATION.LESS_EQUAL.to_sql(), '<=')
        self.assertEqual(SQLWHEREOPERATION.GREATER.to_sql(), '>')
        self.assertEqual(SQLWHEREOPERATION.GREATER_EQUAL.to_sql(), '>=')
        self.assertEqual(SQLWHEREOPERATION.IN.to_sql(), 'in')
        self.assertEqual(SQLWHEREOPERATION.NOT_IN.to_sql(), 'not in')
        self.assertEqual(SQLWHEREOPERATION.BETWEEN.to_sql(), 'between')
        self.assertEqual(SQLWHEREOPERATION.NOT_BETWEEN.to_sql(), 'not between')
        self.assertEqual(SQLWHEREOPERATION.LIKE.to_sql(), 'like')
        self.assertEqual(SQLWHEREOPERATION.NOT_LIKE.to_sql(), 'not like')

    def test_SqlWhereObject(self):
        self.assertTrue(SqlWhereObject)

        self.assertFalse(SqlWhereObject())
        self.assertFalse(SqlWhereObject().is_true())

        self.assertEqual(SqlWhereObject().__len__(), 0)
        self.assertEqual(SqlWhereObject().length(), 0)

        self.assertEqual(SqlWhereObject(), SqlWhereObject())
        self.assertEqual(SqlWhereObject(), SqlWhereNull())
        self.assertNotEqual(SqlWhereObject(), SqlObject())
        self.assertNotEqual(SqlWhereObject(), '')

        self.assertEqual(SqlWhereObject().to_dict(), dict())

        self.assertEqual(SqlWhereObject().to_sql(), '')

    def test_SqlWhereStr(self):
        self.assertTrue(SqlWhereStr)
        self.assertRaises(ValueError, SqlWhereStr, '')

        wherestr = SqlWhereStr('a')
        self.assertTrue(wherestr)
        self.assertTrue(wherestr.is_true())
        wherestr.__where_str__ = ''
        self.assertFalse(wherestr)
        self.assertFalse(wherestr.is_true())

        self.assertEqual(SqlWhereStr('a').length(), 1)
        self.assertEqual(SqlWhereStr('a=1').__len__(), 1)

        self.assertEqual(SqlWhereStr('a'), SqlWhereStr('a'))
        self.assertTrue(SqlWhereStr('a').is_equal(SqlWhereStr('a')))
        self.assertNotEqual(SqlWhereStr('a'), SqlWhereStr('b'))
        self.assertFalse(SqlWhereStr('a').is_equal(SqlWhereStr('b')))

        self.assertEqual(SqlWhereStr('a').to_dict(), dict(sql='a'))

        self.assertEqual(SqlWhereStr('a').to_sql(), 'a')

    def test_where_operation(self):
        self.assertTrue(SqlWhereOperation)

        case = SqlWhereOperation('a', value=1)
        self.assertTrue(case.length() == 1)
        self.assertTrue(case.__len__() == case.length())
        self.assertTrue(case)
        self.assertTrue(case.is_true() == bool(case))
        case.key = 'b'
        case.key.__key__ = ''
        self.assertTrue(case.length() == 0)
        self.assertTrue(case.__len__() == case.length())
        self.assertFalse(case)
        self.assertTrue(case.is_true() == bool(case))

        self.assertEqual(SqlWhereOperation('a', value=1).to_dict(),
                         dict(key=SqlKey('a'), operation=SQLWHEREOPERATION.EQUAL, value=1))

        self.assertEqual(SqlWhereOperation('a', value=1).to_sql(),
                         '`a` = 1')
        self.assertEqual(SqlWhereNotIn('a', 1, None, 'a').to_sql(),
                         '`a` not in (1,NULL,"a")')
        self.assertEqual(SqlWhereNotBetween('a', 1, None).to_sql(),
                         '`a` not between 1 and NULL')
        self.assertEqual(SqlWhereNotLike('a', '%s').to_sql(),
                         '`a` not like "%s"')

    def test_where_node(self):
        self.assertTrue(SqlWhereNode)

        node = SqlWhereNode()
        self.assertEqual(node.__note__, SQLWHERENODE.AND)
        self.assertFalse(node)
        self.assertFalse(node.is_true())

        node.__left__ = SqlWhereStr('a=1')
        self.assertTrue(node)
        self.assertTrue(node.is_true())


if __name__ == '__main__':
    unittest.main()

