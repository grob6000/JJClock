# JJ Clock
# Lots of love from George 2021

## INCLUDES ##
import datetime
import os
import random
import math
import os
import serial
import time
import pytz
import timezonefinder
from PIL import Image, ImageDraw, ImageFont
import sys
from github import Github

if "linux" in sys.platform:
  from gpiozero import Device, Button
  #from gpiozero.pins.mock import MockFactory
  from IT8951.display import AutoEPDDisplay
  from IT8951 import constants
  import pydbus
  import subprocess

# set up logger
import logging
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

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
rinstances = {}
for k,r in jjrenderer.renderers.items():
    rinst = r()
    name = rinst.getName()
    rinstances[name] = rinst
    if not name in modelist:
      modelist.append(name)
logging.debug(str(modelist))

# populate menu
menu = [rinstances["config"]]
for k, r in rinstances.items():
  if "clock" in k and not k == "clock_birthday": # hide birthday mode!
    menu.append(r)
logging.debug(menu)

menutimeout = 10 # seconds

## GLOBALS ##
pleasequit = False
currentmode = -1 # initialise as an invalid mode; any mode change will trigger change
displaymanger = None # set up
menuitemselected = 0
lastsoftwareupdatecheck = 0

# timing
t_lastbuttonpress = 0
menutimeout_armed = False

tz = pytz.UTC
tf = timezonefinder.TimezoneFinder()
currentdt = datetime.datetime.now()

## FUNCTIONS ##
  
def onButton():
  global menuitemselected
  global menu
  global menutimeout_armed
  global t_lastbuttonpress
  global currentmode
  global displaymanager
  t_lastbuttonpress = time.monotonic()
  logging.info("button pressed, t={0}".format(t_lastbuttonpress))
  if currentmode == "menu":
    menuitemselected = (menuitemselected+1)%len(menu) 
    logging.debug("selected item = " + str(menuitemselected))
    displaymanager.doRender(rinstances["menu"], menu=menu, selecteditem=menuitemselected)
  else:
    menutimeout_armed = True
    changeMode("menu")

def onMenuTimeout():
  global menuitemselected
  logging.info("menu timeout")
  changeMode(menu[menuitemselected].getName())

def formatIP(ip):
  return "{ip[0]}.{ip[1]}.{ip[2]}.{ip[3]}".format(ip=ip)
  
def changeMode(mode):
  global modelist
  global currentmode
  global renderers
  global menuitemselected
  global menu
  r = None
  kwargs = {"mode":mode}
  if mode in modelist and not mode == currentmode:
    logging.info("changing mode to " + mode)
    currentmode = mode
    settings.setSetting("mode", mode)
    if mode == "config":
      # set wifi to AP mode
      wifimanager.setWifiMode("ap")
      gpsstat = gpshandler.getStatus()
      kwargs["ssid"] = ap_ssid
      kwargs["password"] = ap_pass
      kwargs["ip"] = ap_addr
      kwargs["port"] = webadmin_port
      kwargs["gpsstat"] = gpsstat
    elif mode == "menu":
      # do not change mode for menu
      kwargs["selecteditem"] = menuitemselected
      kwargs["menu"] = menu
    else:
      wifimanager.setWifiMode("client") # all other modes should be in client state (if no wifi configured, will be disconnected...)
    if mode in rinstances:
      r = rinstances[mode]
      kwargs["timestamp"] = currentdt
    else:
      r = jjrenderer.Renderer()
    displaymanager.doRender(r,**kwargs)
  else:
    logging.warning("invalid mode " + mode + " - not changing")
  
def updateTime(dt, force=False):
  global currentdt
  #global renderers
  global currentmode
  if force or not currentdt.minute == dt.minute:
    #print(dt)
    if ("clock" in currentmode):
      if dt.day==birthday["day"] and dt.month==birthday["month"] and not currentmode=="clock_birthday":
        changeMode("clock_birthday")
      elif (currentmode in rinstances):
        ui = rinstances[currentmode].getUpdateInterval()
        if ((dt.minute + dt.hour*60) % ui == 0):
          displaymanager.doRender(rinstances[currentmode], timestamp=dt, mode=currentmode)
  currentdt = dt
  
def setSystemTz(tzname):
    if "linux" in sys.platform:
      systzname = getSystemTz()
      if not tzname == systzname:
        logging.info("updating system timezone")
        r = subprocess.run(["sudo","timedatectl","set-timezone",tzname])
        if r.returncode == 0:
          logging.info("success - system timezone changed to " + getSystemTz())
      else:
        logging.info("not updating system timezone - already set to " + systzname)
    else:
      logging.warning("non-linux os: cannot update system timezone.")

def getSystemTz():
  if "linux" in sys.platform:
    return pydbus.SystemBus().get(".timedate1").Timezone
  else:
    logging.warning("cannot access system timezone. returning dummy.")
    return "UTC"

def checkForUpdate():
  global lastupdate
  
  g = Github(githubtoken)
  repo = g.get_repo(githubrepo)
  rels = repo.get_releases()
  latestpub = datetime.datetime.min
  for r in rels:
    if r.published_at > latestpub:
      latestpub = r.published_at
      latestrel = r
  wgeturl = latestrel.tarball_url
  tag = latestrel.tag_name
  logging.debug("found tag " + tag)
  
  # get the current tag of the repo
  myname = ""
  if "linux" in sys.platform:
    try:
      myname = subprocess.run(["git", "describe", "--tags", "--abbrev=0"], text=True, capture_output=True).stdout.strip()
    except subprocess.CalledProcessError:
      logging.warning("unknown version. will update.")
  
  lastsoftwareupdatecheck = time.monotonic()
  
  if myname == tag:
    logging.info("currently latest version. no update required.")
  else:
    if "linux" in sys.platform:
      logging.info("current version: " + myname + ", available: " + tag)
      doUpdate(wgeturl, tag)
    else:
      logging.warning("will not update on windows")
    
  return wgeturl, tag

def doUpdate(wgeturl, tag):

  updateok = True
  logging.info("updating now...")
  if "linux" in sys.platform:
    
    # display an updating screen
    displaymanager.doRender(jjrenderer.renderers["RendererUpdating"](), version=tag)
    
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

## SCRIPT ##
if __name__ == "__main__":
  
  # load settings
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
  if "linux" in sys.platform:
    logging.info("init epd display")
    epddisplay = display.EPDDisplay(vcom=display_vcom) # init epd display
    epddisplay.cropbox = cropbox # set cropbox to match frame
    displaymanager.displaylist.append(epddisplay) # register display
  else:
    logging.warning("no display on this platform. using pygame.")
    pygamedisplay = display.PygameDisplay()
    pygamedisplay.resize = True
    displaymanager.displaylist.append(pygamedisplay)
  
  # admin server
  wa = webadmin.WebAdmin()
  wa.start()
  
  # wifi testing
  n = wifimanager.getNetworks()
  print(n)
  
  sn = wifimanager.scanNetworks()
  print(sn)
  
  i = wifimanager.addNetwork("test", "nobigdeal")
  n = wifimanager.getNetworks()
  print(n)
  
  wifimanager.removeNetwork(i)
  n = wifimanager.getNetworks()
  print(n)
  
  # now screen is running, check for update
  checkForUpdate()
  
  # load system timezone
  tz = pytz.timezone(getSystemTz())
  
  # load last mode
  changeMode(settings.getSetting("mode"))
  
  # gps serial
  gpshandler = gpshandler.GpsHandler() # create and start gps handler
  gpshandler.connect()
  
  tlastupdate = time.monotonic()
  while not pleasequit:
      
      t = time.monotonic()
      if menutimeout_armed and t - t_lastbuttonpress > menutimeout:
        menutimeout_armed = False
        onMenuTimeout()
      
      # if NMEA has been received, update the time
      if gpshandler.pollUpdated():
        force = False
        stat = gpshandler.getStatus()
        if stat["hastime"]:
          if stat["tz"]:
            dt = gpshandler.getDateTime(local=True)
            p = "using nmea time + tz: "
            # update timezone cached
            if not tz == stat["tz"]:
              tz = stat["tz"]
              # update system timezone
              if not getSystemTz() == tz.zone:
                setSystemTz(tz.zone)
                force = True # force a render update; e.g. even if this occurs mid-minute...
          else:
            dt = gpshandler.getDateTime(local=False).astimezone(tz)
            p = "using nmea time + cached tz: "
        else:
          dt = datetime.datetime.now()
          p = "using system time: "
        if dt:
          logging.debug(p + dt.strftime("%H:%M:%S %z"))
          t = time.monotonic()
          tlastupdate = t          
          updateTime(dt)
          if t-lastsoftwareupdatecheck > minupdateinterval:
            if dt.hour == updatehour or t-lastsoftwareupdatecheck > maxupdateinterval:
              checkForUpdate()
      else:
        t = time.monotonic()
        if ((t - tlastupdate) >= 2):
          tlastupdate = t
          updateTime(datetime.datetime.now().astimezone())
          
      # if web action is pending
      adata = wa.getActionData()
      if adata:
        # data is available
        logging.debug(adata)
          
      time.sleep(0.1) # limit frequency / provide a thread opportunity
  
  # Close the window and quit.
  logging.info("quitting")
