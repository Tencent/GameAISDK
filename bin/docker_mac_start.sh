#bin/bash

cd /data1/game_ai_sdk/build
sh build_modules.sh CPU
sh build.sh CPU

cp /data1/game_ai_sdk/bin/*.so* /usr/local/lib/
ldconfig
cd /data1/game_ai_sdk/tools/SDKTool
adb connect host.docker.internal:7788

source /etc/profile
python main.py
