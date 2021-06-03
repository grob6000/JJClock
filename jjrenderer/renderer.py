from PIL import Image, ImageDraw, ImageFont, ImageOps
import glob
import os.path
import datetime
from pathlib import Path
import logging
from pyowm import OWM # weather api
import urllib.request # for downloading images/data

from jjcommon import owm_key

_localdir = os.path.dirname(os.path.realpath(__file__))
_fontpath = Path(_localdir).parent.joinpath("font").absolute()
_imgpath = Path(_localdir).parent.joinpath("img").absolute()

_owm = OWM(owm_key)

def getWeatherByCity(city, country):
  reg = _owm.city_id_registry()
  locs = reg.locations_for(city, country=country)
  if len(locs)>0:
    return getWeatherByLoc(locs[0].lat, locs[0].lon)
  else:
    logging.debug("No weather results for city={0}, country={1}".format(city,country))
    return None

def getWeatherByLoc(lat=0,lon=0):
  mgr = _owm.weather_manager()
  try:
    one_call = mgr.one_call(lat=lat, lon=lon, units="metric")
  except:
    logging.warning("Error obtaining weather for lat={0} lon={1}".format(lat, lon))
    one_call = None
  return one_call

def getWeatherIcon(wicon):
  p = os.path.join(_imgpath, "owmico_{0}.png".format(wicon))
  if not os.path.isfile(p):
    logging.debug("icon {0} not present, downloading from open weather maps".format(wicon))
    urllib.request.urlretrieve("http://openweathermap.org/img/wn/{0}.png".format(wicon), os.path.join(_imgpath, "owmico_{0}.png".format(wicon)))
  img = getImage("owmico_{0}".format(wicon)) # cached icon
  return img

def fill(img, color=0xFF):
  img.paste(color, box=(0,0,img.size[0],img.size[1]))
  return img

def getFont(fontname="ebgaramondmedium", fontsize=24):
  #print(_fontpath)
  fnt = None
  try:
    fnt = ImageFont.truetype(os.path.join(_fontpath, fontname + ".ttf"), fontsize)
  except OSError:
    logging.debug("did not find ttf font, trying otf")
  if not fnt:
    try:
      fnt = ImageFont.truetype(os.path.join(_fontpath, fontname + ".otf"), fontsize)
    except OSError:
      logging.debug("did not find otf font")
      fnt = getFont() # return default
  return fnt
  
def getImage(imagename):
  p = Path(_imgpath).joinpath(imagename).absolute()
  if os.path.isfile(p):
    return Image.open(p)
  p = Path(_imgpath).joinpath(imagename + ".png").absolute()
  if os.path.isfile(p):
    return Image.open(p)
  else:
    raise FileNotFoundError("Image file could not be found: " + imagename)

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