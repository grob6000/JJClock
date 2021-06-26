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
    return {"icon":"icon_euro.png","text":"Euro","description":"One for every country in the union. Eventually..."}
  def doRender(self, screen, **kwargs):
    if len(styles) > 0:
      r = random.randint(0,len(styles)-1) # select a random style
      #r = len(styles)-1
      return styles[r].doRender(self, screen, **kwargs) # pass the render down to the selected style
    else:
      return super().doRender(screen, **kwargs) # use default...

# proposed style list:
    #Austria / Kleine Zeitung
#Belgium / Gazet Van Antwerpen
#Bulgaria / Trud
#Croatia / Novi List
#Cyprus / Alithia
#Czechia / Lidove Noviny
#Denmark / Politiken
    #Estonia / Postimees
#Finland / Helsingin Sanomat
    #France / Le Monde
    #Germany / Bild
#Greece / Estia
#Hungary
#Ireland	
#Italy / Corriere Della Sera
#Latvia
#Lithuania
#Luxembourg
#Malta
#Netherlands
#Poland
#Portugal
#Romania
#Slovakia
#Slovenia
#Spain / El Pais
#Sweden

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
    icon = None
    if weatherdata:
      logging.debug(weatherdata.current)
      icon = getWeatherIcon(weatherdata.current.weather_icon_name).resize((30,30), Image.ANTIALIAS)
      tt = "{0:.0f}° C".format(weatherdata.current.temperature()["temp"])
    else:
      tt = "15° C" # dummy value if no connection
    if icon: # only paste icon if we got one
      screen.paste(icon, (194,136), icon)
    draw.text((228, 142),tt,font=weatherfont,fill=0xFF)
    return screen

class _StyleAustrian(RendererEuroClock):
  def doRender(self, screen, **kwargs):
    
    fill(screen)

    # box for logo
    w = int(screen.size[0] * 0.80)
    h = int(647 / 1280 * w)
    x0 = int((screen.size[0]-w)/2)
    y0 = int((screen.size[1]-h)/2)
    screen.paste(0x44, box=(x0,y0,x0+w,y0+h))

    # text
    th = int(208/647*h)
    tw = int(1123/1280*w)
    tpad = int(57/647*h)
    tx0 = int((screen.size[0]-tw)/2)
    ty0 = y0 + int((h-(2*th)-tpad)/2)
    t = ts.GetTimeString(kwargs["timestamp"], lang="de")
    lines = ts.HalfAndHalf(t)
    fonts = (getFont("arialblack", 200), getFont("arialnarrow", 200))
    for i in [0,1]:
      l = lines[i].upper()
      tsz = fonts[i].getsize(l)
      yoff = fonts[i].getoffset(l)[1]
      img = Image.new("L", tsz)
      d = ImageDraw.Draw(img)
      d.text((0,0),l,font=fonts[i],fill=0xFF)
      img = img.crop((0, yoff, img.size[0], img.size[1]))
      img = img.resize((tw, th), Image.ANTIALIAS)
      screen.paste(img, (tx0,ty0+i*(th+tpad)), mask=img)

    return screen

class _StyleGerman(RendererEuroClock):
  def doRender(self, screen, **kwargs):

    img = Image.new("L", (1000,1100)) # do this at a fixed res then resize at the end
    fill(img, 0x53)
    ns = [kwargs["timestamp"].hour//10, kwargs["timestamp"].hour%10, kwargs["timestamp"].minute//10, kwargs["timestamp"].minute%10]
    mapimg = getImage("map_bildfont")
    x = 115
    y0 = 115
    for n in ns:
      cimg = mapimg.crop((n*170,0,(n+1)*170,mapimg.size[1]))
      img.paste(cimg, (x,y0))
      x += 200
    s = "unabhängig - überparteilich".upper()
    font = getFont("arialblack", 80)
    tsz = font.getsize(s)
    ti = Image.new("L", tsz)
    d = ImageDraw.Draw(ti)
    d.text((0,0),s,font=font,fill=0xFF)
    ti = ti.resize((1000-230, 60), Image.ANTIALIAS)
    img.paste(ti, (115, 950), mask=ti)
    
    # blit this onto the screen
    fill(screen)
    h = int(screen.size[1]*0.5)
    w = int(h/img.size[1]*img.size[0])
    x0 = int((screen.size[0]-w)/2)
    y0 = int((screen.size[1]-h)/2)
    screen.paste(img.resize((w,h), Image.ANTIALIAS), (x0,y0))
    
    # date
    s = "{0},{1}.{2} {3}".format(ts.daystrings_de[kwargs["timestamp"].weekday()], kwargs["timestamp"].day, ts.monthstrings_de[kwargs["timestamp"].month-1], kwargs["timestamp"].year).upper()
    datefont = getFont("arialbold",100)
    dsz = datefont.getsize(s)
    di = Image.new("L", dsz)
    fill(di)
    d = ImageDraw.Draw(di)
    d.text((0,0),s,font=datefont,fill=0x53)
    di = di.resize((w, int(w/10)))
    screen.paste(di, (x0, y0 - int(di.size[1]*1.3)))

    # barcode
    y1 = y0 + h + int(h*0.05)
    barcode = getImage("barcode")
    screen.paste(barcode, (x0+w-barcode.size[0], y1))

    # price
    draw = ImageDraw.Draw(screen)
    pricefont = getFont("arialbold", 20)
    draw.text((x0, y1), "1.00 EURO 44/8", font=pricefont, fill=0x00)
    draw.text((x0, y1 + int(h/10)), "www.bild.de", font=pricefont, fill=0x00)

    return screen

       

# automated luxury space communist style collection
styles = []
l = locals().copy()
for name, obj in l.items():
  if name.startswith("_Style"):
    styles.append(obj)
logging.debug("euro styles loaded: " + str(styles))