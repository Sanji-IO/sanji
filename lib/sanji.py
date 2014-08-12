#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import paho.mqtt.client as mqtt 
from router import *
from random import randint
from threading import Thread
import signal
import sys
import os
import router



'''
Status Codes
'''
CODE_OK = 200
CODE_BAD_REQUEST = 400
CODE_INTERNAL_SERVER_ERROR = 500


'''
Environment Variables
'''
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

        keepalive=60
        self._mqtt = mqtt.Client()
        self.model_name = model_name
        self.model_path = model_path
        self.model_initiator = ModelInitiator(self.model_name, self.model_path)
        self.model_initiator.mkdir()
        self.model_initiator.create_db()
    
        # setup variable
        self.ip = ip
        self.port = port
        self.keepalive = keepalive
        self.router = router.Router()

        # setup callbacks
        self._mqtt.on_connect = self._mqtt_on_connect
        self._mqtt.on_message = self._mqtt_on_message
        
        signal.signal(signal.SIGINT, self.exit)

        self.init()

    def init(self):
        pass

    def _mqtt_on_message(self, mqttc, obj, msg):
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

        #client = mqtt.Client()
        client = mosquitto.Mosquitto(client_id="38129")
        client.on_connect = self.on_connect
        client.on_message = self.on_message
        client.on_publish = self.on_publish
        client.on_subscribe = self.on_subscribe
        client.on_log = self.on_log


        print "start to connect"
        client.connect("127.0.0.1", 1883, 60)
        print "end connect"

        # Blocking call that processes network traffic, dispatches callbacks and
        # handles reconnecting.
        # Other loop*() functions are available that give a threaded interface and a
        # manual interface.
        client.loop_forever()



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





class SanjiJSON(object):
    '''
    ' Provide JSON operations.
    ' Format Example:
        {
            "id":3,
            "method":"get",
            "resource": "/services",
            "code": 200,
            "data": {
                "resources":["http_server","dhcp_server"]
            }
        }
    '''
    def __init__(self, model_name):
        pass


class Model2Model(object):
    def __init__(self):
        pass


if __name__ == '__main__':
    pass
