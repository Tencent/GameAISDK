# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging

import tensorflow as tf
import numpy as np

from .ReplayMemory import ReplayMemory

class QNetwork(object):
    """
    Q-Network implement
    """

    def __init__(self, args):
        self.duelingNetwork = args['dueling_network']
        self.stateImgWidth = args['input_img_width']
        self.stateImgHeight = args['input_img_height']
        self.stateRecentFrame = args['state_recent_frame']
        self.termDelayFrame = args['terminal_delay_frame']
        self.actionSpace = args['action_space']
        self.gama = args['reward_discount']
        self.lr = args['learn_rate']
        self.qnetUpdateStep = args['qnet_update_step']
        self.memorySize = args['memory_size']
        self.miniBatchSize = args['mini_batch_size']
        self.trainWithDoubleQ = args['train_with_double_q']
        self.gpuMemoryFraction = args['gpu_memory_fraction']
        self.gpuMemoryGrowth = args['gpu_memory_growth']
        self.checkPointPath = args['checkpoint_path']
        self.showImgState = args['show_img_state']

        self.trainStep = 0
        self.trainStepBase = 0
        self.logger = logging.getLogger('agent')

        # init replay memory
        self.memory = ReplayMemory(maxSize=self.memorySize, \
                            termDelayFrame=self.termDelayFrame, \
                            stateRecentFrame=self.stateRecentFrame, \
                            showState=self.showImgState)

        #init q-network
        self.Create()

        # saving and loading networks
        self.saver = tf.train.Saver()

        #set gpu memory percent
        gpuConfig = tf.ConfigProto()
        gpuConfig.gpu_options.per_process_gpu_memory_fraction = self.gpuMemoryFraction
        gpuConfig.gpu_options.allow_growth = self.gpuMemoryGrowth

        self.session = tf.InteractiveSession(config=gpuConfig)
        #self.merged = tf.summary.merge_all()
        #self.summaryWriter = tf.summary.FileWriter("tf_logs", self.session.graph)

        self.session.run(tf.global_variables_initializer())

        #try to load params from checkpoint
        self.Restore()

    def Create(self):
        """
        Create Q-Network: include current Q network, target Q network,
        sync operation and train optimizer
        """
        # current Q network
        with tf.name_scope('Q_Network'):
            self.stateInput, self.QValue, self.networkParams = self.BuildNet()

        # Target Q Network
        with tf.name_scope('Target_Q_Network'):
            self.stateInputT, self.QValueT, self.networkParamsT = self.BuildNet()

        # sync Q-network params
        self.copyTargetQNet = []
        with tf.name_scope('copy'):
            for i in range(0, len(self.networkParams)):
                paramsT = self.networkParamsT[i]
                params = self.networkParams[i]
                syncOp = paramsT.assign(params)
                self.copyTargetQNet.append(syncOp)

        # cost operation
        with tf.name_scope('cost'):
            self.actionInput = tf.placeholder("float", [None, self.actionSpace])
            self.yInput = tf.placeholder("float", [None])

            qAction = tf.reduce_sum(tf.multiply(self.QValue, self.actionInput), reduction_indices=1)
            self.cost = tf.reduce_mean(tf.square(self.yInput - qAction))

        # trainning optimizer
        with tf.name_scope('train'):
            self.trainOptimizer = tf.train.AdamOptimizer(self.lr).minimize(self.cost)

    def Train(self):
        """
        Train Q-Network use replay memory
        """
        # Step 1: obtain random minibatch from replay memory
        minibatch = self.memory.Random(self.miniBatchSize)
        stateBatch = [data[0] for data in minibatch]
        actionBatch = [data[1] for data in minibatch]
        rewardBatch = [data[2] for data in minibatch]
        nextStateBatch = [data[3] for data in minibatch]
        terminalBatch = [data[4] for data in minibatch]

        # Step 2: calculate y label
        yBatch = []

        if self.trainWithDoubleQ:
            qValueBatch = self.QValue.eval(feed_dict={self.stateInput : nextStateBatch})
            actionIndexBatch = [np.argmax(qv) for qv in qValueBatch]
            qValueTBatch = self.QValueT.eval(feed_dict={self.stateInputT : nextStateBatch})

            for i in range(0, self.miniBatchSize):
                terminal = terminalBatch[i]
                if terminal:
                    yBatch.append(rewardBatch[i])
                else:
                    actionIndex = actionIndexBatch[i]
                    yBatch.append(rewardBatch[i] + self.gama * qValueTBatch[i][actionIndex])
        else:
            qValueBatch = self.QValueT.eval(feed_dict={self.stateInputT : nextStateBatch})
            for i in range(0, self.miniBatchSize):
                terminal = terminalBatch[i]
                if terminal:
                    yBatch.append(rewardBatch[i])
                else:
                    yBatch.append(rewardBatch[i] + self.gama * np.max(qValueBatch[i]))

        # Step 3: optimize network params
        self.trainOptimizer.run(feed_dict={self.yInput : yBatch,
                                           self.actionInput : actionBatch,
                                           self.stateInput : stateBatch})

        # save network every 10000 iteration
        if self.trainStep % 10000 == 0 and self.trainStep != 0:
            self.Save()

        # sync network params, from current network to target network
        if self.trainStep % self.qnetUpdateStep == 0:
            self.session.run(self.copyTargetQNet)

        self.trainStep += 1

    def EvalQValue(self, state):
        """
        Interface of evaluate Q-Network Q value when predict action
        """
        qValue = self.QValue.eval(feed_dict={self.stateInput : [state]})[0]
        return qValue

    def StoreTransition(self, action, reward, nextState, terminal):
        """
        Save replay (s, a, r, t) to replay memory
        """
        self.memory.Add(action, reward, nextState, terminal)

    def Save(self):
        """
        Save network-model and params
        """
        globalStepSaved = self.trainStep + self.trainStepBase
        self.saver.save(self.session, self.checkPointPath + 'network-dqn',
                        global_step=globalStepSaved)

    def Restore(self):
        """
        Restore network-model and params
        """
        checkpoint = tf.train.get_checkpoint_state(self.checkPointPath)
        if checkpoint and checkpoint.model_checkpoint_path:
            base = len(self.checkPointPath + 'network-dqn-')
            self.trainStepBase = int(checkpoint.model_checkpoint_path[base:])
            self.saver.restore(self.session, checkpoint.model_checkpoint_path)
            self.logger.info('Loaded network weights: {}'.format(checkpoint.model_checkpoint_path))
        else:
            self.logger.warning('Could not find old network weights')

    def VariableSummaries(self, var):
        """
        Attach a lot of summaries to a Tensor (for TensorBoard visualization)
        """
        with tf.name_scope('summaries'):
            mean = tf.reduce_mean(var)
            tf.summary.scalar('mean', mean)
            with tf.name_scope('stddev'):
                stddev = tf.sqrt(tf.reduce_mean(tf.square(var - mean)))
            tf.summary.scalar('stddev', stddev)
            tf.summary.scalar('max', tf.reduce_max(var))
            tf.summary.scalar('min', tf.reduce_min(var))
            tf.summary.histogram('histogram', var)

    def WeightVariable(self, shape):
        """
        Initialize Q network weight params
        """
        with tf.name_scope('weights'):
            initial = tf.truncated_normal(shape, stddev=0.01)
            variable = tf.Variable(initial)
            self.VariableSummaries(variable)
        return variable

    def BiasVariable(self, shape):
        """
        Initialize Q network bias params
        """
        with tf.name_scope('biases'):
            initial = tf.constant(0.01, shape=shape)
            variable = tf.Variable(initial)
            self.VariableSummaries(variable)
        return variable

    def Conv2d(self, x, W, stride, paddingStyle="SAME"):
        """
        Conv operation used by Q network
        """
        return tf.nn.conv2d(x, W, strides=[1, stride, stride, 1], padding=paddingStyle)

    def MaxPool2x2(self, x, paddingStyle="SAME"):
        """
        Pooling operation used by Q network
        """
        return tf.nn.max_pool(x, ksize=[1, 2, 2, 1], strides=[1, 2, 2, 1], padding=paddingStyle)

    def BuildNet(self):
        """
        Build Q network use conv layer and fc layer
        """
        with tf.name_scope('input_layer'):
            stateInput = tf.placeholder("float", [None,
                                                  self.stateImgHeight,
                                                  self.stateImgWidth,
                                                  self.stateRecentFrame])

        with tf.name_scope('conv_layer1'):
            W_conv1 = self.WeightVariable([8, 8, 4, 32])
            b_conv1 = self.BiasVariable([32])
            h_conv1 = tf.nn.relu(self.Conv2d(stateInput, W_conv1, 4) + b_conv1)

        with tf.name_scope('pool_layer1'):
            h_pool1 = self.MaxPool2x2(h_conv1)

        with tf.name_scope('conv_layer2'):
            W_conv2 = self.WeightVariable([4, 4, 32, 64])
            b_conv2 = self.BiasVariable([64])
            h_conv2 = tf.nn.relu(self.Conv2d(h_pool1, W_conv2, 2) + b_conv2)

        with tf.name_scope('conv_layer3'):
            W_conv3 = self.WeightVariable([3, 3, 64, 128])
            b_conv3 = self.BiasVariable([128])
            h_conv3 = tf.nn.relu(self.Conv2d(h_conv2, W_conv3, 1) + b_conv3)
            h_conv3_flat = tf.reshape(h_conv3, [-1, 9856])

        with tf.name_scope('fc_layer1'):
            W_fc1 = self.WeightVariable([9856, 768])
            b_fc1 = self.BiasVariable([768])
            h_fc1 = tf.nn.relu(tf.matmul(h_conv3_flat, W_fc1) + b_fc1)

        if self.duelingNetwork is True:
            with tf.name_scope('value_layer'):
                W_fc2_V = self.WeightVariable([768, 1])
                b_fc2_V = self.BiasVariable([1])
                value = tf.matmul(h_fc1, W_fc2_V) + b_fc2_V

            with tf.name_scope('advantage_layer'):
                W_fc2_A = self.WeightVariable([768, self.actionSpace])
                b_fc2_A = self.BiasVariable([self.actionSpace])
                advantage = tf.matmul(h_fc1, W_fc2_A) + b_fc2_A

            with tf.name_scope('q_value_layer'):
                QValue = value + (advantage - tf.reduce_mean(advantage, axis=1, keep_dims=True))

            networkParams = [W_conv1, b_conv1, W_conv2, b_conv2, W_conv3, b_conv3,
                             W_fc1, b_fc1, W_fc2_V, b_fc2_V, W_fc2_A, b_fc2_A]
        else:
            with tf.name_scope('q_value_layer'):
                W_fc2 = self.WeightVariable([768, self.actionSpace])
                b_fc2 = self.BiasVariable([self.actionSpace])
                QValue = tf.matmul(h_fc1, W_fc2) + b_fc2

            networkParams = [W_conv1, b_conv1, W_conv2, b_conv2, W_conv3, b_conv3, W_fc1, b_fc1, W_fc2, b_fc2]

        return stateInput, QValue, networkParams
