#!/usr/bin/env python
# -*- coding: UTF-8 -*-


import logging
import uuid

from collections import deque
from threading import Event
from threading import RLock
from threading import Thread
from time import sleep
from time import time

from sanji.message import Message


_logger = logging.getLogger("sanji.sdk.session")


class Status(object):
    """
    Status of session
    """
    CREATED = 0
    SENDING = 1
    SENT = 2
    RESOLVED = 3
    SEND_TIMEOUT = 4
    RESPONSE_TIMEOUT = 4


class TimeoutError(Exception):
    pass


class StatusError(Exception):
    pass


class SessionError(Exception):
    pass


class Session(object):
    """
    Session
    """
    def __init__(self):
        self.aging_unit = 0.5
        self.session_list = {}
        self.session_lock = RLock()
        self.timeout_queue = deque([], maxlen=10)
        self.stop_event = Event()
        self.thread_aging = Thread(target=self.aging)
        self.thread_aging.daemon = True
        self.thread_aging.start()

    def stop(self):
        self.stop_event.set()
        if self.thread_aging.is_alive():
            self.thread_aging.join()

    def resolve(self, msg_id, message=None, status=Status.RESOLVED):
        with self.session_lock:
            session = self.session_list.pop(msg_id, None)
            if session is None:
                return

            session["resolve_message"] = message
            session["status"] = status
            session["is_resolved"].set()
            return session

    def resolve_send(self, mid_id):
        with self.session_lock:
            for session in self.session_list.itervalues():
                if session["mid"] == mid_id:
                    session["status"] = Status.SENT
                    session["is_published"].set()
                    return session
            _logger.debug("Nothing can be resolved mid_id: %s" % mid_id)
            return None

    def create(self, message, mid=None, age=60, force=True):
        """
        create session
            force if you pass `force = False`, it may raise SessionError
                due to duplicate message id
        """
        with self.session_lock:
            if not hasattr(message, "id"):
                message.__setattr__("id", "event-%s" % (uuid.uuid4().hex,))
            if self.session_list.get(message.id, None) is not None:
                if force is False:
                    raise SessionError("Message id: %s duplicate!" %
                                       message.id)
                else:
                    message = Message(message.to_dict(), generate_id=True)

            session = {
                "status": Status.CREATED,
                "message": message,
                "age": age,
                "mid": mid,
                "created_at": time(),
                "is_published": Event(),
                "is_resolved": Event()
            }
            self.session_list.update({
                message.id: session
            })

            return session

    def aging(self):
        while not self.stop_event.is_set():
            with self.session_lock:
                for session_id in self.session_list:
                    session = self.session_list[session_id]
                    # TODO: use system time diff to decrease age
                    #       instead of just - 1 ?
                    session["age"] = session["age"] - self.aging_unit
                    # age > 0
                    if session["age"] > 0:
                        continue

                    # age <= 0, timeout!
                    _logger.debug("Message timeout id:%s", session_id)
                    if session["is_published"].is_set():
                        session["status"] = Status.SEND_TIMEOUT
                    else:
                        session["status"] = Status.RESPONSE_TIMEOUT
                    session["is_published"].set()
                    session["is_resolved"].set()

                    self.timeout_queue.append(session)

                # remove all timeout session
                self.session_list = dict((k, self.session_list[k]) for k
                                         in self.session_list
                                         if self.session_list[k]["status"] !=
                                         Status.SEND_TIMEOUT or
                                         self.session_list[k]["status"] !=
                                         Status.RESPONSE_TIMEOUT)
            sleep(self.aging_unit)
