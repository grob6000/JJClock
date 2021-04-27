from PIL import Image, ImageDraw, ImageFont
import glob
import os.path
import datetime
from pathlib import Path

_localdir = os.path.dirname(os.path.realpath(__file__))
_fontpath = Path(_localdir).parent.joinpath("font").absolute()

def fill(img, color=0xFF):
  img.paste(color, box=(0,0,img.size[0],img.size[1]))
  return img

def getFont(fontname="ebgaramondmedium", fontsize=24):
  print(_fontpath)
  return ImageFont.truetype(os.path.join(_fontpath, fontname + ".ttf"), fontsize)

def getImage(imagename):

  p = Path("../img/" + imagename).absolute()
  if os.path.isfile(p):
    return Image.open(p)
  
  p = Path("../img/" + imagename + ".png").absolute()
  if os.path.isfile(p):
    return Image.open("../img/" + imagename + ".png")
  else:
    raise FileNotFoundError("Image file could not be found: " + imagename)

def testRenderer(rendererclass):
  print("Test render " + rendererclass.__name__)
  
  screensize = (1448, 1072) # Set the width and height of the screen [width, height]
  cropbox = (10,10,1410,1060) # area we should work within / x1, y1, x2, y2
  boxsize = (cropbox[2]-cropbox[0],cropbox[3]-cropbox[1]) # x,y
  kwargs = {"timestamp":datetime.datetime.now()}
  overlaycolor = 0xD0

  rinst = rendererclass()
  screen = Image.new("L", boxsize)
  screen = rinst.doRender(screen, **kwargs)
  draw = ImageDraw.Draw(screen)
  draw.rectangle((0,0,boxsize[0]-1,boxsize[1]-1),fill=None, outline=overlaycolor)
  clx = int(screen.size[0]/2)
  cly = int(screen.size[1]/2)
  draw.line((0,cly,screen.size[0],cly),fill=overlaycolor)
  draw.line((clx,0,clx,screen.size[1]),fill=overlaycolor)
  screen.show()

#renderer base class
class Renderer:

  def getName(self):
    return "default"
    
  def getUpdateInterval(self):
    return 1
  
  def getMenuItem(self):
    return {"text":"Default", "icon":"default.png"}
  
  def doRender(self, screen, **kwargs):
    fill(screen) # fill screen with white
    stdfnt = getFont()
    draw = ImageDraw.Draw(screen)
    tsz = stdfnt.getsize("X")
    maxlen = int((screen.size[0] - 100) / tsz[0])
    i = 0
    draw.text((50,50), type(self).__name__, font=stdfnt, fill=0x00)
    for k,v in kwargs.items():
      t = "{0}: {1}".format(str(k),str(v))
      if len(t) > maxlen:
        t = t[:maxlen-3] + "..."
      draw.text((50,100+i*tsz[1]*1.5), t, font=stdfnt, fill=0x00)
      i=i+1
    return screen