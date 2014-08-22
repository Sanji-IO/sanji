#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from Queue import Queue
from Queue import Empty
import os
import sys
from threading import Event
from threading import Thread
import unittest

try:
    sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../../')
    from sanji.core import Sanji
    from sanji.core import Route
    from sanji.message import SanjiMessage
    from connection_mockup import ConnectionMockup
except ImportError as e:
    print e
    print "Please check the python PATH for import test module."
    exit(1)


class TestModel(Sanji):

    def a111112(self):
        pass

    @Route(resource="/model/test/:id", methods="get")
    def get(self, message):
        pass

    @Route(resource="/model/test/:id", methods="post")
    def post(self, message):
        pass

    @Route(resource="/model/test/:id", methods="delete")
    def delete(self, message):
        pass

    @Route(resource="/model/test/:id", methods="put")
    def put(self, message):
        pass

    @Route(resource="/model/:id", methods=["get", "delete", "put"])
    def generic(self, message):
        pass

    @Route(resource="/model/:thisismyid", methods=["get", "delete", "put"])
    def thisismyid(self, message):
        pass

    def a11111(self):
        pass

    @Route(resource="/model", methods="put")
    def put2(self, message):
        pass


class TestRouteFunction(unittest.TestCase):

    def test_route(self):
        test_model = TestModel(connection=ConnectionMockup())
        routes = test_model.router.routes
        self.assertIn("/model/test/:id", routes)
        self.assertEqual(4, len(routes["/model/test/:id"].handlers))
        self.assertIn("/model", routes)
        self.assertEqual(1, len(routes["/model"].handlers))
        self.assertIn("/model/:id", routes)
        self.assertEqual(3, len(routes["/model/:id"].handlers))


class TestSanjiClass(unittest.TestCase):
    # @classmethod
    # def setUpClass(cls):
    #     print "Mosquitto broker is up."

    # @classmethod
    # def tearDownClass(cls):
    #     print "Mosquitto broker is down."

    def setUp(self):
        self.test_model = TestModel(connection=ConnectionMockup())

    def tearDown(self):
        self.test_model.stop()
        self.test_model = None

    def test_on_message(self):
        # Normal message
        class Message(object):
            def __init__(self, payload):
                self.topic = ""
                self.qos = 2
                self.payload = payload

        message = Message({
            "id": 1234,
            "method": "get",
            "resource": "/test__dispatch_message",
            "data": {
                "test": "OK"
            }
        })
        smessage = SanjiMessage(message.payload)
        self.test_model.on_message(None, None, message)
        data = self.test_model.in_data.get()
        self.assertEqual(data.to_dict(), smessage.to_dict())

        # Non-JSON String message
        message = Message(None)
        self.test_model.on_message(None, None, message)
        with self.assertRaises(Empty):
            self.test_model.in_data.get(timeout=0.1)

        # UNKNOW TYPE message
        message = Message("{}")
        self.test_model.on_message(None, None, message)
        with self.assertRaises(Empty):
            self.test_model.in_data.get(timeout=0.1)

    def test__dispatch_message(self):
        queue = Queue()
        this = self
        # message1
        message1 = SanjiMessage({
            "id": 1234,
            "method": "get",
            "resource": "/test__dispatch_message",
            "data": {
                "test": "OK"
            }
        })

        def create_mock_handler(index):
            def _mock_handler(self, message):
                queue.put(index)

            return _mock_handler

        for _ in range(0, 10):
            self.test_model.router.get("/test__dispatch_message",
                                       create_mock_handler(_))

        # message2
        message2 = SanjiMessage({
            "id": 3456,
            "method": "get",
            "resource": "/test__dispatch_message/12345",
            "data": {
                "test": "OK"
            }
        })

        def mock_handler_2(self, message):
            this.assertEqual(12345, int(message.param["id"]))

        self.test_model.router.get("/test__dispatch_message/:id",
                                   mock_handler_2)

        # put messages in in_data queue
        self.test_model.in_data.put(message1)
        self.test_model.in_data.put(message2)

        # start dispatch messages
        event = Event()
        thread = Thread(target=self.test_model._dispatch_message,
                        args=(event,))
        thread.daemon = True
        thread.start()
        event.set()
        thread.join()

        # check dispatch sequence
        current_index = -1
        while queue.empty() is False:
            index = queue.get()
            self.assertLess(current_index, index)
            current_index = index

    def test_register_routes(self):
        def func_maker(name, order):
            def wrapper():
                print name
            wrapper.__dict__["_order"] = order
            return wrapper

        methods = [
            ("func1", func_maker("func1", 4)),
            ("func2", func_maker("func2", 3)),
            ("func3", func_maker("func3", 2)),
            ("func4", func_maker("func4", 1)),
        ]

        methods = self.test_model._register_routes(methods)
        previous = None
        for name, func in methods:
            if previous is None:
                previous = func
            self.assertLessEqual(previous._order, func._order)

    def test_run(self):
        self.test_model.run()


if __name__ == "__main__":
    unittest.main()
