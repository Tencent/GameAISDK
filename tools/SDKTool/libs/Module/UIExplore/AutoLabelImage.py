# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import sys
import time
import signal
import logging
import subprocess
from libs.CommonDialog import *
from libs.utils import GetfilesCount

platform = sys.platform


class AutoLabelImage(object):
    def __init__(self, canvas, zoomWidget, ui):
        self.__logger = logging.getLogger('sdktool')
        self.__zoomWidget = zoomWidget
        self.__canvas = canvas
        self.__ui = ui
        self.__autoLabelPath = None
        # path to RefineDet
        fileDir = os.path.dirname(os.path.abspath(__file__))
        self.__refineDetPath = os.path.join(fileDir, "../../../../../Modules/RefineDet/")

    def SetPath(self, path):
        self.__autoLabelPath = path

    def Label(self):
        imageCount = GetfilesCount(self.__autoLabelPath)
        if imageCount <= 0:
            text = "failed, no image in {}, please check".format(self.__autoLabelPath)
            dialog = CommonDialog(title="AutoLabelImage", text=text)
            dialog.popUp()
            return
        # ...................Auto label subprocess begin..................
        currentPath = os.getcwd()
        # os.chdir("bin/RefineDet/")
        if not os.path.exists(self.__refineDetPath):
            raise Exception("RefineDet Path {} is not exist".format(self.__refineDetPath))

        os.chdir(self.__refineDetPath)
        args = ['python', 'detect_mutilple_images.py', '--test_images', self.__autoLabelPath]
        if platform == 'win32':
            if hasattr(os.sys, 'winver'):
                pro = subprocess.Popen(args, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
            else:
                pro = subprocess.Popen(args)
        else:
            cmd = "python detect_mutilple_images.py --test_images {}".format(self.__autoLabelPath)
            pro = subprocess.Popen(cmd,
                                   shell=True, preexec_fn=os.setsid)
        os.chdir(currentPath)

        if pro is None:
            self.__logger.error("open action sample failed")
            return
        else:
            self.__logger.info('Run ActionSample Create PID: {} SubProcess'.format(pro.pid))
        # ...................Auto label subprocess end..................

        self.__canvas.CreateProcessbar("自动标签", "处理中", 0, imageCount)

        jsonCount = GetfilesCount(self.__autoLabelPath, ".json")
        while jsonCount < imageCount:
             # jsonCount += 1
             self.__logger.debug("josn count is {}".format(jsonCount))
             self.__canvas.SetBarCurValue(jsonCount)
             QApplication.processEvents()
             time.sleep(0.5)
             jsonCount = GetfilesCount(self.__autoLabelPath, ".json")

        self.__canvas.CloseBar()
        QMessageBox.information(self.__canvas, "提示", "处理完成")

        self.__logger.info("kill process {}".format(pro.pid))
        if platform == 'win32':
            if hasattr(os.sys, 'winver'):
                # os.kill(self.actionSamplePro.pid, signal.SIGINT)
                os.kill(pro.pid, signal.CTRL_BREAK_EVENT)
            else:
                pro.send_signal(signal.SIGTERM)
        else:
            os.killpg(pro.pid, signal.SIGINT)