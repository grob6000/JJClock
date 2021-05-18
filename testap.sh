#!/bin/sh
echo AP MODE > ./testap.log
bash ./apmode.sh |& tee -a ./testap.log
echo SLEEP >> ./testap.log
sleep 20
echo CLIENT MODE >> ./testap.log
bash ./clientmode.sh |& tee -a ./testap.log
echo FINISHED >> ./testap.log