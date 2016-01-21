# coding: utf-8
import enum

import lib.wsgi

CODE = {
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
        if status_code not in CODE:
            raise ValueError('%s is not in HTTP_CODE' % status_code)
        self.code = status_code
        self.msg = CODE[self.code]

    def __bool__(self):
        return self.code in CODE

    def to_str(self):
        return '%s %s' % (self.code, self.msg)


class METHOD(enum.Enum):
    """
        HTTP 方法 - 枚举
    """
    GET = 1
    POST = 2

    def __eq__(self, other):
        if isinstance(other, str):
            return self.to_str() == other
        return super().__eq__(other)

    def to_str(self):
        return 'GET' if self == self.GET else 'POST' if self == self.POST else ''

    @classmethod
    def from_str(cls, str_method: str):
        str_method = str_method.strip().upper()
        if str_method == 'GET':
            return cls.GET
        elif str_method == 'POST':
            return cls.POST


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
                self.add(arg[0], *arg[1:])

    def iter_items(self):
        for key, values in self.items():
            if not isinstance(values, list):
                values = [values]
            for value in values:
                yield key, value

    def iter_lines(self):
        for key, value in self.iter_items():
            yield '%s: %s\r\n' % (key, value)
        yield '\r\n'

    def to_list(self):
        return list(self.iter_items())

    def to_str(self):
        return ''.join(list(self.iter_lines()))

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


class Request(object):
    """
        HTTP 请求
    """

    def __init__(self, environ):
        self.environ = lib.wsgi.Environ(environ)
        self.url = self.environ.url
        self.method = METHOD.from_str(self.environ.method)

    def get_header(self):
        pass


class Response(object):
    """
        HTTP 响应
    """
    def __init__(self, code: int=200, header: Header=None, buffer: bytes=None):
        self.code = code
        self.header = header or Header()
        self.buffer = buffer or b''

    def __bool__(self):
        return self.code in CODE and isinstance(self.header, Header) and isinstance(self.buffer, bytes)

    def __call__(self, start_response):
        if not callable(start_response):
            raise ValueError('start_response "%s" is not callable' % start_response)
        start_response(Status(self.code).to_str(), self.header.to_list())
        return self

    def __iter__(self):
        yield self.buffer


class NotFountResponse(Response):
    def __init__(self):
        super().__init__(404, Header(['Content-type', 'text/plain']), Status(404).to_str().encode())
