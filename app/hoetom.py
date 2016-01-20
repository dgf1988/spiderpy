# coding: utf-8
import api.hoetom as hoetom
import lib.web as web
import logging
import wsgiref.headers


logging.basicConfig(level=logging.INFO)


router = web.Router(host='localhost')
server = web.Server(router)


@router.default
class Player(web.Controller):

    @web.action([web.METHOD.GET], int)
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

    @web.action([web.METHOD.GET], str)
    def name(self, player_name: str):
        logging.info('player name = "%s"' % player_name)
        if not player_name:
            return web.NotFountResponse()
        db = hoetom.Db().open()
        player = db.player.get(p_name=player_name)
        db.close()

        if not player:
            return web.NotFountResponse()
        self.response.header.set('Content-type', 'text/html')
        self.response.buffer = player.to_str().encode()


@router.controller('country')
class Country(web.Controller):
    @web.action([web.METHOD.GET], int)
    def default(self, natid=None):
        list_country = []
        country = dict()
        db = hoetom.Db().open()
        if natid:
            country = db.country.get(natid)
        else:
            list_country = db.country.list(100)
        db.close()

        self.response.header.set('content-type', 'text/html')
        if list_country:
            self.response.buffer = '<br/>'.join(['%s %s' % (country['id'], country['name']) for country in list_country]).encode()
        elif country:
            self.response.buffer = ('%s %s' % (country['id'], country['name'])).encode()


if __name__ == '__main__':
    server.listen(5000)
