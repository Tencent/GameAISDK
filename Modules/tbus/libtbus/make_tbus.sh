#!/bin/sh


if [ `whoami` = "root" ];then
       echo "root user"
       cp -f libtbus.so /usr/local/lib/
else
       echo "not root user"
       sudo cp -f libtbus.so /usr/local/lib/
fi
