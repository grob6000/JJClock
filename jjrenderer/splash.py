from jjrenderer.renderer import *

class RendererSplash(Renderer):
  def getName(self):
    return "splash"
  def getMenuItem(self):
    return {"icon":"default.png","text":"Splash"}
  def doRender(self, screen, **kwargs):
    screen.paste(Image.open("./img/splash.png"))
    return screen