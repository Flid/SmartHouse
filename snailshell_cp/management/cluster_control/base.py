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


def create_environment(keys_map):
    output = []

    for key, value in keys_map.items():
        if value.startswith('$'):
            value = getattr(settings, value[1:])

        output.append(f'{key}={value}')

    return output


def get_all_settings_keys():
    output = []

    for key in dir(settings):
        value = getattr(settings, key)

        if isinstance(value, (str, int)):
            output.append(key)

    return output


def build_host_string(login, host, port):
    return f'{login}@{host}:{port}'
