#!/bin/sh

echo "------------------------------------- build plugin start -------------------"

rm -rf ../bin/PlugIn
python3 CompilePy3Pyc.py ../src/PlugIn/  ../bin/PlugIn/ || exit 1

echo "------------------------------------- build plugin end -------------------\n"
