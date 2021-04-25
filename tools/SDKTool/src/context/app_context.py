# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

from ..common.singleton import Singleton


class AppContext(metaclass=Singleton):
    __init = False

    def __init__(self):
        super(AppContext, self).__init__()
        if not self.__init:
            self.__context_info = dict()
            self.__init = True

    def set_info(self, info_key: str, info_value) -> bool:
        if not isinstance(info_key, str):
            return False

        self.__context_info[info_key] = info_value
        return True

    def get_info(self, info_key: str, default_value=None):
        return self.__context_info.get(info_key, default_value)

g_app_context = AppContext()
