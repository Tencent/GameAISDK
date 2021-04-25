# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

from .ui_explore.auto_label_image import auto_label_image_inst
from .ui_explore.user_label_image import user_label_image_inst
from .ui_explore.explore_result_evaluate import explore_result_evaluate_inst
from .ui_explore.explore_train import explore_train_inst
from .ui_explore.explore_run import explore_run_inst
from .ui_explore.auto_explore_config import auto_explore_cfg_inst


# ********************* 自动标记函数接口 *****************
def auto_save_label_path(path):
    """Save auto label path

    Save auto label path to disk for next load

    :param path: image label path, is dir

    :return: bool, represent result saving label path
    """
    auto_label_image_inst.auto_label_path = path
    return True


def auto_get_label_path():
    """Get label path

    Get label path in auto label stage

    :return: str, represent auto label path
    """
    return auto_label_image_inst.auto_label_path


def auto_start_label():
    """Start model to label image.

    Start model inference by subprocess for objects detect
    """
    auto_label_image_inst.begin_label()


# ********************* 样本重标记接口 *****************
def user_save_label_path(path):
    """Save user label path

    Save user label path for next load in user label stage

    :param path: str, represent user label path

    :return: bool, represent save result
    """
    user_label_image_inst.user_label_path = path
    return True


def user_get_label_path():
    """Get label path

    Get label path in user label stage

    :return: str, represent user label path
    """
    return user_label_image_inst.user_label_path


def user_save_image_label(file_name, image_path_name, scene_name, labels):
    """Save image label to file

    Save adjusted label to file

    :param file_name: image name
    :param image_path_name: full image path
    :param scene_name: image label belong to scene
    :param labels: image labels, for example:
        [{
            "x": 100,
            "y": 200,
            "width": 100,
            "height": 100,
        },]

    :return: bool, represent save result
    """
    return user_label_image_inst.save_label2file(file_name, image_path_name, scene_name, labels)


def user_get_image_label(image_path_name):
    """Get image labels info

    Get image labels by image_path_name

    :param image_path_name: image path, will convert label path(json format)

    :return: A list for multiple image labels, for example:
        {
            "fileName": "",
            "scene": "",
            "labels": [{
               "label": "",
               "name": "",
               "click_num": int,
               "points": [start_x, start_y, end_x, end_y]
            }]
        }
    """
    return user_label_image_inst.load_label_json(image_path_name)


def user_delete_image_and_label(image_path_name):
    """Delete image and image label

    Delete image by image path(image_path_name), delete image label by
    image_path_name(can convert to image label path)

    :param image_path_name: full image path

    :return: bool, represent delete result
    """
    return user_label_image_inst.delete_image_and_label(image_path_name)


# ********************* UI自动探索训练 *****************
def explore_train_get_data_path():
    """Get explore train data path

    Get explore train data path in train stage

    :return: str, represent train data path
    """
    return explore_train_inst.train_data_path


def explore_train_save_data_path(train_data_path):
    """Save train data path

    Save train data path for next load in train stage

    :param train_data_path: str, represent result evaluate path

    :return: bool, represent save result
    """
    explore_train_inst.train_data_path = train_data_path
    return True


def explore_train_get_params():
    """Get model train params

    Get model train params in train stage

    :return: a dict, represent model train params, if not set, will return {}, for example:
        {
            "epochs": 5
        }
    """
    return explore_train_inst.train_params_dict


def explore_train_save_params(train_params_dict):
    """Save model train params

    Save model train params for next load in train stage

    :param train_params_dict: dict, represent model train params

    :return: bool, represent save result
    """
    explore_train_inst.train_params_dict = train_params_dict
    return True


# ********************* UI自动探索运行 *****************
def explore_run_get_data_path():
    """Get explore run data path

    Get explore run data path in run stage

    :return: str, represent run data path
    """
    return explore_run_inst.run_data_path


def explore_run_save_data_path(run_data_path):
    """Save run data path

    Save run data path for next load in run stage

    :param run_data_path: str, represent result evaluate path

    :return: bool, represent save result
    """
    explore_run_inst.run_data_path = run_data_path
    return True


def explore_run_get_params():
    """Get model run params

    Get model run params in run stage

    :return: a dict, represent model run params, if not set, will return {}, for example:
        {
            "epochs": 5
        }
    """
    return explore_run_inst.run_params_dict


def explore_run_save_params(run_params_dict):
    """Save model run params

    Save model run params for next load in run stage

    :param run_params_dict: dict, represent model run params

    :return: bool, represent save result
    """
    explore_run_inst.run_params_dict = run_params_dict
    return True


# ********************* UI自动探索结果 *****************
def explore_result_get_path():
    """Get ui explore result evaluate path

    Get ui explore result evaluate path in result analysis stage

    :return: str, represent result evaluate path
    """
    return explore_result_evaluate_inst.result_evaluate_path


def explore_result_save_path(result_evaluate_path):
    """Save result evaluate path

    Save result evaluate path for next load in result analysis stage

    :param result_evaluate_path: str, represent result evaluate path

    :return: bool, represent save result
    """
    explore_result_evaluate_inst.result_evaluate_path = result_evaluate_path
    return True


def explore_result_graph_analysis():
    """Get graph analysis result

    Get graph analysis result loading from disk

    :return: a dict map represent graph analysis result, for example:
        {
            "image_name1": {
                "image": "1",
                "label": "1.json",
                "label_list": [{
                    "nextUI": "image_name2",
                    "x": 100,
                    "y": 200,
                    "w": 200,
                    "h": 200,
                    "clickNum": "5",
                }],
            },
            "image_name2": {
                ...
            },
        }
    """
    return explore_result_evaluate_inst.graph_analysis_result()


def explore_result_coverage_info():
    """Get coverage info

    Get coverage info loading from disk

    :return: a tuple that contain two element, which element is dict map, if coverage file not exist,
        will return ({}, {}), for example:
        ({
            "sampleNum": 10,
            "coverNum": 5,
            },{
                "sampleNum": 10,
                "coverNum": 5,
            }
        )
    """
    return explore_result_evaluate_inst.get_coverage_info()


def explore_result_coverage_detail():
    """Get coverage detail info

    Get coverage detail info loading from disk

    :return: a list, each element is dict map in list, if coverage file not exist,
        will return [],for example:
        [{
            "fileName": "1.jpg",
            "sampleNum": 5,
            "coverNum": 4,
            "coverage": 0.8
        },
        ]
    """
    return explore_result_evaluate_inst.get_coverage_detail()


def ui_explore_config_get():
    """Get ui explore config

    Get ui explore config before run ui explore service

    :return: a dict, represent ui explore config, if not set, will return {}, for example:
        {
            "UiExplore": {
                "OutputFolder": "data/run_result",
                "MaxClickNumber": 99,
                "WaitTime": 5
            },
            "ButtonDetection": {
                "ModelType": "RefineNet",
                "PthModelPath": "data/UIAuto/model/Refine_hc2net_version3_self_dataset_epoches_55.pth",
                "Threshold": 0.1,
                "MaskPath": ""
            },
            "UiCoverage": {
                "ComputeCoverage": True,
                "SampleFolder": "data/UIAuto/sample",
                "ORBThreshold": 0.05
            },
            "Debug": {
                "ShowButton": True,
                "ShowCostTime": False,
                "ShowImageRatio": 0.5,
                "TestGetState": False
            }
        }
    """
    return auto_explore_cfg_inst.get_auto_config_params()


def ui_explore_save_config(config_params):
    """Save ui explore config

    Save ui explore config before run ui explore service

    :param config_params: dict, represent ui explore config

    :return: bool, represent save result
    """
    return auto_explore_cfg_inst.save_auto_config_params(config_params)
