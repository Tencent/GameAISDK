# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

from distutils.core import setup, Extension

MOD = 'tbus'
setup(name=MOD, ext_modules=[
        Extension(MOD,
                  sources=['tbus.c'],
                  include_dirs=['../../tbusdll/busdll'],
                  library_dirs=['./'],
                  libraries=['busdll'])])
