# -*- coding: utf-8 -*-
from lib.sqldb import *
from bs4 import BeautifulSoup
from lib.url import Url
from lib.hash import md5
from enum import unique, Enum
import os
import string
import json
import datetime
import re


class HoetomDBClient(object):
    def __init__(self, user='root', passwd='guofeng001', db='hoetom'):
        self.__db = SqlDB(user=user, passwd=passwd, db=db)
        pass

    @property
    def db(self):
        return self.__db

    def __enter__(self):
        self.db.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()


class HoetomClient(object):
    @staticmethod
    def get_html(url=None, str_url=''):
        if url and isinstance(url, Url):
            code, html = url.httpget(encoding='gbk')
            if code is 200:
                return html
        elif str_url:
            code, html = Url(str_url).httpget(encoding='gbk')
            if code is 200:
                return html
        return ''


class PlayerList(HoetomDBClient):
    DB = 'hoetom'
    Table = 'playerid'
    ID = 'id'
    PlayerID = 'playerid'
    Posted = 'posted'
    URL = 'http://www.hoetom.com/playerlist_2011.jsp'
    Pattern_Playerid = r'playerinfor_2011\.jsp\?id=(?P<id>\d+)'
    List_ln = string.ascii_lowercase + '*'

    def update(self, *url_list):
        for url in url_list:
            print(url.str())
            code, html = url.httpget()
            if code is 200:
                list_id = PlayerList.find_playerid(html)
                print(list_id)
                list_save = self.save_many(list_id)
                print(list_save)

    def save(self, playerid: int):
        test_save = self.db.table(PlayerList.Table).where(playerid=playerid).select(PlayerList.ID)
        if test_save:
            return test_save[0][PlayerList.ID]
        return self.db.table(PlayerList.Table).set(playerid=playerid).insert()

    def save_many(self, list_playerid):
        list_save = []
        for each_id in list_playerid:
            list_save.append(self.save(each_id))
        return list_save

    def top(self, top=0, skip=0):
        return [each[PlayerList.PlayerID] for each in self.db.table(PlayerList.Table).order(PlayerList.ID).limit(top, skip).select(PlayerList.PlayerID)]

    @staticmethod
    def playeranking():
        url = Url('http://www.hoetom.com/playeranking_2011.jsp')
        code, html = url.httpget()
        if code is 200:
            return PlayerList.find_playerid(html)

    def count(self):
        return self.db.table(PlayerList.Table).select('count(id) as num')[0]['num']

    @staticmethod
    def make_query(ln: str, pc=1, nid=-1):
        return locals()

    @staticmethod
    def make_url(ln: str):
        return Url(PlayerList.URL, query=PlayerList.make_query(ln))

    @staticmethod
    def list_url(*ln_list):
        if not ln_list:
            ln_list = PlayerList.List_ln
        for char in ln_list:
            yield PlayerList.make_url(char)

    @staticmethod
    def get_html(url: Url):
        return url.httpget()

    @staticmethod
    def find_playerid(html: str):
        list_find = re.findall(PlayerList.Pattern_Playerid, html, re.I)
        return set(list_find)


class Country(object):
    Table = 'country'
    ID = 'id'
    Name = 'name'

    def __init__(self, name='', id=0):
        self.id = 0
        self.name = ''
        if id:
            self.id = id
        if name:
            self.name = name

    def save(self, db: HoetomDBClient):
        test_save = db.db.table(Country.Table).where(name=self.name).select(Country.ID)
        if test_save:
            return test_save[0][Country.ID]
        return db.db.table(Country.Table).set(name=self.name).insert()

    @staticmethod
    def list(db: HoetomDBClient, length=0, skip=0):
        return db.db.table(Country.Table).limit(length, skip).select()

    @staticmethod
    def find(db: HoetomDBClient, name: str):
        find = db.db.table(Country.Table).where(name=name).select(Country.ID, Country.Name)
        if find:
            return find[0]

    @staticmethod
    def get(db: HoetomDBClient, countryid: int):
        get = db.db.table(Country.Table).where(id=countryid).select(Country.ID, Country.Name)
        if get:
            return get[0]


class Rank(object):
    Table = 'rank'
    ID = 'id'
    Rank = 'rank'

    def __init__(self, rank='', id=0):
        self.id = 0
        self.rank = ''
        if id:
            self.id = id
        if rank:
            self.rank = rank

    def save(self, db: HoetomDBClient):
        test_save = db.db.table(Rank.Table).where(rank=self.rank).select(Rank.ID)
        if test_save:
            return test_save[0][Rank.ID]
        return db.db.table(Rank.Table).set(rank=self.rank).insert()

    @staticmethod
    def list(db: HoetomDBClient, length=0, skip=0):
        return db.db.table(Rank.Table).limit(length, skip).select()

    @staticmethod
    def find(db: HoetomDBClient, rank: str):
        find = db.db.table(Rank.Table).where(rank=rank).select(Rank.ID, Rank.Rank)
        if find:
            return find[0]

    @staticmethod
    def get(db: HoetomDBClient, rankid: int):
        get = db.db.table(Rank.Table).where(id=rankid).select(Rank.ID, Rank.Rank)
        if get:
            return get[0]


class Sex(object):
    Default = 0
    Boy = 1
    Girl = 2

    @staticmethod
    def sex(sex: str):
        if sex == '男':
            return Sex.Boy
        if sex == '女':
            return Sex.Girl
        return Sex.Default


class PlayerInfo(object):
    Table = 'player'

    def __init__(self, hoetomid=0, name='', sex=Sex.Default, nat=Country(), rank=Rank(), birth='0000-00-00'):
        self.hoetomid = hoetomid
        self.p_name = name
        self.p_sex = sex
        self.p_nat = nat
        self.p_rank = rank
        if not birth:
            birth = '0000-00-00'
        self.p_birth = birth

    def save(self, db: HoetomDBClient):
        find = PlayerInfo.exist_name(db, self.p_name)
        if find:
            return find[0]['id']
        nat = self.p_nat.save(db)
        rank = self.p_rank.save(db)
        return db.db.table(PlayerInfo.Table)\
                    .set(hoetomid=self.hoetomid,
                         p_name=self.p_name,
                         p_sex=self.p_sex,
                         p_nat=nat,
                         p_rank=rank,
                         p_birth=self.p_birth)\
                    .insert()

    @staticmethod
    def exist_name(db: HoetomDBClient, name: str):
        find = db.db.table(PlayerInfo.Table).where(p_name=name).select('id')
        if find:
            return find

    @staticmethod
    def from_html(html: str):
        m_player = re.search(r'href="\?id=(?P<id>\d+)&refresh=y">(?P<name>\w+)', html, re.IGNORECASE)
        if not m_player:
            return None
        hoetomid = m_player.group('id')
        name = m_player.group('name')

        m_sex = re.search(r'性别</th>\s*?<td><b>(?P<sex>\w+)', html, re.I)
        sex = ''
        if m_sex:
            sex = m_sex.group('sex')

        m_nat = re.search(r'国籍</th>\s*?<td><b>(?P<nat>\w+)', html, re.I)
        nat = ''
        if m_nat:
            nat = m_nat.group('nat')

        m_rank = re.search(r'段位</th>\s*?<td><b>(?P<rank>\w+)', html, re.I)
        rank = ''
        if m_rank:
            rank = m_rank.group('rank')

        m_birth = re.search(r'出生日期</th>\s*?<td><b>(?P<birth>[\d\-]+)', html, re.I)
        birth = ''
        if m_birth:
            birth = m_birth.group('birth')

        return PlayerInfo(int(hoetomid), name, Sex.sex(sex), Country(nat), Rank(rank), birth)

    @staticmethod
    def from_dict(kwargs: dict):
        return PlayerInfo(**kwargs)

    def __str__(self):
        str_items = ['hoetomid: %s' % self.hoetomid,
                     'name: %s' % self.p_name,
                     'sex: %s' % self.p_sex,
                     'nat: %s' % self.p_nat.name,
                     'rank: %s' % self.p_rank.rank,
                     'birth: %s' % self.p_birth]
        return '\n'.join(str_items)

    def __eq__(self, other):
        if not isinstance(other, PlayerInfo):
            return False
        return self.p_name == other.p_name and self.p_birth == other.p_birth and self.p_nat == other.p_nat


class PlayerClient(HoetomDBClient):
    Addr = 'http://www.hoetom.com/playerinfor_2011.jsp'

    def save(self, playerinfo: PlayerInfo):
        saveid = playerinfo.save(self)
        print(saveid)
        return saveid

    def save_many(self, *playerinfo):
        list_save = []
        for p_info in playerinfo:
            if not isinstance(p_info, PlayerInfo):
                continue
            list_save.append(self.save(p_info))
        return list_save

    def save_from_playerid(self, *playerid):
        list_url = [PlayerClient.make_url(each) for each in playerid]
        for url in list_url:
            code, html = url.httpget(encoding='gbk')
            if code is 200 and html:
                self.save(PlayerClient.get_info(html))

    def count(self):
        count = self.db.table('player').select('count(id) as num')
        if count:
            return count[0]['num']

    @staticmethod
    def get_html(url: Url):
        code, html = url.httpget(encoding='gbk')
        if code is 200:
            return html

    @staticmethod
    def get_info(html: str):
        return PlayerInfo.from_html(html)

    @staticmethod
    def make_url(plaeyrid: int):
        return Url(PlayerClient.Addr, query=dict(id=plaeyrid))


class HoetomHtml(object):
    Table = 'html'

    def __init__(self, url: Url):
        self.url = url
        self.code = 0
        self.html = ''

    def httpget(self):
        code, html = self.url.httpget(encoding='gbk')
        self.html = html
        self.code = code
        return self.code

    def urlmd5(self):
        return self.url.md5()


class HoetomHtmlStor(object):
    Pathroot = 'd:/HtmlStor/Hoetom_Html'
    Table = 'html'
    ID = 'id'
    Htmlurl = 'htmlurl'
    Update = 'update'

    @staticmethod
    def save(db: HoetomDBClient, html: HoetomHtml):
        if html.code != 200:
            return 0
        urlmd5 = html.urlmd5()
        pathname = HoetomHtmlStor.pathname(urlmd5)
        if not os.path.exists(pathname):
            os.makedirs(pathname)
        with open(HoetomHtmlStor.fullname(urlmd5), 'w') as fsave:
            fsave.write(html.html)
        find = db.db.table(HoetomHtmlStor.Table).where(htmlurl=urlmd5).select('id')
        if find:
            return find[0]['id']
        insert = db.db.table(HoetomHtmlStor.Table).set(htmlurl=urlmd5).insert()
        if insert:
            return insert

    @staticmethod
    def load(db: HoetomDBClient, str_url='', md5_url='', url=None):
        if str_url:
            return HoetomHtmlStor.loadbymd5(db, md5(str_url))
        if md5_url:
            return HoetomHtmlStor.loadbymd5(db, md5_url)
        if url and isinstance(url, Url):
            return HoetomHtmlStor.loadbymd5(db, url.md5())
        pass

    @staticmethod
    def loadbymd5(db: HoetomDBClient, md5_url: str):
        fullname = HoetomHtmlStor.fullname(md5_url)
        id = db.db.table(HoetomHtmlStor.Table).where(htmlurl=md5_url).select(HoetomHtmlStor.ID)
        if os.path.isfile(fullname) and id:
            with open(fullname, 'r') as fopen:
                return id[0][HoetomHtmlStor.ID], fopen.read()
        return 0,''


    @staticmethod
    def filename(str_md5: str):
        return '%s.txt' % str_md5[12:]

    @staticmethod
    def pathname(str_md5: str):
        return '%s/%s/%s/%s' % (HoetomHtmlStor.Pathroot, str_md5[:4], str_md5[4:8], str_md5[8:12])

    @staticmethod
    def fullname(str_md5: str):
        return '%s/%s' % (HoetomHtmlStor.pathname(str_md5), HoetomHtmlStor.filename(str_md5))


class Test_Sgf(object):

    def test_sgf(self):
        sgf = json.loads('[{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":15,"y":3},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":3,"y":3},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":16,"y":15},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":14,"y":15},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":2,"y":15},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":16,"y":16},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":4,"y":16},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":15,"y":15},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":16,"y":14},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":17,"y":16},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":16,"y":10},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":9,"y":16},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":2,"y":5},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":5,"y":2},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":3,"y":9},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":2,"y":7},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":3,"y":7},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":3,"y":8},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":4,"y":8},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":2,"y":8},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":2,"y":9},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":3,"y":6},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":4,"y":7},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":2,"y":6},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":4,"y":9},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":3,"y":5},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":8,"y":15},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":9,"y":15},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":9,"y":14},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":3,"y":16},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":3,"y":15},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":8,"y":16},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":7,"y":15},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":10,"y":14},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":10,"y":13},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":9,"y":13},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":8,"y":14},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":9,"y":12},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":11,"y":14},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":10,"y":15},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":10,"y":12},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":9,"y":11},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":10,"y":11},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":9,"y":10},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":10,"y":10},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":9,"y":9},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":11,"y":8},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":9,"y":7},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":10,"y":6},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":8,"y":5},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":10,"y":4},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":16,"y":5},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":16,"y":3},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":16,"y":8},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":14,"y":5},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":14,"y":6},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":13,"y":6},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":14,"y":7},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":15,"y":5},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":13,"y":7},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":16,"y":9},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":12,"y":6},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":13,"y":5},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":13,"y":10},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":14,"y":11},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":13,"y":11},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":13,"y":12},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":14,"y":12},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":15,"y":11},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":12,"y":12},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":13,"y":13},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":12,"y":13},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":13,"y":14},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":12,"y":14},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":13,"y":15},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":12,"y":15},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":13,"y":16},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":15,"y":14},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":15,"y":13},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":16,"y":13},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":14,"y":14},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":17,"y":14},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":10,"y":7},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":16,"y":12},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":15,"y":12},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":17,"y":8},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":11,"y":17},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":10,"y":9},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":12,"y":10},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":11,"y":9},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":12,"y":9},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":12,"y":8},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":13,"y":9},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":12,"y":11},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":14,"y":9},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":14,"y":10},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":15,"y":10},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":15,"y":8},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":15,"y":9},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":11,"y":10},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":16,"y":6},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":17,"y":6},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":17,"y":5},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":16,"y":7},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":15,"y":6},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":12,"y":5},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":11,"y":3},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":12,"y":3},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":12,"y":2},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":10,"y":5},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":11,"y":5},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":9,"y":5},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":11,"y":6},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":12,"y":4},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":11,"y":4},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":13,"y":2},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":12,"y":1},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":13,"y":1},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":10,"y":2},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":14,"y":3},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":15,"y":1},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":17,"y":9},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":17,"y":10},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":18,"y":9},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":18,"y":6},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":18,"y":7},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":18,"y":5},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":18,"y":10},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":17,"y":12},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":18,"y":12},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":17,"y":13},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":18,"y":13},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":16,"y":11},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":17,"y":15},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":18,"y":11},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":17,"y":11},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":3,"y":2},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":16,"y":13},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":18,"y":11},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":17,"y":4},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":16,"y":4},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":17,"y":11},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":15,"y":17},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":16,"y":12},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":2,"y":3},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":4,"y":3},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":1,"y":4},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":8,"y":2},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":12,"y":7},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":11,"y":7},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":13,"y":4},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":2,"y":16},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":4,"y":15},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":13,"y":3},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":12,"y":7},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":15,"y":2},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":13,"y":8},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":16,"y":2},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":14,"y":1},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":16,"y":1},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":17,"y":3},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":15,"y":0},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":17,"y":1},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":17,"y":2},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":18,"y":2},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":18,"y":1},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":18,"y":0},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":17,"y":0},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":16,"y":0},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":2,"y":2},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":14,"y":2},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":1,"y":2},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":4,"y":17},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":1,"y":13},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":1,"y":14},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":2,"y":14},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":3,"y":14},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":1,"y":11},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":1,"y":10},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":4,"y":12},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":5,"y":11},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":5,"y":12},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":6,"y":12},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":6,"y":11},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":6,"y":13},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":5,"y":10},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":4,"y":11},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":1,"y":9},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":0,"y":10},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":2,"y":10},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":3,"y":10},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":3,"y":11},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":4,"y":10},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":1,"y":15},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":0,"y":14},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":2,"y":12},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":1,"y":8},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":3,"y":13},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":1,"y":16},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":5,"y":13},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":4,"y":14},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":5,"y":14},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":6,"y":14},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":5,"y":15},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":6,"y":16},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":6,"y":10},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":2,"y":11},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":5,"y":6},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":3,"y":12},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":1,"y":7},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":0,"y":9},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":3,"y":11},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":2,"y":10},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":5,"y":7},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":8,"y":1},{"LB":[],"RN":false,"black":false,"c":2,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":true,"x":7,"y":1},{"LB":[],"RN":false,"black":true,"c":1,"comment":"","fixed":false,"letterListString":"","pass":false,"resetNumber":false,"white":false,"x":9,"y":1}]')

        return sgf


class SgfPlayer(object):
    B = 1
    W = 2


class SgfStep(object):
    def __init__(self, p=0, n=0, x=0, y=0):
        self.x = 0
        self.y = 0
        self.p = 0
        self.n = 0

    def tojson(self):
        return str(self.todict())

    def todict(self):
        return dict(p=self.p, n=self.n, x=self.x, y=self.y)
