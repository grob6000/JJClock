import random
import logging

from jjrenderer.renderer import *

class RendererSurpriseClock(Renderer):

  name = "clock_surprise"
  isclock = True
  menuitem = {"icon":"icon_surprise.png","text":"Surprise Me","description":"Picks a random clock every day. Enjoy them all!"}
  updateinterval = 1

  def __init__(self):
    self._lastpickdate = None
    self._currentrenderer = Renderer() # start with the default renderer. This should only be accessed here!
    self._clocklist = [] # list of clocks to pick from
    for rclass in renderers.values():
      cname = str(rclass.name).lower()
      if cname.startswith("clock_") and not cname == "clock_birthday": # only pick clocks; using class name
        self._clocklist.append(rclass)
    logging.debug("clocks being used by surprise clock: " + str(self._clocklist))

  def doRender(self, screen, **kwargs):
    # maybe pick a new one
    if "timestamp" in kwargs:
      thedate = kwargs["timestamp"].date()
      if not self._lastpickdate or thedate > self._lastpickdate:
        # pick a new renderer
        rnd = random.randint(0, len(self._clocklist)-1)
        self._currentrenderer = self._clocklist[rnd]() # instantiate new renderer
        self.updateinterval = self._currentrenderer.updateinterval
        self._lastpickdate = thedate
        logging.info("surprise clock selected: " + self._currentrenderer.name)
    # render using my captive renderer
    screen = self._currentrenderer.doRender(screen, **kwargs)
    return screen