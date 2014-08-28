#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
This is s Sanji Onject
"""

from Queue import Empty
from Queue import Queue
import inspect
import logging
import os
import signal
import sys
from threading import Event
from threading import Thread

from sanji.message import Message
from sanji.message import MessageType
from sanji.publish import Publish
from sanji.router import Router
from sanji.session import Session


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

logger = logging.getLogger()


class Sanji(object):
    """
    This is for sanji framework.
    """
    def __init__(self, connection=None):
        # Model-related
        self.model_name = None
        self.model_path = None

        # Router-related (Dispatch)
        self.router = Router()
        self.dispatch_thread_count = 5
        self.dispatch_thread_list = []

        # Response-related (Resolve)
        self._session = Session()
        self.resolve_thread_count = 1
        self.resolve_thread_list = []

        # Message Bus
        self._conn = connection
        self.req_queue = Queue()
        self.res_queue = Queue()

        # Setup callbacks
        self._conn.set_on_connect(self.on_connect)
        self._conn.set_on_message(self.on_message)
        self._conn.set_on_connect(self.on_connect)

        # Publisher
        self.publish = Publish(self._conn, self._session)

        # Register signal to call stop()
        signal.signal(signal.SIGINT, self.stop)

        # Auto-register routes
        methods = inspect.getmembers(self, predicate=inspect.ismethod)
        self._register_routes(methods)

        # Custom init function
        logger.debug("Custom init start")
        self.init()
        logger.debug("Custom init finish")

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
                message = self.req_queue.get(timeout=0.5)
            except Empty:
                continue

            results = self.router.dispatch(message)
            if len(results) == 0:
                logger.debug("No route be found.")
                logger.debug(message.to_json())
                continue

            for result in results:  # same route
                map(lambda cb: cb(self, result["message"]),
                    result["callbacks"])
        logger.debug("_dispatch_message thread is terminated")

    def _resolve_responses(self, stop_event):
        """
        _resolve_responses
        """
        while not stop_event.is_set():
            try:
                message = self.res_queue.get(timeout=0.1)
            except Empty:
                continue
            session = self._session.resolve(message.id, message)
            if session is None:
                logger.debug("Unknow response. Not for me.")
        logger.debug("_resolve_responses thread is terminated")

    def run(self):
        """
        run
        """
        # create a thread pool
        for _ in range(0, self.dispatch_thread_count):
            stop_event = Event()
            thread = Thread(target=self._dispatch_message,
                            name="thread-%s" % _, args=(stop_event,))
            thread.daemon = True
            thread.start()
            self.dispatch_thread_list.append((thread, stop_event))
        logger.debug("Thread pool is created")
        # start connection, this will block until stop()
        self._conn.connect()

    def stop(self):
        """
        exit
        """
        logger.debug("Bundle is been shutting down")
        self._conn.disconnect()

        # TODO: shutdown all threads
        for thread, event in self.dispatch_thread_list:
            event.set()
        for thread, event in self.dispatch_thread_list:
            thread.join()

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
            message = Message(msg.payload)
        except TypeError:
            logger.debug("Got an invaild json string")
            return

        if message.type() == MessageType.UNKNOWN:
            logger.debug("Got an UNKNOWN message, don't dispatch")
            return

        if message.type() == MessageType.RESPONSE:
            self.res_queue.put(message)

        if message.type() == MessageType.REQUEST or \
           message.type() == MessageType.DIRECT or \
           message.type() == MessageType.HOOK or \
           message.type() == MessageType.EVENT:
            self.req_queue.put(message)

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
        logger.debug("Connection established with result code %s" % rc)

    def register(self):
        self.publish.post("/controller/registration")


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
