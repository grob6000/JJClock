from jjrenderer.renderer import *

class RendererTemplate(Renderer):
  
  name = "template" # a unique name. if it's a clock, please use format "clock_*"
  isclock = True # True if this is a clock, and False if it is not (only clocks will be added to the menu)
  # icon should be 200x200, added to the "img" folder; and should start with "icon_"
  # text: the friendly name of the item (displayed on the menu screen and web)
  menuitem = {"icon":"icon_default.png","text":"Template","description":"Template - put a description here to show on web interface only"}
  #updateinterval = 1 # minutes. uncomment and change this if you want to update at other intervals

  def doRender(self, screen, **kwargs):
    screen = super().doRender(screen,**kwargs) # default (comment this out / replace with your own code to render a clock face)

    # use PIL image library (it's already imported) to turn 'screen' from a black empty box into a clock face
    # 
    # kwargs is a dictionary containing useful data, primarily:
    #   kwargs["timestamp"] - is a python datetime.datetime, in local time (with timezone info), with the time you should display
    #
    # useful functions common to many renderers can be found in jjrenderer.renderer, e.g.
    #   fill()
    #   getFont()
    #   getImage()
    #   getWeatherByCity()

    return screen