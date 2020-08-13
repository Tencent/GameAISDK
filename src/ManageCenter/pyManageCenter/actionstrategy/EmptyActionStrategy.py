# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging

from .AbstractActionStrategy import AbstractActionStrategy

LOG = logging.getLogger('ManageCenter')


class EmptyActionStrategy(AbstractActionStrategy):
    """
    Empty Action Strategy implement class
    """
    def __init__(self):
        pass

    def Initialize(self):
        """
        Initialize, do nothing
        """
        return True

    def Finish(self):
        """
        Finish, do nothing
        """
        return True

    def Reset(self):
        """
        Reset, do nothing
        """
        pass

    def Perform(self, action):
        """
        Perform strategy, do nothing, just return the input
        """
        return action
