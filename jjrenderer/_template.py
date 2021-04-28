from jjrenderer.renderer import *

class RendererTemplate(Renderer):
  def getName(self):
    return "template"
  def getMenuItem(self):
    return {"icon":"default.png","text":"Template"}
  def doRender(self, screen, **kwargs):
    return super().doRender(screen,**kwargs)