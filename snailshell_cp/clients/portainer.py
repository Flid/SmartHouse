from urllib.parse import urljoin

from .base import BaseHTTPClient, BaseHTTPClientError
import json
from django.conf import settings


class DockerAPIError(BaseHTTPClientError):
    pass


class PortainerClient(BaseHTTPClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._auth_token = None

    @classmethod
    def get_internal_client(cls, auth=True):
        client = cls(settings.PORTAINER_INTERNAL_URL)

        if auth:
            client.authenticate(
                settings.PORTAINER_ADMIN_USER,
                settings.PORTAINER_ADMIN_PASSWORD,
            )

        return client

    def _perform_request(self, method, path, with_auth=True, **kwargs):
        headers = kwargs.pop('headers', {})
        if with_auth:
            if not self._auth_token:
                raise RuntimeError('Need to call `authenticate` first!')

            headers['Authorization'] = 'Bearer {}'.format(self._auth_token)

        return super()._perform_request(
            method,
            path,
            headers=headers,
            **kwargs
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
        full_path = 'api/endpoints/{}/docker/{}'.format(
            endpoint_id,
            path.lstrip('/'),
        )

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

        data = {'Image': '{}:{}'.format(image, tag)}
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
        except KeyError:
            raise ValueError('Failed to get container ID from response')

    def start_container(self, endpoint_id, id_or_name):
        response = self.call_docker_api(
            endpoint_id,
            'POST',
            'containers/{}/start'.format(id_or_name),
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
        response = self._perform_request(
            'DELETE',
            f'api/endpoints/{endpoint_id}',
        )

    def get_external_link_for_endpoint(self, endpoint_id):
        return urljoin(self.base_url, f'#/endpoints/{endpoint_id}')
