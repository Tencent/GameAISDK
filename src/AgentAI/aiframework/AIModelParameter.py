# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

class AIModelParameter(object):
    """
    Agent AI model parameter, including env, module, model package and class etc
    provider the data class manage the parameter
    """
    def __init__(self, use_plugin_env, env_package, env_module, env_class, use_plugin_model, model_package
                 ,model_module, model_class, use_default_run_func):
        self.use_plugin_env = use_plugin_env
        self.env_package = env_package
        self.env_module = env_module
        self.env_class = env_class
        self.use_plugin_model = use_plugin_model
        self.model_package = model_package
        self.model_module = model_module
        self.model_class = model_class
        self.use_default_run_func = use_default_run_func
