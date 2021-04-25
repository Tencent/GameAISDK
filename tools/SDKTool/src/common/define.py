# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import sys
from enum import Enum, unique

from PyQt5.QtGui import QColor

# platform = sys.platform

STANDARD_WIDTH = 800
DEFAULT_MENU_WIDTH = 180

LOGPATH = './cfg/log.ini'
CFGPATH = './cfg/SDKTool.ini'

ITEM_TYPE_PROJECT = "project"
ITEM_TYPE_VERSION = "version"
ITEM_TYPE_SCENE = "scene"
ITEM_TYPE_TASK = "task"
ITEM_TYPE_ELEMENT = "element"
ITEM_TYPE_ELEMENT_NAME = "elementName"
ITEM_TYPE_ELEMENTS = 'elements'
ITEM_TYPE_TEMPLATE = "template"
ITEM_TYPE_TEMPLATES = 'templates'
ITEM_TYPE_UISTATE_ID = "uistateID"
ITEM_TYPE_GAME_HALL = "gamehall"
ITEM_TYPE_GAME_START = "gamestart"
ITEM_TYPE_GAME_OVER = "gameover"
ITEM_TYPE_CLOSE_ICONS = "closeicons"
ITEM_TYPE_GAME_POP_UI = "game pop ui"
ITEM_TYPE_DEVICE_POP_UI = "device pop ui"
ITEM_TYPE_UISTATES = "uistates"
ITEM_TYPE_UI_ELEMENT = "uielement"
ITEM_TYPE_IMAGE_FLODER = "imagefloder"
ITEM_TYPE_REFER_TASK = "refertask"
ITEM_TYPE_ACTIONSAMPLE = "actionsample"
ITEM_TYPE_ACTIONSAMPLE_ROOT = "actionsampleroot"
ITEM_TYPE_ACTIONSAMPLE_ELEMENT = "actionelement"
ITEM_TYPE_MAPPATH = "mappath"
ITEM_TYPE_MAPPATH_IMAGE = "mappathimage"
ITEM_TYPE_MAPPATH_LINEPATH = "mappathline"
ITEM_TYPE_MAPPATH_SINGLE_LINE = "mappathsingleline"
ITEM_TYPE_MAPPATH_GRAPH = "mapgraphpath"
ITEM_TYPE_MAPPATH_GRAPH_POINT = "mapgraphpathpoint"
ITEM_TYPE_MAPPATH_GRAPH_PATHS = "mapgraphpathpaths"
ITEM_TYPE_REFER_TEMPLATES = "refertemplates"
ITEM_TYPE_UI_SCRIPT_TASKS = "uiscripttasks"
ITEM_TYPE_UI_SCRIPT_TASK = "uiscripttask"
ITEM_TYPE_ACTION_REGION = "actionRegion"
ITEM_TYPE_UI_SCRIPT_TASK_ACTION = "uiscripttaskaction"
ITEM_TYPE_UI_ROI = "ROI"

ITEM_TYPE_TASK_IMG_PATH = "path"
ITEM_TYPE_IMAGE = "image"
# ITEM_TYPE_FOLDER = "folder"
ITEM_TYPE_PHONE_SERIAL = "phone_serial"

ITEM_ELEMENTS_NAME = 'elements'
ITEM_CONDITION_NAME = 'condition'
ITEM_CONDITIONS_NAME = 'Conditions'

DEVICE_SUCCESS_STATE = "device"

SCENE_TASKS_TYPE = "tasks"
TASK_TYPE_FIXOBJ = "fix object"
TASK_TYPE_PIX = "pixel"
TASK_TYPE_STUCK = "stuck"
TASK_TYPE_DEFORM = "deform object"
TASK_TYPE_NUMBER = "number"
TASK_TYPE_FIXBLOOD = "fix blood"
TASK_TYPE_DEFORMBLOOD = "deform blood"

task_type_list = [TASK_TYPE_FIXOBJ, TASK_TYPE_PIX, TASK_TYPE_STUCK, TASK_TYPE_DEFORM,
                  TASK_TYPE_NUMBER, TASK_TYPE_FIXBLOOD, TASK_TYPE_DEFORMBLOOD]

TASK_TYPE_REFER_LOCATION = "location"
TASK_TYPE_REFER_BLOODLENGTHREG = "bloodlengthreg"

refer_type_list = \
    [
        TASK_TYPE_REFER_LOCATION,
        TASK_TYPE_REFER_BLOODLENGTHREG
    ]

ALGORITHM_LOCATION_DETECT = "Detect"
ALGORITHM_LOCATION_INFER = "Infer"

refer_location_algorithm = \
    [
        ALGORITHM_LOCATION_DETECT,
        ALGORITHM_LOCATION_INFER
    ]

ALGORITHM_BLOODLENGTHREG_TAPLATEMATCH = "TemplateMatch"

ALGORITHM_FIXOBJ_COLORMATCH = "ColorMatch"
ALGORITHM_FIXOBJ_GRADMATCH = "GradMatch"
ALGORITHM_FIXOBJ_EDGEMATCH = "EdgeMatch"
ALGORITHM_FIXOBJ_ORBMATCH = "ORBMatch"

fix_obj_algorithm = \
    [
        ALGORITHM_FIXOBJ_COLORMATCH,
        ALGORITHM_FIXOBJ_GRADMATCH,
        ALGORITHM_FIXOBJ_EDGEMATCH,
        ALGORITHM_FIXOBJ_ORBMATCH
    ]


ALGORITHM_NUMBER_TEMPLATEMATCH = "TemplateMatch"


DEFAULT_MAXPOINTNUM = 512
DEFAULT_FILTERSIZE = 3
DEFAULT_DEFORM_THRESHOLD = 0.35
DEFAULT_TEMPLATE_THRESHOLD = 0.7
DEFAULT_STUCK_THRESHOLD = 0.99
DEFAULT_FIXOBJ_ALGORITHM = ALGORITHM_FIXOBJ_COLORMATCH
DEFAULT_NUMBER_ALGORITHM = ALGORITHM_NUMBER_TEMPLATEMATCH
DEFAULT_MINSCALE = 1.0
DEFAULT_MAXSCALE = 1.0
DEFAULT_SCALELEVEL = 1
DEFAULT_REFER_MINSCALE = 0.8
DEFAULT_REFER_MAXSCALE = 1.2
DEFAULT_REFER_SCALELEVEL = 9
DEFAULT_EXPANDWIDTH = 0.1
DEFAULT_EXPANDHEIGHT = 0.1
DEFAULT_MATCHCOUNT = 5
DEFAULT_INTERVALTIME = 5.0
DEFAULT_SKIPFRAME = 1
DEFAULT_BLOODLENGTH = 123

DEFAULT_MAX_BBOXNUM = 1

DEFAULT_UI_SHIFT = 20
DEFAULT_UI_KEYPOINT = 5

DEFAULT_UI_CHECK_SAME_FRAME = 10

DEFAULT_REFER_TYPE = TASK_TYPE_REFER_LOCATION
DEFAULT_REFER_LOCATION_ALGORITHM = ALGORITHM_LOCATION_DETECT

DEFAULT_TMPL_EXPD_W_PIXEL = 25
DEFAULT_TMPL_EXPD_H_PIXEL = 25
DEFAULT_EXPD_W_RATIO = 0.275
DEFAULT_EXPD_H_RATIO = 0.275

MAX_TEMPLATE_NUM = 20

TYPE_UIACTION_CLICK = "click"
TYPE_UIACTION_DRAG = "drag"
TYPE_UIACTION_DRAGCHECK = "dragcheck"
TYPE_UIACTION_SCRIPT = "script"
DEFAULT_UI_DRAG_CHECK_LENGTH = 80
DEFAULT_UI_DURING_TIME_MS = 100
DEFAULT_UI_SLEEP_TIME_MS = 100


TYPE_ACTIONSAMPLE_NONE = "none"
TYPE_ACTIONSAMPLE_DOWN = "down"
TYPE_ACTIONSAMPLE_UP = "up"
TYPE_ACTIONSAMPLE_CLICK = "click"
TYPE_ACTIONSAMPLE_SWIPE = "swipe"

ActionSampleMapType = {
    0: TYPE_ACTIONSAMPLE_NONE,
    1: TYPE_ACTIONSAMPLE_DOWN,
    2: TYPE_ACTIONSAMPLE_UP,
    3: TYPE_ACTIONSAMPLE_CLICK,
    4: TYPE_ACTIONSAMPLE_SWIPE
}

ActionSampleMapIndex = {
    TYPE_ACTIONSAMPLE_NONE: 0,
    TYPE_ACTIONSAMPLE_DOWN: 1,
    TYPE_ACTIONSAMPLE_UP: 2,
    TYPE_ACTIONSAMPLE_CLICK: 3,
    TYPE_ACTIONSAMPLE_SWIPE: 4
}


Click_Key = \
    [
        "actionX",
        "actionY",
        "actionThreshold",
        "actionTmplExpdWPixel",
        "actionTmplExpdHPixel",
        "actionROIExpdWRatio",
        "actionROIExpdHRatio"
    ]


Drag_Key = \
    [
        "actionX1",
        "actionY1",
        "actionThreshold1",
        "actionTmplExpdWPixel1",
        "actionTmplExpdHPixel1",
        "actionROIExpdWRatio1",
        "actionROIExpdHRatio1",
        "actionX2",
        "actionY2",
        "actionThreshold2",
        "actionTmplExpdWPixel2",
        "actionTmplExpdHPixel2",
        "actionROIExpdWRatio2",
        "actionROIExpdHRatio2"
    ]

Drag_Check_Key = \
    [
         "actionX",
         "actionY"
    ]

ROI_Key = \
    [
        "x",
        "y",
        'w',
        'h',
        "width",
        "height",
        "templateThreshold"
    ]

image_path_keys = \
    [
        'imgPath',
        'targetImg',
        'roiImg',
        'path',
        'maskPath'
    ]

file_path_keys = \
    [
        'scriptPath',
        'cfgPath',
        'weightPath',
        'namePath',
        'ActionCfgFile'
    ]

path_keys = image_path_keys + file_path_keys

# UI_HIDDEN_KEYS = Click_Key + Drag_Key + Drag_Check_Key + ROI_Key
UI_HIDDEN_KEYS = ['action', 'ROI', 'task']

action_keys = \
    [
        "actionX",
        "actionY",
        "actionX1",
        "actionY1",
        "actionX2",
        "actionY2"
    ]

positive_integer_value_keys = action_keys + \
    [
        'w',
        'h',
        "width",
        "height",
        "screenWidth",
        "screenHeight"
    ]

need_value_keys = path_keys + positive_integer_value_keys


rect_node_keys = \
    [
        'ROI',
        'location',
        'templateLocation',
        'region',
        'inner',
        'outer',
        'actionRegion',
        'roiRegion',
        'startRect',
        'endRect',
        'inferROI',
        'inferSubROI'
    ]

point_node_keys = \
    [
        'center',
        'startPoint',
        'endPoint'
    ]


SCENE_HIDDEN_KEYS = \
    [
        'groupID',
        'name',
        'minScale',
        'maxScale',
        'scaleLevel',
        'maxBBoxNum',
        'location',
        'classID',
        'filterSize',
        'maxPointNum',
        'intervalTime',
        'bloodLength',
        'templateLocation',
        'inferROI',
        'expandWidth',
        'expandHeight',
        'ROI'
    ]

UI_NAMES = \
    [
        'HallUI',
        'StartUI',
        'OverUI',
        'Game',
        'Device'
    ]


PHONE_BG_COLOR = QColor(70, 150, 200)


@unique
class Mode(Enum):
    PROJECT = 0
    UI = 1
    SCENE = 2
    AI = 3
    RUN = 4
    UI_AUTO_EXPLORE = 5


class MediaType(object):
    VIDEO = "Video"
    ANDROID = "Android"
    IOS = "IOS"
    WINDOWS = "Windows"


@unique
class DebugType(Enum):
    GameReg = 0
    UI = 1


@unique
class RunType(Enum):
    UI_AI = 0
    AI = 1
    AUTO_EXPLORER = 2


class RunTypeText(object):
    UI_AI = 'UI+AI'
    AI = 'AI'
    AUTO_EXPLORER = 'AutoExplorer'

algorithm_keys = dict()
algorithm_keys[TASK_TYPE_FIXOBJ] = fix_obj_algorithm
algorithm_keys[TASK_TYPE_REFER_LOCATION] = refer_location_algorithm


class AIAlgorithmType(object):
    IM = 1
    DQN = 2
    RAINBOW = 3

AI_CONFIG_DIR = 'cfg/task/agent/'
AI_CONFIG_ALGORITHM_PATH = "cfg/task/agent/Algorithm.json"
AI_CONFIG_IM_ACTION_PATH = "cfg/task/agent/ImitationAction.json"
AI_CONFIG_DQN_ACTION_PATH = "cfg/task/agent/DQNAction.json"
AI_CONFIG_RAINBOW_ACTION_PATH = "cfg/task/agent/RainbowAction.json"
AI_CONFIG_IM_LEARNING_PATH = "cfg/task/agent/ImitationLearning.json"
AI_CONFIG_DQN_LEARNING_PATH = "cfg/task/agent/DQNLearning.json"
AI_CONFIG_RAINBOW_LEARNING_PATH = "cfg/task/agent/RainbowLearning.json"
AI_CONFIG_IM_ENV_PATH = "cfg/task/agent/ImitationEnv.json"
AI_CONFIG_DQN_ENV_PATH = "cfg/task/agent/DQNEnv.json"
AI_CONFIG_RAINBOW_ENV_PATH = "cfg/task/agent/RainbowEnv.json"

UI_PATH = 'cfg/task/ui/UIConfig.json'
TASK_PATH = 'cfg/task/gameReg/Task.json'
REFER_PATH = 'cfg/task/gameReg/Refer.json'

__file_path = os.path.abspath(os.path.dirname(__file__))
SDK_PATH = '{}/../../../../'.format(__file_path)
ACTION_SAMPLE_PATH = '{}/../modules/action_sampler/'.format(__file_path)
# ACTION_SAMPLE_CFG_TEMPLATE_PATH = "{}/cfg/cfg_template.json".format(ACTION_SAMPLE_PATH)
ACTION_SAMPLE_CFG_PATH = "{}/cfg/cfg.json".format(ACTION_SAMPLE_PATH)
BASE_ACTION_CFG_PATH = 'cfg/action.json'
ACTION_SAMPLE_GAME_ACTION_CFG_PATH = "{}/{}".format(ACTION_SAMPLE_PATH, BASE_ACTION_CFG_PATH)


BIN_PATH = '{}/../../../../bin'.format(__file_path)

AICLIENT_PATH = 'AIClient' if sys.platform.startswith("win") else 'AIClient_ubuntu16'
PHONE_CLIENT_PATH = '{}/tools/{}/'.format(SDK_PATH, AICLIENT_PATH)

AI_SDK_DATA_PATH = SDK_PATH + 'data'
SDK_BIN_PATH = SDK_PATH + '/bin/'
DEBUG_UI_CMD = 'UIRecognize mode SDKTool'
DEBUG_GAME_REG_CMD = 'GameReg mode SDKTool'

TBUS_PATH = "cfg/bus.ini"


AI_NAME = "AI"
AI_ALGORITHM = 'Algorithm'
AI_ACTIONS = 'Actions'
AI_RESOLUTION = 'Resolution'

AI_DEFINE_ACTIONS = 'Define Actions'
AI_DEFINE_ACTION = 'Define Action'

AI_OUT_ACTIONS = 'AI Actions'
AI_OUT_ACTION = 'AI Action'

AI_ACTION_TYPES = [
    'down',
    'up',
    'click',
    'swipe',
    'joystick',
    'key'
]

DQN_ACTION_TYPES = [
    'down',
    'up',
    'click',
    'swipe',
    'key'
]

CONTACTS = [
    '0',
    '1',
    '2',
    '3',
    '4',
    '5'
]

VALID_RATIO = \
    [
        '0.1',
        '0.2',
        '0.3',
        '0.4',
        '0.5'
    ]

IM_TASK_VALUE = \
    [
        '0',
        '0,1',
        '1'
    ]

KEY_ACTION_VALUE = \
    [
        'click',
        'down',
        'up',
        'text'
    ]

AI_GAME_STATE = 'Game State'
AI_GAME_BEGIN = 'Begin'
AI_GAME_OVER = 'Over'

AI_PARAMETER = "Parameter"
AI_MODEL_PARAMETER = 'Model Parameter'
AI_ACTION_PARAMETERS = "Action Parameters"
AI_ACTION_PARAMETER = "Action Parameter"

AI_KEYS = [
    AI_NAME,
    AI_ALGORITHM,
    AI_PARAMETER,
    AI_ACTIONS,
    AI_DEFINE_ACTIONS,
    AI_DEFINE_ACTION,
    AI_OUT_ACTIONS,
    AI_OUT_ACTION,
    AI_GAME_STATE,
    AI_GAME_BEGIN,
    AI_GAME_OVER,
    AI_PARAMETER,
    AI_ACTION_PARAMETER,
    AI_ACTION_PARAMETERS,
    AI_MODEL_PARAMETER
]

DEFAULT_PROJECT_CONFIG_FOLDER = "Resource/project"
DEFAULT_TASK_IO_CONFIG_FOLDER = "cfg/task/io"
DEFAULT_TASK_MC_CONFIG_FOLDER = "cfg/task/mc"
DEFAULT_PLATFORM_CONFIG_FOLDER = "cfg/platform"
DEFAULT_DATA_IM_CONFIG_FOLDER = 'data/ImitationModel'
DEFAULT_DATA_IMAGES_FOLDER = 'data/images'

ELEMENT_TEMPLATE_JSON = "Resource/cfg/element_template.json"
REFER_TEMPLATE_JSON = "Resource/cfg/refer_template.json"
SUB_ITEM_TEMPLATE_JSON = "Resource/cfg/sub_item_template.json"

PRIOR = 'prior'
TASK = 'task'

# IM_PARAMETER_FILE = 'Resource/ImitationLearningParameter.json'
# DQN_PARAMETER_FILE = 'Resource/DqnLearningParameter.json'
# RAIN_BOW_PARAMETER_FILE = 'Resource/RainbowLearningParameter.json'
BOOL_FLAGS = [
    'True',
    'False'
]


Number_Int_Key = \
    [
        "groupID",
        "taskID",
        "task_id",
        "skipFrame",
        "scaleLevel",
        "classID",
        "x", "y", "w", "h",
        "bloodLength",
        "width",
        "height",
        "filterSize",
        "maxPointNum",
        "matchCount",
        "walkSpeed",
        "id",
        "shift",
        "actionX",
        "actionY",
        "actionX1",
        "actionY1",
        "actionX2",
        "actionY2",
        "keyPoints",
        "screenWidth",
        "screenHeight",
        "actionTmplExpdWPixel",
        "actionTmplExpdHPixel",
        "actionTmplExpdWPixel1",
        "actionTmplExpdHPixel1",
        "maxBBoxNum",
        "objTask",
        # "task",
        "actionAheadNum",
        "inputHeight",
        "inputWidth",
        "actionAheadNum",
        "useClassBalance",
        "classImageTimes",
        "actionPerSecond",
        "actionTimeMs",
        "trainIter",
        "timeStep",
        "contact",
        PRIOR,
        "FrameFPS",
        "FrameHeight",
        "FrameWidth",
        'quantizeNumber',
        'template',
        'duelingNetwork',
        'inputImgWidth',
        'inputImgHeight',
        'stateRecentFrame',
        'terminalDelayFrame',
        'framePerAction',
        'observeFrame',
        'exploreFrame',
        # 'initialEpsilon',
        # 'finalEpsilon',
        'qNetworkUpdateStep',
        'trainWithDoubleQ',
        # 'gpuMemoryFraction',
        # 'gpuMemoryGrowth',
        # 'checkPointPath',
        'trainFrameRate',
        'runType',
        # 'scoreTaskID',
        'maxScoreRepeatedTimes',
        'durationMS',
        "hostPort"
        # 'winTaskID',
        # 'loseTaskID'
    ]

Number_Float_Key = \
    [
        "expandWidth",
        "expandHeight",
        "minScale",
        "maxScale",
        "threshold",
        "intervalTime",
        "actionThreshold",
        "templateThreshold",
        "actionROIExpdWRatio",
        "actionROIExpdHRatio",
        "actionROIExpdWRatio2",
        "actionROIExpdHRatio2",
        "actionThreshold1",
        "actionROIExpdWRatio1",
        "actionROIExpdHRatio1",
        "actionThreshold2",
        "actionTmplExpdWPixel2",
        "actionTmplExpdHPixel2",
        "randomRatio",
        "validDataRatio",
        'rewardDiscount',
        'learnRate',
        'endLearnRate',

        'showImgState',
        'miniBatchSize',
        'initScore',
        'rewardOverRepeatedTimes',
        'winReward',
        'loseReward',
        'maxRunningReward',
        'minRunningReward',
        'rewardPerPostiveSection',
        'rewardPerNegtiveSection',
        'scorePerSection',
        'initialEpsilon',
        'finalEpsilon',
        'gpuMemoryFraction',
        'gpuMemoryGrowth',
        "memorySize"
    ]

Number_Key = Number_Int_Key + Number_Float_Key

BOOL_Keys = \
    [
        "Debug",
        "isSmallNet",
        "useResNet",
        "isMax",
        "useLstm",
        "OutputAsVideo",
        "LogTimestamp"
    ]

DISABLE_EDIT_KEYS = \
    [
        'id',
        'name',
        'taskName',
        'taskID'
    ]

# XXXLearning.json中定义的参数名称
LEARNING_CONFIG_EXCITATIONFUNCTION_Key = "excitationFunction"
LEARNING_CONFIG_STARTTASKID_KEY = "startTaskID"
LEARNING_CONFIG_SCORETASKID_KEY = "scoreTaskID"
LEARNING_CONFIG_WINTASKID_KEY = "winTaskID"
LEARNING_CONFIG_LOSETASKID_KEY = "loseTaskID"
LEARNING_CONFIG_TASKID_LIST = [LEARNING_CONFIG_STARTTASKID_KEY,
                               LEARNING_CONFIG_SCORETASKID_KEY,
                               LEARNING_CONFIG_WINTASKID_KEY,
                               LEARNING_CONFIG_LOSETASKID_KEY]

RUN_NAME = "Run"
TRAIN_NAME = "Train"
TEST_NAME = "Test"
CONFIG_RECORD = "Config Record"
START_RECORD = "Start Record"
STOP_RECORD = "Stop Record"
START_TRAIN = "Start Train"
STOP_TRAIN = "Stop Train"

TEST_CONFIG = "Config"
START_TEST = "Start Test"
STOP_TEST = "Stop Test"

RUN_KEYS = \
    [
        RUN_NAME,
        TRAIN_NAME,
        TEST_NAME,
        CONFIG_RECORD,
        START_RECORD,
        STOP_RECORD,
        START_TRAIN,
        STOP_TRAIN,
        START_TEST,
        STOP_TEST
    ]

# UI_EXPLORE_KEYS = \
#     [
#         'Step0: 配置样本',
#         'Step1: 样本自动标记',
#         'Step2: 样本重标记',
#         'Step3: 训练',
#         'Step4: UI自动化探索结果',
#         '样本修改'
#     ]

PROCESS_NAMES = \
    [
        "UI",
        "GameReg",
        "Agent"
    ]

LOG_LEVEL = \
    [
        "ERROR",
        "WARN",
        "INFO",
        "DEBUG"
    ]

RECORD_CONFIG_FILE = 'Resource/cfg/record_cfg.json'
RECORD_ANDROID_GUIDANCE_IMG = 'Resource/Sample_Record.PNG'
RECORD_WINDOWS_GUIDANCE_IMG = 'Resource/Sample_Record2.PNG'

UI_PROCESS_NAME = './UIRecognize'
GAMEREG_PROCESS_NAME = './GameReg'
if sys.platform == 'win32':
    UI_PROCESS_NAME = 'UIRecognize.exe'
    GAMEREG_PROCESS_NAME = 'GameReg.exe'


MC_PROCESS_AI_MODE_NAME = 'python manage_center.py --runType=%s' % RunTypeText.AI
MC_PROCESS_UI_AI_MODE_NAME = 'python manage_center.py --runType=%s' % RunTypeText.UI_AI
IO_PROCESS_NAME = 'python io_service.py'
AI_PROCESS_NAME = 'python agentai.py'
PHONE_CLIENT_PROCESS_NAME = 'python demo.py'

RUN_UI_AI_TEXTS = [
    MC_PROCESS_UI_AI_MODE_NAME,
    IO_PROCESS_NAME,
    AI_PROCESS_NAME,
    UI_PROCESS_NAME,
    GAMEREG_PROCESS_NAME
]

RUN_AI_TEXTS = [
    MC_PROCESS_AI_MODE_NAME,
    IO_PROCESS_NAME,
    AI_PROCESS_NAME,
    GAMEREG_PROCESS_NAME
]

SDK_RUN_MODE = [RunTypeText.UI_AI, RunTypeText.AI, RunTypeText.AUTO_EXPLORER]

WINDOW_WIDTH_NAME = 'window width:'
WINDOW_HEIGHT_NAME = 'window height:'
WINDOW_HANDLE_NAME = "window handle:"
WINDOW_QPATH_NAME = "window QPath:"
SPY_WINDOW_NAME = 'Spy Window'

LONG_EDGE = 'long edge:'
MULTI_RESOLUTION = 'multi resolution:'
RUN_TYPE_KEYWORD = 'run type:'
CANVAS_FPS_KEYWORD = 'canvas fps:'

DEFAULT_LONG_EDGE = 1280
MAX_LOG_LINE_NUM = 500

# SDKTool从Agent收到的动作ID (for android)
ACTION_ID_DOWN = 1
ACTION_ID_UP = 2
ACTION_ID_MOVE = 3
ACTION_ID_CLICK = 4
ACTION_ID_SWIPE = 5
ACTION_ID_SWIPEDOWN = 6
ACTION_ID_SWIPEMOVE = 7
ACTION_ID_INPUT_TEXT = 8
ACTION_ID_INPUT_KEY = 9

ACTION_NAMES = {
    ACTION_ID_DOWN: "down",
    ACTION_ID_UP: 'up',
    ACTION_ID_MOVE: 'move',
    ACTION_ID_CLICK: 'click',
    ACTION_ID_SWIPE: 'swipe',
    ACTION_ID_SWIPEDOWN: 'swipedown',
    ACTION_ID_SWIPEMOVE: 'swipemove',
    ACTION_ID_INPUT_TEXT: 'input_text',
    ACTION_ID_INPUT_KEY: 'input_key'
}

# SDKTool从Agent收到的动作ID (for windows)
WINDOW_ACTION_ID_MOUSE_MOVE = 0
WINDOW_MOUSE_LONG_CLICK = 1
WINDOW_MOUSE_DOUBLE_CLICK = 2
WINDOW_MOUSE_RIGHT_CLICK = 3
WINDOW_MOUSE_CLICK = 4
WINDOW_MOUSE_DRAG = 5
WINDOW_KEY_INPUT = 6
WINDOW_KEY_INPUT_STRING = 7
WINDOW_MOUSE_LBUTTON_DOWN = 8
WINDOW_MOUSE_LBUTTON_UP = 9
WINDOW_SIMULATOR_KEY = 10

WINDOW_ACTION_NAMES = {
    WINDOW_ACTION_ID_MOUSE_MOVE: "mousemove",
    WINDOW_MOUSE_LONG_CLICK: 'longclick',
    WINDOW_MOUSE_DOUBLE_CLICK: 'doubleclick',
    WINDOW_MOUSE_RIGHT_CLICK: 'rightclick',
    WINDOW_MOUSE_CLICK: 'click',
    WINDOW_MOUSE_DRAG: 'drag',
    WINDOW_KEY_INPUT: 'input',
    WINDOW_KEY_INPUT_STRING: 'inputstring',
    WINDOW_MOUSE_LBUTTON_DOWN: 'lbuttondown',
    WINDOW_MOUSE_LBUTTON_UP: 'lbuttonup',
    WINDOW_SIMULATOR_KEY: 'simulatorkey'
}

VALID_NUM = '0123456789'
VALID_WORD = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
VALID_SYMBOL = VALID_NUM + VALID_WORD


PORTRAIT = 'portrait'

# ttc resource
UMING_TTC = 'Resource/ttc/uming.ttc'

# pyplot_font
WIN_PYPLOT_FONT = 'SimHei'
LINUX_PYPLOT_FONT = 'Droid Sans Fallback'
