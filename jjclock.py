# JJ Clock
# Lots of love from George 2021

## INCLUDES (required for package checking)
import subprocess
import sys
import pkg_resources

# set up logger
import logging
import jjlogger
logger = jjlogger.getLogger(None)

## INSTALL ANY MISSING PACKAGES ##
required = {"numpy", "pyserial", "timezonefinder", "pytz", "pydbus", "pygithub", "gpiozero", "pillow", "flask", "pyowm", "pygame", "psutil", "waitress", "sdnotify"}
installed = {pkg.key for pkg in pkg_resources.working_set}
missing = required - installed
if missing:
    # implement pip as a subprocess:
    logger.info("installing packages: " + str(missing))
    subprocess.check_call([sys.executable, '-m', 'pip', 'install',*missing])

## INCLUDES (remaining) ##
import datetime
import os
import time
from threading import Event
import pytz
import timezonefinder
#from PIL import Image, ImageDraw, ImageFont
from github import Github
import psutil
from time import sleep

if "linux" in sys.platform:
  from gpiozero import Device, Button
  #from gpiozero.pins.mock import MockFactory
  from IT8951.display import AutoEPDDisplay
  from IT8951 import constants
  import pydbus
  import subprocess
  import sdnotify

## LOCAL MODULES ##

import jjrenderer
import gpshandler
import wifimanager
import webadmin
import settings
import display
import updater

## CONSTANTS ##

from jjcommon import *

# collect all availabel modes
modelist = ["splash","menu","config"]
# load renderers, generate menu
for k in jjrenderer.renderers.keys():
    if not k in modelist:
      modelist.append(k)
logging.debug("modelist = " + str(modelist))

# populate menu
menu = [jjrenderer.renderers["config"],]
for k, r in jjrenderer.renderers.items():
  if r.isclock and not k == "clock_birthday": # hide birthday mode!
    menu.append(r)
logging.debug("menu = " + str(menu))

# instantiate a renderer (will reuse this; only instantiate a new one on mode changes)
currentrenderer = jjrenderer.Renderer()

menutimeout = 10 # seconds

## GLOBALS ##
pleasequit = False
currentmode = -1 # initialise as an invalid mode; any mode change will trigger change
displaymanger = None # set up
wa = None
gpsh = None
menuindexselected = 0

# timing
t_lastbuttonpress = 0
menutimeout_armed = False

# systemd watchdog
wdev = os.getenv('WATCHDOG_USEC')
watchdoginterval = 30 # seconds; default
if wdev:
  watchdocinterval = int(wdev)/2000000 # seconds

tz = pytz.UTC
pytz.all_timezones
tf = timezonefinder.TimezoneFinder()
currentdt = datetime.datetime.now().astimezone(tz)

# display update hash for polling
displayhash = 0

## FUNCTIONS ##
  
def onButton():
  global menuindexselected
  global menu
  global menutimeout_armed
  global t_lastbuttonpress
  global currentmode
  global displaymanager
  global currentrenderer
  t_lastbuttonpress = time.monotonic()
  menutimeout_armed = True
  logger.debug("button pressed, t={0}".format(t_lastbuttonpress))
  if currentmode == "menu":
    if not currentrenderer.name == "menu":
      currentrenderer = jjrenderer.renderers["menu"]()
    menuindexselected = (menuindexselected+1)%len(menu) 
    logger.debug("selected item = " + str(menuindexselected))
    displaymanager.doRender(currentrenderer, menu=menu, selecteditem=menuindexselected)
  else:
    changeMode("menu")

def onMenuTimeout():
  global menuindexselected
  newmode = menu[menuindexselected].name
  logger.info("Menu closed")
  changeMode(newmode)

def formatIP(ip):
  return "{ip[0]}.{ip[1]}.{ip[2]}.{ip[3]}".format(ip=ip)

def changeMode(mode):
  global modelist
  global currentmode
  global menuindexselected
  global menu
  global currentrenderer
  r = None
  kwargs = {"mode":mode}
  if not mode in modelist:
    logger.warning("Unrecognized mode requested: " + mode)
  elif mode == currentmode:
    logger.debug("Already in mode, no change required: " + mode)
  else:
    logger.info("Changing mode to: " + mode)
    currentmode = mode
    settings.setSetting("mode", mode, quiet=True) # update quietly; don't trigger registered events (they might have come here!)
    r = None
    if mode == "config":
      # set wifi to AP mode
      wifimanager.setWifiMode("ap")
      if gpsh:
        gpsstat = gpsh.getStatus()
      else:
        gpsstat = None
      kwargs["ssid"] = settings.getSettingValue("apssid")
      kwargs["password"] = settings.getSettingValue("appass")
      kwargs["ip"] = ap_addr
      kwargs["port"] = webadmin_port
      kwargs["gpsstat"] = gpsstat
    elif mode == "menu":
      # do not change wifimode for menu
      kwargs["selecteditem"] = menuindexselected
      kwargs["menu"] = menu
    else:
      wifimanager.setWifiMode("client") # all other modes should be in client state (if no wifi configured, will be disconnected...)
    if mode in modelist and not r:
      currentrenderer = jjrenderer.renderers[mode]()
      kwargs["timestamp"] = currentdt
    else:
      currentrenderer = jjrenderer.Renderer()
    displaymanager.doRender(currentrenderer,**kwargs)
  
def updateTime(dt, force=False):
  if force:
    logger.debug("forcing display update!")
  global currentdt
  #global renderers
  global currentmode
  global currentrenderer
  if force or not currentdt.minute == dt.minute:
    #print(dt)
    if ("clock" in currentmode):
      # BIRTHDAY EASTER EGG HAHA CAN'T FIX THIS
      if dt.day==birthday["day"] and dt.month==birthday["month"] and not currentmode=="clock_birthday":
        changeMode("clock_birthday")
      else:
        ui = currentrenderer.updateinterval
        if force or ((dt.minute + dt.hour*60) % ui == 0):
          displaymanager.doRender(currentrenderer, timestamp=dt, mode=currentmode)
  currentdt = dt

def setSystemTz(tzname):
    if "linux" in sys.platform:
        r = subprocess.run(["sudo","timedatectl","set-timezone",tzname])
        if r.returncode == 0:
          logger.info("System timezone changed to: " + getSystemTz())
        else:
          logger.info("Error while attempting to update system timezone to: " + tzname)
    else:
      logger.warning("non-linux os: cannot update system timezone.")

def getSystemTz():
  if "linux" in sys.platform:
    return pydbus.SystemBus().get(".timedate1").Timezone
  else:
    logger.warning("cannot access system timezone. returning dummy.")
    return "UTC"

def checkForUpdate():
  # this does a version check before proceeding
  updater.getCurrentVersion()
  updater.getLatestVersion()
  if updater.latestversion and updater.currentversion:
    if updater.latestversion == updater.currentversion:
      logger.info("Currently latest version: " + updater.latestversion + ". No update required.")
    else:
      doUpdate()
  else:
    logger.warning("Will not update, unknown version information.")

def doUpdate():
  global epddisplay, wa, displaymanager, gpsh, pygamedisplay
  if "linux" in sys.platform:
    logger.debug("current version: " + updater.currentversion + ", available: " + updater.latestversion)
    displaymanager.doRender(jjrenderer.renderers["updating"](), version="{0} --> {1}".format(updater.currentversion, updater.latestversion))
    logger.debug("killing things...")
    if wa:
      wa.stop() # stop web admin
    if gpsh:
      gpsh.disconnect() # disconnect gps from serial (if this is still alive when next version starts, will fail)
    if pygamedisplay:
      pygamedisplay.stop() # kill pygame display
    if epddisplay:
      epddisplay.disconnect() # disconnect epddisplay from SPI (if this is still alive when next version starts, will fail)
    updater.doUpdate(updater.latestversion) # will quit
  else:
    logger.warning("will not update on windows")

modifiers = ['', 'k', 'M', 'G', 'T']
def formatmemory(m):
  i = 0
  while (m>1024):
    m = m / 1024
    i = i + 1
  return "{0:.4g} {1}B".format(m, modifiers[i])

# setting change events
event_changemode = Event()
event_apupdate = Event()
event_manualtzupdate = Event()
event_gitcredentials = Event()

## SCRIPT ##
if __name__ == "__main__":

  logger.info("JJClock starts!")

  sdn = None
  if "linux" in sys.platform:
    sdn = sdnotify.SystemdNotifier()
  
  # load settings
  settings._settingsdefaults["mode"].validationlist = modelist # use mode list to select from
  settings.loadSettings()

  # init gpio
  logger.info("Initializing GPIO...")
  if "linux" in sys.platform:
    #Device.pin_factory = MockFactory()
    userbutton = Button(buttongpio, bounce_time=debounce/1000.0)
    userbutton.when_pressed = onButton
  else:
    logger.warning("GPIO not available on this platform, no button enabled.")
  
  # init display(s)
  logger.info("Initializing Display...")
  displaymanager = display.DisplayManager(size=(cropbox[2]-cropbox[0], cropbox[3]-cropbox[1])) # display manager primary surface will be the size of the target surface of the display
  pygamedisplay = None
  epddisplay = None
  if "linux" in sys.platform:
    epddisplay = display.EPDDisplay(vcom=display_vcom) # init epd display
    epddisplay.cropbox = cropbox # set cropbox to match frame
    displaymanager.displaylist.append(epddisplay) # register display
  else:
    logger.warning("No display on this platform. Using pygame.")
    pygamedisplay = display.PygameDisplay(start=False) # don't start just yet...
    pygamedisplay.resize = True
    displaymanager.displaylist.append(pygamedisplay)
    pygamedisplay.restart() # start!
  
  # wifi manager init
  logger.info("Setting up Wifi Configuration...")
  wifimanager.readHostapd() # read the official hostapd from system
  wifimanager.updateHostapd(settings.getSettingValue("apssid"), settings.getSettingValue("appass")) # update hostapd with settings

  # now screen is running, check for update
  logger.info("Checking for Update...")
  updater.setGitCredentials() # do this on boot; and when settings change
  checkForUpdate()
  
  # load timezone
  tz = pytz.timezone(settings.getSettingValue("manualtz"))
  currentdt = datetime.datetime.now().astimezone(tz) # init currentdt using new datetime

  # load last mode
  changeMode(settings.getSettingValue("mode"))
  
  # gps serial
  logger.info("Connecting to GPS...")
  gpsh = gpshandler.GpsHandler() # create and start gps handler
  gpsh.connect()
  
  # start webadmin server
  logger.info("Starting Webserver...")
  wa = webadmin.WebAdmin()
  wa.start()
  displaymanager.displaylist.append(wa.display)
  wa.providemenu(menu)

  # setting change event registration - other threads might change settings, but reaction to changes should always be routed through the main loop
  settings.register(["mode"], event_changemode) # change mode when mode setting is updated from web interface (or elsewhere, unquietly)
  settings.register(["manualtz"], event_manualtzupdate) # update the timezone when manual timezone is changed
  settings.register(["apssid", "appass"], event_apupdate) # register wifimanager to respond to future changes to hostapd settings
  settings.register(["githubuser", "githubtoken"], event_gitcredentials) # update git credentials

  # at this point consider the service ready
  twatchdog = time.monotonic()
  if sdn:
    sdn.notify("READY=1")
    sdn.notify("WATCHDOG=1")


  ## MAIN LOOP ##

  tlastupdate = time.monotonic()
  while not pleasequit:
      
      t = time.monotonic()

      if sdn:
        if (twatchdog - t) > watchdoginterval:
          sdn.notify("WATCHDOG=1")

      if pygamedisplay and pygamedisplay.buttonevent.is_set():
        pygamedisplay.buttonevent.clear()
        onButton()

      if menutimeout_armed:
        tdiff = t - t_lastbuttonpress
        if tdiff > menutimeout:
          menutimeout_armed = False
          onMenuTimeout()
      
      if event_apupdate.is_set():
        event_apupdate.clear()
        # update ap as per settings
        apssid = settings.getSettingValue("apssid")
        appass = settings.getSettingValue("appass")
        wifimanager.updateHostapd(apssid,appass)

      if event_changemode.is_set():
        event_changemode.clear()
        # change mode as per settings
        newmode = settings.getSettingValue("mode")
        changeMode(newmode)
      
      if event_gitcredentials.is_set():
        event_gitcredentials.clear()
        updater.setGitCredentials()

      if wa.updatecheckrequest.is_set():
        wa.updatecheckrequest.clear()
        updater.getLatestVersion()
      
      if wa.updatedorequest.is_set():
        wa.updatedorequest.clear()
        updater.doUpdate() # default tag will be the last checked version

      autotz = settings.getSettingValue("autotz")

      tzchanged = False
      if event_manualtzupdate.is_set():
        event_manualtzupdate.clear()
        manualtz = settings.getSettingValue("manualtz")
        try:
          tztemp = pytz.timezone(manualtz)
        except pytz.UnknownTimeZoneError:
          logger.warning("Bad manual timezone, will not change: " + manualtz)
        else:
          tzchanged = bool(not (tz.zone == tztemp.zone))
          tz = tztemp
          if tzchanged:
            logger.info("Manually set new timezone: " + tz.zone)
      
      if tzchanged and not getSystemTz() == tz.zone:
        setSystemTz(tz.zone)
      
      # if NMEA has been received, update the time
      dt = None
      p = ""
      gpson = settings.getSettingValue("gpson")
      autotz = settings.getSettingValue("autotz")
      if gpson and gpsh.pollUpdated():
        # have some gps data I can use
        stat = gpsh.getStatus()
        if stat["hastime"]:
          if autotz and stat["tz"]:
            dt = gpsh.getDateTime(local=True)
            p = "using gps time + auto tz: "
            # update timezone cached
            if not tz == stat["tz"]:
              logger.info("GPS provides new timezone: " + tz.zone)
              tzchanged = True
              tz = stat["tz"]
              # update timezone setting --> will trigger system tz update next time around
              settings.setSetting("manualtz", tz.zone)
          else:
            dt = gpsh.getDateTime(local=False).astimezone(tz)
            p = "using gps time + manual tz: "
      else:
        
        if ((t - tlastupdate) > 2):
          # it's been more than a couple of seconds (gps should do 1/s) - probably not working, should use system time
          dt = datetime.datetime.now().astimezone(tz)
          p = "using system time + manual tz: "

      if dt:
        logger.debug(p + dt.strftime("%H:%M:%S %z") + " (" + tz.zone + ")")
        tlastupdate = t
        updateTime(dt)
      elif tzchanged:
        # don't have a new time but tzchanged so need to force an update - & use cached time with new timezone
        tlastupdate = t
        updateTime(currentdt.astimezone(tz), True)

      # update check
      secondssinceupdatecheck = updater.getTimeSinceLastChecked().total_seconds()
      if secondssinceupdatecheck > minupdateinterval:
        if (dt and dt.hour == updatehour) or secondssinceupdatecheck > maxupdateinterval:
          checkForUpdate()

      # provide status to webadmin
      memoryusage = formatmemory(psutil.Process().memory_info().vms)
      if gpsh:
        gpsstat = gpsh.getStatus()
      else:
        gpsstat = None
      wa.provideStatus({
        "tz":tz,
        "timestamp":currentdt.astimezone(tz),
        "mode":currentmode, 
        "gps":gpsstat,
        "memory":memoryusage,
        "threadstate":{"gps":(gpsh and gpsh.isrunning()),"web":(wa and wa.isrunning()),"pygame":(pygamedisplay and pygamedisplay.isrunning())},
        "currentversion":updater.currentversion,
        "latestversion":updater.latestversion,
      })
          
      time.sleep(0.1) # limit frequency / provide a thread opportunity
  
  # Close the window and quit.
  logger.info("Exiting")
