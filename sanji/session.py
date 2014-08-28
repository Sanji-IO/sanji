from Queue import Queue
from threading import Lock
from threading import Thread
from threading import Event
from time import sleep
from time import time


class Status(object):
    """
    Status of session
    """
    CREATED = 0
    SENDING = 1
    SENT = 2
    RESOLVED = 3
    TIMEOUT = 4


class TimeoutError(Exception):
    pass


class StatusError(Exception):
    pass


class Session(object):
    """
    Session
    """
    def __init__(self):
        self.session_list = {}
        self.session_lock = Lock()
        self.timeout_queue = Queue()
        self.stop_event = Event()
        self.thread_aging = Thread(target=self.aging)
        self.thread_aging.daemon = True
        self.thread_aging.start()

    def stop(self):
        self.stop_event.set()
        self.thread_aging.join()

    def resolve(self, msg_id, data=None, status=Status.RESOLVED):
        self.session_lock.acquire()
        session = self.session_list.pop(msg_id, None)
        if session is None:
            # TODO: Warning message, nothing can be resolved.
            print "TODO: Warning message, nothing can be resolved"
            return
        session["resolve_message"] = data
        session["status"] = status
        session["is_resolve"].set()
        self.session_lock.release()
        return session

    def resolve_send(self, mid_id):
        self.session_lock.acquire()
        for session in self.session_list.itervalues():
            if session["mid"] == mid_id:
                session["status"] = Status.SENT
                self.session_lock.release()
                return session
        self.session_lock.release()
        return None

    def create(self, message, mid=None, age=60):
        self.session_lock.acquire()
        if self.session_list.get(message.id, None) is not None:
            self.session_lock.release()
            return None
        session = {
            "status": Status.CREATED,
            "data": message,
            "age": age,
            "mid": mid,
            "created_at": time(),
            "is_resolve": Event()
        }
        self.session_list.update({
            message.id: session
        })
        self.session_lock.release()

        return session

    def aging(self):
        while not self.stop_event.is_set():
            self.session_lock.acquire()
            for session_id in self.session_list:
                session = self.session_list[session_id]
                # TODO: use system time diff to decrease age
                #       instead of just - 1 ?
                session["age"] = session["age"] - 0.5
                if session["age"] <= 0:
                    session["status"] = Status.TIMEOUT
                    session["is_resolve"].set()
                    self.timeout_queue.put(session)

            # remove all timeout session
            self.session_list = {k: self.session_list[k] for k
                                 in self.session_list
                                 if self.session_list[k]["status"]
                                 != Status.TIMEOUT}
            self.session_lock.release()
            sleep(0.5)
