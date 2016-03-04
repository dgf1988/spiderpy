# coding: utf-8
import re
import os
import hashlib
import logging

import requests

import lib.url
import lib.orm


__all__ = ['HtmlTable', 'HtmlDb', 'HtmlPage', 'Html']


@lib.orm.table(
        'html', fields='id html_url html_code html_encoding html_update', primarys='id', uniques=dict(url='html_url'))
class HtmlTable(lib.orm.Table):
    id = lib.orm.AutoIntField()

    html_url = lib.orm.VarcharField()
    html_code = lib.orm.IntField()
    html_encoding = lib.orm.CharField(default='utf-8', nullable=True)

    html_update = lib.orm.DatetimeField(current_timestamp=True, on_update=True)


class HtmlDb(lib.orm.Db):
    def __init__(self, user='root', password='guofeng001', db='html', host='localhost', port=3306):
        super().__init__(db=lib.orm.Mysql(user, password, db, host, port))
        self.html = self.set(HtmlTable)
        logging.info(self.html)


class HtmlPage(object):
    Path = 'D:/HtmlStor/'
    Encoding = 'utf-8'

    def __init__(self, url: lib.url.UrlParse, encoding=None):
        self.url = url
        self.urlstr = url.str_url()
        self.urlmd5 = hashlib.md5(self.urlstr.encode()).hexdigest()

        self.urlhost = self.url.host
        self.urlpath = self.url.path

        self.filepath, self.filename = self.get_filename()

        self.encoding = encoding
        self.text = ''
        self.code = 0

    def __repr__(self):
        return '<HtmlPage: url=%s, encoding=%s>' % (self.url, self.encoding)

    def get_title(self):
        if self.text:
            s = re.search(r'<title>(?P<title>.*?)</title>', self.text, re.IGNORECASE)
            if s:
                return s.group('title')

    def get_filename(self):
        if self.urlpath == '/' or self.urlpath == '':
            filepath = self.Path + self.urlhost + '/' + self.urlmd5[0:2]
        else:
            filepath = self.Path + self.urlhost + '%s/' % self.urlpath + self.urlmd5[0:2]
        return filepath, filepath+'/'+self.urlmd5[2:]+'.html'

    def get(self, timeout=30, encoding=None, allow_code=(200,)):
        r = requests.get(self.urlstr, timeout=timeout)
        if r.status_code in allow_code:
            r.encoding = encoding or self.encoding or r.encoding
            self.encoding = r.encoding
            self.text = r.text
            self.code = r.status_code
            return r.status_code

    def save(self):
        if self.text:
            if not os.path.exists(self.filepath):
                os.makedirs(self.filepath)
            with open(self.filename, 'w', encoding=self.encoding or self.Encoding) as f:
                f.write(self.text)
            return 1

    def load(self):
        if self.url:
            if os.path.exists(self.filename) and os.path.isfile(self.filename):
                with open(self.filename, 'r', encoding=self.encoding or self.Encoding) as f:
                    self.text = f.read()
                return 1

    def delete(self):
        # 删除文件
        if os.path.exists(self.filename) and os.path.isfile(self.filename):
            os.remove(self.filename)
        # 删除文件夹
        try:
            os.removedirs(self.filepath)
        except FileNotFoundError as e:
            logging.warning(str(e))
        except IOError as e:
            logging.warning(str(e))
        # 返回文件名
        finally:
            return self.filename

    def update(self, timeout=30, encoding=None, allow_code=(200,)):
        return self.get(timeout, encoding, allow_code) and self.save() and self.code

    def to_html(self):
        return HtmlTable(html_url=self.urlstr, html_encoding=self.encoding, html_code=self.code)


class Html(object):

    Config = dict(
        path_root='D:/HtmlStor/',
        db_user='root',
        db_passwd='guofeng001',
        db_name='html',
        db_host='localhost',
        db_port=3306,
        db_charset='utf8'
    )

    Db = None

    def __init__(self):
        self.data = None
        self.page = None

    @property
    def url(self):
        return self.data.get('html_url')

    @classmethod
    def db_set(cls, **kwargs):
        # 重置
        if cls.Db and cls.Db.is_open():
            cls.Db.close()
        cls.Db = HtmlDb(
                kwargs.get('user') or cls.Config.get('db_user'),
                kwargs.get('passwd') or cls.Config.get('db_passwd'),
                kwargs.get('db') or kwargs.get('database') or kwargs.get('name') or cls.Config.get('db_name'),
                kwargs.get('host') or cls.Config.get('db_host'),
                kwargs.get('port') or cls.Config.get('db_port')
        )
        return bool(cls.Db)

    @classmethod
    def db_open(cls):
        if not cls.Db:
            cls.db_set()
        cls.Db.open()

    @classmethod
    def db_is_open(cls):
        return cls.Db.is_open()

    @classmethod
    def db_close(cls):
        cls.Db.close()

    def db_get(self, primarykey=None, **kwargs):
        html_get = self.Db.html.get(primarykey, **kwargs)
        if html_get:
            self.data = html_get
            return self.data.get_primarykey()

    def db_add(self):
        if not self.data:
            return None
        html_add = self.Db.html.add(self.data)
        if html_add:
            self.data = html_add
            return self.data.get_primarykey()

    def db_remove(self):
        self.Db.html.remove(self.data)
        self.data = None

    def db_update(self):
        html_update = self.Db.html.update(self.data)
        if html_update:
            self.data = html_update
            return self.data.get_primarykey()

    def page_get(self, timeout=30, allow_code=(200,)):
        if self.data and self.data['html_url']:
            self.page = HtmlPage(lib.url.parse(self.data['html_url']), self.data['html_encoding'])
            if self.page.get(timeout, allow_code=allow_code):
                self.data['html_encoding'] = self.page.encoding
                self.data['html_code'] = self.page.code
                return self.page.code

    def page_load(self):
        if self.data and self.data['html_url']:
            self.page = HtmlPage(lib.url.parse(self.data['html_url']), self.data['html_encoding'])
            return self.page.load()

    def page_save(self):
        return self.page and self.page.save()

    def page_update(self, timeout=30, allow_code=(200,)):
        return self.page_get(timeout, allow_code) and self.page_save()

    def page_delete(self):
        self.page.delete()
        self.page = None

    def get(self, url, timeout=30, encoding=None, allow_code=(200,)):
        self.data = HtmlTable(html_url=url, html_encoding=encoding)
        return self.page_get(timeout, allow_code)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    Html.db_open()
    html = Html()
    assert html.data is None
    assert html.page is None

    html.db_get(html_url='http://www.weiqi163.com')

    for h in Html.Db.html:
        print(h)

    Html.db_close()
