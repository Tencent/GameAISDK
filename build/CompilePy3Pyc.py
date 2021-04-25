# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import sys
import py_compile

excludedirs = ['modules']


def WalkerCompile(srcdir, dstdir):
    """
    Recursive compile python script
    """
    if not os.path.exists(dstdir):
        os.mkdir(dstdir)

    for filename in os.listdir(srcdir):
        if filename.startswith('.'):
            continue

        filePath = os.path.join(srcdir, filename)

        if filename.endswith('.py') and os.path.isfile(filePath):
            dstFilePath = os.path.join(dstdir, filename + 'c')
            print(filePath + ' --> ' + dstFilePath)
            ret = py_compile.compile(filePath, cfile=dstFilePath)
            if ret is None and sys.version.startswith('3'):
                print("--------------error happend, please check python src file--------------")
                sys.exit(1)

        if os.path.isdir(filePath):
            for curdir in excludedirs:
                if filename == curdir:
                    continue

            dstPath = os.path.join(dstdir, filename)
            WalkerCompile(filePath, dstPath)


if __name__ == "__main__":
    if len(sys.argv) == 3:
        WalkerCompile(sys.argv[1], sys.argv[2])
    else:
        print('please set py srcdir and pyc dstdir')
