import jjrenderer.renderer as jjr
import random
import datetime
import logging

class RendererSurpriseClock(jjr.Renderer):

  name = "clock_surprise"
  isclock = True

  def __init__(self):
    self._lastpickdate = None
    self._currentrenderer = jjr.Renderer() # start with the default renderer. This should only be accessed here!
    self._clocklist = [] # list of clocks to pick from
    for cname, rclass in jjr.renderers.items():
      cname = str(cname).lower()
      if cname.startswith("clock_") and not cname == "clock_birthday": # only pick clocks; using class name
        self._clocklist.append(rclass)
    logging.debug("clocks being used by surprise clock: " + str(self._clocklist))

  def getName(self):
    return self.name
  def getMenuItem(self):
    return {"icon":"icon_surprise.png","text":"Surprise Me","description":"Picks a random clock every day. Enjoy them all!"}
  def getUpdateInterval(self): # typically 1 minute; only need this if overriding
    return self._currentrenderer.getUpdateInterval()

  def doRender(self, screen, **kwargs):
    # maybe pick a new one
    if "timestamp" in kwargs:
      thedate = datetime.datetime(kwargs["timestamp"]).date()
      if thedate > self._lastpickdate:
        # pick a new renderer
        rnd = random.randint(0, len(self._clocklist))
        self._currentrenderer = self._clocklist[rnd]() # instantiate new renderer
        self._lastpickdate = thedate
    # render using my captive renderer
    screen = self._currentrenderer.doRender(self, screen, **kwargs)
    return screen