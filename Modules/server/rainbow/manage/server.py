# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import select
import socket
import struct
import sys
import threading
import time
import os
import numpy as np
import configparser
from manage.master import Master
from manage.worker import Worker
from log.log import LOG

sys.path.append('manage')
MAGIC_NUMBER = 967345
MAX_WORKER_COUNT = 6
SERVER_ADDRESS = ('0.0.0.0', 8888)
ACTION_SPACE = 3
IMAGE_WIDTH = 84
IMAGE_HEIGHT = 84

SERVER_CONFIG_FILE = 'cfg/server.ini'


class Server:
    def __init__(self):
        self.__server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__epoll = select.epoll()
        self.__fd_to_socket = {}
        self.__fd_to_worker_index = {}
        self.__worker_index_to_fd = []
        self.__worker_threads = []

        self.__master = None
        self.__workers = []

        # 默认值
        self.server_ip = '0.0.0.0'
        self.server_port = 8888

        self.__train_fps = 20
        self.__train_time = 1.0 / self.__train_fps
        self.__last_time = None

    def init(self):
        self._load_server_config()
        self._init_server()
        self._init_master()
        self._init_worker()
        return True

    def run(self):
        self._start_worker()

        self.__last_time = time.time()
        while True:
            self._poll_data()

            # control train frequency per second
            now_time = time.time()
            if now_time - self.__last_time > self.__train_time:
                self.__master.train()
                self.__last_time = now_time

            time.sleep(0.002)

    def finish(self):
        self._stop_worker()
        self._finish_server()
        return True

    def _init_server(self):
        """
        Create tcp server, epoll, and listen port
        """
        self.__server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        config_address = (self.server_ip, self.server_port)
        self.__server_socket.bind(config_address)

        self.__server_socket.listen(MAX_WORKER_COUNT)
        self.__server_socket.setblocking(False)
        self.__epoll.register(self.__server_socket.fileno(), select.EPOLLIN)

        LOG.info('init server successful')
        return True

    def _finish_server(self):
        """
        Release tcp server and epoll
        """
        self.__epoll.unregister(self.__server_socket.fileno())
        self.__epoll.close()
        self.__server_socket.close()

        LOG.info('finish server successful')
        return

    def _init_master(self):
        self.__master = Master()

        LOG.info('init master successful')
        return

    def _init_worker(self):
        for worker_index in range(MAX_WORKER_COUNT):
            worker = Worker(worker_index, self.__master)
            self.__workers.append(worker)
            self.__worker_index_to_fd.append(-1)

        LOG.info('init {} workers successful'.format(MAX_WORKER_COUNT))
        return

    def _start_worker(self):

        for worker in self.__workers:
            thread = threading.Thread(target=lambda: worker.work())
            thread.start()
            self.__worker_threads.append(thread)

        LOG.info('start {} workers successful'.format(MAX_WORKER_COUNT))
        return

    def _stop_worker(self):
        for thread in self.__worker_threads:
            thread.join()

        LOG.info('stop {} workers successful'.format(MAX_WORKER_COUNT))
        return

    def _poll_data(self):
        events = self.__epoll.poll()
        for fd, event in events:
            if fd == self.__server_socket.fileno():
                self._accept_client()

            elif event & select.EPOLLHUP:
                self._close_client(fd)

            elif event & select.EPOLLIN:
                frame_info = self._receive_frame_info(fd)
                if frame_info is not None:
                    index = self.__fd_to_worker_index[fd]
                    worker = self.__workers[index]
                    worker.set_frame_info(frame_info)

                else:
                    self._close_client(fd)

            elif event & select.EPOLLOUT:
                index = self.__fd_to_worker_index[fd]
                worker = self.__workers[index]
                action_info = worker.get_action_info()
                if action_info is not None:
                    self._send_action_info(fd, action_info)

    def _accept_client(self):
        client_socket, _ = self.__server_socket.accept()
        client_socket.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)

        fd = client_socket.fileno()
        self.__epoll.register(fd, select.EPOLLIN | select.EPOLLOUT)
        self.__fd_to_socket[fd] = client_socket

        for index in range(len(self.__workers)):
            if self.__worker_index_to_fd[index] == -1:
                self.__worker_index_to_fd[index] = fd
                self.__fd_to_worker_index[fd] = index

                LOG.info('assign fd {} to worker {}'.format(fd, index))
                break

        LOG.info('accept client {} successful'.format(fd))
        return

    # 关闭客户端
    def _close_client(self, fd):
        self.__epoll.unregister(fd)
        self.__fd_to_socket[fd].close()
        del self.__fd_to_socket[fd]

        index = self.__fd_to_worker_index[fd]
        self.__worker_index_to_fd[index] = -1
        del self.__fd_to_worker_index[fd]

        LOG.info('close client {} successful'.format(fd))
        return

    # 介绍数据帧
    def _receive_frame_info(self, fd):
        client_socket = self.__fd_to_socket[fd]

        header = client_socket.recv(4, socket.MSG_WAITALL)
        LOG.info("the length of header is {}, header:{}", len(header), header)

        if len(header) != 4:
            LOG.error('header length is not 4')
            return None

        data_length = struct.unpack('i', header)[0]
        data_bin = client_socket.recv(data_length, socket.MSG_WAITALL)
        if len(data_bin) != data_length:
            LOG.error('the length of dataBin is not equal to data length')
            return None

        # 前面16个字节是魔数、补偿信息、是否终止、帧序号，后面是帧数据
        magic_number, reward, terminal, frame_index = struct.unpack('ifii', data_bin[0:16])
        if magic_number != MAGIC_NUMBER:
            LOG.error('magic number error')
            return None

        np_array = np.fromstring(data_bin[16:], np.uint8)
        image = np.reshape(np_array, (IMAGE_WIDTH, IMAGE_HEIGHT))
        done = bool(terminal == 1)
        LOG.debug('receive frame information from fd {}: frame index = {}, reward = {}'.format(client_socket.fileno(),
                                                                                               frame_index, reward))
        return image, reward, done, frame_index

    # 发送操作信息
    def _send_action_info(self, fd, action_info):
        client_socket = self.__fd_to_socket[fd]

        action_index = action_info[0]
        frame_index = action_info[1]
        data_bin = struct.pack("iii", MAGIC_NUMBER, action_index, frame_index)
        client_socket.sendall(data_bin)
        LOG.debug('send action information to fd {}, action index = {}'.format(fd, action_index))
        return

    #  加载服务器的配置, 方便服务器
    def _load_server_config(self):
        current_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        config_path = os.path.join(current_path, SERVER_CONFIG_FILE)
        LOG.info("the config path of server is {}, current_path:{}".format(config_path, current_path))

        if os.path.exists(config_path):
            server_config = configparser.ConfigParser()
            server_config.read(config_path)
        else:
            LOG.error('Config File not exist in {0}'.format(config_path))
            return False

        # 从配置文件中读取IP和端口
        self.server_ip = server_config.get('SERVER', 'IP', fallback='0.0.0.0')
        self.server_port = server_config.getint('SERVER', 'Port', fallback=8888)
        LOG.info("the server info as list, ip:{}, port:{}".format(self.server_ip, self.server_port))
        return True
