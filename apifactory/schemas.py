"""
Generic schemas.
"""

class EmptySchema(object):

    @classmethod
    def serialize(cls, request_data):
        return {}

    @classmethod
    def deserialize(cls, response):
        return {}


class StringSchema(object):

    @classmethod
    def serialize(cls, request_data):
        return request_data

    @classmethod
    def deserialize(cls, response):
        return response