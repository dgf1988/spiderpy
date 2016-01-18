import wsgiref.simple_server
import tenjin
from tenjin.helpers import *
import enum
import re


HTTP_CODE = {
    100: 'CONTINUE',
    101: 'SWITCHING PROTOCOLS',
    200: 'OK',
    201: 'CREATED',
    202: 'ACCEPTED',
    203: 'NON-AUTHORITATIVE INFORMATION',
    204: 'NO CONTENT',
    205: 'RESET CONTENT',
    206: 'PARTIAL CONTENT',
    300: 'MULTIPLE CHOICES',
    301: 'MOVED PERMANENTLY',
    302: 'FOUND',
    303: 'SEE OTHER',
    304: 'NOT MODIFIED',
    305: 'USE PROXY',
    306: 'RESERVED',
    307: 'TEMPORARY REDIRECT',
    400: 'BAD REQUEST',
    401: 'UNAUTHORIZED',
    402: 'PAYMENT REQUIRED',
    403: 'FORBIDDEN',
    404: 'NOT FOUND',
    405: 'METHOD NOT ALLOWED',
    406: 'NOT ACCEPTABLE',
    407: 'PROXY AUTHENTICATION REQUIRED',
    408: 'REQUEST TIMEOUT',
    409: 'CONFLICT',
    410: 'GONE',
    411: 'LENGTH REQUIRED',
    412: 'PRECONDITION FAILED',
    413: 'REQUEST ENTITY TOO LARGE',
    414: 'REQUEST-URI TOO LONG',
    415: 'UNSUPPORTED MEDIA TYPE',
    416: 'REQUESTED RANGE NOT SATISFIABLE',
    417: 'EXPECTATION FAILED',
    500: 'INTERNAL SERVER ERROR',
    501: 'NOT IMPLEMENTED',
    502: 'BAD GATEWAY',
    503: 'SERVICE UNAVAILABLE',
    504: 'GATEWAY TIMEOUT',
    505: 'HTTP VERSION NOT SUPPORTED',
}


class HttpStatus(object):
    def __init__(self, code: int):
        self.code = code
        self.msg = HTTP_CODE[self.code]

    def to_str(self):
        return '%s %s' % (self.code, self.msg)


class Environ(object):

    def __init__(self, environ: dict):
        self.environ = environ

    @property
    def addr(self):
        return self.environ['REMOTE_ADDR']

    @property
    def server(self):
        return self.environ['SERVER_NAME']

    @property
    def method(self):
        return self.environ['REQUEST_METHOD']

    @property
    def scheme(self):
        return self.environ['wsgi.url_scheme']

    @property
    def host(self):
        return self.environ['HTTP_HOST']

    @property
    def port(self):
        return int(self.environ['SERVER_PORT'])

    @property
    def path(self):
        return self.environ['PATH_INFO']

    @path.setter
    def path(self, value: str):
        self.environ['PATH_INFO'] = value

    @property
    def query(self):
        return self.environ['QUERY_STRING']

    @property
    def protocol(self):
        return self.environ['SERVER_PROTOCOL']

    @property
    def user_agent(self):
        return self.environ['HTTP_USER_AGENT']

    def iter_items(self):
        return self.environ.items()

    def iter_line(self):
        for key, value in self.environ.items():
            yield '%s: %s\r\n' % (key, value)
        yield '\r\n'


class Header(dict):
    def __init__(self, *args):
        super().__init__()
        for arg in args:
            if isinstance(arg, tuple) and len(arg) > 1:
                self.add(arg[0], list(arg[1:]))

    def iter_items(self):
        for key, values in dict.items(self):
            if not isinstance(values, list):
                values = [values]
            for value in values:
                yield (key, value)

    def iter_line(self):
        for key, value in self.iter_items():
            yield '%s: %s\r\n' % (key, value)
        yield '\r\n'

    def to_list(self):
        return list(self.iter_items())

    def to_str(self):
        return ''.join(list(self.iter_line()))

    def add(self, key, value):
        if isinstance(value, list):
            for v in value:
                self.add(key, v)
        elif key in self:
            if isinstance(self[key], list):
                self[key].append(value)
            else:
                self[key] = [self[key], value]
        else:
            self[key] = [value]


class Request(object):
    def __init__(self, environ):
        self.environ = Environ(environ)
        if not self.environ.path:
            self.environ.path = '/'
        elif not self.environ.path.startswith('/'):
            self.environ.path = '/' + self.environ.path
        m_path = re.match(r'/(?P<controller>\w+)?(/(?P<action>\w+))?(/(?P<query>.*))?', self.environ.path)
        self.controller = m_path.group('controller')
        self.action = m_path.group('action')
        self.query = m_path.group('query')


class Response(object):
    def __init__(self, status: HttpStatus, header: Header, start_response, body: bytes, callback):
        self.status = status
        self.header = header
        self.start_response = start_response if callable(start_response) else None
        self.body = body
        self.callback = callback if callable(callback) else None
        if self.start_response is None:
            raise ValueError('Response start_response is None')

    def __iter__(self):
        self.start_response(self.status.to_str(), self.header.to_list())
        if self.body:
            yield self.body
        if self.callback:
            yield self.callback()


class WebServer(object):
    def __init__(self, host='localhost', port=80, app=None):
        self.host = host
        self.port = port
        self.app = wsgiref.simple_server.make_server(host=self.host, port=self.port, app=app)

    def run(self):
        self.app.serve_forever()


def server(host='localhost', port=80):
    return WebServer(host, port, App)


def get(route):
    def set_route(func):
        App.Controller[route] = func
        return func
    return set_route


class App(object):
    Controller = dict()

    def __init__(self, environ, start_response):
        self.environ = Environ(environ)
        self.response = start_response

    def __iter__(self):
        status = '200 OK'
        header = [('Content-type', 'text/plain; charset=utf-8')]
        self.response(status, header)
        p = Path(self.environ.path)
        if p.controller not in self.Controller:
            return [b'']
        if p.action:
            yield getattr(self.Controller[p.controller], p.action, self.Controller[p.controller].index)()
        else:
            yield getattr(self.Controller[p.controller], 'index')()


class Path(object):
    PatternPath = r'(?P<action>[^//]*)(/(?P<query>[^//]*))?'

    def __init__(self, path: str):
        self.path = path.strip().strip('/')
        paths = self.path.split('/')
        self.paths = paths
        self.controller = None
        self.action = None
        self.args = None
        len_path = len(paths)
        if len_path > 0:
            self.controller = paths[0]
        if len_path > 1:
            self.action = paths[1]
        if len_path > 2:
            self.args = paths[2:]


class Controller(object):
    __controller_name__ = ''

    def index(self):
        return ('%s index' % self.__controller_name__).encode()


def controller(name, *args, **kwargs):
    def set_controller(cls):
        cls.__controller_name__ = name
        App.Controller[name] = cls(*args, **kwargs)
        return cls
    return set_controller


class AppMain(App):
    pass


def handle_request(request):
    pass




