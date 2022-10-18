from cache import Cache
from load_balancer import LoadBalancer
from models.target import Target
import os
from threading import Lock


class Config:
    def __init__(self) -> None:
        # targets is not included in instance
        # properties as it is handled by load
        # the load balancer.
        self.port: str = '80'
        self.cache_size: int = 400
        self.ttl: int = 20 * 60
        self.unit_time: int = 300
        self.delimitier: str = ''
        self.path_to_persistence: str = os.path.join(
            os.path.expanduser('~'),
            'persistence.proxy'
        )
        # path to config file can not be assigned
        # via config file for obvious reasons.
        self.path_to_config_file: str = os.path.join(
            os.path.expanduser('~'),
            'proxy.conf'
        )
        self.path_to_log: str = os.path.join(
            os.path.expanduser('~'),
            'proxy.log'
        )

        self.vars = {
            'port',
            'targets',
            'cache_size',
            'ttl',
            'unit_time',
            'delimiter',
            'path_to_persistence'
        }
        self.lock: Lock = Lock()
        self.read_config()
        self.init_cache()
        self.sanity_check_config()

    def init_cache(self) -> None:
        self.cache: Cache = Cache(
            self.cache_size,
            self.ttl,
            self.delimitier,
            self.path_to_persistence,
            self.lock
        )

    def parse_targets(self, targets_string: str) -> list[Target]:
        targets: list[Target] = []
        for target in targets_string:
            split_target: list[str] = target.split(':')
            if len(split_target) != 2:
                raise Exception('Invalid configuration file')
            ip, host = split_target
            targets.append(Target(ip, host))
        return targets

    def read_config(self) -> None:
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
                    self.port: str = val
                elif key == 'cache_size':
                    self.cache_size: int = int(val)
                elif key == 'ttl':
                    self.ttl: int = int(val)
                elif key == 'unit_time':
                    self.unit_time: int = int(val)
                else:
                    self.load_balancer: LoadBalancer = LoadBalancer(
                        self.parse_targets(val)
                    )

    def sanity_check_config(self) -> None:
        for var in self.vars:
            if not hasattr(self, var):
                raise Exception(f'{var} missing in configuration file')

        for var in self.vars:
            if getattr(self, var) == '':
                raise Exception(
                    f'{var} defined in configuration file can not be empty')

        if not hasattr(self, 'load_balancer'):
            raise Exception('load_balancer missing in configuration file')

        if not hasattr(self, 'cache'):
            raise Exception('load_balancer missing in configuration file')
