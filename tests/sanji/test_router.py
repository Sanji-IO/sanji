from __future__ import print_function

import sys
import os

from mock import Mock

if sys.version_info >= (2, 7):
    import unittest
else:
    import unittest2 as unittest

try:
    sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../../')
    import sanji.router as router
    from sanji.message import Message
except ImportError:
    print("Please check the python PATH for import test module. (%s)"
          % __file__)
    exit(1)


class TestFunctions(unittest.TestCase):

    def test_compile_resource(self):
        self.assertEqual(
            router.compile_resource('/abc/:id').pattern,
            "^abc/(?P<id>[\w-]+?)(\?(?P<querystring>.*))?$"
        )

        self.assertEqual(
            router.compile_resource('/abc/:id').pattern,
            router.compile_resource('/abc/:id/').pattern
        )


class TestRouteClass(unittest.TestCase):

    def setUp(self):
        self.route = router.Route('/test/resource/:id')

    def tearDown(self):
        self.route = None

    def test_init(self):
        self.assertTrue(hasattr(self.route.get, "__call__"))
        self.assertTrue(hasattr(self.route.post, "__call__"))
        self.assertTrue(hasattr(self.route.put, "__call__"))
        self.assertTrue(hasattr(self.route.delete, "__call__"))
        self.assertTrue(hasattr(self.route.all, "__call__"))
        self.assertEqual(len(self.route.handlers), 0)

        def callback1():
            print("I am test callback1")

        def callback2():
            print("I am test callback2")

        self.route.get(callback1)
        self.assertEqual(self.route.handlers[0]['method'], "get")
        self.assertEqual(self.route.handlers[0]['callback'], callback1)
        self.route.post(callback2)
        self.assertEqual(self.route.handlers[1]['method'], "post")
        self.assertEqual(self.route.handlers[1]['callback'], callback2)
        self.route.put(callback1)
        self.assertEqual(self.route.handlers[2]['method'], "put")
        self.assertEqual(self.route.handlers[2]['callback'], callback1)
        self.route.delete(callback2)
        self.assertEqual(self.route.handlers[3]['method'], "delete")
        self.assertEqual(self.route.handlers[3]['callback'], callback2)

    def test_create_handler_func(self):
        func = self.route.create_handler_func("get")
        self.assertTrue(hasattr(func, "__call__"))

        def callback():
            print("test callback")
        func(callback)

        self.assertEqual(len(self.route.handlers), 1)
        self.assertEqual(self.route.handlers[0]['method'], "get")
        self.assertEqual(self.route.handlers[0]['callback'], callback)

    def test_dispatch(self):
        request = dict(
            resource="/test/resource/123",
            method="get",
            data=dict()
        )

        def callback(req):
            print(req)

        self.route.get(callback)
        message = Message(request)
        self.assertEqual(len(self.route.dispatch(message)), 1)

    def test_get_methods(self):
        def func():
            pass

        self.route.get(func)
        self.route.post(func)
        self.route.delete(func)
        self.route.delete(func)
        methods = self.route.get_methods()
        self.assertEqual(len(methods), 3)
        self.assertIn('post', methods)
        self.assertIn('get', methods)
        self.assertIn('delete', methods)
        self.assertNotIn('put', methods)


class TestRouterClass(unittest.TestCase):
    def setUp(self):
        self.router = router.Router()

    def tearDown(self):
        self.router = None

    def test_init(self):
        self.assertTrue(hasattr(self.router.get, "__call__"))
        self.assertTrue(hasattr(self.router.post, "__call__"))
        self.assertTrue(hasattr(self.router.put, "__call__"))
        self.assertTrue(hasattr(self.router.delete, "__call__"))
        self.assertTrue(hasattr(self.router.all, "__call__"))
        self.assertEqual(len(self.router.routes), 0)

        def callback1():
            print("I am test callback1")

        def callback2():
            print("I am test callback2")

    def test_dispatch(self):
        request = {
            "id": 3345678,
            "resource": "/test/resource/112?aaa=bbb",
            "method": "get",
            "data": {}
        }

        # case 1: normal
        callback = Mock(return_value="case1")
        self.router.post("/test/resource", callback)
        request["resource"] = "/test/resource/"
        request["method"] = "post"
        result = self.router.dispatch(Message(request))
        self.assertEqual(1, len(result))
        self.assertEqual(1, len(result[0]["handlers"]))
        self.assertEqual(result[0]["handlers"][0]["callback"](), "case1")
        callback.assert_called_once_with()

        # case 2: using route method
        callback2 = Mock(return_value="case2")
        self.router.route("/test/dunplicate").post(callback2)
        self.router.route("/test/dunplicate/:id").post(callback2)
        request["resource"] = "/test/dunplicate/1234"
        result = self.router.dispatch(Message(request))
        self.assertEqual(1, len(result))
        self.assertEqual(1, len(result[0]["handlers"]))
        self.assertEqual(result[0]["handlers"][0]["callback"](), "case2")
        callback2.assert_called_once_with()

        # case 3: not found
        request = {
            "id": 698978,
            "resource": "/test/resource/",
            "method": "get",
            "data": {}
        }
        result = self.router.dispatch(Message(request))
        self.assertEqual(0, len(result))

    def test_dispatch_multi_params(self):
        request = {
            "id": 3345678,
            "resource": "/multi_params/1_1/2-2",
            "method": "post",
            "data": {}
        }
        callback = Mock(return_value="test_dispatch_multi_params")
        self.router.route("/multi_params/:id/:u_id").post(callback)
        result = self.router.dispatch(Message(request))
        self.assertEqual(1, len(result))

    def test_get_routes(self):
        def func():
            pass
        self.router.post("/test/resource/", func)
        self.router.route("/test/resource/:id") \
            .get(func) \
            .post(func) \
            .delete(func) \
            .put(func)

        routes = self.router.get_routes()

        self.assertIn("/test/resource/", routes)
        methods = routes["/test/resource/"]
        self.assertIn('post', methods)

        self.assertIn("/test/resource/:id", routes)
        methods = routes["/test/resource/:id"]
        self.assertIn('get', methods)
        self.assertIn('post', methods)
        self.assertIn('delete', methods)
        self.assertIn('put', methods)


if __name__ == "__main__":
    unittest.main()
