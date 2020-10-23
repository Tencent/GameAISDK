import cv2
import time
import logging

import platform
__is_windows_system = platform.platform().lower().startswith('window')
__is_linux_system = platform.platform().lower().startswith('linux')
if __is_windows_system:
    from demo_windows.PlatformWeTest import PlatformWeTest, setup_logging
    from demo_windows.Initializer import Initializer
elif __is_linux_system:
    from demo_ubuntu16.PlatformWeTest import PlatformWeTest, setup_logging
    from demo_ubuntu16.Initializer import Initializer
else:
    raise Exception('system is not support!')


logger = logging.getLogger(__name__)

def __test_move(GAME_HEIGHT=640):
    # test move
    device_action = PlatformWeTest("127.0.0.1")
    ret, desc = device_action.init(is_portrait=True, long_edge=GAME_HEIGHT)
    if ret is False:
        logger.info("device action init fail")
        device_action.deinit()
        return

    di, _ = device_action.get_device_info()
    __width = GAME_HEIGHT * 1.0 / di.display_height * di.display_width
    start_x, start_y, end_x, end_y = 50, int(GAME_HEIGHT/2), 250, int(GAME_HEIGHT/2)

    steps_w = 20
    steps = int((end_x - start_x) * 1.0 / steps_w)
    steps_h = int((end_y - start_y) / steps)

    logger.info("{},{} -> {},{}, steps={}".format(start_x, start_y, end_x, end_y, steps))

    device_action.touch_reset()
    device_action.touch_down(start_x, start_y, 0)
    device_action.touch_down(end_x, start_y, 1)
    for i in range(0, steps):
        time.sleep(0.2)
        device_action.touch_move(start_x + i * steps_w, start_y + i * steps_h, 0)
        device_action.touch_move(end_x - i * steps_w, start_y + i * steps_h, 1)

    device_action.touch_up(0)
    device_action.touch_up(1)
    time.sleep(0.2*steps+2)

device_action = None
def _onMouseEvent(event, x, y, flags, param):
    global device_action
    if event & cv2.EVENT_LBUTTONUP:  # cv2.EVENT_LBUTTONUP=4
        if device_action:
            st = time.time()
            device_action.touch_down(x, y, 0)
            device_action.touch_up(0)
            print(time.time()-st)
            
def __test_image(GAME_HEIGHT = 640):
    global device_action
    device_action = PlatformWeTest("127.0.0.1", Initializer.TOUCH_SEVER_PORT, Initializer.CLOUD_SCREEN_PORT)
    ret, desc = device_action.init(is_portrait=True, 
                                   long_edge=GAME_HEIGHT,
                                   standone=True)
    if ret is False:
        logger.info("device action init fail")
        device_action.deinit()
        return
    
    device_action.touch_reset()
    index = 0
    while True:
        err, image = device_action.get_image()
        if err == 0 and image is not None:
            #logger.info("index={} orientation: {}".format(index, device_action.get_rotation()))
            try:
                #cv2.imwrite("test_{}.jpg".format(index), image)
                cv2.imshow('test1', image)
                if index == 0:
                    cv2.setMouseCallback('test1', _onMouseEvent)
                cv2.waitKey(1)
            except:
                pass
            index = index + 1
        else:
            logger.info("error: {}".format(err))

        time.sleep(1)

def __test_getinfo(GAME_HEIGHT = 640):
    # test get touch info
    device_action = PlatformWeTest("127.0.0.1", Initializer.TOUCH_SEVER_PORT, Initializer.CLOUD_SCREEN_PORT)
    ret, desc = device_action.init(is_portrait=False, long_edge=GAME_HEIGHT, standalone=True)
    if ret is False:
        logger.info("device action init fail")
        device_action.deinit()
        return

    device_info, _ = device_action.get_device_info()
    logger.info("{}".format(device_info))


if __name__ == "__main__":
    setup_logging(default_path="demo/logging.json")

    __test_image()
    #__test_move()
