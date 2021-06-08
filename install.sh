#!/bin/sh

NOW=$( date '+%F_%H%M%S' )

# install required programs
sudo apt-get -y update
sudo apt-get -y install git python3 python3-pip hostapd dnsmasq libjpeg-dev zlib1g-dev libfreetype6-dev liblcms1-dev libopenjp2-7 libtiff5 libsecret-1-0 libsecret-1-dev libatlas-base-dev authbind

# save git credentials
#sudo make --directory=/usr/share/doc/git/contrib/credential/libsecret
#git config --global credential.helper /usr/share/doc/git/contrib/credential/libsecret/git-credential-libsecret
git config --global credential.helper store
git config --global user.name "grob6000"
git config --global user.password "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"

# python packages
sudo pip3 install numpy pyserial timezonefinder pytz pydbus pygithub gpiozero Pillow flask pyowm pygame

# raspberry pi config
sudo raspi-config nonint do_spi 0 # enable SPI
sudo raspi-config nonint do_hostname "jjclock" # set hostname
sudo raspi-config nonint do_serial 2 # disable serial terminal but enable /dev/serial0
sudo timedatectl set-ntp True # enable ntp

# disable bt
sudo systemctl disable bluetooth.service
if sudo grep -Fxq "dtoverlay=pi3-disable-bt" /boot/config.txt
then
    #skip
    echo skipping disable bt
else
    #append
    echo "dtoverlay=pi3-disable-bt" >> /boot/config.txt
fi

# install epd driver
cd ./IT8951
sudo pip3 install -r requirements.txt
sudo pip3 install ./
cd ~/JJClock

mkdir ./oldconfig

# set up hostapd
echo ***** SETTING UP HOSTAPD *****
cp /etc/hostapd/hostapd.conf ./oldconfig/hostapd_$NOW.conf
sudo rm /etc/hostapd/hostapd.conf
sudo cp ./hostapd.conf /etc/hostapd/hostapd.conf
sudo sed -i '/DAEMON_CONF=/c\DAEMON_CONF=/etc/hostapd/hostapd.conf' /etc/init.d/hostapd
sudo systemctl disable hostapd.service # disabled by default

# set up dnsmasq
echo ***** SETTING UP DNSMASQ *****
cp /etc/dnsmasq.conf ./oldconfig/dnsmasq_$NOW.conf
sudo rm /etc/dnsmasq.conf
sudo cp ./dnsmasq.conf /etc/dnsmasq.conf
sudo systemctl disable dnsmasq.service # disabled by default

# set up access to port 80
sudo touch /etc/authbind/byport/80
sudo chmod 777 /etc/authbind/byport/80

# set up script as service, run on boot
echo ***** SETTING UP BOOT SERVICE *****
sudo cp ./jjclock.service /etc/systemd/system/
sudo chmod 644 /etc/systemd/system/jjclock.service
sudo systemctl daemon-reload
sudo systemctl enable jjclock.service
sudo systemctl restart jjclock.service
