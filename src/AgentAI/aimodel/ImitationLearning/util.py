# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import random
from tensorflow import keras

import cv2

import numpy as np


def ShuffleArray(feature, label):
    """
    Shuffle Array
    :param feature: the feature to train model, which is an array
    :param label: the label of the feature, which is an array
    :return: the shuffled feature and label
    """
    randIndex = [a for a in range(feature.shape[0])]
    random.shuffle(randIndex)
    featureShuffle = feature[randIndex, :]
    labelShuffle = label[randIndex, :]
    return featureShuffle, labelShuffle


def ShuffleList(feature, label):
    """
    Shuffle list
    :param feature: the feature to train model, which is a list
    :param label: the label of the feature, which is a list
    :return: the shuffled feature and label
    """
    randIndex = [a for a in range(len(feature))]
    random.shuffle(randIndex)
    featureShuffle = [feature[ind] for ind in randIndex]
    labelShuffle = [label[ind] for ind in randIndex]
    return featureShuffle, labelShuffle


def RepeatArray(x, num):
    """
    Repeat array.
    :param x: the original feature, which is an array.
    :param num: the repeat times, which is an int number.
    :return: the augmented feature, which is an array
    """
    if num < 1:
        randIndex = [a for a in range(x.shape[0])]
        random.shuffle(randIndex)
        y = x[randIndex[0:int(np.round(x.shape[0] * num))], :]
    else:
        num = int(num)
        xShape = list(x.shape)
        xShape[0] = np.round(x.shape[0] * num)
        y = np.zeros(xShape)
        for n in range(num):
            y[x.shape[0] * n:x.shape[0] * (n + 1), :] = x

    return y


def RepeatList(x, num):
    """
    Repeat list.
    :param x: the original feature, which is a list.
    :param num: the repeat times, which is an int number.
    :return: the augmented feature, which is a list.
    """
    if num < 1:
        randIndex = [a for a in range(x.shape[0])]
        random.shuffle(randIndex)
        y = x[randIndex[0:int(np.round(x.shape[0] * num))], :]
    else:
        num = int(num)
        y = x * num
    return y


def FindIndex(x, y):
    """
    Find index of y in x
    :param x: a list
    :param y: the target to find, which is a number.
    :return: a index list indicating the location of y in x.
    """
    return [a for a in range(len(x)) if x[a] == y]


def ReadTxt(txtPath):
    """
    Read txt to get file name and the corresponding labels (support multi-task)
    :param txtPath: the path of txt. Each row of txt is composed of fileName and label,
    such as ../img.png 0 1. Here, the front string is the imagePath, 0 is the class label
    for the first task, 1 is the class label for the second task.
    :return: the list of fileName and the array of label for multi-task
    """
    with open(txtPath) as f:
        feature = f.readlines()
        f.close()
    feature = [s.strip() for s in feature]
    featureOut = [s.split(' ') for s in feature]
    filePathList = [featureTmp[0] for featureTmp in featureOut]
    labelList = [featureTmp[1:] for featureTmp in featureOut]
    labelArray = np.zeros([len(labelList), len(labelList[0])])
    for i, _ in enumerate(labelList):
        for j, _ in enumerate(labelList[0]):
            labelArray[i, j] = int(labelList[i][j])
    return filePathList, labelArray


def ObtainTaskDict(actionDefine):
    """
    Obtain task dict
    :param actionDefine: a dictionary from imitationLearning.json
    :return: the task list, action dictionary for each task,
    dictionary of action name for each task.
    """

    # obtain task List for multiTask (default is 0)
    taskList = list()
    for _, actionDefineTmp in enumerate(actionDefine):
        taskList = taskList + actionDefineTmp["task"]

    taskList = list(set(taskList))
    taskActionDict = dict()
    actionNameDict = dict()
    for task in taskList:
        taskActionDict[task] = list()
        actionNameDict[task] = list()

    for _, actionDefineTmp in enumerate(actionDefine):
        for task in actionDefineTmp["task"]:
            taskActionDict[task].append(actionDefineTmp)

    for key in taskActionDict:
        taskActionList = taskActionDict[key]
        actionNameDict[key] = [taskActionList[n]["name"] for n in range(len(taskActionList))]

    return taskList, taskActionDict, actionNameDict


def DataGenerator(actionSpaceList, imgFiles=None, labels=None, batchSize=64, dim=150):
    """
    Generator for fit_generator
    :param actionSpaceList: action number for different tasks, which is a list.
    :param imgFiles: list of image file name.
    :param labels: the classes for different tasks, whicn is an array.
    :param batchSize: the image number for one batch.
    :param dim: the size of input image. The image is resized to [dim, dim]
    :return: the batch of input images, the one-hot label array for different tasks.
    """
    m = len(imgFiles)
    numMinibatches = int(m / batchSize)
    while 1:
        permutation = list(np.random.permutation(m))
        for i in range(numMinibatches):
            minibatchesX = np.empty((batchSize, dim, dim, 3))
            minibatchesY0 = np.empty((batchSize), dtype=int)
            minibatchesY1 = np.empty((batchSize), dtype=int)

            index = permutation[i * batchSize:(i + 1) * batchSize]
            for j, ind in enumerate(index):
                img = cv2.imread(imgFiles[ind]).astype('float')
                imgOut = PreprocessImage(img)
                minibatchesX[j,] = imgOut
                if len(actionSpaceList) == 1:
                    minibatchesY0[j] = labels[ind, 0]

                else:
                    minibatchesY0[j] = labels[ind, 0]
                    minibatchesY1[j] = labels[ind, 1]

            minibatchesY0 = keras.utils.to_categorical(minibatchesY0,
                                                       num_classes=actionSpaceList[0])

            if len(actionSpaceList) == 2:
                minibatchesY1 = keras.utils.to_categorical(minibatchesY1,
                                                           num_classes=actionSpaceList[1])

            if len(actionSpaceList) == 1:
                yield minibatchesX, minibatchesY0
            else:
                yield minibatchesX, [minibatchesY0, minibatchesY1]


def PreprocessImage(img):
    """
    Preprocess for imput image.
    :param actionSpaceList: action number for different tasks, which is a list.
    :param img: the image.
    :return: the normalized image.
    """
    imgOut = img / 255.
    return imgOut


def GetFeatureAndLabel(feature, label, fileName, actionSpaceList):
    """
    Get feature and label
    :param feature: the original feature for each image, which is a dictionary. The key
    is the name of image file.
    :param label: the label of feature, which is a dictionary. The key
    is the name of image file.
    :param fileName: file name of image, which is a list
    :param actionSpaceList: action number for different tasks, which is a list.
    :return: the feature array and one-hot label list for multi-task
    """
    for key in feature.keys():
        timeStep = feature[key].shape[0]
        featureDim = feature[key].shape[1]
        taskNum = label[key].shape[0]
        break
    featureMulti = np.zeros([len(fileName), timeStep, featureDim])
    labelMulti = np.zeros([len(fileName), taskNum])

    index = list()
    for n, fileNameTmp in enumerate(fileName):
        if fileNameTmp in feature.keys():
            featureMulti[n, :] = feature[fileNameTmp]
            labelMulti[n, :] = label[fileNameTmp]
            index.append(n)
        else:
            continue

    if len(index) == 0:
        return None, None

    featureMultiOut = featureMulti[index, :]
    labelMultiOut = labelMulti[index, :]

    labelMultiVecOut = list()
    for n in range(taskNum):
        labelMultiVecOut.append(keras.utils.to_categorical(labelMultiOut[:, n],
                                                           num_classes=actionSpaceList[n]))
    return featureMultiOut, labelMultiVecOut
