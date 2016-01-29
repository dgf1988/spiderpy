# coding: utf-8
import re
import os
import hashlib
import logging

import requests

import lib.url
import lib.orm


__all__ = ['Html', 'db',
           'get', 'load', 'update', 'delete']


PathRoot = 'd:/HtmlStor/'
DbConfig = dict(
    user='root',
    passwd='guofeng001',
    database='html'
)


@lib.orm.table('html', fields='id html_url html_code html_encoding html_update',
               primarykey='id', unique=dict(url='html_url'))
class Html(lib.orm.Table):
    id = lib.orm.AutoIntField()
    html_url = lib.orm.VarcharField()
    html_code = lib.orm.IntField()
    html_encoding = lib.orm.CharField(default='utf-8', nullable=True)
    html_update = lib.orm.DatetimeField(current_timestamp=True, on_update=True)

    def __init__(self, html_url, **kwargs):
        super().__init__(html_url=html_url, **kwargs)
        self['html_url'] = lib.url.parse(self['html_url']).str_url()
        self.urlmd5 = hashlib.md5(self['html_url'].encode()).hexdigest()
        self.text = ''

    def http_get(self, timeout=30, encoding=''):
        response = requests.get(self['html_url'], timeout=timeout)
        response.encoding = encoding or self['html_encoding'] or response.encoding or 'utf-8'
        self['html_encoding'] = response.encoding
        self['html_code'], self.text = response.status_code, response.text
        return self['html_code']

    def get_title(self):
        if self.text:
            search = re.search(r'<title>(?P<title>.*?)</title>', self.text, re.IGNORECASE)
            if search:
                return search.group('title')

    def get_filepath(self):
        url = lib.url.parse(self['html_url'])
        urlpath = url.path
        urlhost = url.host
        if urlpath == '/' or urlpath == '':
            return PathRoot + urlhost + '/' + self.urlmd5[0:2]
        else:
            return PathRoot + urlhost + '%s/' % urlpath + self.urlmd5[0:2]

    def get_filename(self):
        return self.urlmd5[2:]+'.html'

    def save(self):
        path = self.get_filepath()
        savename = path+'/'+self.get_filename()
        if not os.path.exists(path):
            os.makedirs(path)
        with open(savename, 'w', encoding=self['html_encoding']) as fsave:
            fsave.write(self.text)
            if not self.has_primarykey():
                _get_ = db.html.get(html_url=self['html_url'])
                if _get_:
                    self.set_primarykey(_get_.get_primarykey())
            _update_key_ = db.html.save(self) or self.get_primarykey()
            self.update(db.html.get(_update_key_).items())
            return self.get_primarykey()

    def load(self):
        _path_ = self.get_filepath()
        _loadname_ = _path_+'/'+self.get_filename()
        if os.path.exists(_path_) and os.path.isfile(_loadname_):
            with open(_loadname_, 'r', encoding=self['html_encoding']) as fload:
                self.text = fload.read()
                _entity_html_ = db.html.get(html_url=self['html_url'])
                if _entity_html_:
                    self.update(_entity_html_.items())
                    return True
        return False

    def http_update(self, timeout=30, encoding='', allow_httpcode=(200,)):
        _entity_ = db.html.get(html_url=self['html_url'])
        if _entity_:
            self.set_primarykey(_entity_.get_primarykey())
            self['html_encoding'] = encoding or self['html_encoding'] or _entity_['html_encoding']
            if self.http_get(timeout) in allow_httpcode:
                return self.save()

    def delete(self):
        _path_ = self.get_filepath()
        _delete_name_ = _path_+'/'+self.get_filename()
        if os.path.exists(_delete_name_) and os.path.isfile(_delete_name_):
            os.remove(_delete_name_)
        try:
            os.removedirs(_path_)
        except FileNotFoundError as _e_:
            logging.warning(_e_.__str__())
        except OSError as _e_:
            logging.warning(_e_.__str__())
        finally:
            if self.has_primarykey():
                db.html.delete(self)
            elif self['html_url']:
                _entity_ = db.html.get(html_url=self['html_url'])
                if _entity_ and _entity_.has_primarykey():
                    db.html.delete(_entity_)


class Db(lib.orm.Db):
    def __init__(self):
        super().__init__(lib.orm.Mysql(user=DbConfig['user'], passwd=DbConfig['passwd'], db=DbConfig['database']))
        self.html = self.table_set(Html)


db = Db()


def get(html_url, timeout=30, encoding=''):
    _html_ = Html(html_url=html_url)
    _html_.http_get(timeout, encoding)
    return _html_


def load(html_url):
    _html_ = Html(html_url=html_url)
    _html_.load()
    return _html_


def update(html_url, timeout=30, encoding='', allow_httpcode=(200,)):
    _html_ = Html(html_url=html_url)
    _html_.http_update(timeout, encoding, allow_httpcode)
    return _html_


def delete(html_url):
    Html(html_url=html_url).delete()


if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING)
    list_postid = (1741, 1738, 1727, 1723)
    list_posturl = ['http://www.dingguofeng.com/?p=%s' % postid for postid in list_postid]
    db.open()

    h = Html('http')
    print(h['html_url'], h.urlmd5, bool(h))
    h.text = '1'
    h['html_code'] = 1
    h['html_encoding'] = '3'
    print(bool(h), h['html_encoding'])

    db.close()
