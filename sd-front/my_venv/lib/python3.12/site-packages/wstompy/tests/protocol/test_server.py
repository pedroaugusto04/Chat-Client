import pytest

from ...protocol.server import Stomp12


protocol = Stomp12

_EXAMPLE_PATH = '/example/path'
_EXAMPLE_BODY = 'lorem'


@pytest.mark.kwparametrize(
    [
        dict(
            version='1',
            heartbeat_incoming=None,
            heartbeat_outgoing=None,
            session=None,
            server_name=None,
            server_version=None,
            expected='CONNECTED\naccept-version:1\n\n\x00\n',
        ),
    ]
)
def test_connected(
    version,
    heartbeat_incoming,
    heartbeat_outgoing,
    session,
    server_name,
    server_version,
    expected,
):
    assert (
        protocol.connected(
            version=version,
            heartbeat_incoming=heartbeat_incoming,
            heartbeat_outgoing=heartbeat_outgoing,
            session=session,
            server_name=server_name,
            server_version=server_version,
        )
        == expected
    )


@pytest.mark.kwparametrize(
    [
        dict(
            subscription='1',
            destination=_EXAMPLE_PATH,
            message_id='1',
            custom_headers=None,
            expected=(
                f'MESSAGE\nsubscription:1\nmessage-id:1\ndestination:{_EXAMPLE_PATH}\ncontent-type:text/plain\n\x00\n'
            ),
        ),
        dict(
            subscription='1',
            destination=_EXAMPLE_PATH,
            message_id='1',
            custom_headers={'myheader1': 'myvalue1'},
            expected=(
                f'MESSAGE\nsubscription:1\nmessage-id:1\ndestination:{_EXAMPLE_PATH}\n'
                'content-type:text/plain\nmyheader1:myvalue1\n\x00\n'
            ),
        ),
    ]
)
def test_message(subscription, destination, message_id, custom_headers, expected):
    assert (
        protocol.message(
            subscription=subscription,
            destination=destination,
            message_id=message_id,
            custom_headers=custom_headers,
        )
        == expected
    )


@pytest.mark.kwparametrize(
    [
        dict(
            receipt_id='1',
            expected='RECEIPT\nreceipt-id:1\n\n\x00\n',
        ),
    ]
)
def test_receipt(receipt_id, expected):
    assert (
        protocol.receipt(
            receipt_id=receipt_id,
        )
        == expected
    )


@pytest.mark.kwparametrize(
    [
        dict(
            receipt_id='1',
            message=_EXAMPLE_BODY,
            content_length=None,
            expected=(
                'ERROR\n'
                'receipt-id:1\n'
                'content-type:text/plain\n'
                f'content-length:{len(_EXAMPLE_BODY)}\n'
                f'message:{_EXAMPLE_BODY}\n'
                '\x00\n'
            ),
        ),
    ]
)
def test_error(receipt_id, message, content_length, expected):
    assert (
        protocol.error(
            receipt_id=receipt_id,
            message=message,
            content_length=content_length,
        )
        == expected
    )
