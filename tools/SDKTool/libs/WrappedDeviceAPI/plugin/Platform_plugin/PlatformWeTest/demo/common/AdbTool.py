# -*- coding: UTF-8 -*-
__author__ = 'minhuaxu'

import logging
import os
import re
import subprocess
import pathlib

logger = logging.getLogger(__name__)

class AdbTool(object):
    def __init__(self, serial=None, adb_server_host=None, adb_server_port=None):
        self.__adb_cmd = None

        self.default_serial = serial if serial else os.environ.get("ANDROID_SERIAL", None)
        self.adb_server_host = str(adb_server_host if adb_server_host else 'localhost')
        self.adb_server_port = str(adb_server_port if adb_server_port else '5037')

    def adb(self):
        if self.__adb_cmd is None:
            import distutils
            if "spawn" not in dir(distutils):
                import distutils.spawn
            adb_cmd = distutils.spawn.find_executable("adb")
            if adb_cmd:
                adb_cmd = os.path.realpath(adb_cmd)

            if not adb_cmd and "ANDROID_HOME" in os.environ:
                # 尝试通过ANDROID_HOME环境变量查找
                filename = "adb.exe" if os.name == 'nt' else "adb"
                adb_cmd = os.path.join(os.environ["ANDROID_HOME"], "platform-tools", filename)
                if not os.path.exists(adb_cmd):
                    raise EnvironmentError(
                        "Adb not found in $ANDROID_HOME path: %s." % os.environ["ANDROID_HOME"])

            self.__adb_cmd = adb_cmd
        return self.__adb_cmd

    def cmd(self, *args):
        '''adb command, add -s serial by default. return the subprocess.Popen object.'''
        serial = self.device_serial()

        if serial:
            if " " in serial:  # TODO how to include special chars on command line
                serial = "'%s'" % serial

            if False:
                return self.raw_cmd(*["-s", serial] + list(args))
            else:
                return self.raw_cmd(*args)
        else:
            return self.raw_cmd(*args)

    def cmd_wait(self, *args):
        # serial = self.device_serial()
        # cmd = None
        # if serial:
        #     if " " in serial:  # TODO how to include special chars on command line
        #         serial = "'%s'" % serial
        #         cmd = self.raw_cmd(*["-s", serial] + list(args))
        #     else:
        #         cmd = self.raw_cmd(*args)
        # else:
        #     cmd = self.raw_cmd(*args)
        cmd = self.raw_cmd(*args)
        cmd.wait()
        erro, out = cmd.communicate()
        print(erro, out)
        return out

    def raw_cmd(self, *args):

        '''adb command. return the subprocess.Popen object.'''
        cmd_line = [self.adb()] + list(args)
        if os.name != "nt":
            cmd_line = [" ".join(cmd_line)]
        print(cmd_line)
        return subprocess.Popen(cmd_line, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def device_serial(self):

        if not self.default_serial:
            devices = self.devices()
            if devices:
                if len(devices) is 1:
                    self.default_serial = list(devices.keys())[0]
                else:
                    raise EnvironmentError("Multiple devices attached but default android serial not set.")
            else:
                raise EnvironmentError("Device not attached.")
        return self.default_serial

    def devices(self):
        '''get a dict of attached devices. key is the device serial, value is device name.'''
        out = self.raw_cmd("devices").communicate()[0].decode("utf-8")
        match = "List of devices attached"
        index = out.find(match)
        if index < 0:
            raise EnvironmentError("adb is not working.")
        return dict([s.split("\t") for s in out[index + len(match):].strip().splitlines() if s.strip()])

    def forward(self, local_port, device_port):

        '''adb port forward. return 0 if success, else non-zero.'''
        return self.cmd("forward", "tcp:{0}".format(local_port), "tcp:{0}".format(device_port)).wait()

    def forward_list(self):
        '''list all forward socket connections.'''

        version = self.version()
        if int(version[1]) <= 1 and int(version[2]) <= 0 and int(version[3]) < 31:
            raise EnvironmentError("Low adb version.")
        lines = self.raw_cmd("forward", "--list").communicate()[0].decode("utf-8").strip().splitlines()
        return [line.strip().split() for line in lines]

    def push(self, src, dest):
        '''push file to phone'''
        return self.cmd("push", src, dest)

    def version(self):
        '''adb version'''
        match = re.search(r"(\d+)\.(\d+)\.(\d+)", self.raw_cmd("version").communicate()[0].decode("utf-8"))
        return [match.group(i) for i in range(4)]
