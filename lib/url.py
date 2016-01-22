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
        return self._parse.scheme or self._default_scheme or None

    @property
    def host(self):
        return self._parse.netloc or None

    @property
    def hostname(self):
        return self._parse.hostname or self._default_hostname or None

    @property
    def port(self):
        scheme = self.scheme or ''
        port = self._parse.port or self._default_port
        if scheme == 'http':
            return port or 80
        elif scheme == 'https':
            return port or 443
        elif scheme == 'ftp':
            return port or 21
        return port or None

    @property
    def path(self):
        return self._parse.path or None

    @property
    def params(self):
        return self._parse.params or None

    @property
    def query(self):
        return self._parse.query or None

    def dict_query(self):
        return urllib.parse.parse_qs(self._parse.query)

    def list_query(self):
        return urllib.parse.parse_qsl(self._parse.query)

    @property
    def fragment(self):
        return self._parse.fragment or None

    @property
    def username(self):
        return self._parse.username or None

    @property
    def password(self):
        return self._parse.password or None

    def items(self):
        yield 'scheme', self.scheme
        yield 'hostname', self.hostname
        yield 'port', self.port
        yield 'path', self.path
        yield 'params', self.params
        yield 'query', self.query
        yield 'fragment', self.fragment

    def dict_url(self):
        return dict(
            scheme=self.scheme,
            hostname=self.hostname,
            port=self.port,
            path=self.path,
            params=self.params,
            query=self.query,
            fragment=self.fragment
        )

    def str_url(self):
        str_url = [self.scheme or self._default_scheme]
        if self.scheme or self._default_scheme:
            str_url.append(':')
        if not self.hostname:
            str_url.clear()
        else:
            str_url.append('//%s' % self.hostname)
            if self.scheme == 'http' and self.port and self.port != 80:
                str_url.append(':%s' % self.port)
        if not self.path.startswith('/'):
            str_url.append('/')
        str_url.append(self.path)
        if self.path and self.params:
            str_url.append(';%s' % self.params)
        if self.query:
            str_url.append('?%s' % self.query)
        if self.fragment:
            str_url.append('#%s' % self.fragment)
        return ''.join(str_url)

    def is_equal(self, other):
        return self.dict_url() == other.dict_url() if isinstance(other, UrlParse) else str(self) == str(other)

    def __iter__(self):
        return self.items()

    def __str__(self):
        return self.str_url()

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.str_url())


def parse(url: str, default_scheme='', default_hostname='', default_port=0) -> UrlParse:
    return UrlParse(url, default_scheme, default_hostname, default_port)
