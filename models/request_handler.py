import socket
import threading
from models.config import Config


class RequestHandlder:

    def __init__(self, _socket: socket.socket, connection: socket.socket, config: Config) -> None:
        self.socket: socket.socket = _socket
        self.connection: socket.socket = connection
        self.request_data_pool: list[bytes] = []
        self.response_data_pool: list[bytes] = []
        self.config: Config = config

    def run(self) -> None:
        threading.Thread(target=self.handle).start()

    @staticmethod
    def _handle_logging(function):
        def logged_method(self, *args, **kwargs) -> None:
            try:
                function(self, *args, **kwargs)
                # TODO log request here
            except Exception as e:
                print(e)
                # TODO log errors here
                pass
        return logged_method

    @_handle_logging
    def handle(self) -> None:
        self.receive_data(self.connection, self.request_data_pool)
        if res := self.is_cached():
            self.response_data_pool = res.encode('utf-8')
        else:
            self.send_data(self.socket, self.request_data_pool)
            self.receive_data(self.socket, self.response_data_pool)
            self.cache_response()
            self.socket.close()
        self.send_data(self.connection, self.response_data_pool)
        self.connection.close()

    def receive_data(self, _socket: socket.socket, data_pool: list[bytes]) -> None:
        while True:
            data: bytes = _socket.recv(1024)
            if not data:
                break
            data_pool.append(data)

    def send_data(self, _socket: socket.socket, data_pool: list[bytes]) -> None:
        for data in data_pool:
            _socket.send(data)

    def is_cached(self) -> None:
        request = b''.join(self.request_data_pool).decode('utf-8')
        return self.config.cache.get(request)

    def cache_response(self) -> None:
        request: str = b''.join(self.request_data_pool).decode('utf-8')
        response: str = b''.join(self.response_data_pool).decode('utf-8')
        self.config.cache.add(request, response)
