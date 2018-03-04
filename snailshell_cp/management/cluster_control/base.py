from contextlib import wraps

from django.conf import settings
from fabric.api import settings as fab_settings
from fabric.api import task
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
        with fab_settings(abort_exception=CommandRunError):
            try:
                return func(*args, **kwargs)
            except NetworkError as exc:
                raise NodeConnectionError(str(exc.args))

    return _runner


def copy_configs(keys_map):
    return [
        f'{key_to}={getattr(settings, key_from)}'
        for key_to, key_from in keys_map.items()
    ]


def get_all_settings_keys():
    output = []

    for key in dir(settings):
        value = getattr(settings, key)

        if isinstance(value, (str, int)):
            output.append(key)

    return output


def build_host_string(login, host, port):
    return f'{login}@{host}:{port}'
