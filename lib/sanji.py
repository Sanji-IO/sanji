#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import paho.mqtt.client as mqtt
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


class ModelInitiator(object):
    '''
    '   Deal with some model initialization works like DB and Condifuration files creating.
    '''
    def __init__(self, model_name, model_path, db_type="json"):
        self.model_name = model_name
        self.model_path = model_path
        self.db_type = db_type

    def mkdir(self):
        data_folder_path = self.model_path + "/data"

        if not os.path.exists(data_folder_path):
            os.mkdir(data_folder_path)

    def create_db(self):
        factory_json_db_path = self.model_path + "/data/" + self.model_name + ".factory.json"
        json_db_path = self.model_path + "/data/" + self.model_name + ".json"

        if self.db_type == "json":
            if not os.path.exists(json_db_path):
                if os.path.exists(factory_json_db_path):
                    shutil.copy2(factory_json_db_path, json_db_path)


    def __del__(self):
        pass



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
