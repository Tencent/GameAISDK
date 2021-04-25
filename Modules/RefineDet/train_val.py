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
    from windows.train_val_util import main
elif __is_linux_system:
    sys.path.append(os.path.dirname(__file__))
    sys.path.append(os.path.join(os.path.dirname(__file__), 'ubuntu'))
    from ubuntu.train_val_util import main
else:
    raise Exception('system is not support!')


"""
## basic configurations
parser.add_argument('-v', '--version', default='Refine_hc2net_version3',
                    help='Refine_vgg, Refine_mobile, Refine_hcnet, Refine_hc2net, Refine_hc2net_version2, Refine_hc2net_version3, '
                         'Refine_hc2net_version4, Refine_shufflenetv2, Refine_mobilenetv2, Refine_mobilenetv3, '
                         'Refine_mobilenetv3_version2, Refine_mobilenetv3_version3, Refine_resnet101, Refine_resnet101_heavy')
parser.add_argument('-s', '--size', default=320, type=int, help='320, 512 (512 support Refine_hc2net_version3, Refine_resnet101, Refine_resnet101_heavy)')
parser.add_argument('-d', '--dataset', default='self_dataset',  help='VOC, COCO, OpenImage500, Objects365 or self dataset')
parser.add_argument('--num_classes', default=5, type=int, help='number of classes, including background')
## train and test label lists
parser.add_argument('--train_label_list', default='train_dataset.txt', type=str, help='train label list')
parser.add_argument('--train_image_root', default='', type=str, help='training image root for openimage dataset')
parser.add_argument('--test_label_list', default='test_dataset.txt', type=str, help='test label list')
parser.add_argument('--test_image_root', default='', type=str, help='testing image root for openimage dataset')
## data augumentation
parser.add_argument('--augment', default=False, type=str2bool, help='use data augmentation or not')
parser.add_argument('--crop', default=False, type=str2bool, help='use crop for data augmentation of not ')
parser.add_argument('--rotate', default=False, type=str2bool, help='use ratota for data augmentation or not')
parser.add_argument('--noise', default=False, type=str2bool, help='use noise for data augmentation or not')
parser.add_argument('--train_shuffle', default=True, type=str2bool, help='shuffle training data or not')
## training setting
parser.add_argument('-b', '--batch_size', default=16, type=int, help='Batch size for training')
parser.add_argument('--num_workers', default=6, type=int, help='Number of workers used in dataloading')
parser.add_argument('--cuda', default=False, type=str2bool, help='Use cuda to train model')
parser.add_argument('--ngpu', default=3, type=int, help='gpus')
## post processing
parser.add_argument('-n', '--nms_type', default='normal', type=str, help='nms type: soft, normal')
parser.add_argument('--obj_thresh', default=0.01, type=float, help='object thresh for testing')
parser.add_argument('--nms_thresh', default=0.45, type=float, help='nms thresh for testing')
## training tricks
parser.add_argument('--weighted_classes', default=True, type=str2bool, help='use weighted classes or not')
parser.add_argument('--loc_loss_type', default='giou', type=str, help='smooth_l1, giou, iou')
parser.add_argument('--loss_type', default='IOUGuided_OHEM', type=str, help='OHEM, focal_loss, ghm_loss, libra, IOUGuided_OHEM, GIOUGuided_OHEM')
parser.add_argument('--IOU_guided_ratio', default=0.25, type=float, help='IOU guided ratio for IOUGuided_OHEM')
parser.add_argument('--weighted_IOU_Guided', default=True, type=str2bool, help='use weighted IOU guided loss or not')
parser.add_argument('--uncertainty_factor', default=True, type=str2bool, help='use uncertainty factor for multitask learning')
parser.add_argument('--basenet', default='./weights/Refine_hc2net_version3_self_dataset_epoches_55.pth', help='pretrained base model')
## learning rate relavent
parser.add_argument('--lr', '--learning-rate', default=1e-1, type=float, help='initial learning rate')
parser.add_argument('--momentum', default=0.96, type=float, help='momentum')
parser.add_argument('--resume_net', default=True, type=str2bool, help='resume net for retraining')
parser.add_argument('--resume_epoch', default=55, type=int, help='resume iter for retraining')
parser.add_argument('-max', '--max_epoch', default=60, type=int, help='max epoch for retraining')
parser.add_argument('-we', '--warm_epoch', default=2, type=float, help='warm epoch for retraining')
parser.add_argument('--weight_decay', default=5e-4, type=float, help='Weight decay for SGD')
parser.add_argument('--gamma', default=0.1, type=float, help='Gamma update for SGD')
parser.add_argument('--adjust_type', default='step', type=str, help='learning rate adjusting type: step, cosine')
## loss weight
parser.add_argument('--anchor_class_loss_ratio', default=1.0, type=float, help='anchor class loss ratio')
parser.add_argument('--class_loss_ratio', default=1.0, type=float, help='class loss ratio')
## save and print
parser.add_argument('--save_folder', default='weights', help='Location to save checkpoint models')
parser.add_argument('--date', default='model')
parser.add_argument('--save_frequency', default=10, type=int, help='how many epoches to save model')
parser.add_argument('--print_frequency', default=1, type=int, help='how many iters to print loss')
parser.add_argument('--retest', default=False, type=str2bool, help='test cache results')
parser.add_argument('--test_frequency', default=10, type=int, help='how many epoches to test model')
## random seed
parser.add_argument('--rand_seed', type=int, default=2,  help='seed for torch ramdom')
"""


if __name__ == "__main__":
    main()
