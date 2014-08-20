from message import SanjiMessage
from message import SanjiMessageType

"""
Publish message module
"""
class Publish(object):
    """
    Publish class
    """
    def __init__(self, connection):
        self._connection = connection
        for method in ["get", "post", "put", "delete"]:
            self.__setattr__(method, self.create_crud_func(method))

    def create_crud_func(self, method):
        """
        create_crud_func
        """
        def _crud(resource, data=None):
            """
            _crud
            """
            payload = {
                "resource": resource,
                "method": method
            }
            if data != None:
                payload["data"] = data
            message = SanjiMessage(payload, generate_id=True)
            self._connection.publish(topic="/controller", qos=2,
                payload=message.to_dict())
        return _crud

    def event(self, resource, data):
        """
        event
        """
        pass

    def direct(self, resource, data):
        """
        direct
        """
        pass

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