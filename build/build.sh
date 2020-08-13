#!/bin/sh

if [ $# -lt 1 ]; then
	echo "useage: ./build.sh GPU|CPU"
	exit 1
fi

./gen_pb.sh || exit 2
./build_io.sh || exit 3
./build_mc.sh || exit 4
./build_agent.sh || exit 5
./build_api.sh || exit 6
./build_plugin.sh || exit 7
if [ -d ../src/ImgProc/ ]; then
	./build_cpp.sh $1 || exit 8
fi