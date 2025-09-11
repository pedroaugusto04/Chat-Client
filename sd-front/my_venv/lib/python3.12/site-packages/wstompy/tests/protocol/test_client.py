import pytest

from ...protocol.client import Stomp12, Ack

protocol = Stomp12

_EXAMPLE_HOST = 'example.com'
_EXAMPLE_PATH = '/example/path'
_EXAMPLE_BODY = 'lorem'


@pytest.mark.kwparametrize(
    [
        dict(
            host=_EXAMPLE_HOST,
            heartbeat_incoming=None,
            heartbeat_outgoing=None,
            login=None,
            passcode=None,
            session=None,
            server=None,
            expected=f'CONNECT\naccept-version:1.2\nhost:{_EXAMPLE_HOST}\n\n\x00\n',
        ),
    ]
)
def test_connect(
    host,
    heartbeat_incoming,
    heartbeat_outgoing,
    login,
    passcode,
    session,
    server,
    expected,
):
    assert (
        protocol.connect(
            host=host,
            heartbeat_incoming=heartbeat_incoming,
            heartbeat_outgoing=heartbeat_outgoing,
            login=login,
            passcode=passcode,
            session=session,
            server=server,
        )
        == expected
    )


@pytest.mark.kwparametrize(
    [
        dict(
            destination=_EXAMPLE_PATH,
            body=_EXAMPLE_BODY,
            transaction=None,
            custom_headers=None,
            expected=f'SEND\ndestination:{_EXAMPLE_PATH}\ncontent-type:text/plain\n{_EXAMPLE_BODY}\n\x00\n',
        ),
        dict(
            destination=_EXAMPLE_PATH,
            body=_EXAMPLE_BODY,
            transaction='transaction1',
            custom_headers=None,
            expected=(
                f'SEND\ndestination:{_EXAMPLE_PATH}\ncontent-type:text/plain\n'
                f'transaction:transaction1\n{_EXAMPLE_BODY}\n\x00\n'
            ),
        ),
        dict(
            destination=_EXAMPLE_PATH,
            body=_EXAMPLE_BODY,
            transaction=None,
            custom_headers={'myheader1': 'myheadervalue1'},
            expected=(
                f'SEND\ndestination:{_EXAMPLE_PATH}\ncontent-type:text/plain\n'
                f'myheader1:myheadervalue1\n{_EXAMPLE_BODY}\n\x00\n'
            ),
        ),
    ]
)
def test_send(destination, body, transaction, custom_headers, expected):
    assert (
        protocol.send(
            destination=destination,
            body=body,
            transaction=transaction,
            custom_headers=custom_headers,
        )
        == expected
    )


@pytest.mark.kwparametrize(
    [
        dict(
            id_='1',
            destination=_EXAMPLE_PATH,
            ack=None,
            expected=f'SUBSCRIBE\nid:1\ndestination:{_EXAMPLE_PATH}\n\n\x00\n',
        ),
        dict(
            id_='2',
            destination=_EXAMPLE_PATH,
            ack=Ack.CLIENT,
            expected=f'SUBSCRIBE\nid:2\ndestination:{_EXAMPLE_PATH}\nack:{Ack.CLIENT}\n\n\x00\n',
        ),
    ]
)
def test_subscribe(id_, destination, ack, expected):
    assert (
        protocol.subscribe(
            id=id_,
            destination=destination,
            ack=ack,
        )
        == expected
    )


@pytest.mark.kwparametrize(
    [
        dict(
            id_='1',
            expected='UNSUBSCRIBE\nid:1\n\n\x00\n',
        ),
    ]
)
def test_unsubscribe(id_, expected):
    assert (
        protocol.unsubscribe(
            id=id_,
        )
        == expected
    )


@pytest.mark.kwparametrize(
    [
        dict(
            id_='1',
            transaction=None,
            expected='ACK\nid:1\n\n\x00\n',
        ),
        dict(
            id_='1',
            transaction='transaction1',
            expected='ACK\nid:1\ntransaction:transaction1\n\n\x00\n',
        ),
    ]
)
def test_ack(id_, transaction, expected):
    assert (
        protocol.ack(
            id=id_,
            transaction=transaction,
        )
        == expected
    )


@pytest.mark.kwparametrize(
    [
        dict(
            id_='1',
            transaction=None,
            expected='NACK\nid:1\n\n\x00\n',
        ),
        dict(
            id_='1',
            transaction='transaction1',
            expected='NACK\nid:1\ntransaction:transaction1\n\n\x00\n',
        ),
    ]
)
def test_nack(id_, transaction, expected):
    assert (
        protocol.nack(
            id=id_,
            transaction=transaction,
        )
        == expected
    )


@pytest.mark.kwparametrize(
    [
        dict(
            transaction=None,
            expected='BEGIN\n\n\x00\n',
        ),
        dict(
            transaction='transaction1',
            expected='BEGIN\ntransaction:transaction1\n\n\x00\n',
        ),
    ]
)
def test_begin(transaction, expected):
    assert (
        protocol.begin(
            transaction=transaction,
        )
        == expected
    )


@pytest.mark.kwparametrize(
    [
        dict(
            transaction=None,
            expected='COMMIT\n\n\x00\n',
        ),
        dict(
            transaction='transaction1',
            expected='COMMIT\ntransaction:transaction1\n\n\x00\n',
        ),
    ]
)
def test_commit(transaction, expected):
    assert (
        protocol.commit(
            transaction=transaction,
        )
        == expected
    )


@pytest.mark.kwparametrize(
    [
        dict(
            transaction=None,
            expected='ABORT\n\n\x00\n',
        ),
        dict(
            transaction='transaction1',
            expected='ABORT\ntransaction:transaction1\n\n\x00\n',
        ),
    ]
)
def test_abort(transaction, expected):
    assert (
        protocol.abort(
            transaction=transaction,
        )
        == expected
    )


@pytest.mark.kwparametrize(
    [
        dict(
            receipt_id=None,
            expected='DISCONNECT\n\x00\n',
        ),
        dict(
            receipt_id='1',
            expected='DISCONNECT\nreceipt:1\n\x00\n',
        ),
    ]
)
def test_disconnect(receipt_id, expected):
    assert (
        protocol.disconnect(
            receipt_id=receipt_id,
        )
        == expected
    )
