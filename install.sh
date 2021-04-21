#!/bin/sh

NOW=$( date '+%F_%H%M%S' )

# install required programs
sudo apt-get -y install git
sudo apt-get -y install python3
sudo apt-get -y install python3-pip
sudo apt-get -y install python3-pygame
sudo apt-get -y install hostapd
sudo apt-get -y install dnsmasq
#sudo apt-get -y install netfilter-persistent iptables-persistent

# python packages
#sudo pip3 install pygame
sudo pip3 install gpiozero
sudo pip3 install pillow

# raspberry pi config
sudo raspi-config nonint do_spi 0 # enable SPI
sudo raspi-config nonint do_hostname "jjclock" # set hostname
sudo raspi-config nonint do_serial 1 # disable serial terminal

# download/update
cd ~
git clone https://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@github.com/grob6000/JJClock
cd ~/JJClock
git checkout main
git pull --force

mkdir ./oldconfig

# install epd driver
cd ./IT8951
pip3 install -r requirements.txt
pip3 install ./

# set up hostapd
cp /etc/hostapd/hostapd.conf ./oldconfig/hostapd_$NOW.conf
sudo rm /etc/hostapd/hostapd.conf
sudo cp ./hostapd.conf /etc/hostapd/hostapd.conf
sudo sed -i '/DAEMON_CONF=/c\DAEMON_CONF=/etc/hostapd/hostapd.conf' /etc/init.d/hostapd
sudo systemctl disable hostapd.service # disabled by default

# set up dnsmasq
cp /etc/dnsmasq.conf ./oldconfig/dnsmasq_$NOW.conf
sudo rm /etc/dnsmasq.conf
sudo cp ./dnsmasq.conf /etc/dnsmasq.conf
sudo systemctl disable dnsmasq.service # disabled by default

# set up script as service, run on boot
sudo cp ./jjclock.service /etc/systemd/system/
sudo chmod 644 /etc/systemd/system/jjclock.service
sudo systemctl daemon-reload
#sudo systemctl enable jjclock.service
#sudo systemctl start jjclock.service
sudo systemctl disable jjclock.service
