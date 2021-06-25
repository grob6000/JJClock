from jjrenderer.renderer import *

class RendererConfig(Renderer):

  bigfont = getFont(fontsize=100)
  mediumfont = getFont(fontsize=50)
  
  def getName(self):
    return "config"
  def getMenuItem(self):
    return {"icon":"icon_config.png","text":"Configuration"}
  def doRender(self, screen, **kwargs):
    
    fill(screen)
    
    # header
    t = "Configuration"
    tsz = RendererConfig.bigfont.getsize(t)
    configicon = getImage("config")
    x0 = int((screen.size[0] - configicon.size[0] - tsz[0] - 50) / 2)
    y0 = 200
    screen.paste(configicon, (x0, y0))
    x = x0 + configicon.size[0] + 50
    draw = ImageDraw.Draw(screen)
    draw.text((x, int(y0 + configicon.size[1]/2 - tsz[1]/2)), t, font=RendererConfig.bigfont, fill=0x00)
    
    # data
    if kwargs["port"] == 80:
      addr = str(kwargs["ip"])
    else:
      addr = str(kwargs["ip"]) + ":" + str(kwargs["port"])
    t = [["Wifi SSID:", str(kwargs["ssid"])],
         ["WIFI Password:",str(kwargs["password"])],
         ["Address:", "http:\\\\{}\\".format(addr)]]
    y = y0 + configicon.size[1] + 100
    for l in t:
      draw.text((x0, y), l[0], font=RendererConfig.mediumfont, fill=0x00)
      draw.text((x0+400, y), l[1], font=RendererConfig.mediumfont, fill=0x00)
      y = y + 80
    
    return screen