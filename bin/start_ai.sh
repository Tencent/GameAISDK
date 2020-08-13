#!/bin/sh

PWD=`pwd`
export PATH=$PATH:$PWD/
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$PWD/lib/

echo "Run AI Service"


#Start MC process
python3 manage_center.py --runType=AI >/dev/null 2>&1 &
sleep 1

#Check MC process
ps -fe | grep 'python3 manage_center.py' | grep -v grep
if [ $? -ne 0 ]; then
	echo "No MC process"
	exit 4
fi


#Start IO process
python3 io_service.py >/dev/null 2>&1 &
sleep 1

#Check IO process
ps -fe | grep 'python3 io_service.py' | grep -v grep
if [ $? -ne 0 ]; then
	echo "No IO process"
	exit 5
fi


#Start Agent process
python3 agentai.py >/dev/null 2>&1 &
sleep 10

#Check Agent process
ps -fe | grep 'python3 agentai.py' | grep -v grep
if [ $? -ne 0 ]; then
	echo "No Agent process"
	exit 1
fi


#Start GameReg process
./GameReg >/dev/null 2>&1 &
sleep 1

#Check GameReg process
ps -fe | grep 'GameReg' | grep -v grep
if [ $? -ne 0 ]; then
	echo "No GameReg process"
	exit 3
fi


exit 0
