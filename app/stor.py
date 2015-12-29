from lib.db import DB
import hashlib
import os
from lib.hash import md5


class Html(object):
    ID = 'id'
    Urlmd5 = 'urlmd5'
    Htmlmd5 = 'htmlmd5'
    Posted = 'posted'


class Stor(DB):

    def __init__(self, user='root', passwd='guofeng001', db='html', table='html', path_root='D:/HtmlStor'):
        DB.__init__(self, user=user, passwd=passwd, db=db)
        self.__pathroot = path_root
        self.__table = table

    def save(self, url, html):
        if not url or not html:
            raise ValueError
        md5_html = md5(html)
        md5_url = md5(url)
        sql = 'select * from %s ' \
              'where %s=\"%s\"' % (self.__table, Html.Htmlmd5, md5_html)
        if self.execute(sql):
            return self.fetchone()['id']
        sql = 'insert into %s ' \
              'set %s="%s",%s=\"%s\"' % (self.__table, Html.Urlmd5, md5_url, Html.Htmlmd5, md5_html)
        str_path = self.pathname(md5_html)
        str_file = self.filename(md5_html)
        if not os.path.exists(str_path):
            os.makedirs(str_path)
        with open(str_path+'/'+str_file, 'wb') as f:
            f.write(html)
            if self.execute(sql):
                self.commit()
                return self.lastid()

    def loadhtml(self, md5_html):
        str_path = self.pathname(md5_html)
        str_file = self.filename(md5_html)
        with open(str_path+'/'+str_file, 'r') as f:
            return f.read()

    def load(self, id):
        dict_html = self.get(id)
        if dict_html:
            return self.loadhtml(dict_html.find('htmlmd5'))

    def get(self, id):
        sql = 'select * from %s where %s=%s' % (self.__table, Html.ID, id)
        if self.execute(sql):
            return self.fetchone()

    def list(self):
        sql = 'select * from %s' % self.__table
        if self.execute(sql):
            return self.fetchall()

    def pathname(self, str_md5):
        return '{pathroot}/{a}/{b}/{c}'\
            .format(pathroot=self.__pathroot, a=str_md5[:4], b=str_md5[4:8], c=str_md5[8:12])

    def filename(self, str_md5):
        return str_md5[12:]+'.{table}'.format(table=self.__table)

    def fullname(self, str_md5):
        return '{path}/{file}'.format(path=self.pathname(str_md5), file=self.filename(str_md5))

    @staticmethod
    def md5(str_html):
        m = hashlib.md5()
        m.update(str_html)
        return m.hexdigest()




