from flask import Flask, request, render_template, send_from_directory, Response, abort
from werkzeug.wsgi import FileWrapper
from io import BytesIO
import threading
import ctypes
import wifimanager # should be relatively threadsafe...
import settings # should be relatively threadsafe...
import copy
from PIL import Image
import waitress
import subprocess

from jjcommon import *
from gpshandler import formatlatlon
import jjrenderer

from display import MemoryDisplay

import jjlogger
logger = jjlogger.getLogger("webadmin")
jjlogger.subsumeLogger("werkzeug")
jjlogger.subsumeLogger("waitress")

class WebAdmin():
  
  def __init__(self):
    self._app = Flask(__name__)
    jjlogger.subsumeLogger(self._app.logger)
    self._worker = threading.Thread(target=self._run, daemon=True)
    self._stopevent = threading.Event()
    self.rebootevent = threading.Event()
    self._datalock = threading.Lock()
    self._pages = [
      {"url":"/","name":"Home","id":"index","func":self.getpageindex},
      {"url":"/menu","name":"Menu","id":"menu","func":self.getpagemenu},
      {"url":"/wifi","name":"Wifi","id":"wifi","func":self.getpagewifi},
      {"url":"/settings","name":"Settings","id":"settings","func":self.getpagesettings},
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
    self._app.add_url_rule("/api/screenpoll", view_func=self.getpoll, methods=['GET'])
    self._app.add_url_rule("/api/setmode", view_func=self.setmode, methods=['POST'])       
    self._app.add_url_rule("/api/update/check", view_func=self.getupdateversion, methods=['GET'])      
    self._app.add_url_rule("/api/update/do", view_func=self.doupdate, methods=['GET'])
    self._app.add_url_rule("/api/reboot",view_func=self.doreboot, methods=["GET"])           
    self._app.add_url_rule("/api/icons/<string:iconfile>", view_func=self.geticon, methods=['GET'])    
    self._app.add_url_rule("/api/log.txt", view_func=self.getlog, methods=['GET'])    
    self._app.add_url_rule("/<string:fname>", view_func=self.getgeneral, methods=["GET"])
    self._savednetworks = []
    self._scannetworks = []
    self._menu = []
    self.display = MemoryDisplay()
    self.display.resize = True
    self.updatecheckrequest = threading.Event()
    self.updatedorequest = threading.Event()

  def __del__(self):
    if self._worker.is_alive():
      self.stop()
      
  def start(self):
    self._worker.start()
    logger.info("webadmin server started")
  
  def isrunning(self):
    return self._worker.is_alive()

  def _get_my_tid(self):
    if not self._worker.is_alive():
      logger.warning("the webadmin thread is not active")
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
        logger.debug("invalid thread id, could not stop")
      elif res != 1:
        ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid), None)
      else:
        logger.debug("thread stopped")
    else:
      logger.debug("thread was not running, already stopped!")
      return
  
  def _run(self):
    try:
      waitress.serve(self._app, listen='*:80')
      #self._app.run(debug=False, use_reloader=False, host='0.0.0.0', port=webadmin_port)
    except Exception as e:
      logger.info("Webapp stopped")

  def provideStatus(self, statusdict):
    with self._datalock:
      self._statusdict = copy.deepcopy(statusdict) 
  
  def getgeneral(self, fname):
    if fname.startswith('favicon'):
      return send_from_directory(os.path.join('static','favicon'), fname)
    else:
      abort(404)

  # returns action data dict, and clears action data (one shot)
  # returns None if there is no new data (can be polled)
  def getActionData(self):
    with self._datalock:
      adata = self._actiondata
      self._actiondata = None
    return adata
    
  def getpageindex(self):
    return render_template('index.html', pages=self._pages, pageid="index")
  
  def getpagewifi(self):
    return render_template('wifi.html', pages=self._pages, pageid="wifi")
  
  def getpagesettings(self):
    return render_template('settings.html', pages=self._pages, pageid="settings")
  
  def getpagemenu(self):
    return render_template('menu.html', pages=self._pages, pageid="menu", menudata=self._menudata)
    
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
      logger.warning("bad request to addnetwork")
      return ""
      
  def removenetwork(self):
    network = request.get_json(silent=True)
    if network and "id" in network:
      wifimanager.removeNetwork(network["id"])
    else:
      logger.warning("bad request to addnetwork")
    return ""
        
  def scan(self):
    with self._datalock:
      scans = wifimanager.scanNetworks()
    return {"scans":scans}   

  def reconfigurewifi(self):
    wifimanager.reconfigureWifi()
    return {"result":"ok"}
  
  def getscreen(self):
    logger.debug("getscreen")
    img = self.display.getImage()
    b = BytesIO()
    img.save(b, format="PNG")
    b.seek(0)
    w = FileWrapper(b)
    r = Response(w, mimetype="image/png", direct_passthrough=True)
    logger.debug(r)
    return r

  def getpoll(self):
    hash = self.display.getHash()
    return {"hash":hash}

  def setmode(self):
    r = request.get_json(silent=True)
    if "mode" in r:
      if r["mode"] == "ap":
        wifimanager.setWifiMode("ap")
      if r["mode"] == "client":
        wifimanager.setWifiMode("client")
    else:
      logger.warning("bad request to setmode")
    return {"mode":wifimanager.getWifiMode()}

  def setsetting(self):
    r = request.get_json(silent=True)
    out = {}
    if "settings" in r:
      settings.setSettings(r["settings"])
      sdict = settings.getSettings(r["settings"].keys())
      for k,v in sdict.items():
        out[k] = v.asDict()
    return {"settings":out}
  
  def getsetting(self):
    r = request.get_json(silent=True)
    logger.debug("getsetting request: " + request.get_data().decode())
    s = None
    if r and "settings" in r:
      s = r["settings"]
      logger.debug("getting partial settings: " + str(s))
      sdict = settings.getSettings(s)
    else:
      sdict = settings.getAllSettings()
    out = {}
    for k,v in sdict.items():
      out[k] = v.asDict()
    return {"settings":out}

  def getstatus(self):
    with self._datalock:
      r = copy.deepcopy(self._statusdict)
    # prepare some fields for jsonification: timezones as zone string, add location string, timestamps in ISO format (better than JSON crap)
    if r["tz"]:
      r["tz"] = r["tz"].zone
    if r["gps"]["tz"]:
      r["gps"]["tz"] = r["gps"]["tz"].zone
    r["gps"]["loc"] = formatlatlon(r["gps"]["lat"], r["gps"]["lng"])
    if r["timestamp"]:
      r["timestamp"] = str(r["timestamp"])
    if r["gps"]["dtutc"]:
      r["gps"]["dtutc"] = str(r["gps"]["dtutc"])
    return r
  
  def geticon(self, iconfile):
    logger.debug(iconfile)
    i = iconfile
    if not i.startswith("icon_"):
      i = "icon_" + iconfile # only serve stuff starting with icon_ hehe
    p = jjrenderer.getImagePath(i)
    logger.debug(i + " --> " + str(p.absolute()))
    if p:
      return send_from_directory(os.path.dirname(p), os.path.basename(p))
    abort(404) # not found otherwise

  def providemenu(self, menu=[]):
    logger.debug("menu provided to webadmin")
    self._menudata = []
    for rclass in menu:
      md = copy.deepcopy(rclass.menuitem)
      md["name"] = rclass.name
      md["updateinterval"] = rclass.updateinterval
      self._menudata.append(md)

  def getupdateversion(self):
    self.updatecheckrequest.set() # request a check. browser will wait and ask for result later
    return {"status":"ok"}
    
  def doupdate(self):
    self.updatedorequest.set() # request an update. browser probably will need refreshing!
    return {"status":"ok"}
  
  def doreboot(self):
    self.rebootevent.set()
    return {"status":"ok"}

  def getlog(self):
    journaltext = ""
    try:
      cp = subprocess.run(["journalctl", "-u", "jjclock.service"], capture_output=True, text=True, check=True)
      journaltext = cp.stdout
    except subprocess.CalledProcessError as e:
      logger.error("error while reading log: " + str(e))
      abort(500)
    r = Response(journaltext, mimetype="text/plain", direct_passthrough=True)
    return r
    