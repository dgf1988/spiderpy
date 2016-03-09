# coding: utf-8
import datetime
import enum

import lib.orm


__all__ = ['SEX', 'CountryTable', 'RankTable', 'PlayerTable', 'PlayeridTable', 'SgfTable', 'HoetomDb']


class SEX(enum.IntEnum):
    Default = 0, '未知'
    Boy = 1, '男'
    Girl = 2, '女'

    def __new__(cls, value, ch_str):
        obj = int.__new__(cls, value)
        obj._value_ = value
        obj.ch_str = ch_str
        return obj

    def __str__(self):
        return '<%s: %s, %s>' % (self.__class__.__name__, self.value, self.ch_str)

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
            if v.ch_str == sex:
                index_sex = v
        return index_sex or SEX.Default


@lib.orm.table('country', fields='id name', primarys='id', uniques=dict(c_name='name'))
class CountryTable(lib.orm.Table):
    id = lib.orm.AutoIntField()
    name = lib.orm.CharField()


@lib.orm.table('rank', 'id rank', 'id', dict(r_rank='rank'))
class RankTable(lib.orm.Table):
    id = lib.orm.AutoIntField()
    rank = lib.orm.CharField()


@lib.orm.table('playerid', 'id playerid', 'id', dict(p_playerid='playerid'))
class PlayeridTable(lib.orm.Table):
    id = lib.orm.AutoIntField()
    playerid = lib.orm.IntField()

    def to_url(self):
        return 'http://www.hoetom.com/playerinfor_2011.jsp?id=%s' % self['playerid']


@lib.orm.table('player', 'id p_id p_name p_sex p_nat p_rank p_birth', 'id', dict(p_name='p_name', p_id='p_id'),
               dict(p_nat=CountryTable, p_rank=RankTable))
class PlayerTable(lib.orm.Table):
    id = lib.orm.AutoIntField()
    p_id = lib.orm.IntField()
    p_name = lib.orm.CharField()
    p_sex = lib.orm.IntField(default=SEX.Default.value, nullable=True)
    p_nat = lib.orm.IntField(nullable=True)
    p_rank = lib.orm.IntField(nullable=True)
    p_birth = lib.orm.DateField(nullable=True)


@lib.orm.table(name='sgf', fields='id s_white s_black s_name s_sgf s_time s_place s_rule s_result', primarys='id')
class SgfTable(lib.orm.Table):
    id = lib.orm.AutoIntField()
    s_white = lib.orm.CharField()
    s_black = lib.orm.CharField()
    s_name = lib.orm.CharField()
    s_sgf = lib.orm.TextField()
    s_time = lib.orm.DatetimeField(nullable=True)
    s_place = lib.orm.CharField(nullable=True)
    s_rule = lib.orm.CharField(nullable=True)
    s_result = lib.orm.CharField(nullable=True)
    s_update = lib.orm.DatetimeField(current_timestamp=True, on_update=True)


class PlayerData(object):
    def __init__(self):
        self.data = None
        self.sex = None
        self.nat = None
        self.rank = None

    def __bool__(self):
        return bool(self.data)

    def to_dict(self):
        return dict(
            id=self.data['id'],
            p_id=self.data['p_id'],
            p_name=self.data['p_name'],
            p_sex=self.sex and self.sex.ch_str,
            p_nat=self.nat and self.nat['name'],
            p_rank=self.rank and self.rank['rank'],
            p_birth=self.data['p_birth']
        )

    def to_str(self):
        return 'id: {id}, playerid: {p_id}, 姓名: {p_name}, 性别: {p_sex}, 国籍: {p_nat}, 段位: {p_rank}, 生日: {p_birth}'\
            .format(**self.to_dict())


class HoetomDb(lib.orm.Db):
    def __init__(self, user='root', passwd='guofeng001', db='hoetom', host='localhost', port=3306):
        super().__init__(lib.orm.Mysql(user, passwd, db, host, port))
        self.player = self.set(PlayerTable)
        self.rank = self.set(RankTable)
        self.country = self.set(CountryTable)
        self.playerid = self.set(PlayeridTable)
        self.sgf = self.set(SgfTable)

    def get_player(self, primarykey=None, **kwargs):
        _player_ = self.player.get(primarykey, **kwargs)
        if _player_:
            _player_get_ = PlayerData()
            _player_get_.data = _player_
            _player_get_.sex = SEX.from_obj(_player_get_.data['p_sex'])
            if _player_['p_nat']:
                _player_get_.nat = self.country.get(_player_['p_nat'])
            if _player_['p_rank']:
                _player_get_.rank = self.rank.get(_player_['p_rank'])
            return _player_get_

if __name__ == '__main__':
    with HoetomDb() as db:
        db.sgf.create()