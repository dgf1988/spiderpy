# coding: utf-8

from lib.db import *
from lib.table import *
from lib.mapping import *
from lib.sql import *
from collections import OrderedDict


@table('html', fields='id html_url html_code html_encoding html_update', primarys='id', uniques=dict(url='html_url'))
class Html(Table):
    id = AutoIntField()
    html_url = VarcharField()
    html_code = IntField()
    html_encoding = CharField(default='utf-8', nullable=True)
    html_update = DatetimeField(current_timestamp=True, on_update=True)


@table('country', fields='id name', primarys='id', uniques=dict(c_name='name'))
class CountryTable(Table):
    id = AutoIntField()
    name = CharField()


class DbHoetom(Db):
    def __init__(self):
        super().__init__(Mysql('root', 'guofeng001', 'hoetom'))
        self.country = self.set(CountryTable)


if __name__ == '__main__':
    with DbHoetom() as db:
        c = CountryTable()
        print(c)
