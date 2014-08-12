#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
This is s Sanji Onject
"""
import paho.mqtt.client as mqtt
from router import *
from random import randint
from threading import Thread
import signal
import sys
import os
import router
import shutil


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
            "keepalive": 60
        }

        for (prop, default) in defaults.iteritems():
            setattr(self, prop, kwargs.get(prop, default))

        self._mqtt = mqtt.Client()
        self.router = router.Router()
        self.model_initiator = ModelInitiator(getattr("model_name"), getattr("model_path"))
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
        print(msg.topic+" "+str(msg.payload))

    def _mqtt_on_connect(self, mqttc, obj, flags, rc):
        print("Connected with result code "+str(rc))
        mqttc.subscribe("#")

    def run(self):
        self._mqtt.connect(self.ip, self.port, self.keepalive)
        self._mqtt.loop_forever()

    def exit(self, signal, frame):
        self._mqtt.loop_stop()
        sys.exit(0)

    def on_connect(mqttc, obj, flags, rc):
        print("rc: "+str(rc))
    def on_message(mqttc, obj, msg):
        print(msg.topic+" "+str(msg.qos)+" "+str(msg.payload))
    def on_publish(mqttc, obj, mid):
        print("mid: "+str(mid))
    def on_subscribe(mqttc, obj, mid, granted_qos):
        print("Subscribed: "+str(mid)+" "+str(granted_qos))
    def on_log(mqttc, obj, level, string):
        print(string)











if __name__ == '__main__':
    pass
