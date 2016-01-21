# coding: utf-8
import wsgiref.simple_server

import lib.http
import lib.router


class Server(object):
    def __init__(self, router: lib.router.Router):
        # 路由器
        self.router = router

    def __call__(self, environ, start_response):
        # 请求
        request = lib.http.Request(environ)
        # 路由， 列表参数， 字典参数
        route, args, kwargs = self.router(request.url)
        if route:
            # 路由成功后，通过路由生成控制器实例
            controller = route(request, *args, **kwargs)
            if controller:
                # 控制器生成成功后， 由控制器响应请求
                response = controller()
                if response:
                    # 发送响应，并返回响应实例
                    return response(start_response)
        # 返回 404错误 响应
        return lib.http.NotFountResponse()(start_response)

    def listen(self, port=8080):
        wsgiref.simple_server.make_server(self.router.host, port, self).serve_forever()


if __name__ == '__main__':
    pass
