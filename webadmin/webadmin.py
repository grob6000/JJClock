from flask import Flask, request, render_template, send_from_directory, Response
from werkzeug.wsgi import FileWrapper
from io import BytesIO
import threading
import ctypes
import logging
import wifimanager # should be relatively threadsafe...
import settings # should be relatively threadsafe...
import urllib
import copy
from PIL import Image
from jjcommon import *

from display import MemoryDisplay

class WebAdmin():
  
  def __init__(self):
    self._app = Flask(__name__)
    self._worker = threading.Thread(target=self._run, daemon=True)
    self._stopevent = threading.Event()
    self._actionevent = threading.Event()
    self._actiondata = {}
    self._datalock = threading.Lock()
    self._requestwaiter = threading.Event()
    self._pages = [
      {"url":"/","name":"Home","func":self.getpageindex},
      {"url":"/wifi","name":"Wifi","func":self.getpagewifi},
      {"url":"/settings","name":"Settings","func":self.getpagesettings},
      {"url":"/menu","name":"Clock Menu","func":self.getpagemenu},
    ]
    for p in self._pages:
      self._app.add_url_rule(p["url"], view_func=p["func"], methods=['GET'])
    self._app.add_url_rule("/api/getnetworks", view_func=self.getnetworks, methods=['GET'])
    self._app.add_url_rule("/api/scannetworks", view_func=self.scan, methods=['GET'])
    self._app.add_url_rule("/api/addnetwork", view_func=self.addnetwork, methods=['POST'])
    self._app.add_url_rule("/api/removenetwork", view_func=self.removenetwork, methods=['POST'])
    self._app.add_url_rule("/api/screen.png", view_func=self.getscreen, methods=['GET'])
    self._app.add_url_rule("/api/reconfigurewifi", view_func=self.reconfigurewifi, methods=['GET'])
    self._app.add_url_rule("/api/setwifimode", view_func=self.setmode, methods=['POST'])
    self._app.add_url_rule("/api/settings", view_func=self.setsetting, methods=['POST', 'PUT'])
    self._app.add_url_rule("/api/settings", view_func=self.getsetting, methods=['GET'])
    self._app.add_url_rule("/api/status", view_func=self.getstatus, methods=['GET'])
    self._savednetworks = []
    self._scannetworks = []
    self._menu = []
    self.display = MemoryDisplay()
    self.display.resize = True

  def __del__(self):
    if self._worker.is_alive():
      self.stop()
      
  def start(self):
    self._worker.start()
    logging.info("webadmin server started")

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
      self._app.run(debug=True, use_reloader=False, host='0.0.0.0', port=webadmin_port)
    except Exception as e:
      print("app stopped: {0}".format(e))
  
  #def provideWifiNetworks(self, networks):
  #  with self._datalock:
  #    self._savednetworks = networks
  
  #def provideWifiScan(self, networks):
  #  with self._datalock:
  #    self._scannetworks = networks  

  #def provideMenu(self, menu):
  #  with self._datalock:
  #    self._menu = menu   
  # 

  def provideStatus(self, statusdict):
    with self._datalock:
      self._statusdict = copy.deepcopy(statusdict) 
  
  # returns action data dict, and clears action data (one shot)
  # returns None if there is no new data (can be polled)
  def getActionData(self):
    with self._datalock:
      adata = self._actiondata
      self._actiondata = None
    return adata
    
  def getpageindex(self):
    return render_template('index.html', pages=self._pages)
  
  def getpagewifi(self):
    #with self._datalock:
    #  networks = wifimanager.getNetworks()
    #  scans = wifimanager.scanNetworks()
    return render_template('wifi.html', pages=self._pages)
  
  def getpagesettings(self):
    return "not implemented"
  
  def getpagemenu(self):
    return "not implemented"
    
  def getnetworks(self):
    with self._datalock:
      networks = wifimanager.getNetworks()
      wifimode = wifimanager.getWifiMode()
    return {"networks":networks, "wifimode":wifimode}
    
  def addnetwork(self):
    network = request.get_json(silent=True)
    if network and "ssid" in network:
      ssid = str(network["ssid"])
      psk = None
      if "psk" in network:
        psk = str(network["psk"])
      i = wifimanager.addNetwork(ssid, psk)
      return {"id":i, "ssid":ssid}
    else:
      logging.warning("bad request to addnetwork")
      return ""
      
  def removenetwork(self):
    network = request.get_json(silent=True)
    if network and "id" in network:
      wifimanager.removeNetwork(network["id"])
    else:
      logging.warning("bad request to addnetwork")
    return ""
        
  def scan(self):
    with self._datalock:
      scans = wifimanager.scanNetworks()
    return {"scans":scans}   

  def reconfigurewifi(self):
    wifimanager.reconfigureWifi()
    return {"result":"ok"}
  
  def getscreen(self):
    logging.debug("getscreen")
    img = self.display.getImage()
    b = BytesIO()
    img.save(b, format="PNG")
    b.seek(0)
    w = FileWrapper(b)
    r = Response(w, mimetype="image/png", direct_passthrough=True)
    logging.debug(r)
    return r

  def setmode(self):
    r = request.get_json(silent=True)
    if "mode" in r:
      if r["mode"] == "ap":
        wifimanager.setWifiMode("ap")
      if r["mode"] == "client":
        wifimanager.setWifiMode("client")
    else:
      logging.warning("bad request to setmode")
    return {"mode":wifimanager.getWifiMode()}

  def setsetting(self):
    r = request.get_json(silent=True)
    out = {}
    for k, v in r.items():
      settings.setSetting(str(k), v)
      out[str(k)] = settings.getSetting(str(k))
    return out
  
  def getsetting(self):
    r = request.get_json(silent=True)
    s = None
    if r and "settings" in r:
      s = r["settings"]
      out = {}
      for k in s:
        out[str(k)] = settings.getSetting(str(k))
    else:
      out = settings.getAllSettings() # get all if nothing specified
    return out

  def getstatus(self):
    with self._datalock:
      r = copy.deepcopy(self._statusdict)
    return r

  def getnavbar(self):
    return render_template('navbar.html', pages=self._pages)
