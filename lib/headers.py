# coding: utf-8
import re


__all__ = ['Headers', 'HeaderItem', 'HeaderValue', 'ContentType', 'UserAgent', 'TextPlain', 'TextHtml', 'TextCss']


def _flat_list(*args) -> list:
    flat_list = []
    for i in args:
        if isinstance(i, (tuple, list)):
            flat_list.extend(_flat_list(*i))
        else:
            flat_list.append(i)
    return flat_list


def _convert_header_key(key: str):
    if not key:
        raise ValueError('header item\'s key must be not empty')
    return '-'.join(each.capitalize() for each in re.split(r'[_\-\s]', key) if each)


class HeaderValue(object):
    def __init__(self, value: str, **params):
        if not value:
            raise ValueError('value must be not empty')
        self.value = value
        self.params = {k: v for k, v in params.items()}

    def str_params(self):
        return ';'.join(['%s=%s' % (k, v) for k, v in self.params.items()]) if self.params else ''

    def clear_params(self):
        self.params.clear()

    def has_param(self, key: str):
        return key in self.params

    def get_param(self, key: str):
        return self.params.get(key)

    def del_param(self, key: str):
        if key in self.params:
            del self.params[key]

    def set_param(self, key: str, value):
        if key and value:
            self.params[key] = str(value)

    def is_true(self):
        return bool(self.value)

    def is_equal(self, other):
        return self.value == other.value and self.params == other.params if isinstance(other, HeaderValue) \
            else self.to_str() == other if isinstance(other, str) else False

    def to_str(self):
        return '%s;%s' % (self.value, self.str_params()) if self.params else self.value.__str__()

    def __bool__(self):
        return self.is_true()

    def __iter__(self):
        yield self.value
        yield self.str_params()

    def __eq__(self, other):
        return self.is_equal(other)

    def __str__(self):
        return self.to_str()

    def __hash__(self):
        return hash(self.to_str())

    def __repr__(self):
        return '<%s: %s, %s>' % (self.__class__.__name__, self.value, self.str_params() if self.params else None)


class HeaderItem(object):
    def __init__(self, key: str, *values):
        self.key = _convert_header_key(key)
        values = _flat_list(*values)
        self.values = set([value for value in values if isinstance(value, (str, HeaderValue))])

    def str_values(self):
        return ', '.join([str(value) for value in self.values]) if self.values else ''

    def clear_values(self):
        self.values.clear()

    def has_value(self, value):
        return value in self.values

    def add_value(self, value):
        self.values.add(value)

    def del_value(self, value):
        self.values.remove(value)

    def set_value(self, *values):
        values = _flat_list(*values)
        self.values = set([value for value in values if isinstance(value, (str, HeaderValue))])

    def is_true(self):
        return bool(self.key) and bool(self.values)

    def is_equal(self, other):
        return self.key == other.key and self.values == other.values if isinstance(other, HeaderItem) \
            else self.to_str() == other if isinstance(other, str) else False

    def to_str(self):
        return '%s: %s' % (self.key, self.str_values())

    def __bool__(self):
        return self.is_true()

    def __eq__(self, other):
        return self.is_equal(other)

    def __str__(self):
        return self.to_str()

    def __iter__(self):
        yield self.key
        yield self.str_values()

    def __contains__(self, item):
        return self.has_value(item)

    def __repr__(self):
        return '<%s: %s, %s>' % (self.__class__.__name__, self.key, self.str_values())


class Headers(object):

    def __init__(self, *headeritems, **kw_headeritems):
        convert_headers = []
        for item in headeritems:
            if isinstance(item, (tuple, list)) and len(item) >= 2:
                convert_headers.append(HeaderItem(item[0], *item[1:]))
            elif isinstance(item, HeaderItem):
                convert_headers.append(item)

        for key, value in kw_headeritems.items():
            if isinstance(value, str):
                convert_headers.append(HeaderItem(key, value))

        self.headers = convert_headers

    def len(self):
        return len(self.headers)

    def len_if_true(self):
        return sum([1 for item in self.headers if item])

    def is_true(self):
        return bool(self.len_if_true())

    def items(self):
        return self.headers

    def items_if_true(self):
        return [item for item in self.headers if item]

    def lines(self):
        return [str(item) for item in self.headers]

    def keys(self):
        return [item.key for item in self.headers]

    def values(self):
        return [item.values for item in self.headers]

    def has(self, key: str) -> bool:
        key = _convert_header_key(key)
        for item in self.headers:
            if item.key == key:
                return True
        return False

    def get(self, key: str, default=None) -> HeaderItem:
        key = _convert_header_key(key)
        for item in self.headers:
            if item.key == key:
                return item
        return default

    def get_all(self, key: str):
        key = _convert_header_key(key)
        return [item for item in self.headers if item.key == key]

    def delete(self, key: str):
        key = _convert_header_key(key)
        self.headers = [item for item in self.headers if item.key != key]

    def delete_if_false(self):
        self.headers = [item for item in self.headers if item]

    def add(self, item):
        if isinstance(item, (tuple, list)) and len(item) >= 2:
            self.headers.append(HeaderItem(item[0], *item[1:]))
        elif isinstance(item, HeaderItem):
            self.headers.append(item)

    def add_many(self, *items, **kw_items):
        for item in items:
            self.add(item)
        for k, v in kw_items.items():
            self.add((k, v))

    def set(self, item):
        if isinstance(item, (tuple, list)) and len(item) >= 2:
            key, values = _convert_header_key(item[0]), item[1:]
            self.headers = [each_item for each_item in self.headers if each_item.key != key]
            self.headers.append(HeaderItem(key, *values))
        elif isinstance(item, HeaderItem):
            self.headers = [each_item for each_item in self.headers if each_item.key != item.key]
            self.headers.append(item)

    def set_many(self, *items, **kw_items):
        for item in items:
            self.set(item)
        for k, v in kw_items.items():
            self.set((k, v))

    def set_default(self, item):
        if isinstance(item, (tuple, list)) and len(item) >= 2:
            key, values = _convert_header_key(item[0]), item[1:]
            for each_item in self.headers:
                if each_item.key == key:
                    return each_item
            self.headers.append(HeaderItem(key, *values))
        elif isinstance(item, HeaderItem):
            for each_item in self.headers:
                if each_item.key == item.key:
                    return each_item
            self.headers.append(item)
        return item

    def set_default_many(self, *items, **kw_items):
        for item in items:
            self.set_default(item)
        for k, v in kw_items.items():
            self.set_default((k, v))

    def to_list(self):
        return [(item.key, item.str_values()) for item in self.headers]

    def to_str(self):
        return '\r\n'.join([item.__str__() for item in self.headers]) + '\r\n\r\n'

    def __len__(self):
        return self.len()

    def __bool__(self):
        return self.is_true()

    def __iter__(self):
        return self.headers

    def __contains__(self, item):
        return self.has(item) if isinstance(item, str) else self.has(item.key) if isinstance(item, HeaderItem) \
            else self.has(item[0]) if isinstance(item, (tuple, list)) else False

    def __getitem__(self, item: str) -> HeaderItem:
        return self.get(item)

    def __delitem__(self, key: str):
        return self.delete(key)

    def __setitem__(self, key: str, value):
        self.get(key).set_value(value)

    def __getattr__(self, item: str) -> HeaderItem:
        return self.get(item)

    def __delattr__(self, item: str):
        return self.delete(item)

    def __setattr__(self, key: str, value):
        if key == 'headers':
            return super().__setattr__(key, value)
        self.get(key).set_value(value)

    def __str__(self):
        return self.to_str()

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.headers)

    def __bytes__(self):
        return self.to_str().encode()


class Text(HeaderValue):

    @property
    def charset(self):
        return self.get_param('charset')

    @charset.setter
    def charset(self, value: str):
        self.set_param('charset', value)


class TextHtml(Text):
    def __init__(self, **params):
        super().__init__('text/html', **params)


class TextPlain(Text):
    def __init__(self, **params):
        super().__init__('text/plain', **params)


class TextXml(Text):
    def __init__(self, **params):
        super().__init__('text/xml', **params)


class TextCss(Text):
    def __init__(self, **params):
        super().__init__('text/css', **params)


class ContentType(HeaderItem):
    def __init__(self, *values):
        super().__init__('Content-Type', *values)


class UserAgent(HeaderItem):
    def __init__(self, *values):
        super().__init__('User-Agent', *values)
