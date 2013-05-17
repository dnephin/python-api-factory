from collections import namedtuple
import requests
import urlparse


HTTPRequest = namedtuple('HTTPRequest', 'path method query data headers')


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
            query=http_request.query,
            data=http_request.data,
            headers=http_request.headers)

    def receive(self, api_spec, response):
        return api_spec.output_schema.deserialize(response.json)