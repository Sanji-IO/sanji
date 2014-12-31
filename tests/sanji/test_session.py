from __future__ import print_function

import os
import sys
from collections import deque
from mock import Mock
from mock import MagicMock
from mock import patch

if sys.version_info >= (2, 7):
    import unittest
else:
    import unittest2 as unittest

try:
    sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../../')
    from sanji.session import Session
    from sanji.message import Message
    from sanji.session import Status
    from sanji.session import SessionError
except ImportError:
    print("Please check the python PATH for import test module. (%s)"
          % __file__)
    exit(1)


class TestSessionClass(unittest.TestCase):

    @patch("sanji.session.sleep")
    @patch("sanji.session.Thread")
    def setUp(self, Thread, sleep):
        self.thread_mock = Thread.return_value = MagicMock()
        self.thread_mock.is_alive.return_value = True
        self.session = Session()

    def tearDown(self):
        self.session.stop()
        self.session = None

    def test_init(self):
        self.assertIsInstance(self.session.session_list, dict)
        self.assertIsInstance(self.session.timeout_queue, deque)

    def test_resolve(self):
        message1 = Message({}, generate_id=True)
        self.session.create(message1)
        self.assertEqual(self.session.resolve(message1.id)["message"],
                         message1)

        # resolve unknow message
        self.session.resolve(1234)

    def test_resolve_send(self):
        # normal
        message1 = Message({}, generate_id=True)
        self.session.create(message1, mid=1)
        session = self.session.resolve_send(1)
        self.assertEqual(session["message"], message1)
        self.assertEqual(session["status"], Status.SENT)
        # not found
        self.assertEqual(self.session.resolve_send(1234), None)

    def test_create(self):
        message1 = Message({}, generate_id=True)
        message2 = Message({}, generate_id=True)
        message3 = Message({}, generate_id=True)

        # create session as normal
        self.session.create(message1)
        self.assertEqual(self.session.session_list[message1.id]["message"],
                         message1)
        # id duplicate
        message2.id = message1.id
        session = self.session.create(message2)
        self.assertNotEqual(session, None)

        message3.id = message1.id
        with self.assertRaises(SessionError):
            self.session.create(message3, force=False)

    def test_stop_is_alive_false(self):
        self.thread_mock.is_alive.return_value = False
        self.session.stop()
        self.assertFalse(self.session.thread_aging.is_alive())
        self.assertFalse(self.thread_mock.join.called)

    def test_stop_is_alive_true(self):
        self.thread_mock.is_alive.return_value = True
        self.session.stop()
        self.thread_mock.join.assert_called_once_with()

    @patch("sanji.session.sleep")
    def test_aging(self, sleep):
        self.session.stop()

        message1 = Message({}, generate_id=True)

        # timeout (response)
        self.session.create(message1, age=0)
        m = self.session.stop_event = Mock()
        conf = {"is_set.side_effect": [False, True, False, True]}
        m.configure_mock(**conf)
        self.session.aging()

        try:
            self.session.timeout_queue.pop()
        except Exception:
            self.fail("timeout_queue is empty")

        # timeout (send)
        self.session.create(message1, age=0)
        self.session.aging()

        for session in self.session.session_list.itervalues():
            session["is_published"].set()

        try:
            self.session.timeout_queue.pop()
        except Exception:
            self.fail("timeout_queue is empty")


if __name__ == "__main__":
    unittest.main()
