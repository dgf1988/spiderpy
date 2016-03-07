# coding: utf-8
import re
import os
import hashlib
import logging

import requests

import lib.url
import lib.orm


__all__ = ['HtmlTable', 'HtmlDb', 'HtmlClient']


@lib.orm.table(
        'html', fields='id html_url html_code html_encoding html_update', primarys='id', uniques=dict(url='html_url'))
class HtmlTable(lib.orm.Table):
    DefaultPath = 'D:/HtmlStor/'
    DefaultEncoding = 'utf-8'

    id = lib.orm.AutoIntField()

    html_url = lib.orm.VarcharField()
    html_code = lib.orm.IntField()
    html_encoding = lib.orm.CharField(default='utf-8', nullable=True)

    html_update = lib.orm.DatetimeField(current_timestamp=True, on_update=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.text = ''

    def get_title(self):
        if self.text:
            s = re.search(r'<title>(?P<title>.*?)</title>', self.text, re.IGNORECASE)
            if s:
                return s.group('title')

    def get_filename(self):
        url_parse = lib.url.parse(self['html_url'])
        url_path = url_parse.path
        url_host = url_parse.host
        url_md5 = hashlib.md5(url_parse.str_url().encode()).hexdigest()
        if url_path == '/' or url_path == '':
            file_path = self.DefaultPath + url_host + '/' + url_md5[0:2]
        else:
            file_path = self.DefaultPath + url_host + '%s/' % url_path + url_md5[0:2]
        return file_path, file_path+'/'+url_md5[2:]+'.html'

    def get_page(self, timeout=30, encoding=None, allow_code=(200,)):
        r = requests.get(self['html_url'], timeout=timeout)
        if r.status_code in allow_code:
            r.encoding = encoding or self['html_encoding'] or r.encoding
            self['html_encoding'] = r.encoding
            self['html_code'] = r.status_code
            self.text = r.text
            return r.status_code

    def load_page(self):
        file_path, file_name = self.get_filename()
        if os.path.exists(file_name) and os.path.isfile(file_name):
            with open(file_name, 'r', encoding=self['html_encoding'] or self.DefaultEncoding) as f:
                self.text = f.read()
                return 1

    def save_page(self):
        file_path, file_name = self.get_filename()
        if not os.path.exists(file_path):
            os.makedirs(file_path)
        with open(file_name, 'w', encoding=self['html_encoding'] or self.DefaultEncoding) as f:
            f.write(self.text)
            return 1

    def delete_page(self):
        file_path, file_name = self.get_filename()
        # 删除文件
        if os.path.exists(file_name) and os.path.isfile(file_name):
            os.remove(file_name)
        # 删除文件夹
        try:
            os.removedirs(file_path)
        except FileNotFoundError as e:
            logging.warning(str(e))
        except IOError as e:
            logging.warning(str(e))
        # 返回文件名
        finally:
            return 1


class HtmlDb(lib.orm.Db):
    def __init__(self, user='root', password='guofeng001', db='html', host='localhost', port=3306):
        super().__init__(db=lib.orm.Mysql(user, password, db, host, port))
        self.html = self.set(HtmlTable)


class HtmlClient(object):
    def __init__(self, db_config=None):
        self.db = HtmlDb(**db_config) if db_config else HtmlDb()

    def open_db(self):
        self.db.open()
        return self

    def close_db(self):
        self.db.close()

    def __enter__(self):
        return self.open_db()

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.close_db()

    def get(self, primarykey=None, url=None, encoding=None, timeout=30, allow_code=(200,)):
        gethtml = self.db.html.get(primarykey) if primarykey else self.db.html.get(html_url=url) if url else None
        if not gethtml:
            gethtml = HtmlTable(html_url=url)
        if gethtml.get_page(encoding=encoding, timeout=timeout, allow_code=allow_code):
            return gethtml

    def load(self, primarykey=None, url=None):
        loadhtml = self.db.html.get(primarykey) if primarykey else self.db.html.get(html_url=url) if url else None
        if loadhtml:
            loadhtml.load_page()
            return loadhtml

    def save(self, html_table):
        html_table.save_page()
        return self.db.html.save(html_table)

    def delete(self, html_table):
        html_table.delete_page()
        self.db.html.remove(html_table)


if __name__ == '__main__':
    with HtmlClient() as client:
        myhtml = client.load(url='http://www.weiqi163.com/')
        print(myhtml.get_title(), myhtml)