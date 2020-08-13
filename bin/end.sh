#!/bin/sh

# Send SIGUSR1 to each process to call exit
pkill -SIGUSR1 -f manage_center.py
pkill -SIGINT -f agentai.py
# pkill -SIGUSR1 -f GameRegMain.py
pkill -SIGUSR1 -f GameReg
pkill -SIGUSR1 -f UIRecognize
pkill -SIGUSR1 -f io_service.py

sleep 4

# Clean SHM resource
ipcs | awk '{if($6==0) printf "ipcrm shm %d\n",$2}'| sh
