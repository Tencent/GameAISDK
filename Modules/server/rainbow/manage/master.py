# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import argparse
import queue
import time
import numpy as np
import torch

from log.log import LOG
from model.agent import Agent
from model.memory import ReplayMemory

MAX_WORKER_COUNT = 6
ACTION_SPACE = 3
LOG_FREQUENCY = 1000


class Master:
    """
    master, train AI model
    """

    def __init__(self):
        LOG.info('init master')

        self.__loop_count = 0
        self.__train_step = 0

        self.__args = self._set_args()
        LOG.info("the args is{}".format(self.__args))
        self.rainbow = Agent(self.__args, ACTION_SPACE)
        self.rainbow.train()

        self.__count_list = list()
        self.__queue_list = list()
        self.__memory_list = list()
        for _ in range(MAX_WORKER_COUNT):
            self.__count_list.append(0)
            self.__queue_list.append(queue.Queue())
            self.__memory_list.append(ReplayMemory(self.__args, self.__args.memory_capacity))

        self.__priority_weight_increase = (1 - self.__args.priority_weight) / (
                self.__args.T_max - self.__args.learn_start)

    def send_transition(self, index, state, action_index, reward, done):
        self.__queue_list[index].put((state, action_index, reward, done))
        return

    def __get_action_data(self, idx):
        while True:
            if not self.__queue_list[idx].empty():
                (state, action_index, reward, done) = self.__queue_list[idx].get()
                self.__memory_list[idx].append(state, action_index, reward, done)
                self.__count_list[idx] += 1
                return True
            return False

    def __get_train_data(self):
        index_list = list()
        for idx in range(MAX_WORKER_COUNT):
            if self.__get_action_data(idx) is True:
                index_list.append(idx)
        return index_list

    def __save_train_model(self):
        if self.__train_step % 2e4 == 0:
            st = time.time()
            self.rainbow.save('./Model/', name='model_{}.pth'.format(self.__train_step))
            et = time.time()
            cost_ime = ((et - st) * 1000)
            LOG.info('saving rainbow costs {} ms at train step {}'.format(cost_ime, self.__train_step))

    def __print_progress_log(self, start_time):
        if self.__loop_count % LOG_FREQUENCY == 0:
            cost_ime = ((time.time() - start_time) * 1000)
            LOG.info('train rainbow is {} ms at loop count {}'.format(cost_ime, self.__loop_count))

    def train(self):

        start_time = time.time()
        index_list = self.__get_train_data()

        if len(index_list) == 0:
            return

        for _ in range(3):
            i = np.random.randint(len(index_list))
            idx = index_list[i]

            if self.__count_list[idx] >= self.__args.learn_start:

                # Anneal importance sampling weight β to 1
                self.__memory_list[idx].priority_weight = min(
                    self.__memory_list[idx].priority_weight + self.__priority_weight_increase, 1)

                if self.__loop_count % self.__args.replay_frequency == 0:
                    start_time = time.time()
                    self.rainbow.learn(self.__memory_list[idx])  # Train with n-step distributional double-Q learning
                    self.__print_progress_log(start_time)
                    self.__save_train_model()
                    self.__train_step += 1

        # Update target network
        if self.__loop_count % self.__args.target_update == 0:
            # LOG.info('master updates target net at train step {}'.format(self.__trainStep))
            self.rainbow.update_target_net()

        if self.__loop_count % LOG_FREQUENCY == 0:
            LOG.info('train time is {} ms at loop count {}'.format(((time.time() - start_time) * 1000),
                                                                   self.__loop_count))

        self.__loop_count += 1

        return

    # pylint: disable=R0201
    def _set_args(self):
        parser = argparse.ArgumentParser(description='Rainbow')
        parser.add_argument('--enable-cuda', action='store_true', help='Enable CUDA')
        parser.add_argument('--enable-cudnn', action='store_true', help='Enable cuDNN')

        parser.add_argument('--T-max', type=int, default=int(50e6), metavar='STEPS',
                            help='Number of training steps (4x number of frames)')

        parser.add_argument('--architecture', type=str, default='canonical', choices=['canonical', 'data-efficient'],
                            metavar='ARCH', help='Network architecture')
        parser.add_argument('--history-length', type=int, default=4, metavar='T',
                            help='Number of consecutive states processed')
        parser.add_argument('--hidden-size', type=int, default=512, metavar='SIZE', help='Network hidden size')
        parser.add_argument('--noisy-std', type=float, default=0.1, metavar='σ',
                            help='Initial standard deviation of noisy linear layers')
        parser.add_argument('--atoms', type=int, default=51, metavar='C', help='Discretised size of value distribution')
        parser.add_argument('--V-min', type=float, default=-10, metavar='V',
                            help='Minimum of value distribution support')
        parser.add_argument('--V-max', type=float, default=10, metavar='V',
                            help='Maximum of value distribution support')

        parser.add_argument('--model', type=str, metavar='PARAMS', help='Pretrained model (state dict)')
        parser.add_argument('--memory-capacity', type=int, default=int(40000), metavar='CAPACITY',
                            help='Experience replay memory capacity')
        parser.add_argument('--replay-frequency', type=int, default=1, metavar='k',
                            help='Frequency of sampling from memory')
        parser.add_argument('--priority-exponent', type=float, default=0.5, metavar='ω',
                            help='Prioritised experience replay exponent (originally denoted α)')
        parser.add_argument('--priority-weight', type=float, default=0.4, metavar='β',
                            help='Initial prioritised experience replay importance sampling weight')
        parser.add_argument('--multi-step', type=int, default=3, metavar='n',
                            help='Number of steps for multi-step return')
        parser.add_argument('--discount', type=float, default=0.99, metavar='γ', help='Discount factor')
        parser.add_argument('--target-update', type=int, default=int(1e3), metavar='τ',
                            help='Number of steps after which to update target network')
        parser.add_argument('--learning-rate', type=float, default=1e-4, metavar='η', help='Learning rate')
        parser.add_argument('--adam-eps', type=float, default=1.5e-4, metavar='ε', help='Adam epsilon')
        parser.add_argument('--batch-size', type=int, default=32, metavar='SIZE', help='Batch size')
        parser.add_argument('--learn-start', type=int, default=int(400), metavar='STEPS',
                            help='Number of steps before starting training')

        # Setup
        args = parser.parse_args()

        # set random seed
        np.random.seed(123)
        torch.manual_seed(np.random.randint(1, 10000))

        args.enable_cuda = True
        args.enable_cudnn = True

        # set torch device
        if torch.cuda.is_available() and args.enable_cuda:
            args.device = torch.device('cuda')
            torch.cuda.manual_seed(np.random.randint(1, 10000))
            torch.backends.cudnn.enabled = args.enable_cudnn
        else:
            args.device = torch.device('cpu')

        return args
