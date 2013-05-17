"""
Generic IRetryStrategy and IErrorStrategy objects that will work with
any Transport.
"""

class NoRetryStrategy(object):
    """Do not attempt any retries."""

    def retry(self, func):
        return func()


class NoErrorStrategy(object):

    def handle(self, func):
        return func()