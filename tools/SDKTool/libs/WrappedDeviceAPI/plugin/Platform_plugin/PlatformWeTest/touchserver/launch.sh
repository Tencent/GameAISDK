#!/bin/bash

adb push xxx/touchserver /data/local/tmp/

adb chmod 777 /data/local/tmp/touchserver

adb shell /data/local/tmp/touchserver

# the touch server listen on port 25766 in android phone
adb forward tcp:localport tcp:25766

# detect 
adb forward --list

