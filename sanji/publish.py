"""
Publish message module
"""

from sanji.message import Message
from sanji.session import Status
from sanji.session import TimeoutError
from sanji.session import StatusError


class Publish(object):

    """
    Publish class
    """
    def __init__(self, connection, session):
        self._conn = connection
        self._session = session
        for method in ["get", "post", "put", "delete"]:
            self.__setattr__(method, self.create_crud_func(method))

    def _wait_resolved(self, session):
        session["is_resolved"].wait()
        if session["status"] == Status.RESPONSE_TIMEOUT:
            raise TimeoutError(session)
        elif session["status"] == Status.RESOLVED:
            return session["resolve_message"]
        raise StatusError(session)

    def _wait_published(self, session):
        session["is_published"].wait()
        if session["status"] == Status.SEND_TIMEOUT:
            raise TimeoutError(session)
        elif session["status"] == Status.SENT:
            return session
        raise StatusError(session)

    def _create_message(self, headers=None, data=None):
        payload = headers
        if isinstance(data, Message):
            return data
        else:
            if data is not None:
                payload["data"] = data

        return Message(payload, generate_id=True)

    def create_crud_func(self, method):
        """
        create_crud_func
        """
        def _crud(resource, data=None, block=True, timeout=60):
            """
            _crud
            """
            headers = {
                "resource": resource,
                "method": method
            }
            message = self._create_message(headers, data)
            mid = self._conn.publish(topic="/controller",
                                     qos=2,
                                     payload=message.to_dict())
            session = self._session.create(message, mid=mid, age=timeout)
            session["status"] = Status.SENDING

            # non-blocking, response mid immediately
            if block is False:
                return self._wait_published(session)
            # blocking, until we get response
            return self._wait_resolved(session)
        return _crud

    def event(self, resource, data=None, block=True, timeout=60):
        """
        event
        """
        headers = {
            "resource": resource,
            "method": "post",
            "tunnel": self._conn.tunnel
        }
        message = self._create_message(headers, data)
        mid = self._conn.publish(topic="/controller", qos=2,
                                 payload=message.to_dict())

        session = self._session.create(message, mid=mid, age=timeout)
        session["status"] = Status.SENDING
        # non-blocking, response mid immediately
        if block is False:
            return session
        # blocking, until it is been published
        return self._wait_published(session)

    def direct(self, resource, data=None, block=True, timeout=60):
        """
        direct
        """
        payload = {
            "resource": resource,
            "method": "post",
            "tunnel": self._conn.tunnel,
            "data": data
        }
        message = Message(payload, generate_id=True)
        mid = self._conn.publish(topic="/controller", qos=2,
                                 payload=message.to_dict())

        return mid

    def response(self, orig_message):
        """
        response
        """
        def _response():
            """
            _response
            """
            pass
        return _response
