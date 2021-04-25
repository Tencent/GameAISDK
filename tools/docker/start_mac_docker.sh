#bin/bash
socat TCP-LISTEN:6000,reuseaddr,fork UNIX-CLIENT:\"$DISPLAY\"  &
open -a xquartz &

adb devices |awk 'NR==2 {print $1}' |xargs adbkit usb-device-to-tcp -p 7788 &

path=$(dirname $(dirname `pwd`))
echo 'project path:' $path
docker run -v $path:/data1/game_ai_sdk -it base_aisdktoolclt_ubt16:debug-2.0.2 /bin/bash /data1/game_ai_sdk/bin/docker_start_service.sh
