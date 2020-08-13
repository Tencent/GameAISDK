#!/usr/bin/env python
# coding: utf-8

import time
import logging
import pathlib
from .common.AdbTool import AdbTool
from concurrent.futures import ThreadPoolExecutor, wait

logger = logging.getLogger(__name__)

class Initializer:
    TOUCH_SEVER_PORT = 1111
    CLOUD_SCREEN_PORT = 1113

    def __init__(self, resource_dir, serial=None):
        self.__adb = AdbTool(serial)
        self.__resource_dir = resource_dir
        self.__thread_pool = ThreadPoolExecutor(max_workers=2)
        self.__touch_future = None
        self.__cloudscreen_futrue = None

    def __get_abi_sdk(self):
        abi = self.__adb.cmd('shell',
                             'getprop',
                             'ro.product.cpu.abi').communicate()[0].decode('utf-8', 'ignore').strip()
        sdk = self.__adb.cmd('shell',
                             'getprop',
                             'ro.build.version.sdk').communicate()[0].decode('utf-8', 'ignore').strip()
        logger.info("adi={}, sdk={}".format(abi, sdk))
        return abi, sdk

    def __install_touch_server(self):
        try:
            logger.info("Install touch server...")
            abi, _ = self.__get_abi_sdk()

            file_path = "{}/touchserver/binary/{}/touchserver".format(self.__resource_dir, abi)
            if not pathlib.Path(file_path).is_file():
                raise FileNotFoundError("touchserver is not exsit")

            logger.info("Push touch server to device")
            self.__adb.cmd_wait('push', file_path, '/data/local/tmp')
            self.__adb.cmd_wait('shell', 'chmod', '0755', '/data/local/tmp/touchserver')

            logger.info("Install touch server complete")
        except Exception as e:
            logger.error('error: %s', e)
            raise e

    def __install_cloudscreen_server(self):
        try:
            logger.info("Install cloud screen...")
            abi, sdk = self.__get_abi_sdk()
            so_path = "{}/cloudscreen/libs/android-{}/{}/cloudscreen.so".format(self.__resource_dir, sdk, abi)
            if not pathlib.Path(so_path).is_file():
                raise FileNotFoundError("cloudscreen.so is not exsit")
            self.__adb.cmd_wait('push', so_path, '/data/local/tmp')

            binary_path = "{}/cloudscreen/binary/{}/cloudscreen".format(self.__resource_dir, abi)
            if not pathlib.Path(binary_path).is_file():
                raise FileNotFoundError("cloudscreen.so is not exsit")

            logger.info("Push touch server to device")
            self.__adb.cmd_wait('push', binary_path, '/data/local/tmp')
            self.__adb.cmd_wait('shell', 'chmod', '0755', '/data/local/tmp/cloudscreen')

            logger.info("Install cloud screen complete")
        except Exception as e:
            logger.error('error: %s', e)
            raise e

    def forward(self, local_port, remote_port):
        if self.__adb.forward(local_port, remote_port) != 0:
            raise Exception("bind {} to {} error:".format(local_port, remote_port))

    def __launch_touchserver(self):
        try:
            logger.info("touchserver run begin...")
            self.__adb.cmd_wait("shell", "/data/local/tmp/touchserver")
            logger.error("touchserver run over")
        except Exception as e:
            logger.error('launch touchserver exception', exc_info=True)

    def __launch_cloudscreen(self):
        try:
            logger.info("cloudscreen run begin...")
            self.__adb.cmd_wait("shell", "LD_LIBRARY_PATH=/data/local/tmp /data/local/tmp/cloudscreen")
            logger.error("cloudscreen run over")
        except Exception as e:
            logger.error('launch cloudscreen exception', exc_info=True)

    def setup(self, install=False):
        if install:
            self.__install_touch_server()
            self.__install_cloudscreen_server()
            self.__adb.cmd_wait("shell", "killall", "touchserver")
            self.__adb.cmd_wait("shell", "killall", "cloudscreen")
            self.__touch_future = (self.__thread_pool.submit(self.__launch_touchserver))
            self.__cloudscreen_futrue = self.__thread_pool.submit(self.__launch_cloudscreen)

        self.forward(self.TOUCH_SEVER_PORT, 25766)
        self.forward(self.CLOUD_SCREEN_PORT, 15666)

        time.sleep(4)

    def wait(self):
        wait([self.__touch_future, self.__cloudscreen_futrue])
