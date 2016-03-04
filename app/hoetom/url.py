# coding: utf-8

import lib.url


class PlayerUrl(object):
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
