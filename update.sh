#!/bin/sh

# get flags
while getopts u:p: flag
do
    case "${flag}" in
        u) githubuser=${OPTARG};;
        p) githubpass=${OPTARG};;
    esac
done

set -x # print stuff

# this should work from outside the install directory!
cd /home/pi/JJClock

# stop service
sudo systemctl stop jjclock.service

# ensure git credentials are there (so bad!)
git config --global user.name "${GITHUBUSER}"
git config --global user.password "${GITHUBPASS}"

# use git to update
git fetch --all
tag=$(git describe --tags `git rev-list --tags --max-count=1`)
git checkout $tag
git pull origin HEAD

# place any new dependencies here

sudo systemctl start jjclock.service