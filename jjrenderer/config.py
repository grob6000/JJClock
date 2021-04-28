from jjrenderer.renderer import *

class RendererConfig(Renderer):
  def getName(self):
    return "config"
  def getMenuItem(self):
    return {"icon":"config.png","text":"Configuration"}
  def doRender(self, screen, **kwargs):
    return super().doRender(screen,**kwargs)