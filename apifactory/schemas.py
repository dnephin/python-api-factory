"""
Generic schemas.
"""

class EmptySchema(object):

    validates_keys = []

    @classmethod
    def serialize(cls, request_data):
        return {}

    @classmethod
    def deserialize(cls, response):
        return {}


class RawSchema(object):

    @classmethod
    def serialize(cls, request_data):
        return request_data

    @classmethod
    def deserialize(cls, response):
        return response