from jjrenderer.renderer import *

# Copy this template, save as a new file in the jjrenderer module folder (anything, but without a _ at the beginning, please - e.g. "euro.py")
# The app will discover the contents automatically when starting.

# change my name - clocks should be format "Renderer[Name]Clock", others "Renderer[Name]". Must be unique!
class RendererTemplate(Renderer):
  """Template Renderer"""

  name = "template" # a unique name, used for mode and menu selection. if it's a clock, please prepend "clock_", e.g. "clock_euro"
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