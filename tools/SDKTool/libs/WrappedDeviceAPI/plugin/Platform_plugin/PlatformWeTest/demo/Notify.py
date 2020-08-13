import os
import time
import json
import requests
import threading

host_ip = os.environ.get("TEST_AGENT_IP", "172.23.0.1")
manager_port = int(os.environ.get("WTMANAGER_PORT", "8080"))
device_serial = os.environ.get("ADB_SERIAL")
mobile_agent_port = None

shouldStop = False
last_touch = (1080, 1920, 0, 0) #(with, height, x, y)
mutex = threading.Lock()

def post_touch(w, h, x, y):
    global last_touch
    with mutex:
        last_touch = (w, h, x, y)

def get_touch():
    global last_touch
    with mutex:
        touch = last_touch
        last_touch = None
        return touch

def notify_loop():
    while shouldStop == False:
        touch = get_touch()
        if touch:
            w,h,x,y = touch
            __notify_touch(-1, w, h, x, y, device_serial)

        time.sleep(2)

def start():
    global shouldStop
    shouldStop = False
    t = threading.Thread(target=notify_loop, args=())
    t.setDaemon(True)
    t.start()

def __get_seq():
    return int(round(time.time()*1000))

def __notify_touch(testid, width, height, x, y, serial):
    global mobile_agent_port
    if mobile_agent_port is None:
        mobile_agent_port = __get_mobile_agent_port(serial)

    url = 'http://{}:{}/touchpositionnotify'.format(host_ip, mobile_agent_port)
    params = json.dumps(dict(testid=testid, width=width, height=height, x=x, y=y, name="WeTest"))

    json_str = json.dumps(dict(params=params, sequenceId=__get_seq(), serial=serial))
    print("msg={}".format(json_str))

    headers = {"content-type": "application/json"}
    r = requests.post(url, headers=headers, data=json_str, timeout=10)
    print(r.text)

def __get_mobile_agent_port(serial):
    url = 'http://{}:{}/servicerealport'.format(host_ip, manager_port)
    params = json.dumps(dict(portType="dev-http-port-req", serialNumber=serial))

    json_str = json.dumps(dict(params=params, sequenceId=__get_seq(), serial=serial))
    # print("msg={}".format(json_str))

    headers = {"content-type": "application/json"}
    r = requests.post(url, headers=headers, data=json_str, timeout=10)
    print("type(r.text)={}".format(r.text))
    json_ret = json.loads(r.text)
    if "errorno" in json_ret and json_ret["errorno"] == 0:
        ret_str = json_ret["result"]
        load_dict = json.loads(ret_str)
        port = load_dict["dev-http-port-req"]
        print("mobile-agent-port: {}".format(port))
        return port
    # print(r.text)
    return 0

#serial = "MASLHMB7B1100454"
#get_mobile_agent_port(serial)
#test_touch_picture(40020, 0, 1080, 1920, 508, 1531, serial)
