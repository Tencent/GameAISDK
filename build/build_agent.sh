#!/bin/sh

echo "------------------------------------- build agent start -------------------"

rm -rf ../bin/AgentAI
python3 CompilePy3Pyc.py ../src/AgentAI/  ../bin/AgentAI/ || exit 1
cp -f ../src/AgentAI/*.py  ../bin/ || exit 2

echo "------------------------------------- build agent end -------------------\n"
