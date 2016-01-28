# coding: utf-8
import re
import os
import hashlib

import requests

import lib.url
import lib.orm


@lib.orm.table_set('html', fields='id html_url html_code html_encoding html_update',
                   primarykey='id', unique=dict(url='html_url'))
class Html(lib.orm.Table):
    id = lib.orm.AutoIntField()
    html_url = lib.orm.VarcharField()
    html_code = lib.orm.IntField()
    html_encoding = lib.orm.CharField(default='utf-8', nullable=True)
    html_update = lib.orm.DatetimeField(current_timestamp=True, on_update=True)

    def to_page(self):
        topage = Page(self['html_url'], self['html_encoding']) \
            if self['html_encoding'] else Page(self['html_url'])
        topage.code = self['html_code']
        return topage


class Db(lib.orm.DbContext):
    def __init__(self, user='root', passwd='guofeng001', database='html'):
        super().__init__(lib.orm.Mysql(user=user, passwd=passwd, db=database))
        self.html = self.table_set(Html)


class Page(object):
    StorRoot = 'd:/HtmlStor/'

    def __init__(self, str_url: str, encoding='utf-8'):
        self.encoding = encoding
        self.url = str_url
        self.urlmd5 = hashlib.md5(self.url.encode()).hexdigest()
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
        url = lib.url.UrlParse(self.url)
        urlpath = url.path
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
            return True
        else:
            return False


if __name__ == '__main__':
    d = Db().open()

    list_html = d.html.list(limit=(10, 0))
    list_page = [h.entity.to_page() for h in list_html]
    list_title = [p.get_title() for p in list_page if p.load()]
    for t in list_title:
        print(t)
    d.close()
