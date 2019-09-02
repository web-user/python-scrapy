# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
import requests
from urllib.parse import urlencode


class GimmeProxy(object):
    API_URL = 'http://gimmeproxy.com/api/getProxy?{conf}'
    API_CONF = {
        'get': 'true',
        'post': 'true',
        'maxCheckPeriod': '1200',
        'protocol': 'http',
        'supportsHttps': 'true',
        'user-agent': 'true',
        'referer': 'true',
        'cookies': 'true',
        'minSpeed': '50',
        'api_key': 'api_key'
    }

    def __init__(self, update_proxy_count=4):
        self.update_proxy_count = update_proxy_count
        self.counter = 0
        self.response = None

    def receive_proxy(self):
        if self.counter > self.update_proxy_count or self.response is None:
            try:
                self.response = json.loads(requests.get(self.API_URL.format(conf=urlencode(self.API_CONF))).text)
                self.counter = 0
            except Exception as e:
                return None

        self.counter += 1

        return 'http://{host}:{port}'.format(host=self.response['ip'], port=self.response['port'])
