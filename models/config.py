from cache import Cache
from models.load_balancer import LoadBalancer
from models.target import Target
import os


class Config:
    def __init__(self) -> None:
        self.path_to_config_file: str = os.path.join(
            os.path.expanduser('~'),
            'proxy.conf'
        )
        self.delimiter = '¬'  # TODO change
        self.vars = {
            'port': 8088,
            'cache_size': 40000000000000000000,
            'targets': ['127.0.0.1:8000'],
            'ttl': 20 * 60,
            'unit_time': 300,
            'connection_timeout': 10,
            'path_to_persistence': os.path.join(
                os.path.expanduser('~'),
                'persistence.proxy'
            ),
            'path_to_log': os.path.join(
                os.path.expanduser('~'),
                'proxy.log'
            ),
        }
        self.sleep_time: int = 20
        self.read_config()
        self.init_cache()
        self.sanity_check_config()
        self.set_load_balancer()

    def init_cache(self) -> None:
        self.cache: Cache = Cache(
            self.vars['cache_size'],
            self.vars['ttl'],
            self.delimiter,
            self.vars['path_to_persistence'],
            self.sleep_time
        )

    def parse_targets(self, targets_string: list[str]) -> list[Target]:
        targets: list[Target] = []
        for target in targets_string:
            split_target: list[str] = target.split(':')
            if len(split_target) != 2:
                raise Exception('Invalid configuration file')
            host, port = split_target
            port = int(port)
            targets.append(Target(host, port))
        return targets

    def set_load_balancer(self):
        self.load_balancer: LoadBalancer = LoadBalancer(
            self.parse_targets(self.vars['targets'])
        )

    def read_config(self) -> None:
        if not os.path.exists(self.path_to_config_file):
            print('Configuration file not found')
            print('Proceeding with default settings')
            return
        with open(self.path_to_config_file) as f:
            while line := f.readline():
                tokens: list[str] = line.split('=')
                if len(tokens) != 2:
                    raise Exception('Invalid configuration file')
                key, val = tokens
                if key not in self.vars:
                    raise Exception(
                        f'{key} is not a valid variable in the configuration file'
                    )
                if key == 'port':
                    self.vars['port'] = int(val)
                elif key == 'cache_size':
                    self.vars['cache_size'] = int(val)
                elif key == 'ttl':
                    self.vars['ttl'] = int(val)
                elif key == 'unit_time':
                    self.vars['unit_time'] = int(val)
                elif key == 'targets':
                    self.vars['targets'] = val.split(',')
                elif key == 'connection_timeout':
                    self.vars['connection_timeout'] = int(val)

    def sanity_check_config(self) -> None:
        for value in self.vars.values():
            if not value:
                raise Exception(
                    f'{value} defined in configuration file can not be null')
