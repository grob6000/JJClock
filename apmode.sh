#!/bin/sh
wpa_cli disable_network 0
sudo ip link set dev wlan0 down
sudo ip addr add 192.168.99.1/25 dev wlan0
sudo systemctl restart dnsmasq.service
sudo systemctl restart hostapd.service