# coding: utf-8
from lib import web
from lib.orm import *
from lib import hash
import re
import os
import requests


@table_name('html')
@table_columns('id', 'html_url', 'html_code', 'html_encoding', 'html_update')
@table_uniques(url='html_url')
class Html(Table):
    id = PrimaryKey()
    html_url = VarcharField()
    html_code = IntField()
    html_encoding = CharField(default='utf-8', nullable=True)
    html_update = DatetimeField(current_timestamp=True, on_update=True)

    def to_page(self):
        return Page(self['html_url'], self['html_encoding']) \
            if self['html_encoding'] is not None else Page(self['html_url'])


@dbset_tables(html=Html)
class DbHtml(DbSet):
    def __init__(self, user='root', passwd='guofeng001', database='html'):
        super().__init__(db.Database(user=user, passwd=passwd, db=database))


class Page(object):
    StorRoot = 'd:/HtmlStor/'

    def __init__(self, str_url: str, encoding='utf-8'):
        self.encoding = encoding
        self.url = web.Url(str_url).str()
        self.urlmd5 = hash.md5(self.url)
        self.code = 0
        self.text = ''

    def get(self, timeout=10):
        response = requests.get(self.url, timeout=timeout)
        response.encoding = self.encoding
        self.code, self.text = response.status_code, response.text
        return self.code

    def get_title(self):
        return re.search(r'<title>(?P<title>.*?)</title>', self.text, re.IGNORECASE).group('title')

    def to_html(self):
        return Html(html_url=self.url, html_code=self.code, html_encoding=self.encoding)

    def get_filepath(self):
        url = web.Url(self.url)
        urlpath = url.strpath()
        urlhost = url.host
        if urlpath == '/' or urlpath == '':
            return self.StorRoot+urlhost+'/'+self.urlmd5[0:2]
        else:
            return self.StorRoot+urlhost+'%s/' % urlpath+self.urlmd5[0:2]

    def get_filename(self):
        return self.urlmd5[2:]+'.html'

    def save(self):
        path = self.get_filepath()
        savename = path+'/'+self.get_filename()
        if not os.path.exists(path):
            os.makedirs(path)
        with open(savename, 'w', encoding=self.encoding) as fsave:
            fsave.write(self.text)

    def load(self):
        path = self.get_filepath()
        loadname = path+'/'+self.get_filename()
        if os.path.exists(path) and os.path.isfile(loadname):
            with open(loadname, 'r', encoding=self.encoding) as fload:
                self.text = fload.read()
            return
        else:
            raise ValueError('not exists file')

