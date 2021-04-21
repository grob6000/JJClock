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
from gpiozero.pins.mock import MockFactory
from IT8951.display import AutoEPDDisplay
from IT8951 import constants
import time

## CONSTANTS ##

screensize = (1448, 1072) # Set the width and height of the screen [width, height]
display_vcom = -2.55 # v - as per cable

buttongpio = 23
debounce = 50 #ms

modelist = ["wificonfig","displaytest","clock_euro","clock_brexit"]

iface = "wlan0"
ap_ssid = "JJClockSetup"
ap_pass = "12071983"
ip_addr = (192,168,99,1)
ip_mask = (255,255,255,0)
dhcp_start = (192,168,99,10)
dhcp_end = (192,168,99,20)

## GLOBALS ##
pleasequit = False
currentmode = modelist[0]
wifimode = None
epddisplay = None

## FUNCTIONS ##

def onButton():
  print("button pressed")

def changeMode(mode):
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
  epddisplay.frame_buf.paste(img, (0,0))
  epddisplay.draw_full(constants.DisplayModes.GC16)

def updateDisplay(pygamesurf):
  print("updating display")
  data = pygame.image.tostring(pygamesurf, 'RGBA')
  img = Image.fromstring('RGBA', screensize, data)
  displayImage(img, epddisplay)

def testDisplay(gridsize=100):
  print("test image for display")
  epddisplay.display.frame_buf.paste(0xFF, box=(0,0,epddisplay.width,epddisplay.height)) # fill white
  for y in range(0,int(epddisplay.height/gridsize)):
    for x in range(0,int(epddisplay.width/gridsize)):
      if (x+y)%2==0: # make an alternating pattern
        epddisplay.display.frame_buf.paste(0x00, box=(x*gridsize,y*gridsize,min((x+1)*gridsize-1,display.width),min((y+1)*gridsize-1,display.height))) # draw black squares
  
## SCRIPT ##

# init gpio
print("init gpio")
Device.pin_factory = MockFactory()
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
time.sleep(5)

#localdir = os.path.dirname(os.path.realpath(__file__))
#print(localdir)

while not pleasequit:
  	# handle events
	if pygame.event.peek(pygame.QUIT):
		pleasequit = True
	if pygame.event.peek(pygame.VIDEOEXPOSE) or pygame.event.peek(pygame.VIDEORESIZE):
		rerender = True
	pygame.event.clear()
    
	clock.tick(12)     # --- Limit to 5 frames per second
    
# Close the window and quit.
print("quitting")
pygame.quit()