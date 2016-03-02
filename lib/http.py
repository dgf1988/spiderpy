# coding: utf-8
import enum
import http
import urllib.parse
import wsgiref.util
import re

import lib.headers
import lib.url


__all__ = ['STATUS', 'CODE', 'Status', 'METHOD']


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

    @property
    def code(self):
        return self.status.value

    @property
    def message(self):
        return self.status.phrase

    @property
    def description(self):
        return self.status.description

    def is_true(self):
        return isinstance(self.status, http.HTTPStatus)

    def is_equal(self, other):
        return self.status == other.status and self.code == other.code and self.message == other.message \
            if isinstance(other, Status) else self.to_str() == other if isinstance(other, str) else False

    def to_str(self):
        return '%s %s' % (self.code, self.message)

    def __eq__(self, other):
        return self.is_equal(other)

    def __iter__(self):
        yield self.code
        yield self.message
        yield self.description

    def __str__(self):
        return self.to_str()

    def __repr__(self):
        return '<%s: %s %s>' % (self.__class__.__name__, self.code, self.message)


class METHOD(enum.Enum):
    """
        HTTP 方法 - 枚举
    """
    GET = 1
    POST = 2

    def is_true(self):
        return bool(self)

    def is_equal(self, other):
        return self.to_str() == other if isinstance(other, str) else super().__eq__(other)

    def to_str(self):
        return 'GET' if self == self.GET else 'POST' if self == self.POST else ''

    def __eq__(self, other):
        return self.is_equal(other)

    def __str__(self):
        return self.to_str()

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.to_str())

    @classmethod
    def from_str(cls, str_method: str):
        str_method = str_method.strip().upper()
        return cls.GET if str_method == 'GET' else cls.POST if str_method == 'POST' else None


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
        self.url_parse = lib.url.parse(urllib.parse.unquote(wsgiref.util.request_uri(self.environ)))

    @property
    def os(self):
        return self.environ['OS']

    @property
    def content_type(self):
        return self.environ['CONTENT_TYPE']

    @property
    def content_length(self):
        return self.environ['CONTENT_LENGTH']

    # request
    @property
    def request_method(self):
        return self.environ['REQUEST_METHOD']

    @property
    def request_scheme(self):
        return wsgiref.util.guess_scheme(self.environ)

    @property
    def request_protocol(self):
        return self.environ['SERVER_PROTOCOL']

    @property
    def request_host(self):
        return self.environ['HTTP_HOST']

    @property
    def request_path(self):
        return self.environ['PATH_INFO']

    @property
    def request_query(self):
        # return urllib.parse.unquote(self.environ['QUERY_STRING'])
        return self.environ['QUERY_STRING']

    @property
    def request_addr(self):
        return self.environ['REMOTE_ADDR']

    # server
    @property
    def server_name(self):
        return self.environ['SERVER_NAME']

    @property
    def server_software(self):
        return self.environ['SERVER_SOFTWARE']

    @property
    def server_port(self):
        return int(self.environ['SERVER_PORT'])

    # wsgi
    @property
    def wsgi_version(self):
        return self.environ['wsgi.version']

    @property
    def wsgi_errors(self):
        return self.environ['wsgi.errors']

    @property
    def wsgi_multiprocess(self):
        return self.environ['wsgi.multiprocess']

    @property
    def wsgi_multithread(self):
        return self.environ['wsgi.multithread']

    # python
    @property
    def python_path(self):
        return self.environ['PYTHONPATH']

    @property
    def python_io_encoding(self):
        return self.environ['PYTHONIOENCODING']

    def len(self):
        return len(self.environ)

    def items(self):
        return self.environ.items()

    def keys(self):
        return self.environ.keys()

    def values(self):
        return self.environ.values()

    def get(self, key: str, default=None):
        return self.environ.get(key, default)

    def request_headers(self):
        matchs = (re.match(r'HTTP_(?P<key>\w+)', k, re.IGNORECASE) for k in self.environ.keys())
        return lib.headers.Headers((match.group('key'), self.environ.get(match.group())) for match in matchs if match)

    def request_items(self):
        yield 'Protocol', self.request_protocol
        yield 'Method', self.request_method
        yield 'Url', self.url_parse.str_url()
        for k, v in self.request_headers().items():
            yield k, v


class Request(object):
    """
        HTTP 请求
    """

    def __init__(self, environ):
        self.environ = Environ(environ)
        self.url_parse = self.environ.url_parse
        self.method = METHOD.from_str(self.environ.request_method)
        self.protocol = self.environ.request_protocol
        self.headers = self.environ.request_headers()

    def is_true(self):
        return self.headers.is_true() and bool(self.protocol) and self.method

    def __repr__(self):
        return '<%s: %s %s %s>' % (self.__class__.__name__, self.method, self.url_parse.str_url(), self.protocol)


class Response(object):
    """
        HTTP 响应
    """
    def __init__(self, code: int=200, header: lib.headers.Headers=None, buffer: bytes=None):
        self.code = code
        self.header = header or lib.headers.Headers()
        self.buffer = buffer or b''

    def __bool__(self):
        return self.code in CODE and self.header.is_true() and self.buffer

    def __call__(self, start_response):
        if not callable(start_response):
            raise ValueError('start_response "%s" is not callable' % start_response)
        start_response(Status(self.code).to_str(), self.header.to_list())
        yield self.buffer

    def __repr__(self):
        response_status = Status(self.code)
        return '<%s: %s %s>' % (self.__class__.__name__, response_status.code, response_status.message)


class NotFountResponse(Response):
    def __init__(self):
        super().__init__(404, lib.headers.Headers(['Content-type', 'text/plain']), Status(404).to_str().encode())
