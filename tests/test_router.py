import unittest

try:
    sys.path.append('../src')
    import router
except ImportError as e:
    print "Please check the python PATH for import test module."
    exit(1)


class TestFunctions(unittest.TestCase):

    def test_trim_uri(self):
        uris = [
            dict(uri="/api/v1/test", trimUri="api/v1/test"),
            dict(uri="/api/v1/test/", trimUri="api/v1/test"),
            dict(uri="////api/v1/test////", trimUri="api/v1/test"),
            dict(uri="////api/v1/test", trimUri="api/v1/test"),
            dict(uri="api/v1/test/", trimUri="api/v1/test"),
            dict(uri="api/v1/test//////", trimUri="api/v1/test"),
            dict(uri="test", trimUri="test"),
            dict(uri="//test/", trimUri="test"),
            dict(uri="/test", trimUri="test")
        ]

        for testcase in uris:
            self.assertEqual(router.trim_uri(testcase["uri"]), testcase["trimUri"])

    def test_parse_querystring(self):
        self.assertEqual(
            router.parse_querystring("abc=123&cde=456"),
            {'abc': '123', 'cde': '456'}
        )

        self.assertEqual(
            router.parse_querystring("abc=123&&&&cde=456"),
            {'abc': '123', 'cde': '456'}
        )

        self.assertEqual(
            router.parse_querystring("&&&&abc=123&&&&cde=456&&&&&async"),
            {'abc': '123', 'cde': '456', 'async': True}
        )

        self.assertEqual(
            router.parse_querystring("&&&&abc=123&&&&cde=456&&&&&async=false"),
            {'abc': '123', 'cde': '456', 'async': 'false'}
        )

    def test_compile_uri(self):
        self.assertEqual(
            router.compile_uri('/abc/:id').pattern,
            "^abc/(?P<id>\w+?)(\?(?P<querystring>.*))?$"
        )

        self.assertEqual(
            router.compile_uri('/abc/:id').pattern,
            router.compile_uri('/abc/:id/').pattern
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
        self.assertEqual(len(self.route.dispatch(request)), 1)
        self.route.dispatch(request)[0](request)


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

        self.router.get("/test/resource/:id", callback1)
        route = router.Route("/test/resource/:id").get(callback1)
        self.assertItemsEqual(self.router.routes[0].handlers, route.handlers)

        self.router.post("/test/resource/:id", callback1)
        route = router.Route("/test/resource/:id").post(callback1)
        self.assertItemsEqual(self.router.routes[1].handlers, route.handlers)

        self.router.put("/test/resource/:id", callback1)
        route = router.Route("/test/resource/:id").put(callback1)
        self.assertItemsEqual(self.router.routes[2].handlers, route.handlers)

        self.router.delete("/test/resource/:id", callback1)
        route = router.Route("/test/resource/:id").delete(callback1)
        self.assertItemsEqual(self.router.routes[3].handlers, route.handlers)

    def test_dispatch(self):
        request = {
            "resource": "/test/resource/112?aaa=bbb",
            "method": "get",
            "data": {}
        }

        request_data = {
            "uri": "test/resource/112?aaa=bbb",
            "method": "get",
            "param": {
                "id": "112",
                "querystring": "aaa=bbb"
            },
            "query": {
                "aaa": "bbb"
            },
            "data": {}
        }

        response = "fake response mock"

        def callback(method):
            def _cb(req, res):
                print "[%s] callback!" % method
                request_data["method"] = method
                self.assertEqual(req, request_data)
                self.assertEqual(res, response)

            return _cb


        for times in range(1, 3):
            self.router.post("/test/resource/", callback("post"))
            self.router.route("/test/resource/:id") \
                .get(callback("get")) \
                .post(callback("post")) \
                .delete(callback("delete")) \
                .put(callback("put"))

            for method in ["get", "post", "delete", "put"]:
                request["method"] = method
                request_data["method"] = method
                dispatch_result = self.router.dispatch(request)

                self.assertEqual(len(dispatch_result[0]["callbacks"]), 1)
                self.assertEqual(len(dispatch_result), times)
                self.assertEqual(dispatch_result[0]['req'], request_data)

        # test dispatch threading

if __name__ == "__main__":
    unittest.main()