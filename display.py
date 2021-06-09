from PIL import Image
from threading import Lock, Thread, Event
import sys
if "linux" in sys.platform:
  from IT8951.display import AutoEPDDisplay
  from IT8951 import constants
import logging
import pygame
import time
import jjrenderer
import datetime

class DisplayManager:
  
  _fillcolor = 255
  
  def __init__(self, size=(1400,1050)):
    self._screenlock = Lock()
    with self._screenlock:
      self._screen = Image.new("L", size)
    self.displaylist = []
  
  def doRender(self, renderer=None, **kwargs):
    self._screen.paste(DisplayManager._fillcolor, box=(0,0,self._screen.size[0],self._screen.size[1]))
    self._screen = renderer.doRender(self._screen, **kwargs)
    for d in self.displaylist:
      if isinstance(d, Display):
        d.displayImage(img=self._screen)
  
  def getScreen(self):
    with self._screenlock:
      img = self._screen.copy()
    return img

  def getSize(self):
    with self._screenlock:
      sz = self._screen.size
    return sz


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
    try:
      self._epddisplay = AutoEPDDisplay(vcom=vcom)
    except:
      logging.warning("EPD Display failed to init; will not function")
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

class PygameDisplay(Display):
  
  displayfillcolor = (255, 255 ,255)

  def __init__(self, windowsize=(1024,768)):
    super().__init__()
    self._windowsize = windowsize
    self._pygamethread = Thread(target=self._run, daemon=True)
    self._pygamethread.start()
    self._updateevent = Event()
    self._stopevent = Event()
    self._imglock = Lock()
    self._img = None
  
  def displayImage(self, img=None):
    if img and self._pygamethread.is_alive(): # only if pygame is running
      with self._imglock:
        self._img = img # swap the image
      self._updateevent.set() # signal to pygame to update the screen
  
  def getSize(self):
    return self._windowsize
  
  def __del__(self):
    logging.debug("pygamedisplay __del__")
    self._stopevent.set()
    self._pygamethread.join() # wait for close of thread

  def _run(self):
    logging.debug("pygame thread start")
    pygame.init()
    surf = pygame.display.set_mode(self._windowsize)

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
      for event in pygame.event.get():
        if event.type == pygame.QUIT:
          pygame.quit()
          self._stopevent.set()
    logging.info("pygame thread quit")

## TEST SCRIPT ##
if __name__ == "__main__":
  print("DISPLAY TEST")
  logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
  dm = DisplayManager()
  pgd = PygameDisplay(dm.getSize())
  dm.displaylist.append(pgd)
  r = jjrenderer.renderers["RendererBrexitClock"]()
  while True:
    dm.doRender(r, timestamp=datetime.datetime.now())
    time.sleep(5)
        