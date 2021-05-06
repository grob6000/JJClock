#!/bin/sh

NOW=$( date '+%F_%H%M%S' )

# install required programs
sudo apt-get -y update
sudo apt-get -y install git python3 python3-pip hostapd dnsmasq libjpeg-dev zlib1g-dev libfreetype6-dev liblcms1-dev libopenjp2-7 libtiff5

# python packages
sudo pip3 upgrade pip
sudo pip3 install pyserial timezonefinder pytz pydbus pygithub gpiozero Pillow

# raspberry pi config
sudo raspi-config nonint do_spi 0 # enable SPI
sudo raspi-config nonint do_hostname "jjclock" # set hostname
sudo raspi-config nonint do_serial 1 # disable serial terminal
sudo timedatectl set-ntp True # enable ntp

# install epd driver
cd ./IT8951
sudo pip3 install -r requirements.txt
sudo pip3 install ./
cd ~/JJClock

mkdir ./oldconfig

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
sudo systemctl enable jjclock.service
sudo systemctl start jjclock.service
