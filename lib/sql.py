# coding=utf-8
from enum import Enum, unique



@unique
class ORDER(Enum):
    ASC = 0
    DESC = 1


class OrderBy(object):
    def __init__(self, key: str, order: ORDER):
        self.__key = key
        self.__mod = order

    def __str__(self):
        if self.__mod is ORDER.ASC:
            return '{key} ASC'.format(key=self.__key)
        else:
            return '{key} DESC'.format(key=self.__key)


class Order(object):
    def __init__(self, *orderby, **kwargs):
        self.__order = []
        for each in orderby:
            if isinstance(each, str):
                self.__order.append(OrderBy(each, ORDER.ASC))
            elif isinstance(each, OrderBy):
                self.__order.append(each)
            else:
                raise ValueError
        for k, v in kwargs.items():
            if isinstance(v, str):
                v = v.lower()
                if not v or v == 'asc':
                    self.__order.append(OrderBy(k, ORDER.ASC))
                elif v == 'desc':
                    self.__order.append(OrderBy(k, ORDER.DESC))
            else:
                if not v or v is ORDER.ASC:
                    self.__order.append(OrderBy(k, ORDER.ASC))
                else:
                    self.__order.append(OrderBy(k, ORDER.DESC))

    def __str__(self):
        return ','.join([str(each) for each in self.__order])

    def __bool__(self):
        return len(self.__order) > 0


class Sql(object):
    SET = 'set'
    INTO = 'into'
    AND = 'AND'
    OR = 'OR'
    FROM = 'from'

    ORDERBY = 'order by'
    LIMIT = 'limit'

    INSERT = 'insert'
    DELETE = 'delete'
    UPDATE = 'update'
    SELECT = 'select'

    WHERE = 'where'
    WHERE_EQUAL = '='
    WHERE_NOTEQUAL = '<>'
    WHERE_GREATER = '>'
    WHERE_GREATEREQUAL = '>='
    WHERE_LESS = '<'
    WHERE_LESSEQUAL = '<='
    WHERE_NOT = 'NOT'
    WHERE_IN = 'IN'
    WHERE_BETWEEN = 'BETWEEN'
    WHERE_LIKE = 'LIKE'

    def __init__(self):
        self.__table = ''
        self.__method = ''
        self.__where = None
        self.__order = None
        self.__limit = dict(length=0, skip=0)
        self.__select = []
        self.__sets = {}

    def clear(self):
        self.__table = ''
        self.__method = ''
        self.__where = None
        self.__order = None
        self.__limit = dict(length=0, skip=0)
        self.__select = []
        self.__sets = {}

    def table(self, name_table: str):
        self.__table = name_table
        return self

    def set(self, **kwargs):
        for k, v in kwargs.items():
            self.__sets[k] = v
        return self

    def where(self, *wherecase, **kwargs):
        if not self.__where:
            self.__where = Where(*wherecase, **kwargs)
        else:
            self.__where.Or(Where(*wherecase, **kwargs))
        return self

    def order(self, *orderby, **kwargs):
        self.__order = Order(*orderby, **kwargs)
        return self

    def limit(self, length: int, skip=0):
        self.__limit['length'] = length
        self.__limit['skip'] = skip
        return self

    def select(self, *select):
        if not select:
            select = ['*']
        self.__method = Sql.SELECT
        self.__select = select
        return self

    def insert(self):
        self.__method = Sql.INSERT
        return self

    def delete(self):
        self.__method = Sql.DELETE
        return self

    def update(self):
        self.__method = Sql.UPDATE
        return self

    def to_str(self):
        return str(self)

    def __str__(self):
        if self.__method is Sql.SELECT:
            sql_items = [self.__method, ','.join(self.__select), Sql.FROM, Sql.keytostr(self.__table)]
            if self.__where:
                sql_items.append(Sql.WHERE)
                sql_items.append(str(self.__where))
            if self.__order:
                sql_items.append(Sql.ORDERBY)
                sql_items.append(str(self.__order))
            sql_limit = Sql.limittostr(self.__limit)
            if sql_limit:
                sql_items += [Sql.LIMIT, sql_limit]
            return ' '.join(sql_items)
        elif self.__method is Sql.INSERT:
            sql_items = [self.__method, Sql.INTO, Sql.keytostr(self.__table),
                         Sql.SET, Sql.setstostr(self.__sets)]
            return ' '.join(sql_items)
        elif self.__method is Sql.DELETE:
            sql_items = [self.__method, Sql.FROM, Sql.keytostr(self.__table),
                         Sql.WHERE, str(self.__where)]
            return ' '.join(sql_items)
        elif self.__method is Sql.UPDATE:
            sql_items = [self.__method, Sql.keytostr(self.__table),
                         Sql.SET, Sql.setstostr(self.__sets),
                         Sql.WHERE, str(self.__where)]
            return ' '.join(sql_items)
        else:
            raise ValueError('no method')

    @staticmethod
    def setstostr(sets: dict):
        str_items = []
        for k, v in sets.items():
            str_items.append('{key}={value}'.format(key=Sql.keytostr(k), value=Sql.valuetostr(v)))
        return ','.join(str_items)

    @staticmethod
    def valuetostr(value):
        if isinstance(value, (int, bool, float)):
            return '%s' % value
        else:
            return '"%s"' % value

    @staticmethod
    def keytostr(name_key: str):
        return '`%s`' % name_key

    @staticmethod
    def limittostr(limit: dict):
        if limit['length'] and limit['skip']:
            return '%s,%s' % (limit['skip'], limit['length'])
        elif limit['length'] and not limit['skip']:
            return '%s' % limit['length']
        elif not limit['length'] and limit['skip']:
            return '%s,-1' % limit['skip']
        else:
            return ''


class SqlMethod(object):
    def __init__(self, table_name: str):
        self.sql = Sql().table(table_name)

    def __str__(self):
        return str(self.sql)

    def to_str(self):
        return str(self)


class Insert(SqlMethod):
    def __init__(self, table_name: str):
        super().__init__(table_name)
        self.sql.insert()

    def set(self, **kwargs):
        self.sql.set(**kwargs)
        return self


class Delete(SqlMethod):
    def __init__(self, table_name: str):
        super().__init__(table_name)
        self.sql.delete()

    def where(self, *wherecase, **kwargs):
        self.sql.where(*wherecase, **kwargs)
        return self


class Update(SqlMethod):
    def __init__(self, table_name: str):
        super().__init__(table_name)
        self.sql.update()

    def where(self, *wherecase, **kwargs):
        self.sql.where(*wherecase, **kwargs)
        return self

    def set(self, **kwargs):
        self.sql.set(**kwargs)
        return self


class Select(SqlMethod):
    def __init__(self, table_name: str, *list_select):
        super().__init__(table_name)
        self.sql.select(*list_select)

    def where(self, *wherecase, **kwargs):
        self.sql.where(*wherecase, **kwargs)
        return self

    def order(self, *orderby, **kwargs):
        self.sql.order(*orderby, **kwargs)
        return self

    def limit(self, length: int, skip=0):
        self.sql.limit(length, skip)
        return self


class WhereBy(object):
    def __init__(self, key):
        if not isinstance(key, str) or not key:
            raise ValueError
        self.__key = key
        pass

    @property
    def key(self):
        return self.__key

    # =
    def Equal(self, value):
        return WhereEquel(self.key, value)

    def __eq__(self, other):
        return self.Equal(other)

    # <>
    def Not_equal(self, value):
        return WhereNotEqual(self.key, value)

    def __ne__(self, other):
        return self.Not_equal(other)

    # >
    def Greater(self, value):
        return WhereGreater(self.key, value)

    def __gt__(self, other):
        return self.Greater(other)

    # >=
    def Greater_equal(self, value):
        return WhereGreaterEqual(self.key, value)

    def __ge__(self, other):
        return self.Greater_equal(other)

    # <
    def Less(self, value):
        return WhereLess(self.key, value)

    def __lt__(self, other):
        return self.Less(other)

    # <=
    def Less_equal(self, value):
        return WhereLessEqual(self.key, value)

    def __le__(self, other):
        return self.Less_equal(other)

    #
    def Between(self, beg, end):
        return WhereBetween(self.key, beg, end)

    def Not_between(self, beg, end):
        return WhereNotBetween(self.key, beg, end)

    def Like(self, like_exp):
        return WhereLike(self.key, like_exp)

    def Not_like(self, like_exp):
        return WhereNotLike(self.key, like_exp)

    def In(self, *listvalue):
        return WhereIn(self.key, *listvalue)

    def Not_in(self, *listvalue):
        return WhereNotIn(self.key, *listvalue)


class Where(object):
    def __init__(self, *wherecase, **where_keyvalue):
        self.__list = []
        self.__sign = []
        if wherecase:
            self.And(*wherecase)
        if where_keyvalue:
            self.And(*[WhereEquel(k, v) for k, v in where_keyvalue.items()])
        pass

    def And(self, *wherecase):
        len_case = len(wherecase)
        self.__list += wherecase
        self.__sign += [Sql.AND] * len_case
        return self

    def Or(self, *wherecase):
        len_case = len(wherecase)
        self.__list += wherecase
        self.__sign += [Sql.OR] * len_case
        return self

    def __bool__(self):
        return len(self.__list) > 0

    def __and__(self, other):
        return self.And(other)

    def __or__(self, other):
        return self.Or(other)

    def __str__(self):
        len_list = len(self.__list)
        list_item = []
        for i in range(len_list):
            if isinstance(self.__list[i], Where):
                list_item.append('( ' + str(self.__list[i]) + ' )')
            else:
                list_item.append(str(self.__list[i]))
            if i + 1 < len_list:
                list_item.append(str(self.__sign[i + 1]))
        return ' '.join(list_item)


class WhereCase(object):
    def __init__(self, key, sign, *listvalue):
        self.__key = key
        self.__sign = sign
        self.__listvalue = listvalue
        pass

    @property
    def key(self):
        return self.__key

    @property
    def sign(self):
        return self.__sign

    @property
    def listvalue(self):
        return self.__listvalue

    @staticmethod
    def strkey(key):
        return '`{key}`'.format(key=key)

    @staticmethod
    def strvalue(value):
        if isinstance(value, (int, bool, float)):
            return '%s' % value
        else:
            return '\"%s\"' % value

    def __str__(self):
        return '`{key}` {sign} {value}'\
            .format(key=self.key, sign=self.sign, value=self.strvalue(self.listvalue[0]))

    def __and__(self, other):
        return Where(self).And(other)

    def __or__(self, other):
        return Where(self).Or(other)


class WhereEquel(WhereCase):
    def __init__(self, key, value):
        WhereCase.__init__(self, key, Sql.WHERE_EQUAL, value)


class WhereLess(WhereCase):
    def __init__(self, key, value):
        WhereCase.__init__(self, key, Sql.WHERE_LESS, value)


class WhereGreater(WhereCase):
    def __init__(self, key, value):
        WhereCase.__init__(self, key, Sql.WHERE_GREATER, value)


class WhereLessEqual(WhereCase):
    def __init__(self, key, value):
        WhereCase.__init__(self, key, Sql.WHERE_LESSEQUAL, value)


class WhereGreaterEqual(WhereCase):
    def __init__(self, key, value):
        WhereCase.__init__(self, key, Sql.WHERE_GREATEREQUAL, value)


class WhereNotEqual(WhereCase):
    def __init__(self, key, value):
        WhereCase.__init__(self, key, Sql.WHERE_NOTEQUAL, value)


class WhereBetween(WhereCase):
    def __init__(self, key, beg, end):
        WhereCase.__init__(self, key, Sql.WHERE_BETWEEN, beg, end)

    def __str__(self):
        return '{key} {sign} {beg} {And} {end}' \
            .format(key=self.strkey(self.key),
                    sign=self.sign,
                    beg=self.strvalue(self.listvalue[0]),
                    And=Sql.AND,
                    end=self.strvalue(self.listvalue[1]))


class WhereNotBetween(WhereCase):
    def __init__(self, key, beg, end):
        WhereCase.__init__(self, key, Sql.WHERE_BETWEEN, beg, end)

    def __str__(self):
        return '{key} NOT {sign} {beg} {And} {end}' \
            .format(key=self.strkey(self.key),
                    sign=self.sign,
                    beg=self.strvalue(self.listvalue[0]),
                    And=Sql.AND,
                    end=self.strvalue(self.listvalue[1]))


class WhereIn(WhereCase):
    def __init__(self, key, *listvalue):
        WhereCase.__init__(self, key, Sql.WHERE_IN, *listvalue)

    def __str__(self):
        str_items = [self.strkey(self.key),
                     self.sign,
                     '(',
                     ','.join([self.strvalue(value) for value in self.listvalue]),
                     ')']
        return ' '.join(str_items)


class WhereNotIn(WhereCase):
    def __init__(self, key, *listvalue):
        WhereCase.__init__(self, key, Sql.WHERE_IN, *listvalue)

    def __str__(self):
        str_items = [self.strkey(self.key),
                     Sql.WHERE_NOT,
                     self.sign,
                     '(',
                     ','.join([self.strvalue(value) for value in self.listvalue]),
                     ')']
        return ' '.join(str_items)


class WhereLike(WhereCase):
    def __init__(self, key, like_exp):
        WhereCase.__init__(self, key, Sql.WHERE_LIKE, like_exp)

    def __str__(self):
        return '{key} {sign} "{like_exp}"'\
                .format(key=self.strkey(self.key), sign=self.sign, like_exp=self.listvalue[0])


class WhereNotLike(WhereCase):
    def __init__(self, key, like_exp):
        WhereCase.__init__(self, key, Sql.WHERE_LIKE, like_exp)

    def __str__(self):
        return '{key} NOT {sign} "{like_exp}"'\
                .format(key=self.strkey(self.key), sign=self.sign, like_exp=self.listvalue[0])


