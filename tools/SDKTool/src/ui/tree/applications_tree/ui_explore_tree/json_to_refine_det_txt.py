# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import json
import random

import xml.dom.minidom as xmlDoc
import xml.etree.ElementTree as ET
from collections import OrderedDict
import cv2
import numpy as np

PROD_MIN_SAMPLE_NUM = 2000
DEBUG_MIN_SAMPLE_NUM = 50


def create_element_text(xml, ele_tag, text_tag):
    node_value = xml.createTextNode(text_tag)
    node = xml.createElement(ele_tag)
    node.appendChild(node_value)
    return node


def json_to_xml(json_dir):
    json_paths = get_files(json_dir, [".json"])
    # print("json count is {}".format(len(json_paths)))

    for json_path in json_paths:
        with open(json_path, 'r') as json_file:
            json_data = json.load(json_file, object_pairs_hook=OrderedDict)

        file_path, _ = os.path.split(json_path)
        new_file_path = os.path.join(file_path, json_data['fileName'])
        if not os.path.exists(new_file_path):
            print('file(%s) is not found!' % new_file_path)
            continue

        img = cv2.imread(new_file_path)

        xml = xmlDoc.Document()
        annotation = xml.createElement('annotation')
        xml.appendChild(annotation)

        folder = create_element_text(xml, 'folder', 'LabelImg')
        annotation.appendChild(folder)

        filename = create_element_text(xml, 'filename', 'fileName')
        annotation.appendChild(filename)

        path = create_element_text(xml, 'path', os.path.join(json_dir, json_data['fileName']))
        annotation.appendChild(path)

        source = xml.createElement('source')
        database = create_element_text(xml, 'database', 'Unknown')
        source.appendChild(database)
        annotation.appendChild(source)

        size = xml.createElement('size')
        width = create_element_text(xml, 'width', str(img.shape[1]))

        size.appendChild(width)
        height = create_element_text(xml, 'height', str(img.shape[0]))
        size.appendChild(height)

        depth = create_element_text(xml, 'depth', str(img.shape[2]))
        size.appendChild(depth)
        annotation.appendChild(size)

        path = create_element_text(xml, 'segmented', '0')
        annotation.appendChild(path)

        for bbox in json_data['labels']:
            if bbox['w'] < 0:
                bbox['x'] = bbox['x'] + bbox['w']
                bbox['w'] = abs(bbox['w'])
            if bbox['h'] < 0:
                bbox['y'] = bbox['y'] + bbox['h']
                bbox['h'] = abs(bbox['h'])

            obj = xml.createElement('object')
            name = create_element_text(xml, 'name', bbox['label'])
            obj.appendChild(name)

            pose = create_element_text(xml, 'pose', 'Unspecified')
            obj.appendChild(pose)

            truncated = create_element_text(xml, 'truncated', '0')
            obj.appendChild(truncated)

            difficult = create_element_text(xml, 'difficult', '0')
            obj.appendChild(difficult)

            bndbox = xml.createElement('bndbox')
            xmin = create_element_text(xml, 'xmin', str(int(bbox['x'])))
            bndbox.appendChild(xmin)

            ymin = create_element_text(xml, 'ymin', str(int(bbox['y'])))
            bndbox.appendChild(ymin)

            xmax = create_element_text(xml, 'xmax', str(int(bbox['x']) + int(bbox['w'])))
            bndbox.appendChild(xmax)

            ymax = create_element_text(xml, 'ymax', str(int(bbox['y']) + int(bbox['h'])))
            bndbox.appendChild(ymax)

            obj.appendChild(bndbox)
            annotation.appendChild(obj)

        xml_path = json_path.replace('json', 'xml')
        f = open(xml_path, 'wb')
        f.write(xml.toprettyxml(indent='\t', newl='\n', encoding='utf-8'))
        f.close()


classes = [
    ['return'],
    ['close'],
    ['tag'],
    ['other']]


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


def get_files(directory_name, format_list=None):
    format_list = [".png", ".bmp", ".jpg", ".jpeg"] if format_list is None else format_list
    files = []
    file_count = 0
    for dir_path, _, file_names in os.walk(directory_name):
        for file in file_names:
            if os.path.splitext(file)[1] in format_list:
                file_count = file_count + 1
                # print("dir_path {}, dir_names {} file is {}".format(dir_path, dir_names, file))
                files.append("{}/{}".format(dir_path, file))

    return files


def convert_annotation(xml, image_name):
    in_file = open(xml)
    tree = ET.parse(in_file)

    root = tree.getroot()
    size = root.find('size')
    w = int(size.find('width').text)
    if w == 0:
        return []

    info_box_list = list()
    for obj in root.iter('object'):
        difficult = obj.find('difficult').text
        cls = obj.find('name').text
        for ind, classes_temp in enumerate(classes):
            if cls not in classes_temp or int(difficult) == 1:
                continue
            xmlbox = obj.find('bndbox')
            info_box = (float(xmlbox.find('xmin').text),
                        float(xmlbox.find('ymin').text),
                        float(xmlbox.find('xmax').text),
                        float(xmlbox.find('ymax').text), ind + 1)
            info_box_list.append(info_box)

    if os.path.exists(image_name):
        return info_box_list
    return []


def obtain_annotation(xml):
    in_file = open(xml)
    tree = ET.parse(in_file)

    root = tree.getroot()
    size = root.find('size')
    w = int(size.find('width').text)

    cls_list = list()

    if w == 0:
        return cls_list

    for obj in root.iter('object'):
        difficult = obj.find('difficult').text
        cls = obj.find('name').text
        for ind, classes_temp in enumerate(classes):
            if cls not in classes_temp or int(difficult) == 1:
                continue
            cls_id = ind
            cls_list.append(cls_id)

    return cls_list


def sample_ratio(sample_num, class_list, min_sample_num):
    if sample_num < min_sample_num:
        min_ratio = [min_sample_num * 0.1 / sample_num] * len(class_list)
    else:
        min_ratio = [0.1] * len(class_list)
    return min_ratio


def get_new_list(class_list, cls_list_total, min_sample_num):
    if len(class_list) == 0:
        return []
    # 所有样本的标签列表
    cls_total = list()
    # 每个标签包含的所有样本id
    class_ind_list = list()
    for i in range(len(class_list)):
        class_ind_list.append(list())

    sample_num = len(cls_list_total)

    # get index for different class_list
    for n in range(sample_num):
        cls_total = cls_total + cls_list_total[n]
        for i in range(len(class_list)):
            if i in cls_list_total[n]:
                class_ind_list[i].append(n)
    min_ratio = sample_ratio(sample_num, class_list, min_sample_num)

    # get total number for different class_list
    # 计算每类标签包含的框框数量
    cls_hist = list()
    for n in range(0, len(class_list)):
        cls_hist.append(cls_total.count(n))

    # add files for class_list with fewer samples
    total_sample_num = np.sum(cls_hist)

    min_sample_num = [total_sample_num * min_ratio[n] for n in range(len(min_ratio))]
    # 扩容每类标签的样本
    for idx, cls_value in enumerate(cls_hist):
        if cls_value == 0:
            continue
        class_time = int(np.ceil(min_sample_num[idx] * 1. / cls_value))
        class_ind_list[idx] = class_ind_list[idx] * class_time
    # 计算扩展后的样本id列表（有重复）
    class_ind_list_total = list()
    for class_ind_value in class_ind_list:
        class_ind_list_total = class_ind_list_total + class_ind_value

    # get index for different class_list
    cls_total = list()
    for value in class_ind_list_total:
        cls_total = cls_total + cls_list_total[value]

    # get total number for different class_list
    cls_hist = list()
    for n in range(0, len(class_list)):
        cls_hist.append(cls_total.count(n))

    return class_ind_list_total


def obj2str(info_box_list_total, idx, init_result):
    for n in range(0, len(info_box_list_total[idx])):
        result = init_result + ' {} {} {} {} {}'.format(int(info_box_list_total[idx][n][0]),
                                                        int(info_box_list_total[idx][n][1]),
                                                        int(info_box_list_total[idx][n][2]),
                                                        int(info_box_list_total[idx][n][3]),
                                                        int(info_box_list_total[idx][n][4]))
    return result


def xml_to_refine_det_txt(xml_dir, train_data_file=0, test_data_file=0, min_sample_num=2000):
    list_file_name_total = list()
    cls_list_total = list()
    info_box_list_total = list()
    name_list = list()

    xml_list = get_files(xml_dir, [".xml"])
    img_list = get_files(xml_dir)

    for xml in xml_list:
        # list_file.write(xml.replace('xml', 'jpg') + '\n')
        jpg_name = xml.replace('xml', 'jpg')
        png_name = xml.replace('xml', 'png')
        bmp_name = xml.replace('xml', 'bmp')
        jpeg_name = xml.replace('xml', 'jpeg')
        # find image Name
        find_flag = False
        for image_name in [jpg_name, png_name, bmp_name, jpeg_name]:
            if image_name in img_list:
                find_flag = True
                break

        if not find_flag:
            continue
        info_box_list = convert_annotation(xml, image_name)

        if len(info_box_list) == 0:
            continue

        list_file_name_total.append(image_name)
        name_list.append(image_name)  # 样本图片名称
        cls_list_total.append(obtain_annotation(xml))
        info_box_list_total.append(info_box_list)

    train_num = int(np.ceil(len(cls_list_total)))
    train_list_total = cls_list_total[0:train_num]
    train_list_total_new = get_new_list(classes, train_list_total, min_sample_num)

    name_list_new = list()
    for item in train_list_total_new:
        result = '{}'.format(name_list[item])
        result = obj2str(info_box_list_total, item, result)
        name_list_new.append(result)
    random.shuffle(name_list_new)

    # save train file
    list_file = open(train_data_file, 'w')
    for idx, value in enumerate(name_list_new):
        if idx == len(name_list_new) - 1:
            list_file.write(value)
        else:
            list_file.write(value + '\n')
    list_file.close()
    # print("save to file {} sucess".format(train_data_file))

    # save test file
    list_file = open(test_data_file, 'w')
    for idx, item in enumerate(name_list):
        result = obj2str(info_box_list_total, idx, item)
        list_file.write(result + '\n')

    list_file.close()


def json_to_refine_det_txt(file_dir, train_data_file, test_data_file, is_debug):
    min_sample_num = DEBUG_MIN_SAMPLE_NUM if is_debug else PROD_MIN_SAMPLE_NUM
    json_to_xml(file_dir)
    xml_to_refine_det_txt(file_dir, train_data_file, test_data_file, min_sample_num)
