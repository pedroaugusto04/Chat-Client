from abc import ABC, abstractmethod
from typing import Optional

from . import DEFAULT_CONTENT_TYPE


class StompServerProtocol(ABC):
    @classmethod
    @abstractmethod
    def connected(
        cls,
        version,
        heartbeat_incoming: str = None,
        heartbeat_outgoing: str = None,
        session=None,
        server_name=None,
        server_version=None,
    ):
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def message(
        cls,
        subscription: str,
        destination: str,
        message_id: str,
        custom_headers: Optional[dict] = None,
        content_type: str = DEFAULT_CONTENT_TYPE,
    ):
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def receipt(cls, receipt_id: str):
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def error(
        cls,
        receipt_id: str,
        message: str,
        content_type: str = DEFAULT_CONTENT_TYPE,
        content_length: Optional[int] = None,
    ):
        raise NotImplementedError


class Stomp12(StompServerProtocol):
    @classmethod
    def connected(
        cls,
        version,
        heartbeat_incoming: str = None,
        heartbeat_outgoing: str = None,
        session=None,
        server_name=None,
        server_version=None,
    ):
        if heartbeat_incoming or heartbeat_outgoing:
            _heartbeat = f'heart-beat:{heartbeat_incoming},{heartbeat_outgoing}\n'
            if not (heartbeat_incoming and heartbeat_outgoing):
                raise ValueError(
                    'Must set none or both heartbeat settings. '
                    f'heartbeat_incoming={heartbeat_incoming} heartbeat_outgoing={heartbeat_outgoing}'
                )
        else:
            _heartbeat = ''
        _session = f'session:{session}\n' if session else ''
        _server = f"{server_name}{f'/{server_version}' if server_version else ''}" if server_name else ''
        return f'CONNECTED\naccept-version:{version}{_heartbeat}{_session}{_server}\n\n\x00\n'

    @classmethod
    def message(
        cls,
        subscription: str,
        destination: str,
        message_id: str,
        custom_headers: Optional[dict] = None,
        content_type: str = DEFAULT_CONTENT_TYPE,
    ):
        """
        MESSAGE frames are used to convey messages from subscriptions to the client.

        :param subscription:
        :param destination:
        :param message_id:
        :param custom_headers: MESSAGE frames will also include all user defined headers that were present when the
            message was sent to the destination in addition to the server specific headers that MAY get added to the
            frame. Consult your server's documentation to find out the server specific headers that it adds to
            messages.
        :param content_type:
        """
        _custom_headers = (
            ''.join([f'{k}:{v}\n' for k, v in custom_headers.items()]) if custom_headers is not None else ''
        )
        return (
            'MESSAGE\n'
            f'subscription:{subscription}\n'
            f'message-id:{message_id}\n'
            f'destination:{destination}\n'
            f'content-type:{content_type}\n'
            f'{_custom_headers}'
            '\x00\n'
        )

    @classmethod
    def receipt(cls, receipt_id: str):
        return f'RECEIPT\nreceipt-id:{receipt_id}\n\n\x00\n'

    @classmethod
    def error(
        cls,
        receipt_id: str,
        message: str,
        content_type: str = DEFAULT_CONTENT_TYPE,
        content_length: Optional[int] = None,
    ):
        """

        :param receipt_id: If the error is related to a specific frame sent from the client, the server SHOULD add
            additional headers to help identify the original frame that caused the error.
        :param message:
        :param content_type: ERROR frames SHOULD include a content-length header and a content-type header if a body
            is present.
        :param content_length: if None then naively calculated
        """
        _content_length = len(message) if content_length is None else content_length
        return (
            'ERROR\n'
            f'receipt-id:{receipt_id}\n'
            f'content-type:{content_type}\n'
            f'content-length:{_content_length}\n'
            f'message:{message}\n'
            '\x00\n'
        )
