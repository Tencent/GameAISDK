# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import re
import time
import subprocess
import platform
from APIDefine import *
from .ADBDevice import Device

class ADBClient(object):
    __adb_cmd = None

    def __init__(self, host='127.0.0.1', port=5037):
        """
        Args:
            - host: adb server host, default 127.0.0.1
            - port: adb server port, default 5037
        """
        self._host = host or '127.0.0.1'
        self._port = port or 5037

    @property
    def server_host(self):
        return self._host
    
    @classmethod
    def adb_path(cls):
        """return adb binary full path"""
        # if cls.__adb_cmd is None:
        #     if "ANDROID_HOME" in os.environ:
        #         filename = "adb"
        #         adb_dir = os.path.join(os.environ["ANDROID_HOME"], "platform-tools")
        #         adb_cmd = os.path.join(adb_dir, filename)
        #         if not os.path.exists(adb_cmd):
        #             raise EnvironmentError(
        #                 "Adb not found in $ANDROID_HOME/platform-tools path: %s." % adb_dir)
        #     else:
        #         import distutils
        #         if "spawn" not in dir(distutils):
        #             import distutils.spawn
        #         adb_cmd = distutils.spawn.find_executable("adb")
        #         if adb_cmd:
        #             adb_cmd = os.path.realpath(adb_cmd)
        #         else:
        #             raise EnvironmentError("$ANDROID_HOME environment not set.")
        #     cls.__adb_cmd = adb_cmd
        # __dir__ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cls.__adb_cmd = ADB_CMD
        return cls.__adb_cmd

    @property    
    def _host_port_args(self):
        args = []
        if self._host and self._host != '127.0.0.1':
            args += ['-H', self._host]
        if self._port:
            args += ['-P', str(self._port)]
        return args

    def raw_cmd(self, *args, **kwargs):
        '''adb command. return the subprocess.Popen object.'''
        cmds = [self.adb_path()] + self._host_port_args + list(args)
        kwargs['stdout'] = kwargs.get('stdout', subprocess.PIPE)
        kwargs['stderr'] = kwargs.get('stderr', subprocess.PIPE)
        return subprocess.Popen(cmds, **kwargs)

    def run_cmd(self, *args, **kwargs):
        p = self.raw_cmd(*args, **kwargs)
        return p.communicate()[0].decode('utf-8', 'ignore').replace('\r\n', '\n')

    def devices(self):
        '''get a dict of attached devices. key is the device serial, value is device name.'''
        out = self.run_cmd('devices') #subprocess.check_output([self.adb_path(), 'devices']).decode("utf-8")
        if 'adb server is out of date' in out:
            out = self.run_cmd('devices')
        match = "List of devices attached"
        index = out.find(match)
        if index < 0:
            raise EnvironmentError("adb is not working.")
        return dict([s.split("\t") for s in out[index + len(match):].strip().splitlines() 
                if s.strip() and not s.strip().startswith('*')])

    def version(self):
        '''
        Get version of current adb
        Return example:
            [u'1.0.32', u'1', u'0', u'32']
        '''
        '''adb version'''
        match = re.search(r"(\d+)\.(\d+)\.(\d+)", self.run_cmd("version"))
        return [match.group(i) for i in range(4)]

    def get_serial(self):
        devices = self.devices()
        if devices:
            if len(devices) is 1:
                serial = list(devices.keys())[0]
            else:
                raise EnvironmentError("Multiple devices attached but default android serial not set.")
        else:
            raise EnvironmentError("Device not attached.")

        if devices[serial] != 'device':
            raise EnvironmentError("Device(%s) is not ready. status(%s)." %
                (serial, devices[serial]))

        return serial

    def device(self, serial=None):
        devices = self.devices()
        if not serial:
            if devices:
                if len(devices) is 1:
                    serial = list(devices.keys())[0]
                else:
                    raise EnvironmentError("Multiple devices attached but default android serial not set.")
            else:
                raise EnvironmentError("Device not attached.")
        else:
            if serial not in devices:
                raise EnvironmentError("Device(%s) not attached." % serial)

        if devices[serial] != 'device':
            raise EnvironmentError("Device(%s) is not ready. status(%s)." % 
                (serial, devices[serial]))
        return Device(self, serial)

    def connect(self, addr):
        '''
        Call adb connect
        Return true when connect success
        '''
        if addr.find(':') == -1:
            addr += ':5555'
        output = self.run_cmd('connect', addr)
        return 'unable to connect' not in output

    def disconnect(self, addr):
        ''' disconnect device '''
        return self.raw_cmd('disconnect', addr).wait()

    def forward_list(self):
        '''
        adb forward --list
        TODO: not tested
        '''
        version = self.version()
        if int(version[1]) <= 1 and int(version[2]) <= 0 and int(version[3]) < 31:
            raise EnvironmentError("Low adb version.")
        lines = self.run_cmd("forward", "--list").strip().splitlines()
        return [line.strip().split() for line in lines]

    def forward(self, serial, local_port, remote_port=None):
        '''
        adb port forward. return local_port
        TODO: not tested
        '''
        # Shift args, because remote_port is required while local_port is optional
        if remote_port is None:
            remote_port, local_port = local_port, None
            print(serial, remote_port, local_port)
            self.raw_cmd("-s", serial, "forward", "tcp:%d" % local_port, "tcp:%d" % remote_port).wait()
            return local_port


if __name__ == '__main__':
    adb = ADBClient()
    # print adb.devices()
    print('adb version: {0}'.format(adb.version()[0]))

    dev = adb.device()

    print('is locked: {0}'.format(dev.is_locked()))
    dev.wake()
    dev.unlock()

    print('is screen on: {0}'.format(dev.is_screen_on()))

    # package_name = 'com.tencent.pao'
    # dev.is_app_running(package_name)

    app = dev.current_app()
    curr_pkg = app.get('package')
    curr_act = app.get('activity')
    print('current app: {0}/{1}'.format(curr_pkg, curr_act))

    print('battery: {0}/100'.format(dev.battery()))
    print('temperature: {0} degree'.format(dev.temperature()))

    short_side, long_side= dev.wmsize()
    print('screen size: {0} X {1}'.format(short_side, long_side))
    # dev.launch_app(package_name='com.tencent.pao', activity_name='.BreezeGame')
    # dev.install_busybox()
    # time.sleep(5)
    # cpu_usage = dev.cpu_usage(package_name=app.get('package'))
    # mem_usage = dev.mem_usage(package_name=app.get('package'))
    # print 'dumpsys cpu usage: {0} %'.format(cpu_usage)
    # print 'dumpsys memory usage: {0} MB'.format(round(float(mem_usage)/1024, 1))

    cpu_usage, mem_usage = dev.cpu_mem_usage_with_top(package_name=curr_pkg)
    print('top cpu usage: {0} %'.format(cpu_usage))
    print('top memory usage: {0} MB'.format(round(float(mem_usage)/1024, 1)))

    # dev.fps_init()
    # # time.sleep(1)
    # count = 10
    # while count > 0:
    #     fps = dev.fps()
    #     print('fps: {0}'.format(fps))
    #     time.sleep(1)
    #     count -= 1

    # dev.fps_finish()

    # dev.bind_rotation(1)
    res = dev.device_hardware()
    print(res)
