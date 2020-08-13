# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import re
import collections
import time
import math
from .surface_stats_collector import SurfaceStatsCollector

_DISPLAY_RE = re.compile(
    r'.*DisplayViewport{valid=true, .*orientation=(?P<orientation>\d+), .*deviceWidth=(?P<width>\d+), deviceHeight=(?P<height>\d+).*')
_PROP_PATTERN = re.compile(r'\[(?P<key>.*?)\]:\s*\[(?P<value>.*)\]')

__dir__ = os.path.dirname(os.path.abspath(__file__))
VENDOR_BASE_DIR = __dir__ + '/../vendor/'
BUSYBOX_BASE_DIR = VENDOR_BASE_DIR + '/busybox/'

class Device(object):
    Display = collections.namedtuple('Display', ['width', 'height', 'rotation'])
    Package = collections.namedtuple('Package', ['name', 'path'])

    def __init__(self, client, serial):
        ''' TODO: client change to host, port '''
        self._client = client
        self._serial = serial
        self._collector = None
        self.cpuIdx = None
        self.memIdx = None
        self._hwInfos = None

    def __del__(self):
        self.fps_finish()

    @property
    def serial(self):
        return self._serial
    
    def raw_cmd(self, *args, **kwargs):
        args = ['-s', self._serial] + list(args)
        return self._client.raw_cmd(*args, **kwargs)

    def run_cmd(self, *args, **kwargs):
        """
        Unix style output, already replace \r\n to \n

        Args:
            - timeout (float): timeout for a command exec
        """
        timeout = kwargs.pop('timeout', None)
        p = self.raw_cmd(*args, **kwargs)
        comm = p.communicate()
        stdoutdata = comm[0].decode('utf-8', 'ignore').replace('\r\n', '\n')
        if len(stdoutdata) > 0:
            return stdoutdata
        else:
            stderrdata = comm[1].decode('utf-8', 'ignore').replace('\r\n', '\n')
            return stderrdata

    def shell(self, *args, **kwargs):
        """
        Run command `adb shell`
        """
        args = ['shell'] + list(args)
        return self.run_cmd(*args, **kwargs)

    def keyevent(self, key):
        ''' Call: adb shell input keyevent $key '''
        self.shell('input', 'keyevent', key)

    def remove(self, filename):
        """ 
        Remove file from device
        """
        output = self.shell('rm', filename)
        # any output means rm failed.
        return False if output else True

    def install_wetest_tools(self):
        target_path = VENDOR_BASE_DIR + "/DialogHandler.jar"
        self.push(source_file=target_path)
        target_path = VENDOR_BASE_DIR + "/wetest_dialog_config.properties"
        self.push(source_file=target_path)

    def install(self, filename):
        """
        TOOD(ssx): Install apk into device, show progress

        Args:
            - filename(string): apk file path
        """
        self.install_wetest_tools()
        uiautomator_process = self.raw_cmd('shell',
                                           'uiautomator',
                                           'runtest',
                                           'DialogHandler.jar',
                                           '-c',
                                           'com.tencent.wetest.accessibility.Stub')

        output = self.run_cmd('install', '-r', '-t', '-d', '-g', filename)
        uiautomator_process.kill()
        if output.startswith('Success'):
            return True
        else:
            return False

    def uninstall(self, package_name, keep_data=False):
        """
        Uninstall package

        Args:
            - package_name(string): package name ex: com.example.demo
            - keep_data(bool): keep the data and cache directories
        """
        if keep_data:
            return self.run_cmd('uninstall', '-k', package_name)
        else:
            return self.run_cmd('uninstall', package_name)

    def push(self, source_file, target_file='/data/local/tmp'):
        self.run_cmd('push', source_file, target_file)

    def pull(self, source_file, target_file=None):
        if target_file is None:
            raise RuntimeError('Not supported now')
        self.run_cmd('pull', source_file, target_file)

    def screenshot(self, savedPath='/data/local/tmp/screenshot.png'):
        self.shell('screencap', '-p', str(savedPath))

    def uiautomatorDump(self, compressed=True):
        if compressed:
            self.shell('uiautomator', 'dump', '--compressed')
        else:
            self.shell('uiautomator', 'dump')

    def properties(self):
        '''
        Android Properties, extracted from `adb shell getprop`

        Returns:
            dict of props, for
            example:
                {'ro.bluetooth.dun': 'true'}
        '''
        props = {}
        for line in self.shell(['getprop']).splitlines():
            m = _PROP_PATTERN.match(line)
            if m:
                props[m.group('key')] = m.group('value')
        return props

    def packages(self):
        """
        Show all packages
        """
        pattern = re.compile(r'package:(/[^=]+\.apk)=([^\s]+)')
        packages = []
        for line in self.shell('pm', 'list', 'packages', '-f').splitlines():
            m = pattern.match(line)
            if not m:
                continue
            path, name = m.group(1), m.group(2)
            packages.append(self.Package(name, path))
        return packages

    def click(self, x, y):
        '''
        same as adb -s ${SERIALNO} shell input tap x y
        FIXME(ssx): not tested on horizontal screen
        '''
        self.shell('input', 'tap', str(x), str(y))

    def swipe(self, sx, sy, ex, ey, durationMS=50):
        self.shell('input', 'swipe', str(sx), str(sy), str(ex), str(ey), str(durationMS))

    def input_text(self, text):
        self.shell('input', 'text', str(text))

    def forward(self, local_port, remote_port):
        '''
        adb port forward. return local_port
        TODO: not tested
        '''
        return self._client.forward(self.serial, local_port, remote_port)

    def is_locked(self):
        """
        Returns:
            - lock state(bool)
        Raises:
            RuntimeError
        """
        # _lockScreenRE = re.compile('mShowingLockscreen=(true|false)')
        _lockScreenRE = re.compile('isStatusBarKeyguard=(true|false)')
        m = _lockScreenRE.search(self.shell('dumpsys', 'window', 'policy'))
        if m:
            return (m.group(1) == 'true')
        raise RuntimeError("Couldn't determine screen lock state")

    def is_screen_on(self):
        '''
        Checks if the screen is ON.
        Returns:
            True if the device screen is ON
        Raises:
            RuntimeError
        '''

        _screenOnRE = re.compile('mScreenOnFully=(true|false)')
        m = _screenOnRE.search(self.shell('dumpsys', 'window', 'policy'))
        if m:
            return (m.group(1) == 'true')
        raise RuntimeError("Couldn't determine screen ON state")

    def wake(self):
        """
        Wake up device if device locked
        """
        if not self.is_screen_on():
            self.keyevent('WAKEUP')

    def is_keyboard_shown(self):
        dim = self.shell('dumpsys', 'input_method')
        if dim:
            # FIXME: API >= 15 ?
            return "mInputShown=true" in dim
        return False

    def current_app(self):
        """
        Return: dict(package, activity, pid?)
        Raises:
            RuntimeError
        """
        # try: adb shell dumpsys window windows
        _focusedRE = re.compile('mFocusedApp=.*ActivityRecord{\w+ \w+ (?P<package>.*)/(?P<activity>.*) .*')
        m = _focusedRE.search(self.shell('dumpsys', 'window', 'windows'))
        if m:
            tmpActivity = m.group('activity')
            if tmpActivity.startswith('.'):
                tmpActivity = m.group('package') + tmpActivity
            return dict(package=m.group('package'), activity=tmpActivity)

        # try: adb shell dumpsys activity top
        _activityRE = re.compile(r'ACTIVITY (?P<package>[^/]+)/(?P<activity>[^/\s]+) \w+ pid=(?P<pid>\d+)')
        m = _activityRE.search(self.shell('dumpsys', 'activity', 'top'))
        if m:
            tmpActivity = m.group('activity')
            if tmpActivity.startswith('.'):
                tmpActivity = m.group('package') + tmpActivity
            return dict(package=m.group('package'), activity=tmpActivity, pid=int(m.group('pid')))
        raise RuntimeError("Couldn't get focused app")

    def is_app_running(self, package_name):
        res = self.shell('ps')
        if res:
            # FIXME: API >= 15 ?
            return package_name in res
        return False

    def cpu_usage(self, package_name):
        # _cpuinfoRE = re.compile(package_name + r':\s(?P<cpuusage>\d+([.]{1}\d+){0,1})% user')
        _cpuinfoRE = re.compile(r'\D(?P<cpuusage>\d+([.]{1}\d+){0,1})%\s\d+/' + package_name + ':\s')
        m = _cpuinfoRE.search(self.shell('dumpsys', 'cpuinfo'))
        if m:
            return float(m.group('cpuusage'))
        return -1
        # raise RuntimeError("Couldn't get cpu usage")

    def mem_usage(self, package_name):
        _meminfoRE = re.compile(r'TOTAL\s*(?P<memoryused>\d+)')
        m = _meminfoRE.search(self.shell('dumpsys', 'meminfo', package_name))
        if m:
            return float(m.group('memoryused'))
        return -1
        # raise RuntimeError("Couldn't get memory usage")

    def temperature(self):
        _temperatureRE = re.compile(r'\s*temperature:\s*(?P<temperature>\d+)')
        m = _temperatureRE.search(self.shell('dumpsys', 'battery'))
        if m:
            return float(m.group('temperature')) / 10.
        return -1

    def battery(self):
        _batteryRE = re.compile(r'\s*level:\s*(?P<battery>\d+)')
        m = _batteryRE.search(self.shell('dumpsys', 'battery'))
        if m:
            return m.group('battery')
        return -1

    def wmsize(self):
        _wmsizeRE = re.compile(r'Physical size:\s(?P<height>\d+)x(?P<width>\d+)')
        m = _wmsizeRE.search(self.shell('wm', 'size'))
        if m:
            return (int(m.group('height')), int(m.group('width')))
        raise RuntimeError("Couldn't get window size")

    def launch_app(self, package_name, activity_name):
        if activity_name.startswith('com.'):
            fullActivityName = package_name + '/' + activity_name
        elif activity_name.startswith('.'):
            fullActivityName = package_name + '/' + package_name + activity_name
        else:
            fullActivityName = package_name + '/' + package_name + '.' + activity_name
        self.shell('am', 'start', '-n', fullActivityName)

    def kill_app(self, package_name):
        self.shell('am', 'force-stop', package_name)

    def clear_app_data(self, package_name):
        self.shell('pm', 'clear', package_name)

    def disable_all_ime(self):
        for line in self.shell('ime', 'list', '-s').splitlines():
            self.shell('ime', 'disable', line)

    def enable_all_ime(self):
        for line in self.shell('ime', 'list', '-s').splitlines():
            self.shell('ime', 'enable', line)

    def install_busybox(self):
        abi = self.shell('getprop', 'ro.product.cpu.abi').strip()

        # push busybox file
        target_path = BUSYBOX_BASE_DIR + "/busybox"
        self.raw_cmd('push', target_path, '/data/local/tmp').wait()
        self.shell('chmod', '0755', '/data/local/tmp/busybox')

    def cpu_usage_with_busybox(self, package_name):
        res = self.shell('/data/local/tmp/busybox', 'top', '-n1',
                         '|', '/data/local/tmp/busybox', 'grep', package_name)
        if res:
            toplist = res.split()
            if toplist[-1] == package_name:
                cpuusage = toplist[-2]
                return cpuusage
        return -1

    def cpu_mem_usage_with_top(self, package_name):
        if self.cpuIdx is None:
            out = self.shell('top -n 1 -d 0 | grep PID')
            self.cpuIdx = out.split().index('CPU%')
            self.memIdx = out.split().index('RSS')
        out = self.shell('top -n 1 -d 0 | grep', package_name)
        if out:
            lines = out.splitlines()
            cpuusage = 0
            memusage = 0
            for line in lines:
                outlist = line.split()
                cpuusage += float(outlist[self.cpuIdx][0:-1])
                if outlist[-1] == package_name:
                    memusage = float(outlist[self.memIdx][0:-1])
            return cpuusage, memusage
        return -1, -1

    def unlock(self):
        if self.is_locked():
            self.shell('input swipe 300 1000 300 0')

    def close_screen(self):
        if self.is_screen_on():
            self.keyevent('SLEEP')

    def fps_init(self):
        app = self.current_app()
        package_name = app.get('package')
        activity_name = app.get('activity')
        if self._collector is None:
            if activity_name.startswith('com.'):
                fullActivityName = package_name + '/' + activity_name
            else:
                fullActivityName = package_name + '/' + package_name + activity_name

            wrappedSurfaceViewName = '"SurfaceView - ' + fullActivityName + '"'
            wrappedFullActivityName = '"' + fullActivityName + '"'
            out = self.shell('dumpsys SurfaceFlinger | grep ' + wrappedSurfaceViewName)
            if out:
                self._collector = SurfaceStatsCollector(self, wrappedSurfaceViewName)
            else:
                wrappedSurfaceViewName = "SurfaceView"
                out = self.shell('dumpsys SurfaceFlinger | grep ' + wrappedSurfaceViewName)
                if out:
                    self._collector = SurfaceStatsCollector(self, wrappedSurfaceViewName)
                else:
                    self._collector = SurfaceStatsCollector(self, wrappedFullActivityName)
            self._collector.DisableWarningAboutEmptyData()
            self._collector.Start()
            self._fps = 0

    def fps(self):
        results = self._collector.SampleResults()
        if not results:
            pass
        else:
            for item in results:
                if item.value is not None and item.name == 'avg_surface_fps':
                    self._fps = item.value
        return self._fps

    def fps_finish(self):
        if self._collector is not None:
            self._collector.Stop()
            self._collector = None

    def fps_with_service(self):
        _frameRE = re.compile(r'Result: Parcel\((?P<frameCount>[0-9a-fA-F]{8})\s+')
        out = self.shell('su -c "service call SurfaceFlinger 1013;"')
        m = _frameRE.search(out)
        if m:
            return (int(m.group('frameCount'), 16))
        raise RuntimeError("Couldn't get frame count"+out)

    def forbid_rotation(self):
        self.shell('content insert --uri content://settings/system --bind name:s:accelerometer_rotation --bind value:i:0')

    def bind_rotation(self, rotation):
        self.forbid_rotation()
        cmds = 'content insert --uri content://settings/system --bind name:s:user_rotation --bind value:i:' + str(rotation)
        self.shell(cmds)

    def device_hardware(self):
        if self._hwInfos is None:
            self._hwInfos = {}

            out = self.shell('getprop', 'ro.product.brand')
            if out:
                lines = out.splitlines()
                self._hwInfos['brand'] = lines[0]

            out = self.shell('getprop', 'ro.product.model')
            if out:
                lines = out.splitlines()
                self._hwInfos['model'] = lines[0]

            # out = self.shell('getprop', 'ro.board.platform')
            # if out:
            #     lines = out.splitlines()
            #     self._hwInfos['board'] = lines[0]

            out = self.shell('getprop', 'ro.build.version.release')
            if out:
                lines = out.splitlines()
                self._hwInfos['version'] = 'Android %s' % lines[0]

            out = self.shell('cat /proc/cpuinfo | grep processor')
            if out:
                lines = out.splitlines()
                self._hwInfos['coresNum'] = len(lines)

            # out = self.shell('cat /sys/devices/system/cpu/cpufreq/all_time_in_state')
            # if out:
            #     lines = out.splitlines()
            #     words = lines[-1].split()
            #     frequency = float(words[0]) / 1000 / 1000
            #     print frequency
            #     self._hwInfos['maxFrequency'] = '%.2f GHz' % frequency

            out = self.shell('cat /proc/meminfo')
            if out:
                lines = out.splitlines()
                words = lines[0].split()
                memTotal = int(math.ceil(float(words[1]) / 1024 / 1024))
                self._hwInfos['memorySize'] = memTotal * 1024

            out = self.shell('wm size')
            if out:
                lines = out.splitlines()
                words = lines[0].split()
                self._hwInfos['resolution'] = words[2]

        return self._hwInfos
