#!/bin/sh
echo AP MODE > ./testap.log
bash ./apmode.sh |& tee -a ./testap.log
sleep 1
ifconfig wlan0 |& tee -a ./testap.log
echo SLEEP >> ./testap.log
sleep 30
echo CLIENT MODE >> ./testap.log
bash ./clientmode.sh |& tee -a ./testap.log
sleep 1
ifconfig wlan0 |& tee -a ./testap.log
echo FINISHED >> ./testap.log