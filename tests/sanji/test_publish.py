#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from __future__ import print_function

from mock import patch
from mock import Mock
from mock import ANY
import os
import sys

if sys.version_info >= (2, 7):
    import unittest
else:
    import unittest2 as unittest

try:
    sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../../')
    from sanji.publish import Publish
    from sanji.publish import Retry
    from sanji.session import Session
    from sanji.session import TimeoutError
    from sanji.session import StatusError
    from sanji.session import Status
    from sanji.message import Message
    from sanji.connection.mockup import Mockup
except ImportError:
    print("Please check the python PATH for import test module. (%s)"
          % __file__)
    exit(1)


class TestFunctionClass(unittest.TestCase):

    def test_retry(self):
        # case 1: timeout
        def target():
            raise TimeoutError
        Retry(target=target, options={"retry": False, "interval": 0})

        # case 2: normal
        msg = Message({})

        def target2():
            setattr(msg, "code", 200)
            return msg
        res = Retry(target=target2, options={"retry": False, "interval": 0})
        self.assertEqual(res, msg)

        # case 3: retry
        msg = Message({})

        def target2():
            setattr(msg, "code", 500)
            return msg
        res = Retry(target=target2, options={"retry": 3, "interval": 0})
        self.assertEqual(res, None)


class TestPublishClass(unittest.TestCase):

    @patch("sanji.session.Thread")
    def setUp(self, Thread):
        self.conn = Mockup()
        self.session = Session()
        self.publish = Publish(self.conn, self.session)

    def tearDown(self):
        self.session.stop()
        self.conn = None
        self.session = None
        self.publish = None

    def test_crud(self):  # noqa
        self.conn.publish = Mock(return_value=1)
        self.session.create = Mock(return_value={})

        # CRUD: block
        with patch("sanji.publish.Publish._wait_published") as _wait_published:
            _wait_published.return_value = None
            for method in ["get", "put", "post", "delete"]:
                self.publish.__getattribute__(method)("/test/resource",
                                                      {"test": method}, False)
                self.conn.publish.assert_called_once_with(topic="/controller",
                                                          qos=2,
                                                          payload=ANY)
                self.conn.publish.reset_mock()
                self.session.create.assert_called_once_with(ANY, mid=1, age=60)
                self.session.create.reset_mock()

        # CRUD: non-block
        with patch("sanji.publish.Publish._wait_resolved") as _wait_resolved:
            # Normal case
            _wait_resolved.return_value = None
            for method in ["get", "put", "post", "delete"]:
                self.publish.__getattribute__(method)("/test/resource",
                                                      {"test": method}, True)

            # Timeout
            _wait_resolved.side_effect = TimeoutError
            for method in ["get", "put", "post", "delete"]:
                with self.assertRaises(TimeoutError):
                    self.publish.__getattribute__(method)("/test/resource",
                                                          {"test": method},
                                                          True, 0)

            # StatusError
            _wait_resolved.side_effect = StatusError
            for method in ["get", "put", "post", "delete"]:
                with self.assertRaises(StatusError):
                    self.publish.__getattribute__(method)("/test/resource",
                                                          {"test": method},
                                                          True)

    def test_event(self):
        with patch("sanji.publish.Publish._wait_published") as _wait_published:
            _wait_published.return_value = None
            self.publish._conn.publish = Mock()
            self.publish.event.get("/test/event2",
                                   {"type": "notify2", "message": "hi"})
            self.publish._conn.publish.assert_called_once_with(
                topic="/controller", qos=2, payload=ANY)

    def test_direct(self):
        with patch("sanji.publish.Publish._wait_published") as _wait_published:
            _wait_published.return_value = None
            self.publish.direct.get("/test/direct1", {
                                    "type": "direct1",
                                    "message": "hi"},
                                    block=False)
            _wait_published.assert_called_once_with(ANY)

    def test_create_response(self):

        messages = [
            Message({"test": "block"}, generate_id=True),
            Message({"query": {}, "param": {}, "sign": ["controller"]},
                    generate_id=True)
        ]

        def check_message(topic, qos, payload):
            self.assertNotIn("query", payload)
            self.assertNotIn("param", payload)
            self.assertIn("sign", payload)
            self.assertIn("code", payload)
            self.assertIn("this is sign", payload["sign"])

        self.publish._wait_published = Mock(return_value=None)
        self.conn.publish = check_message
        for message in messages:
            resp = self.publish.create_response(message, "this is sign")
            resp(500, {"ccc": "moxa best"})
            self.publish._wait_published.assert_called_once_with(
                ANY, no_response=True)
            self.publish._wait_published.reset_mock()

    def test__create_message(self):
        # input dict
        msg = self.publish._create_message({}, None)
        self.assertIsInstance(msg, Message)
        msg = self.publish._create_message(
            {'method': 'get', 'sign': ['aaa', 'bbb']}, {'test': 1234}
        )
        self.assertEqual(msg.method, 'get')
        self.assertEqual(msg.data['test'], 1234)
        self.assertEqual(msg.sign, ['aaa', 'bbb'])

        # input Messgae
        in_msg = Message({'method': 'post', 'resource': '/test'})
        out_msg = self.publish._create_message(data=in_msg)
        self.assertDictEqual(in_msg.__dict__, out_msg.__dict__)

    def test__wait_resolved(self):
        # RESPONSE_TIMEOUT
        session = self.session.create(Message({}, generate_id=True))
        session["is_resolved"].set()
        session["status"] = Status.RESPONSE_TIMEOUT
        with self.assertRaises(TimeoutError):
            self.publish._wait_resolved(session)

        # RESOLVED
        session = self.session.create(Message({}, generate_id=True))
        session["is_resolved"].set()
        session["status"] = Status.RESOLVED
        session["resolve_message"] = True
        self.assertTrue(self.publish._wait_resolved(session))

        # UNKNOWN
        session = self.session.create(Message({}, generate_id=True))
        session["is_resolved"].set()
        session["status"] = 999
        with self.assertRaises(StatusError):
            self.publish._wait_resolved(session)

    def test__wait_published(self):
        # SEND_TIMEOUT
        session = self.session.create(Message({}, generate_id=True))
        session["status"] = Status.SEND_TIMEOUT
        session["is_published"].set()
        with self.assertRaises(TimeoutError):
            self.publish._wait_published(session)

        # SENT
        session = self.session.create(Message({}, generate_id=True))
        session["status"] = Status.SENT
        session["is_published"].set()
        self.assertDictEqual(self.publish._wait_published(session),
                             session)

        # UNKNOWN
        session = self.session.create(Message({}, generate_id=True))
        session["status"] = 999
        session["is_published"].set()
        with self.assertRaises(StatusError):
            self.publish._wait_published(session)


if __name__ == "__main__":
    unittest.main()
