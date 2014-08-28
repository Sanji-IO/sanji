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

    def _wait_response(self, session):
        session["is_resolve"].wait()
        if session["status"] == Status.TIMEOUT:
            raise TimeoutError(session)
        elif session["status"] == Status.RESOLVED:
            return session["resolve_message"]
        raise StatusError(session)

    def create_crud_func(self, method):
        """
        create_crud_func
        """
        def _crud(resource, data=None, block=True, timeout=60):
            """
            _crud
            """
            if isinstance(data, Message):
                message = data
            else:
                payload = {
                    "resource": resource,
                    "method": method
                }
                if data is not None:
                    payload["data"] = data
                message = Message(payload, generate_id=True)

            mid = self._conn.publish(topic="/controller",
                                     qos=2,
                                     payload=message.to_dict())
            session = self._session.create(message, mid=mid, age=timeout)
            session["status"] = Status.SENDING

            if block is False:
                return mid
            # TODO:
            # add to session and wait(blocking) reply.
            # return Reply data
            return self._wait_response(session)
        return _crud

    def event(self, resource, data):
        """
        event
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

    def direct(self, resource, data):
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
