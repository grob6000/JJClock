# JJ Clock
# Lots of love from George 2021

## INCLUDES ##
import pygame
import datetime
import os
import random
import math
import os
from gpiozero import Device, Button
#from gpiozero.pins.mock import MockFactory
from IT8951.display import AutoEPDDisplay
from IT8951 import constants
import time
from PIL import Image, ImageDraw, ImageFont

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
currentmode = modelist[0]
currentwifimode = "unknown"
epddisplay = None
menuitemselected = 0
menutimer=-1

## FUNCTIONS ##

def timerReset():
  global menutimeout
  global menutimer
  menutimer = menutimeout

def timerTick():
  global menutimer
  if menutimer > 0:
    menutimer = menutimer - 1
  if menutimer == 0:
    menutimer = -1 # disable
    onMenuTimeout()
  
def onButton():
  global menuitemselected
  print("button pressed")
  if currentmode == "menu":
    menuitemselected = (menuitemselected+1)%len(menu)
    showMenu()
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
  if mode in modelist:
    print("changing mode to " + mode)
    if mode == "wificonfig":
      # set wifi to AP mode
      setWifiMode("ap")
      showNotImplemented(mode) # todo - show wifi information
    else:
      setWifiMode("client") # all other modes should be in client state (if no wifi configured, will be disconnected...)
      if mode == "menu":
        showMenu()
      elif mode == "splash":
        displayImage(Image.open("./img/splash.png"))
      else:
        showNotImplemented(mode)
      savePersistentMode(mode)
  else:
    print("invalid mode " + mode + " - not changing")
      
def showNotImplemented(mode="unknown"):
  global boxsize
  screen = Image.new('L', boxsize)
  screen.paste(0xFF, box=(0,0,screen.size[0],screen.size[1]))
  draw = ImageDraw.Draw(screen)
  fnt = ImageFont.truetype("./font/ebgaramondmedium.ttf",20)
  t = "Uh-oh. '" + mode + "' has not been implemented!"
  tsz = fnt.getsize(t)
  draw.text((screen.size[0]/2-tsz[0]/2, screen.size[1]/2-tsz[1]/2), t, font=fnt, fill=0x00)
  displayImage(screen)
  
def displayImage(img, x=0, y=0, resize=False):
  global epddisplay
  global boxsize
  global cropbox
  if resize:
    ratio = min(img.size[0]/boxsize[0],img.size[1]/boxsize[1]) # calculate ration required to fit image
    imgadj = img.resize((img.size[0]*ratio,img.size[1]*ratio), Image.ANTIALIAS)
  else:
    imgadj = img
  imgadj = imgadj.crop((0,0,boxsize[0],boxsize[1])) # crop to visible box
  epddisplay.frame_buf.paste(img, (cropbox[0]+x,cropbox[1]+y)) # paste to buffer
  epddisplay.draw_full(constants.DisplayModes.GC16) # display

def updateDisplay(pygamesurf):
  global epddisplay
  print("updating display")
  data = pygame.image.tostring(pygamesurf, 'RGBA')
  img = Image.fromstring('RGBA', screensize, data)
  displayImage(img, epddisplay)

def testDisplay(gridsize=100):
  displayImage(Image.open("./img/test.png"))
  
def showMenu():
  global menuitemselected
  global menu
  global menusize
  global menupatchsize
  global menuicondim
  global boxsize
  
  ipp = menusize[0] * menusize[1] # number of items per page
  page = int(menuitemselected / ipp)
  pi_select = menuitemselected % ipp # index of item selected on page
  
  fnt = ImageFont.truetype("./font/ebgaramondmedium.ttf",20)
  
  screen = Image.new('L', boxsize)
  screen.paste(0xFF, box=(0,0,screen.size[0],screen.size[1]))
  
  for pi in range(0, ipp):
    mi = pi+(page*ipp)
    if len(menu) > mi:
      menuimg = Image.new('L', menupatchsize)
      menuimg.paste(0xFF, box=(0,0,menuimg.size[0],menuimg.size[1]))
      menuimg.paste(Image.open(menu[mi]["icon"]).resize((menuicondim,menuicondim),Image.ANTIALIAS),(int((menupatchsize[0]-menuicondim)/2),20))
      draw = ImageDraw.Draw(menuimg)
      fsz = fnt.getsize(menu[mi]["text"])
      draw.text((int(menuimg.size[0]/2-fsz[0]/2), menuicondim + 30),menu[mi]["text"],font=fnt,fill=0x00)
      x = int((pi % menusize[0] + 0.5) * (screen.size[0] / menusize[0]) - menupatchsize[0]/2)
      y = int((int(pi / menusize[0]) + 0.5) * (screen.size[1] / menusize[1]) - menupatchsize[1]/2)
      if pi == pi_select: # show this item as selected with surrounding box
        screen.paste(0x80, box=(x-20, y-20, x+menupatchsize[0]+20, y+menupatchsize[1]+20))
      screen.paste(menuimg, (x,y))
  
  draw = ImageDraw.Draw(screen)
  pagetext = "Page {0} of {1}".format(page+1, math.ceil(len(menu)/ipp))
  ptsz = fnt.getsize(pagetext)
  draw.text((int(screen.size[0]/2-ptsz[0]/2), 20), pagetext, font=fnt, fill=0x00)
  
  displayImage(screen)
  
## SCRIPT ##

# init gpio
print("init gpio")
#Device.pin_factory = MockFactory()
userbutton = Button(buttongpio, bounce_time=debounce/1000.0)
userbutton.when_pressed = onButton

# init pygame
print("init pygame engine")
os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()
#screen = pygame.display.set_mode(screensize)
#pygame.display.set_caption("My Game")
clock = pygame.time.Clock() # Used to manage how fast the screen updates

# init epd display
print("init display")
epddisplay = AutoEPDDisplay(vcom=display_vcom)

# splash
changeMode("splash")
time.sleep(2)

# load last mode
changeMode(loadPersistentMode())

#localdir = os.path.dirname(os.path.realpath(__file__))
#print(localdir)

while not pleasequit:
  	# handle events
	#if pygame.event.peek(pygame.QUIT):
	#	pleasequit = True
	#if pygame.event.peek(pygame.VIDEOEXPOSE) or pygame.event.peek(pygame.VIDEORESIZE):
	#	rerender = True
	#pygame.event.clear()
    print("tick")
    clock.tick(1) # --- Limit to 1 frame per second
    timerTick()

# Close the window and quit.
print("quitting")
pygame.quit()
