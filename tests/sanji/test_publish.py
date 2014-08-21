import os
import sys
import json
import unittest

try:
    sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../../')
    from sanji.publish import Publish
    from connection_mockup import ConnectionMockup
except ImportError:
    print "Please check the python PATH for import test module. (%s)" \
        % __file__
    exit(1)


class TestPublishClass(unittest.TestCase):

    def setUp(self):
        self.conn = ConnectionMockup()
        self.publish = Publish(self.conn)

    def tearDown(self):
        self.conn = None
        self.publish = None

    def test_crud(self):
        this = self
        mids = []
        this.index = 0

        def on_publish(self, mid):
            this.assertIn(mid, mids)

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

        # CRUD
        mids.append(this.publish.get("/test/resource", block=False))
        mids.append(this.publish.put("/test/resource", {"test": "nice"}))
        mids.append(this.publish.post("/test/resource", {"test": "good"}))
        mids.append(this.publish.delete("/test/resource", {"test": "ok"}))

        self.conn.connect()

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
