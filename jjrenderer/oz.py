from jjrenderer.renderer import *
import jjrenderer.jjtimestring as ts
import random
import logging

class RendererOzClock(Renderer):

  name = "clock_oz"
  isclock = True
  menuitem = {"icon":"icon_oz.png","text":"Oz", "description":"AUSSIE AUSSIE AUSSIE! OI OI OI!" }
  updateinterval = 5

  def doRender(self, screen, **kwargs):
    if "timestamp" in kwargs and kwargs["timestamp"]:
      kwargs["tstring"] = ts.GetTimeString(kwargs["timestamp"], lang="en_oz")
      kwargs["dstring"] = ts.GetDateString(kwargs["timestamp"], lang="en", includeday=True)
    else:
      kwargs["tstring"] = "No bloody idea mate"
      kwargs["dstring"] = "Today"
    if len(styles) > 0:
      r = random.randint(0,len(styles)-1) # select a random style
      #r = 4
      return styles[r].doRender(self, screen, **kwargs) # pass the render down to the selected style
    else:
      return super().doRender(screen, **kwargs) # use default...

class _StyleAustralian(RendererOzClock):
  def doRender(self, screen, **kwargs):
    bg = getImage("bg_theaustralian")
    screen.paste(bg)
    draw = ImageDraw.Draw(screen)
    datefont = getFont("timesbold", 12)

    # dateline
    x = 1357
    y = 158
    wd = ts.GetDayOfWeek(kwargs["timestamp"]).upper()
    sz = datefont.getsize(wd)
    draw.text((x-sz[0],y), wd, font=datefont, fill=0x00)
    ds = "{0} {1}, {2}".format(ts.monthstrings_en[kwargs["timestamp"].month].title(), kwargs["timestamp"].day, kwargs["timestamp"].year)
    y = 170
    sz = datefont.getsize(ds)
    draw.text((x-sz[0],y), ds, font=datefont, fill=0x00)
    
    # time headline
    blockHeadline(screen, bbox=(53, 400, 523, 691), text=kwargs["tstring"], pad=0, fontname="timesbold")
    
    # smaller heading today's date
    x = 555
    y = 383
    subheadfont = getFont("timesbold", 48)
    draw.text((x,y),"Today is " + kwargs["dstring"],font=subheadfont,fill=0x00)
    
    # random ozzie image
    plonkImage(screen, (554, 448, 1167, 1050), getImage("oz_*"))

    return screen   

 
    
# automated luxury space communist style collection
styles = []
l = locals().copy()
for name, obj in l.items():
  if name.startswith("_Style"):
    styles.append(obj)
logging.debug("oz styles loaded: " + str(styles))