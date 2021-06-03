import json
import os
import logging
from pathlib import Path
from threading import Lock

_settingspath = "/etc/jjclock/settings.json"
_settingsdict = {}
_settingsfilelock = Lock()
_settingsdictlock = Lock()

def loadSettings():
  global _settingsdict
  if os.path.isfile(_settingspath):
    s = {}
    with _settingsfilelock:
      with open(_settingspath) as f:
        s = json.load(f)
    with _settingsdictlock:
      _settingsdict = s
    logging.debug("settings loaded from file")
  else:
    # generate and save default settings
    logging.debug("settings file not found, generating default")
    with _settingsdictlock:
      _settingsdict = {"mode":"clock_digital"}
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

def setSetting(name, value):
    name = str(name)
    if not _settingsdict[name] == value:
      with _settingsdictlock:
        _settingsdict[name] = value
      saveSettings()