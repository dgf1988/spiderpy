# coding: utf-8
import logging

import api.hoetom as hoetom

import lib.controller
import lib.router
import lib.server
import lib.http
from lib.headers import *


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
            self.response.buffer = '<br/>'.join([player.str_url() for player in list_player]).encode()
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
        self.response.buffer = player.str_url().encode()


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
    import urllib.parse
    import lib.headers
    import lib.http
    import lib.wsgi
    import wsgiref.simple_server

    def app(environ, start_response):
        env = lib.http.Environ(environ)
        start_response(lib.http.Status(200).to_str(), lib.headers.Headers(('Content-type', 'text/html;charset=utf-8')).to_list())
        for k, v in env.request_items():
            yield '<p><b>{key}:</b> {value}</p>\r\n'.format(key=k, value=v).encode()
        yield '<p>=========================================================================================</p>'.encode()
        for k, v in env.items():
            yield '<p><b>{key}:</b> {value}</p>\r\n'.format(key=k, value=v).encode()

    server = wsgiref.simple_server.make_server('localhost', 8080, app)
    server.serve_forever()
