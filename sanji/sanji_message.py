class SanjiMessageType(object):
    """
    Message Type Enum

        Check is response message or not
        - [v] id
        - [v] code
        - [v] method
        - [v] resource
        - [x] sign
        - [x] tunnel

        Check is request message or not
        - [v] id
        - [x] code
        - [v] method
        - [v] resource
        - [x] sign
        - [x] tunnel

        Check is event message or not
        - [v] id
        - [x] code
        - [v] method
        - [v] resource
        - [x] sign
        - [v] tunnel

        Check is event message or not
        - [x] id
        - [v] code
        - [v] method
        - [v] resource
        - [x] sign
        - [x] tunnel

        Check is hook message or not
        - [v] id
        - [x] code
        - [v] method
        - [v] resource
        - [v] sign
        - [x] tunnel
    """

    UNKNOW = 0
    RESPONSE = 1
    REQUEST = 2
    DIRECT = 3
    EVENT = 4
    HOOK = 5

    FIELDS = {
        RESPONSE: {
            "must": ["id", "code", "method", "resource"],
            "prohibit": ["sign", "tunnel"]
        },
        REQUEST: {

            "must": ["id", "method", "resource"],
            "prohibit": ["code", "sign", "tunnel"]
        },
        DIRECT: {
            "must": ["id", "method", "resource", "tunnel"],
            "prohibit": ["code", "sign"]
        },
        EVENT: {
            "must": ["code", "method", "resource"],
            "prohibit": ["id", "sign", "tunnel"]
        },
        HOOK: {
            "must": ["id", "method", "resource", "sign"],
            "prohibit": ["code", "tunnel"]
        }
    }

class SanjiMessage(object):
    """
    SanjiMessage
    """


    def __init__(self, message):
        self.data = message
        self.type = SanjiMessage.get_message_type(message)

    @staticmethod
    def get_message_type(message):
        """
        Return message's type
        """
        for msg_type in SanjiMessageType.FIELDS:
            if SanjiMessage.is_type(msg_type, message):
                return msg_type

        return SanjiMessageType.UNKNOW

    @staticmethod
    def is_type(msg_type, msg):
        """
        Return message's type is or not
        """
        for prop in SanjiMessageType.FIELDS[msg_type]["must"]:
            if msg.get(prop, False) == False:
                return False
        for prop in SanjiMessageType.FIELDS[msg_type]["prohibit"]:
            if msg.get(prop, False) != False:
                return False

        return True
