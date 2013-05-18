from testify import TestCase, setup, assert_equal
import mock
from testify.assertions import assert_raises_and_contains

from apifactory import interfaces, factory
from apifactory.spec import ClientSpec, APISpec, RequestSpec


def build_spec_builder(in_schema, out_schema):
    def builder(name, method):
        return APISpec(name, method, in_schema, out_schema)
    return builder


class APIClientTestCase(TestCase):

    @setup
    def setup_client(self):
        request_schema = mock.create_autospec(interfaces.ISchema)
        response_schema = mock.create_autospec(interfaces.ISchema)
        apis = build_spec_builder(request_schema, response_schema)
        req_spec = RequestSpec(mock.create_autospec(interfaces.IRetryStrategy),
                               mock.create_autospec(interfaces.IErrorStrategy))
        req_spec.error_strategy.handle.side_effect = lambda f: f()
        req_spec.retry_strategy.retry.side_effect = lambda f: f()

        self.client_mapping = {
            'update_one':   ClientSpec(apis('one', 'POST'), req_spec),
            'get_one':      ClientSpec(apis('one', 'GET'), req_spec),
            'get_two':      ClientSpec(apis('two', 'GET'), req_spec),
            'search':       ClientSpec(apis('search', 'GET'), req_spec),
        }
        self.transport = mock.create_autospec(interfaces.ITransport)
        self.client = factory.build_client(self.client_mapping, self.transport)

    def test__getattr__update_one(self):
        response = self.client.update_one(id='id', fresh_read=True)
        api_spec, request_spec = self.client_mapping['update_one']
        assert_equal(response, self.transport.receive.return_value)
        self.transport.receive.assert_called_with(
            api_spec, self.transport.send.return_value)

        self.transport.build.assert_called_with(
            api_spec, dict(id='id', fresh_read=True))

        self.transport.send.assert_called_with(
            self.transport.build.return_value)

        assert_equal(request_spec.error_strategy.handle.call_count, 1)
        assert_equal(request_spec.retry_strategy.retry.call_count, 1)


    def test__getattr__unknown_method(self):
        method_name = 'missing_method'
        assert_raises_and_contains(AttributeError,
            method_name,
            getattr, self.client, method_name)