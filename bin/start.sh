#!/bin/sh

PWD=`pwd`
export PATH=$PATH:$PWD/
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/opencv3.4.2/lib

if [ $# -gt 0 ]; then
    if [ $1 = AI ]; then
        ./start_ai.sh
        exit 1
    elif [ $1 = UI+AI ]; then
        ./start_ui_ai.sh
        exit 2
    elif [ $1 = TRAIN ]; then
        ./start_im_train.sh
        exit 3
    elif [ $1 = UI ]; then
        ./start_ui.sh
        exit 4
    fi
else
    ./start_ai.sh
    exit 1
fi

exit 0
