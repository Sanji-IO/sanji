# pylint: disable=no-name-in-module

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
        # CRUD
        self.publish.get("/test/resource")
        msg = json.loads(self.conn.on_publish())
        self.assertEqual("get", msg["payload"]["method"])

        self.publish.put("/test/resource", {"test": "nice"})
        msg = json.loads(self.conn.on_publish())
        self.assertEqual("put", msg["payload"]["method"])
        self.assertEqual({"test": "nice"}, msg["payload"]["data"])

        self.publish.post("/test/resource", {"test": "good"})
        msg = json.loads(self.conn.on_publish())
        self.assertEqual("post", msg["payload"]["method"])
        self.assertEqual({"test": "good"}, msg["payload"]["data"])

        self.publish.delete("/test/resource", {"test": "ok"})
        msg = json.loads(self.conn.on_publish())
        self.assertEqual("delete", msg["payload"]["method"])
        self.assertEqual({"test": "ok"}, msg["payload"]["data"])

    def test_event(self):
        self.publish.event("/test/event", {"type": "notify", "message": "hi"})
        # msg = self.conn.on_publish()

    def test_direct(self):
        self.publish.direct(None, None)

    def test_response(self):
        func = self.publish.response(None)
        func()

if __name__ == "__main__":
    unittest.main()
