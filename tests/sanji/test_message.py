import unittest
import sys
import os

try:
    sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../../sanji')
    from message import SanjiMessage
    from message import SanjiMessageType
    from message import parse_querystring
    from message import trim_resource
    from router import Route
except ImportError:
    print "Please check the python PATH for import test module."
    exit(1)

class TestFunctions(unittest.TestCase):

    def test_trim_resource(self):
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
            self.assertEqual(trim_resource(testcase["uri"]), testcase["trimUri"])

    def test_parse_querystring(self):
        self.assertEqual(
            parse_querystring("abc=123&cde=456"),
            {'abc': '123', 'cde': '456'}
        )

        self.assertEqual(
            parse_querystring("abc=123&&&&cde=456"),
            {'abc': '123', 'cde': '456'}
        )

        self.assertEqual(
            parse_querystring("&&&&abc=123&&&&cde=456&&&&&async"),
            {'abc': '123', 'cde': '456', 'async': True}
        )

        self.assertEqual(
            parse_querystring("&&&&abc=123&&&&cde=456&&&&&async=false"),
            {'abc': '123', 'cde': '456', 'async': 'false'}
        )

class TestSanjiMessageClass(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_request_msg(self):
        msg = {
            "id": 123124,
            "resource": "/network/cellular/1",
            "method": "get",
            "data": {}
        }

        sanjimsg = SanjiMessage(msg)
        self.assertEqual(sanjimsg.type(), SanjiMessageType.REQUEST)

    def test_response_msg(self):
        msg = {
            "id": 123124,
            "code": 200,
            "resource": "/network/cellular/1",
            "method": "get",
            "data": {}
        }

        sanjimsg = SanjiMessage(msg)
        self.assertEqual(sanjimsg.type(), SanjiMessageType.RESPONSE)

    def test_direct_msg(self):
        msg = {
            "id": 123124,
            "resource": "/network/cellular/1",
            "method": "get",
            "tunnel": "asdf",
            "data": {}
        }

        sanjimsg = SanjiMessage(msg)
        self.assertEqual(sanjimsg.type(), SanjiMessageType.DIRECT)

    def test_event_msg(self):
        msg = {
            "code": 200,
            "resource": "/network/cellular/1",
            "method": "get",
            "data": {}
        }

        sanjimsg = SanjiMessage(msg)
        self.assertEqual(sanjimsg.type(), SanjiMessageType.EVENT)

    def test_hook_msg(self):
        msg = {
            "id": 123124,
            "resource": "/network/cellular/1",
            "method": "get",
            "sign": ["abc", "def"],
            "data": {}
        }

        sanjimsg = SanjiMessage(msg)
        self.assertEqual(sanjimsg.type(), SanjiMessageType.HOOK)

    def test_unknow_msg(self):
        msg = {
            "id": 123124,
            "resource": "/network/cellular/1",
            "method": "get",
            "sign": ["abc", "def"],
            "tunnel": "123",
            "data": {}
        }

        sanjimsg = SanjiMessage(msg)
        self.assertEqual(sanjimsg.type(), SanjiMessageType.UNKNOWN)

        msg = {
            "resource": "/network/cellular/1",
            "method": "get",
            "sign": ["abc", "def"],
            "tunnel": "123",
            "data": {}
        }

        sanjimsg = SanjiMessage(msg)
        self.assertEqual(sanjimsg.type(), SanjiMessageType.UNKNOWN)

        msg = {
            "method": "get",
            "sign": ["abc", "def"],
            "tunnel": "123",
        }

        sanjimsg = SanjiMessage(msg)
        self.assertEqual(sanjimsg.type(), SanjiMessageType.UNKNOWN)

        msg = {
            "method": "get",
            "sign": ["abc", "def"],
        }

        sanjimsg = SanjiMessage(msg)
        self.assertEqual(sanjimsg.type(), SanjiMessageType.UNKNOWN)

    def test_match(self):
        def get(self):
            pass

        msg = {
            "id": 123,
            "method": "get",
            "resource": "/model/123?abc=123"
        }

        matched_msg = {
            "_type": 2,
            "resource": "/model/123?abc=123",
            "_resource": "model/123?abc=123",
            "query": {"abc": "123"},
            "id": 123,
            "param": 
                {"id": "123"},
            "method": "get"
        }

        sanjimsg = SanjiMessage(msg)
        route = Route("/model/:id")
        route.get(get)
        self.assertEqual(sanjimsg.match(route).__dict__, matched_msg)

        msg = {
            "id": 123,
            "method": "get",
            "resource": "/model/123"
        }

        matched_msg = {
            "_type": 2,
            "resource": "/model/123",
            "_resource": "model/123",
            "query": {},
            "id": 123,
            "param": 
                {"id": "123"},
            "method": "get"
        }

        sanjimsg = SanjiMessage(msg)
        route = Route("/model/:id")
        route.get(get)
        self.assertEqual(sanjimsg.match(route).__dict__, matched_msg)

    def test_generate_id(self):
        msg = SanjiMessage({})
        msg_id = msg.generate_id()
        self.assertEqual(msg.id, msg_id)
        self.assertTrue(msg.id < 100000)
        self.assertTrue(msg.id > 0)

if __name__ == "__main__":
    unittest.main()
