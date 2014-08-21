#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import os
import sys
import uuid
import paho.mqtt.client as mqtt
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../')
from message import SanjiMessage
from message import SanjiMessageType
from connection import Connection


class MQTT(Connection):
    """
    MQTT
    """
    def __init__(self, broker_ip="127.0.0.1", broker_port=1883,
                 broker_keepalive=60):
        # proerties
        self.tunnel = uuid.uuid4().hex
        self.broker_ip = broker_ip
        self.broker_port = broker_port
        self.broker_keepalive = broker_keepalive
        self.client = mqtt.Client()

        # methods
        self.subscribe = self.client.subscribe
        self.unsubscribe = self.client.unsubscribe

    def connect(self):
        """
        connect
        """
        self.client.connect(self.broker_ip, self.broker_port,
                            self.broker_keepalive)
        self.client.loop_forever()

    def disconnect(self):
        """
        disconnect
        """
        self.client.loop_stop()

    def set_tunnel(self, tunnel):
        """
        set_tunnel(self, tunnel):
        """
        if self.tunnel is not None:
            self.client.unsubscribe(str(self.tunnel))

        self.tunnel = tunnel
        self.client.subscribe(str(self.tunnel))

    def set_on_connect(self, func):
        """
        set_on_connect
        """
        self.client.on_connect = func

    def set_on_message(self, func):
        """
        set_on_message
        """
        self.client.on_message = func

    def set_on_publish(self, func):
        """
        set_on_publish
        """
        self.client.on_publish = func

    def publish(self, message, msg_type=SanjiMessageType.REQUEST,
                topic="/controller", qos=2):
        """
        publish
        """
        if not isinstance(message, SanjiMessage):
            raise TypeError("message should be SanjiMessage instance")

        if message.type() == SanjiMessageType.UNKNOWN:
            raise ValueError("message should be vaild SanjiMessageType")

        message_id = None
        if msg_type == SanjiMessageType.REQUEST or \
           msg_type == SanjiMessageType.DIRECT:
            message_id = message.generate_id()
        else:
            message_id = message.id

        return message_id
