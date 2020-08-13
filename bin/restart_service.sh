#!/bin/sh

PWD=`pwd`
export PATH=$PATH:$PWD/
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$PWD/lib/

echo "Restart services"

if [ $# -gt 0 ]; then
    if [ $1 = AI ]; then
        pkill -SIGINT -f agentai.py
        # pkill -SIGUSR1 -f GameRegMain.py
        pkill -SIGUSR1 -f GameReg
        sleep 4
        # Clean SHM resource
        ipcs | awk '{if($6==0) printf "ipcrm shm %d\n",$2}'| sh

        #Start Agent process
        python3 agentai.py >/dev/null 2>&1 &
        sleep 10

        #Start GameRecognize process
        # python3 GameRegMain.py >/dev/null 2>&1 &
        ./GameReg >/dev/null 2>&1 &
        sleep 1

        exit 0
    elif [ $1 = UI+AI ]; then
        pkill -SIGINT -f agentai.py
        # pkill -SIGUSR1 -f GameRegMain.py
        pkill -SIGUSR1 -f GameReg
        pkill -SIGUSR1 -f UIRecognize
        sleep 4
        # Clean SHM resource
        ipcs | awk '{if($6==0) printf "ipcrm shm %d\n",$2}'| sh

        #Start Agent process
        python3 agentai.py >/dev/null 2>&1 &
        sleep 10

        #Start GameRecognize process
        # python3 GameRegMain.py >/dev/null 2>&1 &
        ./GameReg >/dev/null 2>&1 &
        sleep 1

        #Start UIRecognize process
        ./UIRecognize >/dev/null 2>&1 &
        sleep 1

        exit 0
    elif [ $1 = UI ]; then
        pkill -SIGUSR1 -f UIRecognize
        sleep 4
        # Clean SHM resource
        ipcs | awk '{if($6==0) printf "ipcrm shm %d\n",$2}'| sh

        #Start UIRecognize process
        ./UIRecognize >/dev/null 2>&1 &
        sleep 1

        exit 0
    fi
else
    pkill -SIGINT -f agentai.py
    # pkill -SIGUSR1 -f GameRegMain.py
    pkill -SIGUSR1 -f GameReg
    sleep 4
    # Clean SHM resource
    ipcs | awk '{if($6==0) printf "ipcrm shm %d\n",$2}'| sh

    #Start Agent process
    python3 agentai.py >/dev/null 2>&1 &
    sleep 10

    #Start GameRecognize process
    # python3 GameRegMain.py >/dev/null 2>&1 &
    ./GameReg >/dev/null 2>&1 &
    sleep 1

    exit 0
fi

exit 0
