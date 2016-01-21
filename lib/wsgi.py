# coding: utf-8
import wsgiref.util
import urllib.parse


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
        get_url = self.environ['wsgi.url_scheme'] + '://'

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

    def iter_lines(self):
        for key, value in self.environ.items():
            yield '%s: %s\r\n' % (key, value)
        yield '\r\n'
