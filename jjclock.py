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
  if "clock" in k:
    menu.append(r)

menutimeout = 10 # seconds

## GLOBALS ##
pleasequit = False
currentmode = -1 # initialise as an invalid mode; any mode change will trigger change
currentwifimode = "unknown"
epddisplay = None
menuitemselected = 0

# timing
t_lastbuttonpress = 0
menutimeout_armed = False

systzname = "UTC"
tz = pytz.UTC
tf = timezonefinder.TimezoneFinder()
currentdt = datetime.datetime.now()

## FUNCTIONS ##
  
def displayRender(renderer, **kwargs):
  global epddisplay
  global cropbox
  global boxsize
  screen = Image.new("L", boxsize)
  screen = renderer.doRender(screen,**kwargs)
  if epddisplay:
    epddisplay.frame_buf.paste(screen, (cropbox[0],cropbox[1])) # paste to buffer
    epddisplay.draw_full(constants.DisplayModes.GC16) # display
  else:
    screen.show()
  
def onButton():
  global menuitemselected
  global menu
  global menutimeout_armed
  global t_lastbuttonpress
  global currentmode
  t_lastbuttonpress = time.monotonic()
  logging.info("button pressed, t={0}".format(t_lastbuttonpress))
  if currentmode == "menu":
    menuitemselected = (menuitemselected+1)%len(menu) 
    logging.debug("selected item = " + str(menuitemselected))
    displayRender(rinstances["menu"], menu=menu, selecteditem=menuitemselected)
  else:
    menutimeout_armed = True
    changeMode("menu")

def onMenuTimeout():
  global menuitemselected
  logging.info("menu timeout")
  changeMode(menu[menuitemselected].getName())

def setWifiMode(newwifimode):
  global currentwifimode
  if (newwifimode == currentwifimode):
    logging.info("wifi mode unchanged")
  elif newwifimode == "ap":
    logging.info("NOT IMPLEMENTED - wifi mode AP")
    currentwifimode = newwifimode
  elif newwifimode == "client":
    logging.info("NOT IMPLEMENTED - wifi mode Client")
    currentwifimode = newwifimode
  else:
    logging.info("invalid wifi mode, no change")

def savePersistentMode(mode):
  logging.info("NOT IMPLEMENTED - persist mode as file")

def loadPersistentMode():
  return "clock_digital" # default for now
  logging.info("NOT IMPLEMENTED - load persistent mode from file")

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
    if mode == "config":
      # set wifi to AP mode
      setWifiMode("ap")
      gpsstat = gpshandler.getStatus()
      kwargs["ssid"] = ap_ssid
      kwargs["password"] = ap_pass
      kwargs["ip"] = formatIP(ip_addr)
      kwargs["gpsstat"] = gpsstat
    else:
      setWifiMode("client") # all other modes should be in client state (if no wifi configured, will be disconnected...)
    if mode == "menu":
        kwargs["selecteditem"] = menuitemselected
        kwargs["menu"] = menu
    if mode in rinstances:
      r = rinstances[mode]
      kwargs["timestamp"] = currentdt
    else:
      r = jjrenderer.Renderer()
    savePersistentMode(mode)
    displayRender(r,**kwargs)
  else:
    logging.warning("invalid mode " + mode + " - not changing")
  
def updateTime(dt):
  global currentdt
  #global renderers
  #global currentmode
  currentdt = dt
  #print(dt)
  ui = rinstances[currentmode].getUpdateInterval()
  if (dt.second == 0) and ("clock" in currentmode) and (currentmode in rinstances) and ((dt.minute + dt.hour*60) % ui == 0):
    displayRender(rinstances[currentmode], timestamp=dt, mode=currentmode)

def setSystemTz(tzname):
  if not tzname == systzname:
    if "linux" in sys.platform:
      logging.info("updating system timezone")
      r = subprocess.run(["sudo","timedatectl","set-timezone",tzname])
      if r.returncode == 0:
        logging.info("success - system timezone changed to " + getSystemTz())
    else:
      systzname = tzname
      logging.warning("non-linux os: cannot update system timezone. dummy value set to " + systzname)

def getSystemTz():
  if "linux" in sys.platform:
    return pydbus.SystemBus().get(".timedate1").Timezone
  else:
    logging.warning("cannot access system timezone. returning dummy.")
    return systzname

def checkForUpdate():
  logging.warning("not implemented - check for update")
  return False

def doUpdate():
  logging.warning("not implemented - do update. application will not restart.")
  quit() # update will quit the script; we'll expect the updater to restart it
  
## SCRIPT ##
if __name__ == "__main__":

  # init gpio
  if "linux" in sys.platform:
    logging.info("init gpio")
    #Device.pin_factory = MockFactory()
    userbutton = Button(buttongpio, bounce_time=debounce/1000.0)
    userbutton.when_pressed = onButton
  else:
    logging.warning("GPIO not available on this platform, no button enabled.")
  
  # init epd display
  if "linux" in sys.platform:
    logging.info("init display")
    epddisplay = AutoEPDDisplay(vcom=display_vcom)
  else:
    logging.warning("no display on this platform.")
    epddisplay = None
  
  # splash
  #changeMode("splash")
  #time.sleep(2)
  
  # load system timezone
  systzname = getSystemTz()
  tz = pytz.timezone(systzname)
  
  # load last mode
  changeMode(loadPersistentMode())
  
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
        stat = gpshandler.getStatus()
        if stat["hastime"]:
          if stat["hasfix"]:
            dt = gpshandler.getDateTime(local=True)
            p = "using nmea time + tz: "
          else:
            dt = gpshandler.getDateTime(local=False).astimezone(tz)
            p = "using nmea time + cached tz: "
        else:
          dt = datetime.datetime.now()
          p = "using system time: "
        if dt:
          logging.debug(p + dt.strftime("%H:%M:%S %z"))
          updateTime(dt)
      else:
        t = time.monotonic()
        if ((t - tlastupdate) >= 2):
          tlastupdate = t
          updateTime(datetime.datetime.now())
          
      time.sleep(0.2) # limit to 5Hz
  
  # Close the window and quit.
  logging.info("quitting")
