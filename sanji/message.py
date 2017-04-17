import simplejson as json
import copy
import os
import random
from random import randint

try:
    from urllib import parse
except ImportError:
    import urlparse as parse

random.seed(os.urandom(10))


def parse_querystring(querystring):
    """
    Return parsed querystring in dict
    """
    if querystring is None or len(querystring) == 0:
        return {}

    qs_dict = parse.parse_qs(querystring, keep_blank_values=True)
    for key in qs_dict:
        if len(qs_dict[key]) != 1:
            continue
        qs_dict[key] = qs_dict[key][0]
        if qs_dict[key] == '':
            qs_dict[key] = True

    return dict((key, qs_dict[key]) for key in qs_dict if len(key) != 0)


def trim_resource(resource):
    """
    trim_resource
    """
    return resource.strip(" \t\n\r/")


class MessageType(object):
    """
    Message Type Enum

        Check is response message or not
        - [v] id
        - [v] code
        - [v] method
        - [v] resource
        - [v] sign
        - [x] tunnel

        Check is request message or not
        - [v] id
        - [x] code
        - [v] method
        - [v] resource
        - [x] sign
        - [x] tunnel

        Check is direct message or not
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

    UNKNOWN = 0
    RESPONSE = 1
    REQUEST = 2
    DIRECT = 3
    EVENT = 4
    HOOK = 5

    FIELDS = {
        RESPONSE: {
            "must": ["id", "code", "method", "resource", "sign"],
            "prohibit": ["tunnel"]
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


class Message(object):
    """
    Message
    """
    def __init__(self, message, generate_id=False):
        if isinstance(message, str) or isinstance(message, unicode):
            try:
                message = json.loads(message)
            except Exception:
                raise ValueError("Invaild Message." +
                                 "Must be a vaild JSON String")

        if not isinstance(message, dict):
            raise TypeError("Message must be JSON string or Dict")

        # put all prop into object
        for (prop, value) in message.iteritems():
            setattr(self, prop, value)

        if generate_id is True:
            self.generate_id()

        # put message type
        self._type = Message.get_message_type(self.__dict__)

    def generate_id(self):
        setattr(self, "id", randint(0, 655350))
        return self.id

    def type(self):
        return self._type

    def to_json(self, pretty=True):
        """
        to_json will call to_dict then dumps into json format
        """
        data_dict = self.to_dict()
        if pretty:
            return json.dumps(
                data_dict, sort_keys=True, indent=2)
        return json.dumps(data_dict, sort_keys=True)

    def to_dict(self):
        """
        to_dict will clean all protected and private properties
        """
        return dict(
            (k, self.__dict__[k]) for k in self.__dict__ if k.find("_") != 0)

    def match(self, route):
        """
        Match input route and return new Message instance
        with parsed content
        """
        _resource = trim_resource(self.resource)
        self.method = self.method.lower()
        resource_match = route.resource_regex.search(_resource)
        if resource_match is None:
            return None

        # build params and querystring
        params = resource_match.groupdict()
        querystring = params.pop("querystring", "")
        setattr(self, "param", params)
        setattr(self, "query", parse_querystring(querystring))

        return copy.deepcopy(self)

    def to_response(self, sign, code=200, data=None):
        """
        transform message to response message
        Notice: this method will return a deepcopy
        """
        msg = copy.deepcopy(self)
        msg.data = data

        setattr(msg, 'code', code)
        for _ in ["query", "param", "tunnel"]:
            if not hasattr(msg, _):
                continue
            delattr(msg, _)

        if hasattr(msg, 'sign') and isinstance(msg.sign, list):
            msg.sign.append(sign)
        else:
            msg.sign = [sign]

        msg._type = Message.get_message_type(msg.__dict__)

        return msg

    def to_event(self):
        """
        get rid of id, sign, tunnel and update message type
        Notice: this method will return a deepcopy
        """
        msg = copy.deepcopy(self)
        for _ in ["id", "sign", "tunnel", "query", "param"]:
            if not hasattr(msg, _):
                continue
            delattr(msg, _)

        msg._type = Message.get_message_type(msg.__dict__)

        return msg

    @staticmethod
    def get_message_type(message):
        """
        Return message's type
        """
        for msg_type in MessageType.FIELDS:
            if Message.is_type(msg_type, message):
                return msg_type

        return MessageType.UNKNOWN

    @staticmethod
    def is_type(msg_type, msg):
        """
        Return message's type is or not
        """
        for prop in MessageType.FIELDS[msg_type]["must"]:
            if msg.get(prop, False) is False:
                return False
        for prop in MessageType.FIELDS[msg_type]["prohibit"]:
            if msg.get(prop, False) is not False:
                return False

        return True
