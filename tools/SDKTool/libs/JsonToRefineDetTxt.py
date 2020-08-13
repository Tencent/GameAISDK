# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import json
import glob
import random
import numpy as np

import cv2


import xml.dom.minidom as xmlDoc
import xml.etree.ElementTree as ET
from collections import OrderedDict

MIN_SAMPLE_NUM = 2000
def JsonToXml(jsonDir):
    # json_paths = list(glob.iglob(os.path.join(jsonDir, '*.json'),recursive=True))
    json_paths = Getfiles(jsonDir, ".json")
    print("josn count is {}".format(len(json_paths)))

    for json_path in json_paths:
        with open(json_path, 'r') as json_file:
            json_data = json.load(json_file, object_pairs_hook=OrderedDict)

        filePath, _  = os.path.split(json_path)
        fileName = os.path.join(filePath, json_data['fileName'])
        img = cv2.imread(fileName)
        xml = xmlDoc.Document()
        annotation = xml.createElement('annotation')
        xml.appendChild(annotation)

        folder = xml.createElement('folder')
        folder_value = xml.createTextNode('LabelImg')
        folder.appendChild(folder_value)
        annotation.appendChild(folder)

        filename = xml.createElement('filename')
        filename_value = xml.createTextNode(json_data['fileName'])
        filename.appendChild(filename_value)
        annotation.appendChild(filename)

        path = xml.createElement('path')
        path_value = xml.createTextNode(os.path.join(jsonDir, json_data['fileName']))
        path.appendChild(path_value)
        annotation.appendChild(path)

        source = xml.createElement('source')
        database = xml.createElement('database')
        database_value = xml.createTextNode('Unknown')
        database.appendChild(database_value)
        source.appendChild(database)
        annotation.appendChild(source)

        size = xml.createElement('size')
        width = xml.createElement('width')
        width_value = xml.createTextNode(str(img.shape[1]))
        width.appendChild(width_value)
        size.appendChild(width)
        height = xml.createElement('height')
        height_value = xml.createTextNode(str(img.shape[0]))
        height.appendChild(height_value)
        size.appendChild(height)
        depth = xml.createElement('depth')
        depth_value = xml.createTextNode(str(img.shape[2]))
        depth.appendChild(depth_value)
        size.appendChild(depth)
        annotation.appendChild(size)

        path = xml.createElement('segmented')
        path_value = xml.createTextNode('0')
        path.appendChild(path_value)
        annotation.appendChild(path)

        for bbox in json_data['labels']:
            if bbox['w'] < 0:
                bbox['x'] = bbox['x'] + bbox['w']
                bbox['w'] = abs(bbox['w'])
            if bbox['h'] < 0:
                bbox['y'] = bbox['y'] + bbox['h']
                bbox['h'] = abs(bbox['h'])

            obj = xml.createElement('object')
            name = xml.createElement('name')
            name_value = xml.createTextNode(bbox['label'])
            name.appendChild(name_value)
            obj.appendChild(name)

            pose = xml.createElement('pose')
            pose_value = xml.createTextNode('Unspecified')
            pose.appendChild(pose_value)
            obj.appendChild(pose)

            truncated = xml.createElement('truncated')
            truncated_value = xml.createTextNode('0')
            truncated.appendChild(truncated_value)
            obj.appendChild(truncated)

            difficult = xml.createElement('difficult')
            difficult_value = xml.createTextNode('0')
            difficult.appendChild(difficult_value)
            obj.appendChild(difficult)

            bndbox = xml.createElement('bndbox')
            xmin = xml.createElement('xmin')
            xmin_value = xml.createTextNode(str(int(bbox['x'])))
            xmin.appendChild(xmin_value)
            bndbox.appendChild(xmin)

            ymin = xml.createElement('ymin')
            ymin_value = xml.createTextNode(str(int(bbox['y'])))
            ymin.appendChild(ymin_value)
            bndbox.appendChild(ymin)

            xmax = xml.createElement('xmax')
            xmax_value = xml.createTextNode(str(int(bbox['x']) + int(bbox['w'])))
            xmax.appendChild(xmax_value)
            bndbox.appendChild(xmax)

            ymax = xml.createElement('ymax')
            ymax_value = xml.createTextNode(str(int(bbox['y']) + int(bbox['h'])))
            ymax.appendChild(ymax_value)
            bndbox.appendChild(ymax)

            obj.appendChild(bndbox)
            annotation.appendChild(obj)

        xml_path = json_path.replace('json', 'xml')
        print(xml_path)
        f = open(xml_path, 'wb')
        f.write(xml.toprettyxml(indent='\t', newl='\n', encoding='utf-8'))
        f.close()

classes = [
    ['return'],
    ['close'],
    ['tag'],
    ['other']]

#MIN_RATIO = 0.1
# MIN_RATIO = [0.1] * len(classes)
# MIN_RATIO[-1] = 0.6


def convert(size, box):
    dw = 1. / size[0]
    dh = 1. / size[1]
    x = (box[0] + box[1]) / 2.0
    y = (box[2] + box[3]) / 2.0
    w = box[1] - box[0]
    h = box[3] - box[2]
    x = x * dw
    w = w * dw
    y = y * dh
    h = h * dh
    return (x, y, w, h)


def Getfiles(directoryName, formatList = [".png", ".bmp", ".jpg", ".jpeg"]):
    files = []
    file_count = 0
    for dirPath, dirNames, fileNames in os.walk(directoryName):
        for file in fileNames:
            if os.path.splitext(file)[1] in formatList:
                file_count = file_count + 1
                print("dirPath {}, dirNames {} file is {}".format(dirPath, dirNames, file))
                files.append("{}/{}".format(dirPath, file))

    return files


def convert_annotation(xml, imageName):
    inFile = open(xml)
    tree = ET.parse(inFile)
    infoBoxList = list()
    root = tree.getroot()
    size = root.find('size')
    w = int(size.find('width').text)
    h = int(size.find('height').text)

    if w == 0:
        print(xml)
        return []

    for obj in root.iter('object'):
        difficult = obj.find('difficult').text
        cls = obj.find('name').text
        for ind, classesTemp in enumerate(classes):
            if cls not in classesTemp or int(difficult) == 1:
                continue
            cls_id = ind
            # cls_id = 0
            xmlbox = obj.find('bndbox')
            infoBox = (float(xmlbox.find('xmin').text), float(xmlbox.find('ymin').text), float(xmlbox.find('xmax').text),
                 float(xmlbox.find('ymax').text), cls_id + 1)
            infoBoxList.append(infoBox)

    # imageName = xml.replace('xml', 'jpg')
    if os.path.exists(imageName):
        # img = cv2.imread(imageName)
        # height = img.shape[0]
        # width = img.shape[1]
        # if height == h and width == w:
        return infoBoxList
        # else:
        #     return []
    else:
        return []


def obtain_annotation(xml):
    inFile = open(xml)
    tree = ET.parse(inFile)

    root = tree.getroot()
    size = root.find('size')
    w = int(size.find('width').text)
    h = int(size.find('height').text)

    clsList = list()

    if w == 0:
        print(xml)
        return clsList

    for obj in root.iter('object'):
        difficult = obj.find('difficult').text
        cls = obj.find('name').text
        for ind, classesTemp in enumerate(classes):
            if cls not in classesTemp or int(difficult) == 1:
                continue
            cls_id = ind
            # cls_id = 0
            clsList.append(cls_id)

    return clsList


def GetNewList(classes, clsListTotal):
    clsTotal = list()
    classIndList = list()
    for i in range(len(classes)):
        classIndList.append(list())

    sampleNum = len(clsListTotal)

    # get index for different classes
    for n in range(sampleNum):
        clsTotal = clsTotal + clsListTotal[n]
        for i in range(len(classes)):
            if i in clsListTotal[n]:
                classIndList[i].append(n)

    if sampleNum < MIN_SAMPLE_NUM:
        MIN_RATIO = [MIN_SAMPLE_NUM * 0.1 / sampleNum] * len(classes)
    else:
        MIN_RATIO = [0.1] * len(classes)

    # get total number for different classes
    clsHist = list()
    for n in range(0, len(classes)):
        clsHist.append(clsTotal.count(n))
    print('old clsHist is {}'.format(clsHist))

    # add files for classes with fewer samples
    totalSampleNum = np.sum(clsHist)

    minSampleNum = [totalSampleNum * MIN_RATIO[n] for n in range(len(MIN_RATIO))]

    for i in range(len(clsHist)):
        if clsHist[i] == 0:
            print('error: class {} hist is 0 '.format(classes[i]))
            continue

        classTime = int(np.ceil(minSampleNum[i] * 1. / clsHist[i]))
        classIndList[i] = classIndList[i] * classTime

    classIndListTotal = list()
    for i in range(len(classIndList)):
        classIndListTotal = classIndListTotal + classIndList[i]

    # get index for different classes
    clsTotal = list()
    for n in range(len(classIndListTotal)):
        clsTotal = clsTotal + clsListTotal[classIndListTotal[n]]

    # get total number for different classes
    clsHist = list()
    for n in range(0, len(classes)):
        clsHist.append(clsTotal.count(n))
    print('new clsHist is {}'.format(clsHist))

    return classIndListTotal


def xmlToRefineDetTxt(xmlDir, trainDataFile=0, testDataFile=0):
    listFileNameTotal = list()
    clsListTotal = list()
    imageNameTotal = list()
    infoBoxListTotal = list()
    nameList = list()

    xmlList =Getfiles(xmlDir, [".xml"])
    imgList = Getfiles(xmlDir)
    # xmlList = glob.glob(os.path.join(xmlDir, '*.xml'))
    print("xml count {}".format(len(xmlList)))

    for xml in xmlList:
        # listFile.write(xml.replace('xml', 'jpg') + '\n')
        jpgName = xml.replace('xml', 'jpg')
        pngName = xml.replace('xml', 'png')
        bmpName = xml.replace('xml', 'bmp')
        jpegName = xml.replace('xml', 'jpeg')
        # find image Name
        findFlag = False
        for imageName in [jpgName, pngName, bmpName, jpegName]:
            if imageName in imgList:
                findFlag = True
                break

        if not findFlag:
            continue
        infoBoxList = convert_annotation(xml, imageName)

        if len(infoBoxList) == 0:
            continue

        clsList = obtain_annotation(xml)
        listFileNameTotal.append(imageName)
        nameList.append(imageName)
        # listFileNameTotal.append(xml.replace('xml', 'jpg'))
        # nameList.append(xml.replace('xml', 'jpg'))
        clsListTotal.append(clsList)
        infoBoxListTotal.append(infoBoxList)

    # trainNum = int(np.ceil(len(clsListTotal) * 5./6))
    trainNum = int(np.ceil(len(clsListTotal)))
    trainListTotal = clsListTotal[0:trainNum]
    trainListTotalNew = GetNewList(classes, trainListTotal)

    nameListNew = list()
    for item in trainListTotalNew:
        result = '{}'.format(nameList[item])
        if len(infoBoxListTotal[item])==0:
            print(result)
        for n in range(len(infoBoxListTotal[item])):
            result = result + ' {} {} {} {} {}'.format(int(infoBoxListTotal[item][n][0]),
                                                       int(infoBoxListTotal[item][n][1]),
                                                       int(infoBoxListTotal[item][n][2]),
                                                       int(infoBoxListTotal[item][n][3]),
                                                       int(infoBoxListTotal[item][n][4]))
        nameListNew.append(result)
    random.shuffle(nameListNew)

    # save train file
    listFile = open(trainDataFile, 'w')
    for n in range(len(nameListNew)):
        if n == len(nameListNew) - 1:
            listFile.write(nameListNew[n])
        else:
            listFile.write(nameListNew[n] + '\n')
    listFile.close()
    print("save to file {} sucess".format(trainDataFile))

    # save test file
    listFile = open(testDataFile, 'w')
    #for item in range(trainNum, len(nameList)):
    for item in range(0, len(nameList)):
        # print(item)
        result = '{}'.format(nameList[item])
        # print("item {}".format(nameList[item]))
        for n in range(len(infoBoxListTotal[item])):
            result = result + ' {} {} {} {} {}'.format(int(infoBoxListTotal[item][n][0]),
                                                       int(infoBoxListTotal[item][n][1]),
                                                       int(infoBoxListTotal[item][n][2]),
                                                       int(infoBoxListTotal[item][n][3]),
                                                       int(infoBoxListTotal[item][n][4]))
        # print("result{}".format(result))
        # if item == len(nameList) - 1:
        #     listFile.write(result)
        # else:
        listFile.write(result + '\n')

    listFile.close()
    print("save to file {} sucess".format(testDataFile))


def JonToRefineDetTxt(Dir, trainDataFile, testDataFile):
    JsonToXml(Dir)
    xmlToRefineDetTxt(Dir, trainDataFile, testDataFile)


if __name__ == "__main__":
    trainDataFile = 'game_ai_sdk/tools/SDKTool/data/UIExplore/train_dataset.txt'
    testDataFile = 'game_ai_sdk/tools/SDKTool/data/UIExplore/test_dataset.txt'
    JonToRefineDetTxt('game_ai_sdk/tools/SDKTool/data/UIExplore/sample', trainDataFile, testDataFile)