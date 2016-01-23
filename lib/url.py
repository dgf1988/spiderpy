# -*- coding: utf-8 -*-
import urllib.parse

__all__ = ['parse', 'UrlParse']


class UrlParse(object):
    def __init__(self, url: str, default_scheme='', default_hostname='', default_port=0):
        url = url or '/'
        self._parse = urllib.parse.urlparse(url, default_scheme)
        self._default_scheme = default_scheme
        self._default_hostname = default_hostname
        self._default_port = default_port

    @property
    def scheme(self):
        return self._parse.scheme or self._default_scheme or ''

    @property
    def host(self):
        return self._parse.netloc or ''

    @property
    def hostname(self):
        return self._parse.hostname or self._default_hostname or ''

    @property
    def port(self):
        scheme = self.scheme.lower()
        port = self._parse.port or self._default_port
        if scheme == 'http':
            return port or 80
        elif scheme == 'https':
            return port or 443
        elif scheme == 'ftp':
            return port or 21
        return port or 0

    @property
    def path(self):
        return self._parse.path or ''

    @property
    def params(self):
        return self._parse.params or ''

    @property
    def query(self):
        return self._parse.query or ''

    def dict_query(self):
        return urllib.parse.parse_qs(self._parse.query)

    def list_query(self):
        return urllib.parse.parse_qsl(self._parse.query)

    @property
    def fragment(self):
        return self._parse.fragment or ''

    @property
    def username(self):
        return self._parse.username or ''

    @property
    def password(self):
        return self._parse.password or ''

    def items(self):
        yield 'scheme', self.scheme
        yield 'username', self.username
        yield 'password', self.password
        yield 'hostname', self.hostname
        yield 'port', self.port
        yield 'path', self.path
        yield 'params', self.params
        yield 'query', self.query
        yield 'fragment', self.fragment

    def dict_url(self):
        return dict(
            scheme=self.scheme,
            username=self.username,
            password=self.password,
            hostname=self.hostname,
            port=self.port,
            path=self.path,
            params=self.params,
            query=self.query,
            fragment=self.fragment
        )

    def str_url(self):
        scheme = self.scheme.lower()
        hostname = self.hostname
        port = self.port
        path = self.path
        params = self.params
        query = self.query
        fragment = self.fragment
        url_items = [scheme, ':'] if scheme and hostname else []
        if hostname:
            url_items.append('//%s' % hostname)
            if scheme == 'http' and port and port != 80:
                url_items.append(':%s' % port)
        if not path.startswith('/'):
            url_items.append('/')
        url_items.append(path)
        if path and params:
            url_items.append(';%s' % params)
        if query:
            url_items.append('?%s' % query)
        if fragment:
            url_items.append('#%s' % fragment)
        return ''.join(url_items)

    def is_true(self):
        return isinstance(self.scheme, str) and isinstance(self.username, str) and isinstance(self.password, str) and \
                isinstance(self.hostname, str) and isinstance(self.port, int) and isinstance(self.path, str) and \
                isinstance(self.params, str) and isinstance(self.query, str) and isinstance(self.fragment, str)

    def is_equal(self, other):
        return self.dict_url() == other.dict_url() if isinstance(other, UrlParse) else str(self) == str(other)

    def to_str(self):
        return self.str_url()

    def __str__(self):
        return self.to_str()

    def __iter__(self):
        return self.items()

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.str_url())


def parse(url: str, default_scheme='', default_hostname='', default_port=0) -> UrlParse:
    return UrlParse(url, default_scheme, default_hostname, default_port)
