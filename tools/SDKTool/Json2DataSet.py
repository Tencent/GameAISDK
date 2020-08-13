# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import shutil

JSONPATH = "Images"
OUTPUTPATH = "res"

if os.path.exists("res/cv2_mask") is False:
    os.mkdir("res/cv2_mask")

if os.path.exists("res/json") is False:
    os.mkdir("res/json")

if os.path.exists("res/labelme_json") is False:
    os.mkdir("res/labelme_json")

if os.path.exists("res/pic") is False:
    os.mkdir("res/pic")

for file in os.listdir(JSONPATH):
    if os.path.splitext(file)[1] == ".json":
        fileName = os.path.splitext(file)[0]
        cmd = 'labelme_json_to_dataset -o ' + OUTPUTPATH + '/labelme_json/\"' + fileName + '\" ' + JSONPATH + '/\"' + file + '\"'
        os.system(cmd)
        shutil.copy(JSONPATH + '/' + file, OUTPUTPATH + '/json/' + file)
        shutil.copy(OUTPUTPATH + '/labelme_json/' + fileName + '/label.png', OUTPUTPATH + '/cv2_mask/' + fileName + '.png')
        shutil.copy(OUTPUTPATH + '/labelme_json/' + fileName + '/img.png', OUTPUTPATH + '/pic/' + fileName + '.png')