from collections import namedtuple
import httplib
import functools
import requests
import urlparse
from apifactory import strategy, spec


HTTPRequest = namedtuple('HTTPRequest', 'path method query data headers')

class HTTPNotFound(strategy.ClientError):
    """404"""

class HTTPBadRequest(strategy.ClientError):
    """400"""


def build_http_request(api_spec, request_data):
    def get_data_query(method, request_schema, request_data):
        if method == 'POST':
            return request_schema.serialize(request_data), None
        return None, request_schema.serialize(request_data)

    data, query = get_data_query(
        api_spec.method, api_spec.request_schema, request_data)

    return HTTPRequest(api_spec.name, api_spec.method, query, data, None)


class HTTPTransport(object):
    """Simple synchronous HTTP transport using requests library."""

    def __init__(self, host, port):
        self.host = host
        self.port = port

    build = staticmethod(build_http_request)

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
        return api_spec.response_schema.deserialize(response.json)


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


def GET(name, request_schema, response_schema):
    """Factory method for creating APISpecs with the GET method."""
    return spec.APISpec(name, 'GET', request_schema, response_schema)


def POST(name, request_schema, response_schema):
    """Factory method for creating APISpecs with the POST method."""
    return spec.APISpec(name, 'POST', request_schema, response_schema)


# TODO: move to async module? not really http specific
class Async(object):
    """Transform a strategy object to work with futures returned by asynchronous
    http transport.
    """
    def __init__(self, wrapped):
        self.wrapped = wrapped

    def __getattr__(self, item):
        if not hasattr(self.wrapped, item):
            raise AttributeError(item)

        def make_call(func):
            resp_future = func()
            def future_wrapper(timeout=None):
                func = functools.partial(resp_future, timeout=timeout)
                return getattr(self.wrapped, item)(func)
            return future_wrapper
        return make_call


def make_async(request_spec):
    """Convert a RequestSpec to use async strategies."""
    return spec.RequestSpec(
        Async(request_spec.retry_strategy),
        Async(request_spec.error_strategy))