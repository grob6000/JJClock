#!/bin/sh
# this should work from outside the install directory!
cd ~/JJClock

# stop service
sudo systemctl stop jjclock.service

# use git to update
git fetch --all
tag=$(git describe --tags `git rev-list --tags --max-count=1`)
git checkout $tag
git pull -f

# place any new dependencies here

sudo systemctl start jjclock.service