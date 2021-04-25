#!/bin/sh

gen_cpp_pb()
{
	echo ../protocol/$2 '-->' $1
	protoc -I ../protocol --cpp_out $1 ../protocol/$2 || exit 1
}

gen_py_pb()
{
	echo ../protocol/$2 '-->' $1
	protoc -I ../protocol --python_out $1 ../protocol/$2 || exit 1
}

echo "------------------------------------- generate pb start -------------------"

if [ -d ../src/ImgProc/ ]; then
	gen_cpp_pb ../src/ImgProc/Protobuf/ common.proto
	gen_cpp_pb ../src/ImgProc/Protobuf/ gameregProtoc.proto
fi

if [ -d ../tools/SDKTool/src/communicate/protocol/ ]; then
	gen_py_pb ../tools/SDKTool/src/communicate/protocol/ common.proto
	gen_py_pb ../tools/SDKTool/src/communicate/protocol/ gameregProtoc.proto
fi

gen_py_pb ../src/ManageCenter/pyManageCenter/protocol/ common.proto
gen_py_pb ../src/ManageCenter/pyManageCenter/protocol/ gameregProtoc.proto
gen_py_pb ../src/IOService/pyIOService/protocol/ common.proto
gen_py_pb ../src/IOService/pyIOService/protocol/ gameregProtoc.proto
gen_py_pb ../src/API/AgentAPI/protocol/ common.proto
gen_py_pb ../src/API/AgentAPI/protocol/ gameregProtoc.proto
gen_py_pb ../src/AgentAI/protocol/ common.proto
gen_py_pb ../src/AgentAI/protocol/ gameregProtoc.proto

echo "------------------------------------- generate pb end -------------------\n"
