#!/bin/sh
sudo systemctl stop hostapd.service 2<&1 | tee -a debug.log
sudo systemctl stop dnsmasq.service 2<&1 | tee -a debug.log
#sudo ip link set dev wlan0 down
sudo ip addr flush dev wlan0 2<&1 | tee -a debug.log
wpa_cli enable network 0 2<&1 | tee -a debug.log
sudo dhclient -v 2<&1 | tee -a debug.log