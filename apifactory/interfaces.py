"""
Interface definitions for factory dependencies.

These service primarily as documentation and testing with mock.create_autospec()
"""


class ITransport(object):
    """Response for performing the transport of the API request."""

    def build(self, api_spec, *args, **kwargs):
        """Passed the api_spec, args, kwargs. Should return a Request object
        that will be passed to send().
        """
        pass

    def send(self, request):
        """Passed a request object created by the IRequestBuilder, should
        return a response object.
        """
        pass

    def receive(self, api_spec, response):
        """Passed an api_spec, and a response object returned by send(), should
        return a response object.
        """
        pass


class IRetryStrategy(object):

    def retry(self, func):
        pass


class IErrorStrategy(object):

    def handle(self, func):
        pass



class ISchema(object):

    def serialize(self, *args, **kwargs):
        """Serialize method arguments for a request."""
        pass


    def deserialize(self, response):
        """Transform a response into a data object."""
        pass