# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging
from abc import abstractmethod
from collections import OrderedDict

from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5.QtWidgets import QTreeWidgetItem, QComboBox
from PyQt5 import QtGui

from ...canvas.shape import Shape
from ....common.define import AI_NAME, AI_ACTIONS, AI_DEFINE_ACTIONS, AI_DEFINE_ACTION, AI_OUT_ACTIONS, AI_OUT_ACTION, \
                              AI_RESOLUTION, BOOL_FLAGS, DISABLE_EDIT_KEYS, Mode, CONTACTS, KEY_ACTION_VALUE, \
                              IM_TASK_VALUE, ITEM_TYPE_ACTION_REGION, image_path_keys, rect_node_keys, point_node_keys
from ....config_manager.ai.ai_manager import AIManager, AIType
from ....config_manager.task.task_manager import TaskManager
from ...canvas.ui_canvas import canvas, reset_canvas_roi, reset_canvas_action

from ...dialog.edit_dialog import EditDialog
from ...dialog.label_dialog import LabelDialog
from ...dialog.tip_dialog import show_warning_tips
from ..tree_manager import tree_mgr
from ...utils import get_tree_top_nodes, get_sub_nodes, create_tree_item, save_action, ExecResult, is_str_valid, \
    is_image
from ...main_window.tool_window import ui
from ..ai_tree.action_im_data import ImActionData
from ..ai_tree.action_dqn_data import DqnActionData
from ..ai_tree.action_rain_bow_data import RainBowActionData
from ....context.app_context import g_app_context


logger = logging.getLogger("sdktool")


class ActionNode(QObject):
    clear_right_tree_signal = pyqtSignal(ExecResult)

    def __init__(self):
        super().__init__()
        self.__left_tree = ui.tree_widget_left
        self.__right_tree = ui.tree_widget_right
        self.__define_action_node = None
        self.__out_action_node = None
        self.__resolution_node = None
        self.__slot_result = True
        self.__im_action_data = ImActionData()
        self.__dqn_action_data = DqnActionData()
        self.__rain_bow_data = RainBowActionData()

    def clear(self):
        self.__define_action_node = None
        self.__out_action_node = None
        self.__resolution_node = None
        self.__slot_result = True

    def create_node(self):
        # 查找 AI 节点
        result = ExecResult()
        self.clear_right_tree_signal.emit(result)
        if not result:
            return

        project_node = self.__left_tree.topLevelItem(0)
        if len(project_node.text(0)) == 0:
            show_warning_tips("please new project first")
            return

        ai_node = self.__get_ai_node(project_node)
        action_node = self.__get_action_node(ai_node)

        # 删除action下的子节点信息
        self.__remove_sub_action_node(action_node)

        # 创建分辨率节点信息
        self.__create_resolution_node(action_node)

        # 创建define action和ai_action
        self.__create_define_action_node(action_node)
        self.__create_out_action_node(action_node)

        # 创建每个game和ai每个元素的节点
        self._create_game_action_element_node()
        self.__create_ai_action_element_node()
        action_node.setExpanded(True)

    @abstractmethod
    def __get_ai_node(self, project_node):
        nodes = get_sub_nodes(project_node)
        ai_node = None
        for node in nodes:
            if node.text(0) == AI_NAME:
                ai_node = node
                break

        if ai_node is None:
            ai_node = create_tree_item(key='AI', edit=False)
            project_node.addChild(ai_node)
            project_node.setExpanded(True)
        return ai_node

    @abstractmethod
    def __get_action_node(self, ai_node):
        sub_nodes = get_sub_nodes(ai_node)
        action_node = None
        for node in sub_nodes:
            if node.text(0) == AI_ACTIONS:
                action_node = node
                break

        if action_node is None:
            action_node = create_tree_item(key=AI_ACTIONS, edit=False)
            ai_node.addChild(action_node)
            ai_node.setExpanded(True)

        return action_node

    @abstractmethod
    def __remove_sub_action_node(self, action_node):
        count = action_node.childCount()
        action_list = []

        for index in range(0, count):
            action_list.append(action_node.child(index))

        for action in action_list:
            action_node.removeChild(action)

    def __create_define_action_node(self, action_node):
        self.__define_action_node = create_tree_item(key=AI_DEFINE_ACTIONS, node_type=AI_DEFINE_ACTIONS, edit=False)
        action_node.addChild(self.__define_action_node)

    def __create_out_action_node(self, action_node):
        ai_mgr = AIManager()
        if ai_mgr.get_ai_type() == AIType.DQN_AI.value or ai_mgr.get_ai_type() == AIType.RAIN_BOW_AI.value:
            return

        self.__out_action_node = create_tree_item(key=AI_OUT_ACTIONS, node_type=AI_OUT_ACTIONS, edit=False)
        action_node.addChild(self.__out_action_node)

    def __create_resolution_node(self, action_node):
        ai_mgr = AIManager()
        if ai_mgr.get_ai_type() == AIType.IMITATION_AI.value:
            return

        self.__resolution_node = create_tree_item(key=AI_RESOLUTION, node_type=AI_RESOLUTION, edit=False)
        action_node.addChild(self.__resolution_node)

    def _create_game_action_element_node(self):
        ai_mgr = AIManager()
        game_action = ai_mgr.get_game_action(ai_mgr.get_ai_type())
        if game_action is None:
            return
        actions = game_action.get_all()
        for action in actions:
            self.__define_action_node.addChild(
                create_tree_item(key=action[1], value=str(action[0]), node_type=AI_DEFINE_ACTION, edit=False))
            self.__define_action_node.setExpanded(True)

    def __create_ai_action_element_node(self):

        if self.__out_action_node is None:
            return

        ai_mgr = AIManager()
        ai_action = ai_mgr.get_ai_action(ai_mgr.get_ai_type())
        if ai_action is None:
            return
        actions = ai_action.get_all()
        for action in actions:
            self.__out_action_node.addChild(
                create_tree_item(key=action[1], value=str(action[0]), node_type=AI_OUT_ACTION, edit=False))
            self.__out_action_node.setExpanded(True)

    def create_complex_node(self, key, value, root=None):
        # 0: key, 1:value, 2:type
        if root is None:
            sub_node = QTreeWidgetItem(self.__right_tree)
            sub_node.setText(0, key)
        else:
            sub_node = create_tree_item(key=key, edit=True)
            root.addChild(sub_node)
            root.setExpanded(True)

        logger.debug("value %s type %s", value, type(value))
        if isinstance(value, bool):
            combobox = QComboBox()
            combobox.addItems(BOOL_FLAGS)
            # combobox.setCurrentIndex(-1)
            combobox.setText(str(value))
            combobox.currentTextChanged.connect(self._combobox_text_changed)
            sub_node.setText(1, str(value))
            self.__right_tree.setItemWidget(sub_node, 1, combobox)

        elif isinstance(value, (int, float, str)):
            logger.debug("key %s value %s type str", key, value)
            sub_node.setText(1, str(value))
            if key not in DISABLE_EDIT_KEYS:
                sub_node.setFlags(sub_node.flags() | Qt.ItemIsEditable)

        elif isinstance(value, (dict, OrderedDict)):
            logger.debug("value %s type dict", value)
            for sub_key, sub_value in value.items():
                self.create_complex_node(key=sub_key, value=sub_value, root=sub_node)

            sub_node.setExpanded(True)

    def save_ai_action(self):
        action_params = OrderedDict()
        top_nodes = get_tree_top_nodes(self.__right_tree)
        for node in top_nodes:
            key = node.text(0)
            if node.childCount() == 0:
                value = node.text(1)
                action_params[key] = value
            elif node.text(0) == 'actionIDGroup':
                # actionIDGroup
                action_ids = []
                sub_nodes = get_sub_nodes(node)
                for sub_node in sub_nodes:
                    logger.debug("check state is %s, type %s", sub_node.checkState(0),
                                 type(sub_node.checkState(0)))
                    if sub_node.checkState(0) == Qt.Checked:
                        action_id = int(sub_node.text(1))
                        action_ids.append(action_id)
                action_params[key] = action_ids
            else:
                action_params[key] = save_action(node)
        if 'actionIDGroup' not in action_params:
            show_warning_tips('保存AI Actions失败，当前右树未包含actionIDGroup参数')
            return
        self._get_action_data().save_ai_action(action_params, self._get_action_data().get_ai_action_inner())

    def save_game_action(self):
        action_params = OrderedDict()
        top_nodes = get_tree_top_nodes(self.__right_tree)
        for node in top_nodes:
            key = node.text(0)
            if node.childCount() == 0:
                value = node.text(1)
                action_params[key] = value
            else:
                action_params[key] = save_action(node)

        self._get_action_data().save_game_action(action_params, self._get_action_data().get_game_action_inner())

    def new_ai_action(self):
        if None in [self.__out_action_node]:
            self.create_node()

        result = ExecResult()
        self.clear_right_tree_signal.emit(result)
        if not result.flag:
            logger.error("new ai action failed")
            return False

        dlg = EditDialog(label_text='name', default_edit='action name', title='input')
        dlg.edit.setFocus()
        self.__slot_result = True
        dlg.finish_signal.connect(self._new_ai_action)
        dlg.pop_up()
        if self.__slot_result:
            return True
        self.__slot_result = True
        return False

    def new_game_action(self):
        if None in [self.__define_action_node]:
            self.create_node()

        # 发送信号，接收信号，处理完了后，才会继续执行
        result = ExecResult()
        self.clear_right_tree_signal.emit(result)

        if not result.flag:
            return False

        dlg = EditDialog(label_text='name', default_edit='action name', title='input')
        dlg.edit.setFocus()
        # 初始化self.__slot_result为True
        self.__slot_result = True
        dlg.finish_signal.connect(self._new_game_action)
        dlg.pop_up()
        # 检查槽函数的执行结果
        if self.__slot_result:
            return True
        self.__slot_result = True
        return False

    def _new_game_none_action(self, action_name):
        if not self.check_name(action_name):
            show_warning_tips("name have already exist")
            return

        # 接收信号，处理完了后，才会继续执行
        result = ExecResult()
        self.clear_right_tree_signal.emit(result)

        if not result.flag:
            return

        self.__right_tree.clear()
        canvas.reset_state()

        # 构造右树
        game_action = self._get_action_data().get_game_action_inner()
        param = self._get_action_data().new_game_none_action(action_name, game_action)
        # 'none' 动作不可编辑
        for key, value in param.items():
            item = QTreeWidgetItem(self.__right_tree)
            item.setText(0, key)
            item.setText(1, str(value))

        # 构造左树
        action_id = param.get('id')
        action_node = create_tree_item(key=action_name, value=action_id, node_type=AI_DEFINE_ACTION, edit=False)
        self.__define_action_node.addChild(action_node)
        self.__define_action_node.setExpanded(True)

        tree_mgr.set_mode(Mode.AI)

    def new_game_none_action(self):
        if None in [self.__define_action_node]:
            self.create_node()

        dlg = EditDialog(label_text='name', default_edit='action name', title='input')
        dlg.edit.setFocus()
        dlg.finish_signal.connect(self._new_game_none_action)
        dlg.pop_up()

    def _new_game_action(self, action_name):
        if not self.check_name(action_name):
            show_warning_tips("name have already exist")
            self.__slot_result = False
            return

        # 检查命名是否合法(数字或是英文字符)
        if not is_str_valid(action_name):
            show_warning_tips('{} is not valid(char or num)'.format(action_name))
            self.__slot_result = False
            return

        self.__right_tree.clear()
        canvas.reset_state()

        # 构造右树
        param = self._get_action_data().new_game_action(action_name, self._get_action_data().get_game_action_inner())

        # 扩展参数由子类实现
        extend_param = self._get_action_data().game_action_extend_param()
        for key, value in extend_param.items():
            param[key] = value

        self._build_game_action_tree(param)

        # 构造左树
        action_id = param.get('id')
        action_node = create_tree_item(key=action_name, value=action_id, node_type=AI_DEFINE_ACTION, edit=False)
        self.__define_action_node.addChild(action_node)
        self.__define_action_node.setExpanded(True)

        tree_mgr.set_mode(Mode.AI)
        self.__slot_result = True

    def _build_contact_tree(self, key, value, item):
        if key == 'contact':
            combobox = QComboBox()
            combobox.addItems(CONTACTS)
            combobox.setCurrentText(str(value))
            combobox.currentTextChanged.connect(self._combobox_text_changed)
            self.__right_tree.setItemWidget(item, 1, combobox)

    def _build_scene_task_tree(self, key, value, item):
        if key == 'sceneTask':
            combobox = QComboBox()
            task_manager = TaskManager()
            task = task_manager.get_task()
            task_names = [sub_task[1] for sub_task in task.get_all()]
            task_ids = [sub_task[0] for sub_task in task.get_all()]
            # 无任务task时选择此项
            task_text = ''
            task_names.append(task_text)
            combobox.addItems(task_names)

            try:
                if value and value != -1:
                    id_index = task_ids.index(value)
                    task_text = task_names[id_index]
            except ValueError as err:
                logger.error("exception %s", err)

            item.setText(1, task_text)
            combobox.setCurrentText(task_text)
            combobox.currentTextChanged.connect(self._combobox_text_changed)

            self.__right_tree.setItemWidget(item, 1, combobox)

    def _build_type_tree(self, key, value, item):

        if key == 'type':
            # ‘none’动作需要特殊处理
            if value == 'none':
                return

            combobox = QComboBox()
            combobox.addItems(self._get_action_data().get_game_action_type_param())
            combobox.setCurrentText(value)
            combobox.currentTextChanged.connect(self._action_type_changed)
            self.__right_tree.setItemWidget(item, 1, combobox)

    @staticmethod
    def _change_edit_properties(key, item):
        # 修改属性的编辑属性
        if key not in DISABLE_EDIT_KEYS:
            item.setFlags(item.flags() | Qt.ItemIsEditable)

    def _build_game_action_tree(self, parameter):
        for key, value in parameter.items():
            item = QTreeWidgetItem(self.__right_tree)
            item.setText(0, key)
            if isinstance(value, (int, str)):
                item.setText(1, str(value))
                self._build_contact_tree(key, value, item)
                self._build_scene_task_tree(key, value, item)
                self._build_type_tree(key, value, item)
                self._change_edit_properties(key, item)
            elif isinstance(value, (dict, OrderedDict)):
                for sub_key, sub_value in value.items():
                    self.create_complex_node(key=sub_key, value=sub_value, root=item)

    def __get_parameter_node(self):
        top_level_nodes = get_tree_top_nodes(self.__right_tree)
        parameter_node = None
        for node in top_level_nodes:
            if node.text(0) == 'actionRegion':
                parameter_node = node
                break

        if parameter_node is None:
            parameter_node = QTreeWidgetItem(self.__right_tree)

        # 清空parameter_node的子节点
        for _ in range(parameter_node.childCount()):
            parameter_node.takeChild(0)

        return parameter_node

    def init_swipe_node(self):
        parameter_node = self.__get_parameter_node()
        # 构造参数
        params = self._get_action_data().init_swipe_params()

        # 重新创建节点
        for key, value in params.items():
            self.create_complex_node(key=key, value=value, root=parameter_node)

    def init_key_node(self):
        parameter_node = self.__get_parameter_node()
        params = self._get_action_data().init_key_params()
        for key, value in params.items():
            if key == 'actionType':

                sub_node = create_tree_item(key=key, edit=True)
                sub_node.setText(1, str(value))
                parameter_node.addChild(sub_node)
                parameter_node.setExpanded(True)

                combobox = QComboBox()
                combobox.addItems(KEY_ACTION_VALUE)
                combobox.setCurrentText(value)
                combobox.currentTextChanged.connect(self._key_action_type_change)
                self.__right_tree.setItemWidget(sub_node, 1, combobox)

            else:
                self.create_complex_node(key=key, value=value, root=parameter_node)

    def init_joy_stick_node(self):
        parameter_node = self.__get_parameter_node()

        # 构造参数
        params = self._get_action_data().init_joy_stick_params()

        # 重新创建节点
        for key, value in params.items():
            self.create_complex_node(key=key, value=value, root=parameter_node)

    def init_common_node(self):
        parameter_node = self.__get_parameter_node()
        params = self._get_action_data().get_type_param()

        for key, value in params.items():
            self.create_complex_node(key=key, value=value, root=parameter_node)

    def _action_type_changed(self, text):
        cur_node = self.__right_tree.currentItem()
        if cur_node is None:
            logger.error("not select right tree node")
            return False
        cur_node.setText(1, text)

        if text == 'joystick':
            self.init_joy_stick_node()
            cur_node.setExpanded(True)
        elif text == 'swipe':
            self.init_swipe_node()
            cur_node.setExpanded(True)
        elif text == 'key':
            self.init_key_node()
            cur_node.setExpanded(True)
        else:
            self.init_common_node()
            cur_node.setExpanded(True)

    def _build_ai_action_tree(self, parameter):
        for key, value in parameter.items():
            if key == 'actionIDGroup':
                item = QTreeWidgetItem(self.__right_tree)
                item.setText(0, key)
                game_actions = self.get_game_actions()
                # 把所有的game action显示在界面上
                for game_action in game_actions:
                    action_id = game_action[0]
                    action_name = game_action[1]
                    sub_item = create_tree_item(key=action_name, value=action_id, edit=False)
                    sub_item.setCheckState(0, Qt.Unchecked)
                    item.addChild(sub_item)
                    # 如果之前已经选中，需要恢复选中状态
                    for sub_id in value:
                        # sub_id, sub_name = sub_value
                        if sub_id == int(action_id):
                            sub_item.setCheckState(0, Qt.Checked)

                item.setExpanded(True)
            elif key == 'task':
                str_value = ''
                if len(value) == 2:
                    str_value = IM_TASK_VALUE[1]
                elif len(value) == 1:
                    str_value = str(value[0])
                item = QTreeWidgetItem(self.__right_tree)
                item.setText(0, key)
                item.setText(1, str_value)
                combobox = QComboBox()
                combobox.addItems(IM_TASK_VALUE)
                combobox.setCurrentText(str_value)
                combobox.currentTextChanged.connect(self._combobox_text_changed)
                self.__right_tree.setItemWidget(item, 1, combobox)

            else:
                self.create_complex_node(key=key, value=value)

    def _new_ai_action(self, name):
        if not self.check_name(name):
            show_warning_tips("name have already exist")
            self.__slot_result = False
            return

        # 检查命名是否合法(数字或是英文字符)
        if not is_str_valid(name):
            show_warning_tips('{} is not valid(char or num)'.format(name))
            self.__slot_result = False
            return

        # 清空右树
        # 清空画布
        self.__right_tree.clear()
        canvas.reset_state()

        # 构造右树
        action_value = self._get_action_data().new_ai_action(name, self._get_action_data().get_ai_action_inner())
        self._build_ai_action_tree(action_value)

        # 构造左树
        action_id = action_value.get('id')
        self.__out_action_node.addChild(create_tree_item(key=name, value=action_id,
                                                         node_type=AI_OUT_ACTION, edit=False))
        self.__out_action_node.setExpanded(True)

        tree_mgr.set_mode(Mode.AI)
        self.__slot_result = True

    def check_name(self, name):
        current_node = self.__left_tree.currentItem()
        if current_node is None:
            logger.error("current node is none in right tree")
            return False

        names = list()
        sub_nodes = get_sub_nodes(current_node)
        for sub_node in sub_nodes:
            names.append(sub_node.text(0))

        if name in names:
            return False

        return True

    def delete_action(self):
        node = self.__left_tree.currentItem()
        task_name = node.text(0)
        dlg = LabelDialog(text="please confirm to delete {} task ?".format(task_name), title="confirm")
        dlg.finish_signal.connect(lambda: self._delete_action(node))
        dlg.pop_up()

    def _delete_action(self, node):
        parent = node.parent()
        parent.removeChild(node)
        parent_type = parent.text(0)
        action_id = node.text(1)
        action_id = int(action_id)
        if parent_type == AI_DEFINE_ACTIONS:
            self._get_action_data().delete_game_action(action_id, self._get_action_data().get_game_action_inner())
        elif parent_type == AI_OUT_ACTIONS:
            self._get_action_data().delete_ai_action(action_id, self._get_action_data().get_ai_action_inner())
        self.__right_tree.clear()

    def get_game_actions(self):
        sub_nodes = get_sub_nodes(self.__define_action_node)
        actions = []
        for sub_node in sub_nodes:
            actions.append((sub_node.text(1), sub_node.text(0)))
        return actions

    def load_game_action(self, node):
        # result = ExecResult()
        # self.clear_right_tree_signal.emit(result)
        # if not result.flag:
        #     logger.error("load game action failed")
        #     return

        self.__right_tree.clear()
        canvas.reset_state()
        action_id = node.text(1)
        action_id = int(action_id)
        parameter = self._get_action_data().get_game_action(action_id, self._get_action_data().get_game_action_inner())
        self._build_game_action_tree(parameter)

        # 默认加载第一个actionRegion
        # 默认在画布加载第一个元素的图片
        node_count = self.__right_tree.topLevelItemCount()
        if self.__right_tree.topLevelItemCount() == 0:
            return

        for index in range(node_count):
            parent = self.__right_tree.topLevelItem(index)
            if parent.text(0) == ITEM_TYPE_ACTION_REGION:
                sub_nodes = get_sub_nodes(parent)
                img_path = None
                for sub_node in sub_nodes:
                    if sub_node.text(0) in image_path_keys:
                        _img_path = sub_node.text(1)
                        if is_image(_img_path):
                            img_path = _img_path
                            break
                if img_path:
                    pixmap = QtGui.QPixmap.fromImage(QtGui.QImage(img_path))
                    canvas.load_pixmap(pixmap)
                    shapes = []
                    self.__right_tree.setCurrentItem(parent)
                    for sub_node in sub_nodes:
                        key = sub_node.text(0)
                        if key in rect_node_keys:
                            canvas.set_rect_tree_item(sub_node)
                            canvas.set_editing()
                            shape = reset_canvas_roi(sub_node)
                            shapes.append(shape)
                            canvas.shape_tree[shape] = sub_node
                        elif key in point_node_keys:
                            shape = reset_canvas_action(sub_node)
                            shapes.append(shape)
                            canvas.shape_tree[shape] = sub_node

                    if shapes:
                        canvas.load_shapes(shapes)
                    canvas.update()

                    g_app_context.set_info("phone", False)

    def load_ai_action(self, node):
        action_id = node.text(1)
        action_id = int(action_id)
        parameters = self._get_action_data().get_ai_action(action_id, self._get_action_data().get_ai_action_inner())
        # result = ExecResult()
        # self.clear_right_tree_signal.emit(result)
        # if not result.flag:
        #     logger.error("load ai action failed")
        #     return

        self.__right_tree.clear()
        canvas.reset_state()
        self._build_ai_action_tree(parameters)

    def _combobox_text_changed(self, text):
        current_item = self.__right_tree.currentItem()
        current_item.setText(1, text)

    def _key_action_type_change(self, text):

        cur_node = self.__right_tree.currentItem()
        if cur_node is None:
            logger.error("not select right tree node")
            return False
        cur_node.setText(1, text)

        # if text == 'text':
        #     cur_node.

    def _get_action_data(self):
        ai_mgr = AIManager()
        ai_type = ai_mgr.get_ai_type()
        ai_type_value = None
        if ai_type == AIType.IMITATION_AI.value:
            ai_type_value = self.__im_action_data
        elif ai_type == AIType.DQN_AI.value:
            ai_type_value = self.__dqn_action_data
        elif ai_type == AIType.RAIN_BOW_AI.value:
            ai_type_value = self.__rain_bow_data
        return ai_type_value

    def new_canvas_shapes(self, nodes=None):
        canvas.reset_shapes()
        canvas.shapes.clear()
        canvas.mode = canvas.CREATE
        if nodes is None:
            nodes = self.get_top_level_nodes()
        for node in nodes:
            if node.text(0) in ['ROI', 'location', 'templateLocation', 'inferROI', 'inferSubROI']:
                canvas.set_rect_tree_item(node)
                canvas.current_model.append(Shape.RECT)
                canvas.set_editing(False)
