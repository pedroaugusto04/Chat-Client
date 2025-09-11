import websocket

from .protocol.client import Stomp12

WEBSOCKET_STOMP12_SUBPROTOCOL = 'v12.stomp'


class WebSocketStompClient(websocket.WebSocketApp):
    """

    Documentation and typing for on_* methods are taken from websocket.WebSocketApp doc.
    """

    def __init__(self, header_host, socket_url, custom_headers=None, protocol=None, **kwargs):
        """
        :param header_host: Value for Host in headers
        :param socket_url: location of socket to connect to
        :param custom_headers: extra headers needed for your configuration, such as auth
        """
        super().__init__(
            url=socket_url,
            header=custom_headers,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open,
            on_message=self.on_message,
            **kwargs,
        )
        self.protocol = Stomp12 if protocol is None else protocol
        self.header_host = header_host
        self.stomp_is_connected = False

    def on_error(self, _self: websocket.WebSocketApp, error):
        pass

    def on_close(self, _self: websocket.WebSocketApp, close_status_code, close_msg):
        pass

    def on_open(self, _self: websocket.WebSocketApp):
        """Callback object which is called at opening websocket."""
        self.send(self.protocol.connect(self.header_host))

    def on_message(self, _self: websocket.WebSocketApp, message: str):
        """
        Callback object which is called when received data.
        :param _self:
        :param message: utf-8 data received from the server
        """
        if not self.stomp_is_connected:
            if message.startswith(self.protocol.CONNECTED_RESPONSE):
                self.stomp_is_connected = True
                # TODO client -> server heartbeats
            elif message.startswith(self.protocol.ERROR_RESPONSE):
                supported_versions = message.split('\n', 2)[1]
                raise RuntimeError(
                    f'Server does not support STOMP version {self.protocol.VERSION}, '
                    f'they responded with versions {supported_versions}'
                )
        else:
            if message.startswith(self.protocol.DISCONNECT_RESPONSE):
                # From STOMP v. 1.2 docs: Clients MUST NOT send any more frames after the DISCONNECT frame is sent.
                self.stomp_is_connected = False

    def subscribe(self, id, destination, ack='client'):
        self.send(self.protocol.subscribe(id=id, destination=destination, ack=ack))

    def unsubscribe(self, id):
        self.send(self.protocol.unsubscribe(id=id))

    def disconnect(self, receipt_id: str):
        self.send(self.protocol.disconnect(receipt_id=receipt_id))
