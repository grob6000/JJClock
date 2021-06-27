from jjrenderer.renderer import *
from math import ceil

class RendererMenu(Renderer):

  name = "menu"
  isclock = False
  
  menusize = (4,3)
  menupatchsize = (200,200)
  menuicondim = 120
  defaultmenu = [Renderer()]

  def __init__(self, menu=defaultmenu):
    # populate menu entries
    self.setMenu(menu)
  
  def setMenu(self, menu):
    self.menu = menu
    # in case of pre-drawing menu screens, put that here
    
  def doRender(self, screen, **kwargs):
    
    fill(screen)
    draw = ImageDraw.Draw(screen)
    
    if not "selecteditem" in kwargs:
      kwargs["selecteditem"] = 0
    
    if "menu" in kwargs:
      self.setMenu(kwargs["menu"])
    ipp = RendererMenu.menusize[0] * RendererMenu.menusize[1] # number of items per page
    page = int(kwargs["selecteditem"] / ipp)
    pi_select = kwargs["selecteditem"] % ipp # index of item selected on page
    
    stdfnt = getFont()
    
    for pi in range(0, ipp):
      mi = pi+(page*ipp)
      if len(self.menu) > mi:
        menuimg = Image.new('L', RendererMenu.menupatchsize)
        fill(menuimg)
        try:
          img = getImage(self.menu[mi].getMenuItem()["icon"])
        except FileNotFoundError:
          img = getImage("default.png")
        if img:
          menuimg.paste(img.resize((RendererMenu.menuicondim,RendererMenu.menuicondim),Image.ANTIALIAS),(int((RendererMenu.menupatchsize[0]-RendererMenu.menuicondim)/2),20))
        draw2 = ImageDraw.Draw(menuimg)
        t = self.menu[mi].getMenuItem()["text"]
        fsz = stdfnt.getsize(t)
        draw2.text((int(menuimg.size[0]/2-fsz[0]/2), RendererMenu.menuicondim + 30),t,font=stdfnt,fill=0x00)
        x = int((pi % RendererMenu.menusize[0] + 0.5) * (screen.size[0] / RendererMenu.menusize[0]) - RendererMenu.menupatchsize[0]/2)
        y = int((int(pi / RendererMenu.menusize[0]) + 0.5) * (screen.size[1] / RendererMenu.menusize[1]) - RendererMenu.menupatchsize[1]/2)
        if pi == pi_select: # show this item as selected with surrounding box
          screen.paste(0x80, box=(x-20, y-20, x+RendererMenu.menupatchsize[0]+20, y+RendererMenu.menupatchsize[1]+20))
        screen.paste(menuimg, (x,y))
    
    #draw = ImageDraw.Draw(screen)
    pagetext = "Page {0} of {1}".format(page+1, ceil(len(self.menu)/ipp))
    ptsz = stdfnt.getsize(pagetext)
    draw.text((int(screen.size[0]/2-ptsz[0]/2), 20), pagetext, font=stdfnt, fill=0x00)
    return screen