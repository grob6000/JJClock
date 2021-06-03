from jjrenderer.renderer import *
import jjrenderer.jjtimestring as ts

class RendererNixieClock(Renderer):
  
  def __init__(self):
    # load this once
    self.mapimg = getImage('map_nixie')
  
  def getimg(self, digit):
    digit = int(digit) % 10
    x = int(digit % 5) * 150
    y = int(digit // 5) * 300
    print("x={0},y={1}".format(x,y))
    return self.mapimg.crop((x,y,x+150,y+300))
  
  def getName(self):
    return "nixie"
  def getMenuItem(self):
    return {"icon":"icon_nixie.png","text":"Nixie"}
  def doRender(self, screen, **kwargs):
    fill(screen)
    c = (int(screen.size[0]/2), int(screen.size[1]/2)-50)
    # nixie time
    middlespace = 30
    screen.paste(self.getimg(kwargs["timestamp"].hour//10), (c[0]-300-middlespace,c[1]-150))
    screen.paste(self.getimg(kwargs["timestamp"].hour%10), (c[0]-150-middlespace,c[1]-150))
    screen.paste(self.getimg(kwargs["timestamp"].minute//10), (c[0]+middlespace,c[1]-150))
    screen.paste(self.getimg(kwargs["timestamp"].minute%10), (c[0]+150+middlespace,c[1]-150))
    # date in russian
    datefont = getFont("buranussr", 40)
    d = ts.GetDateString(kwargs["timestamp"], lang="ru", includeday=True)
    dsz = datefont.getsize(d)
    draw = ImageDraw.Draw(screen)
    draw.text((c[0]-int(dsz[0]/2),c[1]+200),d,font=datefont,fill=0x00)
    return screen