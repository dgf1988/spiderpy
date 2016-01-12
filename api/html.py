from lib.url import Url
from lib.hash import md5
import os


class Html(object):
    Sql_CreateTable = """
    CREATE TABLE `html` (
        `id` INT(11) NOT NULL AUTO_INCREMENT,
        `urlmd5` CHAR(50) NOT NULL,
        `htmlmd5` CHAR(50) NOT NULL,
        `code` INT(11) NOT NULL,
        `update` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        PRIMARY KEY (`id`)
    )
    COLLATE='utf8_general_ci'
    ENGINE=InnoDB
    """
    Pathroot = 'D:/HtmlStor'
    Table = 'html'
    Encoding = 'utf-8'

    def __init__(self, id=0, url='', urlmd5='', html='', htmlmd5='', code=0, update='0000-00-00 00:00:00'):
        self.id = id
        self.urlmd5 = urlmd5
        self.htmlmd5 = htmlmd5
        self.code = code
        self.lasttime = update
        self.html = html
        self.url = url

    def todict(self):
        return dict(id=self.id, url=self.url, urlmd5=self.urlmd5, htmlmd5=self.htmlmd5, code=self.code, update=self.lasttime)

    def tostr(self):
        return str(self.todict())

    def __eq__(self, other):
        if not isinstance(other, Html):
            return False
        a = self.todict()
        del a['id']
        del a['url']
        del a['update']
        b = other.todict()
        del b['id']
        del b['url']
        del b['update']
        return a == b

    def httpget(self, encoding=''):
        if not self.url:
            return None
        if not encoding:
            encoding = self.Encoding
        code, html = Url(self.url).httpget(encoding=encoding)
        self.code = code
        self.urlmd5 = md5(self.url)
        self.html = html
        self.htmlmd5 = md5(html)
        return code

    def save(self, encoding=''):
        if not self.urlmd5 or not self.html:
            return 0
        pathname = Html.pathname(self.urlmd5)
        if not os.path.exists(pathname):
            os.makedirs(pathname)
        if not encoding:
            encoding = self.Encoding
        with open(Html.fullname(self.urlmd5), 'w', encoding=encoding) as fsave:
            fsave.write(self.html)
        return 1

    def load(self, encoding=''):
        if not self.urlmd5:
            if not self.url:
                return 0
            self.urlmd5 = md5(self.url)
        fullname = Html.fullname(self.urlmd5)
        if not os.path.isfile(fullname):
            return 0
        if not encoding:
            encoding = self.Encoding
        with open(fullname, 'r', encoding=encoding) as fopen:
            self.html = fopen.read()
        return 1

    def insert(self, db: SqlDB):
        if self.id > 0:
            return 0
        gethtml = Html.get(db, urlmd5=self.urlmd5)
        if gethtml:
            self.id = gethtml.id
            if self.update(db):
                return self.id
        else:
            insertid = db.table(Html.Table).set(urlmd5=self.urlmd5, code=self.code, htmlmd5=self.htmlmd5).set()
            if insertid:
                self.id = insertid
                return insertid
        return 0

    def update(self, db: SqlDB):
        if self.id <= 0:
            return 0
        return db.table(Html.Table)\
            .where(id=self.id).set(urlmd5=self.urlmd5, code=self.code, htmlmd5=self.htmlmd5).update()

    @staticmethod
    def get(db: SqlDB, **kwargs):
        gethtml = db.table(Html.Table).where(**kwargs).select()
        if gethtml:
            return Html(**gethtml[0])

    @staticmethod
    def find(db: SqlDB, **kwargs):
        find_html = db.table(Html.Table).where(**kwargs).select()
        if find_html:
            return [Html(**each) for each in find_html]

    @staticmethod
    def list(db: SqlDB, top=0, skip=0):
        list_html = db.table(Html.Table).order(id='DESC').limit(top, skip).select()
        if list_html:
            return [Html(**each) for each in list_html]

    @staticmethod
    def from_httpget(url, encoding='utf-8'):
        if not isinstance(url, (str, Url)):
            raise ValueError
        if isinstance(url, str):
            url = Url(url)
        code, html = url.httpget(encoding=encoding)
        return Html(url=url.str(), urlmd5=md5(url.str()), html=html, htmlmd5=md5(html), code=code)

    @staticmethod
    def filename(str_md5: str):
        return '%s.txt' % str_md5[12:]

    @staticmethod
    def pathname(str_md5: str):
        return '%s/%s/%s/%s' % (Html.Pathroot, str_md5[:4], str_md5[4:8], str_md5[8:12])

    @staticmethod
    def fullname(str_md5: str):
        return '%s/%s' % (Html.pathname(str_md5), Html.filename(str_md5))


class HtmlDB(ObjectDB):
    Sql_CreateTable = """
    CREATE TABLE `html` (
        `id` INT(11) NOT NULL AUTO_INCREMENT,
        `urlmd5` CHAR(50) NOT NULL,
        `htmlmd5` CHAR(50) NOT NULL,
        `code` INT(11) NOT NULL,
        `update` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        PRIMARY KEY (`id`)
    )
    COLLATE='utf8_general_ci'
    ENGINE=InnoDB
    """
    Table = 'html'
    DataCols = ('urlmd5', 'htmlmd5', 'code')

    def __init__(self, id=0, urlmd5='', htmlmd5='', code=0, update=''):
        ObjectDB.__init__(self, id=id)
        self.__urlmd5 = urlmd5
        self.__htmlmd5 = htmlmd5
        self.__code = code
        self.__update = update
        pass

    def to_dict(self):
        return dict(id=self.id, urlmd5=self.__urlmd5, htmlmd5=self.__htmlmd5, code=self.__code, update=self.__update)

