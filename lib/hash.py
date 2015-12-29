import hashlib


def md5(data):
    m = hashlib.md5()
    if isinstance(data, str):
        data = data.encode()
    m.update(data)
    return m.hexdigest()
