# coding: utf-8
import api.hoetom as hoetom
import lib.web as web


@web.get('/player')
def player():
    return 'player is work!'


@web.controller('player', 1000, hoetom.Db())
class Player(web.Controller):
    def __init__(self, uid, db):
        self.uid = uid
        self.db = db

    def get(self):
        return ('player get %s' % self.uid).encode()


if __name__ == '__main__':
    # web.server(port=8080).run()
    h = web.Header(('User-Agent', 'my py web F'),
                   ('Content-type', 'text/html; charset=utf-8'),
                   ('Cookie', 'PHP=lskdjflskdlf', 'PHPSESSID=el4bk1s9v2si1o4i4i6j3jn7e2'))
    print(h.to_str())

