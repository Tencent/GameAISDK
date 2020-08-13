#!/bin/sh
if [ $# -lt 1 ]; then
	echo "useage: ./build_modules.sh GPU|CPU"
	exit 1
fi

AI_SDK_ROOT=`pwd`/..

echo "--------------libtbus start------------------"
#build libtbus.so
cd $AI_SDK_ROOT/Modules/tbus/libtbus
./make_tbus.sh
cp -f libtbus.so $AI_SDK_ROOT/bin
cd -
echo "--------------libtbus end------------------"


echo "--------------pytbus start------------------"
#build tbus.so for python3
cd $AI_SDK_ROOT/Modules/tbus/pytbus/linux-cp3
python3 setup.py build
LIB_DIR=`ls build | grep lib | grep -v grep`
cp -f build/$LIB_DIR/tbus.*.so $AI_SDK_ROOT/bin
cd -
echo "--------------pytbus end------------------"


echo "--------------jsoncpp start------------------"
#build libjsoncpp.so
cd $AI_SDK_ROOT/Modules/Json/jsoncpp-master
./build.sh
cd -
echo "--------------jsoncpp end------------------"


echo "--------------darnet start------------------"
#build libdarknetV3_CPU.so or libdarknetV3_GPU.so
cd $AI_SDK_ROOT/Modules/darknetV3/src

chmod +x InstallYoloV3.sh
if [ $# -gt 0 ]; then
    if [ $1 = GPU ]; then
        ./InstallYoloV3.sh GPU || exit 2
    elif [ $1 = CPU ]; then
        ./InstallYoloV3.sh CPU || exit 3
    fi
else
    ./InstallYoloV3.sh || exit 4
fi
cd -
echo "--------------darnet end------------------"