# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import threading
import logging.config
import signal
import json
import sys
import getopt
import traceback
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

__cur_dir = os.path.dirname(os.path.abspath(__file__))
__sdk_path = os.path.abspath(os.path.join(__cur_dir, '..', '..', '..', 'src'))
sys.path.insert(0, __sdk_path)
sys.path.insert(0, os.path.join(__cur_dir, 'pymodules'))

from actionsampler.action_sampler import ActionSampler, is_windows
if is_windows:
    from actionsampler.window_touch_sampler import unhook_all
from WrappedDeviceAPI.deviceAdapter import DeviceType

LOG_CFG_FILE = 'cfg/log.ini'
_log_dir = os.path.join(__cur_dir, 'log')
if not os.path.exists(_log_dir):
    os.makedirs(_log_dir)
logging.config.fileConfig(LOG_CFG_FILE)

LOG = logging.getLogger('action_sampler')
sampler = None


def print_usage():
    print((os.path.split(sys.argv[0])[1]))
    print(("""
Usage:
%s 
    -h                       - print the usage.
    -s <serial number>       - option, android device's serial number, such as 950d652a.
""" % os.path.split(sys.argv[0])[1]))


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def __echo_response(self, err_code=0, err_msg=''):
        resp = {
            'error_code': err_code,
            'error_message': err_msg
        }
        self._set_headers()
        self.wfile.write(json.dumps(resp).encode())

    def do_GET(self):
        """Serve a GET request."""
        global samp
        result = urlparse(self.path)
        query = result.query
        LOG.info('get a request:%s' % query)
        if not query:
            return self.__echo_response(1, 'empty query')

        queryItems = query.split('&')
        querys = {}
        for item in queryItems:
            k, v = item.split('=')
            querys[k] = v
        if 'method' not in querys:
            return self.__echo_response(2, 'no method')

        method = querys['method']
        if method == 'quit':
            LOG.info('to be ready to quit')
            sampler.set_exited()

        return self.__echo_response()


def http_server(port):
    server_address = ('127.0.0.1', port)
    LOG.info('set up http server at port:%s' % port)
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
    httpd.serve_forever()


def main():
    global sampler
    device_id = None
    device_type = DeviceType.Android.value
    port = 52808
    options, _ = getopt.getopt(sys.argv[1:], 's:p:m:h')
    for opt, value in options:
        if opt == '-h':
            print_usage()
            sys.exit(0)
        elif opt == '-s':
            device_id = value
        elif opt == '-p':
            port = int(value)
        elif opt == '-m':
            device_type = value

    sampler = ActionSampler(device_id, device_type)

    threading.Thread(target=http_server, args=(port,), name='http_server', daemon=True).start()

    LOG.info('==== action_sampler is initializing ====')
    if sampler.init():
        LOG.info('==== action_sampler is going to run ====')
        try:
            sampler.run()
        finally:
            sampler.finish()
            LOG.info('Finished!')
    else:
        LOG.error('==== action_sampler init failed! ====')

if __name__ == '__main__':
    try:
        main()
    finally:
        if is_windows:
            unhook_all()
