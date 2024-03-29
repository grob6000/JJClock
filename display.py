from PIL import Image
from threading import Lock, Thread, Event
from queue import Queue
import sys

from psutil import virtual_memory
if "linux" in sys.platform:
  from IT8951.display import AutoEPDDisplay
  from IT8951 import constants
import pygame
import time
import jjrenderer
import datetime
from hashlib import md5

import jjlogger
import inputmanager

logger = jjlogger.getLogger(__name__)

class DisplayManager:
  
  _fillcolor = 255

  def __init__(self, size=(1400,1050)):
    self._screen = Image.new("L", size)
    self.displaylist = []
  
  def doRender(self, renderer=None, **kwargs):
    self._screen.paste(DisplayManager._fillcolor, box=(0,0,self._screen.size[0],self._screen.size[1]))
    self._screen = renderer.doRender(self._screen, **kwargs)
    for d in self.displaylist:
      if isinstance(d, Display):
        d.displayImage(img=self._screen)

  def getSize(self):
    return self._screen.size


class Display():
  
  def __init__(self):
    self.cropbox = None
    self.resize = False

  def getSize(self):
    return None # virtual display has no size!

  def displayImage(self, img=None):
    pass # a virtual display will do nothing with the image

  def _rebox(self, img):
    sz = self.getSize()
    box = (0,0,sz[0],sz[1])
    if self.cropbox:
      box = self.cropbox
    if self.resize:
      img2 = img.resize((box[2]-box[0],box[3]-box[1])) # resize image to fit in cropbox
    else:
      img2 = img.crop((0,0,box[2]-box[0],box[3]-box[1])) # crop image to fit in cropbox
    return img2
  
  def _getorigin(self):
    if self.cropbox:
      return (self.cropbox[0], self.cropbox[1])
    else:
      return (0,0)

class EPDDisplay(Display):

  def __init__(self, vcom=-2.55):
    super().__init__()
    self.vcom = vcom
    self.connect()
  
  def disconnect(self):
    del self._epddisplay
    self._epddisplay = None

  def connect(self):
    try:
      self._epddisplay = AutoEPDDisplay(vcom=self.vcom)
    except IOError:
      logger.warning("EPD Display failed to init; will not function")
      self._epddisplay = None   

  def getSize(self):
    if self._epddisplay:
      return (self._epddisplay.width, self._epddisplay.height)
    else:
      return None
  
  def displayImage(self, img=None):
    if img and self._epddisplay:
      self._epddisplay.frame_buf.paste(self._rebox(img), self._getorigin()) # paste image as per the cropbox
      self._epddisplay.draw_full(constants.DisplayModes.GC16) # display update

  def isopen(self):
    return bool(self._epddisplay)

class PygameDisplay(Display, inputmanager.InputDevice):
  
  displayfillcolor = (255, 255 ,255)

  def __init__(self, windowsize=(1024,768), start=True):
    super().__init__()
    self._windowsize = windowsize
    self._pygamethread = Thread(target=self._run, daemon=True)
    if start:
      self._pygamethread.start()
    self._updateevent = Event()
    self._stopevent = Event()
    self._imglock = Lock()
    self._img = None
    #self.buttonevent = Event()
    self.actionqueue = Queue()
  
  def displayImage(self, img=None):
    if img and self._pygamethread.is_alive(): # only if pygame is running
      with self._imglock:
        self._img = img # swap the image
      self._updateevent.set() # signal to pygame to update the screen
  
  def getSize(self):
    return self._windowsize

  def restart(self):
    self.stop()
    self._pygamethread.start()
  
  def stop(self):
    if self._pygamethread.is_alive():
      self._stopevent.set()
      self._pygamethread.join()  
  
  def __exit__(self):
    self.stop()

  def _run(self):
    logger.debug("pygame thread start")
    pygame.display.init() # display only
    surf = pygame.display.set_mode((0,0), pygame.FULLSCREEN)
    sz_surf = surf.get_size()
    scale = min(sz_surf[0]/self._windowsize[0], sz_surf[1]/self._windowsize[1])
    boxsize = (int(scale * self._windowsize[0]), int(scale * self._windowsize[1]))
    x0 = int((sz_surf[0]-boxsize[0])/2)
    y0 = int((sz_surf[1]-boxsize[1])/2)
    self.cropbox = (x0,y0,x0+boxsize[0],y0+boxsize[1])
    pygame.fastevent.init()
    pygame.mouse.set_visible(0)

    while not self._stopevent.is_set():
      if self._updateevent.is_set():
        surf.fill(PygameDisplay.displayfillcolor)
        with self._imglock:
          i = self._rebox(self._img)
        raw_str = i.convert('RGB').tobytes("raw", 'RGB')
        s = pygame.image.fromstring(raw_str, i.size, 'RGB')
        surf.blit(s, self._getorigin())
        pygame.display.flip()
        self._updateevent.clear()
      time.sleep(0.1) # limit loop frequency / encourage other threads to run!
      for event in pygame.fastevent.get():
        if event.type == pygame.QUIT:
          pygame.quit()
          self._stopevent.set()
        if event.type == pygame.MOUSEBUTTONUP:
          if event.button == pygame.BUTTON_LEFT:
            #self.buttonevent.set()
            self.actionqueue.put(inputmanager.InputEvent(inputmanager.ACTION_CLICK))
    pygame.display.quit()
    logger.info("pygame thread quit")
  
  def isrunning(self):
    return self._pygamethread.is_alive()

  def open(self):
    self.restart()
  
  def close(self):
    self.stop()
  
  def isopen(self):
    return self.isrunning()

# display stored in memory only - ideal for web
# threadsafe access to image (locked & copies buffer)
# handles conversion & resizing for a particular target
# provides a hash of the display content for polling purposes
class MemoryDisplay(Display):

  def __init__(self, size=(800,600)):
    super().__init__()
    self._screenlock = Lock()
    self._hashlock = Lock()
    self._screen = None
    with self._screenlock:
      self._screen = Image.new("RGB", size)
    self._hash = ""
    self._updateHash()
  
  def _updateHash(self):
    self._hash = md5(self._screen.tobytes()).hexdigest() # string is immutable, need not copy or lock

  def getHash(self):
    return self._hash # string is immutable; need not copy or lock

  def getSize(self):
    sz = None
    with self._screenlock:
      if self._screen:
        sz = self._screen.size
    return sz
  
  def displayImage(self, img=None):
    if img:
      img2 = self._rebox(img.convert("RGB"))
      with self._screenlock:
        self._screen.paste(img2,box=self.cropbox)
      self._updateHash()
      
  
  def getImage(self):
    img = None
    with self._screenlock:
      if self._screen:
        img = self._screen.copy()
    logger.debug(img)
    return img

## TEST SCRIPT ##
if __name__ == "__main__":
  print("DISPLAY TEST")
  logger.basicConfig(stream=sys.stdout, level=logger.DEBUG)
  dm = DisplayManager()
  pgd = PygameDisplay(dm.getSize())
  dm.displaylist.append(pgd)
  r = jjrenderer.renderers["RendererBrexitClock"]()
  while True:
    dm.doRender(r, timestamp=datetime.datetime.now())
    time.sleep(5)
        
      