# coding: utf-8
import logging

import lib.http


class Action(object):
    """
        处理器
    """
    def __init__(self, action_call, accept_method: list, *accept_args, **accept_kwargs):
        self.action_call = action_call if callable(action_call) else None

        self.accept_method = accept_method or []
        self.accept_args = accept_args
        self.accept_kwargs = accept_kwargs

    def __bool__(self):
        return callable(self.action_call)

    def __call__(self, controller, *args, **kwargs) -> lib.http.Response:
        """
            执行 - 执行控制器的处理函数
        :param controller: 控制器实例
        :param args: 执行的列表参数
        :param kwargs: 执行的字典参数
        :return: 返回控制器的响应
        """
        # 执行函数验证
        if not self:
            logging.warning('action %s is not callable' % controller.action_name)
            return None
        # 控制器实例验证
        if not isinstance(controller, Controller):
            logging.warning('%s is not controller instance' % controller)
            return None
        # 请求方法验证
        if controller.request.method not in self.accept_method:
            logging.warning('action %s http method %s is not in action accept method %s' %
                            (controller.action_name, controller.request.method, self.accept_method))
            return None
        # 请求参数验证
        action_args = []
        action_kwargs = dict()
        len_args = len(args)
        # 参数长度验证 - 参数过多，引发404
        if len_args > len(self.accept_args) or len(kwargs) > len(self.accept_kwargs):
            logging.warning('len args %s or len kwargs %s is more then accept len args %s or kwargs %s' %
                            (len_args, len(kwargs), len(self.accept_args), len(self.accept_kwargs)))
            return None
        # 遍历验证和构建执行参数
        for i, accept_type in enumerate(self.accept_args):
            # 索引的参数不存在，参数过少，使用None作默认值
            if i >= len_args:
                action_args.append(None)
                continue
            arg = args[i]
            # 如果验证不通过，返回None
            if accept_type is int and not arg.isnumeric():
                logging.warning('arg %s type %s is not accept type %s' % (arg, type(arg), int))
                return None
            action_args.append(accept_type(arg))

        for key, accept_type in self.accept_kwargs.items():
            if key not in kwargs:
                action_kwargs[key] = None
                continue
            value = kwargs[key]
            if accept_type is int and not value.isnumeric():
                logging.warning('value %s type %s is not accept type %s' % (value, type(value), int))
                return None
            action_kwargs[key] = accept_type(value)

        # 执行控制器的处理函数，并返回控制器或执行函数的响应
        action_response = self.action_call(controller, *action_args, **action_kwargs)
        return action_response if isinstance(action_response, lib.http.Response) else controller.response


# 处理器装饰
def action(accept_method: list, *accept_args, **accept_kwargs):
    # check accept type
    for accept_type in list(accept_args) + list(accept_kwargs.values()):
        if not isinstance(accept_type, type):
            raise ValueError('accept type %s must be type instance' % accept_type)

    def set_action(func):
        return Action(func, accept_method, *accept_args, **accept_kwargs)
    return set_action


class Controller(object):
    """
        控制器 - 处理器任务分发
    """

    def __init__(self, request: lib.http.Request, *args, **kwargs):
        self.request = request
        self.response = lib.http.Response()

        # 请求分发
        len_args = len(args)
        self.action_name = args[0] if len_args > 0 else None
        self.action = getattr(self, self.action_name) \
            if self.action_name and hasattr(self, self.action_name) and callable(getattr(self, self.action_name)) \
            else None
        self.action_name = self.action_name if self.action else None
        self.action = self.action or self.default

        # 参数构建
        self.action_args = args if not self.action_name else args[1:] if len_args > 1 else []
        self.action_kwargs = kwargs

    def __bool__(self):
        return isinstance(self.action, Action)

    def __call__(self) ->lib.http.Response:
        return self.action(self, *self.action_args, **self.action_kwargs) if self else None

    @action(accept_method=[lib.http.METHOD.GET, lib.http.METHOD.POST])
    def default(self, *args, **kwargs):
        self.response.header.add('Content-type', 'text/html')
        body_items = [
            'url=%s' % self.request.url_parse,
            'host=%s' % self.request.environ.host,
            'method=%s' % self.request.method,
        ]
        body = '<br/>'.join(body_items)
        self.response.buffer = body.encode()
