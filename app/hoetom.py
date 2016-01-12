# -*- coding: utf-8 -*-
from lib.url import Url
from lib.hash import md5
from lib.orm import *
import os
import string
import re


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
@table_uniques('name')
class Country(Table):
    id = PrimaryKey()
    name = CharField()


@table_name('rank')
@table_columns('id', 'rank')
@table_uniques('rank')
class Rank(Table):
    id = PrimaryKey()
    rank = CharField()


@table_name('player')
@table_columns('id', 'hoetomid', 'p_name', 'p_sex', 'p_nat', 'p_rank', 'p_birth')
@table_uniques('hoetomid')
class Player(Table):
    id = PrimaryKey()
    hoetomid = IntField()
    p_name = CharField()
    p_sex = IntField()
    p_nat = ForeignKey(table=Country)
    p_rank = ForeignKey(table=Rank)
    p_birth = DateField()

    @classmethod
    def from_html(cls, html):
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

        return cls(hoetomid=int(hoetomid), p_name=name, p_sex=Sex.from_str(sex), p_nat=Country(name=nat),
                   p_rank=Rank(rank=rank),
                   p_birth=datetime.datetime.strptime(birth, '%Y-%m-%d').date())


@table_name('playerid')
@table_columns('id', 'playerid', 'posted')
@table_uniques('playerid')
class Playerid(Table):
    id = PrimaryKey()
    playerid = IntField()
    posted = TimestampField(current_timestamp=True)

    def to_url(self):
        return 'http://www.hoetom.com/playerinfor_2011.jsp?id=%s' % self['playerid']


@dbset_tables(player=Player, rank=Rank, country=Country, playerid=Playerid)
class Hoetom(DbSet):
    def __init__(self):
        super().__init__(db.Database(user='root', passwd='guofeng001', db='hoetom'))


if __name__ == '__main__':
    with Hoetom() as hoetom:
        playerid = hoetom.playerid.get(300)
        print(Rank.get_table_uniques())
        print(Country.get_table_uniques())
        print(Playerid.get_table_uniques())
        print(Player.get_table_uniques())