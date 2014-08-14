#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
This is s Sanji Onject
"""

import paho.mqtt.client as mqtt
from threading import Thread
import signal
import sys
import os
import router
import model_initiator
import uuid

"""
Status Codes
"""
CODE_OK = 200
CODE_BAD_REQUEST = 400
CODE_INTERNAL_SERVER_ERROR = 500


"""
Environment Variables
"""
BROKER_IP = os.getenv("BROKER_IP", "127.0.0.1")
BROKER_PORT = int(os.getenv("BROKER_PORT", 1883))


class Sanji(object):
    '''
    ' This is for sanji framework.
    '''
    def __init__(self, **kwargs):
        defaults = {
            "model_name": "",
            "model_path": "",
            "ip": BROKER_IP,
            "port": BROKER_PORT,
            "tunnel": uuid.uuid4(),
            "keepalive": 60
        }

        for (prop, default) in defaults.iteritems():
            setattr(self, prop, kwargs.get(prop, default))

        self._mqtt = mqtt.Client()
        self.router = router.Router()
        self.model_initiator = model_initiator.ModelInitiator( \
            getattr("model_name"), getattr("model_path"))
        self.model_initiator.mkdir()
        self.model_initiator.create_db()

        # setup callbacks
        self._mqtt.on_connect = self._mqtt_on_connect
        self._mqtt.on_message = self._mqtt_on_message

        signal.signal(signal.SIGINT, self.exit)

        self.init()

    def init(self):
        pass

    def _mqtt_on_message(self, mqttc, obj, msg):
        """This function will recevie all message from mqtt
        Args:
            None
        Retruns:
            None
        """
        print msg.topic+" "+str(msg.payload)

    def _mqtt_on_connect(self, mqttc, obj, flags, rc):
        print "Connected with result code "+str(rc)
        self._set_tunnel(self.tunnel)
        mqttc.subscribe("#")

    def _set_tunnel(self, tunnel):
        if self.tunnel != None:
            self._mqtt.unsubscribe(str(elf.tunnel))

        self.tunnel = tunnel
        self._mqtt.subscribe(str(self.tunnel))

    def run(self):
        self._mqtt.connect(getattr("ip"), getattr("port"), getattr("keepalive"))
        self._mqtt.loop_forever()

    def exit(self, signal, frame):
        self._mqtt.loop_stop()
        sys.exit(0)



if __name__ == '__main__':
    pass
