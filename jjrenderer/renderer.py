from PIL import Image, ImageDraw, ImageFont, ImageOps
import glob
import os.path
import datetime
from pathlib import Path
import logging
from pyowm import OWM # weather api
import urllib.request # for downloading images/data

from jjcommon import owm_key

# directories to use
_localdir = os.path.dirname(os.path.realpath(__file__))
_fontpath = Path(_localdir).parent.joinpath("font").absolute()
_imgpath = Path(_localdir).parent.joinpath("img").absolute()

# open weather maps
_owm = OWM(owm_key)

# list of renderers
renderers = {}

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

def getImagePath(imagename):
  p = Path(_imgpath).joinpath(imagename).absolute()
  if not os.path.isfile(p):
    p = Path(_imgpath).joinpath(imagename + ".png").absolute()
    if not os.path.isfile(p):
      p = None
      logging.warning("could not find image " + imagename)
  return p

def getImage(imagename):
  p = getImagePath(imagename)
  if p:
    img = Image.open(p)
  else:
    img = None
  return img

#renderer base class
class Renderer:
  
  name = "default"
  isclock = False
  menuitem = {"text":"Default", "icon":"default.png", "description":""}
  updateinterval = 1

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