from models.config import Config
from models.target import Target
import socket
import threading


def receive(connection: socket.socket, data_pool: list[bytes]) -> None:
    try:
        while True:
            data = connection.recv(1024)
            if not data:
                break
            data_pool.append(data)
    except Exception as e:
        print(e)
        pass
    finally:
        connection.close()


def send(connection: socket.socket, data_pool, is_connection_alive: list[bool]) -> None:
    # cur_index = 0
    try:
        for data in data_pool:
            connection.send(data)

        # while True:
        #     if (not is_connection_alive[0]) and (cur_index + 1 >= len(data_pool)):
        #         break
        #     if cur_index + 1 <= len(data_pool):
        #         cur_index += 1
    except Exception as e:
        print(e)
        pass


def respond_cache() -> None:
    pass


def start_server(config: Config) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(('', config.port))
        sock.listen()
        while True:
            conn, _ = sock.accept()
            data_pool_request = []
            data_pool_response = []
            is_request_connection_alive: list[bool] = [True]
            is_response_connection_alive: list[bool] = [True]

            target: Target = config.load_balancer.next()

            third_party_sock: socket.socket = socket.socket(
                socket.AF_INET,
                socket.SOCK_STREAM
            )
            third_party_sock.connect((target.host, target.port))

            receiving_request_thread = threading.Thread(
                target=receive,
                args=(
                    conn,
                    data_pool_request,
                    is_request_connection_alive
                )
            )
            send_request_thread = threading.Thread(
                target=send,
                args=(
                    third_party_sock,
                    data_pool_request,
                    is_request_connection_alive
                )
            )
            receiving_response_thread = threading.Thread(
                target=receive,
                args=(
                    third_party_sock,
                    data_pool_response,
                    is_response_connection_alive
                )
            )
            sending_response_thread = threading.Thread(
                target=send,
                args=(
                    conn,
                    data_pool_request,
                    is_response_connection_alive
                )
            )
            receiving_request_thread.start()
            send_request_thread.start()
            receiving_response_thread.start()
            sending_response_thread.start()
