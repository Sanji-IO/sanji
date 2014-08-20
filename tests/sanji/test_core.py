#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import json
import os
import sys
from threading import Lock
from threading import Thread
import time
import unittest

try:
    sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../../sanji')
    from core import Sanji
    from core import Route
    from message import SanjiMessage
    from connection.connection import Connection
except ImportError:
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
    @Route(resource="/model", methods="put")
    def put2(self, message):
        pass
    @Route(resource="/model/:id", methods=["get", "delete", "put"])
    def generic(self, message):
        pass
    @Route(resource="/model/:thisismyid", methods=["get", "delete", "put"])
    def thisismyid(self, message):
        pass
    def a11111(self):
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
        self.test_model = None

    def test_on_message(self):
        pass

    def test_on_connect(self):
        pass

    def test__dispatch_message(self):
        smsg = SanjiMessage({
                "id": 1234,
                "method": "put",
                "resource": "/model",
                "data": {
                    "test": "OK"
                }
            })
        results = self.test_model._dispatch_message(smsg)
        self.assertEqual(1, len(results))
        self.assertEqual(1, len(results[0]["callbacks"]))


        smsg = SanjiMessage({
                "id": 1234,
                "method": "get",
                "resource": "/model/3345678",
                "data": {
                    "test": "OK"
                }
            })
        results = self.test_model._dispatch_message(smsg)
        self.assertEqual(2, len(results))
        self.assertEqual(1, len(results[0]["callbacks"]))
        self.assertEqual(3345678, int(results[0]["message"].param["id"]))
        self.assertEqual(3345678, int(results[1]["message"].param["thisismyid"]))


    def test__get_thread(self):
        pass

    def test__close_thread(self):
        pass

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
            if previous == None:
                previous = func
            self.assertLessEqual(previous._order, func._order)

    def test_run(self):
        pass

    def test_stop(self):
        pass

if __name__ == "__main__":
    unittest.main()
