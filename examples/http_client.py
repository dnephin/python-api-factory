"""An example of using an HTTP client to make a get request which returns
HTML.
"""

import colander
from apifactory import http, factory, spec, schemas


class QuerySchema(colander.MappingSchema):
    q = colander.SchemaNode(colander.String())


query_schema = http.HttpMetaSchema(query=QuerySchema())

api_search = http.GET('search', query_schema, schemas.RawSchema)


transport = http.HTTPTransport('google.com', 80)
client_mapping = {
    'search': spec.ClientSpec(api_search, http.DEFAULT_GET)
}

http_client = factory.build_client(client_mapping, transport)


body = http_client.search(q='stars').content
print "Found %s stars" % body.count('stars')