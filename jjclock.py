# JJ Clock
# Lots of love from George 2021

## INCLUDES (required for package checking)
import subprocess
import sys
import pkg_resources

# set up logger
import logging
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

## INSTALL ANY MISSING PACKAGES ##
required = {"numpy", "pyserial", "timezonefinder", "pytz", "pydbus", "pygithub", "gpiozero", "pillow", "flask", "pyowm", "pygame", "psutil"}
installed = {pkg.key for pkg in pkg_resources.working_set}
missing = required - installed
if missing:
    # implement pip as a subprocess:
    logging.info("installing packages: " + str(missing))
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

if "linux" in sys.platform:
  from gpiozero import Device, Button
  #from gpiozero.pins.mock import MockFactory
  from IT8951.display import AutoEPDDisplay
  from IT8951 import constants
  import pydbus
  import subprocess

## LOCAL MODULES ##

import jjrenderer
import gpshandler
import wifimanager
import webadmin
import settings
import display

## CONSTANTS ##

from jjcommon import *

modelist = ["splash","menu","config"]
# load renderers, generate menu
for k in jjrenderer.renderers.keys():
    if not k in modelist:
      modelist.append(k)
logging.debug(str(modelist))

# populate menu
menu = [jjrenderer.renderers["config"],]
for k, r in jjrenderer.renderers.items():
  if r.isclock and not k == "clock_birthday": # hide birthday mode!
    menu.append(r)
logging.debug(menu)

# instantiate a renderer (will reuse this; only instantiate a new one on mode changes)
currentrenderer = jjrenderer.Renderer()

menutimeout = 10 # seconds

## GLOBALS ##
pleasequit = False
currentmode = -1 # initialise as an invalid mode; any mode change will trigger change
displaymanger = None # set up
menuindexselected = 0
lastsoftwareupdatecheck = 0
swversion = None

# timing
t_lastbuttonpress = 0
menutimeout_armed = False

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
  logging.info("button pressed, t={0}".format(t_lastbuttonpress))
  if currentmode == "menu":
    if not currentrenderer.name == "menu":
      currentrenderer = jjrenderer.renderers["menu"]()
    menuindexselected = (menuindexselected+1)%len(menu) 
    logging.debug("selected item = " + str(menuindexselected))
    displaymanager.doRender(currentrenderer, menu=menu, selecteditem=menuindexselected)
  else:
    changeMode("menu")

def onMenuTimeout():
  global menuindexselected
  logging.info("menu timeout")
  changeMode(menu[menuindexselected].name)

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
  if mode in modelist and not mode == currentmode:
    logging.info("changing mode to " + mode)
    currentmode = mode
    settings.setSetting("mode", mode, quiet=True) # update quietly; don't trigger registered events (they might have come here!)
    r = None
    if mode == "config":
      # set wifi to AP mode
      wifimanager.setWifiMode("ap")
      gpsstat = gpshandler.getStatus()
      kwargs["ssid"] = settings.getSettingValue("apssid")
      kwargs["password"] = settings.getSettingValue("appass")
      kwargs["ip"] = ap_addr
      kwargs["port"] = webadmin_port
      kwargs["gpsstat"] = gpsstat
    elif mode == "menu":
      # do not change mode for menu
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
  else:
    logging.warning("same or invalid mode " + mode + " - not changing")
  
def updateTime(dt, force=False):
  if force:
    logging.debug("forcing display update!")
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
        logging.info("updating system timezone")
        r = subprocess.run(["sudo","timedatectl","set-timezone",tzname])
        if r.returncode == 0:
          logging.info("success - system timezone changed to " + getSystemTz())
    else:
      logging.warning("non-linux os: cannot update system timezone.")

def getSystemTz():
  if "linux" in sys.platform:
    return pydbus.SystemBus().get(".timedate1").Timezone
  else:
    logging.warning("cannot access system timezone. returning dummy.")
    return "UTC"

def checkForUpdate():
  global lastsoftwareupdatecheck
  global swversion

  try:
    g = Github(settings.getSettingValue("githubtoken"))
    repo = g.get_repo(settings.getSettingValue("githubrepo"))
    rels = repo.get_releases()
  except:
    logging.warning("could not connect to github - abandoning update check")
    return None, None

  latestpub = datetime.datetime.min
  latestrel = None
  wgeturl = None
  tag = None
  for r in rels:
    if r.published_at > latestpub:
      latestpub = r.published_at
      latestrel = r
  if latestrel:
    wgeturl = latestrel.tarball_url
    tag = latestrel.tag_name
    logging.debug("found tag " + tag)
  
  # get the current tag of the repo
  myname = None
  if "linux" in sys.platform:
    try:
      myname = subprocess.run(["git", "describe", "--tags", "--abbrev=0"], text=True, capture_output=True).stdout.strip()
    except subprocess.CalledProcessError:
      logging.warning("unknown version. will update.")
  logging.debug("current version: " + str(myname))
  lastsoftwareupdatecheck = time.monotonic()
  swversion = myname

  if tag and myname:
    if myname == tag:
      logging.info("currently latest version: " + myname + ". no update required.")
    else:
      if "linux" in sys.platform:
        logging.info("current version: " + myname + ", available: " + tag)
        doUpdate(wgeturl, tag)
      else:
        logging.warning("will not update on windows")
  else:
    logging.warning("will not update, unknown version information.")
    
  return wgeturl, tag

def doUpdate(wgeturl, tag):

  updateok = True
  logging.info("updating now...")
  if "linux" in sys.platform:
    
    # display an updating screen
    displaymanager.doRender(jjrenderer.renderers["updating"](), version=tag)
    
    # make sure temp dir exists
    subprocess.run(["mkdir", "/tmp/jjclock"])
    
    # copy update script to temp location
    try:
      subprocess.run(["cp", os.path.join(scriptpath, "update.sh"), updatetempfile], check=True)
    except subprocess.CalledProcessError:
      logging.error("could not move update script")
      updateok = False     
      
    try:
      subprocess.Popen(["bash", updatetempfile])
    except subprocess.CalledProcessError:
      logging.error("problem starting update script")
      updateok = False
  
  # quit if all went well  
  if updateok:
    quit()

modifiers = ['', 'k', 'M', 'G', 'T']
def formatmemory(m):
  i = 0
  while (m>1024):
    m = m / 1024
    i = i + 1
  return "{0:.4g} {1}B".format(m, modifiers[i])

event_changemode = Event()
event_apupdate = Event()
event_manualtzupdate = Event()

## SCRIPT ##
if __name__ == "__main__":
  
  # load settings
  settings._settingsdefaults["mode"].validationlist = modelist # use mode list to select from
  settings.loadSettings()

  # init gpio
  if "linux" in sys.platform:
    logging.info("init gpio")
    #Device.pin_factory = MockFactory()
    userbutton = Button(buttongpio, bounce_time=debounce/1000.0)
    userbutton.when_pressed = onButton
  else:
    logging.warning("GPIO not available on this platform, no button enabled.")
  
  # init display(s)
  displaymanager = display.DisplayManager(size=(cropbox[2]-cropbox[0], cropbox[3]-cropbox[1])) # display manager primary surface will be the size of the target surface of the display
  pygamedisplay = display.PygameDisplay(start=False) # don't start just yet...
  pygamedisplay.resize = True
  displaymanager.displaylist.append(pygamedisplay)
  if "linux" in sys.platform:
    logging.info("init epd display")
    epddisplay = display.EPDDisplay(vcom=display_vcom) # init epd display
    epddisplay.cropbox = cropbox # set cropbox to match frame
    displaymanager.displaylist.append(epddisplay) # register display
  else:
    logging.warning("no display on this platform. using pygame.")
    pygamedisplay.restart() # start!
  
  # admin server
  logging.info("starting webserver")
  wa = webadmin.WebAdmin()
  wa.start()
  displaymanager.displaylist.append(wa.display)
  wa.providemenu(menu)

  # wifi manager init
  wifimanager.readHostapd() # read the official hostapd from system
  wifimanager.updateHostapd(settings.getSettingValue("apssid"), settings.getSettingValue("appass")) # update hostapd with settings

  # now screen is running, check for update
  logging.info("checking for update...")
  checkForUpdate()
  
  # load system timezone
  tz = pytz.timezone(settings.getSettingValue("manualtz"))
  currentdt = datetime.datetime.now().astimezone(tz) # init currentdt using new datetime

  # load last mode
  changeMode(settings.getSettingValue("mode"))
  
  # gps serial
  gpshandler = gpshandler.GpsHandler() # create and start gps handler
  gpshandler.connect()
  
  # setting change event registration - other threads might change settings, but reaction to changes should always be routed through the main loop
  settings.register(["mode"], event_changemode) # change mode when mode setting is updated from web interface (or elsewhere, unquietly)
  settings.register(["manualtz"], event_manualtzupdate) # update the timezone when manual timezone is changed
  settings.register(["apssid", "appass"], event_apupdate) # register wifimanager to respond to future changes to hostapd settings

  tlastupdate = time.monotonic()
  while not pleasequit:
      
      t = time.monotonic()

      if pygamedisplay.buttonevent.is_set():
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

      autotz = settings.getSettingValue("autotz")

      tzchanged = False
      if event_manualtzupdate.is_set():
        event_manualtzupdate.clear()
        manualtz = settings.getSettingValue("manualtz")
        try:
          tztemp = pytz.timezone(manualtz)
        except pytz.UnknownTimeZoneError:
          logging.warning("bad manual timezone: " + manualtz)
        else:
          tzchanged = bool(not (tz.zone == tztemp.zone))
          if tzchanged:
            logging.debug("tzchanged")
          tz = tztemp
      
      if tzchanged and not getSystemTz() == tz.zone:
        setSystemTz(tz.zone)
      
      # if NMEA has been received, update the time
      dt = None
      p = ""
      gpson = settings.getSettingValue("gpson")
      autotz = settings.getSettingValue("autotz")
      if gpson and gpshandler.pollUpdated():
        # have some gps data I can use
        stat = gpshandler.getStatus()
        if stat["hastime"]:
          if autotz and stat["tz"]:
            dt = gpshandler.getDateTime(local=True)
            p = "using gps time + auto tz: "
            # update timezone cached
            if not tz == stat["tz"]:
              tzchanged = True
              tz = stat["tz"]
              # update timezone setting --> will trigger system tz update next time around
              settings.setSetting("manualtz", tz.zone)
          else:
            dt = gpshandler.getDateTime(local=False).astimezone(tz)
            p = "using gps time + manual tz: "
      else:
        
        if ((t - tlastupdate) > 2):
          # it's been more than a couple of seconds (gps should do 1/s) - probably not working, should use system time
          dt = datetime.datetime.now().astimezone(tz)
          p = "using system time + manual tz: "

      if dt:
        logging.debug(p + dt.strftime("%H:%M:%S %z") + " (" + tz.zone + ")")
        tlastupdate = t
        updateTime(dt)
      elif tzchanged:
        # don't have a new time but tzchanged so need to force an update - & use cached time with new timezone
        tlastupdate = t
        updateTime(currentdt.astimezone(tz), True)

      # update check
      if t-lastsoftwareupdatecheck > minupdateinterval:
        if (dt and dt.hour == updatehour) or t-lastsoftwareupdatecheck > maxupdateinterval:
          checkForUpdate()

      # provide status to webadmin
      memoryusage = formatmemory(psutil.Process().memory_info().vms)
      wa.provideStatus({"tz":tz, "timestamp":currentdt.astimezone(tz), "mode":currentmode, "gps":gpshandler.getStatus(), "memory":memoryusage, "threadstate":{"gps":(gpshandler and gpshandler.isrunning()),"web":(wa and wa.isrunning()),"pygame":(pygamedisplay and pygamedisplay.isrunning())}, "version":swversion})
          
      time.sleep(0.1) # limit frequency / provide a thread opportunity
  
  # Close the window and quit.
  logging.info("quitting")
