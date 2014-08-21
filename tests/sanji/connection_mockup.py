import os
import sys
import json
from Queue import Queue

try:
    sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../../')
    from sanji.connection.connection import Connection
except ImportError as e:
    print e
    print "Please check the python PATH for import test module."
    exit(1)

class ConnectionMockup(Connection):

    def __init__(self):
        self.publish_queue = Queue()

    def connect(self):
        return 0

    def disconnect(self):
        return 0

    def set_tunnel(self, tunnel):
        return tunnel

    def on_connect(self, func):
        return func

    def on_message(self, func):
        return func

    def publish(self, **kwargs):
        self.publish_queue.put(json.dumps(kwargs))
        return kwargs

    def on_publish(self, timeout=0.1):
        return self.publish_queue.get(timeout=timeout)
