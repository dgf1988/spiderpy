# -*- coding: utf-8 -*-
from lib.orm import *
from lib import hash
from lib import web
from app import html
import requests
import re
import os


class Sex(object):
    Default = 0
    Boy = 1
    Girl = 2

    @staticmethod
    def from_str(sex: str):
        sex = sex.strip()
        if sex == '男':
            return Sex.Boy
        if sex == '女':
            return Sex.Girl
        return Sex.Default


@table_name('country')
@table_columns('id', 'name')
@table_uniques(name_='name')
class Country(Table):
    id = PrimaryKey()
    name = CharField()


@table_name('rank')
@table_columns('id', 'rank')
@table_uniques(rank_='rank')
class Rank(Table):
    id = PrimaryKey()
    rank = CharField()


@table_name('playerid')
@table_columns('id', 'playerid', 'posted')
@table_uniques(playerid_='playerid')
class Playerid(Table):
    id = PrimaryKey()
    playerid = IntField()
    posted = TimestampField(current_timestamp=True)

    def to_url(self):
        return web.Url('http://www.hoetom.com/playerinfor_2011.jsp?id=%s' % self['playerid'])


@table_name('player')
@table_columns('id', 'p_id', 'p_name', 'p_sex', 'p_nat', 'p_rank', 'p_birth')
@table_uniques(playerid='p_id', playername='p_name')
class Player(Table):
    id = PrimaryKey()
    p_id = ForeignKey(table=Playerid)
    p_name = CharField()
    p_sex = IntField(default=Sex.Default, nullable=True)
    p_nat = ForeignKey(table=Country, nullable=True)
    p_rank = ForeignKey(table=Rank, nullable=True)
    p_birth = DateField(nullable=True)

    @classmethod
    def from_html(cls, str_html: str):
        m_player = re.search(r'href="\?id=(?P<id>\d+)&refresh=y">(?P<name>\w+)', str_html, re.IGNORECASE)
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

        return cls(hoetomid=int(hoetomid), p_name=name, p_sex=Sex.from_str(sex), p_nat=Country(name=nat),
                   p_rank=Rank(rank=rank),
                   p_birth=datetime.datetime.strptime(birth, '%Y-%m-%d').date())


@dbset_tables(player=Player, rank=Rank, country=Country, playerid=Playerid)
class Hoetom(DbSet):
    def __init__(self):
        super().__init__(db.Database(user='root', passwd='guofeng001', db='hoetom'))


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
    with html.DbHtml() as dbHtml:
        print(dbHtml.html.list(100))
        for eachhtml in dbHtml.html.list(100):
            eachpage = eachhtml.to_page()
            eachpage.load()
            print(eachpage.get_title())


