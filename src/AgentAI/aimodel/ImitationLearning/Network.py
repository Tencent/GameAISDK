# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import csv
import glob
import logging
import random
import shutil
import sys
import operator
import os

import cv2
import numpy as np

import tensorflow as tf
from tensorflow import keras
from tensorflow.python.keras import regularizers
from tensorflow.python.keras import backend as K
from tensorflow.python.keras.layers import Input, Activation, BatchNormalization, Flatten, Conv2D
from tensorflow.python.keras.applications.resnet50 import conv_block, identity_block
from tensorflow.python.keras.layers import Convolution2D, ZeroPadding2D
from tensorflow.python.keras.layers import MaxPooling2D, Dense, GlobalAveragePooling2D, PReLU, LSTM
from tensorflow.python.keras.models import Sequential, Model
from tensorflow.python.keras.preprocessing.image import ImageDataGenerator
from .ProgressReport import ProgressReport

from .util import *

K.set_image_data_format('channels_last')

DATA_ROOT_DIR = '../'
if os.environ.get('AI_SDK_PATH') is not None:
    DATA_ROOT_DIR = os.environ.get('AI_SDK_PATH') + '/'


class Network(object):
    """
    Network class for imitation learning
    """

    def __init__(self, trainDataDir, testDataDir, trainClassDir, testClassDir, cfgData):
        self.logger = logging.getLogger('agent')
        self.sampleBuf = {}
        self.imageChannel = 3

        self.featureDim = 200

        self.isSmallNet = cfgData.get('isSmallNet') or False
        self.isMax = cfgData.get('isMax') or False
        self.randomRatio = cfgData.get('randomRatio') or 0
        self.trainIter = cfgData.get('trainIter') or 20
        self.timeStep = cfgData.get('timeStep') or 5
        self.randomRatio = self.randomRatio * 1000
        self.useClassBalance = cfgData.get('useClassBalance')
        self.useResNet = cfgData.get('useResNet')

        if self.isSmallNet:
            self.imageSize = 50
        else:
            self.imageSize = 150

        self.progressReport = ProgressReport()
        self.progressReport.Init()
        self.actionAheadNum = cfgData['actionAheadNum']
        self.classImageTimes = cfgData['classImageTimes']
        self.inputHeight = cfgData['inputHeight']
        self.inputWidth = cfgData['inputWidth']
        self.roiRegion = cfgData.get('roiRegion')

        self.actionDefine = cfgData.get('actionDefine')

        self.taskList, self.taskActionDict, self.actionNameDict = ObtainTaskDict(self.actionDefine)

        self.actionSpaceList = list()
        for taskIndex in self.taskList:
            actionName = self.actionNameDict[taskIndex]
            self.actionSpaceList.append(len(actionName))

        if len(self.taskList) > 2:
            self.logger.error('Imitation learning only supports one or two tasks')

        self.actionPriorWeights = [cfgData['actionDefine'][n]['prior']
                                   for n in range(len(cfgData['actionDefine']))]

        self.trainDataDir = trainDataDir
        self.testDataDir = testDataDir

        self.trainClassDir = trainClassDir
        self.testClassDir = testClassDir

        self.modelPath = os.path.join(DATA_ROOT_DIR + 'data/ImitationModel/')
        if not os.path.exists(self.modelPath):
            os.mkdir(self.modelPath)

        self.netBatchSize = 32

        self.kerasModel = None

        self.netLSTMBatchSize = 64

        self.kerasModelLSTM = None

    def Init(self):
        """
        Initialize function
        """
        pass

    def Finish(self):
        """
        Finish fuction
        """
        pass

    def LossCCEPieceWise(self, y_true, y_pred):
        """
        Define piece-wise class cross entropy loss
        """
        state1 = 0.5 * y_pred + 10e-3
        state2 = y_pred
        y_pred = tf.where(y_pred < 2 * 10e-3, x=state1, y=state2)
        loss = K.sum(-K.log(y_pred) * y_true)
        return loss

    def TrainGenerator(self):
        """
        Train network using "fit_generator" function
        """
        if self.useClassBalance:
            self.trainFileName, self.trainLabel = ReadTxt(os.path.join(self.trainClassDir,
                                                                       'data.txt'))
        else:
            self.trainFileName, self.trainLabel = ReadTxt(os.path.join(self.trainClassDir,
                                                                       'dataOri.txt'))

        self.trainFileNameOri, self.trainLabelOri = ReadTxt(os.path.join(self.trainClassDir,
                                                                         'dataOri.txt'))

        self.testFileName, self.testLabel = ReadTxt(os.path.join(self.testClassDir,
                                                                 'data.txt'))

        nb_train_samples = len(self.trainFileName)
        nb_val_samples = len(self.testFileName)

        kerasModel = self.KerasModel()
        self.logger.info(kerasModel.summary())

        if self.taskList == [0, 1]:
            kerasModel.compile(optimizer=tf.keras.optimizers.Adam(lr=0.001,
                                                                  beta_1=0.9,
                                                                  beta_2=0.999,
                                                                  epsilon=1e-08,
                                                                  decay=0.0),
                               loss={'out_task0': self.LossCCEPieceWise,
                                     'out_task1': self.LossCCEPieceWise},
                               loss_weights={'out_task0': 1, 'out_task1': 1},
                               metrics=['accuracy'])

        elif self.taskList == [0]:
            kerasModel.compile(optimizer=tf.keras.optimizers.Adam(lr=0.001,
                                                                  beta_1=0.9,
                                                                  beta_2=0.999,
                                                                  epsilon=1e-08,
                                                                  decay=0.0),
                               loss={'out_task0': self.LossCCEPieceWise},
                               metrics=['accuracy'])

        valAccList = list()

        for trainIter in range(self.trainIter):
            # obtain input features for network
            self.logger.info('trainIter is {}'.format(trainIter))

            trainHistory = kerasModel.fit_generator(DataGenerator(self.actionSpaceList,
                                                                  imgFiles=self.trainFileName,
                                                                  labels=self.trainLabel,
                                                                  batchSize=self.netBatchSize,
                                                                  dim=self.imageSize),
                                                    steps_per_epoch=
                                                    nb_train_samples / self.netBatchSize,
                                                    epochs=1, verbose=1,
                                                    validation_data=
                                                    DataGenerator(self.actionSpaceList,
                                                                  imgFiles=self.testFileName,
                                                                  labels=self.testLabel,
                                                                  batchSize=self.netBatchSize,
                                                                  dim=self.imageSize),
                                                    validation_steps=
                                                    nb_val_samples / self.netBatchSize)
            trainAcc, valAcc = self.GetAcc(trainHistory)
            valAccList.append(valAcc + trainAcc)

            kerasModel.save_weights(self.modelPath + 'my_model_weights' + np.str(trainIter) + '.h5')

            logging.info('Network: Iteration {}....{}: train_acc is {} and val_acc is {}'.format(
                trainIter, self.trainIter, trainAcc, valAcc))
            if trainIter < (self.trainIter - 1):
                self.progressReport.SendTrainProgress(int((trainIter + 1) * 100 / self.trainIter))

        indexAccValMax = valAccList.index(np.max(valAccList))

        logging.info('Use model from the {}th iteration'.format(indexAccValMax))

        srcModelName = self.modelPath + 'my_model_weights' + np.str(indexAccValMax) + '.h5'
        dstModelName = self.modelPath + 'my_model_weights' + '.h5'
        shutil.copyfile(srcModelName, dstModelName)

    def KerasModelSmallNet50(self, imgInput):
        """
        Construct small net. The image size is 50*50, which is suitable for map.
        """
        x = Conv2D(16, (3, 3), activation='tanh')(imgInput)
        x = Conv2D(32, (3, 3), activation='relu')(x)
        x = MaxPooling2D(pool_size=(2, 2))(x)
        x = Conv2D(32, (3, 3), activation='relu')(x)
        x = Conv2D(32, (3, 3), activation='relu')(x)
        x = MaxPooling2D(pool_size=(2, 2))(x)
        x = Conv2D(32, (3, 3), activation='relu')(x)
        x = Conv2D(32, (3, 3), activation='relu')(x)
        x = Flatten()(x)
        x = Dense(self.featureDim, kernel_regularizer=regularizers.l2(0.0002),
                  activity_regularizer=regularizers.l1(0.0002), name='fc_feature')(x)
        x = PReLU()(x)
        return x

    def KerasModelSmallNet150(self, imgInput):
        """
        Construct small net. The image size is 150*150, which is suitable for image.
        """
        x = Conv2D(32, (3, 3), activation='tanh')(imgInput)
        x = Conv2D(32, (3, 3), activation='relu')(x)
        x = MaxPooling2D(pool_size=(2, 2))(x)
        x = Conv2D(32, (3, 3), activation='relu')(x)
        x = Conv2D(32, (3, 3), activation='relu')(x)
        x = MaxPooling2D(pool_size=(2, 2))(x)
        x = Conv2D(32, (3, 3), activation='relu')(x)
        x = Conv2D(32, (3, 3), activation='relu')(x)
        x = MaxPooling2D(pool_size=(2, 2))(x)
        x = Conv2D(64, (3, 3), activation='relu')(x)
        x = Conv2D(64, (3, 3), activation='relu')(x)
        x = MaxPooling2D(pool_size=(2, 2))(x)
        x = Flatten()(x)
        x = Dense(self.featureDim, kernel_regularizer=regularizers.l2(0.0002),
                  activity_regularizer=regularizers.l1(0.0002), name='fc_feature')(x)
        x = PReLU()(x)
        return x

    def KerasModelResNet(self, imgInput):
        """
        Construct resNet. The image size is 150*150, which is suitable for image.
        """
        bn_axis = 3

        x = ZeroPadding2D((3, 3))(imgInput)
        x = Convolution2D(8, 7, strides=(2, 2), name='conv1')(x)
        x = BatchNormalization(axis=bn_axis, name='bn_conv1')(x)
        x = Activation('relu')(x)
        x = MaxPooling2D((3, 3), strides=(2, 2))(x)

        x = conv_block(x, 3, [8, 8, 16],
                       stage=2, block='a', strides=(1, 1))
        x = identity_block(x, 3, [8, 8, 16], stage=2, block='b')
        x = identity_block(x, 3, [8, 8, 16], stage=2, block='c')

        x = conv_block(x, 3, [16, 16, 32], stage=3, block='a')
        x = identity_block(x, 3, [16, 16, 32], stage=3, block='b')
        x = identity_block(x, 3, [16, 16, 32], stage=3, block='c')
        x = identity_block(x, 3, [16, 16, 32], stage=3, block='d')

        x = conv_block(x, 3, [32, 32, 64], stage=4, block='a')
        x = identity_block(x, 3, [32, 32, 64], stage=4, block='b')
        x = identity_block(x, 3, [32, 32, 64], stage=4, block='c')
        x = identity_block(x, 3, [32, 32, 64], stage=4, block='d')
        x = identity_block(x, 3, [32, 32, 64], stage=4, block='e')
        x = identity_block(x, 3, [32, 32, 64], stage=4, block='f')

        x = conv_block(x, 3, [64, 64, 128], stage=5, block='a')
        x = identity_block(x, 3, [64, 64, 128], stage=5, block='b')
        x = identity_block(x, 3, [64, 64, 128], stage=5, block='c')

        x = conv_block(x, 3, [64, 64, 256], stage=6, block='a')
        x = identity_block(x, 3, [64, 64, 256], stage=6, block='b')
        x = identity_block(x, 3, [64, 64, 256], stage=6, block='c')

        x = GlobalAveragePooling2D()(x)
        # x = Flatten()(x)
        x = Dense(self.featureDim, kernel_regularizer=regularizers.l2(0.0002),
                  activity_regularizer=regularizers.l1(0.0002), name='fc_feature')(x)
        x = PReLU()(x)
        return x

    def KerasModel(self):
        """
        Construct two structures of network
        """
        input_shape = (self.imageSize, self.imageSize, self.imageChannel)
        imgInput = Input(shape=input_shape)

        if self.isSmallNet:
            x = self.KerasModelSmallNet50(imgInput)
        else:
            if self.useResNet:
                x = self.KerasModelResNet(imgInput)
            else:
                x = self.KerasModelSmallNet150(imgInput)

        for taskIndex in self.taskList:
            actionName = self.actionNameDict[taskIndex]
            if taskIndex == 0:
                out0 = Dense(len(actionName), activation='softmax', name='out_task0')(x)
            elif taskIndex == 1:
                out1 = Dense(len(actionName), activation='softmax', name='out_task1')(x)
            else:
                assert 'task for multi_task should be 0 or 1'

        if self.taskList == [0, 1]:
            model = Model(imgInput, [out0, out1])

        elif self.taskList == [0]:
            model = Model(imgInput, out0)

        else:
            assert 'taskList only sopports [0,1] and [0], ' \
                   'please check actionDefine in ImitationLearning.json'

        return model

    def KerasModelLSTM(self):
        """
        Define structure of LSTM
        """
        input_shape = (self.timeStep, self.featureDim)
        featureInput = Input(shape=input_shape)
        x = LSTM(100)(featureInput)

        for taskIndex in self.taskList:
            actionName = self.actionNameDict[taskIndex]
            if taskIndex == 0:
                out0 = Dense(len(actionName), activation='softmax', name='out_task0')(x)
            elif taskIndex == 1:
                out1 = Dense(len(actionName), activation='softmax', name='out_task1')(x)
            else:
                assert 'task for multi_task should be 0 or 1'

        if self.taskList == [0, 1]:
            model = Model(featureInput, [out0, out1])

        elif self.taskList == [0]:
            model = Model(featureInput, out0)

        return model

    def TrainLSTM(self):
        """
        Train LSTM
        """
        modelName = self.modelPath + 'my_model_weights.h5'
        kerasModel = self.KerasModel()
        kerasModel.load_weights(modelName)

        kerasModelExtFea = Model(inputs=kerasModel.input,
                                 outputs=kerasModel.get_layer('fc_feature').output)
        self.logger.info(kerasModelExtFea.summary())

        modelLSTM = self.KerasModelLSTM()

        if self.taskList == [0, 1]:
            modelLSTM.compile(optimizer=tf.keras.optimizers.Adam(lr=0.001,
                                                                 beta_1=0.9,
                                                                 beta_2=0.999,
                                                                 epsilon=1e-08,
                                                                 decay=0.0),
                              loss={'out_task0': self.LossCCEPieceWise,
                                    'out_task1': self.LossCCEPieceWise},
                              loss_weights={'out_task0': 1, 'out_task1': 1},
                              metrics=['accuracy'])

        elif self.taskList == [0]:
            modelLSTM.compile(optimizer=tf.keras.optimizers.Adam(lr=0.001,
                                                                 beta_1=0.9,
                                                                 beta_2=0.999,
                                                                 epsilon=1e-08,
                                                                 decay=0.0),
                              loss={'out_task0': self.LossCCEPieceWise},
                              metrics=['accuracy'])

        feaTrain, labelTrain, feaTest, labelTest = self._ExtractFeature(
            kerasModelExtFea)

        if feaTrain is None:
            self.logger.error('No image is found in {}'.format(self.trainDataDir))

        valAccList = list()
        for trainIter in range(self.trainIter):
            trainHistory = modelLSTM.fit(x=feaTrain, y=labelTrain,
                                         validation_data=(feaTest, labelTest),
                                         batch_size=self.netLSTMBatchSize, shuffle=1, epochs=1)

            trainAcc, valAcc = self.GetAcc(trainHistory)
            valAccList.append(valAcc + trainAcc)

            modelLSTM.save_weights(self.modelPath + 'my_model_weights_LSTM'
                                   + np.str(trainIter) + '.h5')

            logging.info('NetworkLSTM: Iter {}....{}: train_acc is {} and val_acc is {}'
                         .format(trainIter, self.trainIter, trainAcc, valAcc))

        indexAccValMax = valAccList.index(np.max(valAccList))

        logging.info('Use model from the {}th iteration'.format(indexAccValMax))

        srcModelName = self.modelPath + 'my_model_weights_LSTM' + np.str(indexAccValMax) + '.h5'
        dstModelName = self.modelPath + 'my_model_weights_LSTM' + '.h5'
        shutil.copyfile(srcModelName, dstModelName)
        self.progressReport.SendTrainProgress(100)

    def GetAcc(self, trainHistory):
        """
        Calculate train and val accuracy
        """
        if self.taskList == [0, 1]:
            trainAcc = 0.5 * (trainHistory.history['out_task0_acc'][0] + \
                              trainHistory.history['out_task1_acc'][0])
            valAcc = 0.5 * (trainHistory.history['val_out_task0_acc'][0] + \
                            trainHistory.history['val_out_task1_acc'][0])
        else:
            trainAcc = trainHistory.history['acc'][0]
            valAcc = trainHistory.history['val_acc'][0]

        return trainAcc, valAcc

    def ExtractNetFeature(self, kerasModelExtFea, fileNameList, label):
        """
        Extract feature for LSTM
        """
        featureFromNet = dict()
        labelFromNet = dict()
        for n, fileName in enumerate(fileNameList):
            img = cv2.imread(fileName).astype('float')
            imgOut = PreprocessImage(img)
            featureTmp = np.zeros([1,
                                   self.imageSize,
                                   self.imageSize,
                                   self.imageChannel])
            featureTmp[0,] = imgOut
            featureFromNet[fileName] = kerasModelExtFea.predict(featureTmp)
            labelFromNet[fileName] = label[n]

        featureConcat, labelConcat = self._ConcatFeature(featureFromNet,
                                                         labelFromNet)

        return featureConcat, labelConcat

    def _ExtractFeature(self, kerasModelExtFea):
        """
        Extract feature of training and test image set for LSTM
        """
        featureTrainOri, labelTrainOri = self.ExtractNetFeature(kerasModelExtFea,
                                                                self.trainFileNameOri,
                                                                self.trainLabelOri)

        featureTrain, labelTrain = GetFeatureAndLabel(featureTrainOri,
                                                      labelTrainOri,
                                                      self.trainFileName,
                                                      self.actionSpaceList)

        featureTestOri, labelTestOri = self.ExtractNetFeature(kerasModelExtFea,
                                                              self.testFileName,
                                                              self.testLabel)

        featureTest, labelTest = GetFeatureAndLabel(featureTestOri,
                                                    labelTestOri,
                                                    self.testFileName,
                                                    self.actionSpaceList)

        return featureTrain, labelTrain, featureTest, labelTest

    def _ConcatFeature(self, featureFromNet, label):
        """
        Concat feature from network for lstm
        """
        featureConcat = dict()
        labelConCat = dict()
        for fileName in featureFromNet.keys():
            _, fileNameTmp = os.path.split(fileName)
            fileNameNum = int(fileNameTmp.split('_')[-1][:-4])

            noFile = 0
            for n in range(self.timeStep):
                fileNameNumTmp = fileNameNum - self.timeStep + n + 1
                fileNameTmp = fileName[:-len(fileNameTmp.split('_')[-1])] +\
                              str(fileNameNumTmp) +\
                              fileName[-4:]

                if fileNameTmp not in featureFromNet.keys():
                    noFile = 1
                    break
                else:
                    noFile = 0

            if noFile:
                continue

            featureTmp = np.zeros([self.timeStep, self.featureDim])
            for n in range(self.timeStep):
                fileNameNumTmp = fileNameNum - self.timeStep + n + 1
                fileNameTmp = fileName[:-len(fileNameTmp.split('_')[-1])] + \
                              str(fileNameNumTmp) + fileName[-4:]
                featureTmp[n, :] = featureFromNet[fileNameTmp]

            featureConcat[fileName] = featureTmp
            labelConCat[fileName] = label[fileName]

        return featureConcat, labelConCat

    def LoadWeights(self):
        """
        Load weights of CNN and LSTM
        """
        self.kerasModel = self.KerasModel()
        self.kerasModel.load_weights(self.modelPath + 'my_model_weights.h5')
        self.kerasModelExtFea = Model(inputs=self.kerasModel.input,
                                      outputs=self.kerasModel.get_layer('fc_feature').output)

        self.kerasModelLSTM = self.KerasModelLSTM()
        self.kerasModelLSTM.load_weights(self.modelPath + 'my_model_weights_LSTM.h5')

    def Predict(self, image):
        """
        Output action given a test image based on CNN
        """
        inputData = self.PrepareData(image)

        if len(self.taskList) == 2:
            predAction = list()
            for n in range(len(self.taskList)):
                actionScore = self.kerasModel.predict(inputData)[n][0]
                predAction.append(self.ChooseAction(actionScore))
        else:
            actionScore = self.kerasModel.predict(inputData)[0]
            predAction = self.ChooseAction(actionScore)
        return predAction

    def PrepareData(self, image):
        """
        Preprare data based on image
        """
        if self.roiRegion is not None:
            image = image[self.roiRegion[1]: self.roiRegion[1] + self.roiRegion[3],
                          self.roiRegion[0]: self.roiRegion[0] + self.roiRegion[2], :]

        if image.shape[0] != self.imageSize or image.shape[1] != self.imageSize:
            image = cv2.resize(image, (self.imageSize, self.imageSize))

        image = PreprocessImage(image)
        inputData = np.zeros([1, self.imageSize, self.imageSize, self.imageChannel])
        inputData[0, :, :, :] = image
        return inputData

    def PredictLSTM(self, inputData):
        """
        Output action given a test feature based on LSTM
        """
        if len(self.taskList) == 2:
            predAction = list()
            for n in range(len(self.taskList)):
                actionScore = self.kerasModelLSTM.predict(inputData)[n][0]
                predAction.append(self.ChooseAction(actionScore))
        else:
            actionScore = self.kerasModelLSTM.predict(inputData)[0]
            predAction = self.ChooseAction(actionScore)

        return predAction

    def ChooseAction(self, actionScore):
        """
        choose action according to score of different actions
        There are two modes: max or randomly choose action
        """
        if self.isMax:
            actionScore = [max(np.floor(actionScore[n] * 1000), 10)
                           for n in range(len(actionScore))]

            actionScore = [actionScore[n] * self.actionPriorWeights[n]
                           for n in range(len(actionScore))]
            self.logger.info('actionScore is {}'.format(actionScore))
            predAction = np.argmax(actionScore)
        else:
            actionScore = [np.floor(actionScore[n] * 1000) + self.randomRatio
                           for n in range(len(actionScore))]

            actionScore = [actionScore[n] * self.actionPriorWeights[n]
                           for n in range(len(actionScore))]

            self.logger.info('actionScore is {}'.format(actionScore))

            predAction = int(self.RandomIndex(actionScore))

        return predAction

    def RandomIndex(self, rate):
        """
        Randomly select a index based on probability distribution
        """
        start = 0
        index = 0
        randnum = random.randint(1, int(sum(rate)))
        for index, scope in enumerate(rate):
            start += scope
            if randnum <= start:
                break
        return index

    def ExtractFeature(self, image):
        """
        Extract feature of the input image
        """
        inputData = self.PrepareData(image)
        feature = self.kerasModelExtFea.predict(inputData)
        return feature
