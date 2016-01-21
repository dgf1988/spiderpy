# coding: utf-8


__all__ = ['Headers', 'ContentType', 'TextPlain', 'TextHtml', 'TextCss']


def _convert_header_key(key: str):
    if not key:
        raise ValueError('header item\'s key must be not empty')
    return key.replace('_', '-')


class HeaderValue(object):
    def __init__(self, value: str, **params):
        if not value:
            raise ValueError('value must be not empty')
        self.value = value
        self.params = {k: str(v) for k, v in params.items()}

    def str_params(self):
        return ';'.join(['%s=%s' % (k, v) for k, v in self.params.items()]) if self.params else ''

    def has_param(self, key: str):
        return key in self.params

    def get_param(self, key: str):
        return self.params.get(key)

    def set_param(self, key: str, value):
        if value:
            self.params[key] = str(value)

    def del_param(self, key: str):
        if key in self.params:
            del self.params[key]

    def is_true(self):
        return bool(self.value) or bool(self.params)

    def is_equal(self, other):
        return self.value == other.value and self.params == other.params if isinstance(other, HeaderValue) \
            else self.to_str() == other if isinstance(other, str) else False

    def to_str(self):
        return '%s;%s' % (self.value, self.str_params()) if self.params else self.value.__str__()

    def __str__(self):
        return self.to_str()

    def __hash__(self):
        return hash(self.to_str())

    def __eq__(self, other):
        return self.is_equal(other)

    def __bool__(self):
        return self.is_true()

    def __repr__(self):
        return '%s(%s, %s)' % (self.__class__.__name__, self.value, self.str_params() if self.params else None)


class HeaderItem(object):
    def __init__(self, key: str, *values):
        self.key = _convert_header_key(key)
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

    def is_true(self):
        return bool(self.key) and bool(self.values)

    def is_equal(self, other):
        return self.key == other.key and self.values == other.values if isinstance(other, HeaderItem) else False

    def to_str(self):
        return '%s: %s' % (self.key, self.str_values())

    def __bool__(self):
        return self.is_true()

    def __eq__(self, other):
        return self.is_equal(other)

    def __str__(self):
        return self.to_str()

    def __iter__(self):
        return self.values.__iter__()

    def __repr__(self):
        return '%s(%s, %s)' % (self.__class__.__name__, self.key, self.str_values())


class Headers(object):
    def __init__(self, *headers, **kwargs):
        convert_headers = []
        for header in headers:
            if isinstance(header, (tuple, list)) and len(header) >= 2:
                convert_headers.append(HeaderItem(header[0], *header[1:]))
            elif isinstance(header, HeaderItem):
                convert_headers.append(header)

        for key, value in kwargs.items():
            if isinstance(value, str):
                convert_headers.append(HeaderItem(key, value))

        self.headers = convert_headers

    def len(self):
        return len(self.headers)

    def len_if_true(self):
        len_if_true = 0
        for item in self.items():
            if item:
                len_if_true += 1
        return len_if_true

    def items(self):
        return self.headers

    def items_if_true(self):
        for item in self.items():
            if item:
                yield item

    def keys(self):
        return [item.key for item in self.items()]

    def values(self):
        return [item.values for item in self.items()]

    def has(self, key: str) -> bool:
        return _convert_header_key(key.lower()) in [item.key.lower() for item in self.items()]

    def get(self, key: str, default=None) -> HeaderItem:
        key = _convert_header_key(key.lower())
        for item in self.items():
            if item.key.lower() == key:
                return item
        return default

    def get_all(self, key: str):
        key = _convert_header_key(key.lower())
        return [item for item in self.items() if item.key.lower() == key]

    def add(self, key: str, *values):
        self.headers.append(HeaderItem(key, *values))

    def delete(self, key: str):
        key = _convert_header_key(key.lower())
        self.headers = [item for item in self.items() if item.key.lower() != key]

    def delete_if_false(self):
        self.headers = [item for item in self.items() if item]

    def set(self, key: str, *values):
        self.delete(key)
        self.headers.append(HeaderItem(key, *values))

    def set_default(self, key: str, *values):
        get_value = self.get(key)
        if get_value is None:
            self.headers.append(HeaderItem(key, *values))
            return values
        return get_value

    def to_list(self):
        return [(item.key, item.str_values()) for item in self.items() if item.is_true()]

    def to_str(self):
        return '\r\n'.join([item.__str__() for item in self.items() if item.is_true()]) + '\r\n\r\n'

    def __len__(self):
        return self.len()

    def __bool__(self):
        return bool(self.len())

    def __iter__(self):
        return self.headers

    def __setitem__(self, key: str, values):
        values = values if isinstance(values, list) else list(values) if isinstance(values, tuple) else [values]
        self.set(key, *values)

    def __getitem__(self, item: str) -> HeaderItem:
        return self.get(item)

    def __delitem__(self, key: str):
        return self.delete(key)

    def __contains__(self, item: str):
        return self.has(item)

    def __str__(self):
        return self.to_str()

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, self.headers)

    def __bytes__(self):
        return self.to_str().encode()

    @property
    def content_type(self):
        return self.get('Content-Type')

    @property
    def user_agent(self):
        return self.get('User-Agent')


class Text(HeaderValue):

    @property
    def charset(self):
        return self.get_param('charset')

    @charset.setter
    def charset(self, value: str):
        self.set_param('charset', 'utf-8')


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


if __name__ == '__main__':
    h = Headers(('User-Agent', 's/2.3'),
                HeaderItem('Content-type', HeaderValue('text/html', charset='utf-8', q=3), HeaderValue('text/plain', q=0.3)))

    print(h)
    textcss = TextCss()
    textcss.charset = 'utf-8'

    h.content_type.add_value(TextXml(q=3, charset='utf-8'))
    print(h)
    print(h.content_type.has_value(TextPlain(q=0.3)))
    print(h.content_type.has_value('text/plain;q=0.3'))

    print(h.len_if_true(), h.len())
    h.content_type.key = ''
    print(h.len_if_true(), h.len())
    h.delete_if_false()
    print(h.len_if_true(), h.len())





