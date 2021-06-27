from jjrenderer.renderer import *

class RendererTemplate(Renderer):
  def getName(self):
    return "template"
    # return "clock_template" # clocks should start with "clock" to be found by the app
  def getMenuItem(self):
    return {"icon":"default.png","text":"Template","description":""}
  #def getUpdateInterval(self): # typically 1 minute; only need this if overriding
  #  return 1
  def doRender(self, screen, **kwargs):
    screen = super().doRender(screen,**kwargs) # default (replace with yours!)
    return screen