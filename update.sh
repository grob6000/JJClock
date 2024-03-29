#!/bin/sh
# arguments: scriptpath githubuser githubtoken path

# allow a second for python to quit
sleep 1

# change to script directory
cd $1

# ensure git credentials are there
git config --global user.name "$2"
git config --global user.password "$3"

# stop service
#sudo systemctl stop jjclock.service

# use git to update
git fetch --all
git checkout $4

# restart service
sudo systemctl restart jjclock.service