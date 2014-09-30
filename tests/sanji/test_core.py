#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from Queue import Empty
from Queue import Queue
import os
import sys
from threading import Event
from threading import Thread
import unittest
import logging


try:
    sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../../')
    from sanji.core import Sanji
    from sanji.core import Route
    from sanji.bundle import Bundle
    from sanji.bundle import BundleConfigError
    from sanji.message import Message
    from sanji.session import Status
    from sanji.connection.mockup import Mockup
except ImportError as e:
    print "Please check the python PATH for import test module."
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

    def setUp(self):
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

        thread = Thread(target=tm.start)
        thread.daemon = True
        thread.start()
        thread.join(0.2)
        event.set()

    def test_on_publish(self):
        self.test_model.on_publish(None, None, 1)

    def test_on_message(self):
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
        smessage = Message(message.payload)
        self.test_model.on_message(None, None, message)
        data = self.test_model.req_queue.get()
        self.assertEqual(data.to_dict(), smessage.to_dict())

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
        smessage = Message(message2.payload)
        self.test_model.on_message(None, None, message2)
        data = self.test_model.res_queue.get()
        self.assertEqual(data.to_dict(), smessage.to_dict())

        # Non-JSON String message
        message = MyMessage(None)
        self.test_model.on_message(None, None, message)
        with self.assertRaises(Empty):
            self.test_model.req_queue.get(timeout=0.1)

        # UNKNOW TYPE message
        message = MyMessage("{}")
        self.test_model.on_message(None, None, message)
        with self.assertRaises(Empty):
            self.test_model.req_queue.get(timeout=0.1)

    def test__dispatch_message(self):  # noqa
        self.test_model.conn_thread = Thread(
            target=self.test_model._conn.connect)
        self.test_model.conn_thread.daemon = True
        self.test_model.conn_thread.start()

        queue = Queue()
        this = self
        # message1
        message1 = Message({
            "id": 1234,
            "method": "get",
            "resource": "/test__dispatch_message",
            "data": {
                "test": "OK"
            }
        })

        def create_mock_handler(index):
            def _mock_handler(self, message, response):
                queue.put(index)

            return _mock_handler

        for _ in range(0, 10):
            self.test_model.router.get("/test__dispatch_message",
                                       create_mock_handler(_))

        # message2
        message2 = Message({
            "id": 3456,
            "method": "get",
            "resource": "/test__dispatch_message/12345",
            "data": {
                "test": "OK"
            }
        })

        def mock_handler_2(self, message, response):
            this.assertEqual(12345, int(message.param["id"]))

        self.test_model.router.get("/test__dispatch_message/:id",
                                   mock_handler_2)

        # message3 - Not Found
        message3 = Message({
            "id": 3456,
            "method": "get",
            "resource": "/not_found/12345"
        })

        # put messages in req_queue queue
        self.test_model.req_queue.put(message1)
        self.test_model.req_queue.put(message2)
        self.test_model.req_queue.put(message3)

        # start dispatch messages
        event = Event()
        thread = Thread(target=self.test_model._dispatch_message,
                        args=(event,))
        thread.daemon = True
        thread.start()
        thread.join(0.001)
        # let response onthefly
        for session in self.test_model._session.session_list.itervalues():
            session["status"] = Status.SENT
            session["is_published"].set()

        while self.test_model.req_queue.empty() is False:
            pass

        event.set()
        thread.join()

        # check dispatch sequence
        current_index = -1
        while queue.empty() is False:
            index = queue.get()
            self.assertLess(current_index, index)
            current_index = index

        # check internal error response
        def mock_handler_3(self, message, response):
            raise Exception("Error")

        self.test_model.router.get("/test_broken_response",
                                   mock_handler_3)

        # message4 - Not Found
        message4 = Message({
            "id": 1234,
            "method": "get",
            "resource": "/test_broken_response"
        })
        self.test_model.req_queue.put(message4)
        # start dispatch messages
        event = Event()
        thread = Thread(target=self.test_model._dispatch_message,
                        args=(event,))
        thread.daemon = True
        thread.start()
        thread.join(0.001)
        # let response onthefly
        for session in self.test_model._session.session_list.itervalues():
            session["status"] = Status.SENT
            session["is_published"].set()

        while self.test_model.req_queue.empty() is False:
            pass

        event.set()
        thread.join()

    def test__resolve_responses(self):
        # prepare messages
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
        event = Event()
        thread = Thread(target=self.test_model._resolve_responses,
                        args=(event,))
        thread.daemon = True
        thread.start()

        while self.test_model.res_queue.empty() is False:
            pass

        event.set()
        thread.join()

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

    def test_start(self):
        del_msg = Message({
            "id": 2266,
            "code": 200,
            "method": "post",
            "resource": "/controller/registration",
            "sign": ["controller"]
        })

        msg = Message({
            "id": 2266,
            "code": 200,
            "method": "post",
            "resource": "/controller/registration",
            "sign": ["controller"],
            "data": {
                "tunnel": "good_luck_sanji"
            }
        })
        thread = Thread(target=self.test_model.start)
        thread.daemon = True
        thread.start()
        thread.join(0.001)
        with self.test_model._session.session_lock:
            for msg_id in self.test_model._session.session_list:
                del_msg.id = msg_id
            self.test_model._Sanji__resolve_responses(del_msg)
        thread.join(0.001)
        with self.test_model._session.session_lock:
            for msg_id in self.test_model._session.session_list:
                msg.id = msg_id
            self.test_model._Sanji__resolve_responses(msg)
        self.test_model.stop_event.set()
        thread.join()
        self.assertFalse(thread.is_alive())

    def test_register(self):
        self.test_model.conn_thread = Thread(
            target=self.test_model._conn.connect)
        self.test_model.conn_thread.daemon = True
        self.test_model.conn_thread.start()

        this = self
        # prepare ressponse messages
        msg = Message({
            "id": 1234,
            "code": 200,
            "method": "post",
            "resource": "/controller/registration",
            "sign": ["test"],
            "data": {
                "tunnel": "good_luck_sanji"
            }
        })

        msg_failed = Message({
            "id": 1234,
            "code": 500,
            "method": "post",
            "resource": "/controller/registration",
            "sign": ["test"],
            "data": {}
        })

        reg_data = Message({
            "id": 1234,
            "method": "post",
            "resource": "/controller/registration",
            "name": "test",
            "data": {
                "tunnel": "Temp_tunnel_for_test",
                "description": "This is a model without description.",
                "hook": [],
                "role": "model",
                "resources": [
                    "/network/ethernet",
                    "/network/cellular"
                ]
            }
        })
        # register OK
        thread = Thread(target=self.test_model.register, args=(reg_data,))
        thread.daemon = True
        thread.start()
        thread.join(0.001)
        self.test_model._Sanji__resolve_responses(msg)
        thread.join()
        self.assertFalse(thread.is_alive())

        # register with failed
        thread = Thread(target=self.test_model.register,
                        args=(reg_data, True, 0))
        thread.daemon = True
        thread.start()
        thread.join(0.001)
        self.test_model._Sanji__resolve_responses(msg_failed)
        thread.join(0.001)
        self.test_model._Sanji__resolve_responses(msg)
        thread.join()
        self.assertFalse(thread.is_alive())

        # register with failed
        thread = Thread(target=self.test_model.register,
                        args=(reg_data, False))
        thread.daemon = True
        thread.start()
        thread.join(0.001)
        self.test_model._Sanji__resolve_responses(msg_failed)
        thread.join()
        self.assertFalse(thread.is_alive())

        # register with failed and raise error
        thread = Thread(target=self.test_model.register,
                        args=(reg_data, 2, 0, 0))
        thread.daemon = True
        thread.start()
        thread.join(0.001)
        self.test_model._Sanji__resolve_responses(msg_failed)
        thread.join(0.001)
        self.test_model._Sanji__resolve_responses(msg_failed)
        thread.join(0.001)
        self.test_model._Sanji__resolve_responses(msg_failed)
        thread.join()
        self.assertFalse(thread.is_alive())

        class ThreadTest(Thread):

            def __init__(self, exception_class=False, *args, **kwargs):
                Thread.__init__(self, *args, **kwargs)
                self.run_old = self.run

                def run_except(*args, **kwargs):
                    if exception_class is False:
                        self.run_old(*args, **kwargs)
                        return

                    with this.assertRaises(exception_class):
                        self.run_old(*args, **kwargs)
                self.run = run_except

        # register with failed and raise error
        thread = ThreadTest(target=self.test_model.register,
                            args=(reg_data, "abc"),
                            exception_class=TypeError)
        thread.daemon = True
        thread.start()
        thread.join(0.001)
        self.test_model._Sanji__resolve_responses(msg_failed)
        thread.join()
        self.assertFalse(thread.is_alive())

        # register with failed and raise error
        thread = ThreadTest(target=self.test_model.register,
                            args=(reg_data, 0, 0, 0))
        thread.daemon = True
        thread.start()
        thread.join(0.001)
        self.test_model._Sanji__resolve_responses(msg_failed)
        thread.join()
        self.assertFalse(thread.is_alive())

    def get_profile(self):
        """
        TODO: needs final controller registration spec to vaild this output
        """
        self.test_model.get_model_profile()

    def test_exit(self):
        with self.assertRaises(SystemExit):
            self.test_model.exit()

if __name__ == "__main__":
    FORMAT = '%(asctime)s - %(levelname)s - %(lineno)s - %(message)s'
    logging.basicConfig(level=0, format=FORMAT)
    logger = logging.getLogger('test')
    unittest.main()
