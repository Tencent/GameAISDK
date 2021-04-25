# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import json
import logging
import shutil
import tarfile
import os
from collections import OrderedDict
import numpy as np
import cv2
from qtpy import QtWidgets
from qtpy import QtGui
from qtpy import QtCore

from PyQt5.QtWidgets import QComboBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap, QIcon
from PyQt5.QtWidgets import QTreeWidgetItem, QTreeWidgetItemIterator, QPushButton

from ..common.define import UI_HIDDEN_KEYS, SCENE_HIDDEN_KEYS, Mode, Number_Float_Key, Number_Int_Key, \
    BOOL_Keys, VALID_SYMBOL, ITEM_TYPE_IMAGE, ITEM_TYPE_IMAGE_FLODER, BOOL_FLAGS, \
    LEARNING_CONFIG_EXCITATIONFUNCTION_Key, LEARNING_CONFIG_TASKID_LIST
from ..ui.dialog.label_dialog import LabelDialog
from ..ui.main_window.tool_window import ui
from ..ui.tree.project_data_manager import g_project_data_mgr, change_image_path
from ..config_manager.task.task_manager import TaskManager
from .dialog.tip_dialog import show_warning_tips
from ..common.define import AI_NAME

logger = logging.getLogger("sdktool")


def create_tree_item(key=None, value=None, node_type=None, edit=True):
    child = QTreeWidgetItem()
    child.setText(0, str(key))
    if value is not None:
        child.setText(1, str(value))

    if node_type is not None:
        child.setText(2, node_type)

    if edit is True:
        child.setFlags(child.flags() | Qt.ItemIsEditable)
    return child


def show_critical_item(item):
    if item is None:
        return

    if item.text(0) in UI_HIDDEN_KEYS:
        if item.childCount() > 0:
            item.setExpanded(False)
        else:
            item.setHidden(True)
        return

    if item.text(0) in SCENE_HIDDEN_KEYS:
        if item.childCount() > 0:
            item.setExpanded(False)
        else:
            item.setHidden(True)
        return

    count = item.childCount()
    if count > 0:
        for index in range(count):
            sub_item = item.child(index)
            show_critical_item(sub_item)
    return


def show_detail_item(item):
    iterator = QTreeWidgetItemIterator(item)
    while iterator.value() is not None:
        iterator.value().setHidden(False)
        iterator.__iadd__(1)


def show_work_tree(tree, mode):
    if tree is None:
        return

    if mode not in [Mode.UI, Mode.SCENE, Mode.AI, Mode.RUN, Mode.UI_AUTO_EXPLORE]:
        return

    project_node = tree.topLevelItem(0)
    nodes = get_sub_nodes(project_node)
    for node in nodes:
        key = node.text(0)
        if (mode == Mode.UI and key == 'UI') or \
                (mode == Mode.SCENE and key == 'Scene') or \
                (mode == Mode.AI and key == 'AI') or \
                (mode == Mode.RUN and key == 'Run') or \
                mode == Mode.UI_AUTO_EXPLORE:
            node.setExpanded(True)
        else:
            node.setExpanded(False)


def get_value(value, key: str, default):
    if not isinstance(value, dict):
        return default
    if key not in value.keys():
        return default
    return value[key]


def is_video(url):
    suffix = url.split('.')[-1]
    return suffix in ['mp4', 'avi']


def is_image(url):
    suffix = url.split('.')[-1]
    return suffix in ['jpg', 'png', 'bmp']


def is_float_number(number: str):
    try:
        float(number)
        return True

    except ValueError:
        return False


def is_number(number: str):
    if is_int_number(number) or is_float_number(number):
        return True
    return False


def is_int_number(number: str):
    try:
        int(number)
        return True

    except ValueError:
        return False


def is_json_file(file_name: str):
    try:
        with open(file_name) as f:
            json.load(f)
        return True
    except IOError as err:
        logger.error("err: %s", str(err))
        return False


def get_sub_nodes(parent):
    nodes = list()
    if parent is None:
        return nodes

    for index in range(parent.childCount()):
        node = parent.child(index)
        nodes.append(node)

    return nodes


def get_ai_node_by_type(left_tree, node_type):
    project_node = left_tree.topLevelItem(0)
    if len(project_node.text(0)) == 0:
        show_warning_tips("please new project first")
        return False

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

    sub_nodes = get_sub_nodes(ai_node)

    for node in sub_nodes:
        if node.text(0) == node_type:
            return node, ai_node

    return None, ai_node


def _recursive_get_item_value_by_type(item_type, parent, result):
    if not parent:
        return

    if parent.text(2) == item_type:
        result.append(parent.text(1))
        return

    sub_nodes = get_sub_nodes(parent)
    for sub_node in sub_nodes:
        _recursive_get_item_value_by_type(item_type, sub_node, result)


def get_item_value_by_type(item_type, parent):
    """ 查找节点parent下的指定类型的项的值

    :param item_type:
    :param parent:
    :return:
    """
    result = []
    _recursive_get_item_value_by_type(item_type, parent, result)
    cnt = len(result)
    if cnt == 0:
        return None
    if cnt == 1:
        return result[0]
    raise ValueError('found multi-result')


def _recursive_get_item_by_type(item_type, parent, result):
    if not parent:
        return

    parent_type = parent.text(2)
    if parent_type == item_type:
        result.append(parent)
        return

    sub_nodes = get_sub_nodes(parent)
    for sub_node in sub_nodes:
        _recursive_get_item_by_type(item_type, sub_node, result)


def get_item_by_type(item_type, parent):
    """ 查找节点parent下的指定类型的项

    :param item_type:
    :param parent:
    :return:
    """
    result = []
    _recursive_get_item_by_type(item_type, parent, result)
    return result


def get_tree_top_nodes(tree):
    nodes = list()
    for index in range(tree.topLevelItemCount()):
        node = tree.topLevelItem(index)
        nodes.append(node)
    return nodes


def is_roi_invalid(roi_node):
    if roi_node is None:
        return False

    w = int(roi_node.child(2).text(1))
    h = int(roi_node.child(3).text(1))

    if w == 0 and h == 0:
        return False
    return True


def valid_number_value(config=None):
    if config is None:
        return

    for key, value in config.items():
        if isinstance(value, (str, int, float)):
            if key in Number_Int_Key:
                config[key] = int(float(value))
            elif key in Number_Float_Key:
                config[key] = float(value)
            elif key in BOOL_Keys:
                config[key] = (value == 'True')
        elif isinstance(value, (dict, OrderedDict)):
            valid_number_value(value)
        elif isinstance(value, (list)):
            for sub_value in value:
                if isinstance(sub_value, (dict, OrderedDict)):
                    valid_number_value(sub_value)


def clear_child(node):
    if node is None:
        return
    for _ in range(node.childCount()):
        node.takeChild(0)


def cvimg_to_qtimg(cvimg):
    cvimg = cvimg.astype('uint8')
    height, width, depth = cvimg.shape
    cvimg = cv2.cvtColor(cvimg, cv2.COLOR_BGR2RGB)
    Qimg = QImage(cvimg.data, width, height, width * depth, QImage.Format_RGB888)
    pixmap = QPixmap.fromImage(Qimg)

    return pixmap


def qtpixmap_to_cvimg(qtpixmap):
    qimg = qtpixmap.toImage()
    temp_shape = (qimg.height(), qimg.bytesPerLine() * 8 // qimg.depth())
    temp_shape += (4,)
    ptr = qimg.bits()
    ptr.setsize(qimg.byteCount())
    result = np.array(ptr, dtype=np.uint8).reshape(temp_shape)
    result = result[..., :3]
    result = result.astype('uint8')
    return result


def set_log_text(text: str):
    ui.set_text(text)


def save_action(node):
    if node is None:
        return

    params = OrderedDict()
    for roi_index in range(node.childCount()):
        action_item = node.child(roi_index)
        name = action_item.text(0)
        value = action_item.text(1)

        if action_item.childCount() > 0:
            params[name] = save_action(action_item)
        else:
            params[name] = value
    return params


def sdk_to_tool_path(config):
    project_data_path = g_project_data_mgr.get_project_data_path()
    sdk_data_path = g_project_data_mgr.get_sdk_data_path()
    change_image_path(config, sdk_data_path, project_data_path)


def tool_to_sdk_path(config):
    project_data_path = g_project_data_mgr.get_project_data_path()
    sdk_data_path = g_project_data_mgr.get_sdk_data_path()
    change_image_path(config, project_data_path, sdk_data_path)


class ExecResult(object):
    def __init__(self):
        self.flag = True


def filter_log(text, valid_log_levels):
    show_log = False
    cur_log_level = ''
    for level in valid_log_levels:
        if level in text:
            show_log = True
            cur_log_level = level
            break

    if not show_log:
        return ''

    valid_log = text.split(cur_log_level)[1]
    if len(valid_log.split(':')) > 1:
        str_valid_log = valid_log.split(':')[1]
    else:
        str_valid_log = valid_log
    return "[{}]: {}".format(cur_log_level, str_valid_log)


def filter_error_log(text):
    return filter_log(text, ['ERROR'])


def filter_warn_log(text):
    return filter_log(text, ['ERROR', 'WARN'])


def filter_info_log(text):
    return filter_log(text, ['ERROR', 'WARN', 'INFO'])


def filter_debug_log(text):
    return filter_log(text, ['ERROR', 'WARN', 'INFO', 'DEBUG'])


def right_tree_value_changed(canvas, node, column, pre_number_value):
    if node is None:
        logger.error("item value changed failed, current item is none")
        return
    logger.debug("right tree value changed key %s, value %s", node.text(0), node.text(1))
    if canvas.mouse_move_flag:
        logger.info("mouse is moving")
        return

    # key can not been changed
    if column == 0:
        return

    changed = True
    node_text0 = node.text(0)
    if node_text0 in Number_Int_Key:
        node_text1 = node.text(1)
        if node_text1 and not is_int_number(node_text1):
            changed = False
            dlg = LabelDialog(text="type of {} should be int".format(node.text(0)))
            dlg.pop_up()

    if node_text0 in Number_Float_Key:
        node_text1 = node.text(1)
        if node_text1 and not is_float_number(node_text1):
            changed = False
            dlg = LabelDialog(text="type of {} should be float".format(node.text(0)))
            dlg.pop_up()

    if not changed:
        node.setText(1, str(pre_number_value))


def is_str_valid(name: str):
    for word in name:
        if word not in VALID_SYMBOL:
            return False
    return True


def clear_files(dir_name, formats=None):
    """ 删除指定目录下的指定格式的文件

    :param dir_name:
    :param formats:
    :return:
    """
    if not formats:
        formats = [".png", ".bmp", ".jpg"]

    if not isinstance(formats, list):
        return

    if not dir_name or not os.path.exists(dir_name):
        return

    file_list = []
    for root, _, file_names in os.walk(dir_name):
        for file_name in file_names:
            if os.path.splitext(file_name)[1] in formats:
                file_list.append(os.path.join(root, file_name))

    for f in file_list:
        os.remove(f)


def get_files_count(dir_name, formats=None):
    if formats is None:
        formats = [".png", ".bmp", ".jpg"]

    if not dir_name or not os.path.exists(dir_name):
        return 0

    file_count = 0
    for _, _, file_names in os.walk(dir_name):
        for file in file_names:
            if os.path.splitext(file)[1] in formats:
                file_count = file_count + 1

    return file_count


def get_file_list(file_path, tree_item, level):
    """ 将file_path目录下的文件添加到树节点tree_item下

    :param file_path:
    :param tree_item:
    :param level:
    :return:
    """
    if tree_item is None:
        print("GetFileList failed, tree_item is None")
        return

    if not file_path or not os.path.exists(file_path):
        print("GetFileList failed, file_path is {}".format(file_path))
        return

    # 获取文件名
    child = QTreeWidgetItem()
    _, file_name = os.path.split(file_path)
    if level > 1:
        # 过滤某些特定文件
        if file_name in ["project.json", "task.json~", "project.json~"]:
            return

        # 创建树的节点，根据后缀名类型的不同来设置不同的icon
        extension = os.path.splitext(file_name)[1]
        if extension in [".jpg", ".png", ".bmp"]:
            child.setText(0, file_name)
            child.setText(2, ITEM_TYPE_IMAGE)
            child.setText(3, file_path)

            icon = QIcon()
            icon.addPixmap(QPixmap(":/menu/image-gallery.png"), QIcon.Normal, QIcon.Off)
            child.setIcon(0, icon)
            tree_item.addChild(child)

        elif extension in ["", ".0", ".1", ".2", ".3", ".4", ".5", ".6", ".7", ".8", ".9"]:
            child.setText(0, file_name)
            child.setText(2, ITEM_TYPE_IMAGE_FLODER)
            child.setText(3, file_path)

            icon = QIcon()
            icon.addPixmap(QPixmap(":/menu/file.png"), QIcon.Normal, QIcon.Off)
            child.setIcon(0, icon)
            tree_item.addChild(child)

        elif extension in [".json"]:
            return

    # 若dir为目录，则递归
    if os.path.isdir(file_path):
        child.setText(0, file_name)
        child.setText(2, ITEM_TYPE_IMAGE_FLODER)
        child.setText(3, file_path)

        items = []
        for item_name in os.listdir(file_path):
            items.append(os.path.join(file_path, item_name))
        items.sort()
        for file_item in items:
            if level > 1:
                get_file_list(file_item, child, level + 1)
            else:
                get_file_list(file_item, tree_item, level + 1)


def make_tar_gz(output_file, source_file):
    if None in [output_file, source_file]:
        raise ValueError("failed: input file or output file is None")
    if not os.path.exists(source_file):
        raise FileNotFoundError("failed: source file {} is not exists".format(source_file))

    with tarfile.open(output_file, "w:gz") as tar:
        tar.add(source_file, arcname=os.path.basename(source_file))
        return True


def create_bool_tree_item(value):
    """ 创建combobox item

    :param value:
    :return:
    """
    combobox = QComboBox()
    combobox.addItems(BOOL_FLAGS)
    combobox.setCurrentText(str(value))
    return combobox


def new_icon(icon):
    return QIcon(':/' + icon)


def new_button(text, icon=None, slot=None):
    b = QPushButton(text)
    if icon is not None:
        b.setIcon(new_icon(icon))
    if slot is not None:
        b.clicked.connect(slot)
    return b


def del_files(obj_dir):
    for root, dirs, files in os.walk(obj_dir):
        for name in files:
            file_path = os.path.join(root, name)
            os.remove(file_path)
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            shutil.rmtree(dir_path)


def get_image_list(folder_dir):
    result = []
    for path, _, file_list in os.walk(folder_dir):
        for file_name in file_list:
            if is_image(file_name):
                result.append(os.path.join(path, file_name))

    return result


def exchange_value(key, dictvalue):
    if key != LEARNING_CONFIG_EXCITATIONFUNCTION_Key:
        return dictvalue

    result = OrderedDict()
    for key_, value in dictvalue.items():
        if key_ in LEARNING_CONFIG_TASKID_LIST:
            result[key_] = __get_task_value(value)
        else:
            result[key_] = value
    return result


def __get_task_value(value):
    task_manager = TaskManager()
    task = task_manager.get_task()

    for sub_task in task.get_all():
        if sub_task[1] == value:
            return sub_task[0]
    return 0


def str_to_bool(value):
    return True if value.lower() == 'true' else False


def create_common_button_box(dialog, accept, reject):
    bb = QtWidgets.QDialogButtonBox(
        QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
        QtCore.Qt.Horizontal,
        dialog)

    bb.button(bb.Ok).setIcon(QtGui.QIcon(":/menu/done.png"))
    bb.button(bb.Cancel).setIcon(QtGui.QIcon(":/menu/undo.png"))
    bb.accepted.connect(accept)
    bb.rejected.connect(reject)
    return bb
