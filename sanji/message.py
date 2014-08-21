import urlparse
import json
import copy
from random import randint


def parse_querystring(querystring):
    """
    Return parsed querystring in dict
    """
    if querystring is None or len(querystring) == 0:
        return {}

    qs_dict = urlparse.parse_qs(querystring, keep_blank_values=True)
    for key in qs_dict:
        if len(qs_dict[key]) != 1:
            continue
        qs_dict[key] = qs_dict[key][0]
        if qs_dict[key] == '':
            qs_dict[key] = True

    return qs_dict


def trim_resource(resource):
    """
    trim_resource
    """
    return resource.strip(" \t\n\r/")


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
    def __init__(self, message, generate_id=False):
        if not isinstance(message, dict):
            try:
                message = json.loads(message)
                if not isinstance(message, dict):
                    message = {}
            except Exception:
                raise ValueError("Invaild SanjiMessage." +
                                 "Must be a vaild JSON String")

        # put all prop into object
        for (prop, value) in message.iteritems():
            setattr(self, prop, value)

        if generate_id is True:
            self.generate_id()

        # put message type
        self._type = SanjiMessage.get_message_type(self.__dict__)

    def generate_id(self):
        setattr(self, "id", randint(0, 65535))
        return self.id

    def type(self):
        return self._type

    def to_json(self, pretty=True):
        """
        to_json will call to_dict then dumps into json format
        """
        data_dict = self.to_dict()
        if pretty:
            return json.dumps(data_dict, sort_keys=True, indent=2)
        return json.dumps(data_dict, sort_keys=True)

    def to_dict(self):
        """
        to_dict will clean all protected and private properties
        """
        return {k: self.__dict__[k] for k in self.__dict__ if k.find("_") != 0}

    def match(self, route):
        """
        Match input route and return new SanjiMessage instance
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

    @staticmethod
    def get_message_type(message):
        """
        Return message's type
        """
        for msg_type in SanjiMessageType.FIELDS:
            if SanjiMessage.is_type(msg_type, message):
                return msg_type

        return SanjiMessageType.UNKNOWN

    @staticmethod
    def is_type(msg_type, msg):
        """
        Return message's type is or not
        """
        for prop in SanjiMessageType.FIELDS[msg_type]["must"]:
            if msg.get(prop, False) is False:
                return False
        for prop in SanjiMessageType.FIELDS[msg_type]["prohibit"]:
            if msg.get(prop, False) is not False:
                return False

        return True
