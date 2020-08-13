# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import sys
import zmq
import time
import signal
import shutil
import logging
import threading
import subprocess
import matplotlib.pyplot as plt

from libs.utils import *
from libs.CommonDialog import *
from libs.JsonToRefineDetTxt import *
from libs.Module.UIExplore.canvasUtils import *
from libs.confirmDialog import confirmDialog

platform = sys.platform


BASE_TRAIN_EPOCH = 55


class TrainLogParam(object):
    def __init__(self):
        self.lossx = []
        self.lossy = []
        self.exitPaintLog = False
        self.exitRecvLog = False

    def SetExitPaintLog(self, flag):
        self.exitPaintLog = flag

    def SetExitRecvLog(self, flag):
        self.exitRecvLog = flag

    def SetExit(self, flag):
        self.exitPaintLog = flag
        self.exitRecvLog = flag
        self.lossx.clear()
        self.lossy.clear()

    def IsValid(self):
        return not (self.exitRecvLog or self.exitRecvLog)


class CNNTrainSample(object):
    def __init__(self, samplePath, canvas, zoomWidget, ui):
        self.__trainProcess = None
        self.__trainSamplePath = samplePath
        self.__logger = logging.getLogger('sdktool')
        self.__zoomWidget = zoomWidget
        self.__canvas = canvas
        self.__ui = ui
        # path to RefineDet
        fileDir = os.path.dirname(os.path.abspath(__file__))
        self.__refineDetPath = os.path.join(fileDir, "../../../../../Modules/RefineDet/")
        self.__preDir = os.path.join(self.__refineDetPath, "test_map/pre")
        self.__grdDir = os.path.join(self.__refineDetPath, "test_map/grd")
        self.__resultsDir = os.path.join(self.__refineDetPath, "test_map/results")
        self.__mapPath = os.path.join(self.__refineDetPath, "mAP.jpg")
        self.__weightFile = os.path.join(self.__refineDetPath,
        "weights/Refine_hc2net_version3_320/model/Final_Refine_hc2net_version3_self_dataset.pth")

        context = zmq.Context()
        self.__socket = context.socket(zmq.PULL)
        self.__socket.bind("tcp://*:5558")

        self.__trainParamDict = {}
        self.__paintLogThread = None
        self.__recvLogThread = None
        self.__mapProcess = None
        self.__mapThread = None

        self.__trainLogParam = TrainLogParam()
        self.__trainDlg = confirmDialog(text="正在训练中")
        self._InitTrainDlg()
        self.__lock = threading.Lock()

    def _InitTrainDlg(self):
        self.__trainDlg.GetButtonBox().accepted.connect(self.ReRun)
        self.__trainDlg.GetButtonBox().button(QDialogButtonBox.Ok).setText("重新训练")
        self.__trainDlg.GetButtonBox().button(QDialogButtonBox.Cancel).setText("取消")

    def SetTrainParam(self, paramDict):
        self.__trainParamDict = paramDict

    def SetSamplePath(self, path):
        self.__trainSamplePath = path

    def GetSamplePath(self):
        return self.__trainSamplePath

    def _ClearFiles(self):
        if os.path.isdir(self.__preDir):
            DelFiles(self.__preDir)

        if os.path.isdir(self.__grdDir):
            DelFiles(self.__grdDir)

        if os.path.isdir(self.__resultsDir):
            DelFiles(self.__resultsDir)

        if os.path.exists(self.__mapPath):
            os.remove(self.__mapPath)

    def Run(self):
        if self.__trainProcess is None:
            self.__logger.info("start train")
            self._ClearFiles()
            self.__trainProcess = self._TranSample()
            self._PaintTrainLog()
        else:
            self.__trainDlg.popUp()

    def ReRun(self):
        self.FinishTrain()
        # 最多等待10s钟，等原有的线程退出
        beginWait = time.time()
        while time.time() - beginWait < 10:
            if self.__trainLogParam.IsValid():
                self.__logger.info("train is valid")
                break
            else:
                time.sleep(1)
        self.__canvas.resetState()
        self.Run()

    def _TranSample(self):
        imageCount = GetfilesCount(self.__trainSamplePath)
        if imageCount <= 0:
            text = "failed, no image in {}, please check".format(self.__trainSamplePath)
            dialog = CommonDialog(title="train", text=text)
            dialog.popUp()
            return

        currentPath = os.getcwd()
        if not os.path.exists(self.__refineDetPath):
            raise Exception("refineDetPath: {} is not exist".format(self.__refineDetPath))

        os.chdir(self.__refineDetPath)
        trainDataSet = "train_dataset.txt"
        testDataSet = "test_dataset.txt"
        JonToRefineDetTxt(self.__trainSamplePath, trainDataSet, testDataSet)
        maxEpoch = self.__trainParamDict.get("微调次数") or 5
        maxEpoch = int(maxEpoch) + BASE_TRAIN_EPOCH

        args = ['python', 'train_val.py', '--max_epoch', str(maxEpoch)]

        if platform == 'win32':
            if hasattr(os.sys, 'winver'):
                pro = subprocess.Popen(args, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
            else:
                pro = subprocess.Popen(args)
        else:
            cmd = "python train_val.py --max_epoch {}".format(maxEpoch)
            pro = subprocess.Popen(cmd, shell=True, preexec_fn=os.setsid)
        if pro is None:
            self.__logger.error("open action sample failed")
        else:
            self.__logger.info('Run ActionSample Create PID: {} SubProcess'.format(pro.pid))

        os.chdir(currentPath)
        return pro

    def _SaveWeight(self):
        if not os.path.exists(self.__weightFile):
            raise Exception("weight file is not exist")
        else:
            dstFile = "{}/../Final_Refine_hc2net_version3_self_dataset.pth".format(self.__trainSamplePath)
            shutil.copyfile(self.__weightFile, dstFile)

    def _PaintTrainLog(self):
        self.__ui.textEdit.setPlainText("训练网络模型")
        maxEpoch = self.__trainParamDict.get("微调次数") or 5
        maxEpoch = int(maxEpoch)

        def _PaintLog(trainLogParam, lock):
            font1 = {'family': 'Times New Roman',
                     'weight': 'normal',
                     'size': 23
                     }
            loss_x = trainLogParam.lossx
            loss_y = trainLogParam.lossy
            loss_y.clear()
            loss_x.clear()
            self.__logger.info("************start paint log************")

            while not trainLogParam.exitPaintLog:
                time.sleep(5)
                lock.acquire()
                plt.cla()
                if len(loss_x) > 0:
                    curEpoch = int(loss_x[-1])
                    plt.xticks(np.arange(min(loss_x), max(loss_x) + 1, step=1))
                else:
                    curEpoch = 1

                plt.plot(loss_x, loss_y, '', c='g')
                self.__logger.debug("paint lossx {}".format(loss_x))
                self.__logger.debug("paint lossy {}".format(loss_y))
                lock.release()
                # if loss_x[-1] < maxEpoch:
                if curEpoch < maxEpoch:
                    plt.title('train(epoch current/max: {}/{})'.format(curEpoch, maxEpoch), font1)
                else:
                    plt.title('train over, max epoch: {}'.format(maxEpoch), font1)

                plt.xlabel('epoch', font1)
                plt.ylabel('loss', font1)
                self.__logger.debug("**************loss x: {} loss y: {}**************".format(loss_x, loss_y))
                plt.grid(loss_x)
                self.__logger.debug("******************save and paint image****************")
                name = './test2.jpg'
                plt.savefig(name)
                PaintImage(name, self.__canvas, self.__zoomWidget, self.__ui)
                AdjustScale(self.__canvas, self.__zoomWidget, self.__ui)
                if len(loss_x) > 0 and len(loss_y) > 0:
                    if int(loss_x[-1]) >= maxEpoch:
                        self.__logger.info("************reach max epoch****************")
                        break
            trainLogParam.SetExitPaintLog(False)
            self.__logger.info("************exit paint log************")

        self.__paintLogThread = threading.Thread(target=_PaintLog, args=(self.__trainLogParam, self.__lock))
        self.__paintLogThread.start()

        def _RecvLog(socket, trainLogParam, lock):
            preEpoch = BASE_TRAIN_EPOCH + 1
            lossList = []
            self.__logger.info("************start recv log************")
            loss_x = trainLogParam.lossx
            loss_y = trainLogParam.lossy

            while not trainLogParam.exitRecvLog:
                self.__logger.debug("recv lossx {}".format(loss_x))
                self.__logger.debug("recv lossy {}".format(loss_y))
                try:
                    data = socket.recv(flags=zmq.NOBLOCK)
                except zmq.ZMQError as e:
                    self.__logger.debug("no data received yet")
                    time.sleep(5)
                    continue

                data = data.decode('utf-8')
                self.__logger.debug("recv log data is {}".format(data))
                if data == 'over':
                    self._SaveWeight()
                    self.__trainProcess = None
                    self.__logger.info("************recv over************")
                    break
                line = data.strip(' ')
                if len(line.split("AL:")) != 2:
                    continue
                strLossList = re.findall(r"AL:(.+?) AC", line)
                if len(strLossList) < 1:
                    continue
                curLoss = float(strLossList[0].strip())
                lossList.append(curLoss)
                strEpoch = re.findall(r"Epoch:(.+?) \|| epochiter:", line)
                if len(strEpoch) < 1:
                    continue
                curEpoch = float(strEpoch[0].strip())
                if curEpoch > preEpoch:
                    loss = np.mean(lossList)
                    lock.acquire()
                    loss_y.append(loss)
                    loss_x.append(int(curEpoch - BASE_TRAIN_EPOCH - 1))
                    lock.release()
                    preEpoch = curEpoch
                    lossList.clear()
            self.__logger.info("************exit recv log************")
            trainLogParam.SetExitRecvLog(False)
        self.__recvLogThread = threading.Thread(target=_RecvLog, args=(self.__socket, self.__trainLogParam, self.__lock))
        self.__recvLogThread.start()

    def _ComMap(self):
        self.__logger.info("********start compute map************")
        while True:
            data = self.__socket.recv().decode('utf-8')
            self.__logger.info("recv log data is {}".format(data))
            if data == 'over':
                self.__logger.info("recv over")
                break
            else:
                time.sleep(1)

        if os.path.exists(self.__mapPath):
            self.__logger.info("process success")
            PaintImage(self.__mapPath, self.__canvas, self.__zoomWidget, self.__ui)
        else:
            raise Exception("image not exist {}".format(self.__mapPath))
        self.__logger.info("********exit compute map********")

    def _ShowCompProcess(self):
        txtCount = GetfilesCount(self.__preDir, ".txt")
        imageCount = GetfilesCount(self.__trainSamplePath)
        self.__canvas.CreateProcessbar("计算map", "处理中", 0, imageCount)
        self.__logger.info("********start show compute information************")
        while txtCount < imageCount:
            self.__logger.debug("txt count is {}, imageCount {}".format(txtCount, imageCount))
            self.__canvas.SetBarCurValue(txtCount)
            # todo:
            QApplication.processEvents()
            time.sleep(0.5)
            txtCount = GetfilesCount(self.__preDir, ".txt")

        self.__canvas.CloseBar()
        QMessageBox.information(self.__canvas, "提示", "处理完成")
        self.__logger.info("********exit show compute information************")

    def AnalyseResult(self):
        currentPath = os.getcwd()
        if not os.path.exists(self.__refineDetPath):
            raise Exception("refineDetPath: {} is not exist".format(self.__refineDetPath))

        os.chdir(self.__refineDetPath)
        args = ['python', 'detectmap.py']
        self.__logger.info("**********detectmap**********")
        if platform == 'win32':
            if hasattr(os.sys, 'winver'):
                self.__mapProcess = subprocess.Popen(args, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
            else:
                self.__mapProcess = subprocess.Popen(args)
        else:
            cmd = "python detectmap.py"
            self.__mapProcess = subprocess.Popen(cmd, shell=True, preexec_fn=os.setsid)
        if self.__mapProcess is None:
            self.__logger.error("open action sample failed")
        else:
            self.__logger.info('Run ActionSample Create PID: {} SubProcess'.format(self.__mapProcess.pid))

        os.chdir(currentPath)

        self.__ui.textEdit.setPlainText("计算mAP")
        PaintImage("./Resource/White.jpeg", self.__canvas, self.__zoomWidget, self.__ui)

        self.__mapThread = threading.Thread(target=self._ComMap)
        self.__mapThread.start()

        # move function ShowCompProcess to thread, may be wrong
        self._ShowCompProcess()

    def FinishMap(self):
        if self.__mapProcess is None:
            return
        self.__logger.info("finish map process pid: {}".format(self.__mapProcess.pid))
        if platform == 'win32':
            self.__mapProcess.kill()
        else:
            os.killpg(self.__trainProcess.pid, signal.SIGINT)

    def FinishTrain(self):
        if self.__trainProcess is None:
            return
        self.__logger.info("finish train process pid: {}".format(self.__trainProcess.pid))
        if platform == 'win32':
            self.__trainProcess.kill()
        else:
            os.killpg(self.__trainProcess.pid, signal.SIGINT)
        self.__trainProcess = None

        if self.__trainLogParam is not None:
            self.__lock.acquire()
            self.__trainLogParam.SetExit(True)
            self.__trainLogParam.lossx.clear()
            self.__trainLogParam.lossy.clear()
            self.__lock.release()
            time.sleep(2)
