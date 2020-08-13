import os
import sys
import time
import logging
import logging.config
import json
import cv2
import numpy
import queue

__dir__ = os.path.dirname(os.path.abspath(__file__))
sys.path.append(__dir__)

import Notify

from .Initializer import Initializer
from devicePlatform.IPlatformProxy import *
from .TcpSocketHandler import TouchSocketHandler, CloudscreenSocketHandler

from .pb.touch.TouchPkgPB_pb2 import *
from .pb.cloudscreen.CloudscreenPkgPB_pb2 import *

logger = logging.getLogger(__name__)

def setup_logging(default_path='logging.json', default_level=logging.INFO, env_key='LOG_CFG'):
    """Setup logging configuration
    """
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = json.load(f)
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)


class PlatformWeTest(IPlatformProxy):
    def __init__(self, host='127.0.0.1', touch_port=Initializer.TOUCH_SEVER_PORT,
                 cloudscreen_port=Initializer.CLOUD_SCREEN_PORT, force_orientation=True):
        IPlatformProxy.__init__(self)
        self.__deviceInfo = DeviceInfo()
        self.__touch_handler = None
        self.__host = host
        self.__touch_port = touch_port
        self.__cloudscreen_port = cloudscreen_port
        self.__cloudscreen_handler = None
        self.__seq = 0

        self.__game_width = 0
        self.__game_height = 0
        self.__regular_height = 0
        self.__scale = None
        self.__orientation = None
        self.__force_orientation = force_orientation
        self.__push_started = False
        # notify mobile agent to capture screen and mark with red dot
        self.__enable_notify = False

    def __get_seq(self):
        self.__seq = self.__seq + 1
        return self.__seq

    def init(self, serial=None, is_portrait=True, long_edge=None, **kwargs):
        # install dependency
        standalone = kwargs["standalone"] if "standalone" in kwargs else True

        __dir__ = os.path.dirname(os.path.abspath(__file__))
        initializer = Initializer(resource_dir=os.path.join(__dir__, ".."))
        initializer.setup(standalone)

        # start touch thread
        self.__touch_handler = TouchSocketHandler(self.__host, self.__touch_port)
        self.__touch_handler.start()
        logger.info("wait touch thread start")
        self.__touch_handler.event.wait()
        logger.info("touch thread started")

        # start cloudscreen thread
        self.__cloudscreen_handler = CloudscreenSocketHandler(self.__host, self.__cloudscreen_port)
        self.__cloudscreen_handler.start()
        logger.info("wait cloudscreen thread start")
        self.__cloudscreen_handler.event.wait()
        logger.info("cloudscreen thread started")

        ret, desc = self.get_device_info()
        if ret is None:
            logger.error("cannot get device info: {}".format(desc))
            return False, desc

        self.__scale = long_edge * 1.0 / self.__deviceInfo.display_height

        if is_portrait:
            self.__game_width = self.__deviceInfo.display_width * self.__scale
            self.__game_height = long_edge
        else:
            self.__game_width = long_edge
            self.__game_height = self.__deviceInfo.display_width * self.__scale
        self.__regular_height = long_edge

        logger.info("game_width={}, height={}".format(self.__game_width, self.__game_height))

        self.__enable_notify = kwargs["enable_notify"] if "enable_notify" in kwargs else False
        if self.__enable_notify:
            logger.info("PlatformWeTest: start Notify thread")
            Notify.start()
        return True, ""

    def deinit(self):
        logger.info("deinit enter")
        if self.__cloudscreen_handler:
            self.__cloudscreen_handler.quit()
            logger.info("stop cloudscreen_handler")

        if self.__touch_handler:
            self.__touch_handler.quit()
            logger.info("stop touch_handler")
        logger.info("deinit end")


    def get_rotation(self):
        return self.__orientation

    def get_device_info(self):
        touch_ret = self.__get_touch_info()
        if touch_ret is None:
            return None, "get touch info error"

        self.__deviceInfo.touch_height = touch_ret["touch_height"]
        self.__deviceInfo.touch_width = touch_ret["touch_width"]
        self.__deviceInfo.touch_slot_number = touch_ret["touch_slot_number"]

        display_ret = self.__get_display_info()
        if display_ret is None:
            return None, "get display info error"
        self.__deviceInfo.display_height = display_ret["dp_height"]
        self.__deviceInfo.display_width = display_ret["dp_width"]
        return self.__deviceInfo, ""

    def get_image(self):
        # err, res = self.__capture_screen(index=0, quality=80,
        #                                  captureType=JPEG_CAPTURE,
        #                                  screenCaptureMode=PRESET_CONFIG_CAPTURE_MODE)
        self.__start_capture_screen_push_mode(height=self.__regular_height,
                                              quality=80,
                                              minInterval=40,
                                              landscape=False)
        err, res = self.__get_frame()
        if err != 0 or res is None:
            logger.info("get image error: {}, res:{}".format(err, res))
            return err, None
        else:
            image = cv2.imdecode(numpy.frombuffer(res["datas"], dtype=numpy.uint8), cv2.IMREAD_COLOR)
            if self.__force_orientation:
                if self.__game_width > self.__game_height:
                    # rotate 90 always
                    return 0, cv2.flip(cv2.transpose(image), 0)
                else:
                    return 0, image
            else:
                # return image as real orientation
                if self.__orientation == SCREEN_ORIENTATION_0:
                    return 0, image
                elif self.__orientation == SCREEN_ORIENTATION_90:
                    return 0, cv2.flip(cv2.transpose(image), 0)
                elif self.__orientation == SCREEN_ORIENTATION_180:
                    # FIXME
                    return 0, cv2.flip(cv2.transpose(image), 0)
                elif self.__orientation == SCREEN_ORIENTATION_270:
                    return 0, cv2.flip(cv2.transpose(image), 1)

            return 0, image

    def touch_down(self, x, y, contact, pressure=50):
        touch = self.__trans_xy2(x, y)
        if self.__enable_notify:
            Notify.post_touch(*touch)

        _x, _y = self.__trans_xy(x, y)
        self.__inject_touch_event(TOUCH_TOUCH_DOWN, _x, _y, contact, pressure)
        self.__touch_commit()

    def touch_move(self, x, y, contact, pressure=50):
        touch = self.__trans_xy2(x, y)

        if self.__enable_notify:
            Notify.post_touch(*touch)

        _x, _y = self.__trans_xy(x, y)
        self.__inject_touch_event(TOUCH_TOUCH_MOVE, _x, _y, contact, pressure)
        self.__touch_commit()

    def touch_up(self, contact):
        self.__inject_touch_event(TOUCH_TOUCH_UP, pointer_id=contact)
        self.__touch_commit()

    def touch_reset(self):
        self.__inject_touch_event(TOUCH_RESET, pressure=0)
        self.__touch_commit()

    def touch_wait(self, milliseconds):
        self.__inject_touch_event(TOUCH_WAIT, wait_time=milliseconds)
        self.__touch_commit()

    def __touch_commit(self):
        self.__inject_touch_event(TOUCH_COMMIT)

    # low device api
    def __inject_touch_event(self, touch_type, x=0, y=0, pointer_id=0, pressure=0, wait_time=0):
        pkg = TouchPkg()
        pkg.header.sequenceId = self.__get_seq()
        pkg.header.timestamp = int(time.time())
        pkg.header.command = TOUCH_EVENT_NOTIFY

        event = pkg.body.touchEventNotify.touchevents.add()
        event.touchType = touch_type
        event.slotId = pointer_id
        event.x = x
        event.y = y
        event.pressure = pressure
        # note: event's waittime is us
        event.waittime = wait_time*1000
        self.__touch_handler.queue.put(pkg)

    def __get_touch_info(self):
        pkg = TouchPkg()
        pkg.header.sequenceId = self.__get_seq()
        pkg.header.timestamp = 0
        pkg.header.command = TOUCH_DEVICE_INIT_REQ
        self.__touch_handler.queue.put(pkg)
        try:
            packet = self.__touch_handler.res_queue.get(timeout=3)
        except queue.Empty:
            logger.error("error: get touch info timeout!")
            return None

        if packet.body.touchDeviceInitRes.result.errorcode == TOUCH_SUCC:
            recv_info = packet.body.touchDeviceInitRes.touchDeviceInfo
            return dict(touch_name=recv_info.devicename,
                        touch_devpath=recv_info.devpath,
                        touch_slot_number=recv_info.maxTrackingID,
                        touch_width=recv_info.maxPostionX,
                        touch_height=recv_info.maxPostionY,
                        touch_hasBtnTouch=recv_info.hasBtnTouch)
        return None

    def __get_display_info(self):
        pkg = CloudscreenPkg()
        pkg.header.sequenceId = self.__get_seq()
        pkg.header.timestamp = 0
        pkg.header.command = DISPLAY_DEVICE_INFO_REQ
        self.__cloudscreen_handler.queue.put(pkg)
        for i in range(0, 10):
            err, packet = self.__cloudscreen_handler.get_last_packet()
            if err != 0 or packet is None:
                logger.error("get_display_info: err={}, packet={}".format(err, packet))
                time.sleep(1)
                continue

            if packet.header.command == DISPLAY_DEVICE_INFO_RES \
                    and packet.body.displayDeviceInfoRes.result.errorcode == CLOUDSCREEN_SUCC:
                recv_info = packet.body.displayDeviceInfoRes
                return dict(dp_width=recv_info.width,     # int
                            dp_height=recv_info.height,   # int
                            dp_fps=recv_info.fps,         # float
                            dp_density=recv_info.density, # float
                            dp_xdpi=recv_info.xdpi,       # float
                            dp_ydpi=recv_info.ydpi,       # float
                            dp_orientation=recv_info.orientation, # ScreenOrientation
                            dp_secure=recv_info.secure,)

        logger.error("error: cannot get display info in 2 seconds")
        return None

    def __get_frame(self):
        err, packet = self.__cloudscreen_handler.get_last_packet()
        if err != 0 or packet is None:
            self.__push_started = False
            return err, packet

        if packet.header.command == SCREEN_CAPTURE_FRAME_NOTIFY \
                and packet.body.screenCaptureFrameNotify.result.errorcode == CLOUDSCREEN_SUCC:
            #logger.info("package: {}".format(packet))
            recv_info = packet.body.screenCaptureFrameNotify
            # update device's orientation
            self.__orientation = int(recv_info.orientation)
            return 0, dict(result=recv_info.result,
                        index=recv_info.index,
                        width=recv_info.width,
                        height=recv_info.height,
                        orientation=recv_info.orientation,
                        len=recv_info.len,
                        datas=recv_info.datas,)
        return packet.body.screenCaptureRes.result.errorcode, None

    def __start_capture_screen_push_mode(self, **kwargs):
        if self.__push_started:
           return

        self.__push_started = True
        pkg = CloudscreenPkg()
        pkg.header.sequenceId = self.__get_seq()
        pkg.header.timestamp = 0
        pkg.header.command = SCREEN_CAPTURE_PUSH_MODE_REQ

        logger.info("----: kwargs {}".format(kwargs))
        logger.info("----: {}".format(kwargs["height"]))
        pkg.body.screenCapturePushModeReq.height = int(kwargs["height"]) if "height" in kwargs else 0
        pkg.body.screenCapturePushModeReq.quality = kwargs["quality"] if "quality" in kwargs else 0
        pkg.body.screenCapturePushModeReq.minInterval = kwargs["minInterval"] if "minInterval" in kwargs else 50
        pkg.body.screenCapturePushModeReq.landscape = kwargs["landscape"] if "landscape" in kwargs else False

        self.__cloudscreen_handler.queue.put(pkg)

    def __stop_capture_screen_push_mode(self):
        if self.__push_started:
            self.__push_started = False

            pkg = CloudscreenPkg()
            pkg.header.sequenceId = self.__get_seq()
            pkg.header.timestamp = 0
            pkg.header.command = SCREEN_CAPTURE_PUSH_STOP_REQ
            self.__cloudscreen_handler.queue.put(pkg)

    def __trans_xy2(self, x, y):
        if self.__game_width > self.__game_height:
            nx, ny = self.__game_height - y, x
            return int(self.__game_height), int(self.__game_width), int(nx), int(ny)
        else:
            nx, ny = x, y
            return int(self.__game_width), int(self.__game_height), int(nx), int(ny)

    def __trans_xy(self, x, y):
        if self.__force_orientation:
            if self.__game_width > self.__game_height:
                nx, ny = self.__game_height - y, x
            else:
                nx, ny = x, y
        else:
            # if get orientation failed, rotation with game_width/game_height
            if self.__orientation != SCREEN_ORIENTATION_UNKNOW:
                orientation = self.__orientation
            else:
                orientation = SCREEN_ORIENTATION_90 if self.__game_height < self.__game_width else SCREEN_ORIENTATION_0

            if orientation == SCREEN_ORIENTATION_0:
                nx, ny = x, y
            elif orientation == SCREEN_ORIENTATION_90:   # counter-clockwise 90
                nx, ny = self.__game_height - y, x
            elif orientation == SCREEN_ORIENTATION_180:
                nx, ny = self.__game_width - y, x
            elif orientation == SCREEN_ORIENTATION_270:  # clockwise 90
                nx, ny = y, self.__game_width - x
            else:
                nx, ny = x, y

        # _x, _y = int(nx / self.__scale), int(ny / self.__scale)
        if self.__game_width > self.__game_height:
            _touch_scale_x = nx / self.__game_height
            _touch_scale_y = ny / self.__game_width
        else:
            _touch_scale_x = nx / self.__game_width
            _touch_scale_y = ny / self.__game_height
        _x = int(self.__deviceInfo.touch_width * _touch_scale_x)
        _y = int(self.__deviceInfo.touch_height * _touch_scale_y)
        logger.info("{},{} -> {},{}".format(x, y, _x, _y))
        return _x, _y

def test_move(GAME_HEIGHT=640):
    # test move
    device_action = PlatformWeTest("127.0.0.1", Initializer.TOUCH_SEVER_PORT, Initializer.CLOUD_SCREEN_PORT)
    device_action.init(is_portrait=False, long_edge=GAME_HEIGHT)
    di = device_action.get_device_info()

    __width = GAME_HEIGHT * 1.0 /di.display_height * di.display_width
    start_x, start_y, end_x, end_y = 0, 0, GAME_HEIGHT, __width

    steps_w = 20
    steps = int((end_x - start_x) * 1.0 / steps_w)
    steps_h = int((end_y - start_y) / steps)

    logger.info("{},{} -> {},{}, steps={}".format(start_x, start_y, end_x, end_y, steps))

    device_action.touch_reset()
    device_action.touch_down(start_x, start_y, 0)
    device_action.touch_down(end_x, start_y, 1)
    for i in range(0, steps):
        #device_action.touch_wait(200)
        time.sleep(0.2)
        device_action.touch_move(start_x + i * steps_w, start_y + i * steps_h, 0)
        device_action.touch_move(end_x - i * steps_w, start_y + i * steps_h, 1)

    device_action.touch_up(0)
    device_action.touch_up(1)

def test_image(GAME_HEIGHT = 640):
    device_action = PlatformWeTest("127.0.0.1", Initializer.TOUCH_SEVER_PORT, Initializer.CLOUD_SCREEN_PORT)
    ret, desc = device_action.init(is_portrait=True, long_edge=GAME_HEIGHT)
    if ret is False:
        logger.info("device action init fail")
        device_action.deinit()
        return

    index = 0
    while True:
        err, image = device_action.get_image()
        if err == 0:
            logger.info("index={} orientation: {}".format(index, device_action.get_rotation()))
            # cv2.imwrite("test_{}.jpg".format(index), image)
            index = index + 1
        else:
            logger.info("error: {}".format(err))

        time.sleep(1)

def test_getinfo(GAME_HEIGHT = 640):
    # test get touch info
    device_action = PlatformWeTest("127.0.0.1", Initializer.TOUCH_SEVER_PORT, Initializer.CLOUD_SCREEN_PORT)
    device_action.init(is_portrait=False, long_edge=GAME_HEIGHT)
    device_info = device_action.get_device_info()
    logger.info("{}".format(device_info))

if __name__ == "__main__":
    setup_logging()

    test_image()
    # test_move()
