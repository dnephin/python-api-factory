import mock
from testify import TestCase, assert_equal, setup

from apifactory import http, interfaces
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
        request = self.transport.build(api_spec, 'id', thing='foo')
        expected = http.HTTPRequest(api_spec.name, api_spec.method,
            self.schema.serialize.return_value, None, None)
        assert_equal(request, expected)
        self.schema.serialize.assert_called_with('id', thing='foo')

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
        assert_equal(output, api_spec.output_schema.deserialize.return_value)
        api_spec.output_schema.deserialize.assert_called_with(response.json)
