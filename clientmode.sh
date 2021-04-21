#!/bin/sh
sudo systemctl stop hostapd.service
sudo systemctl stop dnsmasq.service
wpa_cli enable network 0
