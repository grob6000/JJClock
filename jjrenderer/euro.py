from jjrenderer.renderer import *

import random
import importlib

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
    print("Francois")
    fill(screen)
    return screen

# automated luxury space communist style collection
styles = []
l = locals().copy()
for name, obj in l.items():
  if name.startswith("_Style"):
    styles.append(obj)
print(styles)

if __name__ == "__main__":
  testRenderer(RendererEuroClock)