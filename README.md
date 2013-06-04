API Factory
===========

A python library for creating API clients and generic servlets. This library
is built in layers.

Core
----
The core layer is a set of interfaces, value objects (namedtuple), and
`glue code` to bind them together. The interfaces outline:

* retrying failed requests
* handling errors (and raising appropriate exceptions)
* request transport
* request/response encoding, validation, and serialization

The following modules are part of this layer:

* ``apifactory.interfaces``
* ``apifactory.spec``
* ``apifactory.factory``

Note that caching and service discovery are not covered at this time. These
tasks tend to be more application specific and should live on top of the client
created by ``factory.build_client()``. They made be included in the future.


Implementation
--------------
The second layer contains some common implementations of the interfaces which
can be used to create full clients and generic views.

The following modules are part of this layer:

* ``apifactory.schemas``
* ``apifactory.strategy``
* ``apifactory.http``


How it works
------------

### API Spec

Start by creating a specification. A specification starts as one or more APISpec
objects. Each APISpec object identifies an API endpoint.


    from apifactory import spec
    example_spec = spec.APISpec('name', 'method', request_schema, response_schema)

The ``name`` is an identifier for this request. With HTTP this is usually a
string, but it can be any unique identifier. The ``name`` is accessed by the
``ITransport.build()`` method and the service view builder (TODO: interface name).

The ``method`` is an access method. In http this is an HTTP method. Other
protocols may be able to ignore the method.

The ``request_schema`` is an ``ISchema`` object which serializes the kwargs
passed to the service client, and deserializes it on the server side. Similarly
the ``response_schema`` is an ``ISchema`` object which serializes the response
and deserializes it on the client side.


### Client Spec

Once the interface has been defined you can create a specification for the
client.


Service View Spec
~~~~~~~~~~~~~~~~~
