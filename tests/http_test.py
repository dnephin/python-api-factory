import mock
from testify import TestCase, assert_equal, setup
from testify.assertions import assert_raises

from apifactory import http, interfaces, schemas
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

    def test_receive(self):
        response = mock.Mock()
        api_spec = self.api_spec
        output = self.transport.receive(self.api_spec, response)
        assert_equal(output, api_spec.response_schema.deserialize.return_value)
        api_spec.response_schema.deserialize.assert_called_with(response.json)


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


class HttpMetaSchemaTestCase(TestCase):

    @setup
    def setup_schema(self):
        self.body_schema = mock.create_autospec(interfaces.ISchema)
        self.path_schema = mock.create_autospec(interfaces.ISchema)
        self.meta_schema = http.HttpMetaSchema(
            body=self.body_schema,
            path=self.path_schema)

    def test_serialize(self):
        self.body_schema.serialize.return_value = {'one': 'une', 'three': 'trois'}
        self.path_schema.serialize.return_value = {'two': 'deux'}
        source = {'one': 1, 'two': 2, 'three': 3}
        output = self.meta_schema.serialize(source)
        expected = {
            'body': {'one': 'une', 'three': 'trois'},
            'path': {'two': 'deux'}
        }
        assert_equal(output, expected)

    def test_deserialize(self):
        self.body_schema.deserialize.return_value = {'one': 'une', 'three': 'trois'}
        self.path_schema.deserialize.return_value = {'two': 'deux'}
        source =  mock.Mock(body={'one': 1, 'three': 3}, path={'two': 2})
        output = self.meta_schema.deserialize(source)
        expected = {
            'one': 'une',
            'two': 'deux',
            'three': 'trois'
        }
        assert_equal(output, expected)