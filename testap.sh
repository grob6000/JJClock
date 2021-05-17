#!/bin/sh
echo ** AP MODE **
bash ./apmode.sh
echo ** SLEEP **
sleep 20
echo ** CLIENT MODE **
bash ./clientmode.sh
