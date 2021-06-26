from jjrenderer.renderer import *

class RendererBirthdayClock(Renderer):
  def getName(self):
    return "clock_birthday"
  def getMenuItem(self):
    return {"icon":"icon_birthday.png","text":"Birthday","description":"Happy Birthday JJ!"}
  def doRender(self, screen, **kwargs):
    #fill(screen)
    bg = getImage("bg_cake")
    screen.paste(bg)
    ns = [kwargs["timestamp"].hour//10, kwargs["timestamp"].hour%10, kwargs["timestamp"].minute//10, kwargs["timestamp"].minute%10]
    x = int((screen.size[0]-800)/2)
    y0 = 150
    mapimg = getImage("map_birthdaycandles")
    for i in range(0,len(ns)):
      cimg = mapimg.crop((200*ns[i],0,200*(ns[i]+1),mapimg.size[1]))
      lambda x : 255 if x > 0 else 0
      mimg = cimg.convert('L').point(lambda x : 0 if x == 255 else 255, mode='1')
      screen.paste(cimg, (x,y0), mask=mimg)
      x = x + 200

    return screen