from jjrenderer.renderer import *

import random
import importlib
import logging
import datetime
import jjrenderer.jjtimestring as ts

import pyowm # python open weather map - for local weather in EURRRROPE

class RendererEuroClock(Renderer):
  
  def getName(self):
    return "clock_euro"
  def getMenuItem(self):
    return {"icon":"eu.png","text":"Euro"}
  def doRender(self, screen, **kwargs):
    if len(styles) > 0:
      #r = random.randint(0,len(styles)-1) # select a random style
      r = 1
      return styles[r].doRender(self, screen, **kwargs) # pass the render down to the selected style
    else:
      return super().doRender(screen, **kwargs) # use default...
    
class _StyleFrench(RendererEuroClock):
  def doRender(self, screen, **kwargs):
  
    # get time-related text
    t = "Je ne connais pas l'heure"
    d = "Aujourd'hui"
    if "timestamp" in kwargs and kwargs["timestamp"]:
      t = ts.GetTimeString(kwargs["timestamp"], lang="fr")
      d = ts.GetDateString(kwargs["timestamp"], lang="fr").upper()
    logging.info("time: {0}, date: {1}".format(t,d))
    
    fill(screen)
    
    draw = ImageDraw.Draw(screen)
    pad = 50
    y = 200
    
    # logo
    logomaxheight = 200
    logomaxwidth = 800
    logo = getImage("logo_lemonde")
    s = 1.0
    if logo.size[1]/logo.size[0] > logomaxheight/logomaxwidth:
      s = logomaxheight/logo.size[1]
    else:
      s = logomaxwidth/logo.size[0]
    logo = logo.resize((int(logo.size[0]*s), int(logo.size[1]*s)),Image.ANTIALIAS)
    screen.paste(logo,(int(screen.size[0]/2 - logo.size[0]/2),y))
    y = y + logo.size[1] + pad
    
    # intermediate bar
    barheight = 120
    screen.paste(0x80, box=(100, y, screen.size[0]-100, y+barheight))
    dividers = 2
    ifont1 = getFont("arialnarrow",42)
    ifont2 = getFont("arialnarrowbold",42)
    itext1 = ["DERNIÈRES", "AFFAIRES", "LE MONDE"]
    itext2 = ["NOUVELLES", "EN COURS", "DES LIVRES"]
    itextheight = ifont1.getsize("X")[1]
    iy1 = int(y + (barheight-itextheight*2)/3)
    iy2 = int(y + itextheight + (barheight-itextheight*2)/3*2)
    for i in range(dividers+1):
      x = int(((screen.size[0]-200) / (dividers+1)) * (i)) + 100
      draw.text((x+20,iy1),itext1[i],font=ifont1,fill=0xFF)
      draw.text((x+20,iy2),itext2[i],font=ifont2,fill=0xFF)
      if i > 0:
        screen.paste(0xFF, box=(x-2,y+int(barheight*0.2),x+2,y+int(barheight*0.8)))
        
    y = y + barheight
    
    
    
    # date bar
    datefont = getFont("arialnarrowbold", 36)
    dsz = datefont.getsize(d)
    draw.text((100,y),d,font=datefont,fill=0x00)
    
    pricefont = getFont("arialnarrow", 36)
    p = "2,50€"
    draw.text((100+dsz[0]+50,y),p,font=pricefont,fill=0x00)
    
    w = "WWW.LEMONDE.FR"
    wsz = pricefont.getsize(w)
    draw.text((screen.size[0]-100-wsz[0],y),w,font=pricefont,fill=0x00)
    
    y = y + dsz[1] # + pad # seems to not need this
    
    # headline
    headlinemaxwidth = screen.size[0] - 200
    headlinefont = getFont("arialnarrow", 150)
    tsz = headlinefont.getsize(t)
    headlineimg = Image.new("L", tsz)
    fill(headlineimg)
    d2 = ImageDraw.Draw(headlineimg)
    d2.text((0,0),t,font=headlinefont,fill=0x00)
    if tsz[0] > headlinemaxwidth:
      headlineimg = headlineimg.resize((headlinemaxwidth, headlineimg.size[1]))
    screen.paste(headlineimg, (int(screen.size[0]/2 - headlineimg.size[0]/2),y))
    return screen

class _StyleEstonian(RendererEuroClock):

  def doRender(self, screen, **kwargs):

    bg = getImage("bg_postimees")
    screen.paste(bg)
    draw = ImageDraw.Draw(screen)
    
    # date bar
    d = ts.daystrings_et[kwargs["timestamp"].weekday()].upper()[0] + ", " + kwargs["timestamp"].strftime("%d.%m.%Y")
    datefont = getFont("arial", 15)
    dsz = datefont.getsize(d)
    draw.text((70,142),d,font=datefont,fill=0xFF)
    
    t = ts.GetTimeString(kwargs["timestamp"], lang="ee")
    print(t)
    
    # headline
    hl1font = getFont("arial", 18)
    # 255,368
    draw.text((255,365),t,font=hl1font,fill=0x00)
    hl2font = getFont("arial", 50)
    if len(t)>30 and " " in t:
      lines = ts.HalfAndHalf(t)
    else:
      lines = [t,]
    y = 480
    for l in lines:
      draw.text((72,y), l, font=hl2font, fill=0x00)
      y += 60

    # weather
    weatherfont = getFont("arialbold",15)
    weatherdata = getWeatherByCity("Tallinn", None)
    logging.debug(weatherdata.current)
    icon = getWeatherIcon(weatherdata.current.weather_icon_name).resize((30,30), Image.ANTIALIAS)
    screen.paste(icon, (194,136), icon)
    tt = "{0:.0f}° C".format(weatherdata.current.temperature()["temp"])
    draw.text((228, 142),tt,font=weatherfont,fill=0xFF)
    return screen

# automated luxury space communist style collection
styles = []
l = locals().copy()
for name, obj in l.items():
  if name.startswith("_Style"):
    styles.append(obj)
logging.debug("euro styles loaded: " + str(styles))