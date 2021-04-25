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
    from windows.detect_util import main
elif __is_linux_system:
    sys.path.append(os.path.dirname(__file__))
    sys.path.append(os.path.join(os.path.dirname(__file__), 'ubuntu'))
    from ubuntu.detect_util import main
else:
    raise Exception('system is not support!')

"""  
parser = argparse.ArgumentParser(description='RefineDet Training')
## basic configurations
parser.add_argument('-v', '--version', default='Refine_hc2net_version3',
                    help='Refine_vgg, Refine_mobile, Refine_hcnet, Refine_hc2net, Refine_hc2net_version2, Refine_hc2net_version3, '
                         'Refine_hc2net_version4, Refine_shufflenetv2, Refine_mobilenetv2, Refine_mobilenetv3, '
                         'Refine_mobilenetv3_version2, Refine_mobilenetv3_version3, Refine_resnet101, Refine_resnet101_heavy')
parser.add_argument('-s', '--size', default=320, type=int, help='320, 512 (512 support Refine_hc2net_version3, Refine_resnet101, Refine_resnet101_heavy)')
parser.add_argument('-d', '--dataset', default='self_dataset',  help='VOC, COCO, OpenImage500, Objects365 or self dataset')
parser.add_argument('--num_classes', default=5, type=int, help='number of classes, including background')
## pretained model
parser.add_argument('-m', '--trained_model',
                    default='weights/Refine_hc2net_version3_320/model/Final_Refine_hc2net_version3_self_dataset.pth',
                    type=str, help='Trained state_dict file path to open')
parser.add_argument('--onnx_model',
                    default='weights/Refine_hc2net_version3_320/model/Final_Refine_hc2net_version3_self_dataset.onnx',
                    type=str, help='output onnx model')
## post processing
parser.add_argument('-n', '--nms_type', default='soft', help='nms type: normal, soft')
parser.add_argument('--obj_thresh', default=0.50, type=float, help='object threshold for testing')
parser.add_argument('--nms_thresh', default=0.45, type=float, help='nms threshold for testing')
## src images
parser.add_argument('-f', '--test_images', default='./test_images', help='test images can be folder, image or txt file')
parser.add_argument('--image_nums', default=100, type=int, help='maximum number of test images, -1 means all images in test_images')
parser.add_argument('--save_folder', default='eval/', type=str, help='Dir to save results')
parser.add_argument('--label_list', default='./test_dataset.txt', type=str, help='test image label list')
## platform
parser.add_argument('--cuda', default=False, type=str2bool, help='Use cuda to train model')
parser.add_argument('--inference_platform', default='pytorch', type=str, help='inference platform: caffe2, pytorch')
"""

if __name__ == "__main__":
    main()
