# coding: utf-8
import re
import os
import hashlib
import logging

import requests

import lib.url
import lib.orm


__all__ = ['HtmlTable', 'HtmlDb', 'HtmlPage']


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
    DefaultPath = 'D:/HtmlStor/'
    PatternTitle = r'<title>(?P<title>.*?)</title>'

    def __init__(self, url, encoding=None):
        self.url = url
        self.encoding = encoding
        self.code = 0
        self.text = ''

    def __repr__(self):
        return '<{}: code={}, encoding={}, title={}, url={}, length={}>'.format(
            self.__class__.__name__, self.code, self.encoding, self.get_title(), self.url,
            len(self.text) if self.text else 0
        )

    def get(self, timeout=30):
        if not self.url:
            return None
        r = requests.get(self.url, timeout=timeout)
        r.encoding = self.encoding or r.encoding
        self.code, self.encoding, self.text = r.status_code, r.encoding, r.text
        return self.code

    def save(self):
        filepath, filename = self.get_filename(self.url)
        if not os.path.exists(filepath):
            os.makedirs(filepath)
        with open(filename, 'w', encoding=self.encoding) as f:
            f.write(self.text)
            return 1

    def update(self, timeout=30):
        return self.get(timeout) and self.save() and self.code

    def load(self):
        filepath, filename = self.get_filename(self.url)
        if not os.path.exists(filename) or not os.path.isfile(filename):
            return None
        with open(filename, 'r', encoding=self.encoding) as f:
            self.text = f.read()
            return 1

    def delete(self):
        filepath, filename = self.get_filename(self.url)
        if os.path.exists(filename) and os.path.isfile(filename):
            os.remove(filename)
        try:
            os.removedirs(filepath)
        except FileNotFoundError as e:
            logging.warning(str(e))
        except IOError as e:
            logging.warning(str(e))
        finally:
            return 1

    def get_title(self):
        if not self.text:
            return None
        m_title = re.search(self.PatternTitle, self.text, re.IGNORECASE | re.MULTILINE)
        if m_title:
            return m_title.group('title')

    @classmethod
    def get_filename(cls, url):
        url_parse = lib.url.parse(url)
        url_path = url_parse.path
        url_host = url_parse.host
        url_md5 = hashlib.md5(url_parse.str_url().encode()).hexdigest()
        if url_path == '/' or url_path == '':
            file_path = cls.DefaultPath + url_host + '/' + url_md5[0:2]
        else:
            file_path = cls.DefaultPath + url_host + '%s/' % url_path + url_md5[0:2]
        return file_path, file_path+'/'+url_md5[2:]+'.html'


if __name__ == '__main__':
    page = HtmlPage('http://game.onegreen.net/weiqi/HTML/165283.html', 'gb18030')
    print(page)
    page.get()
    print(page)