import json
import os
import logging
from pathlib import Path
from threading import Lock, Event
import copy
import jjcommon
import copy
from pytz import all_timezones

logging.debug("importing settings.py")

class Setting():
  def __init__(self, name="", value=None, validation=None, validationlist=[]):
    self.name = str(name) # name of the setting
    self._value = value # value of the setting
    self.validation = validation # for a web interface; "string", "password", "int", "list" - otherwise will allow anything
    self.validationlist = validationlist # list of allowed objects as values (==)
  def asDict(self):
    return {"name":str(self.name), "value":self.getValue(), "validation":self.validation, "validationlist":self.validationlist}
  def setValue(self, value):
    if self.validation == "string" or self.validation == "password":
      self._value = str(value)
    elif self.validation == "bool":
      if isinstance(value, str):
        self._value = bool(value.lower()=="true")
      else:
        self._value = bool(value)
    elif self.validation == "int":
      try:
        self._value = int(value)
      except:
        logging.warning(str(value) + " is not a nice integer, did not update value")
    elif self.validation == "list":
      if value in self.validationlist:
        self._value = value
      else:
        logging.warning("attempted to set " + self.name + " to unlisted value " + str(value))
  def getValue(self):
    return self._value

_settingspath = "~/.jjclocksettings/settings.json"
_settings = {}
_settingsfilelock = Lock()
_settingslock = Lock()
_settingsdefaults =  {
                          "mode":Setting(name="Mode",value="clock_digital",validation="list",validationlist=[]),
                          "apssid":Setting(name="AP SSID", value=jjcommon.ap_ssid, validation="string"),
                          "appass":Setting(name="AP Password",value=jjcommon.ap_pass,validation="password"),
                          "gpson":Setting(name="Enable GPS",value=True,validation="bool"),
                          "autotz":Setting(name="Auto Timezone",value=True,validation="bool"),
                          "manualtz":Setting(name="Timezone (Manual)",value="UTC",validation="list",validationlist=all_timezones),
                     }  
_registry = {}
_registrylock = Lock()

def fixRegistry():
  global _registry
  global _registrylock
  global _settings
  global _settingslock
  with _settingslock, _registrylock:
    for k in _settings.keys():
      if not k in _registry:
        _registry[k] = []

def register(settinglist=None, event=Event()):
  global _registry
  global _registrylock
  global _settings
  global _settingslock
  if not event:
    logging.debug("no event specified - not registering")
    return None
  if not settinglist:
    with _settingslock:
      settinglist = _settings.keys()
  with _registrylock:
    for s in settinglist:
      if s in _registry:
        _registry[s].append(event)
      else:
        logging.debug("no such setting, will not register: " + str(s))
        event = None
  return event

def unregister(event):
  global _registry
  global _registrylock
  with _registrylock:
    for v in _registry.values():
      if event in v:
        v.remove(event)

def callUpdate(settinglist=[]):
  events = set()
  with _registrylock:
    for k in settinglist:
      if k in _registry:
        events = events.union(set(_registry[k]))
  for ev in events:
    logging.debug("settings change has triggered event: " + str(ev))
    ev.set()

def loadSettings():
  global _settings, _settingspath, _settingslock
  # load from file
  sdict = {}
  if os.path.isfile(_settingspath):
    with _settingsfilelock:
      with open(_settingspath) as f:
        sdict = json.load(f)

  with _settingslock:
    # populate defaults
    addedsomething = False
    for k,v in _settingsdefaults.items():
      if not k in _settings.keys():
        _settings[k] = copy.deepcopy(v)
      addedsomething = True
    # update values based on file
    for k, v in sdict.items():
      if k in _settings.keys():
        _settings[k].setValue(v) # include validation
      else:
        _settings[k] = Setting(name=k,value=v) # create new setting object
  fixRegistry() # make sure all settings are in here
  logging.debug("settings loaded from file")
  # re-save if any defaults were added
  if addedsomething:
    saveSettings()

def saveSettings():
  # save dict to file
  global _settingspath, _settingsfilelock
  sdir = Path(_settingspath).parent
  if not os.path.isdir(sdir):
    os.makedirs(sdir)
    logging.debug("making settings dir " + str(sdir))
  with open(_settingspath, 'w') as f:
    with _settingsfilelock:
      global _settings
      sdict={}
      for k,v in _settings.items():
        sdict[k] = v.getValue() # only saving key and value - the rest is internal
      logging.debug("settings dict to be saved: " + str(sdict))
      json.dump(sdict, f)
  logging.debug("settings saved")

def getSettingValue(name):
  with _settingslock:
    v = copy.deepcopy(_settings[name].getValue())
  return v

def getSetting(name):
  with _settingslock:
    s = copy.deepcopy(_settings[name])
  return s

def getSettings(names=None):
  if names:
    s = {}
    with _settingslock:
      for n in names:
        n = str(n)
        s[n] = copy.deepcopy(_settings[n])
    return s
  else:
    return getAllSettings()

def getAllSettings():
  d = {}
  with _settingslock:
    d = copy.deepcopy(_settings) # make a copy of the dict (deep, in case objects are referenced)
  return d

def setSetting(name, value, quiet=False):
  setSettings({name:value}, quiet)

def setSettings(dict, quiet=False):
  global _settings, _settingslock
  modified = False
  with _settingslock:
    for k, v in dict.items():
      name = str(k)
      if not _settings[name].getValue() == v:
        _settings[name].setValue(v)
        modified = True
  if modified:
    saveSettings()
    if not quiet: # suppress if quiet
      callUpdate(dict.keys())