import os
import sys
import importlib
from APIDefine import *

parentdir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, parentdir + PLUGIN_TOUCH_DIR)

# 动态导入包，并获取组件对象
def GetPlatformInstance(serial=None, moduleName=None):
    if serial is None:
        logger = logging.getLogger(LOG_DEFAULT)
    else:
        logger = logging.getLogger(serial)
    try:
        if moduleName is None:
            module = importlib.import_module('PlatformDefault')
        else:
            module = importlib.import_module('PlatformWeTest')
        getInstance = getattr(module, "GetInstance")
        return getInstance()
    except Exception as e:
        logger.error(e)
        return None