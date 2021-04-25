# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

from __future__ import division
from torch import nn
from torch.nn import functional as f

import math
import torch


# Factorised NoisyLinear layer with bias
def _scale_noise(size):
    x = torch.randn(size)
    return x.sign().mul_(x.abs().sqrt_())


class NoisyLinear(nn.Module):
    def __init__(self, in_features, out_features, std_init=0.5):
        super(NoisyLinear, self).__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.std_init = std_init

        self.weight_mu = nn.Parameter(torch.empty(out_features, in_features))
        self.weight_sigma = nn.Parameter(torch.empty(out_features, in_features))
        self.register_buffer('weight_epsilon', torch.empty(out_features, in_features))
        self.bias_mu = nn.Parameter(torch.empty(out_features))
        self.bias_sigma = nn.Parameter(torch.empty(out_features))
        self.register_buffer('bias_epsilon', torch.empty(out_features))
        self.reset_parameters()
        self.reset_noise()

    def reset_parameters(self):
        mu_range = 1 / math.sqrt(self.in_features)
        self.weight_mu.data.uniform_(-mu_range, mu_range)
        self.weight_sigma.data.fill_(self.std_init / math.sqrt(self.in_features))
        self.bias_mu.data.uniform_(-mu_range, mu_range)
        self.bias_sigma.data.fill_(self.std_init / math.sqrt(self.out_features))

    def reset_noise(self):
        epsilon_in = _scale_noise(self.in_features)
        epsilon_out = _scale_noise(self.out_features)
        self.weight_epsilon.copy_(epsilon_out.ger(epsilon_in))
        self.bias_epsilon.copy_(epsilon_out)

    # 线性变换
    def forward(self, input_image):
        if self.training:
            return f.linear(input_image, self.weight_mu + self.weight_sigma * self.weight_epsilon,
                            self.bias_mu + self.bias_sigma * self.bias_epsilon)

        return f.linear(input_image, self.weight_mu, self.bias_mu)


class DQN(nn.Module):
    def __init__(self, args, action_space):
        super(DQN, self).__init__()
        self.atoms = args.atoms
        self.action_space = action_space

        if args.architecture == 'canonical':
            self.convs = nn.Sequential(nn.Conv2d(args.history_length, 32, 8, stride=4, padding=0), nn.ReLU(),
                                       nn.Conv2d(32, 64, 4, stride=2, padding=0), nn.ReLU(),
                                       nn.Conv2d(64, 64, 3, stride=1, padding=0), nn.ReLU())
            self.conv_output_size = 3136
        elif args.architecture == 'data-efficient':
            self.convs = nn.Sequential(nn.Conv2d(args.history_length, 32, 5, stride=5, padding=0), nn.ReLU(),
                                       nn.Conv2d(32, 64, 5, stride=5, padding=0), nn.ReLU())
            self.conv_output_size = 576

        self.fc_h_v = NoisyLinear(self.conv_output_size, args.hidden_size, std_init=args.noisy_std)
        self.fc_h_a = NoisyLinear(self.conv_output_size, args.hidden_size, std_init=args.noisy_std)
        self.fc_z_v = NoisyLinear(args.hidden_size, self.atoms, std_init=args.noisy_std)
        self.fc_z_a = NoisyLinear(args.hidden_size, action_space * self.atoms, std_init=args.noisy_std)

    def forward(self, x, log=False):
        x = self.convs(x)
        x = x.view(-1, self.conv_output_size)
        v = self.fc_z_v(f.relu(self.fc_h_v(x)))  # Value stream
        a = self.fc_z_a(f.relu(self.fc_h_a(x)))  # Advantage stream
        v, a = v.view(-1, 1, self.atoms), a.view(-1, self.action_space, self.atoms)
        q = v + a - a.mean(1, keepdim=True)  # Combine streams

        if log:  # Use log softmax for numerical stability
            q = f.log_softmax(q, dim=2)  # Log probabilities with action over second dimension
        else:
            q = f.softmax(q, dim=2)  # Probabilities with action over second dimension

        return q

    def reset_noise(self):
        for name, module in self.named_children():
            if 'fc' in name:
                module.reset_noise()
