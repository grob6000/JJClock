#!/bin/sh
set -x # print stuff

# this should work from outside the install directory!
cd /home/pi/JJClock

# stop service
sudo systemctl stop jjclock.service

# ensure git credentials are there (so bad!)
git config --global user.name "grob6000"
git config --global user.password "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"

# use git to update
git fetch --all
tag=$(git describe --tags `git rev-list --tags --max-count=1`)
git checkout $tag
git pull -f

# place any new dependencies here

sudo systemctl start jjclock.service