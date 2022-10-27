import socket
import threading
from models.config import Config
from models.target import Target
import logging


class RequestHandlder:

    def __init__(self, connection: socket.socket, config: Config) -> None:
        self.target: Target = config.load_balancer.next()
        self.connection: socket.socket = connection
        self.config: Config = config
        self.SEPARATOR = b'\r\n\r\n'

        logging.basicConfig(
            level=logging.INFO,
            filename=self.config.vars['path_to_log'],
            filemode='a',
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%d-%b-%y %H:%M:%S'
        )

    def run(self) -> None:
        threading.Thread(target=self.handle).start()

    @staticmethod
    def _handle_logging(function):
        def logged_method(self, *args, **kwargs) -> None:
            try:
                request, response = function(self, *args, **kwargs)
                tmp = '\n=== Request ===\n%s\n=== Response ===\n%s'
                logging.info(tmp, request, response)
                print(tmp, request, response)
            except Exception as e:
                print(e)
                logging.error('Error: %s', e)
            finally:
                self.connection.close()
        return logged_method

    # @_handle_logging
    def handle(self) -> tuple[bytes, bytes]:
        request: bytes = self.receive_data(self.connection)
        response, can_be_cached = self.is_cached(request)
        if not (response and can_be_cached):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as _socket:
                print("enterd, didnt use cache")
                _socket.connect((self.target.host, self.target.port))
                _socket.settimeout(self.config.vars['connection_timeout'])
                self.send_data(_socket, request)
                response = self.receive_data(_socket)

                # Cache response
                if can_be_cached:
                    self.cache_response(request, response)
        self.send_data(self.connection, response)

        return request, response

    def receive_data(self, _socket: socket.socket) -> bytes:
        buffer: bytes = bytes()
        while not self.is_end_of_header(buffer):
            data: bytes = _socket.recv(1024)
            buffer += data

        header, content = buffer.split(self.SEPARATOR)

        lines: list[bytes] = header.split(b'\r\n')
        content_length: int = 0
        for line in lines:
            if line.startswith(b'Content-Length'):
                content_length: int = int(line.split(b': ')[1].decode('utf-8'))
                break

        while not self.is_end_of_content(content_length, content):
            data: bytes = _socket.recv(1024)
            content += data

        return header + self.SEPARATOR + content

    def is_end_of_header(self, buffer) -> bool:
        return self.SEPARATOR in buffer

    def is_end_of_content(self, length, data) -> bool:
        return len(data) >= length

    def send_data(self, _socket: socket.socket, data_pool: bytes) -> None:
        _socket.sendall(data_pool)

    @staticmethod
    def can_be_cached(data: bytes) -> bool:
        return data.startswith((b'HEAD', b'GET'))

    def is_cached(self, request) -> tuple[bytes, bool]:
        response = self.config.cache.get(request)
        can_be_cached = self.can_be_cached(request)
        return response, can_be_cached

    def cache_response(self, request: bytes, response: bytes) -> None:
        self.config.cache.add(request, response)
