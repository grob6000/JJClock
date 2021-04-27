from jjrenderer.renderer import *

# digital clock
class RendererDigitalClock(Renderer):
  digitalfont = getFont("digital",300)
  digitaldatefont = getFont("ebgaramondmedium", 50)
  def getName(self):
    return "clock_digital"
  def getMenuItem(self):
    return {"text":"Digital", "icon":"digital.png"}
  def doRender(self, screen, **kwargs):
    fill(screen)
    if "timestamp" in kwargs:
      t = "{0:02d}:{1:02d}".format(kwargs["timestamp"].hour, kwargs["timestamp"].minute)
      print(kwargs["timestamp"])
      dstring = '{dt:%A} {dt:%B} {dt.day}, {dt.year}'.format(dt=kwargs["timestamp"])
    else:
      t = "--:--"
      dstring = "Please Wait..."
    tsz = RendererDigitalClock.digitalfont.getsize(t)
    tsz2 = RendererDigitalClock.digitaldatefont.getsize(dstring)
    digy = int((screen.size[1]-tsz[1]-tsz2[1]-50)/2)
    draw = ImageDraw.Draw(screen)
    draw.text((screen.size[0]/2-tsz[0]/2, digy), t, font=RendererDigitalClock.digitalfont, fill=0x00)
    draw.text((screen.size[0]/2-tsz2[0]/2, digy + tsz[1] + 50), dstring, font=RendererDigitalClock.digitaldatefont, fill=0x00)
    return screen

if __name__ == "__main__":
  testRenderer(RendererDigitalClock)