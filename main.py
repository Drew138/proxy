from models.config import Config
from connection import start_server


def main() -> None:
    config: Config = Config()
    start_server(config)


if __name__ == '__main__':
    main()
