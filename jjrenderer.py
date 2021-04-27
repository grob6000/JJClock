## IMPORTS ##
from pillow import Image, ImageDraw, ImageFont

# helpers shared by all renderers
def fill(img, color=0xFF):
  img.paste(color, box=(0,0,img.size[0],img.size[1]))
  return img

#renderer base class
class Renderer:
    
  def getName(self):
    return "default"
    
  def getUpdateInterval(self):
    return 1
  
  def getMenuItem(self):
    return {"text":"Default", "icon":"./img/default.png"}
  
  def doRender(self, screen, **kwargs):
    fill(screen) # fill screen with white
    draw = ImageDraw.Draw(screen)
    fnt = ImageFont.truetype("./font/ebgaramondmedium.ttf",24)
    tsz = digitalfont.getsize("X")
    maxlen = int((screen.size[0] - 100) / tsz[0])
    i = 0
    draw.text((50,50), "DEFAULT RENDERER", font=fnt, fill=0x00)
    for k,v in kwargs.iteritems():
      t = "{0}: {1}".format(str(k),str(v))
      if len(t) > maxlen:
        t = t[:maxlen-3] + "..."
      draw.text((50,100+i*textheight*1.5), t, font=fnt, fill=0x00)
      i=i+1
    return screen