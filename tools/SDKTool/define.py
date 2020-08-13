# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

STANDARD_WIDTH = 800

LOGPATH = './cfg/log.ini'
CFGPATH = './cfg/SDKTool.ini'

ITEM_TYPE_PROJECT = "project"
ITEM_TYPE_VERSION = "version"
ITEM_TYPE_SCENE = "scene"
ITEM_TYPE_TASK = "task"
ITEM_TYPE_ELEMENT = "element"
ITEM_TYPE_TEMPLATE = "template"
ITEM_TYPE_UISTATE_ID = "uistateID"
ITEM_TYPE_GAMEOVER = "gameover"
ITEM_TYPE_CLOSEICONS = "closeicons"
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
ITEM_TYPE_UI_SCRIPT_TASK = "uiscripttask"
ITEM_TYPE_UI_SCRIPT_TASK_ACTION = "uiscripttaskaction"

ITEM_TYPE_TASK_IMG_PATH = "path"
ITEM_TYPE_IMAGE = "image"
# ITEM_TYPE_FOLDER = "folder"

TASK_TYPE_FIXOBJ = "fix object"
TASK_TYPE_PIX = "pixel"
TASK_TYPE_STUCK = "stuck"
TASK_TYPE_DEFORM = "deform object"
TASK_TYPE_NUMBER = "number"
TASK_TYPE_FIXBLOOD = "fix blood"
TASK_TYPE_DEFORMBLOOD = "deform blood"

TASK_TYPE_REFER_LOCATION = "location"
TASK_TYPE_REFER_BLOODLENGTHREG = "bloodlengthreg"

ALGORITHM_LOCATION_DETECT = "Detect"
ALGORITHM_LOCATION_INFER = "Infer"
ALGORITHM_BLOODLENGTHREG_TAPLATEMATCH = "TemplateMatch"

ALGORITHM_FIXOBJ_COLORMATCH = "ColorMatch"
ALGORITHM_FIXOBJ_GRADMATCH = "GradMatch"
ALGORITHM_FIXOBJ_EDGEMATCH = "EdgeMatch"
ALGORITHM_FIXOBJ_ORBMATCH = "ORBMatch"


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
DEFAULT_UI_KEYPOINT = 100

DEFAULT_REFER_TYPE = TASK_TYPE_REFER_LOCATION
DEFAULT_REFER_LOCATION_ALGORITHM = ALGORITHM_LOCATION_DETECT

DEFAULT_TMPL_EXPD_W_PIXEL = 25
DEFAULT_TMPL_EXPD_H_PIXEL = 25
DEFAULT_EXPD_W_RATIO = 0.275
DEFAULT_EXPD_H_RATIO = 0.275

TYPE_UIACTION_CLICK = "click"
TYPE_UIACTION_DRAG = "drag"
TYPE_UIACTION_DRAGCHECK = "dragcheck"
TYPE_UIACTION_SCRIPT = "script"


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

Number_Key = {
    "groupID",
    "taskID",
    "skipFrame",
    "minScale",
    "maxScale",
    "scaleLevel",
    "threshold",
    "classID",
    "x", "y", "w", "h",
    "filterSize",
    "maxPointNum",
    "intervalTime",
    "expandWidth",
    "expandHeight",
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
    "keypoints",
    "screenWidth",
    "screenHeight"
}


Click_Key = \
    {
        "actionX",
        "actionY",
        "actionThreshold",
        "actionTmplExpdWPixel",
        "actionTmplExpdHPixel",
        "actionROIExpdWRatio",
        "actionROIExpdHRatio"
    }


Drag_Key = \
    {
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
    }

Drag_Check_Key = \
    {
        "actionX",
        "actionY",
    }
