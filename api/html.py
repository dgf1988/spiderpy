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


@lib.orm.table('html', fields='id html_url html_code html_encoding html_update',
               primarykey='id', unique=dict(url='html_url'))
class Html(lib.orm.Table):
    id = lib.orm.AutoIntField()
    html_url = lib.orm.VarcharField()
    html_code = lib.orm.IntField()
    html_encoding = lib.orm.CharField(default='utf-8', nullable=True)
    html_update = lib.orm.DatetimeField(current_timestamp=True, on_update=True)

    Config = dict(
        path_root='d:/HtmlStor/',
        db_user='root',
        db_passwd='guofeng001',
        db_name='html',
        db_host='localhost',
        db_port=3306,
        db_charset='utf8'
    )
    Db = None

    def __init__(self, html_url, **kwargs):
        super().__init__(html_url=html_url, **kwargs)
        if not self.Db or not self.Db.is_open():
            raise RuntimeError('the html db is not connecting')
        self['html_url'] = lib.url.parse(self['html_url']).str_url()
        self.urlmd5 = hashlib.md5(self['html_url'].encode()).hexdigest()
        self.text = ''

    def http_get(self, timeout=30, encoding='', allow_httpcode=(200,)):
        response = requests.get(self['html_url'], timeout=timeout)
        if response.status_code in allow_httpcode:
            response.encoding = encoding or self['html_encoding'] or response.encoding
            self['html_encoding'] = response.encoding
            self['html_code'], self.text = response.status_code, response.text
            return self['html_code']

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

    def db_get(self):
        # 从数据库提取
        if self.has_primarykey():
            return self.from_entity(self.Db.html.get(self.get_primarykey()))

    def db_load(self):
        # 从数据库加载
        if self['html_url']:
            return self.from_entity(self.Db.html.get(html_url=self['html_url']))

    def db_save(self):
        # 保存到数据库
        if self['html_url'] and not self.has_primarykey():
            return self.Db.html.save(self) and self.db_load()

    def db_update(self):
        # 更新到数据库
        if self.has_primarykey():
            return self.Db.html.update(self) and self.db_get()

    def db_delete(self):
        if self.has_primarykey():
            return self.Db.html.delete(self)

    def from_entity(self, entity):
        if entity.has_primarykey():
            for k in entity:
                self[k] = entity[k]
            return entity.get_primarykey()

    def get_title(self):
        if self.text:
            search = re.search(r'<title>(?P<title>.*?)</title>', self.text, re.IGNORECASE)
            if search:
                return search.group('title')

    def get_filename(self):
        url = lib.url.parse(self['html_url'])
        urlpath = url.path
        urlhost = url.host
        if urlpath == '/' or urlpath == '':
            filepath = self.Config.get('path_root') + urlhost + '/' + self.urlmd5[0:2]
        else:
            filepath = self.Config.get('path_root') + urlhost + '%s/' % urlpath + self.urlmd5[0:2]
        return filepath, filepath+'/'+self.urlmd5[2:]+'.html'

    def file_save(self):
        if self.text:
            path, filename = self.get_filename()
            if not os.path.exists(path):
                os.makedirs(path)
            with open(filename, 'w', encoding=self['html_encoding']) as f:
                f.write(self.text)
                return True

    def file_load(self):
        if self['html_url']:
            path, filename = self.get_filename()
            if os.path.exists(filename) and os.path.isfile(filename):
                with open(filename, 'r', encoding=self['html_encoding']) as f:
                    self.text = f.read()
                    return True

    def file_delete(self):
        path, filename = self.get_filename()
        if path and filename:
            # 删除文件
            if os.path.exists(filename) and os.path.isfile(filename):
                os.remove(filename)
            # 删除文件夹
            try:
                os.removedirs(path)
            except FileNotFoundError as e:
                pass
            except IOError as e:
                pass
            # 返回文件名
            finally:
                return filename

    def save(self):
        return self.file_save() and (self.db_save() or self.db_update())

    def load(self):
        return self.file_load() and self.db_load()

    def delete(self):
        return self.file_delete() and (self.db_delete() or (self.db_load() and self.db_delete()))

    def to_bs4(self):
        pass


class Db(lib.orm.Db):
    def __init__(self, user, passwd, name_db, host, port, charset):
        super().__init__(lib.orm.Mysql(user, passwd, name_db, host, port, charset))
        self.html = self.table_set(Html)


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

    Html.Db.config.update(db='html')
    with Html.Db as db:
        for tableset in db:
            for item in tableset:
                print(item)

