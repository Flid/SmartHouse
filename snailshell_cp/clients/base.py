import requests
import logging
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class BaseHTTPClientError(Exception):
    def __init__(self, method, url, status_code, content):
        self.method = method
        self.url = url
        self.status_code = status_code
        self.content = content

    def __str__(self):
        return 'Failed to make {} request to {}: {} {}'.format(
            self.method,
            self.url,
            self.status_code,
            self.content,
        )


class BaseHTTPClient:
    def __init__(self, base_url):
        self.base_url = base_url

    def _perform_request(self, method, path, **kwargs):
        url = urljoin(self.base_url, path)

        runner = getattr(requests, method.lower())
        response = runner(url, **kwargs)

        if not response.ok:
            exc = BaseHTTPClientError(
                method,
                url,
                response.status_code,
                response.content,
            )
            logger.error(str(exc))
            raise exc

        logger.debug('Response for {} {}: {} {}'.format(
            method,
            url,
            response.status_code,
            response.content,
        ))

        return response
