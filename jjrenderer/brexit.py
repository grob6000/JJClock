from jjrenderer.renderer import *
import jjrenderer.jjtimestring as ts
import random
import logging
import datetime


class RendererBrexitClock(Renderer):
  def getName(self):
    return "clock_brexit"
  def getMenuItem(self):
    return {"icon":"brexit.png","text":"Brexit"}
  def doRender(self, screen, **kwargs):
    if "timestamp" in kwargs and kwargs["timestamp"]:
      kwargs["tstring"] = ts.GetTimeString(kwargs["timestamp"], lang="en_idiomatic")
      #kwargs["dstring"] = ts.GetDateString(kwargs["timestamp"], lang="en", includeday=True)
    else:
      kwargs["tstring"] = "No bloody idea mate"
      kwargs["dstring"] = "Today"
    if len(styles) > 0:
      #r = random.randint(0,len(styles)-1) # select a random style
      r = 2
      return styles[r].doRender(self, screen, **kwargs) # pass the render down to the selected style
    else:
      return super().doRender(screen, **kwargs) # use default...

class _StyleSun(RendererBrexitClock):
  def doRender(self, screen, **kwargs):
    bg = getImage("bg_thesun")
    screen.paste(bg)
    draw = ImageDraw.Draw(screen)
    datefont = getFont("arial", 32)
    # dateline
    x = 84
    y = 320
    d = ts.GetDateString(kwargs["timestamp"], lang="en", includeday=True)
    #dsz = datefont.getsize(d)
    draw.text((x,y), d, font=datefont, fill=0xFF)
    # web address (matching date)
    w = "thesun.co.uk"
    wsz = datefont.getsize(w)
    draw.text((750-wsz[0],y), w, font=datefont, fill=0xFF)
    
    # time headline
    bgcolor = 0x00
    textcolor = 0xFF
    pad = 20
    bbox = (250+pad, 585+pad, 250+1088-pad, screen.size[1]-pad)
    T = kwargs["tstring"].upper()
    lines = [T, ""]
    hmax = bbox[3]-bbox[1]    
    if len(T)>10 and " " in T:
      lines = ts.HalfAndHalf(T)
      hmax = int((bbox[3]-bbox[1]-pad)/2)
    logging.debug(lines)
    headlinefont = getFont("arialblack", 200)
    y = bbox[1]
    for l in lines:
      if len(l)>0:
        tsz = headlinefont.getsize(l)
        img = Image.new("L", tsz)
        fill(img, color=bgcolor)
        hd = ImageDraw.Draw(img)
        hd.text((0,0),l,font=headlinefont,fill=textcolor)
        img = img.crop((0,headlinefont.getoffset(l)[1],img.size[0],img.size[1]))
        s = min((bbox[2]-bbox[0])/img.size[0], hmax/img.size[1])
        print(s)
        img = img.resize((int(img.size[0]*s), hmax), Image.ANTIALIAS)
        screen.paste(img, (int((bbox[0]+bbox[2]-img.size[0])/2), y))
        y = y + hmax + pad
        
    return screen    

class _StyleMirror(RendererBrexitClock):
  def doRender(self, screen, **kwargs):
    bg = getImage("bg_mirror")
    screen.paste(bg)
    draw = ImageDraw.Draw(screen)
    datefont = getFont("arial", 18)
    # dateline
    x = 520
    y = 97
    d = ts.GetDateString(kwargs["timestamp"], lang="en", includeday=True)
    #dsz = datefont.getsize(d)
    draw.text((x,y), d, font=datefont, fill=0xB0)
    
    # time headline
    bgcolor = 0xFF
    textcolor = 0x00
    pad = 20
    bbox = (65, 425, 65+908, 425+557)
    T = kwargs["tstring"].upper()
    lines = [T, ""]
    hmax = bbox[3]-bbox[1]    
    if len(T)>10 and " " in T:
      lines = ts.HalfAndHalf(T)
      hmax = int((bbox[3]-bbox[1]-pad)/2)
    logging.debug(lines)
    headlinefont = getFont("arialblack", 200)
    y = bbox[1]
    for l in lines:
      if len(l)>0:
        tsz = headlinefont.getsize(l)
        img = Image.new("L", tsz)
        fill(img, color=bgcolor)
        hd = ImageDraw.Draw(img)
        hd.text((0,0),l,font=headlinefont,fill=textcolor)
        img = img.crop((0,headlinefont.getoffset(l)[1],img.size[0],img.size[1]))
        s = min((bbox[2]-bbox[0])/img.size[0], hmax/img.size[1])
        #print(s)
        img = img.resize((int(img.size[0]*s), hmax), Image.ANTIALIAS)
        screen.paste(img, (int((bbox[0]+bbox[2]-img.size[0])/2), y), mask=ImageOps.invert(img))
        y = y + hmax + pad
    
    # bong bong bong
    h = kwargs["timestamp"].hour % 12
    if h == 0:
      h = 12
    y0 = 844
    x = 1025
    bongfont = getFont("arial", 22)
    for bl in range(0, int(h/4)+1):
      bt = "BONG " * min(h-(bl*4),4)
      draw.text((x,y0 + bl*40), bt, font=bongfont, fill=0x00)
    
    return screen    

class _StyleDailyMail(RendererBrexitClock):
  def doRender(self, screen, **kwargs):
    bg = getImage("bg_dailymail")
    screen.paste(bg)
    draw = ImageDraw.Draw(screen)
    datefont = getFont("arial", 18)
    # dateline
    x = 83
    y = 384
    d = ts.GetDateString(kwargs["timestamp"], lang="en", includeday=True).upper()
    #dsz = datefont.getsize(d)
    draw.text((x,y), d, font=datefont, fill=0x00)

    # time headline
    bgcolor = 0x00
    textcolor = 0xFF
    bbox = (636+20, 438+20, 636+691-20, 438+361-20)
    pad = 50
    T = kwargs["tstring"].upper()
    lines = [T, ""]
    hmax = bbox[3]-bbox[1]    
    if len(T)>10 and " " in T:
      lines = ts.HalfAndHalf(T)
      hmax = int((bbox[3]-bbox[1]-pad)/2)
    logging.debug(lines)
    headlinefont = getFont("rockwellbold", 200)
    y = bbox[1]
    for l in lines:
      if len(l)>0:
        tsz = headlinefont.getsize(l)
        img = Image.new("L", tsz)
        fill(img, color=bgcolor)
        hd = ImageDraw.Draw(img)
        hd.text((0,0),l,font=headlinefont,fill=textcolor)
        img = img.crop((0,headlinefont.getoffset(l)[1],img.size[0],img.size[1]))
        s = min((bbox[2]-bbox[0])/img.size[0], hmax/img.size[1])
        #print(s)
        img = img.resize((int(img.size[0]*s), hmax), Image.ANTIALIAS)
        screen.paste(img, (int((bbox[0]+bbox[2]-img.size[0])/2), y), mask=img)
        y = y + hmax + pad
    
    return screen

        
# automated luxury space communist style collection
styles = []
l = locals().copy()
for name, obj in l.items():
  if name.startswith("_Style"):
    styles.append(obj)
logging.debug("brexit styles loaded: " + str(styles))