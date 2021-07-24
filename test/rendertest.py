# test

import sys
import datetime
from PIL import Image, ImageDraw, ImageFont
import logging
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

# to import from parent dir (as we're in test...)
import sys, os, inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

import jjrenderer
from jjcommon import *

dooverlay = False
overlaycolor = 0xD0

if __name__ == "__main__":

  print("Renderer test script")
  
  if len(sys.argv)>1:
    rlist = sys.argv[1:]
  else:
    rlist = jjrenderer.renderers.keys()
  
  kwargs = {"timestamp":datetime.datetime.now().astimezone(), "ip":ap_addr, 
  "port":webadmin_port, "ssid":ap_ssid, "password":ap_pass, "wifimode":"ap", "wifistatus":{"ssid":"WifiNetwork","ip_address":"192.168.99.1"},"ssid":ap_ssid,"password":ap_pass,"ip":ap_addr,"port":80}
  
  print(kwargs)
  
  for r in rlist:
    if r in jjrenderer.renderers:
      print("Rendering " + r)
      screen = Image.new("L", boxsize)
      rinst = jjrenderer.renderers[r]()
      screen = rinst.doRender(screen,**kwargs)
      if dooverlay:
        draw = ImageDraw.Draw(screen)
        draw.rectangle((0,0,boxsize[0]-1,boxsize[1]-1),fill=None, outline=overlaycolor)
        clx = int(screen.size[0]/2)
        cly = int(screen.size[1]/2)
        draw.line((0,cly,screen.size[0],cly),fill=overlaycolor)
        draw.line((clx,0,clx,screen.size[1]),fill=overlaycolor)
      screen.show()