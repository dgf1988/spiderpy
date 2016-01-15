# coding: utf-8
from lib import db
from lib import http
from lib import orm
from lib import h
import re
import os
import requests


@orm.table_name('html')
@orm.table_columns('id', 'html_url', 'html_code', 'html_encoding', 'html_update')
@orm.table_uniques(url='html_url')
class Html(orm.Table):
    id = orm.PrimaryKey()
    html_url = orm.VarcharField()
    html_code = orm.IntField()
    html_encoding = orm.CharField(default='utf-8', nullable=True)
    html_update = orm.DatetimeField(current_timestamp=True, on_update=True)

    def to_page(self):
        topage = Page(self['html_url'], self['html_encoding']) \
            if self['html_encoding'] else Page(self['html_url'])
        topage.code = self['html_code']
        return topage


@orm.dbset_tables(html=Html)
class DbHtml(orm.DbSet):
    def __init__(self, user='root', passwd='guofeng001', database='html'):
        super().__init__(db.Database(user=user, passwd=passwd, db=database))


class Page(object):
    StorRoot = 'd:/HtmlStor/'

    def __init__(self, str_url: str, encoding='utf-8'):
        self.encoding = encoding
        self.url = str_url
        self.urlmd5 = h.md5(self.url.encode())
        self.code = 0
        self.text = ''

    def get(self, timeout=30):
        response = requests.get(self.url, timeout=timeout)
        response.encoding = self.encoding
        self.code, self.text = response.status_code, response.text
        return self.code

    def get_title(self):
        search = re.search(r'<title>(?P<title>.*?)</title>', self.text, re.IGNORECASE)
        if search:
            return search.group('title')
        else:
            return None

    def to_html(self):
        return Html(html_url=self.url, html_code=self.code, html_encoding=self.encoding)

    def to_str(self):
        return 'url=%s, code=%s, encoding=%s' % (self.url, self.code, self.encoding)

    def get_filepath(self):
        url = http.Url(self.url)
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
