import enum
from abc import ABC, abstractmethod
from typing import Optional

from . import DEFAULT_CONTENT_TYPE


class Ack(str, enum.Enum):
    AUTO = 'auto'
    CLIENT = 'client'
    CLIENT_INDIVIDUAL = 'client-individual'


class StompClientProtocol(ABC):
    CONNECT_COMMAND = 'CONNECT'

    @classmethod
    @abstractmethod
    def connect(
        cls,
        host,
        heartbeat_incoming: str = None,
        heartbeat_outgoing: str = None,
        login: str = None,
        passcode: str = None,
        session: str = None,
        server: str = None,
        command: str = CONNECT_COMMAND,
    ) -> str:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def send(
        cls,
        destination: str,
        body: str,
        content_type: str = DEFAULT_CONTENT_TYPE,
        transaction: str = None,
        custom_headers: Optional[dict] = None,
    ) -> str:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def subscribe(cls, id: str, destination: str, ack: Optional[str] = None) -> str:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def unsubscribe(cls, id: str) -> str:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def ack(cls, id: str, transaction: Optional[str] = None) -> str:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def nack(cls, id: str, transaction: Optional[str] = None) -> str:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def begin(cls, transaction: Optional[str] = None) -> str:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def commit(cls, transaction: Optional[str] = None) -> str:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def abort(cls, transaction: Optional[str] = None) -> str:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def disconnect(cls, receipt_id: Optional[str] = None) -> str:
        raise NotImplementedError


class Stomp12(StompClientProtocol):
    """See https://stomp.github.io/stomp-specification-1.2.html"""

    VERSION = '1.2'
    CONNECT_COMMAND = 'CONNECT'
    STOMP_COMMAND = 'STOMP'
    CONNECTED_RESPONSE = 'CONNECTED'
    DISCONNECT_RESPONSE = 'DISCONNECT'
    ERROR_RESPONSE = 'ERROR'

    @classmethod
    def connect(
        cls,
        host,
        heartbeat_incoming: str = None,
        heartbeat_outgoing: str = None,
        login: str = None,
        passcode: str = None,
        session: str = None,
        server: str = None,
        command: str = CONNECT_COMMAND,
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
        _server = f'server:{server}\n' if server else ''
        _session = f'session:{session}\n' if session else ''
        _login = f'login:{login}\n' if login else ''
        _passcode = f'passcode:{passcode}\n' if passcode else ''
        return (
            f'{command}\n'
            f'accept-version:{cls.VERSION}\n'
            f'host:{host}\n'
            f'{_heartbeat}'
            f'{_server}'
            f'{_session}'
            f'{_login}'
            f'{_passcode}'
            '\n\x00\n'
        )

    @classmethod
    def send(
        cls,
        destination: str,
        body: str,
        content_type: str = DEFAULT_CONTENT_TYPE,
        transaction: str = None,
        custom_headers: Optional[dict] = None,
    ):
        _custom_headers = (
            ''.join([f'{k}:{v}\n' for k, v in custom_headers.items()]) if custom_headers is not None else ''
        )
        _content_type = f'content-type:{content_type}\n' if content_type else ''
        _transaction = f'transaction:{transaction}\n' if transaction else ''
        return f'SEND\ndestination:{destination}\n{_content_type}{_transaction}{_custom_headers}{body}\n\x00\n'

    @classmethod
    def subscribe(cls, id: str, destination: str, ack: Optional[str] = Ack.AUTO):
        _ack = f'ack:{ack}\n' if ack is not None else ''
        return f'SUBSCRIBE\nid:{id}\ndestination:{destination}\n{_ack}\n\x00\n'

    @classmethod
    def unsubscribe(cls, id: str):
        return f'UNSUBSCRIBE\nid:{id}\n\n\x00\n'

    @classmethod
    def ack(cls, id: str, transaction: Optional[str] = None):
        _transaction = f'transaction:{transaction}\n' if transaction is not None else ''
        return f'ACK\nid:{id}\n{_transaction}\n\x00\n'

    @classmethod
    def nack(cls, id: str, transaction: Optional[str] = None):
        return f'N{cls.ack(id=id, transaction=transaction)}'

    @classmethod
    def begin(cls, transaction: Optional[str] = None):
        _transaction = f'transaction:{transaction}\n' if transaction is not None else ''
        return f'BEGIN\n{_transaction}\n\x00\n'

    @classmethod
    def commit(cls, transaction: Optional[str] = None):
        _transaction = f'transaction:{transaction}\n' if transaction is not None else ''
        return f'COMMIT\n{_transaction}\n\x00\n'

    @classmethod
    def abort(cls, transaction: Optional[str] = None):
        _transaction = f'transaction:{transaction}\n' if transaction is not None else ''
        return f'ABORT\n{_transaction}\n\x00\n'

    @classmethod
    def disconnect(cls, receipt_id: Optional[str] = None):
        _receipt = f'receipt:{receipt_id}\n' if receipt_id else ''
        return f'DISCONNECT\n{_receipt}\x00\n'
