#!/bin/sh

buildYoloV3()
{
    make -j12 || exit 1
    make install || exit 2
}

if [ $# -gt 0 ]; then
    if [ $1 = GPU ]; then
        cp Makefile_GPU Makefile
        buildYoloV3
    elif [ $1 = CPU ]; then
        cp Makefile_CPU Makefile
        buildYoloV3
    fi
else
    cp Makefile_CPU Makefile
    buildYoloV3

    cp Makefile_GPU Makefile
    buildYoloV3
fi

