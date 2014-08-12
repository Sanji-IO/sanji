import re
import logging
import urlparse


def trim_uri(uri):
	return uri.strip(" \t\n\r/")


def parse_querystring(querystring):
	qsDict = urlparse.parse_qs(querystring, keep_blank_values=True)
	for key in qsDict:
		if len(qsDict[key]) != 1:
			continue
		qsDict[key] = qsDict[key][0]
		if qsDict[key] == '':
			qsDict[key] = True

	return qsDict


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
			print route.uri

			s = route.uriRegex.search(uri)
			if s == None:
				continue

			# build params and querystring
			querystring = s.groupdict().pop("querystring", "")
			req = dict(
				method = method,
				uri = uri,
				param = s.groupdict(),
				query = parse_querystring(querystring),
				data = data
			)

			# logger.debug("Invoke route: [%s] %s" % (method, route.uri))
			route.dispatch(req, response)
