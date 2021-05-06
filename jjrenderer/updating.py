from jjrenderer.renderer import *

class RendererUpdating(Renderer):
  def getName(self):
    return "updating"
  def getMenuItem(self):
    return {"icon":"default.png","text":"Updating"}
  def doRender(self, screen, **kwargs):
    screen.paste(getImage("updating.png"))
    if "version" in kwargs:
      # put version on screen
      draw = ImageDraw.Draw(screen)
      fnt = getFont(fontsize=36)
      tsz = fnt.getsize(kwargs["version"])
      draw.text((screen.size[0]/2-tsz[0]/2, screen.size[1]/2-tsz[1]/2), kwargs["version"], font=fnt, fill=0x00)
    return screen