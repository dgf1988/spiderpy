# coding: utf-8
import re
import os
import hashlib
import logging

import requests

import lib.url
import lib.orm


__all__ = ['Html',
           'get', 'load', 'update', 'delete']


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


class HtmlPage(object):
    Path = 'D:/HtmlStor/'
    Encoding = 'utf-8'

    def __init__(self, html_url, encoding=''):
        self.url = html_url
        self.urlmd5 = hashlib.md5(self.url.encode()).hexdigest()

        self.urlparse = lib.url.parse(html_url)
        self.urlhost = self.urlparse.host
        self.urlpath = self.urlparse.path

        self.filepath, self.filename = self.get_filename()

        self.encoding = encoding
        self.text = ''
        self.code = 0

    def __repr__(self):
        return '<HtmlPage: url=%s, encoding=%s, code=%s>' % (self.url, self.encoding, self.code)

    def http_get(self, timeout=30, encoding='', allow_code=(200,)):
        r = requests.get(self.url, timeout=timeout)
        if r.status_code in allow_code:
            r.encoding = encoding or self.encoding or r.encoding
            self.encoding = r.encoding
            self.text = r.text
            self.code = r.status_code
            return self.code

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

    def update(self, timeout=30, encoding='', allow_code=(200,)):
        return self.http_get(timeout, encoding, allow_code) and self.save() and self.code


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

    def __init__(self, html_url, **kwargs):
        self.html = HtmlTable(html_url)
        self.page = HtmlPage(html_url)

    @property
    def url(self):
        return self.html.get('html_url')

    @classmethod
    def db_reset(cls, **kwargs):
        # 重置
        if cls.Db and cls.Db.is_open():
            cls.Db.close()
        cls.Db = Db(
                kwargs.get('user') or cls.Config.get('db_user'),
                kwargs.get('passwd') or cls.Config.get('db_passwd'),
                kwargs.get('db') or kwargs.get('database') or kwargs.get('name') or cls.Config.get('db_name'),
                kwargs.get('host') or cls.Config.get('db_host'),
                kwargs.get('port') or cls.Config.get('db_port'),
                kwargs.get('charset') or cls.Config.get('db_charset')
        )
        return bool(cls.Db)

    @classmethod
    def db_restart(cls):
        # 重连
        if cls.Db.is_open():
            cls.Db.close()
        cls.Db.open()
        return cls.Db.is_open()

    @classmethod
    def db_open(cls):
        return cls.Db.open()

    @classmethod
    def db_close(cls):
        return cls.Db.close()

    def db_get(self, primarykey=None, **kwargs):






class Db(lib.orm.Db):
    def __init__(self, user, passwd, name_db, host, port, charset):
        super().__init__(lib.orm.Mysql(user, passwd, name_db, host, port, charset))
        self.html = self.set(Html)


Html.Db = Db(Html.Config.get('db_user'),
             Html.Config.get('db_passwd'),
             Html.Config.get('db_name'),
             Html.Config.get('db_host'),
             Html.Config.get('db_port'),
             Html.Config.get('db_charset'))


def get(html_url, timeout=30, encoding='', allow_httpcode=(200,)):
    _html_ = Html(html_url)
    _html_.http_get(timeout, encoding, allow_httpcode)
    return _html_


def load(html_url):
    _html_ = Html(html_url)
    _html_.load()
    return _html_


def update(html_url, timeout=30, encoding='', allow_httpcode=(200,)):
    _html_ = Html(html_url)
    _html_.http_get(timeout, encoding, allow_httpcode)
    _html_.save()
    return _html_


def delete(html_url):
    return Html(html_url).delete()


if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING)

    htmlpage = HtmlPage('http://www.dingguofeng.com')
    print(htmlpage.update())
    print(htmlpage)
    print(htmlpage.load())
    print(htmlpage)

