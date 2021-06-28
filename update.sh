#!/bin/sh

set -x # print stuff

# this should work from outside the install directory and regardless of user
cd /home/pi/JJClock

# stop service
sudo systemctl stop jjclock.service

# ensure git credentials are there (so bad!)
git config --global user.name "$1"
git config --global user.password "$2"

# use git to update
git fetch --all
tag=$(git describe --tags `git rev-list --tags --max-count=1`)
git checkout $tag
git pull origin HEAD

# place any new dependencies here

sudo systemctl start jjclock.service