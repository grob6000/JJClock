#!/bin/sh
set -x
sudo systemctl stop hostapd.service
#sudo systemctl disable hostapd.service
sudo systemctl stop dnsmasq.service
#sudo systemctl disable dnsmasq.service
sudo ip link set dev wlan0 down
sudo ip addr flush dev wlan0
#wpa_cli enable -i wlan0 network 0
wpa_cli -i wlan0 reconfigure
sudo systemctl daemon-reload
sudo systemctl restart dhcpcd.service
#sudo dhclient -r wlan0
sudo dhclient -v wlan0