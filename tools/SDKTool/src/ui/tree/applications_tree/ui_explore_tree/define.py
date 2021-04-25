# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

TOP_LEVEL_TREE_KEYS = \
    [
        '配置样本',
        'Step1: 样本自动标记',
        'Step2: 样本重标记',
        'Step3: 训练',
        'Step4: 执行',
        'Step5: UI自动化探索结果',
    ]

# 序号必须与TOP_LEVEL_TREE_KEYS一一对应
CHILD_ITEM_KEYS = \
    [
        ['路径', '实时生成样本'],
        ['开始自动标记'],
        ['样本修改', '打包样本'],
        ['训练参数设置', '开始训练', '停止训练', '结果分析'],
        ['运行参数设置', '开始执行', '停止运行'],
        ['图分析', '覆盖率分析', "UI详细覆盖分析"],
    ]

# 序号必须与CHILD_ITEM_KEYS一一对应
QICON_IMGS = [
    [
        ":/menu/path.png",
        ":/menu/app.png"
    ],
    [
        ":/menu/operation.png"
    ],
    [
        ":/menu/file.png",
        ":/menu/save1.png"
    ],
    [
        ":/menu/settings.png",
        ":/menu/operation.png",
        ":/menu/operation.png",
        ":/menu/analysis.png"
    ],
    [
        ":/menu/settings.png",
        ":/menu/operation.png",
        ":/menu/operation.png"
    ],
    [
        ":/menu/analysis.png",
        ":/menu/switch.jpg",
        ":/menu/switch.jpg"
    ],
]

PATH_NAME_LIST = [
    '路径',
    'path',
]

TRAIN_LOG_DIR = './data/log.txt'

AUTO_LABEL = 0
USR_LABEL = 1
TRAIN = 2
EXPLORE_RESULT = 3


TRAIN_PARAMS = \
    {
        "微调次数": 5,
        "batch_size": 4,
        "num_workers": 4,
        "is_debug": 1
    }


int_Number_Key = \
    {
        "微调次数",
        "MaxClickNumber",
        "WaitTime",
        "num_workers",
        "batch_size",
        "is_debug"
    }

BOOL_PARAMS_KEYS = [
    "ComputeCoverage",
    "ShowButton"
]

RUN_PARAMS = {
    "MaxClickNumber": 100,
    "WaitTime": 4,
    "ComputeCoverage": True,
    "ShowButton": True,
    "EnvPackage": "UIAuto",
    "EnvModule": "AppExploreEnv",
    "EnvClass": "Env",
    "AIModelPackage": "UIAuto",
    "AIModelModule": "AppExploreAI",
    "AIModelClass": "AI"
}

ITEM_TYPE_IMAGE = "image"
ITEM_TYPE_IMAGE_FLODER = "imagefloder"


UI_AUTO_EXPLORE_RUN_FILTER_KEYS = ["ComputeCoverage"]
