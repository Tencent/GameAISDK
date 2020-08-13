adb push ..\touchserver\binary\arm64-v8a\touchserver /data/local/tmp/

adb shell chmod 777 /data/local/tmp/touchserver

adb shell /data/local/tmp/touchserver

adb forward tcp:1111 tcp:25766

adb forward --list

