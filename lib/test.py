# coding: utf-8


class A(object):
    def __init__(self, a):
        self.a = a

    def __str__(self):
        return '<%s: a=%s>' % (type(self).__name__, self.a)


class B(object):
    def __init__(self, b):
        self.b = b

    def __str__(self):
        return '<%s: b=%s>' % (type(self).__name__, self.b)


class C(A, B):
    def __new__(cls, a, b):
        return object.__new__(cls)

    def __init__(self, a, b):
        A.__init__(self, a)
        B.__init__(self, b)

    def __str__(self):
        return '<%s: a=%s, b=%s>' % (type(self).__name__, self.a, self.b)


class I(object):
    def __init__(self, *args):
        self.args = args

    def type_args(self):
        return type(self.args)

    def iter_args(self):
        for a in self.args:
            yield a

    def str_args(self):
        return str(self.args)

    def len_args(self):
        return len(self.args)


class T(object):
    def __init__(self, k, v):
        self.k = k
        self.v = v

    def to_tuple(self):
        return self.k, self.v


if __name__ == '__main__':
    c = C('test a', 'test b')
    assert c.a == 'test a'
    assert c.b == 'test b'
    i = I(1, 2, 3, 4)
    print(i.type_args(), i.len_args(), i.str_args())
    ii = I(item for item in range(1, 5))
    print(ii.type_args(), ii.len_args(), ii.str_args())
    iii = I(*(item for item in range(1, 5)))
    print(iii.type_args(), iii.len_args(), iii.str_args())
    t = T(1, 2)
    print(t.to_tuple(), type(t.to_tuple()))
