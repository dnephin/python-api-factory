#!/usr/bin/env python


try:
    from setuptools import setup, find_packages
    assert setup
except ImportError:
    from distutils.core import setup

import apifactory

setup(
    name         = 'apifactory',
    version      = '.'.join(map(str, apifactory.version)),
    provides     = ["apifactory"],
    author       = 'Daniel Nephin',
    author_email = 'dnephin@yelp.com',
    description  = 'A library for creating api clients and generic service views.',
    packages     = find_packages(exclude=["tests"]),
    install_requires = ['setuptools'],
)

