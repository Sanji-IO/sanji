import os
import sys
import json
import unittest
from time import sleep
from threading import Thread

try:
    sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../../')
    from sanji.publish import Publish
    from sanji.session import Session
    from sanji.session import TimeoutError
    from sanji.session import StatusError
    from sanji.message import SanjiMessage
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

        def on_publish(self, mid):
            pass
            # this.assertIn(mid, mids)

        def on_message(self, message):
            msg = json.loads(message)
            if this.index == 0:
                this.assertEqual("get", msg["payload"]["method"])
            elif this.index == 1:
                this.assertEqual("put", msg["payload"]["method"])
                this.assertEqual({"test": "nice"}, msg["payload"]["data"])
            elif this.index == 2:
                this.assertEqual("post", msg["payload"]["method"])
                this.assertEqual({"test": "good"}, msg["payload"]["data"])
            elif this.index == 3:
                this.assertEqual("delete", msg["payload"]["method"])
                this.assertEqual({"test": "ok"}, msg["payload"]["data"])

            this.index = this.index + 1
            if this.index == 4:
                this.conn.disconnect()

        self.conn.set_on_message(on_message)
        self.conn.set_on_publish(on_publish)

        # CRUD - non block
        mids.append(this.publish.get("/test/resource", block=False))
        mids.append(this.publish.put("/test/resource", {"test": "nice"},
                    block=False))
        mids.append(this.publish.post("/test/resource", {"test": "good"},
                    block=False))
        mids.append(this.publish.delete("/test/resource", {"test": "ok"},
                    block=False))

        # CRUD - non block fire
        self.conn.connect()

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

        message = SanjiMessage({"test": "block"}, generate_id=True)
        thread = Thread(target=send_block, args=(message, "block",))
        thread.daemon = True
        thread.start()
        sleep(0.1)
        self.session.resolve(message.id, "block")
        thread.join()

        # CRUD - block timeout
        message = SanjiMessage({"test": "timeout"}, generate_id=True)
        thread = Thread(target=send_timeout, args=(message, "timeout",))
        thread.daemon = True
        thread.start()
        sleep(0.1)
        # self.session.resolve(message.id, 1)
        thread.join()

        # Resolve StatusError
        message = SanjiMessage({"test": "StatusError"}, generate_id=True)
        thread = Thread(target=resolve_statuserror, args=(message,))
        thread.daemon = True
        thread.start()
        sleep(0.1)
        self.session.resolve(message.id, 1, 123)
        thread.join()

    def test_event(self):
        this = self
        sent_mid = None

        def on_publish(self, mid):
            this.assertEqual(sent_mid, mid)

        def on_message(self, message):
            msg = json.loads(message)
            this.assertEqual("post", msg["payload"]["method"])
            this.assertEqual({"type": "notify", "message": "hi"},
                             msg["payload"]["data"])
            this.conn.disconnect()

        self.conn.set_on_publish(on_publish)
        self.conn.set_on_message(on_message)
        sent_mid = self.publish.event("/test/event",
                                      {"type": "notify", "message": "hi"})
        self.conn.connect()

    def test_direct(self):
        self.publish.direct(None, None)

    def test_response(self):
        func = self.publish.response(None)
        func()

if __name__ == "__main__":
    unittest.main()
