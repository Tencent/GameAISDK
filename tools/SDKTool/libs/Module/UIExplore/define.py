# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

TOP_LEVEL_TREE_KEYS = \
    [
        'Step1: 样本自动标记',
        'Step2: 样本重标记',
        'Step3: 训练',
        'Step4: UI自动化探索结果'
    ]
CHILD_ITEM_KEYS = \
    [
        ['路径', '开始自动标记'],
        ['路径', '样本修改', '开始重标记', '打包样本'],
        ['路径', '参数设置', '开始训练', '结果分析'],
        ['路径', '图分析', '覆盖率分析', "UI详细覆盖分析"]
    ]

PATH_NAME_LIST = ['路径', 'path']

UI_USR_LABEL_NAME = 'Step2: 样本重标记'
USR_LABEL_ITEM_NAME = '开始重标记'

TRAIN_LOG_DIR = './data/log.txt'

AUTO_LABEL = 0
USR_LABEL = 1
TRAIN = 2
EXPLORE_RESULT = 3


TRAIN_PARAMS = \
    {
        "微调次数": 5
    }


int_Number_Key = \
    {
        "微调次数"
    }
