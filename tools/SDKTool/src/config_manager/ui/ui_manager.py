# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import json
from collections import OrderedDict
from enum import Enum, unique

from .hall_ui import HallUI
from .close_icon_ui import CloseIconUI
from .start_ui import StartUI
from .over_ui import OverUI

from ...common.singleton import Singleton


@unique
class UIType(Enum):
    HALL_UI = 1
    CLOSE_ICON_UI = 2
    DEVICE_CLOSE_ICON_UI = 3
    START_UI = 4
    OVER_UI = 5


class UIManager(metaclass=Singleton):

    __init = False

    def __init__(self):
        super(UIManager, self).__init__()
        if not self.__init:
            self.__ui_object = dict()
            self.__ui_object[UIType.HALL_UI.value] = HallUI()
            self.__ui_object[UIType.CLOSE_ICON_UI.value] = CloseIconUI()
            self.__ui_object[UIType.DEVICE_CLOSE_ICON_UI.value] = CloseIconUI()
            self.__ui_object[UIType.START_UI.value] =  StartUI()
            self.__ui_object[UIType.OVER_UI.value] = OverUI()
            self.__init = True

    def init(self) -> bool:
        return True

    def finish(self) -> None:
        pass

    def get_ui(self, ui_type: int):
        return self.__ui_object.get(ui_type)

    def load_config(self, config_file: str) -> bool:
        try:
            with open(config_file, 'r', encoding='utf-8') as file:
                json_str = file.read()
            config = json.loads(json_str, object_pairs_hook=OrderedDict)
            if isinstance(config['uiStates'], list):
                hall_ui_config, start_ui_config = self._split_uistates_config(config['uiStates'])
                self.__ui_object[UIType.HALL_UI.value].load(hall_ui_config)
                self.__ui_object[UIType.START_UI.value].load(start_ui_config)
            if isinstance(config['gameOver'], list):
                self.__ui_object[UIType.OVER_UI.value].load(config['gameOver'])
            if isinstance(config['closeIcons'], list):
                self.__ui_object[UIType.CLOSE_ICON_UI.value].load(config['closeIcons'])
            if isinstance(config['devicesCloseIcons'], list):
                self.__ui_object[UIType.DEVICE_CLOSE_ICON_UI.value].load(config['devicesCloseIcons'])
            return True
        except (KeyError, FileNotFoundError):
            return False

    def clear_config(self) -> None:
        for key, ui_instance in self.__ui_object.items():
            ui_instance.clear()

    def dump_config(self, config_file: str) -> bool:
        try:
            config = OrderedDict()
            hall_ui_config = self.__ui_object[UIType.HALL_UI.value].dump()
            start_ui_config, start_ui_id = self.__ui_object[UIType.START_UI.value].dump()
            ui_states_config = []
            ui_states_config.extend(hall_ui_config)
            ui_states_config.extend(start_ui_config)
            config['matchStartState'] = start_ui_id
            config['uiStates'] = ui_states_config
            config['gameOver'] = self.__ui_object[UIType.OVER_UI.value].dump()
            config['closeIcons'] = self.__ui_object[UIType.CLOSE_ICON_UI.value].dump()
            config['devicesCloseIcons'] = self.__ui_object[UIType.DEVICE_CLOSE_ICON_UI.value].dump()
            json_str = json.dumps(config, indent=4, ensure_ascii=False)
            with open(config_file, 'w', encoding='utf-8') as file:
                file.write(json_str)
        except (KeyError, FileNotFoundError):
            return False
        return True

    def _split_uistates_config(self, uistates_config):
        start_ui_config = list()
        for i in range(len(uistates_config)-1, -1, -1):
            if uistates_config[i]['id'] >= 1000:
                start_ui_element = uistates_config.pop(i)
                start_ui_config.append(start_ui_element)
        return uistates_config, start_ui_config
