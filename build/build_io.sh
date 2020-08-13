#!/bin/sh

echo "------------------------------------- build io start -------------------"

rm -rf ../bin/pyIOService
python3 CompilePy3Pyc.py ../src/IOService/pyIOService/  ../bin/pyIOService/ || exit 1
cp -f ../src/IOService/*.py  ../bin/ || exit 2

echo "------------------------------------- build io end -------------------\n"