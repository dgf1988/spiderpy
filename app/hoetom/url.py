# coding: utf-8

import lib.url


class PlayerUrl(object):
    _base_url_ = 'http://www.hoetom.com/playerinfor_2011.jsp?id=%s'

    @classmethod
    def make(cls, playerid):
        return cls._base_url_ % playerid

    def __init__(self, playerid):
        self.playerid = playerid
        self.url = lib.url.parse(self.make(self.playerid)).str_url()

    def __str__(self):
        return '<PlayerUrl: %s>' % self.url
