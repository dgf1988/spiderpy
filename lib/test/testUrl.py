import unittest
from lib.url import Url


class MyTestCase(unittest.TestCase):
    def test_(self):
        self.assertEquals(Url().protocol, Url.Http)
        self.assertEquals(Url().str(), '/')
        self.assertEquals(Url('').str(), '/')
        self.assertEquals(Url('//').str(), '/')
        self.assertEquals(Url('///').str(), '/')
        self.assertEquals(Url('////').str(), '//')
        self.assertEquals(Url('/////').str(), '///')
        self.assertEquals(Url('/////').host, '')
        self.assertEquals(Url('./').str(), '/./')
        self.assertEquals(Url('/./').str(), '/./')
        self.assertEquals(Url('//', path='./').path, './')
        self.assertEquals(Url('//a', path='./').path, './')
        self.assertEquals(Url('//a', path='./').strpath(), '/./')
        self.assertEquals(Url('///./').path, '/./')
        self.assertEquals(Url().dict(), dict(protocol=Url.Http, host='', port=80, path='/', query={}))
        self.assertEquals(Url('/', protocol='httP'), Url())
        self.assertEquals(Url(host='www.hoetom.com', path='index.htmlstor', query=dict(id=3)).str(),
                          'http://www.hoetom.com/index.htmlstor?id=3')

    def test_raises(self):
        self.assertRaises(ValueError, Url, protocol='')
        self.assertRaises(ValueError, Url, port='')
        self.assertRaises(ValueError, Url, port=0)


if __name__ == '__main__':
    unittest.main()
