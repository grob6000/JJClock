from jjrenderer.renderer import *

class RendererConfig(Renderer):

  name = "config"
  isclock = False
  menuitem = {"icon":"icon_config.png","text":"Configuration","description":"Enters AP mode to help configure Wifi. You probably don't want to enable this from here!"}

  bigfont = getFont(fontsize=100)
  mediumfont = getFont(fontsize=50)

  def doRender(self, screen, **kwargs):
    
    fill(screen)
    
    # header
    t = "Configuration"
    tsz = RendererConfig.bigfont.getsize(t)
    configicon = getImage("icon_config")
    x0 = int((screen.size[0] - configicon.size[0] - tsz[0] - 150) / 2)
    y0 = 200
    screen.paste(configicon, (x0, y0))
    x = x0 + configicon.size[0] + 150
    draw = ImageDraw.Draw(screen)
    draw.text((x, int(y0 + configicon.size[1]/2 - tsz[1]/2)), t, font=RendererConfig.bigfont, fill=0x00)
    
    # data
    if kwargs["port"] == 80:
      addr = str(kwargs["ip"])
    else:
      addr = str(kwargs["ip"]) + ":" + str(kwargs["port"])

    # get relevant wifi details depending on mode
    ssid = "****"
    pwd = "****"
    ipaddr = "*.*.*.*"
    addr = "*"
    if kwargs["wifimode"] == "client":
      # cautious; might not be present
      if "ssid" in kwargs["wifistatus"]:
        ssid = kwargs["wifistatus"]["ssid"]
      if "ip_address" in kwargs["wifistatus"]:
        ipaddr = kwargs["wifistatus"]["ip_address"]
    else:
      # ap details
      ssid = kwargs["ssid"]
      pwd = kwargs["password"]
      ipaddr = kwargs["ip"]

    # show rdns lookup name if available
    if "dnsname" in kwargs["wifistatus"]:
      addr = kwargs["wifistatus"]["dnsname"]
    else:
      addr = ipaddr

    # append port to addr if not 80
    if not kwargs["port"] == 80:
      addr = addr + ":" + str(kwargs["port"])

    t = [["Wifi SSID:", ssid],
        ["WIFI Password:",pwd],
        ["Address:", "http:\\\\{}\\".format(addr)],
        ["IP Address:", ipaddr]]

    y = y0 + configicon.size[1] + 100
    x0 = 150
    for l in t:
      draw.text((x0, y), l[0], font=RendererConfig.mediumfont, fill=0x00)
      draw.text((x0+400, y), l[1], font=RendererConfig.mediumfont, fill=0x00)
      y = y + 80
    
    return screen