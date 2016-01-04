# coding: utf-8


class Query(object):
    def __init__(self):
        self.__from__ = None
        self.__where__ = None

    def From(self, target):
        self.__from__ = target
        return self

    def Where(self, where):
        self.__where__ = where
        return self

    def Get(self):
        for each in self.__from__:
            if self.__where__(each):
                return each

    def ToList(self):
        for element in self.__from__:
            if self.__where__(element):
                yield element


class WhereEqual(object):
    def __init__(self, key: str, value):
        self.__key__ = key
        self.__value__ = value

    def __call__(self, element):
        if element.get(self.__key__) == self.__value__:
            return True
        return False

    def to_sql(self):
        return '%s = %s' % (self.__key__, self.__value__)


if __name__ == '__main__':
    data = [dict(id=3), dict(id=4), dict(id=4)]
    print(data)
    get = Query().From(data).Where(WhereEqual('id', 4)).ToList()
    print(get)
    get = list(get)
    print(get)
    for each in get:
        print(each)
    print(WhereEqual('id', 4).to_sql())

    d = dict(id=3, name=4, age=5)
    for each in d:
        print(each)
