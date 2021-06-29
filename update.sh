#!/bin/sh
# arguments: scriptpath githubuser githubtoken path

cd $1
# ensure git credentials are there
git config --global user.name "$2"
git config --global user.password "$3"

# use git to update
git fetch --all
git checkout $4
git pull origin HEAD