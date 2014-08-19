"""
This is router class
"""

import re
from message import trim_resource

def compile_resource(resource):
    """
    Return compiled regex for resource matching
    """
    return re.compile("^" + trim_resource(re.sub(r":(\w+)", r"(?P<\1>\w+?)", resource)) +
        r"(\?(?P<querystring>.*))?$")


class Route(object):
    """
    Route class
    """
    def __init__(self, resource):

        # syntax: /network/cellular/:id
        self.resource = trim_resource(resource)
        self.resource_regex = compile_resource(resource)
        self.handlers = []
        
        for method in ["get", "post", "put", "delete", "all"]:
            self.__setattr__(method, self.create_handler_func(method))

    def create_handler_func(self, method):

        def _handler(callback):
            # reentrant default is False [POST, DELETE, PUT]
            reentrant = False
            if method == "get":
                reentrant = True

            self.handlers.append({
                "method": method,
                "callback": callback,
                "reentrant": reentrant
            })
            return self

        return _handler

    def dispatch(self, message):
        callbacks = []
        for handler in self.handlers:
            if handler["method"] != message.method:
                continue

            callbacks.append(handler["callback"])
        return callbacks


class Router(object):
    """
    Router class
    """
    def __init__(self):
        self.routes = {}
        for method in ["get", "post", "put", "delete", "all"]:
            self.__setattr__(method, self.create_route_func(method=method))

    def route(self, resource):
        route = self.routes.get(resource, Route(resource))
        self.routes.update({resource: route})
        # self.routes.append(route)

        return route

    def create_route_func(self, method):
        def _route(resource, handler):
            route = self.routes.get(resource, Route(resource))
            route.__getattribute__(method)(handler)
            self.routes.update({resource: route})
            # self.routes.append(route)
            return self

        return _route

    def dispatch(self, message):
        results = []
        # match routes
        for resource, route in self.routes.items():
            __message = message.match(route)
            if __message == None:
                continue
            results.append({
                "callbacks": route.dispatch(__message),
                "message": __message
            })

        return results
