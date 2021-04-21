#!/bin/sh
sudo systemctl stop hostapd.service 2<&1 | tee clientmodedebug.log
sudo systemctl stop dnsmasq.service 2<&1 | tee -a clientmodedebug.log
#sudo ip link set dev wlan0 down
sudo ip addr flush dev wlan0 2<&1 | tee -a clientmodedebug.log
wpa_cli enable network 0 2<&1 | tee -a clientmodedebug.log
sudo dhclient -r wlan0 -v 2<$1 | tee -a clientmodedebug.log
sudo dhclient wlan0 -v 2<&1 | tee -a clientmodedebug.log