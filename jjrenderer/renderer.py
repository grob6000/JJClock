from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageColor
import glob
import os.path
import datetime
from pathlib import Path
import logging
from pyowm import OWM # weather api
import urllib.request # for downloading images/data
from random import randint

from jjcommon import owm_key
import jjrenderer.jjtimestring as ts

import settings

# directories to use
_localdir = os.path.dirname(os.path.realpath(__file__))
_fontpath = Path(_localdir).parent.joinpath("font").absolute()
_imgpath = Path(_localdir).parent.joinpath("img").absolute()

_owm = None

# list of renderers
renderers = {}


def openowm():
  """Initialise Open Weather Maps API"""
  global _owm
  if not _owm:
    _owm = OWM(settings.getSettingValue("owmkey"))

def getWeatherByCity(city, country):
  """Use Open Weather Maps to get weather by name of city and country.
  
  Keyword Arguments:
  city -- string, city name (REQUIRED)
  country -- string, country name (REQUIRED)

  Returns:
  dict containing owm one_call data if successful.
  Returns None if not successful
  See https://openweathermap.org/api/one-call-api
  """
# open weather maps
  global _owm
  if not _owm:
    openowm()
  reg = _owm.city_id_registry()
  locs = reg.locations_for(city, country=country)
  if len(locs)>0:
    return getWeatherByLoc(locs[0].lat, locs[0].lon)
  else:
    logging.debug("No weather results for city={0}, country={1}".format(city,country))
    return None

def getWeatherByLoc(lat=0,lon=0):
  """Use Open Weather Maps to get weather by GPS coordinates.

  Keyword Arguments:
  lat -- latitude in degrees (default: 0)
  lon -- longitude in degrees (default: 0)

  Returns:
  dict containing owm one_call data if successful.
  Returns None if not successful

  See https://openweathermap.org/api/one-call-api  
  """
  global _owm
  if not _owm:
    openowm()
  mgr = _owm.weather_manager()
  try:
    one_call = mgr.one_call(lat=lat, lon=lon, units="metric")
  except:
    logging.warning("Error obtaining weather for lat={0} lon={1}".format(lat, lon))
    one_call = None
  return one_call

def getWeatherIcon(wicon):
  """Gets the Open Weather Maps standard icon using "icon" value.

  Keyword Arguments:
  wicon -- string, "icon" field returned by OWM API

  Returns:
  PIL image object containing the icon

  See https://openweathermap.org/weather-conditions
  """
  img = None
  try:
    img = getImage("owmico_{0}.png".format(wicon))
  except:
    urllib.request.urlretrieve("http://openweathermap.org/img/wn/{0}.png".format(wicon), os.path.join(_imgpath, "owmico_{0}.png".format(wicon)))
    try:
      img = getImage("owmico_{0}.png".format(wicon))
    except:
      logging.warning("OWM icon was not found and could not be downloaded. Using default.")
      img = getImage("owmico_default") # this is definitely there
  return img

def fill(img, color=0xFF):
  """Fills image with specified colour (default white).
  
  Keyword Arguments:
  img -- PIL image object to be filled
  color -- colour to fill (default = 0xFF (white for mode L))
  
  Returns:
  PIL image object modified"""
  img.paste(color, box=(0,0,img.size[0],img.size[1]))
  return img

def getFont(fontname="ebgaramondmedium", fontsize=24):
  """Finds and loads a font from the font folder.
  
  Keyword Arguments:
  fontname -- string, basename (filename with no extension) of font to load (default = "ebgaramondmedium")
  fontsize -- int, size of font in pt (default = 24)

  Returns:
  If found, PIL ImageFont object as specified
  If not found, returns default font in size specified
  """
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
      fnt = getFont(fontsize=fontsize) # return default
  return fnt

def getImagePath(imagename):
  """Gets the full path of an image; if no extension specified looks for a png.
  Can use wildcards; if multiple matches found will pick at random.
  
  Keyword Arguments:
  imagename -- name of image to find, can be filename or basename (i.e. with no extension) (REQUIRED)

  Returns:
  Path object
  """  
  p = Path(_imgpath).joinpath(imagename).absolute()
  if not os.path.isfile(p):
    p = Path(_imgpath).joinpath(imagename + ".png").absolute()
    if not os.path.isfile(p):
      plist = glob.glob(pathname=imagename+".*",root_dir=_imgpath)
      if len(plist) == 0:
        p = None
        logging.warning("could not find image " + imagename)
      else:
        p = Path(_imgpath).joinpath(plist[randint(0,len(plist)-1)]).absolute() # pick a random from glob; allows using wildcard to select a random image
  return p

def getImage(imagename):
  """Opens the PIL image by name, lookup using getImagePath().
  
  Keyword Arguments:
  imagename -- name of image to find, can be filename or basename (i.e. with no extension) (REQUIRED)

  Returns:
  PIL Image object (not this will be lazily loaded; will only read file when used)"""
  p = getImagePath(imagename)
  if p:
    img = Image.open(p)
  else:
    img = None
  return img

def plonkImage(screen, bbox, img):
  """Plonk img on screen in bbox. Resizes until one dimension is matched, then crops to center of image.
  
  Keyword Arguments:
  screen -- screen/image to paste onto (REQUIRED)
  bbox -- integer rectangle, coordinates on screen to paste into (x0, y0, x1, y1) (REQUIRED)
  img -- image to plonk

  Returns:
   
  Nothing"""
  #bbox = (554, 448, 1167, 1050)
  bbox_sz = (bbox[2]-bbox[0],bbox[3]-bbox[1])
  #ozimg = getImage("oz_*")
  s = max(float(bbox_sz[0]) / float(img.width), float(bbox_sz[1]) / float(img.height))*1.02
  img = img.resize((int(img.width * s), int(img.height * s)), Image.ANTIALIAS)
  x0 = int((img.width-bbox_sz[0])/2.0)
  y0 = int((img.height-bbox_sz[1])/2.0)
  ozimg = img.crop( ( x0, y0, x0+bbox_sz[0], y0+bbox_sz[1] ) )
  screen.paste(ozimg, (bbox[0], bbox[1]))

def blockHeadline(screen, bbox, text, nlines=None, charsperline=20, fontname="arialbold", bgcolor=0xFF, textcolor=0x00, pad=20):
  # time headline
  lines = [text]
  hmax = bbox[3]-bbox[1]
  if nlines == None:
    nlines = int(len(text)/charsperline)+1
  lines = ts.SplitSentence(text,nlines)
  hmax = int((bbox[3]-bbox[1]-(pad*(nlines-1)))/nlines)
  logging.debug(lines)
  headlinefont = getFont(fontname, 200)
  y = bbox[1]
  ascent, descent = headlinefont.getmetrics()
  for n in range(0,nlines):
    l = lines[n]
    if len(l)>0:
      tsz = (headlinefont.getsize(l)[0], ascent+descent)
      img = Image.new("L", tsz)
      fill(img, color=bgcolor)
      hd = ImageDraw.Draw(img)
      hd.text((0,0),l,font=headlinefont,fill=textcolor)
      img = img.crop((0,headlinefont.getoffset(l)[1],img.size[0],img.size[1]))
      s = min((bbox[2]-bbox[0])/img.size[0], hmax/img.size[1])
      #print(s)
      img = img.resize((int(img.size[0]*s), hmax), Image.ANTIALIAS)
      screen.paste(img, (bbox[0], y), mask=ImageOps.invert(img))
      y = y + hmax + pad  

#renderer base class
class Renderer:
  """Generic Renderer, to be inherited by all other renderers.
  
  Instance Variables:
  name -- the unique name of the renderer used as menu and mode. Please start clocks with "clock_" by convention.
  isclock -- boolean, True if this is a clock (will be shown in menu, and updated with time change when active), False otherwise
  menuitem -- dict, providing data to generate a menu entry. Must contain fields:
    "text" -- string, friendly name to display
    "icon" -- string, name of icon to use (see getImage()). should start with 'icon_' by convention
    "description" -- string, additional description to show when using web interface
  updateinterval -- time (in minutes) between updates. Some clocks are better updated less frequently! Default should be 1.

  Methods:
  doRender -- receives a PIL image 'screen' and other arguments (as kwargs) to render a face. Should return the image object after drawing etc.
  """
  name = "default"
  isclock = False
  menuitem = {"text":"Default", "icon":"icon_default.png", "description":""}
  updateinterval = 1

  def doRender(self, screen, **kwargs):
    """Takes an image, renders things onto it (perhaps using info from other kwargs), and returns the modified image.
  
    Keyword Arguments:
    screen -- PIL Image object, to render onto (REQUIRED)

    Returns:
    PIL Image object"""
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

