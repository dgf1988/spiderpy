# coding: utf-8

from lib.db import *
from lib.query import *
from lib.mapping import *
from lib.sql import *
from collections import OrderedDict


@model('html', fields='id html_url html_code html_encoding html_update', primarys='id', uniques=dict(url='html_url'))
class Html(Model):
    id = AutoIntField()
    html_url = VarcharField()
    html_code = IntField()
    html_encoding = CharField(default='utf-8', nullable=True)
    html_update = DatetimeField(current_timestamp=True, on_update=True)


@model('country', fields='id name', primarys='id', uniques=dict(c_name='name'))
class CountryTable(Model):
    id = AutoIntField()
    name = CharField()


if __name__ == '__main__':
    db = Mysql(user='root', passwd='guofeng001', db='hoetom')
    with db:
        q = QuerySet(db, CountryTable)
        print(q.count())
        for item in q.query(order='id'):
            print(item)
