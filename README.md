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
