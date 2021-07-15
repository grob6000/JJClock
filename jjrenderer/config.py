from jjrenderer.renderer import *

import qrcode

class RendererConfig(Renderer):

  name = "config"
  isclock = False
  menuitem = {"icon":"icon_config.png","text":"Configuration","description":"Enters AP mode to help configure Wifi. You probably don't want to enable this from here!"}

  bigfont = getFont(fontsize=100)
  mediumfont = getFont(fontsize=50)
  smallfont = getFont(fontsize=20)

  def doRender(self, screen, **kwargs):
    
    fill(screen)
    
    # header
    t = "Configuration"
    tsz = RendererConfig.bigfont.getsize(t)
    configicon = getImage("icon_config")
    x0 = int((screen.size[0] - configicon.size[0] - tsz[0] - 150) / 2)
    y0 = 100
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
    
    addr = "http://" + addr + "/"

    t = [["Wifi SSID:", ssid],
        ["WIFI Password:",pwd],
        ["Address:", addr],
        ["IP Address:", ipaddr]]

    y = y0 + configicon.size[1] + 80
    x0 = 150
    for l in t:
      draw.text((x0, y), l[0], font=self.mediumfont, fill=0x00)
      draw.text((x0+400, y), l[1], font=self.mediumfont, fill=0x00)
      y = y + 80
    
    # generate qrcode for wifi
    qrcodesize = 250
    y_qrt = y + qrcodesize
    if kwargs["wifimode"] == "ap":
      wifiqrstring = "WIFI:S:{0};T:WPA;P:{1};;".format(ssid, pwd)
      wifiqrimg = qrcode.make(wifiqrstring)
      wifiqrimg = wifiqrimg.resize((qrcodesize,qrcodesize))
      x = int((screen.size[0] - qrcodesize*3)/2)
      screen.paste(wifiqrimg, (x, y))
      tsz = self.smallfont.getsize("Connect Wifi")
      draw.text((x + int((250 - tsz[0])/2), y_qrt), "Connect Wifi", font=self.smallfont, fill=0x00)
      x = x + (qrcodesize * 2)
    else:
      x = int((screen.size[0] - qrcodesize)/2)

    # generate qrcode for link
    qrimg = qrcode.make(addr)
    qrimg = qrimg.resize((qrcodesize,qrcodesize))
    screen.paste(qrimg, (x,y))
    tsz = self.smallfont.getsize("Open Page")
    draw.text((x + int((250 - tsz[0])/2), y_qrt), "Open Page", font=self.smallfont, fill=0x00)
    
    return screen