from jjrenderer.renderer import *
import math

class RendererAnalogClock(Renderer):

  name = "clock_analog"
  isclock = True
  menuitem = {"icon":"icon_analog.png","text":"Analog","description":"I'm just a simple country analog clock. Don't mind me."}

  romannumerals = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]

  def doRender(self, screen, **kwargs):
    fill(screen, color=0xFF)
    draw = ImageDraw.Draw(screen)
    
    # face circle
    margin = 50
    r = int((screen.size[1]/2)-margin)
    t = 10
    c = (int(screen.size[0]/2), int(screen.size[1]/2))
    draw.ellipse((c[0]-r, c[1]-r, c[0]+r, c[1]+r))
    draw.ellipse((c[0]-r+t, c[1]-r+t, c[0]+r-t, c[1]+r-t))
    
    # face ticks
    for i in range(0,60):
      a = math.radians(360/60*i)
      x0 = c[0] + math.cos(a)*(r-t)
      x1 = c[0] + math.cos(a)*r
      y0 = c[1] + math.sin(a)*(r-t)
      y1 = c[1] + math.sin(a)*r
      if i % 5:
        w = 2
      else:
        w = 5
      draw.line((x0,y0,x1,y1), fill=0x00, width=w)
    
    # numbers
    inset = 80
    romanfont = getFont("times",60)
    for i in range(0,12):
      tsz = romanfont.getsize(RendererAnalogClock.romannumerals[i])
      hy = tsz[1] + romanfont.getoffset(RendererAnalogClock.romannumerals[i])[1]
      a = math.radians(360/12*(i+1))
      x = c[0] + math.sin(a)*(r-inset) - int(tsz[0]/2)
      y = c[1] - math.cos(a)*(r-inset) - int(hy/2)
      draw.text((x,y), RendererAnalogClock.romannumerals[i], fill=0x00, font=romanfont)
    
    # hands
    t_min = 7
    r_min = r - 30
    a_min = math.radians(kwargs["timestamp"].minute / 60 * 360)
    x = c[0] + math.sin(a_min)*r_min
    y = c[1] - math.cos(a_min)*r_min
    draw.line((c[0], c[1], x, y), fill=0x00, width=t_min)
    r_hour = int(r / 2)
    t_hour = 10
    a_hour = math.radians(((kwargs["timestamp"].hour % 12) / 12 + kwargs["timestamp"].minute / (12*60)) * 360)
    x = c[0] + math.sin(a_hour)*r_hour
    y = c[1] - math.cos(a_hour)*r_hour
    draw.line((c[0], c[1], x, y), fill=0x00, width=t_hour)    
    
    # boss
    rboss = 15
    draw.ellipse((c[0]-rboss,c[1]-rboss,c[0]+rboss,c[1]+rboss),fill=0x00)
    
    return screen