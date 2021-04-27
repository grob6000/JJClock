from jjrenderer.renderer import *

class RendererBrexitClock(Renderer):
  def getName(self):
    return "clock_brexit"
  def getMenuItem(self):
    return {"icon":"brexit.png","text":"Brexit"}
  def doRender(self, screen, **kwargs):
    return super().doRender(screen,**kwargs)

if __name__ == "__main__":
  testRenderer(RendererBrexitClock)