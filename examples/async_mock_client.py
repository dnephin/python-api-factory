"""
Example of an http client that return futures (to mock the behaviour of an
async client.
"""


from apifactory import http, factory, spec


class QuerySchema(object):

    def serialize(self, request_data):
        return request_data


class RawSchema(object):

    def deserialize(self, response):
        return response


class AsyncHTTPTransportHtml(http.HTTPTransport):

    def send(self, http_request):
        def future(timeout=30):
            return super(AsyncHTTPTransportHtml, self).send(http_request)
        return future

    def receive(self, api_spec, response):
        def future(timeout=30):
            content = response(timeout=timeout).content
            return api_spec.response_schema.deserialize(content)
        return future


api_search = http.GET('search', QuerySchema(), RawSchema())


transport = AsyncHTTPTransportHtml('google.com', 80)
client_mapping = {
    'search': spec.ClientSpec(api_search, http.make_async(http.DEFAULT_GET))
}

http_client = factory.build_client(client_mapping, transport)

future = http_client.search(q='stars')
print "Future ", future

print future(timeout=3)[-300:]
