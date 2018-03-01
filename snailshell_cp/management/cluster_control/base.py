from fabric.api import settings, task
from contextlib import wraps
from fabric.exceptions import NetworkError


class BaseClusterControlException(Exception):
    pass


class CommandRunError(BaseClusterControlException):
    """
    Has an error message in `self.args[0]`
    """


class NodeConnectionError(BaseClusterControlException):
    """
    Failed to connect to a node. The message is in `self.args[0]`
    """


def cp_task(func):
    @task
    @wraps(func)
    def _runner(*args, **kwargs):
        with settings(abort_exception=CommandRunError):
            try:
                return func(*args, **kwargs)
            except NetworkError as exc:
                raise NodeConnectionError(str(exc.args))

    return _runner


def copy_configs(env, keys_map):
    return [
        f'{key_to}={env[key_from]}'
        for key_to, key_from in keys_map.items()
    ]


def build_host_string(login, host, port):
    return f'{login}@{host}:{port}'
