from jjrenderer.renderer import *

class RendererConfig(Renderer):

  bigfont = getFont(fontsize=100)
  mediumfont = getFont(fontsize=50)
  
  def getName(self):
    return "config"
  def getMenuItem(self):
    return {"icon":"config.png","text":"Configuration"}
  def doRender(self, screen, **kwargs):
    
    fill(screen)
    
    # header
    t = "Configuration"
    tsz = RendererConfig.bigfont.getsize(t)
    configicon = getImage("config")
    x = int((screen.size[0] - configicon.size[0] - tsz[0] - 50) / 2)
    screen.paste(configicon, (x, 100))
    x = x + configicon.size[0] + 50
    draw = ImageDraw.Draw(screen)
    draw.text((x, int(100 + configicon.size[1]/2 - tsz[1]/2)), t, font=RendererConfig.bigfont, fill=0x00)
    
    # data
    if kwargs["port"] == 80:
      addr = kwargs["ip"]
    else:
      addr = kwargs["ip"] + ":" + str(kwargs["port"])
    t = "Wifi SSID: {0}\nWIFI Password:{1}\nAddress: http:\\\\{2}\\".format(kwargs["ssid"],kwargs["password"],addr)
    tsz = RendererConfig.mediumfont.getsize(t)
    draw.text((int(screen.size[0]/2 - tsz[0]/2), 100+configicon.size[1]+50), t, font=RendererConfig.mediumfont, fill=0x00)
    
    return screen