# import os
# import sys
# import unittest

# try:
#     sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../../../sanji')
#     from core import Sanji
#     from connection.mqtt import MQTT
# except ImportError:
#     print "Please check the python PATH for import test module."
#     exit(1)

# class TestModel(Sanji):
    
#     def init(self):
#         self.router.route("/model/:id") \
#             .get(self.get) \
#             .post(self.post)

#     def get(self, request, response):
#         print request

#     def post(self, request, response):
#         print request


# class TestSanjiClass(unittest.TestCase):
#     @classmethod
#     def setUpClass(cls):
#         print "Mosquitto broker is up."

#     @classmethod
#     def tearDownClass(cls):
#         print "Mosquitto broker is down."

#     def setUp(self):
#         self.model = TestModel(connection=MQTT())

#     def tearDown(self):
#         self.model = None

#     def test_init(self):
#         self.model.run()


# if __name__ == "__main__":
#     unittest.main()
