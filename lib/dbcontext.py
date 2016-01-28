# coding: utf-8
import lib.db
import lib.mapping
import lib.sql


__all__ = ['EntitySet', 'TableSet', 'DbContext']


class EntitySet(object):
    __slots__ = ('db', 'entity')

    def __init__(self, db=None, entity=None):
        self.db = db
        self.entity = entity

    def save(self):
        if not self.entity.has_primarykey():
            save_sql = lib.sql.From(self.entity.get_table_name()).insert(*self.entity.get_items())
            return self.db.insert_id() if self.db.execute(save_sql.to_sql()) else None

    def update(self, **kwargs):
        if self.entity.has_primarykey():
            primarykey = self.entity.get_primarykey()
            fields = self.entity.get_table_fields()
            for k in kwargs:
                if k in fields and not fields[k].is_auto():
                    self.entity[k] = kwargs[k]
            update_sql = lib.sql.From(self.entity.get_table_name())\
                .where(lib.sql.WhereEqual(self.entity.get_table_primarykey(), primarykey))\
                .update(*self.entity.items())
            return self.db.execute(update_sql.to_sql())

    def delete(self):
        if self.entity.has_primarykey():
            delete_sql = lib.sql.From(self.entity.get_table_name())\
                .where(lib.sql.WhereEqual(self.entity.get_table_primarykey(), self.entity.getprimarykey()))\
                .delete()
            return self.db.execute(delete_sql.to_sql())

    def __bool__(self):
        return self.entity.__bool__() and self.db.__bool__()

    def __str__(self):
        return '<{table_name}: {entity_items}>'\
            .format(table_name=self.entity.get_table_name(),
                    entity_items=list((k, self.entity[k]) for k in self.entity.get_table_fields()))


class TableSet(object):
    def __init__(self, db=None, table=None):
        self.db = db
        self.table = table

    def create(self):
        return self.db.execute(self.table.get_table_sql())

    def new(self, **kwargs):
        return EntitySet(self.db, self.table(**kwargs))

    def save(self, entity):
        return EntitySet(self.db, entity).save()

    def update(self, entity):
        return EntitySet(self.db, entity).update()

    def delete(self, entity):
        return EntitySet(self.db, entity).delete()

    def get(self, primarykey):
        get_sql = lib.sql.From(self.table.get_table_name())\
            .where(lib.sql.WhereEqual(self.table.get_table_primarykey(), primarykey))
        if self.db.execute(get_sql.select(*self.table.get_table_fields().keys()).to_sql()):
            return self.new(**self.db.fetch_all()[0])

    def find(self, **kwargs):
        find_sql = lib.sql.From(self.table.get_table_name())
        for k, v in kwargs.items():
            find_sql.and_where(lib.sql.WhereEqual(k, v))
        if self.db.execute(find_sql.select(*self.table.get_table_fields().keys()).to_sql()):
            return [self.new(**row) for row in self.db.fetch_all()]

    def list(self, **kwargs):
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
        if self.db.execute(list_sql.select(*self.table.get_table_fields().keys()).to_sql()):
            return [self.new(**row) for row in self.db.fetch_all()]

    def count(self):
        count_sql = lib.sql.From(self.table.get_table_name())\
            .select('count(*) as num')
        if self.db.execute(count_sql.to_sql()):
            return self.db.fetch_all()[0]['num']

    def __iter__(self):
        iter_keys_sql = lib.sql.From(self.table.get_table_name())\
            .order(lib.sql.Order(self.table.get_table_primarykey(), 'asc'))\
            .select(self.table.get_table_primarykey())
        if self.db.execute(iter_keys_sql.to_sql()):
            keys = [row[self.table.get_table_primarykey()] for row in self.db.fetch_all()]
            for key in keys:
                yield self.get(key)


class DbContext(object):
    _tables = dict()

    def __init__(self, db=None):
        self.db = db

    def __bool__(self):
        return bool(self.db) and isinstance(self.db, lib.db.Mysql)

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

    def get_config(self):
        return getattr(self.db, '_config')

    def get_tables(self):
        return self._tables

    def get_tables_bydb(self, db_name=''):
        return self.db.get_tables(db_name)

    def create_tables(self, *tables):
        if not tables:
            for table_name in self._tables:
                self.db.execute(self._tables[table_name].get_table_sql())
        else:
            for table in tables:
                if isinstance(table, type) and issubclass(table, lib.mapping.Table):
                    self.db.execute(self.table.get_table_sql())
        return self.get_tables_bydb()

    def table_set(self, table):
        return TableSet(self.db, table)

    def __getattr__(self, table_name):
        tables = self.get_tables()
        if table_name in tables:
            return TableSet(self.db, tables[table_name])
        return super().__getattribute__(table_name)

    def __iter__(self):
        for key, table in self.get_tables().items():
            yield TableSet(self.db, table)


def db_set(**kwargs):
    def set_db(cls):
        cls._tables = {key: table for key, table in kwargs.items()
                       if isinstance(table, type) and issubclass(table, lib.mapping.Table)}
        return cls
    return set_db


@lib.mapping.table_set('html', fields='id html_url html_code html_encoding html_update',
                       primarykey='id', unique=dict(_html_url_='html_url'))
class Html(lib.mapping.Table):
    id = lib.mapping.AutoIntField()
    html_url = lib.mapping.VarcharField(size=100)
    html_code = lib.mapping.IntField()
    html_encoding = lib.mapping.CharField(size=50, nullable=True, default='utf-8')
    html_update = lib.mapping.DatetimeField(current_timestamp=True, on_update=True)


class HtmlDb(DbContext):
    def __init__(self):
        super().__init__(db=lib.db.Mysql(user='root', passwd='guofeng001', db='html_2'))
        self.html = self.table_set(Html)


if __name__ == '__main__':
    pass