"""
Generic schemas.
"""

class EmptySchema(object):

	def serialize(self, request_data):
		return {}
	
	def deserialize(self, response):
		return {}