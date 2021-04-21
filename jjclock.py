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

buttongpio = 23
debounce = 50 #ms

modelist = ["menu","wificonfig","clock_euro","clock_brexit","clock_digital"]

iface = "wlan0"
ap_ssid = "JJClockSetup"
ap_pass = "12071983"
ip_addr = (192,168,99,1)
ip_mask = (255,255,255,0)
dhcp_start = (192,168,99,10)
dhcp_end = (192,168,99,20)

menu_across = 4
menu_down = 2

menu = [
         {"icon":"./img/wifi.png","text":"Config Mode","mode":"wificonfig"},
         {"icon":"./img/eu.png","text":"Euro","mode":"clock_euro"},
         {"icon":"./img/uk.png","text":"Brexit","mode":"clock_brexit"},
         {"icon":"./img/digital.png","text":"Digital","mode":"clock_digital"}
       ]

## GLOBALS ##
pleasequit = False
currentmode = modelist[0]
wifimode = "unknown"
epddisplay = None
menuitemselected = 0

## FUNCTIONS ##

def onButton():
  print("button pressed")
  if not inmenu:
    inmenu = True
    displayMenu()

def changeMode(mode):
  global wifimode
  print("changing mode to " + mode)
  if mode == "wificonfig":
    # TO-DO set wifi to AP mode
    # TO-DO run DHCP server
    # TO-DO start config webserver
    # TO-DO display details on screen
    wifimode = "ap"
  else:
    # check current mode; ensure is in client mode
    if not wifimode == "client":
      # TO-DOset wifi to client mode
      wifimode = "client"
  if mode == "displaytest":
    # TO-DO generate test image
    # TO-DO display on screen
    testDisplay()
  
  
def displayImage(img):
  global epddisplay
  epddisplay.frame_buf.paste(img, (0,0))
  epddisplay.draw_full(constants.DisplayModes.GC16)

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
  ipp = menu_across * menu_down
  page = int(menuitemselected / ipp)
  pi_select = menuitemselected % ipp
  for pi in range(0, ipp):
    mi = pi+(page*ipp)
    if len(menu) > mi:
      menuimg = Image.new('L', (250,250))
      menuimg.paste(
  
  
   
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
changeMode("displaytest")
time.sleep(2)
displayImage(Image.open("./img/splash.png"))
time.sleep(2)

# splash screen
print("splash")

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
    clock.tick(60) # --- Limit to 1 frame per second

# Close the window and quit.
print("quitting")
pygame.quit()
