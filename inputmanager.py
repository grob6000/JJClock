from queue import Queue
import jjlogger
logger = jjlogger.getLogger(__name__)
from math import atan2, degrees
import gpiozero
import sys
if "linux" in sys.platform:
  import ft5406

ACTION_NONE = "none"
ACTION_CLICK = "click"
ACTION_UP = "up"
ACTION_DOWN = "down"
ACTION_LEFT = "left"
ACTION_RIGHT = "right"

class InputManager():
  def __init__(self):
    self.eventqueue = Queue()
    self.inputdevices = []
  def addinput(self, inputdevice):
    if isinstance(inputdevice, InputDevice):
      inputdevice.actionqueue = self.eventqueue
      self.inputdevices.append(inputdevice)
      logger.debug("Added {0} to input devices".format(inputdevice))
    else:
      logger.warning("Cannot add {0} - not an InputDevice".format(inputdevice))
  
class InputEvent():
  def __init__(self, action=ACTION_NONE, pos=(0,0)):
    self.action = action
    self.pos = pos

class InputDevice():
  def __init__(self):
    self._isopen = True
    self.actionqueue = Queue() # this can be replaced by inputmanager
  def open(self):
    self._isopen = True
  def close(self):
    self._isopen = False
  def isopen(self):
    return self._isopen

class GPIOButton(InputDevice):

  def __init__(self, pin=23, pressaction=ACTION_CLICK):
    self.pressaction = pressaction
    self._button = gpiozero.Button(pin=pin, bounce_time=0.050)
    self._button.when_pressed = self.onButton
  
  def onButton(self):
    self.actionqueue.put(InputEvent(self.pressaction,pos=None))

class FT5406TouchInput(InputDevice):
  
  def __init__(self, device="raspberrypi-ts", gesturepx=100, gestureangle=30):
    self._lastpresses = {}
    self.gesturepx = gesturepx
    self.gestureangle = gestureangle
    if "linux" in sys.platform:
      self._ts = ft5406.Touchscreen(device=device)
      for touch in self._ts.touches:
        touch.on_press = self._touch_handler
        touch.on_release = self._touch_handler
        touch.on_move = self._touch_handler
    else:
      self._ts = None
      logger.warning("Cannot init FT5406 on this platform.")
    self.open()
  
  def open(self):
    if self._ts:
      self._ts.run()
      logger.debug("Touchscreen input thread running")
  
  def close(self):
    if self._ts:
      self._ts.stop()
      logger.debug("Touchscreen input thread stopped")
  
  def isopen(self):
    if self._ts:
      return self._ts._running
    else:
      return False

  def _touch_handler(self, event, touch):
    if event == ft5406.TS_PRESS:
      self._lastpresses[touch.slot] = touch
    if event == ft5406.TS_RELEASE:
      if touch.slot in self._lastpresses:
        lastpress = self._lastpresses[touch.slot]
        dx = touch.position[0]-lastpress.position[0]
        dy = touch.position[1]-lastpress.position[1]
        d = ((dx**2) + (dy**2))**0.5
        a = degrees(atan2(dy,dx))
        logger.debug("d = {0:0.1f}, a = {1:0.1f}".format(d,a))
        ie = None
        if d < self.gesturepx:
          # is a tap
          ie = InputEvent(ACTION_CLICK,pos=touch.position)
        else:
          # is long enough to count as a gesture
          if (-1*self.gestureangle < a and a < self.gestureangle):
            ie = InputEvent(ACTION_RIGHT, lastpress.position)
          elif (90-self.gestureangle < a and a < 90+self.gestureangle):
            ie = InputEvent(ACTION_UP, lastpress.position)
          elif (-90-self.gestureangle < a and a < -90+self.gestureangle):
            ie = InputEvent(ACTION_DOWN, lastpress.position)
          elif (180-self.gestureangle < a or a < -180+self.gestureangle):
            ie = InputEvent(ACTION_LEFT, lastpress.position)
        if ie:
          self.actionqueue.put(ie)
          logger.debug("ts action: " + ie.action)

    #if event == ft5406.TS_MOVE:
    #    print("touchscreen move", touch)


