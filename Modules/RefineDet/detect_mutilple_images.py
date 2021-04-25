# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import sys
import platform
__is_windows_system = platform.platform().lower().startswith('window')
__is_linux_system = platform.platform().lower().startswith('linux')
if __is_windows_system:
    sys.path.append(os.path.dirname(__file__))
    sys.path.append(os.path.join(os.path.dirname(__file__), 'windows'))
    from windows.detect_mutilple_images_util import main
elif __is_linux_system:
    sys.path.append(os.path.dirname(__file__))
    sys.path.append(os.path.join(os.path.dirname(__file__), 'ubuntu'))
    from ubuntu.detect_mutilple_images_util import main
else:
    raise Exception('system is not support!')


"""
parser.add_argument('--onnx_model',
                    default='./weights/Refine_hc2net_version3_320/model/Refine_hc2net_version3_self_dataset_epoches_55.onnx',
                    type=str, help='output onnx model')
parser.add_argument('--trained_model',
                    default='./weights/Refine_hc2net_version3_320/model/Refine_hc2net_version3_self_dataset_epoches_55.pth',
                    type=str, help='output onnx model')
## post processing
parser.add_argument('--obj_thresh', default=0.50, type=float, help='object threshold for testing')
parser.add_argument('--nms_thresh', default=0.45, type=float, help='nms threshold for testing')
## src images
parser.add_argument('-f', '--test_images', default='./test_UI', help='folder of test images')
## show result
parser.add_argument('--show_result', default=False, type=str2bool, help='Show result')
"""


if __name__ == '__main__':
    main()
