#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
This is s Sanji Onject
"""

from Queue import Queue
from Queue import Empty
import inspect
import logging
import os
import signal
import sys
from threading import Thread
from threading import Event

from sanji.message import SanjiMessage
from sanji.message import SanjiMessageType
from sanji.router import Router


"""
Status Codes
"""
CODE_OK = 200
CODE_BAD_REQUEST = 400
CODE_INTERNAL_SERVER_ERROR = 500


"""
Environment Variables
"""
BROKER_IP = os.getenv("BROKER_IP", "127.0.0.1")
BROKER_PORT = int(os.getenv("BROKER_PORT", 1883))

logger = logging.getLogger("Core")
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# create formatter and add it to the handlers
formatter = logging.Formatter("%(asctime)s - %(name)s - " +
                              "%(levelname)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)


class Sanji(object):
    """
    This is for sanji framework.
    """
    def __init__(self, connection=None):
        # Model-related
        self.model_name = None
        self.model_path = None

        # Router-related
        self.router = Router()
        self.thread_count = 10
        self.thread_list = []

        # Message Bus
        self._conn = connection
        self.in_data = Queue()

        # Setup callbacks
        self._conn.set_on_connect(self.on_connect)
        self._conn.set_on_message(self.on_message)
        self._conn.set_on_connect(self.on_connect)

        # Register signal to call stop()
        signal.signal(signal.SIGINT, self.stop)

        # Auto-register routes
        methods = inspect.getmembers(self, predicate=inspect.ismethod)
        self._register_routes(methods)

        # Custom init function
        self.init()

    def _register_routes(self, methods):
        """
        _register_routes
        """
        # setup routes by decorator
        methods = [(n, v) for (n, v) in methods if v.__name__ == "wrapper"]
        methods = sorted(methods, key=lambda x: x[1]._order)
        for name, value in methods:
            value()  # execute setting route

        return methods

    def _dispatch_message(self, stop_event):
        """
        _dispatch_message
        """
        while not stop_event.is_set():
            try:
                message = self.in_data.get(timeout=1)
            except Empty:
                continue

            results = self.router.dispatch(message)
            print results
            if len(results) == 0:
                print "no route found!"
                continue

            for result in results:  # same route
                map(lambda cb: cb(self, result["message"]),
                    result["callbacks"])

        print "Thread is terminated"

    def run(self):
        """
        run
        """
        # create a thread pool
        for _ in range(0, self.thread_count):
            stop_event = Event()
            thread = Thread(target=self._dispatch_message,
                            name="thread-%s" % _, args=(stop_event,))
            thread.daemon = True
            thread.start()
            self.thread_list.append((thread, stop_event))

        # start connection, this will block until stop()
        self._conn.connect()

    def stop(self):
        """
        exit
        """
        self._conn.disconnect()

        # TODO: shutdown all threads
        for thread, event in self.thread_list:
            event.set()
        for thread, event in self.thread_list:
            thread.join()
        # sys.exit(0)

    def init(self):
        """
        This is for user implement
        """
        pass

    def on_message(self, client, userdata, msg):
        """This function will recevie all message from mqtt
        client
            the client instance for this callback
        userdata
            the private user data as set in Client() or userdata_set()
        message
            an instance of MQTTMessage. This is a class with members topic,
            payload, qos, retain.
        """
        try:
            message = SanjiMessage(msg.payload)
        except TypeError:
            print "Got an invaild json string"
            return

        if message.type() == SanjiMessageType.UNKNOWN:
            print "Got an UNKNOWN message, don't dispatch"
            return

        self.in_data.put(message)

    def on_connect(self, client, userdata, flags, rc):
        """
        on_connect(self, client, obj, flags, rc):
        client
            the client instance for this callback
        userdata
            the private user data as set in Client() or userdata_set()
        flags
            response flags sent by the broker
        rc
            the connection result
        """
        self._conn.set_tunnel(self._conn.tunnel)
        print "Connected with result code " + str(rc)
        print "Listening on " + self._conn.tunnel


def Route(resource=None, methods=None):
    """
    route
    """
    def _route(func):
        def wrapper(self, *args, **kwargs):
            _methods = methods
            if isinstance(methods, str):
                _methods = [methods]
            route = self.router.route(resource)
            for method in _methods:
                getattr(route, method)(func)
        # Ordered by declare sequence
        # http://stackoverflow.com/questions/4459531/how-to-read-class-attributes-in-the-same-order-as-declared
        f_locals = sys._getframe(1).f_locals
        _order = len([v for v in f_locals.itervalues()
                     if hasattr(v, '__call__') and v.__name__ == "wrapper"])
        wrapper.__dict__["_order"] = _order
        return wrapper
    return _route
