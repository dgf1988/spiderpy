# coding: utf-8


class BaseObject(object):
    def hash(self):
        """

        :return:
        """
        raise NotImplementedError()

    def is_true(self):
        raise NotImplementedError()

    def is_equal(self, other):
        raise NotImplementedError()

    def to_str(self):
        raise NotImplementedError()


class Set(object):
    def __init__(self, iterable):
        self._set = set(item for item in iterable)

    @property
    def set(self):
        return self._set

    def is_true(self):
        return bool(self.set)

    def __bool__(self):
        return self.is_true()

    def is_equal(self, other):
        if isinstance(other, Set):
            return self.set == other.set
        if isinstance(other, set):
            return self.set == other
        return NotImplemented

    def __eq__(self, other):
        return self.is_equal(other)

    def to_str(self):
        return '<Set: %s>' % self.set

    def __str__(self):
        return self.to_str()

    def len(self):
        return len(self.set)

    def __len__(self):
        return self.len()

    def iter(self):
        return self.set.__iter__()

    def __iter__(self):
        return self.iter()

    def items(self):
        return (item for item in self.set)

    def has(self, item):
        return self.set.__contains__(item)

    def __contains__(self, item):
        return self.has(item)

    def pop(self):
        return self.set.pop()

    def push(self, item):
        self.set.add(item)

    def delete(self, item):
        """
         may be throw KeyError
        :param item:
        :return:
        """
        self.set.remove(item)

    def delete_if_exists(self, item):
        self.set.discard(item)

    def clear(self):
        self.set.clear()

    def is_disjoint(self, iterable):
        """
        是否相交
        :param iterable:
        :return:
        """
        return self.set.isdisjoint(iterable)

    def is_subset(self, iterable):
        """
        是否子集
        :param iterable:
        :return:
        """
        return self.set.issubset(iterable)

    def __lt__(self, other):
        return self.is_subset(other)

    def __le__(self, iterable):
        return self.is_subset(iterable)

    def is_supperset(self, iterable):
        """
        是否超集
        :param iterable:
        :return:
        """
        return self.set.issuperset(iterable)

    def __gt__(self, other):
        return self.is_supperset(other)

    def __ge__(self, iterable):
        return self.is_supperset(iterable)

    def union(self, *iterables):
        """
        并集 - 返回新集合
        :param iterables:
        :return:
        """
        return Set(self.set.union(*iterables))

    def __or__(self, other):
        return self.union(other)

    def update(self, *iterables):
        """
        并集 - 更新
        :param iterables:
        :return:
        """
        self.set.update(*iterables)

    def __ior__(self, other):
        self.update(other)
        return self

    def intersection(self, *iterables):
        """
        交集 - 返回新集合
        :param iterables:
        :return:
        """
        return Set(self.set.intersection(*iterables))

    def __and__(self, other):
        return self.intersection(other)

    def intersection_update(self, *iterables):
        self.set.intersection_update(*iterables)

    def __iand__(self, other):
        self.intersection_update(other)
        return self

    def difference(self, *iterables):
        """
        差集 - 返回新集合
        :param iterables:
        :return:
        """
        return Set(self.set.difference(*iterables))

    def __sub__(self, other):
        return self.difference(other)

    def difference_update(self, *iterables):
        self.set.difference_update(*iterables)

    def __isub__(self, other):
        self.difference_update(other)
        return self

    def symmetric_difference(self, iterable):
        """
        对称差 - 返回新集合
        :param iterable:
        :return:
        """
        return Set(self.set.symmetric_difference(iterable))

    def __xor__(self, other):
        return self.symmetric_difference(other)

    def symmetric_difference_update(self, iterable):
        self.set.symmetric_difference_update(iterable)

    def __ixor__(self, other):
        self.symmetric_difference_update(other)
        return self
