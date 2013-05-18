
from collections import namedtuple

APISpec = namedtuple('APISpec', 'name method request_schema response_schema')

RequestSpec = namedtuple('RequestSpec', 'retry_strategy error_strategy')

ClientSpec = namedtuple('ClientSpec', 'api_spec request_spec')
