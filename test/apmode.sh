#!/bin/sh
set -x
#wpa_cli -i wlan0 disable_network 0
wpa_cli -i wlan0 disconnect
sudo ip link set dev wlan0 down
sudo ip addr add 192.168.99.1/25 dev wlan0
#sudo systemctl enable dnsmasq.service
sudo systemctl restart dnsmasq.service
#sudo systemctl enable hostapd.service
sudo systemctl restart hostapd.service