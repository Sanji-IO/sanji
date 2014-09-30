#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
This is s Sanji Onject
"""

from Queue import Empty
from Queue import Queue
import inspect
import logging
import signal
import sys
import os
import threading
from threading import Event
from threading import Thread
from time import sleep

from sanji.message import Message
from sanji.message import MessageType
from sanji.publish import Publish
from sanji.publish import Retry
from sanji.router import Router
from sanji.session import Session
from sanji.bundle import Bundle


logger = logging.getLogger()


class Sanji(object):
    """
    This is for sanji framework.
    """
    def __init__(self, *args, **kwargs):

        # Setup default options
        bundle = kwargs.get("bundle", None)
        connection = kwargs.get("connection", None)
        stop_event = kwargs.get("stop_event", Event())

        if connection is None:
            raise ValueError("Connection is required.")

        # Model-related
        bundle_dir = os.path.dirname(inspect.getfile(self.__class__))
        if bundle is None:
            bundle = Bundle(bundle_dir=bundle_dir)
        self.bundle = bundle
        self.stop_event = stop_event

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
        self.is_ready = Event()
        self.req_queue = Queue()
        self.res_queue = Queue()

        # Setup callbacks
        self._conn.set_on_connect(self.on_connect)
        self._conn.set_on_message(self.on_message)
        self._conn.set_on_connect(self.on_connect)
        self._conn.set_on_publish(self.on_publish)

        # Publisher
        self.publish = Publish(self._conn, self._session)

        # Register signal to call stop() (only mainthread could do this)
        if threading.current_thread().__class__.__name__ == '_MainThread':
            signal.signal(signal.SIGINT, self.exit)

        # Auto-register routes
        methods = inspect.getmembers(self, predicate=inspect.ismethod)
        self._register_routes(methods)

        # Custom init function
        if hasattr(self, 'init') and \
           hasattr(self.init, '__call__'):
            logger.debug("Custom init start")
            self.init(*args, **kwargs)
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
                message = self.req_queue.get_nowait()
                self.__dispatch_message(message)
            except Empty:
                sleep(0.1)
        logger.debug("_dispatch_message thread is terminated")

    def __dispatch_message(self, message):
        results = self.router.dispatch(message)
        if len(results) == 0:
            error_msg = "Route '%s' not found." % message.resource
            logger.info(error_msg)
            logger.debug(message.to_json())
            resp = self.publish.create_response(
                message, self.bundle.profile["name"])
            resp(code=404, data={"message": error_msg})
            return

        try:
            for result in results:  # same route
                resp = self.publish.create_response(
                    result["message"], self.bundle.profile["name"])
                print result["callbacks"]
                map(lambda cb: cb(self, result["message"], resp),
                    result["callbacks"])
        except Exception as e:
            logger.warning(e)
            resp = self.publish.create_response(
                message, self.bundle.profile["name"])
            resp(code=500, data={"message": "Internal Error."})

    def _resolve_responses(self, stop_event):
        """
        _resolve_responses
        """
        while not stop_event.is_set():
            try:
                message = self.res_queue.get_nowait()
                self.__resolve_responses(message)
            except Empty:
                sleep(0.1)
        logger.debug("_resolve_responses thread is terminated")

    def __resolve_responses(self, message):
        session = self._session.resolve(message.id, message)
        if session is None:
            logger.debug("Unknow response. Not for me.")

    def on_publish(self, client, userdata, mid):
        with self._session.session_lock:
            self._session.resolve_send(mid)

    def _create_thread_pool(self):
        # create a thread pool
        for _ in range(0, self.dispatch_thread_count):
            stop_event = Event()
            thread = Thread(target=self._dispatch_message,
                            name="thread-%s" % _, args=(stop_event,))
            thread.daemon = True
            thread.start()
            self.dispatch_thread_list.append((thread, stop_event))

        for _ in range(0, 1):
            stop_event = Event()
            thread = Thread(target=self._resolve_responses,
                            name="thread-%s" % _, args=(stop_event,))
            thread.daemon = True
            thread.start()
            self.dispatch_thread_list.append((thread, stop_event))

        logger.debug("Thread pool is created")

    def start(self):
        """
        start
        """
        def main_thread():
            # create resp, req thread pool
            self._create_thread_pool()

            # start connection, this will block until stop()
            self.conn_thread = Thread(target=self._conn.connect)
            self.conn_thread.daemon = True
            self.conn_thread.start()

            # register model to controller...
            self.is_ready.wait()
            self.deregister()
            self.register(self.get_profile())

            if hasattr(self, 'run'):
                logger.debug("Start running...")
                self.run()

        # start main_thread
        self.main_thread = Thread(target=main_thread)
        self.main_thread.daemon = True
        self.main_thread.start()

        if threading.current_thread().__class__.__name__ == '_MainThread':
            # control this bundle stop or not
            while not self.stop_event.wait(1):
                sleep(1)
        else:
            self.stop_event.wait()

        self.stop()
        logger.debug("Shutdown successfully")

    def exit(self, signum=None, frame=None):
        """
        hook ctrl + c to exit program
        """
        self.stop()
        sys.exit(0)

    def stop(self, *args, **kwargs):
        """
        exit
        """
        logger.debug("Bundle [%s] has been shutting down" %
                     self.bundle.profile["name"])

        if hasattr(self, 'before_stop') and \
           hasattr(self.before_stop, '__call__'):
            logger.debug("Invoking before_stop...")
            self.before_stop()

        self._conn.disconnect()
        self._session.stop()
        self.stop_event.set()

        # TODO: shutdown all threads
        for thread, event in self.dispatch_thread_list:
            event.set()
        for thread, event in self.dispatch_thread_list:
            thread.join()
        self.is_ready.clear()

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
        except (TypeError, ValueError) as e:
            logger.debug(e)
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
        self.is_ready.set()
        logger.debug("Connection established with result code %s" % rc)

    def register(self, reg_data, retry=True, interval=1, timeout=3):
        """
        register function
        retry
            True, infinity retries
            False, no retries
            Number, retries times
        interval
            time period for retry
        return
            False if no success
            Tunnel if success
        """
        resp = Retry(target=self.publish.direct.post,
                     args=("/controller/registration", reg_data,),
                     kwargs={"timeout": timeout},
                     options={"retry": retry, "interval": interval})
        if resp is None:
            logger.error("Can\'t not register to controller")
            sys.exit(1)

        self._conn.set_tunnel(resp.data["tunnel"])
        logger.info("Register successfully tunnel: %s"
                    % (resp.data["tunnel"],))

    def deregister(self, retry=True, interval=1, timeout=3):
        data = {
            "name": self.bundle.profile["name"]
        }

        Retry(target=self.publish.direct.delete,
              args=("/controller/registration", data,),
              kwargs={"timeout": timeout},
              options={"retry": retry, "interval": interval})
        logger.info("Deregister successfully tunnel: %s" %
                    (self._conn.tunnel,))

    def get_profile(self):
        self.bundle.profile["tunnel"] = self._conn.tunnel
        self.bundle.profile["resources"] = [_["resource"] for _ in
                                            self.bundle.profile["resources"]]
        return self.bundle.profile


def Route(resource=None, methods=None):
    """
    route
    """
    def _route(func):
        def wrapper(self, *args, **kwargs):
            # "test" argument means no wrap func this time,
            # return original func immediately.
            if kwargs.get("test", False):
                kwargs.pop("test")
                func(self, *args, **kwargs)

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
