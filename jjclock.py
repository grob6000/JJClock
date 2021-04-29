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
from sys import platform

if "linux" in platform:
  from gpiozero import Device, Button
  #from gpiozero.pins.mock import MockFactory
  from IT8951.display import AutoEPDDisplay
  from IT8951 import constants
  import pydbus
  import subprocess

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
print(modelist)

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
  print("button pressed")
  if currentmode == "menu":
    menuitemselected = (menuitemselected+1)%len(menu) 
    print("selected item = " + str(menuitemselected))
    displayRender(rinstances["menu"], menu=menu, selecteditem=menuitemselected)
  else:
    changeMode("menu")
  t_lastbuttonpress = time.monotonic()
  print("t = " + t_lastbuttonpress)

def onMenuTimeout():
  global menuitemselected
  print("menu timeout")
  changeMode(menu[menuitemselected].getName())

def setWifiMode(newwifimode):
  global currentwifimode
  if (newwifimode == currentwifimode):
    print("wifi mode unchanged")
  elif newwifimode == "ap":
    print("NOT IMPLEMENTED - wifi mode AP")
    currentwifimode = newwifimode
  elif newwifimode == "client":
    print("NOT IMPLEMENTED - wifi mode Client")
    currentwifimode = newwifimode
  else:
    print("invalid wifi mode, no change")

def savePersistentMode(mode):
  print("NOT IMPLEMENTED - persist mode as file")

def loadPersistentMode():
  return "clock_digital" # default for now
  print("NOT IMPLEMENTED - load persistent mode from file")

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
    print("changing mode to " + mode)
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
    print("invalid mode " + mode + " - not changing")
  
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
    if "linux" in platform:
      print("updating system timezone")
      r = subprocess.run(["sudo","timedatectl","set-timezone",tzname])
      if r.returncode == 0:
        print("success - system timezone changed to " + getSystemTz())
    else:
      systzname = tzname
      print("non-linux os: cannot update system timezone. dummy value set to " + systzname)

def getSystemTz():
  if "linux" in platform:
    return pydbus.SystemBus().get(".timedate1").Timezone
  else:
    print("cannot access system timezone. returning dummy.")
    return systzname
  
## SCRIPT ##

# init gpio
if "linux" in platform:
  print("init gpio")
  #Device.pin_factory = MockFactory()
  userbutton = Button(buttongpio, bounce_time=debounce/1000.0)
  userbutton.when_pressed = onButton
else:
  print("GPIO not available on this platform, no button enabled.")

# init epd display
if "linux" in platform:
  print("init display")
  epddisplay = AutoEPDDisplay(vcom=display_vcom)
else:
  print("no display on this platform.")
  epddisplay = None

# splash
changeMode("splash")
time.sleep(2)

# load system timezone
systzname = getSystemTz()
tz = pytz.timezone(systzname)

# load last mode
changeMode(loadPersistentMode())

# gps serial
gpshandler = gpshandler.GpsHandler() # create and start gps handler

tlastupdate = time.monotonic()
while not pleasequit:
    
    # tick every 1 sec
    t = time.monotonic()
    if menutimeout_armed and t - t_lastbuttonpress > menutimout:
      menutimeout_armed = False
      onMenuTimeout()
    
    # if NMEA has been received, update the time
    if gpshandler.pollUpdated():
      dt = gpshandler.getDateTime(local=True)
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
        print(p + t.strftime("%H:%M:%S %z"))
        updateTime(t)
    else:
      t = time.monotonic()
      if ((t - tlastupdate) >= 1):
        tlastupdate = t
        updateTime(datetime.datetime.now())

# Close the window and quit.
print("quitting")
ser.close()
#pygame.quit()
