"""
Connection Interface Module
"""


class Connection(object):
    """
    Connection interface
    """
    def connect(self):
        """
        connect
        """
        raise NotImplementedError("Should have implemented this")

    def disconnect(self):
        """
        disconnect
        """
        raise NotImplementedError("Should have implemented this")

    def set_tunnel(self, type, tunnel, callback=None):
        """
        set tunnel
        """
        raise NotImplementedError("Should have implemented this")

    def set_tunnels(self, tunnels):
        """
        set tunnels
        """
        raise NotImplementedError("Should have implemented this")

    def set_on_connect(self, func):
        """
        set_on_connect
        """
        raise NotImplementedError("Should have implemented this")

    def set_on_message(self, func):
        """
        set_on_message
        """
        raise NotImplementedError("Should have implemented this")

    def set_on_publish(self, func):
        """
        set_on_publish
        """
        raise NotImplementedError("Should have implemented this")

    def publish(self, *args, **kwargs):
        """
        publish
        """
        raise NotImplementedError("Should have implemented this")
