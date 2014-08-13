"""
This is router class
"""

import re
import urlparse


def trim_uri(uri):
    return uri.strip(" \t\n\r/")

def parse_querystring(querystring):
    """
    Return parsed querystring in dict
    """
    qs_dict = urlparse.parse_qs(querystring, keep_blank_values=True)
    for key in qs_dict:
        if len(qs_dict[key]) != 1:
            continue
        qs_dict[key] = qs_dict[key][0]
        if qs_dict[key] == '':
            qs_dict[key] = True

    return qs_dict


def compile_uri(uri):
    """
    Return compiled regex for uri matching
    """
    return re.compile("^" + trim_uri(re.sub(r":(\w+)", r"(?P<\1>\w+?)", uri)) +
        r"(\?(?P<querystring>.*))?$")


class Route(object):
    """
    Route class
    """
    def __init__(self, uri):

        # syntax: /network/cellular/:id
        self.uri = trim_uri(uri)
        self.uri_regex = compile_uri(uri)
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

    def dispatch(self, request):
        callbacks = []
        for handler in self.handlers:
            if handler["method"] != request["method"]:
                continue

            callbacks.append(handler["callback"])
        return callbacks


class Router(object):
    """
    Router class
    """
    def __init__(self):
        self.routes = []
        for method in ["get", "post", "put", "delete", "all"]:
            self.__setattr__(method, self.create_route_func(method=method))

    def route(self, uri):
        route = Route(uri)
        self.routes.append(route)

        return route

    def create_route_func(self, method):
        def _route(uri, handler):
            route = Route(uri).__getattribute__(method)(handler)
            self.routes.append(route)
            return self

        return _route

    def dispatch(self, request):
        callbacks = []
        uri = trim_uri(request["resource"])
        method = request["method"].lower()
        data = request["data"]

        # match routes
        for route in self.routes:
            uri_match = route.uri_regex.search(uri)
            if uri_match == None:
                continue

            # build params and querystring
            querystring = uri_match.groupdict().pop("querystring", "")
            req = {
                "method": method,
                "uri": uri,
                "param": uri_match.groupdict(),
                "query": parse_querystring(querystring),
                "data": data
            }

            callbacks.append({
                "callbacks": route.dispatch(req),
                "req": req
            })

        return callbacks
