import unittest
from lib.url import UrlParse


class MyTestCase(unittest.TestCase):
    def test_(self):
        self.assertEquals(UrlParse().protocol, UrlParse.Http)
        self.assertEquals(UrlParse().str(), '/')
        self.assertEquals(UrlParse('').str(), '/')
        self.assertEquals(UrlParse('//').str(), '/')
        self.assertEquals(UrlParse('///').str(), '/')
        self.assertEquals(UrlParse('////').str(), '//')
        self.assertEquals(UrlParse('/////').str(), '///')
        self.assertEquals(UrlParse('/////').host, '')
        self.assertEquals(UrlParse('./').str(), '/./')
        self.assertEquals(UrlParse('/./').str(), '/./')
        self.assertEquals(UrlParse('//', path='./').path, './')
        self.assertEquals(UrlParse('//a', path='./').path, './')
        self.assertEquals(UrlParse('//a', path='./').strpath(), '/./')
        self.assertEquals(UrlParse('///./').path, '/./')
        self.assertEquals(UrlParse().dict(), dict(protocol=UrlParse.Http, host='', port=80, path='/', query={}))
        self.assertEquals(UrlParse('/', protocol='httP'), UrlParse())
        self.assertEquals(UrlParse(host='www.hoetom.com', path='index.htmlstor', query=dict(id=3)).str(),
                          'http://www.hoetom.com/index.htmlstor?id=3')

    def test_raises(self):
        self.assertRaises(ValueError, UrlParse, protocol='')
        self.assertRaises(ValueError, UrlParse, port='')
        self.assertRaises(ValueError, UrlParse, port=0)


if __name__ == '__main__':
    unittest.main()
