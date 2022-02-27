import platform
import requests_mock.response

import simplejson


requests_mock.response.jsonutils = simplejson
requests_mock.response.json = simplejson


if platform.system() == 'Darwin':
    import socket

    socket.gethostbyname = lambda x: '127.0.0.1'


pytest_plugins = [
    'tests.fixtures.fixtures'
]