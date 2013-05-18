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
        """Called with an IErrorStrategy.handle callable. Should call func()
        and retry on appropriate exceptions, or raise the current exception.
        Return the result of func() on success.
        """
        pass


class IErrorStrategy(object):

    def handle(self, func):
        """Called with an Itransport.send callable. Should call func() handle
        exceptions (or error responses derived from the response of func())
        and return the result of func() on success. Raise appropriate exceptions
        on errors. Raised errors will be handled by an IRetryStrategy.
        """
        pass


class ISchema(object):

    def serialize(self, request_data):
        """Serialize method arguments for a request."""
        pass


    def deserialize(self, response):
        """Transform a response into a data object."""
        pass