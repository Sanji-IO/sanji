"""
Publish message module
"""

from sanji.message import SanjiMessage


class Publish(object):

    """
    Publish class
    """
    def __init__(self, connection):
        self._conn = connection
        for method in ["get", "post", "put", "delete"]:
            self.__setattr__(method, self.create_crud_func(method))

    def create_crud_func(self, method):
        """
        create_crud_func
        """
        def _crud(resource, data=None, block=True):
            """
            _crud
            """
            payload = {
                "resource": resource,
                "method": method
            }
            if data is not None:
                payload["data"] = data
            message = SanjiMessage(payload, generate_id=True)
            mid = self._conn.publish(topic="/controller",
                                     qos=2,
                                     payload=message.to_dict())
            if block is False:
                return mid
            # TODO:
            # add to session and wait(blocking) reply.
            # return Reply data
            return mid
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
        message = SanjiMessage(payload, generate_id=True)
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
        message = SanjiMessage(payload, generate_id=True)
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
