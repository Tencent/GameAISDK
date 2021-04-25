# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import threading
import time
from .threading_lock import thread_lock


class ProcessTimer(threading.Thread):
    MAX_TRY_STOP_TIME = 3
    MONITOR_INTERNAL_TIME = 5
    STOP_PROCESS_INTERNAL_TIME = 2

    SERVICE_STATE_EXCEPTION = 0
    SERVICE_STATE_RUNING = 1
    SERVICE_STATE_OVER = 2

    def __init__(self, service_name, backend_service_dict, callback_func):
        threading.Thread.__init__(self)
        self.service_name = service_name
        self.backend_service_dict = backend_service_dict
        self.callback_func = callback_func
        self._is_over = False
        self._need_stop = False
        self._try_stop_time = 0

        self.__running = threading.Event()   # stop thread flag
        self.__running.set()

    def stop(self):
        msg = 'user want to stop service {}, begin to stop backend service'.format(self.service_name)
        self.callback_func(self.SERVICE_STATE_OVER, msg)
        self._need_stop = True

    @staticmethod
    def _stop_all_pro(service_list):
        for idx in range(len(service_list) - 1, -1, -1):
            pro_obj = service_list[idx]
            pro = pro_obj.get('process')
            if pro.stop_subprocess():
                with thread_lock:
                    del service_list[idx]
        ret = True if len(service_list) == 0 else False
        return ret

    def run(self):
        sleep_time = self.MONITOR_INTERNAL_TIME
        try:
            flag = True
            while flag and self.__running.is_set():
                # monitor process status
                service_list = self.backend_service_dict.get(self.service_name)
                if service_list is None:
                    msg = 'service {} backend process start exception, will exit'.format(self.service_name)
                    self.callback_func(self.SERVICE_STATE_EXCEPTION, msg)
                    break
                for process_obj in service_list:
                    pro_name = process_obj.get('run_program')
                    pro = process_obj.get('process')
                    if not pro.exist_process():
                        msg = 'process {} has exited in service {}, will stop all process and ' \
                              'exit monitor'.format(pro_name, self.service_name)
                        self.callback_func(self.SERVICE_STATE_EXCEPTION, msg)
                        self._need_stop = True
                        break

                # try stop backend process
                if self._need_stop:
                    is_success = self._stop_all_pro(self.backend_service_dict.get(self.service_name))
                    if is_success and self.backend_service_dict.__contains__(self.service_name):
                        with thread_lock:
                            self.backend_service_dict.pop(self.service_name)

                    self._is_over = is_success
                    self._try_stop_time += 1
                    sleep_time = self.STOP_PROCESS_INTERNAL_TIME
                else:
                    msg = 'all process in service {} is running'.format(self.service_name)
                    self.callback_func(self.SERVICE_STATE_RUNING, msg)

                # exit monitor thread
                if self._is_over or self._try_stop_time > self.MAX_TRY_STOP_TIME:
                    if self._try_stop_time > self.MAX_TRY_STOP_TIME:
                        print('service_list', service_list, 'try_time', self._try_stop_time)
                        msg = 'service {} stop failed, some backend process ' \
                              'not exit'.format(self.service_name)
                        self.callback_func(self.SERVICE_STATE_EXCEPTION, msg)
                    else:
                        msg = 'service {} has success stopped, will exit backend monitor'.format(self.service_name)
                        self.callback_func(self.SERVICE_STATE_OVER, msg)

                    if self.backend_service_dict.__contains__(self.service_name):
                        with thread_lock:
                            self.backend_service_dict.pop(self.service_name)
                    break
                time.sleep(sleep_time)
        except RuntimeError as err:
            msg = 'process monitor except exit, please restart service {}, err: {}'.format(self.service_name, err)
            self.callback_func(self.SERVICE_STATE_EXCEPTION, msg)

    def exit_thread(self):
        self.__running.clear()
