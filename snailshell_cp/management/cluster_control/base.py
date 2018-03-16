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


def create_environment(keys_map, include_all=True):
    keys_map = keys_map or {}
    output = []

    keys = set()

    for key, value in keys_map.items():
        if value.startswith('$'):
            try:
                value = getattr(settings.ENV, value[1:])
            except AttributeError:
                value = getattr(settings, value[1:])

        keys.add(key)
        output.append(f'{key}={value}')

    if include_all:
        for key, value in settings.ENV.items():
            if key in keys:
                # Do not override explicitly defined variables
                continue

            output.append(f'{key}={value}')

    return output


def build_host_string(login, host, port):
    return f'{login}@{host}:{port}'
