# coding: utf-8
import api.hoetom as hoetom
import lib.web as web


router = web.Router()
server = web.Server(router)


@router.add('player')
class Player(web.Controller):

    @web.action(accept=[web.HTTP.GET], args=[('playerid', int)])
    def default(self, playerid):
        db = hoetom.Db().open()
        player = db.player.get(int(playerid))
        db.close()
        self.response_header.add('Content-type', 'text/html')
        return player.to_str()


if __name__ == '__main__':
    server.run()

