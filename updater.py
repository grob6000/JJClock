import subprocess
import logging
import github
import datetime
import sys
import os
import pathlib
import time
from threading import Lock

import settings
import jjcommon

currentversion = None
latestversion = None
lastchecked = None

# get the current tag of the repo
def getCurrentVersion():
  global currentversion
  try:
    tag = subprocess.run(["git", "describe", "--tags", "--abbrev=0"], text=True, capture_output=True).stdout.strip()
  except subprocess.CalledProcessError:
    logging.warning("could not determine current repository version")
    tag = None
  logging.debug("determined current version: " + str(tag))
  currentversion = tag
  return tag

def getTimeSinceLastChecked():
  global lastchecked
  if lastchecked:
    return datetime.datetime.utcnow() - lastchecked
  else:
    return datetime.timedelta.max # first time, should encourage checking

# get latest version from github API
def getLatestVersion():
  global latestversion
  global lastchecked
  try:
    g = github.Github(settings.getSettingValue("githubtoken"))
    repo = g.get_repo(settings.getSettingValue("githubrepo"))
    rels = repo.get_releases()
  except:
    logging.warning("could not connect to github - abandoning update check")
    latestversion = None
  latestpub = datetime.datetime.min
  latestrel = None
  tag = None
  for r in rels:
    if r.published_at > latestpub:
      latestpub = r.published_at
      latestrel = r
  if latestrel:
    tag = latestrel.tag_name
    logging.info("retrieved latest github repo version: " + tag)
  latestversion = tag
  lastchecked = datetime.datetime.utcnow()
  return tag

# update to specified version - note this does not stop the program, this needs to be done separately
def doUpdate(tag=None):
  global latestversion
  global currentversion
  logging.debug(tag)
  if not tag:
    logging.debug("using latest version")
    tag = latestversion
  if not tag:
    logging.warning("updater doesn't know the target version. will not update.")
  elif tag == currentversion:
    logging.warning("already this version. will not update.")
  else:
    logging.info("updating now...")
    if "linux" in sys.platform:
      # make sure temp dir exists
      tempfile = pathlib.Path(jjcommon.updatetempfile)
      logging.debug("tempfile = " + tempfile.absolute())
      subprocess.run(["mkdir", "-p", tempfile.parent.absolute()])
      # copy update script to temp location
      try:
        subprocess.run(["cp", os.path.join(jjcommon.scriptpath, "update.sh"), tempfile.absolute()], check=True)
      except subprocess.CalledProcessError:
        logging.error("could not move update script")
      try:
        subprocess.Popen(["bash", tempfile.absolute(), jjcommon.scriptpath, settings.getSettingValue("githubuser"), settings.getSettingValue("githubtoken")], tag)
      except subprocess.CalledProcessError:
        logging.error("problem starting update script")
    else:
      logging.warning("not able to update on this system")
  # check and return the current version after update
  return getCurrentVersion()

# asks system to restart the service, and quits
def restartService():
  if "linux" in sys.platform:
    logging.info("requesting service restart...")
    subprocess.Popen(["sudo", "systemctl", "restart", "jjclock.service"], start_new_session=True)
  else:
    logging.warning("no service to stop on this platform")
  for i in range(10,1,-1):
    logging.debug("quit in " + str(i))
    time.sleep(1)
  logging.debug("service was not terminated, quitting internally")
  quit()