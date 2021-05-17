from flask import Flask, request, render_template
from jjcommon import *
import threading
import ctypes
import logging
import wifimanager # should be relatively threadsafe...

class WebAdmin():

  def __init__(self):
    self._app = Flask(__name__)
    self._worker = threading.Thread(target=self._run, daemon=True)
    self._stopevent = threading.Event()
    self._actionevent = threading.Event()
    self._actiondata = {}
    self._datalock = threading.Lock()
    self._requestwaiter = threading.Event()
    self._app.add_url_rule("/", view_func=self.index)
    self._app.add_url_rule("/wifi", view_func=self.wifi)
    self._savednetworks = []
    self._scannetworks = []
    self._menu = []
    
  def __del__(self):
    if self._worker.is_alive():
      self.stop()
      
  def start(self):
    self._worker.start()
    logger.info("webadmin server started")

  def _get_my_tid(self):
    if not self._worker.is_alive():
      logging.warning("the webadmin thread is not active")
      return None
    
    # do we have it cached?
    if hasattr(self._worker, "_thread_id"):
        return self._worker._thread_id
    
    # no, look for it in the _active dict
    for tid, tobj in threading._active.items():
        if tobj is self._worker:
            self._worker._thread_id = tid
            return tid
                
  def stop(self):
    if self._worker.is_alive():
      tid = self._get_my_tid()
      exc = ctypes.py_object(SystemExit)
      res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid), exc)
      if res == 0:
        logging.warning("invalid thread id, could not stop")
      elif res != 1:
        ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid), None)
      else:
        logging.debug("thread stopped")
    else:
      logging.info("thread was not running, already stopped!")
      return
  
  def _run(self):
    try:
      self._app.run(debug=True, use_reloader=False)
    except:
      print("app stopped")
  
  def provideWifiNetworks(self, networks):
    with self._datalock:
      self._savednetworks = networks
  
  def provideWifiScan(self, networks):
    with self._datalock:
      self._scannetworks = networks  

  def provideMenu(self, menu):
    with self._datalock:
      self._menu = menu    
  
  # returns action data dict, and clears action data (one shot)
  # returns None if there is no new data (can be polled)
  def getActionData(self):
    with self._datalock:
      adata = self._actiondata
      self._actiondata = None
    return adata
    
  def index(self):
    return render_template('index.html')
  
  def wifi(self):
    with self._datalock:
      networks = wifimanager.getNetworks()
      scan = wifimanger.scanNetworks()
    return render_template('wifi.html', networks=networks, scan=scan)