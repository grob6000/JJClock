#!/bin/sh
# replaces jjclock.service with new version
sudo cp ./jjclock.service /etc/systemd/system/
sudo chmod 644 /etc/systemd/system/jjclock.service
sudo systemctl daemon-reload