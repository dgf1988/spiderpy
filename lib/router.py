# coding: utf-8
import collections
import urllib.parse


class Route(object):
    """
        线路
    """
    def __init__(self, name: str, call):
        if not callable(call):
            raise ValueError('%s is not callable' % call)
        self.call = call

        self.name = name or call.__name__
        if not self.name:
            raise ValueError('route name is empty')

    def __bool__(self):
        return self.name and callable(self.call)

    def __call__(self, *args, **kwargs):
        return self.call(*args, **kwargs) if self else None

    def __iter__(self):
        yield self.name
        yield self.call


class Router(collections.OrderedDict):
    """
        路由器
    """
    def __init__(self, host: str, *route_args, **route_kwargs):
        super().__init__()
        self.host = host
        self.default_route = None

        for arg in route_args:
            if isinstance(arg, Route):
                self[arg.name] = arg
            if isinstance(arg, (tuple, list)) and len(arg) == 2:
                route = Route(arg[0], arg[1])
                self[route.name] = route

        for name, call in route_kwargs.items():
            route = Route(name, call)
            self[route.name] = route

    def iter_items(self):
        for route in self.values():
            yield route
        if isinstance(self.default, Route):
            yield self.default

    # 装饰器 - 设置默认控制器
    def default(self, cls_controller):
        self.default_route = Route('', cls_controller)
        return cls_controller

    # 装饰器 - 添加控制器
    def add(self, name: str=None):
        def add_route(call):
            route = Route(name, call)
            self[route.name] = route
            return call
        return add_route

    def routing_controller_by_url(self, url: str):
        """
            路由解析
        :param url: 请求链接
        :return: 路线，参数表， 参数字典
        """
        if not url:
            return None, [], dict()

        # 请求链接解析
        parse_url = urllib.parse.urlparse(url)
        if parse_url.hostname != self.host:
            return None, [], dict()
        list_path = [each for each in parse_url.path.split('/') if each]
        len_path = len(list_path)

        # 路由分发
        route_name = list_path[0] if len_path > 0 else None
        route = self[route_name] \
            if route_name and route_name in self and isinstance(self[route_name], Route) else None
        route_name = route_name if route else None
        route = route or self.default_route

        # 路由参数
        route_args = list_path if not route_name else list_path[1:] if len_path > 1 else []
        route_kwargs = {key: value for key, value in urllib.parse.parse_qsl(parse_url.query)} \
            if parse_url.query else dict()

        # 返回 - 路由，参数表，参数字典
        return route, route_args, route_kwargs

    def __call__(self, url: str):
        return self.routing_controller_by_url(url)
