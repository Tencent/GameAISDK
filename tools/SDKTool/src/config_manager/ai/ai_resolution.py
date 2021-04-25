# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging
logger = logging.getLogger("sdktool")


class AIResolution(object):

    def __init__(self):
        self.__screen_height = None
        self.__screen_width = None

    def set_screen_height(self, screen_height) -> None:
        self.__screen_height = screen_height

    def set_screen_width(self, screen_width) -> None:
        self.__screen_width = screen_width

    def get_screen_height(self):
        return self.__screen_height

    def get_screen_width(self):
        return self.__screen_width

    def load(self, config: dict) -> bool:
        if not isinstance(config, dict):
            return False

        try:
            self.set_screen_height(config['screenHeight'])
            self.set_screen_width(config['screenWidth'])
        except KeyError as err:
            logger.error("load resolution err:{}".format(err))
            return False

        return True

    def dump(self) -> dict:
        config = dict()
        config['screenHeight'] = self.__screen_height
        config['screenWidth'] = self.__screen_width
        return config
