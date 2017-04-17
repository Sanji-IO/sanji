"""
This is router class
"""

import re
from sanji.message import trim_resource


def compile_resource(resource):
    """
    Return compiled regex for resource matching
    """
    return re.compile("^" + trim_resource(re.sub(r":(\w+)", r"(?P<\1>[\w-]+?)",
                      resource)) + r"(\?(?P<querystring>.*))?$")


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
        """
        create_handler_func
        """
        def _handler(callback, schema=None):
            """
            _handler
            """
            # reentrant default is False [POST, DELETE, PUT]
            reentrant = False
            if method == "get":
                reentrant = True

            self.handlers.append({
                "method": method,
                "callback": callback,
                "schema": schema,
                "reentrant": reentrant
            })
            return self

        return _handler

    def dispatch(self, message):
        """
        dispatch
        """
        handlers = []
        for handler in self.handlers:
            if handler["method"] != message.method:
                continue

            handlers.append(handler)
        return handlers

    def get_methods(self):
        methods = set()
        for handler in self.handlers:
            methods.add(handler["method"])

        return list(methods)


class Router(object):
    """
    Router class
    """
    def __init__(self):
        self.routes = {}
        for method in ["get", "post", "put", "delete", "all"]:
            self.__setattr__(method, self.create_route_func(method=method))

    def route(self, resource):
        """
        route
        """
        route = self.routes.get(resource, Route(resource))
        self.routes.update({resource: route})
        return route

    def create_route_func(self, method):
        """
        create_route_func
        """
        def _route(resource, handler, schema=None):
            """
            _route
            """
            route = self.routes.get(resource, Route(resource))
            route.__getattribute__(method)(handler, schema)
            self.routes.update({resource: route})
            return self

        return _route

    def dispatch(self, message):
        """
        dispatch
        """
        results = []
        # match routes
        for resource, route in self.routes.items():
            __message = message.match(route)
            if __message is None:
                continue

            route_result = route.dispatch(__message)
            if len(route_result) == 0:
                continue

            results.append({
                "handlers": route_result,
                "message": __message
            })

        return results

    def get_routes(self):
        routes = {}
        for resource, route in self.routes.iteritems():
            routes.update({resource: route.get_methods()})

        return routes
