import json
from urllib.parse import urljoin

from django.conf import settings

from .base import BaseHTTPClient, BaseHTTPClientError


class DockerAPIError(BaseHTTPClientError):
    pass


class PortainerClient(BaseHTTPClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._auth_token = None

    @classmethod
    def get_internal_client(cls, auth=True):
        client = cls(settings.ENV.PORTAINER_INTERNAL_URL)

        if auth:
            client.authenticate(
                settings.ENV.PORTAINER_ADMIN_USER,
                settings.ENV.PORTAINER_ADMIN_PASSWORD,
            )

        return client

    def _perform_request(self, method, path, with_auth=True, **kwargs):
        headers = kwargs.pop('headers', {})
        if with_auth:
            if not self._auth_token:
                raise RuntimeError('Need to call `authenticate` first!')

            headers['Authorization'] = f'Bearer {self._auth_token}'

        return super()._perform_request(
            method,
            path,
            headers=headers,
            **kwargs,
        )

    def init_admin(self, login, password):
        self._perform_request(
            'POST',
            'api/users/admin/init',
            with_auth=False,
            json={
                'Username': login,
                'Password': password,
            },
        )

    def authenticate(self, login, password):
        # TODO re-auth needed every 8 hours
        response = self._perform_request(
            'POST',
            'api/auth',
            with_auth=False,
            json={
                'Username': login,
                'Password': password,
            },
        )
        self._auth_token = response.json()['jwt']

    def call_docker_api(self, endpoint_id, method, path, params=None, data=None):
        path = path.lstrip('/')
        full_path = f'api/endpoints/{endpoint_id}/docker/{path}'

        response = self._perform_request(
            method,
            full_path,
            params=params,
            json=data,
        )
        lines = response.content.split(b'\n')
        parsed_lines = []

        for line in lines:
            line = line.strip()

            if not line:
                continue

            parsed = json.loads(line)
            if 'error' in parsed:
                raise DockerAPIError(
                    method,
                    full_path,
                    response.status_code,
                    response.content,
                )

            parsed_lines.append(parsed)

        return parsed_lines

    def create_image(self, endpoint_id, image, tag):
        response = self.call_docker_api(
            endpoint_id,
            'POST',
            'images/create',
            params={
                'fromImage': image,
                'tag': tag,
            },
        )
        return response

    def create_container(
        self, endpoint_id, image, tag, name=None, request_data=None,
    ):
        params = {}

        if name:
            params['name'] = name

        data = {'Image': f'{image}:{tag}'}
        data.update(request_data or {})

        response = self.call_docker_api(
            endpoint_id,
            'POST',
            'containers/create',
            data=data,
            params=params,
        )
        try:
            return response[-1]['Id']
        except (IndexError, KeyError):
            raise ValueError('Failed to get container ID from response')

    def get_container_info(self, endpoint_id, name_or_id):
        response = self.call_docker_api(
            endpoint_id,
            'GET',
            f'containers/{name_or_id}/json',
        )
        try:
            return response[-1]
        except IndexError:
            raise ValueError('Failed to fetch container info')

    def start_container(self, endpoint_id, id_or_name):
        response = self.call_docker_api(
            endpoint_id,
            'POST',
            f'containers/{id_or_name}/start',
        )
        return response

    def stop_container(self, endpoint_id, id_or_name):
        response = self.call_docker_api(
            endpoint_id,
            'POST',
            f'containers/{id_or_name}/stop',
        )
        return response

    def delete_container(self, endpoint_id, id_or_name):
        response = self.call_docker_api(
            endpoint_id,
            'DELETE',
            f'containers/{id_or_name}',
        )
        return response

    def add_endpoint(self, name, url):
        response = self._perform_request(
            'POST',
            'api/endpoints',
            json={
                'Name': name,
                'URL': url,
            },
        )
        return response.json()

    def remove_endpoint(self, endpoint_id):
        self._perform_request(
            'DELETE',
            f'api/endpoints/{endpoint_id}',
        )

    def get_external_link_for_endpoint(self, endpoint_id):
        return urljoin(self.base_url, f'#/endpoints/{endpoint_id}')
