#bin/bash

cp /data1/game_ai_sdk/bin/*.so* /usr/local/lib/
ldconfig

cd /data1/game_ai_sdk/tools/SDKTool
adb connect host.docker.internal:7788

source /etc/profile
python main.py
