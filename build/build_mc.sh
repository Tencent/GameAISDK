#!/bin/sh

echo "------------------------------------- build mc start -------------------"

rm -rf ../bin/pyManageCenter
python3 CompilePy3Pyc.py ../src/ManageCenter/pyManageCenter/  ../bin/pyManageCenter/ || exit 1
cp -f ../src/ManageCenter/*.py  ../bin/ || exit 2

echo "------------------------------------- build mc end -------------------\n"