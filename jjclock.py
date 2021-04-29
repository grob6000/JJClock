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
menutimer=-1

systzname = ""
tz = pytz.UTC
tf = timezonefinder.TimezoneFinder()
currentdt = datetime.datetime.now()

## FUNCTIONS ##

## CLOCK RENDERERS ##   
  
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
  
def parseNMEA(line):

  global tf
  global tz
  global systzname
  
  #print(line)
  fields = line.decode('ascii').split(",")
  cmd = fields[0]
  data = {}
  
  if cmd == "$GPRMC":
    
    # utc time
    if (len(fields[1]) >= 6) and (len(fields[9]) >= 6):
      hour = int(fields[1][0:2])
      minute = int(fields[1][2:4])
      second = int(fields[1][4:6])
      day = int(fields[9][0:2])
      month = int(fields[9][2:4])
      year = int(fields[9][4:6]) + 2000 
      data["timestamp"] = datetime.datetime(year, month, day, hour, minute, second, tzinfo=pytz.UTC)

    # signal validity
    data["signalok"] = bool(fields[2] == "A")
    
    # lat and lng
    if len(fields[3])>0:
      lat = float(fields[3][0:2]) + float(fields[3][2:])/60
      if fields[4] == "S":
        lat = lat * -1
      data["lat"] = lat
    if len(fields[5])>0:
      lng = float(fields[5][0:3]) + float(fields[5][3:])/60
      if fields[6] == "W":
        lng = lng * -1
      data["lng"] = lng

    # timezone - check 1/min if all preconditions met (signal quality indicator we will ignore; as long as we have a fix it's probably fine for TZ)
    if "timestamp" in data:
      if second == 0 and "lat" in data and "lng" in data:
        tzname = tf.certain_timezone_at(lat=data["lat"],lng=data["lng"])
        tz = pytz.timezone(tzname)

    
  return data


def timerReset():
  global menutimeout
  global menutimer
  menutimer = menutimeout

def timerTick():
  print("tick")
  global menutimer
  if menutimer > 0:
    menutimer = menutimer - 1
  if menutimer == 0:
    menutimer = -1 # disable
    onMenuTimeout()
  
def onButton():
  global menuitemselected
  global menu
  print("button pressed")
  if currentmode == "menu":
    menuitemselected = (menuitemselected+1)%len(menu) 
    displayRender(rinstances["menu"], menu=menu, selecteditem=menuitemselected)
  else:
    changeMode("menu")
  timerReset()

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

  
#def displayImage(img, x=0, y=0, resize=False):
#  global epddisplay
#  global boxsize
#  global cropbox
#  if resize:
#    ratio = min(img.size[0]/boxsize[0],img.size[1]/boxsize[1]) # calculate ration required to fit image
#    imgadj = img.resize((img.size[0]*ratio,img.size[1]*ratio), Image.ANTIALIAS)
#  else:
#    imgadj = img
#  imgadj = imgadj.crop((0,0,boxsize[0],boxsize[1])) # crop to visible box
#  epddisplay.frame_buf.paste(img, (cropbox[0]+x,cropbox[1]+y)) # paste to buffer
#  epddisplay.draw_full(constants.DisplayModes.GC16) # display

#def updateDisplay(pygamesurf):
#  global epddisplay
#  print("updating display")
#  data = pygame.image.tostring(pygamesurf, 'RGBA')
#  img = Image.fromstring('RGBA', screensize, data)
#  displayImage(img, epddisplay)

#def testDisplay(gridsize=100):
#  displayImage(Image.open("./img/test.png"))
  
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

while not pleasequit:
    
    # tick every 1 sec
    t = time.time()
    if t > lastticktime + 1:
      lastticktime = t
      timerTick()
    
    # if NMEA has been received, update the time
    if gpshandler.pollUpdated():
      dt = gpshandler.getDateTime(local=True)
      stat = gpshandler.getStatus()
        if stat["hastime"]:
          if stat["hasfix"]:
            dt = gpshandler.getDateTime(local=True)
          else:
            dt = gpshandler.getDateTime(local=False).astimezone(tz)
        else:
          dt = datetime.datetime.now()
          p = "using system time: "
        if dt:
          print(p + t.strftime("%H:%M:%S %z"))
          updateTime(t)
    else:
      t = datetime.datetime.now()
      if ((datetime.datetime.now() - tlastupdate).total_seconds() >= 1):
        tlastupdate = t
        updateTime(t)

# Close the window and quit.
print("quitting")
ser.close()
#pygame.quit()
