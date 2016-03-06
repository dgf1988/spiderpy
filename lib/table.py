# coding: utf-8
import lib.db
import lib.mapping
import lib.sql

__all__ = ['Db', 'TableSet']


class ApiTableSet(object):
    def create(self):
        raise NotImplementedError()

    def add(self, entity):
        raise NotImplementedError()

    def update(self, entity):
        raise NotImplementedError()

    def remove(self, entity):
        raise NotImplementedError()

    def get(self, primarykey=None, **kwargs):
        """

        :param primarykey:
        :param kwargs: wheres
        :return:
        """
        raise NotImplementedError()

    def find(self, selects=(), **kwargs):
        """

        :param selects:
        :param kwargs: wheres
        :return:
        """
        raise NotImplementedError()

    def query(self, selects=(), **kwargs):
        """

        :param selects:
        :param kwargs: dict(where=dict(), order='', limit=(0, 0) )
        :return:
        """
        raise NotImplementedError()

    def count(self, **kwargs):
        raise NotImplementedError()

    def __iter__(self):
        raise NotImplementedError()


class TableSet(ApiTableSet):
    def __init__(self, db, table):
        self.db = db
        self.table = table

    def __repr__(self):
        return '<TableSet: db=%s table=%s>' % (self.db.name, self.table.get_table_name())

    def create(self):
        return self.db.execute(self.table.get_sql_create())

    def new(self, iterable=(), **kwargs):
        return self.table(iterable, **kwargs)

    def add(self, entity):
        if not entity.has_primarykey():
            if self.db.execute(entity.get_sql_insert()):
                return self.get(self.db.insert_id())

    def update(self, entity):
        if entity.has_primarykey():
            self.db.execute(entity.get_sql_update())
            return self.get(entity.get_primarykey())

    def save(self, entity):
        return self.add(entity) or self.update(entity)

    def remove(self, entity):
        if entity.has_primarykey():
            return self.db.execute(entity.get_sql_delete())

    def get(self, primarykey=None, **kwargs):
        query = self.db.query(self.table.get_sql_query(where={self.table.get_table_primarykey(): primarykey})) \
            if primarykey else self.db.query(self.table.get_sql_query(where=kwargs)) if kwargs else None
        if query:
            return self.table(**query[0])

    def find(self, selects=(), **kwargs):
        query = self.db.query(self.table.get_sql_query(selects, where=kwargs))
        if query:
            if not selects:
                return [self.table(**row) for row in query]
            else:
                return query

    def query(self, selects=(), **kwargs):
        query = self.db.query(self.table.get_sql_query(selects, **kwargs))
        if query:
            if not selects:
                return [self.table(**row) for row in query]
            else:
                return query

    def count(self, **kwargs):
        query = self.db.query(self.table.get_sql_query(('count(*) as num',), where=kwargs))
        if query:
            return query[0]['num']

    def __iter__(self):
        query = self.db.query(self.table.get_sql_query(
                (self.table.get_table_primarykey(),), order=(self.table.get_table_primarykey(),)))
        if query:
            _gets_ = [item[self.table.get_table_primarykey()] for item in query if item]
            for _get_ in _gets_:
                yield self.get(_get_)


class Db(object):
    """
        数据库连接器
    """
    def __init__(self, db):
        self.db = db

    def __bool__(self):
        return bool(self.db)

    def __str__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.db)

    @property
    def config(self):
        return self.db.config

    @property
    def name(self):
        return self.db.name

    def is_open(self):
        return self.db.is_open()

    def open(self):
        self.db.open()
        return self

    def __enter__(self):
        return self.open()

    def close(self):
        self.db.close()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()

    def get_tables(self, name_db=''):
        return self.db.get_tables(name_db)

    def create_tables(self, *tables):
        if not tables:
            for _tableset_ in self.__dict__.values():
                if isinstance(_tableset_, TableSet):
                    self.db.execute(_tableset_.table.get_sql_create())
        else:
            for _table_ in tables:
                if issubclass(_table_, lib.mapping.Table):
                    self.db.execute(_table_.get_sql_create())
        return self.get_tables()

    def set(self, table):
        if issubclass(table, lib.mapping.Table):
            return TableSet(self.db, table)

    def __iter__(self):
        for _key_ in self.__dict__:
            if isinstance(self.__dict__.get(_key_), TableSet):
                yield self.__dict__.get(_key_)


@lib.mapping.table('html', fields='id html_url html_code html_encoding html_update',
                   primarys='id', uniques=dict(_html_url_='html_url'))
class Html(lib.mapping.Table):
    id = lib.mapping.AutoIntField()
    html_url = lib.mapping.VarcharField(size=100)
    html_code = lib.mapping.IntField()
    html_encoding = lib.mapping.CharField(size=50, nullable=True, default='utf-8')
    html_update = lib.mapping.DatetimeField(current_timestamp=True, on_update=True)


class HtmlDb(Db):
    def __init__(self):
        super().__init__(lib.db.Mysql(user='root', passwd='guofeng001', db='html_2'))
        self.html = TableSet(self.db, Html)


if __name__ == '__main__':
    with HtmlDb() as db:
        print(db.html.table.get_sql_create())
        print(db.html.count())
        db.html.remove(db.html.get(23))
        for h in db.html:
            print(h)