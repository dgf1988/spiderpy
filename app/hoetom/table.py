# coding: utf-8
import datetime
import enum

import lib.orm


__all__ = ['SEX', 'CountryTable', 'RankTable', 'PlayerTable', 'PlayeridTable', 'Db']


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


@lib.orm.table('country', fields='id name', primarykey='id', unique=dict(c_name='name'))
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

    def to_str(self):
        return '姓名：%s，性别：%s，国籍：%s，段位：%s，生日：%s' % \
               (self['p_name'], SEX.from_obj(self['p_sex']).ch_str,
                self['p_nat'],
                self['p_rank'],
                self['p_birth'])


class Db(lib.orm.Db):
    def __init__(self):
        super().__init__(lib.orm.Mysql(user='root', passwd='guofeng001', db='hoetom_2'))
        self.player = self.table_set(PlayerTable)
        self.rank = self.table_set(RankTable)
        self.country = self.table_set(CountryTable)
        self.playerid = self.table_set(PlayeridTable)


if __name__ == '__main__':
    with Db() as db:
        print(db.player.count())