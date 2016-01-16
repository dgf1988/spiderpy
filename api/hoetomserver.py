# coding: utf-8
import wsgiref.simple_server
import api.hoetom


def link(href, title):
    return '<a href="%s">%s</a>' % (href, title)


def app(environ, start_response):
    status = '503 '
    start_response(status, [('charset', 'utf-8')])

    body_response = ''
    with api.hoetom.DbHoetom() as db_hoetom:
        players = db_hoetom.player.list()
        body_response = ''.join([link(player['p_id'].to_url(), player['p_name'])+'<br>' for player in players])

    return [body_response.encode()]

httpd = wsgiref.simple_server.make_server(
    'localhost', 8080, app
)

if __name__ == '__main__':
    httpd.serve_forever()

