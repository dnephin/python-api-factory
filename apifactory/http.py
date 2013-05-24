import colander
from collections import namedtuple
import httplib
import functools
import itertools

try:
    import requests
except ImportError:
    requests = None

import urlparse
from apifactory import strategy, spec


HTTPRequest = namedtuple('HTTPRequest', 'path method query data headers')

class HTTPNotFound(strategy.ClientError):
    """404"""

class HTTPBadRequest(strategy.ClientError):
    """400"""


def build_http_request(api_spec, request_data):
    # TODO: path parts from request_data
    request_data = api_spec.request_schema.serialize(request_data)
    path_data = request_data.get('path')
    path = api_spec.name % path_data if path_data else api_spec.name
    return HTTPRequest(path,
                       api_spec.method,
                       request_data.get('query'),
                       request_data.get('body'),
                       request_data.get('headers'))


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

    def __init__(self, status_code_attr='status_code'):
        self.status_code_attr = status_code_attr

    def handle(self, func):
        response = func()
        status_code = getattr(response, self.status_code_attr)
        if status_code == httplib.OK:
            return response
        if status_code == httplib.NOT_FOUND:
            raise HTTPNotFound()
        if status_code == httplib.BAD_REQUEST:
            raise HTTPBadRequest(response.body)
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


def build_map_from_keys(source, keys):
    return dict((key, source[key]) for key in keys if key in source)


# TODO: make this work with HTTPTransport
# TODO: test case
class HttpMetaSchema(object):
    """A schema which understands how to validate different parts of an http
    request.
    """

    fields = ['body', 'query', 'headers', 'path']

    # TODO: verify no overlaping fields
    def __init__(self, body=None, query=None, headers=None, path=None):
        self.body = body
        self.query = query
        self.headers = headers
        self.path = path

    def serialize(self, request_data):
        """Accepts a blob dict, and returns a dict of fields."""
        def get_values(field, keys):
            serializer = getattr(self, field).serialize
            value = serializer(build_map_from_keys(request_data, keys))
            if value == colander.null:
                return None
            return field, value

        seq = (get_values(*item) for item in self._get_field_to_keys().iteritems())
        return dict(filter(None, seq))

    # TODO: maybe make this take a dict of fields as well?
    def deserialize(self, response):
        """Accepts an HttpRequest/HttpResponse object and returns a dict blob."""
        def values():
            for field, keys in self._get_field_to_keys().iteritems():
                values = getattr(self, field).deserialize(getattr(response, field))
                yield values.items()

        return dict(itertools.chain.from_iterable(values()))

    def _get_field_to_keys(self):
        def get_keys(field):
            if not getattr(self, field):
                return
            return field, getattr(self, field).serialize({}).keys()
        return dict(filter(None, (get_keys(field) for field in self.fields)))