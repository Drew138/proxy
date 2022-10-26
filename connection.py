from models.config import Config
from models.request_handler import RequestHandlder
import socket
import threading


def start_server(config: Config) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        port: int = config.vars['port']
        sock.bind(('', port))
        sock.listen()
        print(f'started listening on port {port}')
        
        threading.Thread(target=config.cache.check_time).start()
        
        while True:
            conn, _ = sock.accept()
            conn.settimeout(config.vars['connection_timeout'])
            request_handler: RequestHandlder = RequestHandlder(
                conn,
                config
            )

            request_handler.run()
