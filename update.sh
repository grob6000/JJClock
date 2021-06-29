#!/bin/sh

# ensure git credentials are there
git config --global user.name "$1"
git config --global user.password "$2"

# use git to update
git fetch --all
tag=$(git describe --tags `git rev-list --tags --max-count=1`)
git checkout $tag
git pull origin HEAD