from models.config import Config
from models.request_handler import RequestHandlder
from models.target import Target
import socket


def start_server(config: Config) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(('', config.port))
        sock.listen()
        while True:
            conn, _ = sock.accept()
            target: Target = config.load_balancer.next()

            third_party_sock: socket.socket = socket.socket(
                socket.AF_INET,
                socket.SOCK_STREAM
            )
            third_party_sock.connect((target.host, target.port))
            request_handler: RequestHandlder = RequestHandlder(
                third_party_sock,
                conn,
                config
            )

            request_handler.run()
