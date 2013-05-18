"""Example of building generic servlets with flask.
"""
import functools
import json

from apifactory import http, factory, spec

from flask import request, Flask


class IdSchema(object):

    def serialize(self, request_data):
        return request_data

    def deserialize(self, response):
        return int(response['id'])


class BoolSchema(object):

    def serialize(self, request_data):
        return request_data

    def deserialize(self, response):
        return response['bool']


class MultiIdSchema(object):

    def serialize(self, from_id, to_id):
        return {
            'fromid': from_id,
            'toid': to_id
        }

    def deserialize(self, response):
        return response['fromid'], response['toid']


id_schema = IdSchema()

api_translate = http.GET('translate', id_schema, id_schema)
api_add_translation = http.POST('translate/add', MultiIdSchema(), BoolSchema())


app = Flask('example_flask')

# There is probably a better way to do this if I knew more about flask
def build_route(api_spec):
    def builder(f):

        @functools.wraps(f)
        def servlet(*args, **kwargs):
            data = json.loads(request.data) if api_spec.method == 'POST' else request.args
            response = f(api_spec.request_schema.deserialize(data))
            return json.dumps(api_spec.response_schema.serialize(response))

        url = '/%s' % api_spec.name
        app.add_url_rule(url, None, servlet, methods=[api_spec.method])
        return servlet
    return builder


mapping = {}


@build_route(api_translate)
def translate(id):
    return dict(id=mapping.get(id, 0))


@build_route(api_add_translation)
def add_translation((from_id, to_id)):
    mapping[from_id] = to_id
    return dict(bool=True)


if __name__ == "__main__":
    app.debug = True
    app.run()