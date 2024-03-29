import json
import os
from pathlib import Path
from threading import Lock, Event
import copy
from pytz import all_timezones
import wifimanager

import jjcommon
import jjlogger
logger = jjlogger.getLogger(__name__)

class Setting():
  def __init__(self, name="", value=None, default=None, validation=None, validationlist=[]):
    self.name = str(name) # name of the setting
    self._value = value # value of the setting
    self.validation = validation # for a web interface; "string", "password", "int", "list" - otherwise will allow anything
    self.validationlist = validationlist # list of allowed objects as values (==)
    self.default = default
  def asDict(self):
    return {"name":str(self.name), "value":self.getValue(), "default":self.default, "validation":self.validation, "validationlist":self.validationlist}
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
        logger.warning(str(value) + " is not a nice integer, did not update value")
    elif self.validation == "list":
      if value in self.validationlist:
        self._value = value
      else:
        logger.warning("attempted to set " + self.name + " to unlisted value " + str(value))
  def getValue(self):
    return self._value
  def makeDefault(self):
    self.setValue(self.default)

_settingspath = os.path.join(os.path.expanduser("~"),".config","jjclock.json")
_settings = {}
_settingsfilelock = Lock()
_settingslock = Lock()
_settingsdefaults =  {
                          "mode":Setting(name="Mode",value="clock_surprise",default="clock_surprise",validation="list",validationlist=[]),
                          "apssid":Setting(name="AP SSID", value=jjcommon.ap_ssid, default=jjcommon.ap_ssid, validation="string"),
                          "appass":Setting(name="AP Password",value=jjcommon.ap_pass,default=jjcommon.ap_pass,validation="password"),
                          "gpson":Setting(name="Enable GPS",value=True,default=True,validation="bool"),
                          "autotz":Setting(name="Auto Timezone",value=True,default=True,validation="bool"),
                          "manualtz":Setting(name="Manual Timezone",value="UTC",default="UTC",validation="list",validationlist=all_timezones),
                          "githubuser":Setting(name="Github Username", value=jjcommon.githubuser, default=jjcommon.githubuser, validation="string"),
                          "githubtoken":Setting(name="Github Access Token", value=jjcommon.githubtoken, default=jjcommon.githubtoken, validation="password"),
                          "githubrepo":Setting(name="Github Repository", value=jjcommon.githubrepo, default=jjcommon.githubrepo, validation="string"),
                          "owmkey":Setting(name="Open Weather Maps Key", value=jjcommon.owm_key, default=jjcommon.owm_key, validation="password"),
                          "loglevel":Setting(name="Log Level", value="INFO", default="INFO", validation="list", validationlist=list(jjlogger.levels.keys())),
                          "netiface":Setting(name="Network Interface", value="wlan0", default="wlan0", validation="list", validationlist=wifimanager.getWifiInterfaces()),
                          "hostname":Setting(name="Hostname", value="jjclock", default="jjclock", validation="string"),
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
    logger.debug("no event specified - not registering")
    return None
  if not settinglist:
    with _settingslock:
      settinglist = _settings.keys()
  with _registrylock:
    for s in settinglist:
      if s in _registry:
        _registry[s].append(event)
      else:
        logger.debug("no such setting, will not register: " + str(s))
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
    logger.debug("settings change has triggered event: " + str(ev))
    ev.set()

def loadSettings():
  global _settings, _settingspath, _settingslock
  # load from file
  sdict = {}
  if os.path.isfile(_settingspath):
    with _settingsfilelock:
      with open(_settingspath) as f:
        sdict = json.load(f)
        logger.debug("settings file found, contains: " + str(sdict))

  with _settingslock:
    # populate defaults
    addedsomething = False
    for k,v in _settingsdefaults.items():
      if not k in _settings.keys():
        _settings[k] = copy.deepcopy(v)
        logger.debug("adding default setting " + k + " = " + str(_settings[k].getValue()))
      addedsomething = True
    # update values based on file
    for k, v in sdict.items():
      if k in _settings.keys():
        _settings[k].setValue(v) # include validation
        logger.debug("update value of setting " + k + " = " + str(_settings[k].getValue()))
      else:
        _settings[k] = Setting(name=k,value=v) # create new setting object
        logger.debug("generated orphan setting " + k + " = " + str(_settings[k].getValue()))
  fixRegistry() # make sure all settings are in here
  # re-save if any defaults were added
  if addedsomething:
    saveSettings()

def saveSettings():
  # save dict to file
  global _settingspath, _settingsfilelock
  sdir = Path(_settingspath).parent
  if not os.path.isdir(sdir):
    os.makedirs(sdir)
    logger.debug("making settings dir " + str(sdir))
  with open(_settingspath, 'w') as f:
    with _settingsfilelock:
      global _settings
      sdict={}
      for k,v in _settings.items():
        sdict[k] = v.getValue() # only saving key and value - the rest is internal
      logger.debug("settings dict to be saved: " + str(sdict))
      json.dump(sdict, f)
  logger.debug("settings saved")

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