import os
import sys
import unittest
from time import sleep
from threading import Thread

try:
    sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../../')
    from sanji.publish import Publish
    from sanji.session import Session
    from sanji.session import TimeoutError
    from sanji.session import StatusError
    from sanji.session import Status
    from sanji.message import Message
    from connection_mockup import ConnectionMockup
except ImportError:
    print "Please check the python PATH for import test module. (%s)" \
        % __file__
    exit(1)


class TestPublishClass(unittest.TestCase):

    def setUp(self):
        self.conn = ConnectionMockup()
        self.session = Session()
        self.publish = Publish(self.conn, self.session)

    def tearDown(self):
        self.session.stop()
        self.conn = None
        self.session = None
        self.publish = None

    def test_crud(self):  # noqa
        this = self
        mids = []
        this.index = 0

        def send(method, resouce, data, block):
            mids.append(this.publish.__getattribute__(method)
                        (resouce, data, block=block))

        threads = []
        for method in ["get", "put", "post", "delete"]:
            thread = Thread(target=send, args=(
                method, "/test/resource", {"test": method}, False))
            thread.daemon = True
            thread.start()
            threads.append(thread)
        sleep(0.5)
        for session in self.session.session_list.itervalues():
            session["status"] = Status.SENT
            session["is_resolved"].set()
            session["is_published"].set()

        for thread in threads:
            thread.join(1)
            self.assertFalse(thread.is_alive())

        # CRUD - block
        def send_block(message, data):
            self.assertEqual(self.publish.get("/test/resource", message),
                             data)

        def send_timeout(message, data):
            with self.assertRaises(TimeoutError):
                print self.publish.put("/test/resource", message, timeout=0)
            with self.assertRaises(TimeoutError):
                self.publish.delete("/test/resource", message, timeout=-1)

        def resolve_statuserror(message):
            with self.assertRaises(StatusError):
                self.publish.put("/", message, timeout=10)

        message = Message({"test": "block"}, generate_id=True)
        thread = Thread(target=send_block, args=(message, "block",))
        thread.daemon = True
        thread.start()
        sleep(0.1)
        self.session.resolve(message.id, "block")
        thread.join(1)
        self.assertFalse(thread.is_alive())

        # CRUD - block timeout
        message = Message({"test": "timeout"}, generate_id=True)
        thread = Thread(target=send_timeout, args=(message, "timeout",))
        thread.daemon = True
        thread.start()
        sleep(0.1)
        # self.session.resolve(message.id, 1)
        thread.join(1)
        self.assertFalse(thread.is_alive())

        # Resolve StatusError
        message = Message({"test": "StatusError"}, generate_id=True)
        thread = Thread(target=resolve_statuserror, args=(message,))
        thread.daemon = True
        thread.start()
        sleep(0.1)
        self.session.resolve(message.id, 1, 123)
        thread.join(1)
        self.assertFalse(thread.is_alive())

    def test_event(self):
        # Resolve StatusError
        def send_block():
            self.publish.event("/test/event2",
                               {"type": "notify2", "message": "hi"})
        thread = Thread(target=send_block, args=())
        thread.daemon = True
        thread.start()
        sleep(0.5)
        self.assertEqual(len(self.session.session_list), 1)
        for session in self.session.session_list.itervalues():
            self.session.resolve_send(session["mid"])
        thread.join(0.5)
        self.assertFalse(thread.is_alive())
        self.assertEqual(len(self.session.session_list), 0)

    def test_direct(self):

        def send_nonblock():
            session = self.publish.direct.get("/test/direct1", {
                                              "type": "direct1",
                                              "message": "hi"},
                                              block=False)
            self.session.resolve(session["message"].id, None)
        thread = Thread(target=send_nonblock, args=())
        thread.daemon = True
        thread.start()
        sleep(0.5)
        self.assertEqual(len(self.session.session_list), 1)
        for session in self.session.session_list.itervalues():
            session["status"] = Status.SENT
            session["is_published"].set()
        thread.join(0.5)
        self.assertFalse(thread.is_alive())

        def send_block():
            self.publish.direct.get("/test/direct2",
                                    {"type": "direct2", "message": "hi"},
                                    block=True)
        thread = Thread(target=send_block, args=())
        thread.daemon = True
        thread.start()
        sleep(0.5)
        self.assertEqual(len(self.session.session_list), 1)
        session = self.session.session_list.values()[0]
        self.session.resolve(session["message"].id, session["mid"])
        thread.join(0.5)
        self.assertFalse(thread.is_alive())

    def test_create_response(self):
        messages = [
            Message({"test": "block"}, generate_id=True),
            Message({"sign": ["controller"]}, generate_id=True)
        ]

        def send_block(msg):
            response = self.publish.create_response(msg)
            response(500, {"ccc": "moxa best"})

        threads = []
        for message in messages:
            thread = Thread(target=send_block, args=(message,))
            thread.daemon = True
            thread.start()
            threads.append(thread)
        map(lambda t: t.join(0.1), threads)

        self.assertEqual(len(self.session.session_list), len(messages))
        for session in self.session.session_list.itervalues():
            session["status"] = Status.SENT
            session["is_published"].set()

        for thread in threads:
            thread.join(0.5)
            self.assertFalse(thread.is_alive())

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
