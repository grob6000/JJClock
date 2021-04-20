#!/bin/sh

# install required programs
sudo apt-get -y install git
sudo apt-get -y install python3
sudo apt-get -y install pip3
sudo apt-get -y install isc-dhcp-server

# python packages
pip3 install pygame
pip3 install gpiozero
pip3 install pillow

# set up dhcp
# set up ap

# download/update
cd ~
git clone https://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@github.com/grob6000/JJClock
cd ~/JJClock
git checkout main
git pull --force

# set up script as service, run on boot
sudo cp ./jjclock.service /etc/systemd/system/
sudo chmod 644 /etc/systemd/system/jjclock.service
sudo systemctl daemon-reload
#sudo systemctl enable jjclock.service
#sudo systemctl start jjclock.service
sudo systemctl disable jjclock.service
