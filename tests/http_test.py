import colander
import mock
from testify import TestCase, assert_equal, setup
from testify.assertions import assert_raises

from apifactory import http, interfaces, schemas, compat
from apifactory import spec


class HTTPTransportTestCase(TestCase):

    @setup
    def setup_transport(self):
        self.host = 'localhost'
        self.port = 8080
        self.transport = http.HTTPTransport(self.host, self.port)
        self.schema = mock.create_autospec(interfaces.ISchema)
        self.api_spec = spec.APISpec('path', 'GET', self.schema, self.schema)

    def test_build(self):
        api_spec = self.api_spec
        request_data = dict(id='id', thing='foo')
        request = self.transport.build(api_spec, request_data)
        expected = http.HTTPRequest(api_spec.name, api_spec.method,
            self.schema.serialize.return_value.get.return_value,
            self.schema.serialize.return_value.get.return_value,
            self.schema.serialize.return_value.get.return_value)
        assert_equal(request, expected)
        self.schema.serialize.assert_called_with(request_data)
        assert_equal(
            self.schema.serialize.return_value.get.mock_calls,
            [mock.call('path'), mock.call().__nonzero__()] +
            [mock.call(field) for field in ('query', 'body', 'headers')])

    def test_build_url(self):
        path =  'what'
        url = self.transport.build_url(path)
        assert_equal(url, 'http://localhost:8080/what')

    @mock.patch('apifactory.http.requests.request', autospec=True)
    def test_send(self, mock_request):
        http_request = mock.create_autospec(http.HTTPRequest, path='what')
        response = self.transport.send(http_request)
        assert_equal(response, mock_request.return_value)
        mock_request.assert_called_with(
            http_request.method,
            'http://localhost:8080/what',
            params=http_request.query,
            data=http_request.data,
            headers=http_request.headers)

    @mock.patch('apifactory.http.JsonHttpResponse', autospec=True)
    def test_receive(self, mock_json_response):
        response = mock.Mock()
        api_spec = self.api_spec
        output = self.transport.receive(self.api_spec, response)
        assert_equal(output, api_spec.response_schema.deserialize.return_value)
        mock_json_response.assert_called_with(response)
        api_spec.response_schema.deserialize.assert_called_with(
            mock_json_response.return_value)


class AsyncTestCase(TestCase):

    @setup
    def setup_async(self):
        self.wrapped = mock.create_autospec(interfaces.IErrorStrategy)
        self.async = http.Async(self.wrapped)

    def test__getattr__method_does_not_exist(self):
        assert_raises(AttributeError, getattr, self.async, 'bogus_method')

    def test__getattr__(self):
        response = mock.Mock()
        future = self.async.handle(response)
        assert_equal(self.wrapped.handle.mock_calls, [])
        response.assert_called_with()

        assert_equal(future(), self.wrapped.handle.return_value)
        assert_equal(self.wrapped.handle.call_count, 1)


class FilterDictTestCase(TestCase):

    def test_filter_dict(self):
        seq = [(1,2), None, (3,4), False, 0]
        assert_equal(http.filter_dict(seq), {1:2, 3:4})


class GetColanderKeysTestCase(TestCase):

    def test_get_colander_keys_validates_keys(self):
        expected = mock.Mock()
        mock_schema = mock.Mock(validates_keys=expected)
        assert_equal(http.get_colander_keys(mock_schema), expected)

    def test_get_colander_keys_from_node_names(self):
        friend = colander.SchemaNode(colander.Tuple())
        friend.add(colander.SchemaNode(colander.Int(),
                   validator=colander.Range(0, 9999), name='rank'))
        friend.add(colander.SchemaNode(colander.Int(), name='foo'))
        assert_equal(http.get_colander_keys(friend), ['rank', 'foo'])


class HttpMetaSchemaTestCase(TestCase):

    @setup
    def setup_schema(self):
        self.body_schema = colander.SchemaNode(colander.Mapping())
        self.body_schema.add(colander.SchemaNode(colander.String(), name='one'))
        self.body_schema.add(colander.SchemaNode(colander.String(),
                             name='three', missing=compat.drop))
        self.path_schema = colander.SchemaNode(colander.Mapping())
        self.path_schema.add(colander.SchemaNode(colander.String(), name='two'))
        self.meta_schema = http.HttpMetaSchema(
            body=self.body_schema,
            path=self.path_schema)

    def test_serialize(self):
        source = {'one': 1, 'two': 2, 'three': 3, 'extra': 9}
        output = self.meta_schema.serialize(source)
        expected = {
            'body': {'one': '1', 'three': '3'},
            'path': {'two': '2'}
        }
        assert_equal(output, expected)

    def test_deserialize(self):
        source =  mock.Mock(body={'one': 1}, path={'two': 2, 'extra': 9})
        output = self.meta_schema.deserialize(source)
        expected = {
            'one': '1',
            'two': '2',
        }
        assert_equal(output, expected)

    def test_serialize_optional(self):
        source = {'one': 1, 'two': 2}
        output = self.meta_schema.serialize(source)
        expected = {
            'body': {'one': '1'},
            'path': {'two': '2'}
        }
        assert_equal(output, expected)

    def test_verify_schema_uniqueness_not_unique(self):
        self.path_schema.add(colander.SchemaNode(colander.String(), name='one'))
        assert_raises(http.SchemaValueError,
              http.HttpMetaSchema, body=self.body_schema, path=self.path_schema)
