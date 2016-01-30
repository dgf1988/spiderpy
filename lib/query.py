# coding: utf-8
import lib.db
import lib.mapping
import lib.sql

__all__ = ['TableSet', 'Db', 'QuerySet']


class EntitySet(object):
    __slots__ = ('db', 'entity')

    def __init__(self, db, entity):
        self.db = db
        self.entity = entity

    def save(self):
        if self.entity.has_primarykey():
            return None
        save_sql = lib.sql.From(self.entity.get_table_name()) \
            .insert(*self.entity.data_items(lambda x: x is not None))
        return self.db.insert_id() if self.db.execute(save_sql.to_sql()) else None

    def update(self, **kwargs):
        if not self.entity.has_primarykey():
            return None
        primarykey = self.entity.get_primarykey()
        [self.entity.set(k, kwargs[k]) for k in kwargs if k in self.entity.data_keys()]
        update_sql = lib.sql.From(self.entity.get_table_name()) \
            .where(lib.sql.WhereEqual(self.entity.get_table_primarykey(), primarykey)) \
            .update(*self.entity.data_items())
        return self.entity.get_primarykey() if self.db.execute(update_sql.to_sql()) else None

    def delete(self):
        if self.entity.has_primarykey():
            delete_sql = lib.sql.From(self.entity.get_table_name()) \
                .where(lib.sql.WhereEqual(self.entity.get_table_primarykey(), self.entity.get_primarykey())) \
                .delete()
            return self.db.execute(delete_sql.to_sql())

    def __bool__(self):
        return self.entity.__bool__() and self.db.__bool__()

    def __str__(self):
        return '<EntitySet: %s %s>' % (self.db, self.entity)


class TableSet(object):
    __slots__ = ('db', 'table')

    def __init__(self, db, table):
        self.db = db
        self.table = table

    def __str__(self):
        return '<TableSet: %s %s>' % (self.db, self.table)

    def __bool__(self):
        return bool(self.db) and bool(self.table)

    def create(self):
        return self.db.execute(self.table.get_table_sql())

    def new(self, **kwargs):
        return self.table(**kwargs)

    def entity(self, entity, **kwargs):
        if entity:
            return EntitySet(self.db, entity)
        if kwargs:
            return EntitySet(self.db, self.table(**kwargs))

    def save(self, entity):
        return EntitySet(self.db, entity).save()

    def update(self, entity):
        return EntitySet(self.db, entity).update()

    def delete(self, entity):
        return EntitySet(self.db, entity).delete()

    def get(self, primarykey=None, **kwargs):
        get_sql = lib.sql.From(self.table.get_table_name())
        if primarykey:
            get_sql.where(lib.sql.WhereEqual(self.table.get_table_primarykey(), primarykey))
        elif kwargs:
            [get_sql.and_where(lib.sql.WhereEqual(k, kwargs[k])) for k in kwargs]
        else:
            return None
        query = self.db.query(get_sql.select(*self.table.get_table_fields().keys()).to_sql())
        return self.table(**query[0]) if query else None

    def get_auto(self, primarykey) -> dict:
        if not primarykey:
            return None
        sql_get = lib.sql.From(self.table.get_table_name())
        sql_get.where(lib.sql.WhereEqual(self.table.get_table_primarykey(), primarykey))
        query = self.db.query(sql_get.select(*self.table.auto_keys()).to_sql())
        return query[0] if query else None

    def get_data(self, primarykey) -> dict:
        if not primarykey:
            return None
        sql_get = lib.sql.From(self.table.get_table_name())
        sql_get.where(lib.sql.WhereEqual(self.table.get_table_primarykey(), primarykey))
        query = self.db.query(sql_get.select(*self.table.data_keys()).to_sql())
        return query[0] if query else None

    def find(self, select='', **kwargs) -> list:
        find_sql = lib.sql.From(self.table.get_table_name())
        [find_sql.and_where(lib.sql.WhereEqual(k, kwargs[k])) for k in kwargs]
        if not select:
            query = self.db.query(find_sql.select(*self.table.get_table_fields().keys()).to_sql())
            return [self.table(**row) for row in query] if query else None
        else:
            return self.db.query(find_sql.select(select).to_sql())

    def list(self, select='', **kwargs) -> list:
        list_sql = lib.sql.From(self.table.get_table_name())
        wheres = kwargs.get('where', [])
        if isinstance(wheres, str):
            list_sql.where(wheres)
        if isinstance(wheres, (tuple, list)):
            for where in wheres:
                list_sql.and_where(where)
        orders = kwargs.get('order', [])
        for order in orders:
            list_sql.add_order(order)
        limit = kwargs.get('limit')
        take = kwargs.get('take', 0)
        skip = kwargs.get('skip', 0)
        if limit:
            take, skip = limit
        if not take and not skip:
            take = 10
            skip = 0
        list_sql.take(take).skip(skip)
        if not select:
            query = self.db.query(list_sql.select(*self.table.get_table_fields().keys()).to_sql())
            return [self.table(**row) for row in query] if query else None
        else:
            return self.db.query(list_sql.select(select).to_sql())

    def count(self, **kwargs) -> int:
        count_sql = lib.sql.From(self.table.get_table_name())
        [count_sql.and_where(lib.sql.WhereEqual(k, kwargs[k])) for k in kwargs]
        query = self.db.query(count_sql.select('count(*) as num').to_sql())
        return query[0]['num'] if query else None

    def __iter__(self):
        iter_keys_sql = lib.sql.From(self.table.get_table_name()) \
            .order(lib.sql.Order(self.table.get_table_primarykey(), 'asc')) \
            .select(self.table.get_table_primarykey())
        query = self.db.query(iter_keys_sql.to_sql())
        if query:
            for k in [row[self.table.get_table_primarykey()] for row in query]:
                yield self.get(k)


class API_Db_Query(object):
    def add(self, entity):
        raise NotImplementedError()

    def save(self, entity):
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


class QuerySet(object):
    def __init__(self, db, model):
        self.db = db
        self.model = model

    def add(self, entity):
        pass

    def update(self, entity):
        pass

    def get(self, primarykey=None, **kwargs):
        query = self.db.query(self.model.get_sql_query(where={self.model.get_model_primarykey(): primarykey})) \
            if primarykey else self.db.query(self.model.get_sql_query(where=kwargs)) if kwargs else None
        if query:
            return self.model(**query[0])

    def find(self, selects=(), **kwargs):
        query = self.db.query(self.model.get_sql_query(selects, where=kwargs))
        if query:
            if not selects:
                return [self.model(**row) for row in query]
            else:
                return query

    def query(self, selects=(), **kwargs):
        query = self.db.query(self.model.get_sql_query(selects, **kwargs))
        if query:
            if not selects:
                return [self.model(**row) for row in query]
            else:
                return query

    def count(self, **kwargs):
        query = self.db.query(self.model.get_sql_query(('count(*) as num',), where=kwargs))
        if query:
            return query[0]['num']


class Db(object):
    __slots__ = ('db',)

    def __init__(self, db):
        self.db = db

    def __bool__(self):
        return bool(self.db)

    def __str__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.db)

    @property
    def config(self):
        return self.db.config

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
                    _tableset_.create()
        else:
            for _table_ in tables:
                if isinstance(_table_, type) and issubclass(_table_, lib.mapping.Table):
                    self.table_set(_table_).create()
        return self.get_tables()

    def table_set(self, table):
        return TableSet(self.db, table)

    def get(self, table, primarykey):
        return TableSet(self.db, table).get(primarykey)

    def foreign_items(self, entity):
        return [(k, self.get(entity.get_table_foreigns(k), entity.get(k))) for k in entity.get_table_foreigns()]

    def __getattr__(self, table_name):
        tables = self.get_tables()
        if table_name in tables:
            return TableSet(self.db, tables[table_name])
        return super().__getattribute__(table_name)

    def __iter__(self):
        for _key_ in self.__dict__:
            if isinstance(self.__dict__.get(_key_), TableSet):
                yield self.__dict__.get(_key_)


@lib.mapping.table('html', fields='id html_url html_code html_encoding html_update',
                   primarykey='id', unique=dict(_html_url_='html_url'))
class Html(lib.mapping.Table):
    id = lib.mapping.AutoIntField()
    html_url = lib.mapping.VarcharField(size=100)
    html_code = lib.mapping.IntField()
    html_encoding = lib.mapping.CharField(size=50, nullable=True, default='utf-8')
    html_update = lib.mapping.DatetimeField(current_timestamp=True, on_update=True)


class HtmlDb(Db):
    def __init__(self):
        super().__init__(lib.db.Mysql(user='root', passwd='guofeng001', db='html_2'))
        self.html = self.table_set(Html)


if __name__ == '__main__':
    pass
