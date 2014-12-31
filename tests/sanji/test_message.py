from __future__ import print_function

import json
import sys
import os

if sys.version_info >= (2, 7):
    import unittest
else:
    import unittest2 as unittest

try:
    sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../../')
    from sanji.message import Message
    from sanji.message import MessageType
    from sanji.message import parse_querystring
    from sanji.message import trim_resource
    from sanji.router import Route
except ImportError:
    print("Please check the python PATH for import test module. (%s)"
          % __file__)
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
            self.assertEqual(trim_resource(testcase["uri"]),
                             testcase["trimUri"])

    def test_parse_querystring(self):
        self.assertEqual(
            parse_querystring("="),
            {}
        )

        self.assertEqual(
            parse_querystring("abc=456&abc=789"),
            {'abc': ['456', '789']}
        )

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


class TestMessageClass(unittest.TestCase):
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

        sanjimsg = Message(msg)
        self.assertEqual(sanjimsg.type(), MessageType.REQUEST)

    def test_response_msg(self):
        msg = {
            "id": 123124,
            "code": 200,
            "resource": "/network/cellular/1",
            "method": "get",
            "sign": ["test"],
            "data": {}
        }

        sanjimsg = Message(msg)
        self.assertEqual(sanjimsg.type(), MessageType.RESPONSE)

    def test_direct_msg(self):
        msg = {
            "id": 123124,
            "resource": "/network/cellular/1",
            "method": "get",
            "tunnel": "asdf",
            "data": {}
        }

        sanjimsg = Message(msg)
        self.assertEqual(sanjimsg.type(), MessageType.DIRECT)

    def test_event_msg(self):
        msg = {
            "code": 200,
            "resource": "/network/cellular/1",
            "method": "get",
            "data": {}
        }

        sanjimsg = Message(msg)
        self.assertEqual(sanjimsg.type(), MessageType.EVENT)

    def test_hook_msg(self):
        msg = {
            "id": 123124,
            "resource": "/network/cellular/1",
            "method": "get",
            "sign": ["abc", "def"],
            "data": {}
        }

        sanjimsg = Message(msg)
        self.assertEqual(sanjimsg.type(), MessageType.HOOK)

    def test_unknow_msg(self):
        msg = {
            "id": 123124,
            "resource": "/network/cellular/1",
            "method": "get",
            "sign": ["abc", "def"],
            "tunnel": "123",
            "data": {}
        }

        sanjimsg = Message(msg)
        self.assertEqual(sanjimsg.type(), MessageType.UNKNOWN)

        msg = {
            "resource": "/network/cellular/1",
            "method": "get",
            "sign": ["abc", "def"],
            "tunnel": "123",
            "data": {}
        }

        sanjimsg = Message(msg)
        self.assertEqual(sanjimsg.type(), MessageType.UNKNOWN)

        msg = {
            "method": "get",
            "sign": ["abc", "def"],
            "tunnel": "123",
        }

        sanjimsg = Message(msg)
        self.assertEqual(sanjimsg.type(), MessageType.UNKNOWN)

        msg = {
            "method": "get",
            "sign": ["abc", "def"],
        }

        sanjimsg = Message(msg)
        self.assertEqual(sanjimsg.type(), MessageType.UNKNOWN)

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
            "query": {"abc": "123"},
            "id": 123,
            "param":
            {"id": "123"},
            "method": "get"
        }

        sanjimsg = Message(msg)
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
            "query": {},
            "id": 123,
            "param":
            {"id": "123"},
            "method": "get"
        }

        sanjimsg = Message(msg)
        route = Route("/model/:id")
        route.get(get)
        self.assertEqual(sanjimsg.match(route).__dict__, matched_msg)

        msg = {
            "id": 123,
            "method": "get",
            "resource": "/model"
        }

        matched_msg = {
            "_type": 2,
            "resource": "/model",
            "query": {},
            "id": 123,
            "param": {},
            "method": "get"
        }

        sanjimsg = Message(msg)
        route = Route("/model")
        route.get(get)
        self.assertEqual(sanjimsg.match(route).__dict__, matched_msg)

    def test_generate_id(self):
        msg = Message({})
        msg_id = msg.generate_id()
        self.assertEqual(msg.id, msg_id)
        self.assertTrue(msg.id < 65535)
        self.assertTrue(msg.id > 0)

    def test_init(self):
        msg = Message({
            "method": "get",
            "resource": "/model/123"
        }, generate_id=True)

        self.assertGreater(msg.id, 0)
        self.assertLess(msg.id, 65535)
        self.assertEqual(msg.type(), MessageType.REQUEST)

        msg_noid = Message({
            "method": "get",
            "resource": "/model/123"
        })
        self.assertEqual(msg_noid.type(), MessageType.UNKNOWN)

        with self.assertRaises(ValueError):
            Message("{")

        with self.assertRaises(TypeError):
            Message(123)

    def test_to_dict(self):
        msg = Message({})
        for prop in msg.to_dict():
            self.assertNotEqual(prop.find("_"), 0)

    def test_to_json(self):
        msg = Message({})
        for prop in json.loads(msg.to_json()):
            self.assertNotEqual(prop.find("_"), 0)
        for prop in json.loads(msg.to_json(pretty=False)):
            self.assertNotEqual(prop.find("_"), 0)


if __name__ == "__main__":
    unittest.main()
