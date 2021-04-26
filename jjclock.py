# JJ Clock
# Lots of love from George 2021

## INCLUDES ##
#import pygame
import datetime
import os
import random
import math
import os
import serial
from gpiozero import Device, Button
#from gpiozero.pins.mock import MockFactory
from IT8951.display import AutoEPDDisplay
from IT8951 import constants
import time
import pytz
import timezonefinder
import subprocess
from PIL import Image, ImageDraw, ImageFont
import pydbus

## CONSTANTS ##

screensize = (1448, 1072) # Set the width and height of the screen [width, height]
display_vcom = -2.55 # v - as per cable
cropbox = (10,10,1410,1060) # area we should work within / x1, y1, x2, y2
boxsize = (cropbox[2]-cropbox[0],cropbox[3]-cropbox[1]) # x,y
clx = int((cropbox[2] + cropbox[0])/2)
cly = int((cropbox[3] + cropbox[1])/2)

menusize = (4,3)
menupatchsize = (200,200)
menuicondim = 120

buttongpio = 23
debounce = 50 #ms

modelist = ["splash", "menu","wificonfig","clock_euro","clock_brexit","clock_digital"]

iface = "wlan0"
ap_ssid = "JJClockSetup"
ap_pass = "12071983"
ip_addr = (192,168,99,1)
ip_mask = (255,255,255,0)
dhcp_start = (192,168,99,10)
dhcp_end = (192,168,99,20)


menu = [
         {"icon":"./img/wifi.png","text":"Config Mode","mode":"wificonfig"},
         {"icon":"./img/eu.png","text":"Euro","mode":"clock_euro"},
         {"icon":"./img/uk.png","text":"Brexit","mode":"clock_brexit"},
         {"icon":"./img/digital.png","text":"Digital","mode":"clock_digital"}
       ]
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

# standard font
stdfnt = ImageFont.truetype("./font/ebgaramondmedium.ttf",24)


## FUNCTIONS ##

## CLOCK RENDERERS ##  

# render helpers #

def fill(img, color=0xFF):
  img.paste(color, box=(0,0,img.size[0],img.size[1]))
  return img

# renderers #

digitalfont = ImageFont.truetype("./font/digital.ttf",300)
digitaldatefont = ImageFont.truetype("./font/ebgaramondmedium.ttf",50)
def renderClockDigital(screen, draw, **kwargs):
  global digitalfont
  global digitaldatefont
  fill(screen)
  if "timestamp" in kwargs:
    t = "{0:02d}:{1:02d}".format(kwargs["timestamp"].hour, kwargs["timestamp"].minute)
    dstring = kwargs["timestamp"].strftime("%A, %-d %B %Y")
  else:
    t = "--:--"
    dstring = "Please Wait..."
  tsz = digitalfont.getsize(t)
  tsz2 = digitaldatefont.getsize(dstring)
  digy = int((screen.size[1]-tsz[1]-tsz2[1]-50)/2)
  draw.text((screen.size[0]/2-tsz[0]/2, digy), t, font=digitalfont, fill=0x00)
  draw.text((screen.size[0]/2-tsz2[0]/2, digy + tsz[1] + 50), dstring, font=digitaldatefont, fill=0x00)
  return screen

def renderClockEuro(screen, draw, **kwargs):
  return renderNotImplemented(screen, draw, **kwargs)
  
def renderClockBrexit(screen, draw, **kwargs):
  return renderNotImplemented(screen, draw, **kwargs)

renderers = {"clock_euro":renderClockEuro, "clock_brexit":renderClockBrexit, "clock_digital":renderClockDigital}
updateintervals = {"clock_brexit":5} # default is 1 min, set this to other values (in minutes) where required

def renderMenu(screen, draw, **kwargs):

  #global menuitemselected
  #global menu
  global menusize
  global menupatchsize
  global menuicondim
  #global boxsize
  
  fill(screen)
  
  if not "selecteditem" in kwargs:
    kwargs["selecteditem"] = 0
  if not "menu" in kwargs:
    return screen
    
  ipp = menusize[0] * menusize[1] # number of items per page
  page = int(kwargs["selecteditem"] / ipp)
  pi_select = kwargs["selecteditem"] % ipp # index of item selected on page
  
  #fnt = ImageFont.truetype("./font/ebgaramondmedium.ttf",20)
  
  #screen = Image.new('L', boxsize)
  #screen.paste(0xFF, box=(0,0,screen.size[0],screen.size[1]))
  
  for pi in range(0, ipp):
    mi = pi+(page*ipp)
    if len(kwargs["menu"]) > mi:
      menuimg = Image.new('L', menupatchsize)
      menuimg.paste(0xFF, box=(0,0,menuimg.size[0],menuimg.size[1]))
      menuimg.paste(Image.open(kwargs["menu"][mi]["icon"]).resize((menuicondim,menuicondim),Image.ANTIALIAS),(int((menupatchsize[0]-menuicondim)/2),20))
      draw2 = ImageDraw.Draw(menuimg)
      fsz = stdfnt.getsize(kwargs["menu"][mi]["text"])
      draw2.text((int(menuimg.size[0]/2-fsz[0]/2), menuicondim + 30),kwargs["menu"][mi]["text"],font=stdfnt,fill=0x00)
      x = int((pi % menusize[0] + 0.5) * (screen.size[0] / menusize[0]) - menupatchsize[0]/2)
      y = int((int(pi / menusize[0]) + 0.5) * (screen.size[1] / menusize[1]) - menupatchsize[1]/2)
      if pi == pi_select: # show this item as selected with surrounding box
        screen.paste(0x80, box=(x-20, y-20, x+menupatchsize[0]+20, y+menupatchsize[1]+20))
      screen.paste(menuimg, (x,y))
  
  #draw = ImageDraw.Draw(screen)
  pagetext = "Page {0} of {1}".format(page+1, math.ceil(len(kwargs["menu"])/ipp))
  ptsz = stdfnt.getsize(pagetext)
  draw.text((int(screen.size[0]/2-ptsz[0]/2), 20), pagetext, font=stdfnt, fill=0x00)
  return screen

def renderConfig(screen, draw, **kwargs):
  return renderNotImplemented(screen, draw, **kwargs)

def renderNotImplemented(screen, draw, **kwargs):
  global stdfnt
  fill(screen)
  if "mode" in kwargs:
    t = "Uh-oh. '" + kwargs["mode"] + "' has not been implemented!"
  else:
    t = "Uh-ok. Mode has not been implemented!"
  tsz = stdfnt.getsize(t)
  draw.text((screen.size[0]/2-tsz[0]/2, screen.size[1]/2-tsz[1]/2), t, font=stdfnt, fill=0x00)
  return screen

def renderSplash(screen, draw, **kwargs):
  screen.paste(Image.open("./img/splash.png"))
  return screen
  
def displayRender(r, **kwargs):
  global epddisplay
  global cropbox
  global boxsize
  screen = Image.new("L", boxsize)
  draw = ImageDraw.Draw(screen)
  screen = r(screen,draw,**kwargs)
  epddisplay.frame_buf.paste(screen, (cropbox[0],cropbox[1])) # paste to buffer
  epddisplay.draw_full(constants.DisplayModes.GC16) # display
  
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
        if not tzname == systzname:
          # TO-DO update system timezone
          print("update system timezone")
          r = subprocess.run(["sudo","timedatectl","set-timezone",tzname])
          if r.returncode == 0:
            systzname = tzname
            print("success")
      # local time - use exising tz if applicable
      data["localtime"] = data["timestamp"].astimezone(tz)
    
  return data


def timerReset():
  global menutimeout
  global menutimer
  menutimer = menutimeout

def timerTick():
  #print("tick")
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
    displayRender(renderMenu, menu=menu, selecteditem=menuitemselected)
  else:
    changeMode("menu")
  timerReset()

def onMenuTimeout():
  global menuitemselected
  print("menu timeout")
  changeMode(menu[menuitemselected]["mode"])

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
    if mode == "wificonfig":
      # set wifi to AP mode
      setWifiMode("ap")
      r = renderConfig
    else:
      setWifiMode("client") # all other modes should be in client state (if no wifi configured, will be disconnected...)
      if mode == "menu":
        r = renderMenu
        kwargs["selecteditem"] = menuitemselected
        kwargs["menu"] = menu
      elif mode == "splash":
        r = renderSplash
      elif mode in renderers:
        r = renderers[mode]
        if "clock" in mode:
          kwargs["timestamp"] = currentdt
      else:
        r = renderNotImplemented
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
  global renderers
  global currentmode
  currentdt = dt
  #print(dt)
  ui = 1
  if currentmode in updateintervals:
    ui = updateintervals[currentmode]
  if (dt.second == 0) and ("clock" in currentmode) and (currentmode in renderers) and ((dt.minute + dt.hour*60) % ui == 0):
    displayRender(renderers[currentmode], timestamp=dt, mode=currentmode)

## SCRIPT ##

# init gpio
print("init gpio")
#Device.pin_factory = MockFactory()
userbutton = Button(buttongpio, bounce_time=debounce/1000.0)
userbutton.when_pressed = onButton

# init pygame
#print("init pygame engine")
#os.environ["SDL_VIDEODRIVER"] = "dummy"
#pygame.init()
#screen = pygame.display.set_mode(screensize)
#pygame.display.set_caption("My Game")
#clock = pygame.time.Clock() # Used to manage how fast the screen updates

# init epd display
print("init display")
epddisplay = AutoEPDDisplay(vcom=display_vcom)

# splash
changeMode("splash")
time.sleep(2)

# load system timezone
timedated = pydbus.SystemBus().get(".timedate1")
systzname = timedated.Timezone
print("system timezone: " + systzname)
tz = pytz.timezone(systzname)

# load last mode
changeMode(loadPersistentMode())

#localdir = os.path.dirname(os.path.realpath(__file__))
#print(localdir)

# gps serial
ser = serial.Serial('/dev/serial0', 9600, timeout=1)

lastticktime = time.time()

while not pleasequit:
  	# handle events
	#if pygame.event.peek(pygame.QUIT):
	#	pleasequit = True
	#if pygame.event.peek(pygame.VIDEOEXPOSE) or pygame.event.peek(pygame.VIDEORESIZE):
	#	rerender = True
	#pygame.event.clear()
    
    # tick every 1 sec
    t = time.time()
    if t > lastticktime + 1:
      lastticktime = t
      timerTick()
    
    # if NMEA has been received, update the time
    if ser.in_waiting>0:
      d = parseNMEA(ser.readline())
      t = None
      if "localtime" in d:
        t = d["localtime"]
        p = "using nmea time: "
      elif "signalok" in d:
        t = datetime.datetime.now()
        p = "using system time: "
      if t:
        print(p + t.strftime("%H:%M:%S %z"))
        updateTime(t)
      
# Close the window and quit.
print("quitting")
ser.close()
#pygame.quit()
