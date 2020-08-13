import sys
import time
import socket
import queue
import logging
import struct
import threading
from queue import Queue

from .pb.touch.TouchPkgPB_pb2 import *
from .pb.cloudscreen.CloudscreenPkgPB_pb2 import *

logger = logging.getLogger(__name__)

MSG_CLOSE_SOCKET = -1

RET_OK = 0
RET_ERR = -1
RET_ERR_SOCKET_EXCEPTION = -2

class TcpSocketHandler(threading.Thread):
    def __init__(self, ip, port, command_filter=None, is_screenmode=False):
        super().__init__()
        self.setDaemon(True)

        self.ip = ip
        self.port = port
        self.sock = None
        self.flag_cancel = False
        self.queue = Queue()
        self.is_screenmode = is_screenmode
        if is_screenmode:
            self.mutex = threading.Lock()
            self.last_packet = None
        else:
            self.res_queue = Queue()
        self.command_filter = command_filter
        self.event = threading.Event()
        self.heartEvent = threading.Event()
        self.reader = TcpSocketHandler.Reader(self)
        self.beater = TcpSocketHandler.HeartBeat(self)
        self.error = RET_OK

    def __read_bytes(self, readlen):
        recv_len = 0
        _buffer = bytearray(readlen)
        buffer = memoryview(_buffer)
        while recv_len < readlen:
            ret = self.sock.recv_into(buffer[recv_len:], readlen - recv_len)
            if ret < 0:
                raise Exception("read error: readlen={}, get={}".format(readlen, recv_len))

            recv_len += ret
        return buffer

    def read_packet(self):
        raise NotImplementedError

    def read_packet_bytes(self):
        if self.sock is None:
            raise Exception("sock is none")

        packet_len_bytes = self.__read_bytes(4)
        packet_len, = struct.unpack(">I", packet_len_bytes)
        packet_bytes = self.__read_bytes(packet_len)
        if len(packet_bytes) != packet_len:
            raise Exception("read error: readlen={}, get={}".format(len(packet_bytes), packet_len))
        return packet_bytes

    def write_packet(self, cspkg):
        if self.sock is None:
            raise Exception("sock is none")

        packet_bytes = cspkg.SerializeToString()
        packet_len = len(packet_bytes)
        packet_len_bytes = struct.pack(">I", packet_len)
        buf = bytearray(packet_len_bytes)
        buf += bytearray(packet_bytes)
        sent_len = self.sock.send(buf)
        if sent_len != (packet_len + 4):
            raise Exception("send packet error")

    def __close_socket(self):
        if self.sock:
            try:
                self.sock.close()
            except:
                logger.error('close socket exception')

    def is_heart_beat(self, pkg):
        return False

    def set_error(self):
        with self.mutex:
            self.error = RET_ERR_SOCKET_EXCEPTION

    def get_error(self):
        with self.mutex:
            return self.error

    def heart_beat(self):
        return None

    def close(self):
        logger.info("close socket, clear event")
        try:
            self.__close_socket()
            self.error = RET_ERR_SOCKET_EXCEPTION
            self.event.clear()
            with self.mutex:
                self.last_packet = None
        except:
            pass

    def quit(self):
        logger.info("quit reader thread...")
        self.flag_cancel = True
        self.event.set()
        self.reader.join(1)
        logger.info("quit reader thread...done")

        if self.beater and self.beater.is_alive():
            self.heartEvent.set()
            self.beater.join(1)
            logger.info("quit beater thread...done")

        logger.info("quit writer thread...")
        self.queue.put(MSG_CLOSE_SOCKET)
        self.join(1)
        logger.info("quit writer thread...done")

    class Reader(threading.Thread):
        def __init__(self, handler):
            super().__init__()
            self.setDaemon(True)
            self.handler = handler
            self.event = handler.event

        def run(self):
            while not self.handler.flag_cancel:
                self.event.wait()
                self.event.clear()
                while not self.handler.flag_cancel:
                    try:
                        packet = self.handler.read_packet()
                        self.handler.error = RET_OK

                        if self.handler.is_heart_beat(packet):
                            logger.info(">-- heart beat <--")
                            continue

                        if self.handler.is_screenmode:
                            with self.handler.mutex:
                                self.handler.last_packet = packet
                        else:
                            self.handler.res_queue.put(packet)
                        # f = self.handler.command_filter
                        # if f and f.is_keep_packet(packet):
                        #     #logger.info("get packet:{}".format(packet))
                        #     #logger.info("get packet")
                        #     self.handler.res_queue.put(packet)
                        # else:
                        #     logger.info("skip packet:{}, f={}".format(packet, f))
                    except Exception as e:
                        logger.error('read packet exception', exc_info=True)
                        # logger.error('read packet exception {}'.format(e))

                        # inform writer thread break
                        logger.info("reader: put packet MSG_CLOSE_SOCKET")
                        self.handler.queue.put(MSG_CLOSE_SOCKET)
                        self.handler.set_error()
                        break

    class HeartBeat(threading.Thread):
        def __init__(self, handler):
            super().__init__()
            self.setDaemon(True)
            self.handler = handler
            self.event = handler.heartEvent

        def run(self):
            while not self.handler.flag_cancel:
                self.event.wait()
                self.event.clear()
                while not self.handler.flag_cancel and self.handler.error is RET_OK:
                    logger.info("<-- heart beat -->")
                    self.handler.queue.put(self.handler.heart_beat())
                    time.sleep(5)

    def run(self):
        # start reader client
        self.reader.start()

        if self.heart_beat():
            self.beater.start()

        while not self.flag_cancel:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                logger.info("connect {}:{}".format(self.ip, self.port))
                try:
                    sock.connect((self.ip, self.port))
                    self.sock = sock
                    logger.info("set socket option")
                    self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    l_onoff = 1;
                    l_linger = 0
                    self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', l_onoff, l_linger))
                    self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                except:
                    logger.error('connect and setoption exception', exc_info=True)
                    self.close()
                    time.sleep(3)
                    continue

                # clear all packets
                while True:
                    try:
                        self.queue.get_nowait()
                    except queue.Empty:
                        break

                # start reader thread
                if not self.event.is_set():
                    logger.info("set event")
                    self.event.set()

                if not self.heartEvent.is_set():
                    logger.info("set heartEvent")
                    self.heartEvent.set()

                # send a heart beat
                if self.heart_beat():
                    self.queue.put(self.heart_beat())

                while not self.flag_cancel:
                    try:
                        packet = self.queue.get(timeout=1)
                    except queue.Empty:
                        continue

                    try:
                        if packet is MSG_CLOSE_SOCKET:
                            break
                        # logger.info("write packet:{}".format(packet))
                        self.write_packet(packet)
                    except:
                        logger.error('write packet exception', exc_info=True)
                        break
                # handle packet
                self.close()
                logger.info("break here, not flag=" + str(not self.flag_cancel) )
                time.sleep(3)


class TouchSocketHandler(TcpSocketHandler):
    def read_packet(self):
        packet_bytes = self.read_packet_bytes()
        pkg = TouchPkg()
        pkg.ParseFromString(packet_bytes)
        return pkg

class CloudscreenSocketHandler(TcpSocketHandler):
    def __init__(self, ip, port, command_filter=None):
        super().__init__(ip, port, command_filter, is_screenmode=True)

    def read_packet(self):
        packet_bytes = self.read_packet_bytes()
        pkg = CloudscreenPkg()
        pkg.ParseFromString(packet_bytes)
        return pkg

    def is_heart_beat(self, pkg):
        return pkg.header.command == CLOUDSCREEN_HEARTBEAT_RES

    def heart_beat(self):
        pkg = CloudscreenPkg()
        pkg.header.sequenceId = 9527
        pkg.header.timestamp = 0
        pkg.header.command = CLOUDSCREEN_HEARTBEAT_REQ
        return pkg

    def get_last_packet(self):
        with self.mutex:
            packet = self.last_packet
            return self.error, packet
