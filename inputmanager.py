from queue import Queue
import jjlogger
logger = jjlogger.getLogger(__name__)
from math import atan2, degrees
import gpiozero
import sys
if "linux" in sys.platform:
  import ft5406

ACTION_NONE = 0
ACTION_CLICK = 1
ACTION_UP = 2
ACTION_DOWN = 3
ACTION_LEFT = 4
ACTION_RIGHT = 5

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
  
  def close(self):
    if self._ts:
      self._ts.stop()
  
  def isopen(self):
    if self._ts:
      return self._ts._running
    else:
      return False

  def _touch_handler(self, event, touch):
    if event == ft5406.TS_PRESS:
      self._lastpresses[touch.slot] = touch
      logger.debug("touchscreen pressed", touch)
    if event == ft5406.TS_RELEASE:
      print("touchscreen released", touch)
      if touch.slot in self._lastpresses:
        lasttouch = self._lastpreses[touch.slot]
        dx = touch.position[0]-lasttouch.position[0]
        dy = touch.position[1]-lasttouch.position[1]
        dsq = (dx**2) + (dy**2)
        if dsq < self.gesturepx**2:
          # is a tap
          self.actionqueue.put(InputEvent(ACTION_CLICK,pos=touch.position))
        else:
          # is long enough to count as a gesture
          a = degrees(atan2(dy,dx))
          if (-1*self.gestureangle < a and a < self.gesturangle):
            self.actionqueue.put(InputEvent(ACTION_RIGHT, lasttouch.position))
          elif (90-self.gestureangle < a and a < 90+self.gestureangle):
            self.actionqueue.put(InputEvent(ACTION_UP, lasttouch.position))
          elif (-90-self.gestureangle < a and a < -90+self.gestureangle):
            self.actionqueue.put(InputEvent(ACTION_DOWN, lasttouch.position))
          elif (180-self.gestureangle < a or a < -180+self.gestureangle):
            self.actionqueue.put(InputEvent(ACTION_LEFT, lasttouch.position))
    if event == ft5406.TS_MOVE:
        print("touchscreen move", touch)

