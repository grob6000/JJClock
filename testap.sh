#!/bin/sh
echo AP MODE
bash ./apmode.sh
sleep 1
ifconfig wlan0
echo SLEEP
sleep 30
echo CLIENT MODE
bash ./clientmode.sh
sleep 1
ifconfig wlan0
echo FINISHED