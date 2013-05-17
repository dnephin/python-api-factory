from collections import namedtuple
import httplib
import requests
import urlparse
from apifactory import strategy, spec


HTTPRequest = namedtuple('HTTPRequest', 'path method query data headers')

class HTTPNotFound(strategy.ClientError):
    """404"""

class HTTPBadRequest(strategy.ClientError):
    """400"""


class HTTPTransport(object):
    """Simple synchronous HTTP transport using requests library."""

    def __init__(self, host, port):
        self.host = host
        self.port = port

    def get_data_query(self, method, input_schema, *args, **kwargs):
        if method == 'POST':
            return input_schema.serialize(*args, **kwargs), None
        return None, input_schema.serialize(*args, **kwargs)

    def build(self, api_spec, *args, **kwargs):
        data, query = self.get_data_query(
            api_spec.method, api_spec.input_schema, *args, **kwargs)

        return HTTPRequest(api_spec.name, api_spec.method, query, data, None)

    def build_url(self, path):
        parts = 'http', '%s:%s' % (self.host, self.port), path, None, None, None
        return urlparse.urlunparse(parts)

    def send(self, http_request):
        return requests.request(
            http_request.method,
            self.build_url(http_request.path),
            params=http_request.query,
            data=http_request.data,
            headers=http_request.headers)

    def receive(self, api_spec, response):
        return api_spec.output_schema.deserialize(response.json)


class HTTPErrorStrategy(object):

    def handle(self, func):
        response = func()
        status_code = response.status_code
        if status_code == httplib.OK:
            return response
        if status_code == httplib.NOT_FOUND:
            raise HTTPNotFound()
        if status_code == httplib.BAD_REQUEST:
            raise HTTPBadRequest()
        raise strategy.ServiceNotAvailable()


class HTTPRetryStrategy(object):

    def __init__(self, retry_count=3):
        self.retry_count = retry_count

    def retry(self, func):
        for _ in xrange(self.retry_count):
            try:
                return func()
            except strategy.ServiceNotAvailable:
                continue
        raise


DEFAULT_GET = spec.RequestSpec(HTTPRetryStrategy(), HTTPErrorStrategy())


def GET(name, input_schema, output_schema):
    """Factory method for creating APISpecs with the GET method."""
    return spec.APISpec(name, 'GET', input_schema, output_schema)


def POST(name, input_schema, output_schema):
    """Factory method for creating APISpecs with the POST method."""
    return spec.APISpec(name, 'POST', input_schema, output_schema)