import wsgiref.util
import wsgiref.simple_server
import wsgiref.headers
import wsgiref.handlers
import logging
import functools
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


class METHOD(enum.Enum):
    """
        HTTP 方法 - 枚举
    """
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


class Header(dict):
    """
        HTTP 头
    """

    def __init__(self, *args):
        """
            Header(('User-Agent', 'web/2.0'),('Content-type', 'text/plain'))
        :param args:
        :return:
        """
        super().__init__()
        for arg in args:
            if isinstance(arg, (tuple, list)) and len(arg) >= 2:
                self[arg[0]] = list(arg[1:])

    def iter_items(self):
        for key, values in self.items():
            if not isinstance(values, list):
                values = [values]
            for value in values:
                yield key, value

    def iter_line(self):
        for key, value in self.iter_items():
            yield '%s: %s\r\n' % (key, value)
        yield '\r\n'

    def to_list(self):
        return list(self.iter_items())

    def to_str(self):
        return ''.join(list(self.iter_line()))

    def add(self, key, *values):
        if key not in self:
            self[key] = []
        add_values = [value for value in values if value not in self[key]]
        self[key].extend(add_values)

    def set(self, key, *values):
        self[key] = list(values)

    @property
    def content_type(self):
        return self['Content-type']

    @content_type.setter
    def content_type(self, value):
        self['Content-type'] = value if isinstance(value, list) else [value]


class Environ(object):
    """
        HTTP请求环境 - 对environ进行包装
    """

    def __init__(self, environ: dict):
        """

        :param environ: 由WSGI服务器提供
        :return:
        """
        self.environ = environ
        self.url = urllib.parse.unquote(wsgiref.util.request_uri(self.environ))

    @property
    def addr(self):
        # 访问者IP地址
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


class Request(object):
    """
        HTTP 请求
    """

    def __init__(self, environ):
        self.environ = Environ(environ)
        self.url = self.environ.url
        self.method = METHOD.from_str(self.environ.method)

    def get_header(self):
        return Header()


class Response(object):
    """
        HTTP 响应
    """
    def __init__(self, code: int=200, header: Header=None, buffer: bytes=None):
        self.code = code
        self.header = header or Header()
        self.buffer = buffer or bytes()

    def __call__(self, start_response):
        if not callable(start_response):
            raise ValueError('start_response "%s" is not callable' % start_response)
        start_response(Status(self.code).to_str(), self.header.to_list())
        return self

    def __iter__(self):
        yield self.buffer

    def code(self, code: int):
        self.code = code
        return self


class NotFountResponse(Response):
    def __init__(self):
        super().__init__(404, Header(['content-type', 'text/plain']), Status(404).to_str().encode())


class Route(object):
    """
        线路
    """
    def __init__(self, name_controller: str, cls_controller):
        if not isinstance(cls_controller, type) or not issubclass(cls_controller, Controller):
            raise ValueError('%s is not controller' % cls_controller)
        self.controller = cls_controller

        self.name = name_controller or cls_controller.__name__
        if not self.name:
            raise ValueError('route name is empty')

    def __bool__(self):
        return isinstance(self.controller, type) and issubclass(self.controller, Controller)

    def __call__(self, *args, **kwargs):
        return self.controller(*args, **kwargs) if self else None

    def __iter__(self):
        yield self.name
        yield self.controller


class Router(collections.OrderedDict):
    """
        路由器
    """
    def __init__(self, host: str, *routes):
        super().__init__()
        self.host = host
        self.default_route = None
        for route in routes:
            if isinstance(route, Route):
                self[route.name] = route

    def iter_items(self):
        for route in self.values():
            yield route
        if isinstance(self.default, Route):
            yield self.default

    # 装饰器 - 设置默认控制器
    def default(self, cls_controller):
        self.default_route = Route('', cls_controller)
        return cls_controller

    # 装饰器 - 添加控制器
    def controller(self, name: str=None):
        def add_controller(cls_controller):
            route = Route(name, cls_controller)
            self[route.name] = route
            return cls_controller
        return add_controller

    def routing_controller_by_url(self, url: str):
        """
            路由解析
        :param url: 请求链接
        :return: 路线，参数表， 参数字典
        """
        if not url:
            return None, [], dict()

        # 请求链接解析
        logging.info('url = "%s"' % url)
        parse_url = urllib.parse.urlparse(url)
        if parse_url.hostname != self.host:
            return None, [], dict()
        list_path = [each for each in parse_url.path.split('/') if each]
        logging.info('list path = "%s"' % list_path)
        len_path = len(list_path)

        # 路由分发
        route_name = list_path[0] if len_path > 0 else None
        route = self[route_name] \
            if route_name and route_name in self and isinstance(self[route_name], Route) else None
        route_name = route_name if route else None
        route = route or self.default_route

        # 路由参数
        route_args = list_path if not route_name else list_path[1:] if len_path > 1 else []
        route_kwargs = {key: value for key, value in urllib.parse.parse_qsl(parse_url.query)} \
            if parse_url.query else dict()

        # 返回 - 路由，参数表，参数字典
        return route, route_args, route_kwargs

    def __call__(self, url: str):
        return self.routing_controller_by_url(url)


class Action(object):
    """
        处理器
    """
    def __init__(self, action_call, accept_method: list, *accept_args, **accept_kwargs):
        self.action_call = action_call if callable(action_call) else None

        self.accept_method = accept_method or []
        self.accept_args = accept_args
        self.accept_kwargs = accept_kwargs

    def __bool__(self):
        return self.action_call is not None and callable(self.action_call)

    def __call__(self, controller, *args, **kwargs) -> Response:
        """
            执行 - 执行控制器的处理函数
        :param controller: 控制器实例
        :param args: 执行的列表参数
        :param kwargs: 执行的字典参数
        :return: 返回控制器的响应
        """
        # 执行函数验证
        if not self:
            logging.warning('action %s is not callable' % controller.action_name)
            return None
        # 控制器实例验证
        if not isinstance(controller, Controller):
            logging.warning('%s is not controller instance' % controller)
            return None
        # 请求方法验证
        if controller.request.method not in self.accept_method:
            logging.warning('action %s http method %s is not in action accept method %s' %
                            (controller.action_name, controller.request.method, self.accept_method))
            return None
        # 请求参数验证
        action_args = []
        action_kwargs = dict()
        len_args = len(args)
        # 参数长度验证
        if len_args > len(self.accept_args) or len(kwargs) > len(self.accept_kwargs):
            logging.warning('len args %s or len kwargs %s is more then accept len args %s or kwargs %s' %
                            (len_args, len(kwargs), len(self.accept_args), len(self.accept_kwargs)))
            return None
        # 遍历验证和构建执行参数
        for i, accept_type in enumerate(self.accept_args):
            # 索引的参数不存在，使用None作默认值
            if i >= len_args:
                action_args.append(None)
                continue
            arg = args[i]
            # 如果验证不通过，返回None
            if accept_type is int and not arg.isnumeric():
                logging.warning('arg %s type is not accept type %s' % (arg, int))
                return None
            action_args.append(accept_type(arg))

        for key, accept_type in self.accept_kwargs.items():
            if key not in kwargs:
                action_kwargs[key] = None
                continue
            value = kwargs[key]
            if accept_type is int and not value.isnumeric():
                logging.warning('value %s type is not accept type %s' % (value, int))
                return None
            action_kwargs[key] = accept_type(value)

        # 执行控制器的处理函数，并返回控制器或执行函数的响应
        action_response = self.action_call(controller, *action_args, **action_kwargs)
        if isinstance(action_response, Response):
            return action_response
        else:
            return controller.response


# 处理器装饰
def action(accept_method: list, *accept_args, **accept_kwargs):
    # check accept type
    for accept_type in list(accept_args) + list(accept_kwargs.values()):
        if not isinstance(accept_type, type):
            raise ValueError('accept type %s must be type instance' % accept_type)

    def set_action(func):
        return Action(func, accept_method, *accept_args, **accept_kwargs)
    return set_action


class Controller(object):
    """
        控制器 - 处理器任务分发
    """

    def __init__(self, request: Request, *args, **kwargs):
        self.request = request
        self.response = Response()

        # 请求分发
        len_args = len(args)
        self.action_name = args[0] if len_args > 0 else None
        self.action = getattr(self, self.action_name) \
            if self.action_name and hasattr(self, self.action_name) and isinstance(getattr(self, self.action_name), Action) \
            else None
        self.action_name = self.action_name if self.action else None
        self.action = self.action or self.default

        # 参数构建
        self.action_args = args if not self.action_name else args[1:] if len_args > 1 else []
        self.action_kwargs = kwargs

    def __bool__(self):
        return isinstance(self.action, Action)

    def __call__(self) ->Response:
        return self.action(self, *self.action_args, **self.action_kwargs) if self else None

    @action(accept_method=[METHOD.GET, METHOD.POST])
    def default(self, *args, **kwargs):
        self.response.header.add('Content-type', 'text/html')
        body_items = [
            'url=%s' % self.request.url,
            'host=%s' % self.request.environ.host,
            'method=%s' % self.request.method,
        ]
        body = '<br/>'.join(body_items)
        self.response.buffer = body.encode()


class Server(object):
    def __init__(self, router: Router):
        # 路由器
        self.router = router

    def __call__(self, environ, start_response):
        # 请求
        request = Request(environ)
        # 路由， 列表参数， 字典参数
        route, args, kwargs = self.router(request.url)
        if route:
            # 路由成功后，通过路由生成控制器实例
            controller = route(request, *args, **kwargs)
            if controller:
                # 控制器生成成功后， 由控制器响应请求
                response = controller()
                if response:
                    # 发送响应，并返回响应实例
                    return response(start_response)
        # 返回 404错误 响应
        return NotFountResponse()(start_response)

    def listen(self, port=8080):
        wsgiref.simple_server.make_server(self.router.host, port, self).serve_forever()

