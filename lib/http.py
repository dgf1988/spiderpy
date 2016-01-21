# coding: utf-8
import enum
import http

import lib.wsgi
import lib.headers


STATUS = http.HTTPStatus
CODE = {status.value: status for status in STATUS.__members__.values()}


class Status(object):
    """
        HTTP 状态
    """
    def __init__(self, code: int):
        if code not in CODE:
            raise ValueError('code "%s" not in http code' % code)
        self.status = CODE[code]
        self.code = self.status.value
        self.message = self.status.phrase
        self.description = self.status.description

    def __eq__(self, other):
        return self.status == other.status and self.code == other.code and self.message == other.message \
            if isinstance(other, Status) else False

    def __iter__(self):
        yield self.code
        yield self.message
        yield self.description

    def to_str(self):
        return '%s %s' % (self.code, self.message)


class METHOD(enum.Enum):
    """
        HTTP 方法 - 枚举
    """
    GET = 1
    POST = 2

    def __eq__(self, other):
        return self.to_str() == other if isinstance(other, str) else super().__eq__(other)

    def to_str(self):
        return 'GET' if self == self.GET else 'POST' if self == self.POST else ''

    @classmethod
    def from_str(cls, str_method: str):
        str_method = str_method.strip().upper()
        return cls.GET if str_method == 'GET' else cls.POST if str_method == 'POST' else None


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
    def __init__(self, code: int=200, header: lib.headers.Headers=None, buffer: bytes=None):
        self.code = code
        self.header = header or lib.headers.Headers()
        self.buffer = buffer or b''

    def __bool__(self):
        return self.code in CODE and isinstance(self.header, lib.headers.Headers) and isinstance(self.buffer, bytes)

    def __call__(self, start_response):
        if not callable(start_response):
            raise ValueError('start_response "%s" is not callable' % start_response)
        start_response(Status(self.code).to_str(), self.header.to_list())
        return self

    def __iter__(self):
        yield self.buffer


class NotFountResponse(Response):
    def __init__(self):
        super().__init__(404, lib.headers.Headers(['Content-type', 'text/plain']), Status(404).to_str().encode())
