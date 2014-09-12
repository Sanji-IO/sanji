import unittest
import sys
import os

try:
    sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../../')
    import sanji.router as router
    from sanji.message import Message
except ImportError:
    print "Please check the python PATH for import test module. (%s)" \
        % __file__
    exit(1)


class TestFunctions(unittest.TestCase):

    def test_compile_resource(self):
        self.assertEqual(
            router.compile_resource('/abc/:id').pattern,
            "^abc/(?P<id>\w+?)(\?(?P<querystring>.*))?$"
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
            print "I am test callback1"

        def callback2():
            print "I am test callback2"

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
            print "test callback"
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
            print req

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
            print "I am test callback1"

        def callback2():
            print "I am test callback2"

        # self.router.get("/test/resource/:id", callback1)
        # route = router.Route("/test/resource/:id").get(callback1)
        # self.assertItemsEqual(self.router.routes["/test/resource/:id"].handlers, route.handlers)

        # self.router.post("/test/resource/:id", callback1)
        # route = router.Route("/test/resource/:id").post(callback1)
        # self.assertItemsEqual(self.router.routes["/test/resource/:id"].handlers, route.handlers)

        # self.router.put("/test/resource/:id", callback1)
        # route = router.Route("/test/resource/:id").put(callback1)
        # self.assertItemsEqual(self.router.routes["/test/resource/:id"].handlers, route.handlers)

        # self.router.delete("/test/resource/:id", callback1)
        # route = router.Route("/test/resource/:id").delete(callback1)
        # self.assertItemsEqual(self.router.routes["/test/resource/:id"].handlers, route.handlers)

    def test_dispatch(self):
        request = {
            "id": 3345678,
            "resource": "/test/resource/112?aaa=bbb",
            "method": "get",
            "data": {}
        }

        request_data = {
            "uri": "test/resource/112?aaa=bbb",
            "method": "get",
            "param": {
                "id": "112"
            },
            "query": {
                "aaa": "bbb"
            },
            "data": {}
        }

        def callback(method):
            def _cb():
                return method
            return _cb

        # for times in range(1, 3):
        self.router.post("/test/resource/", callback("post_no_id"))
        self.router.route("/test/resource/:id") \
            .get(callback("get")) \
            .post(callback("post")) \
            .delete(callback("delete")) \
            .put(callback("put"))

        for method in ["get", "post", "delete", "put"]:
            request["method"] = method
            request_data["method"] = method
            result = self.router.dispatch(Message(request))
            self.assertEqual(method, result[0]["callbacks"][0]())

        request = {
            "id": 3345678,
            "resource": "/test/resource/",
            "method": "post",
            "data": {}
        }

        result = self.router.dispatch(Message(request))
        self.assertEqual("post_no_id", result[0]["callbacks"][0]())

        request = {
            "id": 698978,
            "resource": "/test/resource/",
            "method": "get",
            "data": {}
        }

        result = self.router.dispatch(Message(request))
        self.assertEqual(0, len(result))
        # test dispatch threading

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
