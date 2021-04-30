from jjrenderer.renderer import *

import random
import importlib
import logging

class RendererEuroClock(Renderer):
  
  def getName(self):
    return "clock_euro"
  def getMenuItem(self):
    return {"icon":"eu.png","text":"Euro"}
  def doRender(self, screen, **kwargs):
    if len(styles) > 0:
      r = random.randint(0,len(styles)-1) # select a random style
      return styles[r].doRender(self, screen, **kwargs) # pass the render down to the selected style
    else:
      return super().doRender(screen, **kwargs) # use default...
    
class _StyleFrench(RendererEuroClock):
  def doRender(self, screen, **kwargs):
    logging.info("Francois")
    fill(screen)
    return screen

# automated luxury space communist style collection
styles = []
l = locals().copy()
for name, obj in l.items():
  if name.startswith("_Style"):
    styles.append(obj)
logging.debug("euro styles loaded: " + str(styles))