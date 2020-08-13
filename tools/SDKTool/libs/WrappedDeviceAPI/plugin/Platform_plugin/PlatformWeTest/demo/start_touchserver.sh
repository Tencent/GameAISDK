#!/bin/bash

cd ../touchserver

adb push libs/arm64-v8a/touchserver /data/local/tmp/

adb shell chmod 777 /data/local/tmp/touchserver

adb shell /data/local/tmp/touchserver

# the touch server listen on port 25766 in android phone
adb forward tcp:1111 tcp:25766

# detect 
adb forward --list

