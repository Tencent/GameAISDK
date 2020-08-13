# -*- coding: utf-8 -*-

import os
try:
  import Queue
except ImportError:
  import queue as Queue

import subprocess
import threading
import time
import traceback

__dir__ = os.path.dirname(os.path.abspath(__file__))

class RotationWatcher(object):

    __rotation = 0
    __watcher_process = None

    def open_rotation_watcher(self, on_rotation_change=None):
        package_name = 'jp.co.cyberagent.stf.rotationwatcher'
        out = self.raw_cmd('shell', 'pm', 'list', 'packages', stdout=subprocess.PIPE).communicate()[0].decode('utf-8', 'ignore').replace('\r\n', '\n')
        if package_name not in out:
            apkpath = os.path.join(__dir__, '..', 'vendor', 'RotationWatcher.apk')
            print('install rotationwatcher... {0}'.format(apkpath))
            if 0 != self.raw_cmd('install', '-r', '-t', apkpath).wait():
                print('install rotationwatcher failed.')
                return

        if self.__watcher_process is not None:
            self.__watcher_process.kill()

        out = self.raw_cmd('shell', 'pm', 'path', package_name, stdout=subprocess.PIPE).communicate()[0].decode('utf-8', 'ignore').replace('\r\n', '\n')
        path = out.strip().split(':')[-1]
        p = self.raw_cmd('shell', 
            'CLASSPATH="%s"' % path, 
            'app_process',
            '/system/bin',
            'jp.co.cyberagent.stf.rotationwatcher.RotationWatcher', 
            stdout=subprocess.PIPE)
        self.__watcher_process = p

        queue = Queue.Queue()

        def _pull():
            while True:
                line = p.stdout.readline().strip()
                if not line:
                    if p.poll() is not None:
                        print('rotationwatcher stopped')
                        break
                    continue
                queue.put(line)

        t = threading.Thread(target=_pull)
        t.setDaemon(True)
        t.start()

        def listener(value):
            try:
                self.__rotation = int(value)/90
            except:
                return
            if callable(on_rotation_change):
                on_rotation_change(self.__rotation)

        def _listen():
            while True:
                try:
                    time.sleep(0.005)
                    line = queue.get_nowait()
                    listener(line)
                except Queue.Empty:
                    if p.poll() is not None:
                        break
                    continue
                except:
                    traceback.print_exc()

        t = threading.Thread(target=_listen)
        t.setDaemon(True)
        t.start()

    def GetRotation(self):
        return self.__rotation
