import colander
from collections import namedtuple
import httplib
import functools
import itertools
import urllib

try:
    import requests
except ImportError:
    requests = None

try:
    import simplejson as json
except ImportError:
    import json

import urlparse
from apifactory import strategy, spec, compat


HTTPRequest = namedtuple('HTTPRequest', 'path method query data headers')

class HTTPNotFound(strategy.ClientError):
    """404"""

class HTTPBadRequest(strategy.ClientError):
    """400"""


def build_http_request(api_spec, request_data):
    """Build an HTTPRequest object from a dict of request_data. Uses the
    api_spec to serialize the data.
    """
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
        return api_spec.response_schema.deserialize(response)


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


def filter_dict(seq):
    """Create a dict from seq by filtering out falsy values."""
    return dict(itertools.ifilter(None, seq))


def get_colander_keys(schema):
    """Function which returns the names of SchemaNodes from a colander.Schema.
    Includes a hook for non-colander schema objects which provide a
    `validates_keys` property.
    """
    if hasattr(schema, 'validates_keys'):
        return getattr(schema, 'validates_keys')
    return [node.name for node in schema.children]


def filter_optional(output, optional_sentinel):
    """Filter a dictionary by removing items with value of 'optional_sentinel'.
    Returns a iterable of pairs.
    """
    return ((key, value) for key, value in output.iteritems()
            if value is not optional_sentinel)


class SchemaValueError(ValueError):
    """Raised when a schema can not be created."""


class HttpMetaSchema(object):
    """A schema which understands how to validate different parts of an http
    request.
    """

    def __init__(self, field_to_key_mapper=get_colander_keys, **schemas):
        self.schemas = schemas
        self.field_to_key_mapper = field_to_key_mapper
        self.verify_schema_uniqueness()

    def serialize(self, request_data):
        """Accepts a blob dict, and returns a dict of fields."""
        def get_values(field, keys):
            source = build_map_from_keys(request_data, keys)
            value = self.schemas[field].serialize(source)
            return field, dict(filter_optional(value, colander.null))

        seq = (get_values(*item) for item in self._get_field_to_keys().iteritems())
        return filter_dict(seq)

    # TODO: maybe make this take a dict of fields as well?
    def deserialize(self, response):
        """Accepts an HttpRequest/HttpResponse object and returns a dict blob."""
        def get_values(field):
            values = self.schemas[field].deserialize(getattr(response, field))
            return filter_optional(values, compat.drop)
        seq = (get_values(field) for field in self.schemas)
        return dict(itertools.chain.from_iterable(seq))

    def _get_field_to_keys(self):
        return dict((field, self.field_to_key_mapper(schema))
                    for field, schema in self.schemas.iteritems())

    def verify_schema_uniqueness(self):
        field_to_keys = self._get_field_to_keys()
        for left, right in itertools.combinations(field_to_keys.itervalues(), 2):
            if set(left) & set(right):
                msg = "Schemas have overlapping keys: %s"
                raise SchemaValueError(msg % ','.join(set(left) & set(right)))


class JsonHttpRequest(object):
    """A thin adapter over http.HTTPRequest to convert query/data from a
    dict to the proper format. Some http clients (requests) will do this
    for you. Others (tornado) will not.  This is to be used with the tornado
    brand of requests.
    """

    def __init__(self, request):
        self.request = request

    @property
    def data(self):
        return json.dumps(self.request.data) if self.request.data else None

    @property
    def query(self):
        return urllib.urlencode(self.request.query) if self.request.query else None

    def __getattr__(self, name):
        return getattr(self.request, name)


class JsonHttpResponse(object):
    """A thin adapter over HttpResponse to convert body to a dict.
    """

    def __init__(self, response):
        self.response = response

    @property
    def body(self):
        return json.loads(self.response.body)

    def __getattr__(self, name):
        return getattr(self.response, name)