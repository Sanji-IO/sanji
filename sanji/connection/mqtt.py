#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from __future__ import print_function

import os
import sys
import uuid
import logging
import simplejson as json
import paho.mqtt.client as mqtt
from time import sleep


try:
    sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../../')
    from sanji.connection.connection import Connection
except ImportError as e:
    print(e)
    print("Please check the python PATH for import test module.")
    exit(1)


_logger = logging.getLogger("sanji.sdk.connection.mqtt")


class Mqtt(Connection):

    """
    Mqtt
    """
    def __init__(
        self,
        broker_host=os.getenv('BROKER_PORT_1883_TCP_ADDR', "localhost"),
        broker_port=os.getenv('BROKER_PORT_1883_TCP_PORT', 1883),
        broker_keepalive=60
    ):
        # proerties
        self.tunnels = {
            "internel": (uuid.uuid4().hex, None),
            "model": (None, None),
            "view": (None, None)
        }
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.broker_keepalive = broker_keepalive
        self.client = mqtt.Client()
        self.connect_delay = 3

        # methods
        self.subscribe = self.client.subscribe
        self.unsubscribe = self.client.unsubscribe
        self.message_callback_add = self.client.message_callback_add
        self.message_callback_remove = self.client.message_callback_remove
        self.client.on_log = self.on_log

    def on_log(self, mosq, obj, level, string):
        pass

    def connect(self):
        """
        connect
        """
        _logger.debug("Start connecting to broker")
        while True:
            try:
                self.client.connect(self.broker_host, self.broker_port,
                                    self.broker_keepalive)
                break
            except Exception:
                _logger.debug(
                    "Connect failed. wait %s sec" % self.connect_delay)
                sleep(self.connect_delay)

        self.client.loop_forever()

    def disconnect(self):
        """
        disconnect
        """
        _logger.debug("Disconnect to broker")
        self.client.loop_stop()

    def set_tunnel(self, tunnel_type, tunnel, callback=None):
        """
        set_tunnel(self, tunnel_type, tunnel, callback=None):
        """
        orig_tunnel = self.tunnels.get(tunnel_type, (None, None))[0]
        if orig_tunnel is not None:
            _logger.debug("Unsubscribe: %s", (orig_tunnel,))
            self.client.unsubscribe(str(orig_tunnel))

        self.tunnels[tunnel_type] = (tunnel, callback)

        if callback is not None:
            self.message_callback_add(tunnel, callback)

        self.client.subscribe(str(tunnel))
        _logger.debug("Subscribe: %s", (tunnel,))

    def set_tunnels(self, tunnels):
        """
        set_tunnels(self, tunnels):
        """
        for tunnel_type, (tunnel, callback) in tunnels.iteritems():
            if tunnel is None:
                continue
            self.set_tunnel(tunnel_type, tunnel, callback)

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

    def publish(self, topic="/controller", qos=2, payload=None):
        """
        publish(self, topic, payload=None, qos=0, retain=False)
        Returns a tuple (result, mid), where result is MQTT_ERR_SUCCESS to
        indicate success or MQTT_ERR_NO_CONN if the client is not currently
        connected.  mid is the message ID for the publish request. The mid
        value can be used to track the publish request by checking against the
        mid argument in the on_publish() callback if it is defined.
        """
        result = self.client.publish(topic,
                                     payload=json.dumps(payload),
                                     qos=qos)
        if result[0] == mqtt.MQTT_ERR_NO_CONN:
            raise RuntimeError("No connection")
        return result[1]
