# test

import sys
import datetime
from PIL import Image, ImageDraw, ImageFont

import jjrenderer
from jjcommon import *

overlaycolor = 0xD0

if __name__ == "__main__":

  print("Renderer test script")
  
  if len(sys.argv)>1:
    rlist = sys.argv[1:]
  else:
    rlist = jjrenderer.renderers.keys()
  
  kwargs = {"timestamp":datetime.datetime.now()}
  for r in rlist:
    if r in jjrenderer.renderers:
      print("Rendering " + r)
      screen = Image.new("L", boxsize)
      rinst = jjrenderer.renderers[r]()
      screen = rinst.doRender(screen,**kwargs)
      draw = ImageDraw.Draw(screen)
      draw.rectangle((0,0,boxsize[0]-1,boxsize[1]-1),fill=None, outline=overlaycolor)
      clx = int(screen.size[0]/2)
      cly = int(screen.size[1]/2)
      draw.line((0,cly,screen.size[0],cly),fill=overlaycolor)
      draw.line((clx,0,clx,screen.size[1]),fill=overlaycolor)
      screen.show()