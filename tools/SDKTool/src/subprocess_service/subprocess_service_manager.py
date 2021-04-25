# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import signal
import subprocess
import time
import logging

import psutil

from .subprocess_utils import get_sys_platform
from .threading_lock import thread_lock
from .process_timer import ProcessTimer

logger = logging.getLogger("sdktool")


def generate_subproces_params(param_type):
    SUBPROCESS_DEFAULT_PARAMS_TYPE = 1
    SUBPROCESS_SHELL_TYPE = 2
    SUBPROCESS_STDIN_TYPE = 3
    SUBPROCESS_STDOUT_TYPE = 4

    if get_sys_platform() == 'win32':
        if param_type == SUBPROCESS_DEFAULT_PARAMS_TYPE:
            params = {}
        elif param_type == SUBPROCESS_SHELL_TYPE:
            params = {
                'shell': True}
        elif param_type == SUBPROCESS_STDIN_TYPE:
            params = {
                'shell': True,
                'stdin': subprocess.PIPE,
            }
        elif param_type == SUBPROCESS_STDOUT_TYPE:
            params = {
                'shell': True,
                'stdout': subprocess.PIPE,
                'stderr': subprocess.STDOUT,
            }
        else:
            raise ValueError('subprocess param type error:{}'.format(param_type))
        if hasattr(os.sys, 'winver'):
            params['creationflags'] = subprocess.CREATE_NEW_CONSOLE
    else:
        if param_type == SUBPROCESS_DEFAULT_PARAMS_TYPE:
            params = {}
        elif param_type == SUBPROCESS_SHELL_TYPE:
            params = {
                'shell': True,
                'preexec_fn': os.setsid
            }
        elif param_type == SUBPROCESS_STDIN_TYPE:
            params = {
                'shell': True,
                'stdin': subprocess.PIPE,
                'preexec_fn': os.setsid
            }
        elif param_type == SUBPROCESS_STDOUT_TYPE:
            params = {
                'shell': True,
                'stdout': subprocess.PIPE,
                'stdin': subprocess.PIPE,
                'preexec_fn': os.setsid,
            }
        else:
            raise ValueError('subprocess param type error:{}'.format(param_type))
        os.system('ipcs | awk \'{if($6==0) printf "ipcrm shm %d\n",$2}\'| sh')
    return params


class SubprocessManager(object):
    SUBPROCESS_DEFAULT_PARAMS_TYPE = 1
    SUBPROCESS_SHELL_TYPE = 2
    SUBPROCESS_STDIN_TYPE = 3
    SUBPROCESS_STDOUT_TYPE = 4

    def __init__(self):
        self.process = None
        self.run_program = None

    def __getattr__(self, name):
        if name == "__members__":
            return dir(self.process)
        return getattr(self.process, name)

    def start_subprocess(self, run_program, params_type=1):
        """Start subprocess for aisdk service, including [manage_center, agentai, GameReg, UIRecognize, io_service]

        Start subprocess for aisdk service

        :param run_program: program name, for example:
            'python agentai.py mode SDKTool cfgpath /workspace/project'
        :param params_type: subprocess args type, optional args:
            params_type=1, use default params for subprocess
            params_type=2, shell=true for subprocess
            params_type=3, shell=true, stdin=subprocess.PIPE for subprocess
            params_type=4, shell=true, stdin=subprocess.PIPE, stderr=subprocess.STDOUT for subprocess

        :return: process, subprocess obj
        """

        kwargs = generate_subproces_params(params_type)
        self.run_program = run_program
        self.process = subprocess.Popen(run_program, **kwargs)
        return None if self.process is None else self

    def exist_process(self):
        try:
            p_children = psutil.Process(self.process.pid).children()
            if len(p_children) > 0:
                return True
        except (RuntimeError, psutil.NoSuchProcess) as err:
            logger.error("exist process exception: %s", err)
            return False

    def kill(self):
        return self.stop_subprocess()

    @staticmethod
    def _recursive_kill(pro):
        logger.info("begin to recursive kill %s child process", pro.pid)
        p = psutil.Process(pro.pid)
        p_childs = p.children(recursive=True)
        for p_child in p_childs:
            logger.debug("kill child pro: %s", p_child.pid)
            p_child.terminate()

        pro.wait()
        pro.terminate()
        return True

    def _kill_process(self, pro):
        try:
            if not psutil.pid_exists(pro.pid):
                return True
            if get_sys_platform() == 'win32':
                return self._recursive_kill(pro)

            os.killpg(pro.pid, signal.SIGUSR1)
            pro.wait()
        except RuntimeError as err:
            logger.error("kill pro %s except, %s", pro.pid, err)
            return False
        else:
            logger.info("killed pro %s success", pro.pid)
        return True

    def stop_subprocess(self):
        """Popen start process"""
        logger.info("call stop_subprocess begin to quit subprocess pro %s", self.process.pid)
        if not self.process:
            return True
        return self._kill_process(self.process)


class ServiceManager(object):
    SUBPROCESS_DEFAULT_PARAMS_TYPE = 1
    SUBPROCESS_SHELL_TYPE = 2
    SUBPROCESS_STDIN_TYPE = 3
    SUBPROCESS_STDOUT_TYPE = 4

    MAX_PROCESS_EXIT_TIME = 10

    def __init__(self):
        self.service_info_dict = {}
        self.service_monitor = {}
        self.service_extend_info = {}

    @staticmethod
    def _stop_started_process(programs_info):
        error_process = []
        for _, program in enumerate(programs_info):
            pro = program.get('process')
            if pro is None:
                continue
            if not pro.stop_subprocess():
                logger.error('stop process %s failed', program.get('run_program'))
                error_process.append({'run_program': program.get('run_program'),
                                      'process': program})
                continue
            logger.error('stop process %s success', program.get('run_program'))
        return error_process

    def _start_process(self, service_name, run_programs, process_type=1):
        process_info = self.service_info_dict.get(service_name, [])
        try:
            for _, run_program in enumerate(run_programs):

                with thread_lock:
                    pro = SubprocessManager()
                    pro.start_subprocess(run_program=run_program, params_type=process_type)
                    process_info.append({'run_program': run_program, 'process': pro})
        except RuntimeError as err:
            error_process = self._stop_started_process(process_info)
            logger.error('some process encounter exception when stopping, %s, %s', err, error_process)
            return False, 'some process encounter exception when stopping, {}, {}'.format(err, error_process)
        # wait start completely
        time.sleep(2)
        for process_obj in process_info:
            pro_name = process_obj.get('run_program')
            pro = process_obj.get('process')
            if not pro.exist_process():
                error_process = self._stop_started_process(process_info)
                msg = 'process {} start failed, service_name: {} error: {}'.format(pro_name, service_name,
                                                                                   error_process)
                logger.error(msg)
                return False, msg
        with thread_lock:
            self.service_info_dict[service_name] = process_info
        logger.info('start service %s success %s', service_name, run_programs)
        return True, ''

    @staticmethod
    def _has_exist(single_service_list, run_programs):
        for process_info in single_service_list:
            process_name = process_info.get("run_program")
            if process_name in run_programs:
                return True
        return False

    def _start_monitor(self, service_name, service_info_dict, callback_func):
        pt = ProcessTimer(service_name, service_info_dict, callback_func)
        pt.daemon = True
        pt.start()
        self.service_monitor[service_name] = pt

    def _stop_monitor(self, service_name):
        if self.service_monitor.__contains__(service_name):
            with thread_lock:
                self.service_monitor[service_name].exit_thread()

    def start_service(self, service_name, run_programs, process_param_type=1, callback_func=None, start_internal=5):
        # step1： check run_programs
        if len(self.service_info_dict) > 1:
            err_msg = 'multi-services {} has exist, please stop them first'.format(self.service_info_dict.keys())
            logger.error(err_msg)
            return False, err_msg

        if len(self.service_info_dict) == 1 and service_name not in self.service_info_dict:
            err_msg = 'service %s has exist, please stop first', self.service_info_dict.keys()
            logger.error(err_msg)
            return False, err_msg

        # step2： check run_programs
        if isinstance(run_programs, str):
            run_programs = [run_programs]

        # step3: check exist service
        single_service_list = self.service_info_dict.get(service_name, [])
        if self._has_exist(single_service_list, run_programs):
            logger.error('service %s has exist, please stop first, has started program: %s, '
                         'want to start program: %s', service_name, single_service_list, run_programs)
            return False, 'service {} has exist, please stop, then restart'.format(service_name)

        # step4: stop monitor
        self._stop_monitor(service_name)

        # step5: start process
        is_ok, desc = self._start_process(service_name, run_programs, process_param_type)
        if is_ok:
            self._start_monitor(service_name, self.service_info_dict, callback_func)
        self.service_extend_info[service_name] = {
            'created_time': time.time(),
            "start_internal": start_internal}
        return is_ok, desc

    def stop_service(self, service_name):
        if service_name not in self.service_extend_info:
            return True, 'service {} has not started, do not stop'.format(service_name)

        cur_internal = self.service_extend_info[service_name].get('start_internal') - \
                       (time.time() - self.service_extend_info[service_name].get('created_time'))
        if cur_internal > 0:
            logger.error('stop internal is too short, please wait %s (s) to stop', cur_internal)
            return False, 'please wait {} (s) to stop'.format(cur_internal)

        if not self.service_info_dict.__contains__(service_name):
            logger.error('service %s has not started, do not stop', service_name)
            return True, 'service {} has not started, do not stop'.format(service_name)

        if not self.service_monitor.__contains__(service_name):
            logger.error('service_name:%s monitor process not exist', service_name)
            return False, 'service_name:{} monitor process not exist'
        self.service_monitor[service_name].stop()
        logger.info('service %s has been terminated successfully', service_name)
        return True, ''

    def get_processes(self, service_name):
        if not self.service_info_dict.__contains__(service_name):
            return None
        process_list = []
        process_info_list = self.service_info_dict[service_name]
        for program in process_info_list:
            pro = program.get('process')
            if pro is None:
                continue
            process_list.append(pro)

        if len(process_list) == 1:
            return process_list[0]
        return process_list

    def get_pids(self, service_name):
        if not self.service_info_dict.__contains__(service_name):
            return None
        pids = []
        process_info = self.service_info_dict[service_name]
        for program in process_info:
            pro = program.get('process')
            if pro is None:
                continue
            pids.append(pro.pid)

        if len(pids) == 1:
            return pids[0]
        return pids

    def exist_process(self, service_name):
        if not self.service_info_dict.__contains__(service_name):
            return False
        process_info = self.service_info_dict[service_name]
        for program in process_info:
            pro = program.get('process')
            if not pro.exist_process():
                return False
        return True

    def exist_service(self, service_name):
        return self.service_info_dict.__contains__(service_name)

    def exit_all_service(self):
        """Exit all service when get signal

        For signal to exit all service
        """
        for service_name, _ in self.service_info_dict.items():
            ret, desc = self.stop_service(service_name)
            logger.info("exit_all_service, service_name %s result:%s, desc: %s", service_name, ret, desc)
        begin_time = time.time()
        while time.time() - begin_time < self.MAX_PROCESS_EXIT_TIME:
            if len(self.service_info_dict) == 0:
                logger.info("exit all service success")
                return
            time.sleep(0.2)
        logger.error("exit all service timeout")

    def has_service_running(self):
        """ 返回是否有服务在运行

        :return:
        """
        return len(self.service_info_dict) > 0


backend_service_manager = ServiceManager()
