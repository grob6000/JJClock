# gps handler

import serial
import threading
import pytz
import timezonefinder
import atexit
import time
from sys import platform
import datetime

import jjlogger
logger = jjlogger.getLogger(__name__)

def formatlatlon(lat, lng):
  if lat and lng:
    lat = float(lat)
    lng = float(lng)
    latdir = "N"
    if lat < 0:
      latdir = "S"
    lngdir = "E"
    if lng < 0:
      lngdir = "W"
    return "{0:0.5f}°{1}, {2:0.5f}°{3}".format(lat,latdir,lng,lngdir)
  else:
    return None

class GpsHandler():
  
  _baud = 9600
  _tzcheckinterval = 900
  
  def __init__(self, port='/dev/serial0'):
    logger.debug("initializing gpshandler")
    self._datalock = threading.Lock()
    self._stopevent = threading.Event()
    self._newdataevent = threading.Event()
    self._tf = timezonefinder.TimezoneFinder()
    with self._datalock:
      self._port = port
      self._dt_utc = None
      self._signalok = False
      self._lat = None
      self._lng = None
      self._tz = pytz.UTC
      self._tzfound = False
    self._worker = threading.Thread(target=self._run, daemon=True)
    atexit.register(self.__del__) # try to terminate thread nicely on quit (give back serial port)
    #self._worker.run() # start the thread listening for NMEA data
    
  def __del__(self):
    if self._worker.is_alive():
      self._stopevent.set() # ask the worker thread to exit, which will also release the serial port
      self._worker.join() # wait for this to occur before allowing a quit
  
  def connect(self):
    if self._worker.is_alive():
      logger.debug("already connected!")
    else:
      self._worker.start()
  
  def disconnect(self):
    if self._worker.is_alive():
      self._stopevent.set()
      self._worker.join()
      # gps thread reports disconnection
    else:
      logger.debug("already disconnected!")
  
  def isrunning(self):
    return self._worker.is_alive()
    
  def setPort(self, port):
    wasrunning = self._worker.is_alive()
    if wasrunning:
      self.disconnect()
    with self._datalock:
      self._port = port
    if wasrunning:
      self.connect()
    
  def getDateTime(self, local=True):
    with self._datalock:
      if self._dt_utc:
        if local and self._dt_utc:
          dt = self._dt_utc.astimezone(self._tz)
        else:
          dt = self._dt_utc
    return dt
    
  def getStatus(self):
    with self._datalock:
      hastime = bool(self._dt_utc)
      signalok = self._signalok
      hasfix = bool(self._lat) and bool(self._lng)
      tz = None
      if self._tzfound:
        tz = self._tz
      lat = self._lat
      lng = self._lng
      dt_utc = self._dt_utc
    return {"hastime":hastime, "hasfix":hasfix, "signalok":signalok, "tz":tz, "lat":lat, "lng":lng, "dtutc":dt_utc}
  
  # check if data has been updated since last call
  def pollUpdated(self):
    isupdated = self._newdataevent.is_set()
    self._newdataevent.clear()
    return isupdated
  
  def _run(self):
  
    if not "linux" in platform:
      logger.warning("no serial, handler will quit (blank values available only)")
      return
    
    try:
      ser = serial.Serial(self._port, GpsHandler._baud, timeout=0.2)
    except serial.serialutil.SerialException:
      logger.error("could not open port. GPS will not be initialized. thread quit.")
      return
    else:
      logger.info("GPS connected")
      
    lasttzcheck = time.monotonic() - GpsHandler._tzcheckinterval # keep track of when timezone was last checked; set up to trigger soonish
    while not self._stopevent.is_set(): # repeat until stop
      
      line = ser.readline()# readline from serial - timeouts will return 
      try:
        fields = line.decode('ascii').split(",")
      except UnicodeDecodeError:
        logger.warning("GPS serial data garbage line - ignoring")
        fields = [""]
        
      if fields[0] == "$GPRMC": # only parse GPRMC messages
        #logger.debug("received message: " + str(fields))
        # utc time
        dt_utc = None
        if (len(fields[1]) >= 6) and (len(fields[9]) >= 6):
          hour = int(fields[1][0:2])
          minute = int(fields[1][2:4])
          second = int(fields[1][4:6])
          day = int(fields[9][0:2])
          month = int(fields[9][2:4])
          year = int(fields[9][4:6]) + 2000 
          dt_utc = datetime.datetime(year, month, day, hour, minute, second, tzinfo=pytz.UTC)
    
        # signal validity
        sigok = bool(fields[2] == "A")
        
        # lat and lng
        lat = None
        lng = None
        if len(fields[3])>0:
          lat = float(fields[3][0:2]) + float(fields[3][2:])/60
          if fields[4] == "S":
            lat = lat * -1
        if len(fields[5])>0:
          lng = float(fields[5][0:3]) + float(fields[5][3:])/60
          if fields[6] == "W":
            lng = lng * -1
    
        # get timezone - check 1/min if all preconditions met (signal quality indicator we will ignore; as long as we have a fix it's probably fine for TZ)
        tz = None
        t = time.monotonic() # reuse this
        if dt_utc and t - lasttzcheck > GpsHandler._tzcheckinterval and lat and lng:
          tzname = self._tf.certain_timezone_at(lat=lat,lng=lng)
          tz = pytz.timezone(tzname)
          lasttzcheck = t
          logger.debug("collected timezone from GPS data: " + tzname)
        
        #logger.debug("setting data...")
        # update data
        with self._datalock:
          if dt_utc:
            self._dt_utc = dt_utc
          if lat:
            self._lat = lat
          if lng:
            self._lng = lng
          if tz:
            self._tz = tz
            self._tzfound = True
          if sigok:
            self._signalok = sigok
            
        self._newdataevent.set() # set event for new data
        #logger.debug("newdataevent status = {0}".format(self._newdataevent.is_set()))
  
    ser.close() # after quit, close the serial port
    logger.info("GPS disconnected")
    
      