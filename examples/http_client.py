"""An example of using an HTTP client to make a get request which returns
HTML.
"""

from apifactory import http, factory, spec


class QuerySchema(object):

    def serialize(self, *args, **kwargs):
        return {'q': args[0]}


class RawSchema(object):

    def deserialize(self, response):
        return response


class HTTPTransportHtml(http.HTTPTransport):

    def receive(self, api_spec, response):
        return api_spec.response_schema.deserialize(response.content)


api_search = http.GET('search', QuerySchema(), RawSchema())


transport = HTTPTransportHtml('google.com', 80)
client_mapping = {
    'search': spec.ClientSpec(api_search, http.DEFAULT_GET)
}

http_client = factory.build_client(client_mapping, transport)

print http_client.search('stars')