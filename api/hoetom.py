# -*- coding: utf-8 -*-
import datetime
import re
import api.html
import lib.orm
import lib.db


class Sex(object):
    Default = 0
    Boy = 1
    Girl = 2

    def __init__(self, sex):
        self.sex = None
        if isinstance(sex, str):
            self.sex = self.from_str(sex)
        if isinstance(sex, int):
            if sex in (1, 2):
                self.sex = sex

    def to_str(self):
        return '男' if self.sex == self.Boy else '女'

    @staticmethod
    def from_str(sex: str):
        sex = sex.strip()
        if sex == '男':
            return Sex.Boy
        if sex == '女':
            return Sex.Girl
        return Sex.Default


@lib.orm.table_name('country')
@lib.orm.table_columns('id', 'name')
@lib.orm.table_uniques(name_='name')
class Country(lib.orm.Table):
    id = lib.orm.PrimaryKey()
    name = lib.orm.CharField()


@lib.orm.table_name('rank')
@lib.orm.table_columns('id', 'rank')
@lib.orm.table_uniques(rank_='rank')
class Rank(lib.orm.Table):
    id = lib.orm.PrimaryKey()
    rank = lib.orm.CharField()


@lib.orm.table_name('playerid')
@lib.orm.table_columns('id', 'playerid', 'posted')
@lib.orm.table_uniques(playerid_='playerid')
class Playerid(lib.orm.Table):
    id = lib.orm.PrimaryKey()
    playerid = lib.orm.IntField()
    posted = lib.orm.TimestampField(current_timestamp=True)

    def to_url(self):
        return 'http://www.hoetom.com/playerinfor_2011.jsp?id=%s' % self['playerid']


@lib.orm.table_name('player')
@lib.orm.table_columns('id', 'p_id', 'p_name', 'p_sex', 'p_nat', 'p_rank', 'p_birth')
@lib.orm.table_uniques(playerid='p_id')
class Player(lib.orm.Table):
    id = lib.orm.PrimaryKey()
    p_id = lib.orm.ForeignKey(table=Playerid)
    p_name = lib.orm.CharField()
    p_sex = lib.orm.IntField(default=Sex.Default, nullable=True)
    p_nat = lib.orm.ForeignKey(table=Country, nullable=True)
    p_rank = lib.orm.ForeignKey(table=Rank, nullable=True)
    p_birth = lib.orm.DateField(nullable=True)

    def to_str(self):
        return '姓名：%s，性别：%s，国籍：%s，段位：%s，生日：%s' % \
               (self['p_name'], Sex(self['p_sex']).to_str(),
                self['p_nat']['name'] if self['p_nat'] else None,
                self['p_rank']['rank'] if self['p_rank'] else None,
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

        return cls(p_id=Playerid(playerid=int(hoetomid)), p_name=name, p_sex=Sex.from_str(sex), p_nat=Country(name=nat),
                   p_rank=Rank(rank=rank),
                   p_birth=datetime.datetime.strptime(birth, '%Y-%m-%d').date() if birth else None)


@lib.orm.dbset_tables(player=Player, rank=Rank, country=Country, playerid=Playerid)
class Db(lib.orm.DbSet):
    def __init__(self):
        super().__init__(lib.db.Database(user='root', passwd='guofeng001', db='hoetom'))


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

    print('html=', dbhtml.html.count())
    print('player=', dbhoetom.player.count())

    dbhtml.close()
    dbhoetom.close()

    pass
