# gps handler

import serial
import threading
import queue
import pytz
import timezonefinder
import atexit
import time
from sys import platform
import datetime
import logging

class GpsHandler():
  
  _baud = 9600
  _tzcheckinterval = 300
  _defaultport = '/dev/serial0'
  
  def __init__(self):
    logging.debug("initializing gpshandler")
    self._datalock = threading.Lock()
    self._stopevent = threading.Event()
    self._newdataevent = threading.Event()
    with self._datalock:
      self._port = GpsHandler._defaultport
      self._dt_utc = None
      self._signalok = False
      self._lat = None
      self._lng = None
      self._tz = pytz.UTC
    self._worker = threading.Thread(target=self._run, daemon=True)
    atexit.register(self.__del__) # try to terminate thread nicely on quit (give back serial port)
    #self._worker.run() # start the thread listening for NMEA data
    
  def __del__(self):
    if self._worker.is_alive():
      self._stopevent.set() # ask the worker thread to exit, which will also release the serial port
      self._worker.join() # wait for this to occur before allowing a quit
  
  def connect(self):
    if self._worker.is_alive():
      logging.warning("already connected!")
    else:
      self._worker.start()
  
  def disconnect(self):
    if self._worker.is_alive():
      self._stopevent.set()
      self._worker.join()
      logging.info("gps listener disconnected")
    else:
      logging.warning("already disconnected!")
  
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
    return {"hastime":hastime, "hasfix":hasfix, "signalok":signalok}
  
  # check if data has been updated since last call
  def pollUpdated(self):
    isupdated = self._newdataevent.is_set()
    self._newdataevent.clear()
    return isupdated
  
  def _run(self):
  
    if not "linux" in platform:
      logging.warning("no serial, handler will quit (blank values available only)")
      return
    
    logging.debug("opening port" + self._port)
    ser = serial.Serial(self._port, GpsHandler._baud, timeout=1)
    
    lasttzcheck = time.monotonic() - GpsHandler._tzcheckinterval # keep track of when timezone was last checked; set up to trigger soonish
    while not self._stopevent.is_set(): # repeat until stop
      #logging.debug("waiting for serial input...")
      line = ser.readline()# readline from serial - timeouts will return 
      #logging.debug("serial received: " + line.decode('ascii'))
      fields = line.decode('ascii').split(",")
      if fields[0] == "$GPRMC": # only parse GPRMC messages
        #logging.debug("received message: " + str(fields))
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
        if dt_utc and time.monotonic() - lasttzcheck > GpsHandler._tzcheckinterval and lat and lng:
          tf = timezonefinder.TimezoneFinder()
          tzname = tf.certain_timezone_at(lat=lat,lng=lng)
          tz = pytz.timezone(tzname)
        
        #logging.debug("setting data...")
        # update data
        with self._datalock:
          if dt_utc:
            self._dt_utc = dt_utc
          if sigok:
            self._signalok = sigok
          if lat:
            self._lat = lat
          if lng:
            self._lng = lng
          if tz:
            self._tz = tz
        
        self._newdataevent.set() # set event for new data
        #logging.debug("newdataevent status = {0}".format(self._newdataevent.is_set()))
  
    ser.close() # after quit, close the serial port
    logging.info("quit gpshandler thread success")
    
      