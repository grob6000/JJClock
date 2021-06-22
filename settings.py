import json
import os
import logging
from pathlib import Path
from threading import Lock
import copy
import jjcommon
import copy

_settingspath = "~/.jjclocksettings/settings.json"
_settingsdict = {}
_settingsfilelock = Lock()
_settingsdictlock = Lock()
_settingsdictdefault = {"mode":"clock_digital", "apssid":jjcommon.ap_ssid, "appass":jjcommon.ap_pass}

def loadSettings():
  global _settingsdict
  if os.path.isfile(_settingspath):
    s = {}
    with _settingsfilelock:
      with open(_settingspath) as f:
        s = json.load(f)
    # populate defaults (if not present)
    addedsomething = False
    for ds in _settingsdictdefault:
      if not ds in s:
        s[ds] = _settingsdictdefault[ds]
        addedsomething = True
    # update the settings dict
    with _settingsdictlock:
      _settingsdict = s
    logging.debug("settings loaded from file")
    # re-save if any defaults were added
    if addedsomething:
      saveSettings()
  else:
    # generate and save default settings
    logging.debug("settings file not found, generating default")
    with _settingsdictlock:
      _settingsdict = copy.deepcopy(_settingsdictdefault)
    saveSettings()

def saveSettings():
  # save dict to file
  sdir = Path(_settingspath).parent
  with _settingsfilelock:
    if not os.path.isdir(sdir):
      os.makedirs(sdir)
      logging.debug("making settings dir " + str(sdir))
      with open(_settingspath, 'w') as f:
        json.dump(_settingsdict, f)
  logging.debug("settings saved")

def getSetting(name):
  v = None
  with _settingsdictlock:
    if name in _settingsdict:
      v = _settingsdict[name]
  return v

def getAllSettings():
  d = {}
  with _settingsdictlock:
    d = copy.deepcopy(_settingsdict) # make a copy of the dict (deep, in case objects are referenced)
  return d

def setSetting(name, value):
    name = str(name)
    if not _settingsdict[name] == value:
      with _settingsdictlock:
        _settingsdict[name] = value
      saveSettings()