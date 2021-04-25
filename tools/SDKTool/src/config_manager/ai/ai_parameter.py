# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging
from collections import OrderedDict


logger = logging.getLogger("sdktool")


class AiParameter(object):

    def __init__(self):
        self.__ai_parameter_cfg = OrderedDict()

    def set_config(self, config: OrderedDict) -> None:
        self.__ai_parameter_cfg.clear()
        for key, value in config.items():
            self.__ai_parameter_cfg[key] = value
        return True

    def get_config(self) -> OrderedDict:
        return self.__ai_parameter_cfg

    def load(self, config: OrderedDict) -> bool:
        return self.set_config(config)

    def clear(self) -> None:
        self.__ai_parameter_cfg.clear()

    def dump(self):
        return self.get_config()
