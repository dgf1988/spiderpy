# coding: utf-8
import collections

from app.hoetom.url import *
from app.hoetom.html import *
from app.hoetom.table import *


class Player(object):
    def __init__(self, db_hoetom, id_player):
        self.db = db_hoetom
        self.id = id_player
        if not id_player or not isinstance(id_player, int):
            raise ValueError('playerid %s not accept' % id_player)
        self.url = PlayerUrl(self.id)
        self.html = PlayerHtml(self.url.url)
        self.player = PlayerTable()
        self.data = collections.OrderedDict((
            ('id', None),
            ('name', None),
            ('sex', None),
            ('nat', None),
            ('rank', None),
            ('birth', None)
        ))

    def get_html(self, timeout=30, encoding=''):
        return self.html.http_get(timeout, encoding)

    def load_html(self):
        return self.html.load()

    def get_data_from_html(self):
        if not self.html.text:
            return None
        _items_ = self.items_from_html(self.html.text)
        if _items_:
            self.data.update(_items_)
            return self.data['id'] == self.id

    def get_data_from_player(self):
        # 没有主键不要
        if not self.player.has_primarykey():
            return None
        # 外键不匹配不要
        _entity_playerid_ = self.db.playerid.get(playerid=self.id)
        if not _entity_playerid_ or _entity_playerid_.get_primarykey() != self.player['p_id']:
            return None

        self.data.update(id=_entity_playerid_['playerid'],
                         name=self.player['p_name'],
                         sex=SEX.from_obj(self.player['p_sex']).cn_str,
                         birth=self.player['p_birth'])
        # 国籍外键
        _entity_nat_ = self.db.country.get(self.player['p_nat']) if self.player['p_nat'] else None
        self.data.update(nat=_entity_nat_['name'] if _entity_nat_ else None)
        # 段位外键
        _entity_rank_ = self.db.rank.get(self.player['p_rank']) if self.player['p_rank'] else None
        self.data.update(rank=_entity_rank_['rank'] if _entity_rank_ else None)

        return self.data

    def get_player_from_data(self):
        # id不匹配不要
        if not self.id or self.data['id'] != self.id:
            return None
        if self.player.has_primarykey():
            self.player.set_primarykey(None)

        self.player.update(
                p_name=self.data['name'], p_sex=SEX.from_obj(self.data['sex']).value,
                p_birth=self.data['birth']
        )

        _entity_playerid_ = self.db.playerid.get(playerid=self.id)
        if _entity_playerid_:
            self.player.update(p_id=_entity_playerid_.get_primarykey())
        else:
            self.player.update(p_id=self.db.playerid.save(PlayeridTable(playerid=self.id)))

        _entity_nat_ = self.db.country.get(name=self.data['nat'])
        if _entity_nat_:
            self.player.update(p_nat=_entity_nat_.get_primarykey())
        else:
            self.player.update(p_nat=self.db.country.save(CountryTable(name=self.data['nat'])))

        _entity_rank_ = self.db.rank.get(rank=self.data['rank'])
        if _entity_rank_:
            self.player.update(p_rank=_entity_rank_.get_primarykey())
        else:
            self.player.update(p_rank=self.db.rank.save(RankTable(rank=self.data['rank'])))

        return self.player

    def get_player_from_db(self):

        _entity_playerid_ = self.db.playerid.get(playerid=self.id)
        if not _entity_playerid_:
            return None
        _entity_player_ = self.db.player.get(p_id=_entity_playerid_.get_primarykey())
        if not _entity_player_:
            return None
        self.player.update(**_entity_player_)
        return self.player

    def save_player_into_db(self):
        _entity_playerid_ = self.db.playerid.get(playerid=self.id)
        if _entity_playerid_:
            _entity_player_ = self.db.player.get(p_id=_entity_playerid_.get_primarykey())
            if _entity_player_:
                self.player.set_primarykey(_entity_player_.get_primarykey())
                self.db.player.update(self.player)
                self.player.update(self.db.player.get(self.player.get_primarykey()).items())
                return self.player.get_primarykey()
            else:
                _key_ = self.db.player.save(self.player)
                if _key_:
                    self.player.update(self.db.player.get(_key_).items())
                    return _key_

    def update_player_into_db(self):
        _entity_playerid_ = self.db.playerid.get(playerid=self.id)
        if _entity_playerid_:
            _entity_player_ = self.db.player.get(p_id=_entity_playerid_.get_primarykey())
            if _entity_player_:
                self.player.set_primarykey(_entity_player_.get_primarykey())
                return self.db.player.update(self.player)

    def update(self, timeout=30, encoding='', allow_httpcode=(200,)):
        if self.html.http_update(timeout, encoding, allow_httpcode):
            if self.get_data_from_html():
                if self.get_player_from_data():
                    return self.update_player_into_db()

    def get(self, timeout=30, encoding=''):
        if self.html.http_get(timeout, encoding):
            if self.html.save():
                if self.get_data_from_html():
                    if self.get_player_from_data():
                        return self.save_player_into_db()

    def load(self):
        return self.html.load() and self.get_player_from_db()

    @classmethod
    def items_from_html(cls, str_html: str):
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

        return [('id', int(hoetomid)), ('name', name), ('sex', sex), ('nat', nat), ('rank', rank),
                ('birth', datetime.datetime.strptime(birth, '%Y-%m-%d').date() if birth else None)]


class Hoetom(object):
    def __init__(self):
        pass

    def __enter__(self):
        DbHtml.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        DbHtml.close()


if __name__ == '__main__':
    DbHtml.open()
    with Db() as db:
        for pid in db.playerid:
            p = Player(db, pid['playerid'])
            p.load()
            if not p.player.has_primarykey() and not p.html.has_primarykey():
                p.get()
            print(p.html)
            print(p.player)
            foreigns = db.get_many_bykey(*p.player.foreign_items())
            for k, v in foreigns:
                print(k, '=>', v)
            print('+++++++++++++++++++++++++')
    DbHtml.close()

