# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import argparse
import os
import sys
import shutil
import subprocess
import tempfile
import functools
import logging

__dir__ = os.path.dirname(os.path.abspath(__file__))
MINITOUCH_BASE_DIR = __dir__ + '/../../vendor/minitouch/'

LOG = logging.getLogger('minitouch')

def check_output(cmdstr, shell=True):
    output = subprocess.check_output(cmdstr, stderr=subprocess.STDOUT, shell=shell).decode('utf-8', 'ignore').replace('\r\n', '\n')
    return output

def run_adb(*args, **kwargs):
    cmds = ['adb']
    serialno = kwargs.get('serialno', None)
    if serialno:
        cmds.extend(['-s', serialno])
    host = kwargs.get('host')
    if host:
        cmds.extend(['-H', host])
    port = kwargs.get('port')
    if port:
        cmds.extend(['-P', str(port)])
    cmds.extend(args)
    cmds = map(str, cmds)
    cmdline = subprocess.list2cmdline(cmds)
    try:
        return check_output(cmdline, shell=True)
    except Exception as e:
        raise EnvironmentError('run cmd: {} failed. {}'.format(cmdline, e))


def InstallMinitouch(serialno=None, host=None, port=None):
    LOG.info("Minitouch install started!")
    
    adb = functools.partial(run_adb, serialno=serialno, host=host, port=port)

    LOG.info("Make temp dir ...")
    tmpdir = tempfile.mkdtemp(prefix='ins-minitouch-')
    LOG.debug(tmpdir)
    try:
        # Get device abi and sdk version
        LOG.info("Retrive device information ...")
        abi = adb('shell', 'getprop', 'ro.product.cpu.abi').strip()
        sdk = adb('shell', 'getprop', 'ro.build.version.sdk').strip()

        # push minitouch so file
        target_path = MINITOUCH_BASE_DIR + "libs/" + abi + "/minitouch"
        LOG.info("Push minitouch to device ....")
        adb('push', target_path, '/data/local/tmp')
        adb('shell', 'chmod', '0755', '/data/local/tmp/minitouch')

        LOG.info("Checking [dump device info] ...")
        # print adb('shell', '/data/local/tmp/minitouch -h')
        LOG.info("Minitouch install finished !")

    except Exception as e:
        LOG.error('error: %s', e)
    finally:
        if tmpdir:
            LOG.info("Cleaning temp dir")
            shutil.rmtree(tmpdir)

