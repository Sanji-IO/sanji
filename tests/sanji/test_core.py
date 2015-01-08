#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from __future__ import print_function

from mock import Mock
from mock import patch
from mock import ANY
import os
import sys
from threading import Event
from threading import Thread
import logging

if sys.version_info >= (2, 7):
    import unittest
else:
    import unittest2 as unittest

try:
    from queue import Empty
except ImportError as e:
    print(e)
    from Queue import Empty

from voluptuous import Schema
from voluptuous import Required
from voluptuous import All
from voluptuous import Length
from voluptuous import Range

try:
    sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../../')
    from sanji.core import Sanji
    from sanji.core import Route
    from sanji.bundle import Bundle
    from sanji.bundle import BundleConfigError
    from sanji.message import Message
    from sanji.message import MessageType
    from sanji.connection.mockup import Mockup
except ImportError as e:
    print(e)
    print("Please check the python PATH for import test module.")
    exit(1)

bundle_dir = os.path.normpath(os.path.realpath(__file__) +
                              './../../mockup/bundle')


class TestModel(Sanji):

    def a111112(self):
        pass

    @Route(resource="/model/test/:id", methods="get")
    def get(self, message, response):
        pass

    @Route(resource="/model/test/:id", methods="post")
    def post(self, message, response):
        pass

    @Route(resource="/model/test/:id", methods="delete")
    def delete(self, message, response):
        pass

    @Route(resource="/model/test/:id", methods="put")
    def put(self, message, response):
        pass

    @Route(resource="/model/:id", methods=["get", "delete", "put"])
    def generic(self, message, response):
        pass

    @Route(resource="/model/:thisismyid", methods=["get", "delete", "put"])
    def thisismyid(self, message, response):
        pass

    def a11111(self):
        pass

    @Route(resource="/model", methods="put")
    def put2(self, message, response):
        pass

    @Route(resource="/mockup_resource", methods="get")
    def mockup_handler(self, message, response):
        response(message)

    def before_stop(self):
        pass

    def run(self):
        pass

    def init(self, *args, **kwargs):
        self.test_variable = kwargs.get("test_variable", None)


class TestRouteFunction(unittest.TestCase):

    def test_route(self):
        bundle = Bundle(bundle_dir=bundle_dir)
        test_model = TestModel(connection=Mockup(),
                               bundle=bundle)
        routes = test_model.router.routes
        self.assertIn("/model/test/:id", routes)
        self.assertEqual(4, len(routes["/model/test/:id"].handlers))
        self.assertIn("/model", routes)
        self.assertEqual(1, len(routes["/model"].handlers))
        self.assertIn("/model/:id", routes)
        self.assertEqual(3, len(routes["/model/:id"].handlers))

        # while test=True don't warp function
        def resp(test):
            self.assertTrue(test)
        test_model.mockup_handler(True, resp, test=True)


class TestSanjiClass(unittest.TestCase):

    @patch("sanji.session.Thread")
    def setUp(self, Thread):
        self.bundle = Bundle(bundle_dir=bundle_dir)
        self.test_model = TestModel(connection=Mockup(),
                                    bundle=self.bundle)

    def tearDown(self):
        self.test_model.stop()
        self.test_model = None
        self.bundle = None

    def test_init(self):
        with self.assertRaises(BundleConfigError):
            TestModel(connection=Mockup())

        with self.assertRaises(ValueError):
            TestModel()

        event = Event()
        bundle = Bundle(bundle_dir=bundle_dir)
        tm = TestModel(bundle=bundle, connection=Mockup(),
                       stop_event=event, test_variable=True)

        # bypassing test_variable to init()
        self.assertTrue(tm.test_variable)

    def test_on_publish(self):
        self.test_model.on_publish(None, None, 1)

    def test_on_sanji_message(self):
        # Normal message
        class MyMessage(object):
            def __init__(self, payload):
                self.topic = ""
                self.qos = 2
                self.payload = payload

        # Request
        message = MyMessage({
            "id": 1234,
            "method": "get",
            "resource": "/test__dispatch_message",
            "sign": ["test"],
            "data": {
                "test": "OK"
            }
        })
        with patch.object(self.test_model, "req_queue") as req_queue:
            self.test_model.on_sanji_message(None, None, message)
            req_queue.put.assert_called_once_with(ANY)

        # Response
        message2 = MyMessage({
            "id": 1234,
            "code": 200,
            "method": "get",
            "resource": "/test__dispatch_message",
            "sign": ["test"],
            "data": {
                "test": "OK"
            }
        })
        with patch.object(self.test_model, "res_queue") as res_queue:
            self.test_model.on_sanji_message(None, None, message2)
            res_queue.put.assert_called_once_with(ANY)

        # Non-JSON String message
        message = MyMessage(None)
        self.test_model.on_sanji_message(None, None, message)
        with self.assertRaises(Empty):
            self.test_model.req_queue.get(timeout=0.001)

        # UNKNOW TYPE message
        message = MyMessage("{}")
        self.test_model.on_sanji_message(None, None, message)
        with self.assertRaises(Empty):
            self.test_model.req_queue.get(timeout=0.001)

    def test__dispatch_message(self):  # noqa
        resp = Mock()
        self.test_model.publish.create_response = Mock(return_value=resp)

        # case 1: not found
        with patch.object(self.test_model.router, "dispatch") as dispatch:
            dispatch.return_value = []
            m = Message({"resource": "/"})
            self.test_model._Sanji__dispatch_message(m)
            resp.assert_called_once_with(
                code=404, data={"message": ANY})

        # case 2: normal
        def cb(self, message, response):
            response(code=200, data=message.to_dict())

        resp.reset_mock()
        with patch.object(self.test_model.router, "dispatch") as dispatch:
            dispatch.return_value = [{
                "handlers": [{
                    "callback": cb,
                    "method": "put",
                    "reentrant": False,
                    "schema": None
                }],
                "message": Message({})
            }]
            self.test_model._Sanji__dispatch_message(None)
            resp.assert_called_once_with(code=200, data={})

        # case 3: internal error
            resp.reset_mock()
            dispatch.return_value = [{
                "handlers": [{
                    "callback": Mock(side_effect=Exception("TEST"))
                }],
                "message": Message({})
            }]
            self.test_model._Sanji__dispatch_message(None)
            resp.assert_called_once_with(code=500,
                                         data={"message": "Internal Error."})

        # case 4: schema
            resp.reset_mock()
            schema = Schema({
                Required('q'): All(str, Length(min=1)),
                Required('per_page', default=5): All(
                    int, Range(min=1, max=20)),
                'page': All(int, Range(min=0)),
            })

            def schema_cb(self, message, response):
                response(code=200, data=message.to_dict())

            m = Message({
                "data": {
                    "q": "abc",
                    "per_page": 5,
                    "page": 12
                }
            })
            dispatch.return_value = [{
                "handlers": [{
                    "callback": schema_cb,
                    "schema": schema
                }],
                "message": m
            }]
            self.test_model._Sanji__dispatch_message(None)
            resp.assert_called_once_with(code=200,
                                         data=m.to_dict())

        # case 5: schema error
            resp.reset_mock()
            m = Message({
                "data": {
                    "q": "abc",
                    "per_page": 5,
                    "page": "12"  # change this to str
                }
            })
            dispatch.return_value = [{
                "handlers": [{
                    "callback": schema_cb,
                    "schema": schema
                }],
                "message": m
            }]
            self.test_model._Sanji__dispatch_message(None)
            resp.assert_called_once_with(
                code=400,
                data={"message":
                      "expected int for dictionary value @ data['page']"})

    def test__resolve_responses(self):
        """ It should put message into req_queue if response is not for me """
        msg = Message({
            "id": 3456,
            "code": 200,
            "method": "get",
            "resource": "/not_found/12345",
            "sign": ["test"],
            "data": None
        })
        self.test_model.res_queue.put(msg)

        # start dispatch messages
        thread = Thread(target=self.test_model._resolve_responses)
        thread.daemon = True
        thread.start()

        while self.test_model.res_queue.empty() is False:
            pass

        event_msg_ans = Message({
            "code": 200,
            "method": "get",
            "resource": "/not_found/12345",
            "data": None
        }, generate_id=False)
        event_msg = self.test_model.req_queue.get()
        self.assertEqual(event_msg_ans.to_dict(), event_msg.to_dict())
        self.assertEqual(event_msg.type(), MessageType.EVENT)
        self.test_model.res_queue.put(None)
        thread.join()

    def test_register_routes(self):
        def func_maker(name, order):
            def wrapper():
                print(name)
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

    def test_start(self):
        def run():
            self.test_model.stop_event.set()

        self.test_model._create_thread_pool = Mock()
        self.test_model.is_ready.set()
        self.test_model.deregister = Mock(return_value=True)
        self.test_model.register = Mock(return_value=True)
        self.test_model.stop = Mock()
        self.test_model.run = run

    def test_register(self):
        post = Mock()
        set_tunnel = Mock()
        self.test_model.stop = Mock()
        self.test_model.publish.direct.post = post
        self.test_model._conn.set_tunnel = set_tunnel
        # case 1: normal
        with patch("sanji.core.Retry") as Retry:
            Retry.return_value = Message({
                "data": {
                    "tunnel": 1234
                }
            })
            reg_data = {
                "name": "test_register",
                "role": "model",
                "resources": ["/abc"]
            }
            self.test_model.register(reg_data)
            set_tunnel.assert_called_once_with("model", 1234, ANY)

        # case 2: register failed call stop
            Retry.return_value = None
            self.test_model.register(reg_data)
            self.test_model.stop.assert_called_once_with()

    def test_deregister(self):
        name = self.test_model.bundle.profile["name"]
        reg_data = {
            "name": name,
            "role": "model",
            "resources": ["/abc"]
        }

        self.test_model._conn.tunnels["view"] = "view_tunnel"
        self.test_model._conn.tunnels["model"] = "model_tunnel"
        with patch("sanji.core.Retry") as Retry:
            Retry.return_value = None
            retry = False
            timeout = 2
            interval = 1
            self.test_model.deregister(
                reg_data=reg_data, retry=retry,
                interval=interval, timeout=timeout)
            Retry.assert_called_once_with(
                target=self.test_model.publish.direct.delete,
                args=("/controller/registration", reg_data,),
                kwargs={"timeout": timeout},
                options={"retry": retry, "interval": interval})

    def test_get_profile_model(self):
        """
        TODO: needs final controller registration spec to vaild this output
        """
        profile = self.test_model.get_profile()
        for resource in profile["resources"]:
            self.assertEquals(resource.find(":"), -1)
        self.assertEqual(len(profile["resources"]), 3)

    def test_get_profile_view(self):
        profile = self.test_model.get_profile(role="view")
        for resource in profile["resources"]:
            self.assertEquals(resource.find(":"), -1)
        self.assertEqual(len(profile["resources"]), 1)

    def test_exit(self):
        with self.assertRaises(SystemExit):
            self.test_model.exit()

    def test__create_thread_pool(self):
        self.test_model._create_thread_pool()
        self.assertEqual(self.test_model.dispatch_thread_count +
                         self.test_model.resolve_thread_count,
                         len(self.test_model.thread_list))

if __name__ == "__main__":
    FORMAT = '%(asctime)s - %(levelname)s - %(lineno)s - %(message)s'
    logging.basicConfig(level=20, format=FORMAT)
    logger = logging.getLogger('test')
    unittest.main()
