import unittest
import sys
import os

try:
    sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../src')
    from sanji_message import SanjiMessage, SanjiMessageType
except ImportError:
    print "Please check the python PATH for import test module."
    exit(1)

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
        self.assertEqual(sanjimsg.type, SanjiMessageType.REQUEST)

    def test_response_msg(self):
        msg = {
            "id": 123124,
            "code": 200,
            "resource": "/network/cellular/1",
            "method": "get",
            "data": {}
        }

        sanjimsg = SanjiMessage(msg)
        self.assertEqual(sanjimsg.type, SanjiMessageType.RESPONSE)

    def test_direct_msg(self):
        msg = {
            "id": 123124,
            "resource": "/network/cellular/1",
            "method": "get",
            "tunnel": "asdf",
            "data": {}
        }

        sanjimsg = SanjiMessage(msg)
        self.assertEqual(sanjimsg.type, SanjiMessageType.DIRECT)

    def test_event_msg(self):
        msg = {
            "code": 200,
            "resource": "/network/cellular/1",
            "method": "get",
            "data": {}
        }

        sanjimsg = SanjiMessage(msg)
        self.assertEqual(sanjimsg.type, SanjiMessageType.EVENT)

    def test_hook_msg(self):
        msg = {
            "id": 123124,
            "resource": "/network/cellular/1",
            "method": "get",
            "sign": ["abc", "def"],
            "data": {}
        }

        sanjimsg = SanjiMessage(msg)
        self.assertEqual(sanjimsg.type, SanjiMessageType.HOOK)

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
        self.assertEqual(sanjimsg.type, SanjiMessageType.UNKNOW)

        msg = {
            "resource": "/network/cellular/1",
            "method": "get",
            "sign": ["abc", "def"],
            "tunnel": "123",
            "data": {}
        }

        sanjimsg = SanjiMessage(msg)
        self.assertEqual(sanjimsg.type, SanjiMessageType.UNKNOW)

        msg = {
            "method": "get",
            "sign": ["abc", "def"],
            "tunnel": "123",
        }

        sanjimsg = SanjiMessage(msg)
        self.assertEqual(sanjimsg.type, SanjiMessageType.UNKNOW)

        msg = {
            "method": "get",
            "sign": ["abc", "def"],
        }

        sanjimsg = SanjiMessage(msg)
        self.assertEqual(sanjimsg.type, SanjiMessageType.UNKNOW)

if __name__ == "__main__":
    unittest.main()
