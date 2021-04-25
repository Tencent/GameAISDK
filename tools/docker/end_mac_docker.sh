#bin/bash
ps -e|grep "socat"|grep -v grep|awk '{print $1}' |xargs kill -9
ps -e|grep "quartz"|grep -v grep|awk '{print $1}' |xargs kill -9
docker ps |grep "aisdktoolclt"|grep -v grep|awk '{print $1}' |xargs docker stop
