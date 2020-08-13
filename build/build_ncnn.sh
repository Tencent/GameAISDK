#!/bin/sh

echo "------------------------------------- build darknet2Ncnn -------------------"

if [ $# -lt 1 ]; then
    echo "useage: OPENCV_2|OPENCV_3"
    exit 1
fi

cd ../Modules/darknet2ncnn
cd darknet
make -j8
rm libdarknet.so

echo "------------------------------------- build Ncnn -------------------"
cd ../ncnn
mkdir build
cd build
cmake ..
make -j8
make install
cd ../../

param=""
if [ $1 = OPENCV_2 ]; then
    param="OPENCV=2"
elif [ $1 = OPENCV_3 ]; then
    param="OPENCV=3"
fi
make -j8 ${param}
