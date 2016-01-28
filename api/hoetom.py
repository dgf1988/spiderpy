# -*- coding: utf-8 -*-
import datetime
import enum
import re

import api.html

import lib.orm


class SEX(enum.IntEnum):
    Default = 0, '未知'
    Boy = 1, '男'
    Girl = 2, '女'

    def __new__(cls, value, msg):
        obj = int.__new__(cls, value)
        obj._value_ = value
        obj.msg = msg
        return obj

    def __str__(self):
        return '<%s: %s, %s>' % (self.__class__.__name__, self.value, self.msg)

    @classmethod
    def from_obj(cls, obj):
        if isinstance(obj, str):
            return cls.from_str(obj)
        if isinstance(obj, int):
            return cls.from_int(obj)
        return cls.Default

    @classmethod
    def from_int(cls, index: int):
        index_sex = None
        for k, v in cls.__members__.items():
            if v.value == index:
                index_sex = v
        return index_sex or cls.Default

    @classmethod
    def from_str(cls, sex: str):
        sex = sex.strip()
        index_sex = None
        for k, v in cls.__members__.items():
            if v.msg == sex:
                index_sex = v
        return index_sex or SEX.Default


@lib.orm.table_set('country', fields='id name', primarykey='id', unique=dict(c_name='name'))
class Country(lib.orm.Table):
    id = lib.orm.AutoIntField()
    name = lib.orm.CharField()


@lib.orm.table_set('rank', 'id rank', 'id', dict(r_rank='rank'))
class Rank(lib.orm.Table):
    id = lib.orm.AutoIntField()
    rank = lib.orm.CharField()


@lib.orm.table_set('playerid', 'id playerid', 'id', dict(p_playerid='playerid'))
class Playerid(lib.orm.Table):
    id = lib.orm.AutoIntField()
    playerid = lib.orm.IntField()

    def to_url(self):
        return 'http://www.hoetom.com/playerinfor_2011.jsp?id=%s' % self['playerid']


@lib.orm.table_set('player', 'id p_id p_name p_sex p_nat p_rank p_birth', 'id', dict(p_name='p_name', p_id='p_id'),
                   dict(p_nat=Country, p_rank=Rank))
class Player(lib.orm.Table):
    id = lib.orm.AutoIntField()
    p_id = lib.orm.IntField()
    p_name = lib.orm.CharField()
    p_sex = lib.orm.IntField(default=SEX.Default, nullable=True)
    p_nat = lib.orm.IntField(nullable=True)
    p_rank = lib.orm.IntField(nullable=True)
    p_birth = lib.orm.DateField(nullable=True)

    def to_str(self):
        return '姓名：%s，性别：%s，国籍：%s，段位：%s，生日：%s' % \
               (self['p_name'], SEX.from_obj(self['p_sex']).msg,
                self['p_nat'],
                self['p_rank'],
                self['p_birth'])

    @classmethod
    def from_html(cls, str_html: str):
        m_player = re.search(r'href="\?id=(?P<id>\d+)&refresh=y">(?P<name>[^<]+)', str_html, re.IGNORECASE)
        if not m_player:
            return None
        hoetomid = m_player.group('id')
        name = m_player.group('name')

        m_sex = re.search(r'性别</th>\s*?<td><b>(?P<sex>\w+)', str_html, re.I)
        sex = ''
        if m_sex:
            sex = m_sex.group('sex')

        m_nat = re.search(r'国籍</th>\s*?<td><b>(?P<nat>\w+)', str_html, re.I)
        nat = ''
        if m_nat:
            nat = m_nat.group('nat')

        m_rank = re.search(r'段位</th>\s*?<td><b>(?P<rank>\w+)', str_html, re.I)
        rank = ''
        if m_rank:
            rank = m_rank.group('rank')

        m_birth = re.search(r'出生日期</th>\s*?<td><b>(?P<birth>[\d\-]+)', str_html, re.I)
        birth = ''
        if m_birth:
            birth = m_birth.group('birth')

        return cls(p_id=Playerid(playerid=int(hoetomid)), p_name=name, p_sex=SEX.from_str(sex), p_nat=Country(name=nat),
                   p_rank=Rank(rank=rank),
                   p_birth=datetime.datetime.strptime(birth, '%Y-%m-%d').date() if birth else None)


class Db(lib.orm.DbContext):
    def __init__(self):
        super().__init__(lib.orm.Mysql(user='root', passwd='guofeng001', db='hoetom'))
        self.player = lib.orm.TableSet(self.db, Player)
        self.rank = self.table_set(Rank)
        self.country = self.table_set(Country)
        self.playerid = self.table_set(Playerid)


class Page(api.html.Page):
    def __init__(self, url: str):
        super().__init__(url, encoding='GB18030')

    def get_playerid(self):
        return set(re.findall(r'playerinfor_2011.jsp\?id=(?P<playerid>\d+)', self.text, re.IGNORECASE))

    def get_player(self):
        return Player.from_html(self.text)


PlayerRankingUrl = 'http://www.hoetom.com/playeranking_2011.jsp'


class PlayerIndexUrlList(object):
    BaseUrl = 'http://www.hoetom.com/playerlist_2011.jsp?nid=-1&pc=1'
    BaseIndex = list('abcdefghijklmnopqrstuvwxyz*')

    def __init__(self, beg_page: int=0, end_page: int=0):
        self.beg = beg_page
        self.end = end_page

    def __iter__(self):
        if self.end > self.beg >= 0:
            for i in self.BaseIndex[self.beg:self.end+1]:
                yield self.BaseUrl+'&ln='+i
        elif self.end == 0:
            for i in self.BaseIndex[self.beg:]:
                yield self.BaseUrl+'&ln='+i
        elif self.beg == self.end == 0:
            for i in self.BaseIndex:
                yield self.BaseUrl+'&ln='+i


if __name__ == '__main__':
    dbhtml = api.html.Db().open()
    dbhoetom = Db().open()

    assert SEX.Default == 0
    assert SEX.from_obj('') == 0
    assert SEX.from_obj(333) == 0

    print(dbhoetom.country.count())
    print(dbhoetom.rank.count())
    print(dbhoetom.playerid.count())
    print(dbhoetom.player.count())

    p = dbhoetom.player.get(40)
    print(p.to_str())
    c = dbhoetom.country.get(4)
    r = dbhoetom.rank.get(9)
    p['p_nat'] = c
    p['p_rank'] = r
    print(p.to_str())

    dbhtml.close()
    dbhoetom.close()

    pass
