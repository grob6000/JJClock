from jjrenderer.renderer import *

class RendererMuricaClock(Renderer):
  name = "clock_murica"
  isclock = True
  menuitem = {"icon":"icon_murica.png","text":"'Murica","description":"Like Clockwork. A well regulated Clock, being necessary to the security of a free State, the right of the people to keep and bear Hands shall not be infringed."}
  updateinterval = 5
  gundeathindex = 39566 # deaths per year
  text_y1=330
  text_y2=510
  text_space=60

  def __init__(self):
    self.img_bg = getImage("bg_murica")
    self.img_bg.load()
    self.wildwestfont = getFont("cowboys", 50)
    self.timefont = getFont("arialbold", 80)

  #  return 1
  def doRender(self, screen, **kwargs):
    screen.paste(self.img_bg)
    dt = kwargs["timestamp"]
    yearsofar = (datetime.datetime(dt.year,dt.month,dt.day,0,0,0) - datetime.datetime(dt.year,1,1,0,0,0)).total_seconds() / (365*24*3600)
    secondstoday = (dt.hour * 3600) + (dt.minute * 60) + (dt.second)

    datevalue = int(yearsofar * RendererMuricaClock.gundeathindex)

    timevalue = secondstoday * RendererMuricaClock.gundeathindex / 365 / 24 / 3600
    
    d = 64
    n = int((timevalue % 1) * 64)
    if n > 0:
      while not n%2:
        n = n/2
        d = d/2
    
    t1 = "Today Is:"
    s1 = "{0}".format(datevalue)
    t2 = "The Time Is:"
    if n == 0:
      s2 = "{0:.0f}".format(int(timevalue))
    else:
      s2 = "{0:.0f} & {1:.0f}/{2:.0f}".format(int(timevalue), n, d)
    
    print(s1)
    print(s2)

    d = ImageDraw.Draw(screen)
    
    tsz = self.wildwestfont.getsize(t1)
    d.text(((int(screen.size[0]-tsz[0])/2),self.text_y1),t1,fill=0x00,font=self.wildwestfont)

    tsz = self.timefont.getsize(s1)
    d.text(((int(screen.size[0]-tsz[0])/2),self.text_y1 + self.text_space),s1,fill=0x00,font=self.timefont)   

    tsz = self.wildwestfont.getsize(t2)
    d.text(((int(screen.size[0]-tsz[0])/2),self.text_y2),t2,fill=0x00,font=self.wildwestfont)

    tsz = self.timefont.getsize(s2)
    d.text(((int(screen.size[0]-tsz[0])/2),self.text_y2 + self.text_space),s2,fill=0x00,font=self.timefont)   

    return screen