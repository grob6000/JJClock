from jjrenderer.renderer import *

class RendererBigbenClock(Renderer):
  name = "clock_bigben"
  isclock = True
  menuitem = {"icon":"icon_bigben.png","text":"Big Ben","description":"DONG DONG DONG DONG DONG DONG DONG DONG DONG DONG DONG DONG"}
  _rot = (831,808)
  _targetheight = 0.80
  def __init__(self):
    self.img_bg = getImage("bigben_background")
    self.img_bg.load()
    self.img_mhand = getImage("bigben_minutehand").convert("RGBA")
    self.img_mhand.load()
    self.img_hhand = getImage("bigben_hourhand").convert("RGBA")
    self.img_hhand.load()
  #  return 1
  def doRender(self, screen, **kwargs):
    
    a_min = 360 - (kwargs["timestamp"].minute / 60 * 360)
    a_hour = 360 - (((kwargs["timestamp"].hour % 12) / 12 + kwargs["timestamp"].minute / (12*60)) * 360)
    scale = (screen.size[1] * RendererBigbenClock._targetheight) / self.img_bg.size[1]
    
    composite = Image.new("RGBA",self.img_bg.size, (255,255,255,255))
    composite.paste(self.img_bg)
    imrot = self.img_mhand.rotate(angle=a_min,center=RendererBigbenClock._rot)
    composite.paste(imrot,mask=imrot)
    imrot = self.img_hhand.rotate(angle=a_hour,center=RendererBigbenClock._rot)
    composite.paste(imrot,mask=imrot)
    
    fill(screen)
    composite = composite.resize((int(d * scale) for d in composite.size),Image.ANTIALIAS)
    x0 = int((screen.size[0] - composite.size[0])/2)
    y0 = int((screen.size[1] - composite.size[1])/2)
    screen.paste(composite, (x0,y0))
    
    return screen