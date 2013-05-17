"""
Factory for creating clientlibs and generic servlets.
"""
import functools


class APIClient(object):
    """A simple APIClient. This client accepts a mapping of method name
    to ClientSpec.  It delegates the method call to the IRequestBuilder
    to create an APIRequest.  The request is passed to its ITransport
    to perform the request.

    Each request is wrapped in a IRetryStrategy and IErrorStrategy
    specified in the request_spec associated with the method name in
    the ClientSpec.
    """

    def __init__(self, client_mapping, transport):
        self.client_mapping  = client_mapping
        self.transport       = transport

    def __getattr__(self, item):
        if item not in self.client_mapping:
            raise AttributeError(item)

        api_spec, request_spec = self.client_mapping[item]
        def make_call(*args, **kwargs):
            request = self.transport.build(api_spec, *args, **kwargs)
            response = request_spec.retry_strategy.retry(
                functools.partial(request_spec.error_strategy.handle,
                    functools.partial(self.transport.send, request)))
            return self.transport.receive(api_spec, response)

        return make_call


def build_client(client_mapping, transport):
    """
    param client_mapping: specification used to construct a client
    type client_mapping: a dict of string to ClientSpec objects

    param transport: transport class used to communicate with the server
    type transport: ITransport
    """
    client = APIClient(client_mapping, transport)
    return client
