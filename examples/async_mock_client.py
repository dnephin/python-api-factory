"""
Example of an http client that return futures (to mock the behaviour of an
async client.
"""


from apifactory import http, factory, spec, schemas
import colander


class QuerySchema(colander.MappingSchema):
    q = colander.SchemaNode(colander.String())


query_schema = http.HttpMetaSchema(query=QuerySchema())


class AsyncHTTPTransportHtml(http.HTTPTransport):

    def send(self, http_request):
        def future(timeout=30):
            return super(AsyncHTTPTransportHtml, self).send(http_request)
        return future

    def receive(self, api_spec, response):
        def future(timeout=30):
            return api_spec.response_schema.deserialize(response(timeout=timeout))
        return future


api_search = http.GET('search', query_schema, schemas.RawSchema)


transport = AsyncHTTPTransportHtml('google.com', 80)
client_mapping = {
    'search': spec.ClientSpec(api_search, http.make_async(http.DEFAULT_GET))
}

http_client = factory.build_client(client_mapping, transport)

future = http_client.search(q='stars')
print "Future ", future

body = future(timeout=3).content
print "Found %s stars" % body.index('stars')
