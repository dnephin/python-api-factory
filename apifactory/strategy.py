"""
Generic IRetryStrategy and IErrorStrategy objects that will work with
any Transport.
"""

class ClientError(Exception):
    """Base class for error strategy exceptions."""


class ServiceNotAvailable(ClientError):
    """Generic error for not being able to complete the service request
    because of an error (either in transport or the service failed).

    IErrorStrategy classes should take care to log more details about an
    error before raising this exception.
    """


class NoRetryStrategy(object):
    """Do not attempt any retries."""

    def retry(self, func):
        return func()


class NoErrorStrategy(object):

    def handle(self, func):
        return func()