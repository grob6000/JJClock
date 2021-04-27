from renderer import *

class RendererSplash(Renderer):
  def getName(self):
    return "splash"
  def getMenuItem(self):
    return {"icon":"default.png","text":"Splash"}
  def doRender(self, screen, **kwargs):
    screen.paste(Image.open("./img/splash.png"))

if __name__ == "__main__":
  testRenderer(RendererTemplate)

def RendererSplash(jjrenderer.Renderer):
  def getName(self):
    return "splash"
  def doRender(self, screen, **kwargs):
    screen.paste(getImage("splash.png"))
    return screen  