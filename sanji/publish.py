"""
Publish message module
"""

import logging
from time import sleep

from sanji.message import Message
from sanji.session import Status
from sanji.session import TimeoutError
from sanji.session import StatusError


logger = logging.getLogger()


class Object(object):
    pass


class Publish(object):

    """
    Publish class
    """

    def __init__(self, connection, session):
        self._conn = connection
        self._session = session
        self.direct = Object()
        for method in ["get", "post", "put", "delete"]:
            self.__setattr__(method, self.create_crud_func(method))
            self.direct.__setattr__(method,
                                    self.create_crud_func(method, "DIRECT"))
        self.event = self.create_crud_func("post", "EVENT")

    def _wait_resolved(self, session):
        session["is_resolved"].wait()
        if session["status"] == Status.RESPONSE_TIMEOUT:
            raise TimeoutError(session)
        elif session["status"] == Status.RESOLVED:
            return session["resolve_message"]
        raise StatusError(session)

    def _wait_published(self, session, no_response=False):
        session["is_published"].wait()
        if session["status"] == Status.SEND_TIMEOUT:
            raise TimeoutError(session)
        elif session["status"] == Status.SENT:
            # if no_resonse is required, we resolve it as empty response data
            if no_response is True:
                self._session.resolve(session["message"].id)
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

    def create_crud_func(self, method, request_type="CRUD"):
        """
        create_crud_func
        """
        def _crud(resource, data=None, block=True, timeout=60):
            """
            _crud

            block
                True: wait until response arrival
                False: wait until message is already published to local broker
            """
            headers = {
                "resource": resource,
                "method": method
            }

            # DIRECT/EVENT message needs put tunnel in headers for controller
            if request_type == "DIRECT" or request_type == "EVENT":
                headers["tunnel"] = self._conn.tunnel

            message = self._create_message(headers, data)
            with self._session.session_lock:
                mid = self._conn.publish(topic="/controller",
                                         qos=2,
                                         payload=message.to_dict())
                session = self._session.create(message, mid=mid, age=timeout)
                session["status"] = Status.SENDING

            if request_type == "EVENT":  # EVENT always block is False
                return self._wait_published(session, no_response=True)

            # blocking, until we get response or published
            if block is False:
                return self._wait_published(session)
            return self._wait_resolved(session)
        return _crud

    def create_response(self, message, sign):
        """
        return function for response
        """
        def _response(code=200, data=None):
            """
            _response
            """
            message.data = data
            message.__setattr__('code', code)
            if hasattr(message, 'query'):
                del message.query
            if hasattr(message, 'param'):
                del message.param
            if hasattr(message, 'sign'):
                if isinstance(message.sign, list):
                    message.sign.append(sign)
            else:
                message.sign = [sign]

            with self._session.session_lock:
                mid = self._conn.publish(topic="/controller",
                                         qos=2, payload=message.to_dict())
                session = self._session.create(message, mid=mid, age=10)
            logging.debug("sending response as mid: %s" % mid)
            return self._wait_published(session, no_response=True)
        return _response


def Retry(target=None, args=None, kwargs=None,
          options={"retry": True, "interval": 1}):
    """
    options
        retry
            True, infinity retries
            False, no retries
            Number, retries times
        interval
            time period for retry
        return
            None if no success
            Message if success
    """
    retry = options["retry"]
    interval = options["interval"]

    while True:
        try:
            resp = target(*args, **kwargs)
            # status error
            if resp.code == 200:
                return resp

            logger.info("Request got response status: %s"
                        % (resp.code,) + " retry: %s" % (retry,))
        except TimeoutError:
            logger.info("Request message is timeout")

        # register unsuccessful goes here
        # infinity retry
        if retry is True:
            sleep(interval)
            continue

        # no retry
        if retry is False:
            return None

        # retrying
        try:
            retry = retry - 1
            if retry <= 0:
                return None
        except TypeError as e:
            raise e
        sleep(interval)
