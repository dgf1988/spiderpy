# coding: utf-8

import lib.url


class PlayerInfoUrl(object):
    BaseUrl = 'http://www.hoetom.com/playerinfor_2011.jsp?id=%s'

    @classmethod
    def make(cls, playerid):
        return cls.BaseUrl % playerid

    def __init__(self, playerid):
        self.playerid = playerid
        self.urlparse = lib.url.parse(self.make(self.playerid))
        self.urlstr = self.urlparse.str_url()

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.urlstr())


class PlayerListUrl(object):
    BaseIndex = list('abcdefghijklmnopqrstuvwxyz*')
    BaseUrl = 'http://www.hoetom.com/playerlist_2011.jsp?nid=-1&pc=1&ln='

    @classmethod
    def get(cls, index=-1, ln=None):
        if ln:
            return cls.BaseUrl+ln
        elif 0 <= index <= 26:
            return cls.BaseUrl + cls.BaseIndex[index]

    @classmethod
    def list(cls, beg=0, end=None):
        if end:
            return [cls.get(ln=ln) for ln in cls.BaseIndex[beg:end]]
        else:
            return [cls.get(ln=ln) for ln in cls.BaseIndex[beg:]]

    @classmethod
    def iter(cls):
        for ln in cls.BaseIndex:
            yield cls.BaseUrl + ln


if __name__ == '__main__':
    print(PlayerListUrl.list(0, 27))