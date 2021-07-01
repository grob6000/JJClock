import subprocess
import github
import datetime
import sys
#import os
#import pathlib
#import time
from threading import Lock

import settings
import logpipe
#import jjcommon

import jjlogger
logger = jjlogger.getLogger(__name__)

currentversion = None
latestversion = None
lastchecked = None

# get the current tag of the repo
def getCurrentVersion():
  global currentversion
  try:
    tag = subprocess.run(["git", "describe", "--tags", "--abbrev=0"], text=True, capture_output=True).stdout.strip()
  except subprocess.CalledProcessError:
    logger.warning("Could not determine current github repository version")
    tag = None
  logger.debug("determined current version: " + str(tag))
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
    logger.warning("Could not connect to github - abandoning update check")
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
    logger.info("Latest github repo version: " + tag)
  latestversion = tag
  lastchecked = datetime.datetime.utcnow()
  return tag

# update to specified version - note this does not stop the program, this needs to be done separately
def doUpdate(tag=None):
  global latestversion
  global currentversion
  logger.debug(tag)
  if not tag:
    logger.debug("using latest version")
    tag = latestversion
  if not tag:
    logger.warning("Updater doesn't know the target version. Will not update.")
  #elif tag == currentversion: # temporarily allow forced updating
  #  logger.warning("already this version. will not update.")
  else:
    logger.info("Updating now...")
    if "linux" in sys.platform:
      #updatescript = pathlib.Path(jjcommon.scriptpath).joinpath("update.sh").absolute()
      lp = logpipe.LogPipe(jjlogger.DEBUG, logger)
      try:
        subprocess.run(["git", "config", "--global", "user.name", settings.getSettingValue("githubuser")], check=True, stderr=lp, stdout=lp)
        subprocess.run(["git", "config", "--global", "user.password", settings.getSettingValue("githubpass")], check=True, stderr=lp, stdout=lp)        
        subprocess.run(["git", "fetch", "--all"], check=True, stderr=lp, stdout=lp)
        subprocess.run(["git", "checkout", tag], check=True, stderr=lp, stdout=lp)
        #s = subprocess.Popen(["bash", str(updatescript), jjcommon.scriptpath, settings.getSettingValue("githubuser"), settings.getSettingValue("githubtoken"), tag])
      except subprocess.CalledProcessError:
        logger.error("Problem encountered during update")
      else:
        # rely on update script to restart the service
        logger.info("Update complete, quitting now")
        # quit, citing exit code 0 (success). systemd will restart service
        sys.exit(0)
    else:
      logger.warning("Not able to update on this system")

# asks system to restart the service, and quits
#def restartService():
#  if "linux" in sys.platform:
#    logger.info("Requesting service restart...")
#    subprocess.Popen(["sudo", "systemctl", "restart", "jjclock.service"]) # if this is within the service, the progam should be terminated
#    time.sleep(1)
#    logger.error("Service was not terminated - this process probably not the service. quitting")
#    quit()
#  else:
#    logger.warning("No service to stop on this platform")
