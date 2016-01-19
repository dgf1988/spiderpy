import wsgiref.simple_server
import tenjin
import urllib.parse
import collections
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


class Status(object):
    """
        HTTP 状态
    """

    def __init__(self, status_code: int):
        if status_code not in HTTP_CODE:
            raise ValueError('%s is not in HTTP_CODE' % status_code)
        self.code = status_code
        self.msg = HTTP_CODE[self.code]

    def to_str(self):
        return '%s %s' % (self.code, self.msg)


class HTTP(enum.Enum):
    GET = 1
    POST = 2

    def to_str(self):
        return 'GET' if self == self.GET else 'POST' if self == self.POST else 'Unknow'

    @classmethod
    def from_str(cls, str_method: str):
        str_method = str_method.strip().upper()
        if str_method == 'GET':
            return cls.GET
        elif str_method == 'POST':
            return cls.POST
        return cls.GET


class Environ(object):
    """
        HTTP请求环境
    """

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

    def get_url(self):
        get_url = self.environ['wsgi.url_scheme']+'://'

        if self.environ.get('HTTP_HOST'):
            get_url += self.environ['HTTP_HOST']
        else:
            get_url += self.environ['SERVER_NAME']

            if self.environ['wsgi.url_scheme'] == 'https':
                if self.environ['SERVER_PORT'] != '443':
                   get_url += ':' + self.environ['SERVER_PORT']
            else:
                if self.environ['SERVER_PORT'] != '80':
                   get_url += ':' + self.environ['SERVER_PORT']

        get_url += urllib.parse.quote(self.environ.get('SCRIPT_NAME', ''))
        get_url += urllib.parse.quote(self.environ.get('PATH_INFO', ''))
        if self.environ.get('QUERY_STRING'):
            get_url += '?' + self.environ['QUERY_STRING']
        return get_url

    def iter_items(self):
        return self.environ.items()

    def iter_line(self):
        for key, value in self.environ.items():
            yield '%s: %s\r\n' % (key, value)
        yield '\r\n'


class Header(dict):
    """
        HTTP 头
    """

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
    """
        HTTP 请求
    """

    def __init__(self, environ, start_response):
        self.environ = Environ(environ)
        self.start_response = start_response if callable(start_response) else None
        if not self.start_response:
            raise ValueError('starta_response is not callable or is None')
        self.url = self.environ.get_url()
        self.method = HTTP.from_str(self.environ.method)

    def get_header(self):
        return Header()


class Route(object):
    """
        线路
    """
    def __init__(self, key_name: str, call_action):
        if not callable(call_action):
            raise ValueError('call action "%s" is not callable' % call_action.__name__)
        if not isinstance(call_action, type) or not issubclass(call_action, Controller):
            raise ValueError('call action "%s" is not controller type' % call_action.__name__)
        self.action = call_action

        key_name = key_name or self.action.__name__
        if not key_name:
            raise ValueError('route key name is empty')
        self.name = key_name

    def is_controller(self):
        return isinstance(self.action, type) and issubclass(self.action, Controller)

    def is_callable(self):
        return callable(self.action)

    def __call__(self, *args, **kwargs):
        return self.action(*args, **kwargs)


class Router(collections.OrderedDict):
    """
        路由器
    """
    def __init__(self, *routes):
        super().__init__()
        self.default_route = None
        for route in routes:
            if isinstance(route, Route):
                self[route.name] = route

    @property
    def default(self):
        return self.default_route

    @default.setter
    def default(self, route: Route):
        self.default_route = route

    def iter_items(self):
        for route in self.values():
            yield route
        yield self.default

    def add(self, name: str=None):
        def add_route(call_action):
            route = Route(name or call_action.__name__, call_action)
            self[route.name] = route
            return call_action
        return add_route

    def get_routing(self, request: Request):
        return Routing(request, self)

    def __call__(self, request: Request):
        return self.get_routing(request)


class Routing(object):
    """
        映射
    """
    def __init__(self, request: Request, router: Router):
        self.request = request
        
        url = self.request.environ.get_url()
        self.url = urllib.parse.urlparse(url)
        
        split_path = [each for each in self.url.path.split('/') if each]
        split_len = len(split_path)
        self.name = split_path[0] if split_len > 0 \
            else None
        self.args = split_path[1:] if split_len > 1 \
            else []
        self.query = urllib.parse.parse_qs(self.url.query) if self.url.query \
            else dict()
        self.route = router.get(self.name) if self.name \
            else router.default if isinstance(router.default, Route) \
            else None

    def __call__(self, *args, **kwargs):
        return self.route(self.name, self.request, *self.args, **self.query)

    def __bool__(self):
        return self.route is not None and isinstance(self.route, Route)


class Action(object):
    """
        处理器
    """
    def __init__(self, name: str, accept: list, call_action, args: list):
        self.name = name or call_action.__name__
        self.accept = accept or []
        self.action = call_action
        self.args = collections.OrderedDict()
        if args:
            for arg in args:
                self.args[arg[0]] = arg[1]

    def __call__(self, controller, *args, **kwargs):
        if controller.method not in self.accept:
            return None
        r_buffer = self.action(controller, *args, **kwargs)
        return Response(controller.response_code, controller.response_header, controller.request.start_response,
                        r_buffer)


# 处理器装饰
def action(name: str=None, accept: list=None, args: list=None):
    def set_action(func):
        return Action(name or func.__name__, accept, func, args)
    return set_action


class Controller(object):
    """
        控制器 - 处理器任务分发
    """

    def __init__(self, name_controller=None, request: Request=None, name_action=None, *args, **kwargs):
        self.name = name_controller
        name_action = name_action or 'default'

        self.request = request
        self.method = self.request.method
        self.response_code = 200
        self.response_header = self.request.get_header()

        self.action = self.get_action(name_action) or self.default
        self.args = args
        self.kwargs = kwargs

    def __bool__(self):
        return self.action is not None and callable(self.action) and isinstance(self.action, Action)

    def __call__(self, *args, **kwargs):
        return self.action(self, *self.args, **self.kwargs)

    def get_action(self, name_action: str):
        if hasattr(self, name_action):
            get_action = getattr(self, name_action)
            if isinstance(get_action, Action):
                return get_action

    @action(accept=[HTTP.GET, HTTP.POST])
    def default(self, *args, **kwargs):
        self.response_header.add('Content-type', 'text/plain')
        return '%s default %s %s' % (self.name, self.method.to_str(), self.request.url)


class Response(object):
    """
        HTTP 响应
    """
    def __init__(self, code: int, header: Header, start_response, buffer=None):
        self.status = Status(code)
        self.header = header
        self.start_response = start_response if callable(start_response) else None

        self.buffer = buffer if not isinstance(buffer, str) or buffer is None else buffer.encode()

    def __iter__(self):
        self.start_response(self.status.to_str(), self.header.to_list())
        yield self.buffer


class Server(object):
    def __init__(self, router: Router, host='localhost', port=5000):
        self.router = router
        self.host = host
        self.port = port

    def __call__(self, environ, start_response):
        request = Request(environ, start_response)
        routing = self.router(request)
        if routing:
            controller = routing()
            if controller:
                return controller()
        else:
            request.start_response(Status(404).to_str(), Header(('Content-type', 'text/plain')).to_list())
            return ['{msg}'.format(msg=Status(404).to_str()).encode()]

    def run(self):
        wsgiref.simple_server.make_server(self.host, self.port, self).serve_forever()

