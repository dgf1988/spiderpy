# coding: utf-8
import logging

import api.hoetom as hoetom

import lib.controller
import lib.router
import lib.server
import lib.http


logging.basicConfig(level=logging.INFO)


router = lib.router.Router(host='localhost')
server = lib.server.Server(router)


@router.default
class Player(lib.controller.Controller):

    @lib.controller.action([lib.http.METHOD.GET], int)
    def default(self, playerid: int):
        list_player = []
        player = dict()
        db = hoetom.Db().open()
        if not playerid:
            list_player = db.player.list(100)
        else:
            player = db.player.get(playerid)
        db.close()
        self.response.header.set('Content-type', 'text/html')
        if list_player:
            self.response.buffer = '<br/>'.join([player.to_str() for player in list_player]).encode()
        elif player:
            self.response.buffer = player.to_str().encode()

    @lib.controller.action([lib.http.METHOD.GET], str)
    def name(self, player_name: str):
        logging.info('player name = "%s"' % player_name)
        if not player_name:
            return lib.http.NotFountResponse()
        db = hoetom.Db().open()
        player = db.player.get(p_name=player_name)
        db.close()

        if not player:
            return lib.http.NotFountResponse()
        self.response.header.set('Content-type', 'text/html')
        self.response.buffer = player.to_str().encode()


@router.add('country')
class Country(lib.controller.Controller):
    @lib.controller.action([lib.http.METHOD.GET], int)
    def list(self, natid=None):
        list_country = []
        country = dict()
        db = hoetom.Db().open()
        if natid:
            country = db.country.get(natid)
        else:
            list_country = db.country.list(100)
        db.close()

        self.response.header.content_type = 'text/html; charset=utf-8'
        if list_country:
            self.response.buffer = \
                '<br/>'.join(['%s %s' % (country['id'], country['name']) for country in list_country]).encode()
        elif country:
            print(country)
            self.response.buffer = ('%s %s' % (country['id'], country['name'])).encode()


if __name__ == '__main__':
    import wsgiref.simple_server
    import wsgiref.util
    import wsgiref.headers

    header = wsgiref.headers.Headers([('User-agent', 'web.py/2.0'), ('User-agent', 'web.py/3.0')])
    header.add_header('content-type', 'text/html', charset='utf-8')
    print(header)
