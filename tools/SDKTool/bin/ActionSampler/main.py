# -*- coding: utf-8 -*-
"""
This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.
Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import logging
import logging.config
import signal
import sys

sys.path.insert(0, 'pymodules')
from actionsampler.ActionSampler import ActionSampler

CFG_FILE = 'cfg/cfg.json'
LOG_CFG_FILE = 'cfg/log.ini'
logging.config.fileConfig(LOG_CFG_FILE)

LOG = logging.getLogger('ActionSampler')


def main():
    sampler = ActionSampler()

    def SigHandle(sigNum, _):
        LOG.info('signal {0} recved, sampler is going to shut...'.format(sigNum))
        sampler.SetExited()

    signal.signal(signal.SIGINT, SigHandle)

    LOG.info('==== ActionSampler is initializing ====')
    if sampler.Init():
        LOG.info('==== ActionSampler is going to run ====')
        sampler.Run()
        sampler.Finish()
        LOG.info('Finished!')
    else:
        LOG.error('==== ActionSampler init failed! ====')


if __name__ == '__main__':
    main()
