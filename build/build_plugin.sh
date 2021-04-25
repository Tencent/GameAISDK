#!/bin/sh

echo "------------------------------------- build plugin start -------------------"

rm -rf ../bin/PlugIn
cp -r ../src/PlugIn/  ../bin/PlugIn/ || exit 1

echo "------------------------------------- build plugin end -------------------\n"
