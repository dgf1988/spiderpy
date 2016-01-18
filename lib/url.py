# -*- coding: utf-8 -*-
import re
import requests
import urllib.parse
import hashlib


class Url(object):
    AcceptProtocol = ('http', 'https')
    Http = 'http'
    Https = 'https'

    def __init__(self, strurl='', protocol='http', host='', port=80, path='/', query=None):
        if not query:
            query = {}
        self.__protocol = 'http'
        self.__port = 80
        self.__host = ''
        self.__path = '/'
        self.__query = {}
        if isinstance(strurl, str) and strurl:
            urldict = self.parse(strurl)
            if 'protocol' in urldict and urldict['protocol']:
                protocol = urldict['protocol']
            if 'host' in urldict and urldict['host']:
                host = urldict['host']
            if 'port' in urldict and urldict['port']:
                port = urldict['port']
            if 'path' in urldict and urldict['path'] and urldict['path'] is not '/':
                path = urldict['path']
            if 'query' in urldict and urldict['query']:
                query.update(**urldict['query'])
        self.protocol = protocol
        self.host = host
        self.port = port
        self.path = path
        for k, v in query.items():
            if not isinstance(v, str):
                query[k] = str(v)
        self.query = query
        pass

    @property
    def protocol(self):
        return self.__protocol

    @protocol.setter
    def protocol(self, protocol):
        if not isinstance(protocol, str):
            raise ValueError
        protocol = protocol.lower()
        if protocol not in self.AcceptProtocol:
            raise ValueError
        self.__protocol = protocol

    def strprotocol(self):
        if self.host and self.protocol:
            return self.protocol + ':'
        return ''

    @property
    def port(self):
        return self.__port

    @port.setter
    def port(self, port):
        if not isinstance(port, int) or port <= 0:
            raise ValueError
        self.__port = port

    def strport(self):
        if self.port != 80 and self.host:
            return ':%s' % self.port
        return ''

    @property
    def host(self):
        return self.__host

    @host.setter
    def host(self, host):
        if not isinstance(host, str):
            raise ValueError
        self.__host = host

    def strhost(self):
        if self.host:
            return '//%s' % self.host
        else:
            return ''

    @property
    def path(self):
        return self.__path

    @path.setter
    def path(self, path):
        if not isinstance(path, str):
            raise ValueError
        self.__path = path.strip()

    def strpath(self):
        pathspilt = re.match(r'^/.*', self.path)
        if pathspilt:
            return '%s' % self.path
        else:
            return '/%s' % self.path

    @property
    def query(self):
        return self.__query

    @query.setter
    def query(self, query):
        if not query:
            self.__query = {}
        else:
            self.__query = query

    def strquery(self):
        if self.query:
            return '?%s' % urllib.parse.urlencode(self.query)
        else:
            return ''

    def strsrc(self):
        return self.strpath() + self.strquery()

    def str(self):
        return self.strprotocol() + self.strhost() + self.strport() + self.strsrc()

    def dict(self):
        return dict(
            protocol=self.protocol,
            host=self.host,
            port=self.port,
            path=self.path,
            query=self.query
        )

    def md5(self):
        m = hashlib.md5()
        m.update(self.str().encode())
        return m.hexdigest()

    def get(self, charset='utf-8', timeout=100):
        response = requests.get(self.str(), timeout=timeout)
        response.encoding = charset
        return response.status_code, response.text

    def __str__(self):
        return self.str()

    def __hash__(self):
        return hash(self.str())

    def __eq__(self, other):
        if isinstance(other, Url):
            return self.dict() == other.dict()
        return self.str() == str(other)

    @staticmethod
    def parse(url):
        if not isinstance(url, str):
            raise ValueError
        dicturl = {}
        parseurl = urllib.parse.urlparse(url)
        if parseurl.scheme:
            dicturl['protocol'] = parseurl.scheme
        if parseurl.hostname:
            dicturl['host'] = parseurl.hostname
        if parseurl.port:
            dicturl['port'] = parseurl.port
        if parseurl.path:
            dicturl['path'] = parseurl.path
        if parseurl.query:
            dicturl['query'] = {item[0]: item[1] for item in urllib.parse.parse_qsl(parseurl.query, 1)}
        return dicturl


def parse(str_url: str):
    return Url.parse(str_url)


def get(str_url: str, charset='utf-8', timeout=100):
    return Url(str_url).get(charset=charset, timeout=timeout)
