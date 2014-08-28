__test__ = False

import os
import sys
import unittest
from time import sleep
from Queue import Queue
from threading import Thread
# from threading import Lock

try:
    sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../../')
    from sanji.session import Session
    from sanji.message import Message
    from sanji.session import Status
except ImportError:
    print "Please check the python PATH for import test module. (%s)" \
        % __file__
    exit(1)


class TestSessionClass(unittest.TestCase):

    def setUp(self):
        self.session = Session()

    def tearDown(self):
        self.session.stop()
        self.session = None

    def test_init(self):
        self.assertIsInstance(self.session.session_list, dict)
        # self.assertIsInstance(self.session.session_lock, Lock)
        self.assertIsInstance(self.session.timeout_queue, Queue)
        self.assertIsInstance(self.session.thread_aging, Thread)

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

        # create session as normal
        self.session.create(message1)
        self.assertEqual(self.session.session_list[message1.id]["message"],
                         message1)
        # id duplicate
        message2.id = message1.id
        self.assertEqual(self.session.create(message2), None)

        # aging should be test too
        sleep(1)
        self.assertLess(self.session.session_list[message1.id]["age"], 60)

    def test_stop(self):
        self.session.stop()
        self.assertFalse(self.session.thread_aging.is_alive())

    def test_aging(self):
        message1 = Message({}, generate_id=True)
        self.session.create(message1, age=0)
        sleep(1)
        self.assertFalse(self.session.timeout_queue.empty())


if __name__ == "__main__":
    unittest.main()
