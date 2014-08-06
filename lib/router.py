import re
import logging
from functools import wraps

logger = logging.getLogger()

def trim_uri(uri):
	return uri.strip(" \t\n\r/")

def parse_querystring(querystring):
	query = dict()

	if (querystring == None):
		return query

	for pair in querystring.split("&"):
		if len(pair) == 0:
			continue
		values = pair.split("=", 2)
		if (len(values) == 0):
			continue
		elif (len(values) == 1):
			value = True
		else:
			value = values[1]

		if values[0] in query.keys():
			if isinstance(query[values[0]], list):
				query[values[0]].append(value)
			else:
				query[values[0]] = [query[values[0]], value]
		else:
			query[values[0]] = value

	return query

def compile_uri(uri):
	return re.compile(
			"^" + trim_uri(re.sub(":(\w+)", r"(?P<\1>\w+?)", uri)) +
			"(\?(?P<querystring>.*))?$")


class Route(object):

	def __init__(self, uri):

		# syntax: /network/cellular/:id
		self.uri = trim_uri(uri)
		self.uriRegex = compile_uri(uri)
		self.handlers = []
		
		for method in ["get", "post", "put", "delete", "all"]:
			self.__setattr__(method, self.create_handler_func(method))

	def create_handler_func(self, method):
		def _handler(callback):
			self.handlers.append(dict(method=method, callback=callback))
			return self

		return _handler

	def dispatch(self, request, response):
		for handler in self.handlers:
			if handler["method"] != request["method"]:
				continue

			# fire
			handler["callback"](request, response)

class Router(object):

	def __init__(self):
		self.routes = []
		for method in ["get", "post", "put", "delete", "all"]:
			self.__setattr__(method, self.create_route_func(method=method))

	def route(self, uri):
		r = Route(uri)
		self.routes.append(r)

		return r

	def create_route_func(self, method):
		def _route(uri, handler):
			r = Route(uri).__getattribute__(method)(handler)
			self.routes.append(r)
			return self

		return _route

	def dispatch(self, request, response):
		uri = trim_uri(request["resource"])
		method = request["method"].lower()
		data = request["data"]
		response = dict(fired=False)

		# match routes
		for route in self.routes:
			print route

			s = route.uriRegex.search(uri)
			if s == None:
				continue

			# build params and querystring
			querystring = s.groupdict().pop("querystring", None)
			req = dict(
				method = method,
				uri = uri,
				param = s.groupdict(),
				query = Router.parse_querystring(querystring),
				data = data
			)

			logger.debug("Invoke route: [%s] %s" % (method, route.uri))
			route.dispatch(req, response)
