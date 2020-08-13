#!/bin/sh

echo "------------------------------------- build api start -------------------"

rm -rf ../bin/API
python3 CompilePy3Pyc.py ../src/API/  ../bin/API/ || exit 1

echo "------------------------------------- build api end -------------------\n"
