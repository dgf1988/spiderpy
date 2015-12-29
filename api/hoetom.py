# -*- coding: utf-8 -*-
from lib.sqldb import *
from bs4 import BeautifulSoup
from lib.url import Url
from lib.hash import md5
from enum import unique, Enum
from api.html import Html
from lib.dbsql import *
import os
import string
import json
import datetime
import re


class HoetomHtml(Html):
    DB = 'hoetom'
    Encoding = 'gbk'
    pass


class HoetomDBClient(SqlDB):
    def __init__(self, user='root', passwd='guofeng001', db='hoetom'):
        SqlDB.__init__(self, user=user, passwd=passwd, db=db)


class HoetomClient(object):
    def update_player(self):
        pass

    def update_sgf(self):
        pass


class Hoetom(object):
    Encoding = 'gbk'


class HoetomObject(object):
    DB = 'hoetom'
    Sql_CreateTable = ''
    Table = ''
    ID = 'id'

    def save(self, db: HoetomDBClient):
        pass

    @classmethod
    def get(cls, db: HoetomDBClient, **kwargs):
        get = db.table(cls.Table).where(**kwargs).select()
        if get:
            return cls(**get[0])

    @classmethod
    def find(cls, db: HoetomDBClient, **kwargs):
        pass

    @classmethod
    def list(cls, db: HoetomDBClient, top=0, skip=0):
        pass


class Country(ObjectDB):
    Sql_CreateTable = """
    CREATE TABLE `country` (
        `id` INT(11) NOT NULL AUTO_INCREMENT,
        `name` CHAR(50) NOT NULL,
        PRIMARY KEY (`id`),
        UNIQUE INDEX `name` (`name`)
    )
    COLLATE='utf8_general_ci'
    ENGINE=InnoDB
    AUTO_INCREMENT=1
    """
    Table = 'country'
    DataCols = ('name',)

    def __init__(self, id=0, name=''):
        ObjectDB.__init__(self, id)
        self.name = name

    def __bool__(self):
        return bool(self.name)

    def __str__(self):
        return self.name

    def to_dict(self):
        return dict(id=self.id, name=self.name)

class Rank(ObjectDB):
    Sql_CreateTable = """
    CREATE TABLE `rank` (
        `id` INT(11) NOT NULL AUTO_INCREMENT,
        `rank` CHAR(50) NOT NULL,
        PRIMARY KEY (`id`),
        UNIQUE INDEX `rank` (`rank`)
    )
    COLLATE='utf8_general_ci'
    ENGINE=InnoDB
    AUTO_INCREMENT=1
    """
    Table = 'rank'
    DataCols = ('rank',)

    def __init__(self, id=0, rank=''):
        ObjectDB.__init__(self, id)
        self.rank = rank

    def __bool__(self):
        return bool(self.rank)

    def __eq__(self, other):
        if not isinstance(other, Rank):
            return False
        return str(self) == str(other)

    def to_dict(self):
        return dict(id=self.id, rank=self.rank)

    def __str__(self):
        return self.rank


class Sex(object):
    Default = 0
    Boy = 1
    Girl = 2

    def __init__(self, sex=None):
        self.__sex = Sex.Default
        if isinstance(sex, int):
            self.__sex = sex
        elif isinstance(sex, str):
            self.__sex = Sex.strtoint(sex)

    def to_int(self):
        return self.__sex

    def to_str(self):
        return str(self)

    def to_dict(self):
        return dict(sex=Sex.inttostr(self.__sex))

    def __int__(self):
        return self.__sex

    def __str__(self):
        return Sex.inttostr(self.__sex)

    def __eq__(self, other):
        if not isinstance(other, Sex):
            return False
        return int(self) == int(other)

    def __bool__(self):
        return bool(self.__sex)

    @staticmethod
    def strtoint(sex: str):
        sex = sex.strip()
        if sex == '男':
            return Sex.Boy
        if sex == '女':
            return Sex.Girl
        return Sex.Default

    @staticmethod
    def inttostr(sex: int):
        if sex is Sex.Default:
            return ''
        if sex is Sex.Boy:
            return '男'
        if sex is Sex.Girl:
            return '女'


class PlayerID(ObjectDB):
    BaseUrl = 'http://www.hoetom.com/playerinfor_2011.jsp'
    Table = 'playerid'
    DataCols = ('playerid',)

    def __init__(self, id=0, playerid=0, posted='0000-00-00'):
        ObjectDB.__init__(self, id)
        self.playerid = playerid
        self.posted = posted

    def __int__(self):
        return self.playerid

    def __str__(self):
        return str(self.playerid)

    def __bool__(self):
        return bool(self.playerid)

    def __eq__(self, other):
        if not isinstance(other, PlayerID):
            return False
        return self.playerid == other.playerid

    def to_dict(self):
        return dict(id=self.id, playerid=self.playerid, posted=self.posted)

    def to_url_str(self):
        return PlayerID.BaseUrl + '?id=%s' % self.playerid

    def to_url(self):
        return Url(self.to_url_str())


class Player(ObjectDB):
    BaseUrl = 'http://www.hoetom.com/playerinfor_2011.jsp'
    SqlCreateTable = """
    CREATE TABLE `player` (
        `id` INT(11) NOT NULL AUTO_INCREMENT,
        `hoetomid` INT(11) NULL DEFAULT NULL,
        `p_name` CHAR(50) NOT NULL,
        `p_sex` INT(11) NULL DEFAULT NULL,
        `p_nat` INT(11) NULL DEFAULT NULL,
        `p_rank` INT(11) NULL DEFAULT NULL,
        `p_birth` DATE NULL DEFAULT NULL,
        PRIMARY KEY (`id`),
        UNIQUE INDEX `hoetomid` (`hoetomid`)
    )
    COLLATE='utf8_general_ci'
    ENGINE=InnoDB
    """
    Table = 'player'
    DataCols = ('hoetomid', 'p_name', 'p_sex', 'p_nat', 'p_rank', 'p_birth')

    def __init__(self, id=0, hoetomid=0, p_name='', p_sex=Sex(), p_nat=Country(), p_rank=Rank(), p_birth='0000-00-00'):
        ObjectDB.__init__(self, id)
        self.hoetomid = hoetomid
        self.p_name = p_name
        self.p_sex = p_sex
        self.p_nat = p_nat
        self.p_rank = p_rank
        if not p_birth:
            p_birth = '0000-00-00'
        self.p_birth = p_birth

    @classmethod
    def from_dbget(cls, db: HoetomDBClient, dbget: dict):
        player = dict()
        if 'id' in dbget:
            player['id'] = dbget['id']
        if 'hoetomid' in dbget:
            player['hoetomid'] = dbget['hoetomid']
        if 'p_name' in dbget:
            player['p_name'] = dbget['p_name']
        if 'p_sex' in dbget:
            player['p_sex'] = Sex(dbget['p_sex'])
        if 'p_nat' in dbget:
            player['p_nat'] = Country.get(db, id=dbget['p_nat'])
        if 'p_rank' in dbget:
            player['p_rank'] = Rank.get(db, id=dbget['p_rank'])
        if 'p_birth' in dbget:
            player['p_birth'] = dbget['p_birth']
        return Player(**player)

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

        return Player(0, int(hoetomid), name, Sex(sex), Country(name=nat), Rank(rank=rank), birth)

    @staticmethod
    def make_url(hoetomid: int):
        return Url(Player.BaseUrl, query=dict(id=hoetomid))

    def __str__(self):
        str_items = ['id: %s' % self.id,
                     'hoetomid: %s' % self.hoetomid,
                     'name: %s' % self.p_name,
                     'sex: %s' % self.p_sex.__str__(),
                     'nat: %s' % self.p_nat.__str__(),
                     'rank: %s' % self.p_rank.__str__(),
                     'birth: %s' % self.p_birth]
        return '\n'.join(str_items)

    def __bool__(self):
        return bool(self.p_name)

    def to_dict(self):
        return dict(
            id=self.id,
            hoetomid=self.hoetomid,
            p_name=self.p_name,
            p_sex=self.p_sex,
            p_nat=self.p_nat,
            p_rank=self.p_rank,
            p_birth=self.p_birth
        )

    def __eq__(self, other):
        if not isinstance(other, Player):
            return False
        a = self.to_dict()
        del a['id']
        b = other.to_dict()
        del b['id']
        return a == b




