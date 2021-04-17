#!/bin/sh
sudo apt-get install git
cd ~
git clone https://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@github.com/grob6000/JJClock
cd ~/JJClock
sudo cp ./jjclock.service /etc/systemd/system/
sudo chmod 644 /etc/systemd/system/jjclock.servsysice
sudo systemctl daemon-reload
sudo systemctl enable jjclock.service
sudo systemctl start jjclock.service
